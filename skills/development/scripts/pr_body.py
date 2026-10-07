#!/usr/bin/env python3
"""Render a complete Pull Request body that follows .github/pull_request_template.md.

Every section is present ("None" when empty), the Tests table comes from run_checks.py
evidence, and only the checklist items that the evidence proves are ticked: the developer
reviews and ticks the rest by hand before marking the Pull Request ready.

Usage:
    python pr_body.py --issue 43 --part-of 40 --adr ADR-0007 \
        --summary "Reject login after 5 failed attempts in 15 minutes." \
        --change "auth: throttle failed logins" --change "api: return 429 with Retry-After" \
        --checks .agent-state/items/43-checks.json --baseline .agent-state/items/43-baseline.json \
        --guard-ok --interpretation "AC-1 has no status code; 429 matches api/errors.ts:88" \
        --out .agent-state/items/43-pr.md
    gh pr create --draft --title "feat(auth): reject login after 5 failed attempts (#43)" \
        --body-file .agent-state/items/43-pr.md

Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_checks  # noqa: E402  (sibling module)

BRANCH = re.compile(r"^(feature|bugfix|refactor|chore|docs)/(\d+)-[a-z0-9]+(-[a-z0-9]+){0,4}$")
CHECKLIST = [
    ("branch", "Branch follows `<prefix>/<issue-number>-<short-description>` and is not `main`"),
    ("scope", "The change is limited to the scope of the linked Issue"),
    ("criteria", "Every acceptance criterion is implemented and covered by a test"),
    ("checks", "Tests, lint and build pass locally; required CI checks are green"),
    ("secrets", "No secrets, credentials, `.env` files or personal data are included"),
    ("architecture", "Architecture and Accepted ADRs are respected, or a deviation is documented in an ADR"),
    ("docs", "Documentation is updated for any behaviour change"),
    ("diff", "I reviewed my own diff for debug code, unrelated changes and generated files"),
    ("human", "I understand that only a human code owner approves and merges this Pull Request"),
]


def current_branch() -> str:
    result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=False)
    return result.stdout.strip()


def section(title: str, body: str | list[str] | None) -> str:
    if isinstance(body, list):
        body = "\n".join(f"- {line}" for line in body) if body else None
    return f"## {title}\n\n{(body or 'None').strip()}\n"


def tests_table(checks: dict | None, baseline: dict | None, extra: list[str]) -> str:
    if not checks:
        table = "| Command | Result |\n| --- | --- |\n| Not run | BLOCKED - no run_checks.py record was given |\n"
    else:
        table = run_checks.to_markdown(checks, baseline)
    if extra:
        table += "\n" + "\n".join(f"- {line}" for line in extra) + "\n"
    return table


def render(args: argparse.Namespace, branch: str) -> str:
    checks = json.loads(Path(args.checks).read_text(encoding="utf-8")) if args.checks else None
    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8")) if args.baseline else None
    if checks and baseline:
        checks.setdefault("regressions", run_checks.regressions(checks["results"], baseline))
    match = BRANCH.match(branch)
    proven = {
        "branch": bool(match) and match.group(2) == str(args.issue),
        "checks": bool(checks) and all(r["status"] == "PASS" for r in checks["results"]) and not checks.get("regressions"),
        "secrets": args.guard_ok,
        "diff": args.guard_ok,
        "human": True,
    }
    related = f"Closes #{args.issue}"
    if args.part_of:
        related += f" · Part of #{args.part_of}"
    for adr in args.adr:
        related += f" · {adr}"
    summary = args.summary
    if args.interpretation:
        summary += "\n\n**Interpretation:** " + " ".join(args.interpretation)
    checklist = "\n".join(f"- [{'x' if proven.get(key) else ' '}] {text}" for key, text in CHECKLIST)
    parts = [
        section("Summary", summary),
        section("Related Issue", related),
        section("Changes", args.change),
        section("Architecture impact", args.architecture),
        section("Tests", tests_table(checks, baseline, args.test_note)),
        section("Security considerations", args.security),
        section("Documentation", args.docs),
        section("Breaking changes", args.breaking),
        section("Checklist", checklist),
    ]
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--issue", type=int, required=True, help="the task Issue this Pull Request closes")
    parser.add_argument("--part-of", type=int, help="parent feature Issue")
    parser.add_argument("--adr", action="append", default=[], help="ADR followed, for example ADR-0007")
    parser.add_argument("--summary", required=True, help="what the Pull Request does and why, two to four sentences")
    parser.add_argument("--interpretation", action="append", default=[], help="interpretation of an ambiguous criterion")
    parser.add_argument("--change", action="append", default=[], help="one bullet of the Changes section")
    parser.add_argument("--architecture", help="architecture impact (default None)")
    parser.add_argument("--checks", help="run_checks.py JSON record after the change")
    parser.add_argument("--baseline", help="run_checks.py --baseline JSON record")
    parser.add_argument("--test-note", action="append", default=[], help="extra Tests line (new tests, AC mapping)")
    parser.add_argument("--security", help="security considerations (default None)")
    parser.add_argument("--docs", help="documentation updated (default None)")
    parser.add_argument("--breaking", help="breaking changes (default None)")
    parser.add_argument("--guard-ok", action="store_true", help="diff_guard.py reported no blocking finding")
    parser.add_argument("--branch", help="branch name (default: the current git branch)")
    parser.add_argument("--out", help="write the body to this file")
    args = parser.parse_args(argv)
    body = render(args, args.branch or current_branch())
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(body, encoding="utf-8")
        print(f"Pull Request body written: {args.out}")
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
