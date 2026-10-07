#!/usr/bin/env python3
"""Keep a work item's checkpoint current and mirror it to GitHub (AGENTS.md section 16).

The checkpoint is `.agent-state/items/<n>.md`, rendered from `.agent-state/items/<n>.json`.
Every call merges the given fields; --done appends a step. --mirror creates or edits, in
place, the one comment on the Issue or Pull Request that starts with
`**Checkpoint** · <role>`, so another agent can continue if this one is stopped.

Usage:
    python checkpoint.py --item 43 --role Developer --goal "Reject login after 5 failures" \
        --branch feature/43-login-throttle --next "write the regression test"
    python checkpoint.py --item 43 --done "baseline: 405 passed" --commit abc1234 \
        --validation .agent-state/items/43-checks.json --mirror
    python checkpoint.py --item 43 --show

Python 3.10+, standard library only (gh is used only with --mirror).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import tempfile
from pathlib import Path

FIELDS = ["goal", "role", "branch", "pull_request", "last_commit", "next", "model", "attempt"]


def paths(state_dir: Path, item: int) -> tuple[Path, Path]:
    folder = state_dir / "items"
    return folder / f"{item}.json", folder / f"{item}.md"


def load(path: Path) -> dict:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"done": [], "blockers": [], "validation": []}


def summarise_validation(file: Path) -> list[str]:
    """Lines 'name: STATUS (command)' from a run_checks.py JSON record."""
    record = json.loads(file.read_text(encoding="utf-8"))
    lines = []
    for result in record.get("results", []):
        counts = result.get("counts") or {}
        detail = f", {counts['passed']} passed, {counts['failed']} failed" if "passed" in counts else ""
        lines.append(f"{result['name']}: {result['status']}{detail} (`{result['command']}`)")
    lines += [f"regression: {r}" for r in record.get("regressions", [])]
    return lines


def render(item: int, data: dict) -> str:
    role = data.get("role", "Developer")
    out = [f"**Checkpoint** · {role} · item #{item} · updated {data.get('updated', '')}", ""]
    labels = {"goal": "Goal", "branch": "Branch", "pull_request": "Pull Request", "last_commit": "Last pushed commit",
              "next": "Next step", "model": "Model", "attempt": "Attempt"}
    for key, label in labels.items():
        if data.get(key):
            out.append(f"- **{label}:** {data[key]}")
    out += ["", "**Done**", ""] + ([f"- [x] {step}" for step in data.get("done", [])] or ["- none yet"])
    if data.get("validation"):
        out += ["", "**Validation**", ""] + [f"- {line}" for line in data["validation"]]
    if data.get("blockers"):
        out += ["", "**Blockers**", ""] + [f"- {b}" for b in data["blockers"]]
    return "\n".join(out) + "\n"


def gh(*args: str, stdin: str | None = None) -> str:
    result = subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f"error: gh {' '.join(args[:3])}: {result.stderr.strip()}")
    return result.stdout


def mirror(item: int, role: str, body: str, repo: str | None) -> str:
    repo = repo or gh("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner").strip()
    header = f"**Checkpoint** · {role}"
    comments = json.loads(gh("api", f"repos/{repo}/issues/{item}/comments", "--paginate", "--slurp") or "[]")
    flat = [c for page in comments for c in (page if isinstance(page, list) else [page])]
    existing = next((c for c in flat if str(c.get("body", "")).startswith(header)), None)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        json.dump({"body": body}, handle)
        payload = handle.name
    try:
        if existing:
            gh("api", "-X", "PATCH", f"repos/{repo}/issues/comments/{existing['id']}", "--input", payload)
            return f"edited comment {existing['html_url']}"
        created = json.loads(gh("api", "-X", "POST", f"repos/{repo}/issues/{item}/comments", "--input", payload))
        return f"created comment {created.get('html_url')}"
    finally:
        Path(payload).unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--item", type=int, required=True, help="Issue or Pull Request number")
    parser.add_argument("--state-dir", default=".agent-state")
    for field in FIELDS:
        parser.add_argument(f"--{field.replace('_', '-')}", dest=field)
    parser.add_argument("--commit", dest="last_commit", help="alias of --last-commit")
    parser.add_argument("--done", action="append", default=[], help="append a finished step")
    parser.add_argument("--blocker", action="append", default=[], help="append a blocker")
    parser.add_argument("--clear-blockers", action="store_true")
    parser.add_argument("--validation", help="run_checks.py JSON record to summarise")
    parser.add_argument("--mirror", action="store_true", help="create or edit the Checkpoint comment on GitHub")
    parser.add_argument("--repo", help="owner/repo for --mirror (default: the current repository)")
    parser.add_argument("--show", action="store_true", help="print the checkpoint and exit")
    args = parser.parse_args(argv)

    json_path, md_path = paths(Path(args.state_dir), args.item)
    data = load(json_path)
    if args.show:
        sys.stdout.write(render(args.item, data) if data.get("updated") else "no checkpoint yet\n")
        return 0
    for field in FIELDS:
        value = getattr(args, field)
        if value:
            data[field] = value
    data["done"] = data.get("done", []) + [d for d in args.done if d not in data.get("done", [])]
    if args.clear_blockers:
        data["blockers"] = []
    data["blockers"] = data.get("blockers", []) + args.blocker
    if args.validation:
        data["validation"] = summarise_validation(Path(args.validation))
    data["updated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    body = render(args.item, data)
    md_path.write_text(body, encoding="utf-8")
    print(f"checkpoint written: {md_path}")
    if args.mirror:
        print(mirror(args.item, data.get("role", "Developer"), body, args.repo))
    return 0


if __name__ == "__main__":
    sys.exit(main())
