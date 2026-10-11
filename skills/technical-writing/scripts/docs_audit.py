#!/usr/bin/env python3
"""Audit a repository's README and docs/ against the team's documentation structure (ADR-0005).

Checks:
    structure       README.md, docs/README.md and the Diátaxis and architecture folders exist
    readme          the README has the required sections (overview, getting started, usage,
                    development, documentation, licence; alternative headings accepted)
    links           relative links and anchors in every Markdown file resolve
    orphans         every page under docs/ is linked from another Markdown file
    stale-paths     inline code that names a repository path (`src/app.ts`, `docs/x/`) exists
    mermaid         every mermaid block starts with a known diagram type

Errors (exit 1): missing required structure or README sections, broken links, invalid mermaid.
Warnings: orphans and stale paths.

Usage:
    python docs_audit.py [ROOT] [--json] [--only links,orphans]

Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_PATHS = ["README.md", "docs/README.md", "docs/tutorials", "docs/how-to", "docs/reference",
                  "docs/explanation", "docs/architecture", "docs/decisions"]
README_SECTIONS = {
    "overview": ("overview", "about", "what it is", "introduction"),
    "getting started": ("getting started", "quick start", "quickstart", "installation", "install", "setup"),
    "usage": ("usage", "using", "how to use", "examples"),
    "development": ("development", "contributing", "working on the project", "local development"),
    "documentation": ("documentation", "docs", "further reading"),
    "licence": ("license", "licence"),
}
MERMAID_TYPES = ("flowchart", "graph", "sequenceDiagram", "stateDiagram", "stateDiagram-v2", "classDiagram",
                 "erDiagram", "gantt", "pie", "journey", "gitGraph", "mindmap", "timeline", "C4Context",
                 "C4Container", "C4Component", "C4Dynamic", "C4Deployment", "quadrantChart", "architecture-beta")
SKIP_DIRS = {".git", "node_modules", ".agent-state", "dist", "build", "target", ".venv", "venv", "vendor"}
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)|!\[[^\]]*\]\(([^)\s]+)\)")
CODE_PATH = re.compile(r"`((?:[\w.-]+/)+[\w.-]*)`")
FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([\w-]*)")


def markdown_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.md") if not any(part in SKIP_DIRS for part in p.relative_to(root).parts))


def split(text: str) -> tuple[str, list[tuple[str, str, int]]]:
    """Prose without fenced blocks, and the blocks as (language, body, start line)."""
    prose, blocks, fence, lang, body, start = [], [], None, "", [], 0
    for number, line in enumerate(text.splitlines(), start=1):
        match = FENCE.match(line)
        if fence is None and match:
            fence, lang, body, start = match.group(2), match.group(3), [], number
            prose.append("")
        elif fence is not None and line.strip().startswith(fence):
            blocks.append((lang, "\n".join(body), start))
            fence = None
            prose.append("")
        elif fence is not None:
            body.append(line)
            prose.append("")
        else:
            prose.append(re.sub(r"`[^`]*`", lambda m: m.group(0) if CODE_PATH.fullmatch(m.group(0)) else "", line))
    return "\n".join(prose), blocks


def slug(heading: str) -> str:
    text = re.sub(r"[`*_~]", "", heading.strip().lower())
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    """GitHub-style heading anchors, read outside fenced blocks (inline code in headings is kept)."""
    found, counts, fence = set(), {}, None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = FENCE.match(line)
        if fence is None and match:
            fence = match.group(2)
            continue
        if fence is not None:
            fence = None if line.strip().startswith(fence) else fence
            continue
        match = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
        if match:
            base = slug(match.group(1))
            n = counts.get(base, 0)
            found.add(base if n == 0 else f"{base}-{n}")
            counts[base] = n + 1
    return found


def finding(kind: str, severity: str, where: str, message: str) -> dict:
    return {"check": kind, "severity": severity, "where": where, "message": message}


def audit(root: Path, only: set[str] | None = None) -> list[dict]:
    root = root.resolve()
    wanted = lambda check: only is None or check in only  # noqa: E731
    files = markdown_files(root)
    findings: list[dict] = []
    linked: set[Path] = set()

    if wanted("structure"):
        for required in REQUIRED_PATHS:
            if not (root / required).exists():
                findings.append(finding("structure", "error", required, "required documentation path is missing"))

    readme = root / "README.md"
    if wanted("readme") and readme.is_file():
        headings = [h.strip().lower() for h in re.findall(r"^#{2,3}\s+(.+)$", split(readme.read_text(encoding="utf-8"))[0], re.MULTILINE)]
        for section, names in README_SECTIONS.items():
            if section == "overview":
                continue  # the text under the title is the overview
            if not any(any(name in heading for name in names) for heading in headings):
                findings.append(finding("readme", "error", "README.md", f"missing a '{section}' section (one of: {', '.join(names)})"))

    for path in files:
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        prose, blocks = split(text)
        for match in LINK.finditer(prose):
            target = match.group(1) or match.group(2)
            if re.match(r"^[a-z][a-z0-9+.-]*:", target) or any(c in target for c in "<{$") or "NNNN" in target:
                continue  # external (https:, mailto:) or a template placeholder
            file_part, _, anchor = target.partition("#")
            destination = (path.parent / file_part).resolve() if file_part else path
            if file_part:
                linked.add(destination)
            if not wanted("links"):
                continue
            line = prose.count("\n", 0, match.start()) + 1
            if not destination.exists():
                findings.append(finding("links", "error", f"{rel}:{line}", f"broken link {target}"))
            elif anchor and destination.suffix == ".md" and anchor.lower() not in anchors(destination):
                findings.append(finding("links", "error", f"{rel}:{line}", f"missing anchor {target}"))
        if wanted("stale-paths"):
            for match in CODE_PATH.finditer(prose):
                candidate = match.group(1)
                if any(token in candidate for token in ("<", "*", "{", "$")) or candidate.startswith(("http", "~", "/", "./")):
                    continue
                # Only a path under an existing top-level directory can be stale; branch names such as
                # feature/ or runtime directories such as .agent-state/ are not repository paths.
                if not (root / candidate.split("/")[0]).is_dir():
                    continue
                if not (root / candidate).exists() and not (path.parent / candidate).exists():
                    line = prose.count("\n", 0, match.start()) + 1
                    findings.append(finding("stale-paths", "warning", f"{rel}:{line}", f"`{candidate}` does not exist in the repository"))
        if wanted("mermaid"):
            for lang, body, start in blocks:
                if lang == "mermaid":
                    first = next((l.strip() for l in body.splitlines() if l.strip() and not l.strip().startswith("%%")), "")
                    if not first.startswith(MERMAID_TYPES):
                        findings.append(finding("mermaid", "error", f"{rel}:{start}", f"unknown mermaid diagram type '{first[:30]}'"))

    if wanted("orphans"):
        for path in files:
            rel = path.relative_to(root).as_posix()
            if rel.startswith("docs/") and rel != "docs/README.md" and path.resolve() not in linked:
                findings.append(finding("orphans", "warning", rel, "not linked from any other page"))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--only", help="comma-separated checks: structure,readme,links,orphans,stale-paths,mermaid")
    args = parser.parse_args(argv)
    only = {c.strip() for c in args.only.split(",")} if args.only else None
    findings = audit(Path(args.root), only)
    errors = [f for f in findings if f["severity"] == "error"]
    if args.json:
        print(json.dumps({"errors": len(errors), "warnings": len(findings) - len(errors), "findings": findings}, indent=2))
    else:
        for f in findings:
            print(f"[{f['severity'].upper()}] {f['check']} {f['where']}: {f['message']}")
        print(f"docs_audit: {len(errors)} errors, {len(findings) - len(errors)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
