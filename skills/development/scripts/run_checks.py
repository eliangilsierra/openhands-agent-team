#!/usr/bin/env python3
"""Run a module's validation commands and summarise the results as evidence.

The commands come from the stack profile (detect_stack.py) or from --cmd. Output is
a compact JSON record and, with --md, the rows of the Pull Request "Tests" table:
long logs stay on disk, only the tail and the parsed counts reach the context.

Usage:
    python run_checks.py --profile .agent-state/stack-profile.json [--module apps/web]
                         [--checks lint,typecheck,test,build] [--install]
                         [--baseline | --compare BASELINE.json] [--out RESULT.json] [--md]
    python run_checks.py --cmd test="npm test" --cmd lint="npm run lint"

Exit code: 0 when every executed check passed, 1 when one failed or was blocked.
Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import secret_scan  # noqa: E402  (sibling module: the team's single pattern policy)

SHELL_BUILTINS = {"cd", "export", "set", "test", "[", "echo", "exit", "true", "false", "source", ".", "env"}
ORDER = ["install", "format", "lint", "typecheck", "test", "build", "verify"]
DEFAULT_CHECKS = ["format", "lint", "typecheck", "test", "build"]


def redact(text: str) -> str:
    """Replace every secret of the team policy, so logs and evidence never carry credentials."""
    return secret_scan.redact(text)


def last_int(pattern: str, text: str) -> int | None:
    found = re.findall(pattern, text, re.MULTILINE)
    if not found:
        return None
    value = found[-1]
    return int(value[0] if isinstance(value, tuple) else value)


def parse_counts(output: str) -> dict:
    """Best-effort passed/failed/skipped counts for common test runners."""
    text = re.sub(r"\x1b\[[0-9;]*m", "", output)
    # Maven Surefire / Failsafe: the last "Tests run" line is the total.
    match = re.findall(r"Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)", text)
    if match:
        run, failures, errors, skipped = map(int, match[-1])
        return {"passed": run - failures - errors - skipped, "failed": failures + errors, "skipped": skipped}
    # .NET: "Passed!  - Failed: 0, Passed: 12, Skipped: 1, Total: 13"
    match = re.findall(r"Failed:\s+(\d+), Passed:\s+(\d+), Skipped:\s+(\d+)", text)
    if match:
        failed = sum(int(m[0]) for m in match)
        return {"passed": sum(int(m[1]) for m in match), "failed": failed, "skipped": sum(int(m[2]) for m in match)}
    # Gradle: "5 tests completed, 1 failed, 1 skipped"
    match = re.search(r"(\d+) tests? completed(?:, (\d+) failed)?(?:, (\d+) skipped)?", text)
    if match:
        total, failed, skipped = int(match.group(1)), int(match.group(2) or 0), int(match.group(3) or 0)
        return {"passed": total - failed - skipped, "failed": failed, "skipped": skipped}
    # Jest: "Tests:       1 failed, 2 skipped, 40 passed, 43 total"
    match = re.search(r"^Tests:\s+(.*\d+ total)", text, re.MULTILINE)
    if match:
        line = match.group(1)
        return {key: last_int(rf"(\d+) {key}", line) or 0 for key in ("passed", "failed", "skipped")}
    # Vitest: "      Tests  2 failed | 40 passed | 1 skipped (43)"
    match = re.search(r"^\s*Tests\s+(.*\(\d+\))", text, re.MULTILINE)
    if match:
        line = match.group(1)
        return {"passed": last_int(r"(\d+) passed", line) or 0, "failed": last_int(r"(\d+) failed", line) or 0,
                "skipped": last_int(r"(\d+) (?:skipped|t[o]do)", line) or 0}
    # pytest: "==== 2 failed, 40 passed, 1 skipped in 3.2s ===="
    match = re.search(r"=+ (.*\d+ (?:passed|failed|error|errors|skipped).*) in [\d.]+s", text)
    if match:
        line = match.group(1)
        errors = last_int(r"(\d+) errors?", line) or 0
        return {"passed": last_int(r"(\d+) passed", line) or 0,
                "failed": (last_int(r"(\d+) failed", line) or 0) + errors,
                "skipped": last_int(r"(\d+) skipped", line) or 0}
    # go test: count package lines.
    ok, failed = len(re.findall(r"^ok\s", text, re.MULTILINE)), len(re.findall(r"^FAIL\s", text, re.MULTILINE))
    if ok or failed:
        return {"packages_ok": ok, "packages_failed": failed}
    return {}


def missing_program(command: str, cwd: Path) -> str | None:
    """The command's program when it is neither on PATH nor a file in cwd (checked before running)."""
    try:
        program = shlex.split(command)[0]
    except (ValueError, IndexError):
        return None
    if program in SHELL_BUILTINS or "=" in program:
        return None
    if "/" in program or program.startswith("."):
        return None if (cwd / program).exists() or Path(program).exists() else program
    return None if shutil.which(program) else program


