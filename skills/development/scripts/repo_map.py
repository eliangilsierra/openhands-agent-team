#!/usr/bin/env python3
"""Print a compact map of a repository: files and the symbols they declare.

Orientation in a few thousand characters instead of reading whole files: classes,
interfaces, functions, exported constants and public methods per file, for
TypeScript/JavaScript, Java, Kotlin, Python, Go, C# and Vue. Test files are marked.

Usage:
    python repo_map.py [ROOT] [--focus "src/orders/**,src/api/**"] [--max-chars 12000]

Focus globs are listed first and in full; the rest is filled until --max-chars.
Uses `git ls-files` when ROOT is a git repository (respects .gitignore).
Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

PATTERNS = {
    "ts": [
        r"^\s*export\s+(?:default\s+)?(?:abstract\s+)?(?:async\s+)?(?:function\*?|class|interface|type|enum|const|let)\s+([A-Za-z_$][\w$]*)",
        r"^(?:abstract\s+)?(?:class|interface|enum)\s+([A-Za-z_$][\w$]*)",
        r"^(?:async\s+)?function\*?\s+([A-Za-z_$][\w$]*)",
        r"^\s*@(Component|Injectable|NgModule|Directive|Pipe|Controller|Module)\b",
    ],
    "java": [
        r"^\s*(?:public|protected|private)?\s*(?:abstract\s+|final\s+|sealed\s+|static\s+)*(?:class|interface|enum|record|@interface)\s+(\w+)",
        r"^\s+(?:public|protected)\s+(?:static\s+|final\s+|abstract\s+|synchronized\s+|default\s+)*[\w<>\[\],.? ]+\s+(\w+)\s*\(",
        r"^\s*@(RestController|Controller|Service|Repository|Component|Configuration|Entity|SpringBootApplication)\b",
    ],
    "kotlin": [
        r"^\s*(?:public\s+|internal\s+|private\s+)?(?:data\s+|sealed\s+|abstract\s+|open\s+|enum\s+|value\s+|annotation\s+)*(?:class|interface|object)\s+(\w+)",
        r"^\s*(?:public\s+|internal\s+|override\s+|suspend\s+|inline\s+|operator\s+)*fun\s+(?:<[^>]+>\s*)?(?:[\w.]+\.)?(\w+)\s*\(",
        r"^\s*@(Composable|HiltViewModel|Entity|Dao|Module|AndroidEntryPoint)\b",
    ],
    "python": [
        r"^class\s+(\w+)",
        r"^(?:async\s+)?def\s+(\w+)",
        r"^    (?:async\s+)?def\s+((?!_)\w+)",
        r"^([A-Z][A-Z0-9_]+)\s*[:=]",
    ],
    "go": [
        r"^func\s+(?:\([^)]*\)\s+)?([A-Z]\w*)",
        r"^type\s+(\w+)\s+(?:struct|interface|func|\w)",
    ],
    "csharp": [
        r"^\s*(?:public|internal)\s+(?:static\s+|sealed\s+|abstract\s+|partial\s+)*(?:class|interface|record|struct|enum)\s+(\w+)",
        r"^\s+public\s+(?:static\s+|virtual\s+|override\s+|async\s+)*[\w<>\[\],.? ]+\s+(\w+)\s*\(",
    ],
}
LANGUAGE = {".ts": "ts", ".tsx": "ts", ".js": "ts", ".jsx": "ts", ".mjs": "ts", ".vue": "ts", ".java": "java",
            ".kt": "kotlin", ".kts": "kotlin", ".py": "python", ".go": "go", ".cs": "csharp"}
SKIP = re.compile(r"(^|/)(node_modules|dist|build|target|out|\.next|\.nuxt|coverage|vendor|bin|obj|\.gradle|"
                  r"__pycache__|\.venv|venv|generated|migrations)/|\.min\.js$|\.d\.ts$")
TEST = re.compile(r"(^|/)(tests?|__tests__|spec|androidTest)/|(\.|_)(test|spec)\.\w+$|(^|/)test_\w+\.py$|"
                  r"_test\.go$|(Test|Tests|IT)\.(java|kt|cs)$")
COMPILED = {lang: [re.compile(p) for p in pats] for lang, pats in PATTERNS.items()}


def list_files(root: Path) -> list[str]:
    result = subprocess.run(["git", "-C", str(root), "ls-files"], capture_output=True, text=True, check=False)
    if result.returncode == 0 and result.stdout.strip():
        return sorted(result.stdout.splitlines())
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


def symbols(path: Path, language: str, limit: int = 25) -> list[str]:
    found: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return found
    for line in lines:
        for pattern in COMPILED[language]:
            match = pattern.match(line)
            if match:
                name = match.group(1)
                name = f"@{name}" if pattern.pattern.lstrip("^\\s*").startswith("@") else name
                if name not in found and name not in ("if", "for", "while", "switch", "return", "new"):
                    found.append(name)
                break
        if len(found) >= limit:
            found.append("…")
            break
    return found


def build(root: Path, focus: list[str], max_chars: int) -> str:
    files = [f for f in list_files(root) if Path(f).suffix.lower() in LANGUAGE and not SKIP.search(f)]
    focused = [f for f in files if any(fnmatch.fnmatch(f, g) or f.startswith(g.rstrip("*/") + "/") for g in focus)]
    rest = [f for f in files if f not in focused]
    out: list[str] = []
    size = 0
    omitted = 0
    for group, entries in (("focus", focused), ("repository", rest)):
        if not entries:
            continue
        header = f"## {group} ({len(entries)} files)"
        out.append(header)
        size += len(header) + 1
        for name in entries:
            names = symbols(root / name, LANGUAGE[Path(name).suffix.lower()])
            line = f"{name}{' [test]' if TEST.search(name) else ''}: {', '.join(names) if names else '-'}"
            if group == "repository" and size + len(line) + 1 > max_chars:
                omitted += 1
                continue
            out.append(line)
            size += len(line) + 1
    if omitted:
        out.append(f"... {omitted} more files omitted (raise --max-chars or use --focus)")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--focus", default="", help="comma-separated globs shown first and in full")
    parser.add_argument("--max-chars", type=int, default=12000)
    args = parser.parse_args(argv)
    focus = [g.strip().lstrip("./") for g in args.focus.split(",") if g.strip()]
    sys.stdout.write(build(Path(args.root).resolve(), focus, args.max_chars))
    return 0


if __name__ == "__main__":
    sys.exit(main())
