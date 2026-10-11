#!/usr/bin/env python3
"""Check color contrast against WCAG 2.2: text (AA 4.5:1, AAA 7:1; large text AA 3:1, AAA 4.5:1)
and non-text UI components and graphics (AA 3:1).

Colors are hex (#RGB, #RRGGBB, #AARRGGBB as used by Compose Color(0xAARRGGBB), or 0xAARRGGBB). A
foreground with transparency is blended over the background first.

Usage:
    python contrast.py "#1A73E8" "#FFFFFF"
    python contrast.py 0xFF6750A4 0xFFFFFBFE --json
    python contrast.py --pairs pairs.csv          # CSV rows: name,foreground,background

Exit code: 0 when every pair passes AA for normal text, 1 otherwise.
Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys

HEX = re.compile(r"^(?:#|0x)?([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def parse(color: str) -> tuple[float, float, float, float]:
    """(r, g, b, alpha) in 0..1. Eight digits are AARRGGBB (Android and Compose order)."""
    match = HEX.match(color.strip())
    if not match:
        raise ValueError(f"not a hex color: {color!r}")
    digits = match.group(1)
    if len(digits) == 3:
        digits = "".join(c * 2 for c in digits)
    alpha = 1.0
    if len(digits) == 8:
        alpha, digits = int(digits[:2], 16) / 255, digits[2:]
    r, g, b = (int(digits[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return r, g, b, alpha


def blend(fg: tuple, bg: tuple) -> tuple[float, float, float]:
    alpha = fg[3]
    return tuple(fg[i] * alpha + bg[i] * (1 - alpha) for i in range(3))


def luminance(rgb: tuple[float, float, float]) -> float:
    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(foreground: str, background: str) -> float:
    bg = parse(background)
    if bg[3] < 1:
        raise ValueError("the background must be opaque")
    lighter, darker = sorted((luminance(blend(parse(foreground), bg)), luminance(bg[:3])), reverse=True)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def verdict(value: float) -> dict:
    return {
        "ratio": value,
        "text_aa": value >= 4.5, "text_aaa": value >= 7.0,
        "large_text_aa": value >= 3.0, "large_text_aaa": value >= 4.5,
        "non_text_aa": value >= 3.0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("foreground", nargs="?")
    parser.add_argument("background", nargs="?")
    parser.add_argument("--pairs", help="CSV file with name,foreground,background rows")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    pairs = []
    if args.pairs:
        with open(args.pairs, encoding="utf-8", newline="") as handle:
            pairs = [(row[0], row[1], row[2]) for row in csv.reader(handle) if len(row) >= 3 and not row[0].startswith("#")]
    elif args.foreground and args.background:
        pairs = [("pair", args.foreground, args.background)]
    else:
        parser.error("give a foreground and a background, or --pairs")
    results = []
    for name, fg, bg in pairs:
        try:
            results.append({"name": name, "foreground": fg, "background": bg, **verdict(ratio(fg, bg))})
        except ValueError as error:
            parser.error(f"{name}: {error}")
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            marks = ", ".join(f"{k} {'PASS' if r[k] else 'FAIL'}" for k in ("text_aa", "large_text_aa", "non_text_aa", "text_aaa"))
            print(f"{r['name']}: {r['foreground']} on {r['background']} = {r['ratio']}:1 ({marks})")
    return 0 if all(r["text_aa"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
