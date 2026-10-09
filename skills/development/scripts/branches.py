#!/usr/bin/env python3
"""Resolve the repository's integration branch: the branch task Pull Requests target (ADR-0004).

It is the remote's default branch: `develop` in projects created from the project template, `main` in
single-branch projects. It is read from the repository, never assumed.

Usage:
    python branches.py            prints the remote ref, for example origin/develop
    python branches.py --name     prints only the branch name, for example develop

Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import subprocess
import sys


def _git(*args: str, cwd: str | None = None) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def integration_ref(cwd: str | None = None, remote: str = "origin") -> str:
    """`<remote>/<default branch>`; falls back to develop, then main, when origin/HEAD is not set."""
    head = _git("symbolic-ref", "--quiet", "--short", f"refs/remotes/{remote}/HEAD", cwd=cwd)
    if head:
        return head
    for candidate in ("develop", "main", "master"):
        if _git("rev-parse", "--verify", "--quiet", f"refs/remotes/{remote}/{candidate}", cwd=cwd):
            return f"{remote}/{candidate}"
    return f"{remote}/main"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--name", action="store_true", help="print the branch name without the remote")
    args = parser.parse_args(argv)
    ref = integration_ref()
    print(ref.split("/", 1)[1] if args.name else ref)
    return 0


if __name__ == "__main__":
    sys.exit(main())
