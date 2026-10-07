#!/usr/bin/env python3
"""List the tests related to the files a change touches, and the changed files without tests.

Relates a source file to tests by naming convention (foo.ts -> foo.test.ts / foo.spec.ts,
Foo.java -> FooTest.java / FooTests.java / FooIT.java, foo.py -> test_foo.py / foo_test.py,
foo.go -> foo_test.go, Foo.cs -> FooTests.cs) and by test files that mention the module
name. Use it to run the relevant tests first and to see which changes still lack tests.

Usage:
    python impact_scan.py [--base origin/main] [--files a.ts,b.ts] [--root .] [--json]

Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SOURCE = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".vue", ".java", ".kt", ".py", ".go", ".cs"}
TEST = re.compile(r"(^|/)(tests?|__tests__|spec|androidTest)/|(\.|_)(test|spec)\.\w+$|(^|/)test_\w+\.py$|"
                  r"_test\.go$|(Test|Tests|IT|Spec)\.(java|kt|cs)$")


def git(root: Path, *args: str) -> list[str]:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f"error: git {' '.join(args)}: {result.stderr.strip()}")
    return [line for line in result.stdout.splitlines() if line]


def changed_files(root: Path, base: str) -> list[str]:
    merge_base = git(root, "merge-base", base, "HEAD")[0]
    files = git(root, "diff", "--name-only", "--diff-filter=ACMR", merge_base)
    files += git(root, "ls-files", "--others", "--exclude-standard")
    return sorted(set(files))


def candidate_names(path: str) -> set[str]:
    stem, suffix = Path(path).stem, Path(path).suffix
    names = {f"{stem}.test{suffix}", f"{stem}.spec{suffix}", f"{stem}_test{suffix}", f"test_{stem}{suffix}",
             f"{stem}Test{suffix}", f"{stem}Tests{suffix}", f"{stem}IT{suffix}", f"{stem}Spec{suffix}"}
    if suffix in (".tsx", ".jsx", ".vue"):
        names |= {f"{stem}.test.ts", f"{stem}.spec.ts", f"{stem}.test.tsx", f"{stem}.spec.tsx",
                  f"{stem}.test.js", f"{stem}.spec.js"}
    return names


def related_tests(path: str, tests: list[str], root: Path, contents: dict[str, str]) -> list[str]:
    names = candidate_names(path)
    found = [t for t in tests if Path(t).name in names]
    stem = Path(path).stem
    if len(stem) > 3 and stem.lower() not in ("index", "main", "utils", "types", "init", "__init__"):
        word = re.compile(rf"\b{re.escape(stem)}\b")
        for test in tests:
            if test in found:
                continue
            if test not in contents:
                try:
                    contents[test] = (root / test).read_text(encoding="utf-8", errors="replace")[:20000]
                except OSError:
                    contents[test] = ""
            if word.search(contents[test]):
                found.append(test)
    return found[:15]


def scan(root: Path, changed: list[str]) -> dict:
    all_files = git(root, "ls-files") + git(root, "ls-files", "--others", "--exclude-standard")
    tests = sorted({f for f in all_files if TEST.search(f) and Path(f).suffix in SOURCE})
    contents: dict[str, str] = {}
    related, untested, changed_tests = {}, [], []
    for path in changed:
        if Path(path).suffix not in SOURCE:
            continue
        if TEST.search(path):
            changed_tests.append(path)
            continue
        found = related_tests(path, tests, root, contents)
        if found:
            related[path] = found
        else:
            untested.append(path)
    return {"changed_sources": sorted(set(related) | set(untested)), "changed_tests": changed_tests,
            "related_tests": related, "without_tests": untested,
            "tests_to_run": sorted({t for ts in related.values() for t in ts} | set(changed_tests))}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--files", help="comma-separated files instead of the git diff")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    changed = [f.strip() for f in args.files.split(",")] if args.files else changed_files(root, args.base)
    report = scan(root, changed)
    if args.json:
        print(json.dumps(report, indent=2))
        return 0
    for source, tests in report["related_tests"].items():
        print(f"{source}\n    tests: {', '.join(tests)}")
    for source in report["without_tests"]:
        print(f"{source}\n    tests: none found - add or extend a test, or explain why in the Pull Request")
    if report["changed_tests"]:
        print(f"changed tests: {', '.join(report['changed_tests'])}")
    print(f"run first: {' '.join(report['tests_to_run']) or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