def run(name: str, command: str, cwd: Path, timeout: int, tail: int, log_dir: Path | None) -> dict:
    started = time.monotonic()
    program = missing_program(command, cwd)
    if program:
        return {"name": name, "command": command, "cwd": str(cwd), "exit_code": None, "status": "BLOCKED",
                "note": f"{program} is not installed or not on PATH", "duration_s": 0.0, "counts": {}, "tail": []}
    env = {**os.environ, "CI": "true", "FORCE_COLOR": "0", "NO_COLOR": "1"}
    try:
        proc = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True,
                              timeout=timeout, env=env, errors="replace")
        output, code = (proc.stdout or "") + (proc.stderr or ""), proc.returncode
        missing = code in (126, 127)
        status = "PASS" if code == 0 else ("BLOCKED" if missing else "FAIL")
        note = "command not found or not executable" if missing else ""
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        code, status, note = None, "BLOCKED", f"timed out after {timeout}s"
    output = redact(output)
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / f"{name}.log").write_text(output, encoding="utf-8")
    lines = [line for line in output.splitlines() if line.strip()]
    return {"name": name, "command": command, "cwd": str(cwd), "exit_code": code, "status": status,
            "note": note, "duration_s": round(time.monotonic() - started, 1), "counts": parse_counts(output),
            "tail": lines[-tail:] if status != "PASS" else lines[-min(tail, 5):]}


def describe(result: dict, baseline: dict | None = None) -> str:
    """One-line result: 'PASS - 412 passed, 0 failed (baseline PASS, 405 passed)'."""
    counts = result.get("counts") or {}
    text = result["status"]
    if "passed" in counts:
        text += f" - {counts['passed']} passed, {counts['failed']} failed"
        text += f", {counts['skipped']} skipped" if counts.get("skipped") else ""
    elif "packages_ok" in counts:
        text += f" - {counts['packages_ok']} packages ok, {counts['packages_failed']} failed"
    if result.get("note"):
        text += f" ({result['note']})"
    if baseline:
        base_counts = baseline.get("counts") or {}
        text += f" (baseline {baseline['status']}"
        text += f", {base_counts['passed']} passed)" if "passed" in base_counts else ")"
    return text


def regressions(results: list[dict], baseline: dict) -> list[str]:
    found = []
    previous = {r["name"]: r for r in baseline.get("results", [])}
    for result in results:
        before = previous.get(result["name"])
        if not before:
            continue
        if before["status"] == "PASS" and result["status"] != "PASS":
            found.append(f"{result['name']}: PASS before the change, {result['status']} now")
        b, a = before.get("counts") or {}, result.get("counts") or {}
        if "passed" in b and "passed" in a and a["passed"] + a.get("skipped", 0) < b["passed"] + b.get("skipped", 0):
            found.append(f"{result['name']}: fewer tests than the baseline ({b['passed']} -> {a['passed']} passed)")
        if a.get("skipped", 0) > b.get("skipped", 0):
            found.append(f"{result['name']}: more skipped tests than the baseline ({b.get('skipped', 0)} -> {a['skipped']})")
    return found


def to_markdown(record: dict, baseline: dict | None) -> str:
    previous = {r["name"]: r for r in (baseline or {}).get("results", [])}
    rows = ["| Command | Result |", "| --- | --- |"]
    for result in record["results"]:
        rows.append(f"| `{result['command']}` | {describe(result, previous.get(result['name']))} |")
    for problem in record.get("regressions", []):
        rows.append(f"| regression | {problem} |")
    return "\n".join(rows) + "\n"


