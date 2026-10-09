#!/usr/bin/env python3
"""Review your own diff before every push: secrets, weakened tests, scope creep, debug code.

Secrets are detected with secret_scan.py (the team policy in secret-patterns.tsv).

Compares the working tree (committed and uncommitted changes) with the merge base of
--base (default: the integration branch, origin/HEAD) and reports findings:

    block   must be fixed before pushing (exit code 1), unless allowed with --allow <rule>
            and justified in the Pull Request
    warn    must be looked at; fix it or explain it in the Pull Request

Usage:
    python diff_guard.py [--base origin/develop] [--touches "src/api/**,tests/api/**"]
                         [--allow rule] [--json] [--diff-file FILE]

Secret values are never printed: only the file, the line and the kind of secret.
Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import branches  # noqa: E402  (sibling module: the integration branch, ADR-0004)
import secret_scan  # noqa: E402  (sibling module: the team's single pattern policy)

SECRET_FILES = re.compile(r"(^|/)(\.env(\.(?!example$|sample$|template$)[^/]+)?|id_rsa[^/]*|id_ed25519[^/]*|"
                          r"[^/]+\.(pem|key|p12|pfx|jks|keystore)|\.credentials\.json|credentials\.json)$", re.IGNORECASE)
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|specs|androidTest|testFixtures)/|"
                       r"(\.|_)(test|spec)\.[a-z]+$|(^|/)test_[^/]+\.py$|_test\.(go|py)$|(Test|Tests|Spec|IT)\.(java|kt|cs)$")
FOCUSED = re.compile(r"\b(?:it|describe|test|context)\.only\s*\(|\bf(?:it|describe)\s*\(|@pytest\.mark\.only\b")
SKIPPED = re.compile(r"\b(?:it|describe|test|context)\.skip\s*\(|\bx(?:it|describe|test)\s*\(|@Disabled\b|@Ignore\b|"
                     r"@pytest\.mark\.(?:skip|xfail)\b|\bpytest\.skip\s*\(|\bt\.Skip(?:Now|f)?\s*\(|\bSkip\s*=\s*\"|"
                     r"@unittest\.skip|\.t[o]do\s*\(")
CONFLICT = re.compile(r"^(<{7}|={7}|>{7})( |$)")
MARKER_WORDS = re.compile(r"\b(" + "TO" + "DO|FIX" + "ME|HA" + "CK|X" + "XX)\b")
DEBUG = {
    ".js": r"\bconsole\.(log|debug|trace)\s*\(|^\s*debugger\s*;?",
    ".ts": r"\bconsole\.(log|debug|trace)\s*\(|^\s*debugger\s*;?",
    ".py": r"^\s*print\s*\(|\bbreakpoint\s*\(\)|\bpdb\.set_trace\s*\(",
    ".java": r"System\.(out|err)\.print|\.printStackTrace\s*\(\)",
    ".kt": r"^\s*println\s*\(|\.printStackTrace\s*\(\)|\bLog\.d\s*\(",
    ".go": r"\bfmt\.Print(ln|f)?\s*\(|\bspew\.Dump\s*\(",
    ".cs": r"\bConsole\.Write(Line)?\s*\(|\bDebugger\.Break\s*\(",
}
DEBUG.update({".tsx": DEBUG[".ts"], ".jsx": DEBUG[".js"], ".mjs": DEBUG[".js"], ".vue": DEBUG[".ts"],
              ".kts": DEBUG[".kt"]})
COMMENTED_CODE = re.compile(r"^\s*(//|#)\s*([\w.]+\s*\(.*\)\s*;?|(const|let|var|val|return|if|for|import|def|public|private)\b.*[;{)]$)")
LARGE_FILE_BYTES = 1_000_000
LOCKFILES = {"package-lock.json": "package.json", "pnpm-lock.yaml": "package.json", "yarn.lock": "package.json",
             "poetry.lock": "pyproject.toml", "uv.lock": "pyproject.toml", "go.sum": "go.mod",
             "gradle.lockfile": "build.gradle.kts"}


@dataclass
class Finding:
    rule: str
    severity: str
    file: str
    line: int | None
    message: str


@dataclass
class FileDiff:
    path: str
    status: str = "modified"          # added | deleted | modified | renamed
    binary: bool = False
    added: list = None                 # list of (line number, text)

    def __post_init__(self):
        self.added = self.added or []


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, errors="replace", check=False)
    if result.returncode != 0:
        raise SystemExit(f"error: git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def parse_diff(text: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    current: FileDiff | None = None
    line_no = 0
    for raw in text.splitlines():
        if raw.startswith("diff --git "):
            match = re.match(r"diff --git a/(.*) b/(.*)$", raw)
            current = FileDiff(path=match.group(2) if match else raw.split()[-1])
            files.append(current)
        elif current is None:
            continue
        elif raw.startswith("new file mode"):
            current.status = "added"
        elif raw.startswith("deleted file mode"):
            current.status = "deleted"
        elif raw.startswith("rename to "):
            current.status = "renamed"
        elif raw.startswith("Binary files"):
            current.binary = True
        elif raw.startswith("+++ ") or raw.startswith("--- "):
            if raw.startswith("+++ b/"):
                current.path = raw[6:]
        elif raw.startswith("@@"):
            match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", raw)
            line_no = int(match.group(1)) if match else 0
        elif raw.startswith("+"):
            current.added.append((line_no, raw[1:]))
            line_no += 1
        elif raw.startswith(" "):
            line_no += 1
    return files


def in_touches(path: str, touches: list[str]) -> bool:
    for pattern in touches:
        pattern = pattern.strip().lstrip("./")
        if fnmatch.fnmatch(path, pattern) or path.startswith(pattern.rstrip("*").rstrip("/") + "/") \
                or path == pattern:
            return True
    return False


def extension(path: str) -> str:
    match = re.search(r"\.[A-Za-z0-9]+$", path)
    return match.group(0).lower() if match else ""


def scan(files: list[FileDiff], touches: list[str], sizes: dict[str, int] | None = None) -> list[Finding]:
    sizes = sizes or {}
    findings: list[Finding] = []
    changed = {f.path for f in files}
    for diff in files:
        path, is_test = diff.path, bool(TEST_PATH.search(diff.path))
        if SECRET_FILES.search(path) and diff.status != "deleted":
            findings.append(Finding("secret-file", "block", path, None, "secret-bearing file type must never be committed"))
        if "/.github/workflows/" in f"/{path}" and diff.status != "deleted":
            findings.append(Finding("workflow-change", "block", path, None,
                                    "workflow files change only when the task Issue explicitly asks for it"))
        if touches and not in_touches(path, touches):
            findings.append(Finding("out-of-scope", "block", path, None,
                                    "file is outside the task's Touches; revert it or record it as a follow-up"))
        if is_test and diff.status == "deleted":
            findings.append(Finding("test-deleted", "block", path, None,
                                    "an existing test file was deleted; never remove tests to get green"))
        if sizes.get(path, 0) > LARGE_FILE_BYTES:
            findings.append(Finding("large-file", "block", path, None,
                                    f"file is {sizes[path] // 1024} KiB; generated artefacts and binaries do not belong in the diff"))
        if path.split("/")[-1] in LOCKFILES:
            manifest = LOCKFILES[path.split("/")[-1]]
            sibling = "/".join(path.split("/")[:-1] + [manifest])
            if sibling not in changed and manifest not in changed:
                findings.append(Finding("lockfile-only", "warn", path, None,
                                        f"lockfile changed without {manifest}; make sure no unplanned dependency moved"))
        debug = re.compile(DEBUG[extension(path)]) if extension(path) in DEBUG and not is_test else None
        for number, text in diff.added:
            for found in secret_scan.scan(text, ("secret",)):
                findings.append(Finding("secret", "block", path, number, f"possible {found.rule} (value not shown)"))
            if CONFLICT.match(text):
                findings.append(Finding("conflict-marker", "block", path, number, "unresolved merge conflict marker"))
            if FOCUSED.search(text):
                findings.append(Finding("focused-test", "block", path, number, "focused test runs only part of the suite"))
            if SKIPPED.search(text):
                findings.append(Finding("skipped-test", "block", path, number,
                                        "a test was skipped or marked expected-failure; never weaken tests to get green"))
            if debug and debug.search(text):
                findings.append(Finding("debug-statement", "warn", path, number, f"debug output: {text.strip()[:80]}"))
            if MARKER_WORDS.search(text):
                findings.append(Finding("marker-comment", "warn", path, number,
                                        "unfinished-work marker; finish it or open a follow-up Issue"))
            if COMMENTED_CODE.match(text) and extension(path) not in (".md", ".yml", ".yaml", ".toml", ".sh", ""):
                findings.append(Finding("commented-code", "warn", path, number, "commented-out code"))
    return findings


def collect(base: str) -> tuple[str, dict[str, int], list[str]]:
    merge_base = git("merge-base", base, "HEAD").strip()
    diff = git("diff", "--no-color", "--unified=0", "--find-renames", merge_base)
    untracked = [p for p in git("ls-files", "--others", "--exclude-standard").splitlines() if p]
    sizes = {}
    for path in [f.path for f in parse_diff(diff)] + untracked:
        try:
            with open(path, "rb") as handle:
                handle.seek(0, 2)
                sizes[path] = handle.tell()
        except OSError:
            pass
    return diff, sizes, untracked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", help="branch the Pull Request targets (default: the integration branch, origin/HEAD)")
    parser.add_argument("--touches", default="", help="comma-separated globs from the task's Touches line")
    parser.add_argument("--allow", action="append", default=[], help="rule to downgrade to warn (justify it in the PR)")
    parser.add_argument("--diff-file", help="read a unified diff from this file instead of git (tests, CI)")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    args = parser.parse_args(argv)

    if args.diff_file:
        with open(args.diff_file, encoding="utf-8") as handle:
            diff, sizes, untracked = handle.read(), {}, []
    else:
        diff, sizes, untracked = collect(args.base or branches.integration_ref())
    touches = [t.strip() for t in args.touches.split(",") if t.strip()]
    findings = scan(parse_diff(diff), touches, sizes)
    for path in untracked:
        findings.append(Finding("untracked", "warn", path, None, "untracked file: add it to the commit or delete it"))
    for finding in findings:
        if finding.severity == "block" and finding.rule in args.allow:
            finding.severity = "warn"
            finding.message += " (allowed with --allow: justify it in the Pull Request)"
    blocking = [f for f in findings if f.severity == "block"]

    if args.json:
        print(json.dumps({"blocking": len(blocking), "findings": [asdict(f) for f in findings]}, indent=2))
    else:
        for finding in sorted(findings, key=lambda f: (f.severity != "block", f.file, f.line or 0)):
            where = f"{finding.file}:{finding.line}" if finding.line else finding.file
            print(f"[{finding.severity.upper()}] {finding.rule} {where}: {finding.message}")
        print(f"diff_guard: {len(blocking)} blocking, {len(findings) - len(blocking)} warnings")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
