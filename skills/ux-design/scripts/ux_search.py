#!/usr/bin/env python3
"""Search the UX rule data and build checklists for a platform or stack.

Data: ../data/*.csv (general UX, web interface, charts, colors, typography) and ../data/stacks/*.csv
(react, nextjs, vue, nuxtjs, react-native, html-tailwind, shadcn and the team's jetpack-compose for
Android). Ranking is BM25 over every text column, so free-text queries work in any domain.

Usage:
    python ux_search.py "touch target button"                      # every domain, ranked
    python ux_search.py "list keys" --stack jetpack-compose
    python ux_search.py "form errors" --domain ux --platform mobile
    python ux_search.py --checklist --platform android              # High rules for an Android screen
    python ux_search.py --checklist --stack react --severity high,medium
    python ux_search.py --list                                      # domains, stacks and row counts

Platforms: web, mobile and android (android = mobile + jetpack-compose), plus all.
Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
DOMAINS = {"ux": "ux-guidelines.csv", "web": "web-interface.csv", "charts": "charts.csv",
           "colors": "colors.csv", "typography": "typography.csv"}
PLATFORM_ROWS = {"web": {"web", "all"}, "mobile": {"mobile", "all"}, "android": {"mobile", "all"},
                 "all": None}
PLATFORM_STACKS = {"android": ["jetpack-compose"], "mobile": ["jetpack-compose", "react-native"]}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
TOKEN = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def stacks() -> list[str]:
    return sorted(p.stem for p in (DATA / "stacks").glob("*.csv"))


def load(domain: str | None = None, stack: str | None = None) -> list[dict]:
    """Rows with their source; stack rows get domain 'stack:<name>'."""
    rows: list[dict] = []
    sources = []
    if stack:
        sources.append((f"stack:{stack}", DATA / "stacks" / f"{stack}.csv"))
    elif domain:
        sources.append((domain, DATA / DOMAINS[domain]))
    else:
        sources += [(name, DATA / file) for name, file in DOMAINS.items()]
        sources += [(f"stack:{name}", DATA / "stacks" / f"{name}.csv") for name in stacks()]
    for source, path in sources:
        if not path.is_file():
            raise SystemExit(f"error: unknown data file {path.name} (stacks: {', '.join(stacks())})")
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                rows.append({"source": source, **{k: (v or "").strip() for k, v in row.items() if k}})
    return rows


def matches_platform(row: dict, platform: str | None) -> bool:
    allowed = PLATFORM_ROWS.get(platform or "all")
    if allowed is None or not row.get("Platform"):
        return True
    return row["Platform"].lower() in allowed


def bm25(rows: list[dict], query: str, k1: float = 1.5, b: float = 0.75) -> list[tuple[float, dict]]:
    docs = [tokens(" ".join(v for k, v in row.items() if k != "source")) for row in rows]
    if not docs:
        return []
    average = sum(len(d) for d in docs) / len(docs)
    frequency = Counter(term for doc in docs for term in set(doc))
    terms = tokens(query)
    scored = []
    for doc, row in zip(docs, rows):
        counts = Counter(doc)
        score = 0.0
        for term in terms:
            if term not in counts:
                continue
            idf = math.log(1 + (len(docs) - frequency[term] + 0.5) / (frequency[term] + 0.5))
            tf = counts[term]
            score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(doc) / average))
        if score > 0:
            scored.append((score, row))
    return sorted(scored, key=lambda pair: -pair[0])


def title(row: dict) -> str:
    return row.get("Guideline") or row.get("Issue") or row.get("Data Type") or row.get("Product Type") \
        or row.get("Font Pairing Name") or row.get("Category", "")


def checklist(platform: str | None, stack: str | None, severities: set[str]) -> list[dict]:
    rows = [r for r in load("ux") if matches_platform(r, platform)]
    for name in ([stack] if stack else PLATFORM_STACKS.get(platform or "", [])):
        rows += load(stack=name)
    rows = [r for r in rows if r.get("Severity", "").lower() in severities]
    return sorted(rows, key=lambda r: (SEVERITY_ORDER.get(r.get("Severity", "").lower(), 9), r["source"], title(r)))


def render(rows: list[dict], as_json: bool) -> str:
    if as_json:
        return json.dumps(rows, indent=2, ensure_ascii=False) + "\n"
    lines = []
    for row in rows:
        lines.append(f"- [{row.get('Severity', '-')}] {title(row)} ({row['source']}, {row.get('Category', '')})")
        for label in ("Description", "Do", "Don't", "Code Good", "Docs URL"):
            if row.get(label):
                lines.append(f"    {label}: {row[label]}")
    return "\n".join(lines) + ("\n" if lines else "No rules matched.\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("query", nargs="?", default="", help="free-text query")
    parser.add_argument("--domain", choices=sorted(DOMAINS))
    parser.add_argument("--stack", help=f"one of: {', '.join(stacks())}")
    parser.add_argument("--platform", choices=sorted(PLATFORM_ROWS))
    parser.add_argument("--checklist", action="store_true", help="list rules by severity instead of searching")
    parser.add_argument("--severity", default="critical,high", help="checklist severities (default critical,high)")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--list", action="store_true", help="list domains and stacks with row counts")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.stack and args.stack not in stacks():
        parser.error(f"unknown stack {args.stack!r}; choose one of {', '.join(stacks())}")
    if args.list:
        for name in DOMAINS:
            print(f"domain {name}: {len(load(name))} rows")
        for name in stacks():
            print(f"stack {name}: {len(load(stack=name))} rows")
        return 0
    if args.checklist:
        severities = {s.strip().lower() for s in args.severity.split(",") if s.strip()}
        sys.stdout.write(render(checklist(args.platform, args.stack, severities), args.json))
        return 0
    if not args.query:
        parser.error("give a query, --checklist or --list")
    rows = [r for r in load(args.domain, args.stack) if matches_platform(r, args.platform)]
    if args.platform and not args.stack and not args.domain:
        for name in PLATFORM_STACKS.get(args.platform, []):
            rows = [r for r in rows if not r["source"].startswith("stack:") or r["source"] == f"stack:{name}"]
    results = [row for _, row in bm25(rows, args.query)[: args.limit]]
    sys.stdout.write(render(results, args.json))
    return 0


if __name__ == "__main__":
    sys.exit(main())