def pick_module(profile: dict, wanted: str | None, root: Path) -> dict:
    modules = profile.get("modules", [])
    if wanted:
        for module in modules:
            if module["path"] == wanted.strip("/") or (wanted in (".", "") and module["path"] == "."):
                return module
        raise SystemExit(f"error: module {wanted!r} is not in the profile ({[m['path'] for m in modules]})")
    if len(modules) == 1:
        return modules[0]
    raise SystemExit(f"error: the profile has {len(modules)} modules; choose one with --module "
                     f"({[m['path'] for m in modules]})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--profile", help="stack profile written by detect_stack.py")
    parser.add_argument("--module", help="module path in the profile (required when it has several)")
    parser.add_argument("--root", default=".", help="repository root or worktree (default: current directory)")
    parser.add_argument("--checks", help=f"comma-separated subset of {ORDER} (default: {','.join(DEFAULT_CHECKS)})")
    parser.add_argument("--install", action="store_true", help="run the install command first")
    parser.add_argument("--cmd", action="append", default=[], metavar="NAME=COMMAND", help="add or override a check")
    parser.add_argument("--timeout", type=int, default=900, help="seconds per check (default 900)")
    parser.add_argument("--tail", type=int, default=40, help="output lines kept for failing checks")
    parser.add_argument("--baseline", action="store_true", help="record the state before the change")
    parser.add_argument("--compare", help="baseline JSON to compare with; regressions fail the run")
    parser.add_argument("--out", help="write the JSON record to this file")
    parser.add_argument("--logs", help="directory for full logs (default: next to --out)")
    parser.add_argument("--md", action="store_true", help="print the Pull Request Tests table rows")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    commands: dict[str, str] = {}
    cwd = root
    if args.profile:
        module = pick_module(json.loads(Path(args.profile).read_text(encoding="utf-8")), args.module, root)
        commands.update(module.get("commands", {}))
        cwd = root / module["path"] if module["path"] != "." else root
    for item in args.cmd:
        name, _, command = item.partition("=")
        if not command:
            parser.error(f"--cmd needs NAME=COMMAND, got {item!r}")
        commands[name.strip()] = command.strip()
    if not commands:
        parser.error("no commands: pass --profile or --cmd")

    wanted = [c.strip() for c in args.checks.split(",")] if args.checks else DEFAULT_CHECKS + [
        n for n in commands if n not in ORDER]
    if args.install:
        wanted = ["install"] + [w for w in wanted if w != "install"]
    selected = [n for n in sorted(commands, key=lambda n: ORDER.index(n) if n in ORDER else len(ORDER))
                if n in wanted]
    log_dir = Path(args.logs) if args.logs else (Path(args.out).parent / "logs" if args.out else None)

    results = []
    for name in selected:
        result = run(name, commands[name], cwd, args.timeout, args.tail, log_dir)
        results.append(result)
        if name == "install" and result["status"] != "PASS":
            break
    record = {"mode": "baseline" if args.baseline else "check", "module": str(cwd.relative_to(root)) or ".",
              "results": results,
              "skipped_checks": [n for n in wanted if n not in commands]}
    baseline = json.loads(Path(args.compare).read_text(encoding="utf-8")) if args.compare else None
    if baseline:
        record["regressions"] = regressions(results, baseline)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if args.md:
        sys.stdout.write(to_markdown(record, baseline))
    else:
        for result in results:
            print(f"[{result['status']}] {result['name']}: {result['command']} ({result['duration_s']}s): "
                  f"{describe(result)}")
            if result["status"] != "PASS":
                print("    " + "\n    ".join(result["tail"]))
        for problem in record.get("regressions", []):
            print(f"[REGRESSION] {problem}")
        if record["skipped_checks"]:
            print(f"[NOT APPLICABLE] no command for: {', '.join(record['skipped_checks'])}")
    if args.baseline:
        return 0
    failed = any(r["status"] != "PASS" for r in results) or bool(record.get("regressions"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
