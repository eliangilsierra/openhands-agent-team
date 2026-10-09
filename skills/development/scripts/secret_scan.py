#!/usr/bin/env python3
"""Find secrets and private data in text, using the team's single pattern policy.

The policy is secret-patterns.tsv next to this file, generated from config/secret-patterns.tsv of the
team repository. Findings name the rule and the line, never the matched value.

Scopes:
    secret   tokens, keys, credentials: never in files, commits or anything published
    private  emails, phone numbers, private IPs, personal home paths, card numbers: never in text
             published to GitHub (Issues, Pull Requests, comments, reviews)

Usage:
    python secret_scan.py [--scope secret|private|all] [FILE ...]   (stdin when no file is given)
    python secret_scan.py --scope all .agent-state/items/43-pr.md   before publishing a body by hand

Exit code: 0 clean, 1 findings, 2 usage error. Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

POLICY = Path(__file__).resolve().parent / "secret-patterns.tsv"
SCOPES = ("secret", "private")


@dataclass(frozen=True)
class Rule:
    id: str
    scope: str
    regex: re.Pattern
    strict: bool
    luhn: bool


@dataclass(frozen=True)
class Allow:
    id: str
    scopes: tuple[str, ...]
    regex: re.Pattern


@dataclass(frozen=True)
class Finding:
    rule: str
    scope: str
    line: int


def load_policy(path: Path = POLICY) -> tuple[list[Rule], list[Allow]]:
    rules: list[Rule] = []
    allows: list[Allow] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip() or raw.startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) != 4:
            raise ValueError(f"{path.name}:{number}: expected 4 tab-separated columns")
        rule_id, scope, flags_text, pattern = parts
        flags = set() if flags_text == "-" else set(flags_text.split(","))
        compiled = re.compile(pattern, re.IGNORECASE if "i" in flags else 0)
        if scope == "allow":
            allows.append(Allow(rule_id, tuple(s for s in SCOPES if s in flags) or SCOPES, compiled))
        elif scope in SCOPES:
            rules.append(Rule(rule_id, scope, compiled, "strict" in flags, "luhn" in flags))
        else:
            raise ValueError(f"{path.name}:{number}: unknown scope {scope!r}")
    return rules, allows


_POLICY: tuple[list[Rule], list[Allow]] | None = None


def policy() -> tuple[list[Rule], list[Allow]]:
    global _POLICY
    if _POLICY is None:
        _POLICY = load_policy()
    return _POLICY


def luhn_ok(text: str) -> bool:
    digits = [int(c) for c in text if c.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for index, digit in enumerate(reversed(digits)):
        if index % 2:
            digit *= 2
            digit -= 9 if digit > 9 else 0
        total += digit
    return total % 10 == 0


def _real(rule: Rule, match: str, allows: list[Allow]) -> bool:
    if rule.luhn and not luhn_ok(match):
        return False
    if rule.strict:
        return True
    return not any(rule.scope in a.scopes and a.regex.search(match) for a in allows)


def matches(text: str, scopes: tuple[str, ...] = ("secret",)):
    """Yield (rule, match object) for every real finding."""
    rules, allows = policy()
    for rule in rules:
        if rule.scope not in scopes:
            continue
        for match in rule.regex.finditer(text):
            if _real(rule, match.group(0), allows):
                yield rule, match


def scan(text: str, scopes: tuple[str, ...] = ("secret",)) -> list[Finding]:
    found = {Finding(rule.id, rule.scope, text.count("\n", 0, match.start()) + 1)
             for rule, match in matches(text, scopes)}
    return sorted(found, key=lambda f: (f.line, f.rule))


def redact(text: str, scopes: tuple[str, ...] = ("secret",)) -> str:
    spans = sorted(((m.start(), m.end(), r.id) for r, m in matches(text, scopes)), reverse=True)
    last_start = len(text) + 1
    for start, end, rule_id in spans:
        if end > last_start:  # overlapping matches: keep the outermost replacement only
            continue
        text = text[:start] + f"[REDACTED:{rule_id}]" + text[end:]
        last_start = start
    return text


def describe(findings: list[Finding], source: str = "text") -> str:
    return "; ".join(f"{source}:{f.line} {f.rule} ({f.scope})" for f in findings)


def refuse_if_found(text: str, what: str, scopes: tuple[str, ...] = SCOPES) -> None:
    """Exit with an explanation instead of publishing text that contains findings."""
    findings = scan(text, scopes)
    if findings:
        raise SystemExit(f"refusing to publish {what}: {describe(findings, what)}. Remove or redact the values "
                         f"(use placeholders such as <token> or example.org addresses) and try again.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", help="files to scan (stdin when none)")
    parser.add_argument("--scope", choices=("secret", "private", "all"), default="all")
    args = parser.parse_args(argv)
    scopes = SCOPES if args.scope == "all" else (args.scope,)
    sources = [(name, Path(name).read_text(encoding="utf-8", errors="replace")) for name in args.files] \
        or [("stdin", sys.stdin.read())]
    total = 0
    for name, text in sources:
        for finding in scan(text, scopes):
            print(f"{name}:{finding.line}: {finding.rule} ({finding.scope})")
            total += 1
    print(f"secret_scan: {total} finding(s)" if total else "secret_scan: clean")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
