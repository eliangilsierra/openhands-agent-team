#!/usr/bin/env python3
"""Summarise the team's usage ledger: who spent how much, when, where and with which model.

The ledger (~/.claude/usage/ledger.jsonl, written by the usage-ledger hook, Issue #19) has one line per
subagent run and per coordinator turn, with numbers and identifiers only. cost_usd is an API-equivalent
estimate (config/model-pricing.yaml): the subscription is not billed per token.

Usage:
    python usage_report.py [--by agent|model|item|repo|day|stage] [--since 2026-10-01] [--repo owner/name]
                           [--item 43] [--format table|json|github] [--ledger FILE]

`--format github` prints one short line (under 200 characters) for a Checkpoint or feature Issue comment;
the detailed breakdown stays local.

Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

FIELDS = ("runs", "duration_s", "calls", "tool_calls", "compactions", "input", "output", "cache_read",
          "cache_write", "cost_usd")


def default_ledger() -> Path:
    base = os.environ.get("TEAM_USAGE_DIR") or str(Path.home() / ".claude" / "usage")
    return Path(base) / "ledger.jsonl"


def load(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def select(records: list[dict], since: str | None, repo: str | None, item: int | None) -> list[dict]:
    out = []
    for record in records:
        if since and (record.get("end") or record.get("ts") or "") < since:
            continue
        if repo and record.get("repo") != repo:
            continue
        if item is not None and record.get("item") != item:
            continue
        out.append(record)
    return out


def keys_of(record: dict, by: str) -> list[str]:
    if by == "model":
        return list((record.get("models") or {"unknown": 1}).keys())
    if by == "day":
        return [(record.get("end") or record.get("ts") or "unknown")[:10]]
    if by == "item":
        return [f"#{record['item']}" if record.get("item") else "(coordination)"]
    return [str(record.get(by) or "unknown")]


def aggregate(records: list[dict], by: str) -> dict[str, dict]:
    groups: dict[str, dict] = defaultdict(lambda: dict.fromkeys(FIELDS, 0))
    for record in records:
        keys = keys_of(record, by)
        share = 1 / len(keys)  # a run that used two models is split evenly between them
        for key in keys:
            group = groups[key]
            group["runs"] += share
            for field in ("duration_s", "calls", "tool_calls", "compactions", "cost_usd"):
                group[field] += (record.get(field) or 0) * share
            for field in ("input", "output", "cache_read", "cache_write"):
                group[field] += (record.get("tokens") or {}).get(field, 0) * share
    return dict(groups)


def totals(records: list[dict]) -> dict:
    """All records as one group (a run with two models still counts as one run)."""
    return aggregate([dict(r, kind="all") for r in records], "kind").get("all", dict.fromkeys(FIELDS, 0))


def human(n: float) -> str:
    for unit, size in (("M", 1e6), ("K", 1e3)):
        if n >= size:
            return f"{n / size:.1f}{unit}"
    return f"{n:.0f}"


def table(groups: dict[str, dict], by: str) -> str:
    rows = [f"| {by} | runs | minutes | tokens | cache read | output | API-eq USD |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for key, g in sorted(groups.items(), key=lambda kv: -kv[1]["cost_usd"]):
        tokens = g["input"] + g["output"] + g["cache_read"] + g["cache_write"]
        share = g["cache_read"] / tokens if tokens else 0
        rows.append(f"| {key} | {g['runs']:.0f} | {g['duration_s'] / 60:.0f} | {human(tokens)} | {share:.0%} | "
                    f"{human(g['output'])} | {g['cost_usd']:.2f} |")
    return "\n".join(rows) + "\n"


def github_line(records: list[dict], scope: str) -> str:
    total = totals(records)
    tokens = total["input"] + total["output"] + total["cache_read"] + total["cache_write"]
    share = total["cache_read"] / tokens if tokens else 0
    models = aggregate(records, "model")
    mix = ", ".join(f"{m.replace('claude-', '')} {g['runs']:.0f}" for m, g in sorted(models.items(), key=lambda kv: -kv[1]["runs"])[:3])
    line = (f"Usage{scope}: {total['runs']:.0f} runs, {total['duration_s'] / 60:.0f} min, {human(tokens)} tokens "
            f"({share:.0%} cache), {mix}, ~${total['cost_usd']:.2f} API-eq")
    return line[:199]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--by", choices=("agent", "model", "item", "repo", "day", "stage", "kind"), default="agent")
    parser.add_argument("--since", help="ISO date, for example 2026-10-01")
    parser.add_argument("--repo", help="owner/name")
    parser.add_argument("--item", type=int, help="Issue or Pull Request number")
    parser.add_argument("--format", choices=("table", "json", "github"), default="table")
    args = parser.parse_args(argv)
    records = select(load(args.ledger or default_ledger()), args.since, args.repo, args.item)
    if args.format == "github":
        scope = f" #{args.item}" if args.item else (f" {args.repo}" if args.repo else "")
        print(github_line(records, scope) if records else f"Usage{scope}: no runs recorded")
    elif args.format == "json":
        print(json.dumps({"by": args.by, "groups": aggregate(records, args.by), "total": totals(records)}, indent=2))
    else:
        sys.stdout.write(table(aggregate(records, args.by), args.by) if records else "No runs in the ledger for this filter.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
