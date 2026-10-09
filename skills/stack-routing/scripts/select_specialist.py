#!/usr/bin/env python3
"""Choose the Developer specialist for one task from the stack profile and the task's Touches.

Usage:
    python select_specialist.py --profile PROFILE.json --touches "src/api/**,src/db/**"
    python select_specialist.py --profile PROFILE.json --issue 43 [--repo owner/repo]
    python select_specialist.py --root . --summary

Decisions (printed as JSON):
    explicit   the task carries a valid "Stack: <specialist>" line; it wins
    single     every touched module belongs to one specialist
    split      the task touches modules of several specialists: the Planner should split it;
               until then the generalist "developer" runs it with every stack skill involved
    fallback   nothing matched a known stack; the generalist runs it

Python 3.10+, standard library only (gh is used only with --issue).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import detect_stack  # noqa: E402  (sibling module, works from any working directory)

WILDCARD = re.compile(r"[*?\[{]")
EXTENSIONS = {
    ".java": "java", ".kt": "kotlin", ".kts": "kotlin", ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".vue": "typescript", ".py": "python",
    ".go": "go", ".cs": "csharp",
}


def parse_task(body: str) -> tuple[list[str], str | None]:
    """Extract the Touches globs and the optional Stack line from a task Issue body."""
    touches: list[str] = []
    stack = None
    for line in body.splitlines():
        match = re.match(r"^\s*[-*]?\s*\**Touches:?\**:?\s*(.+)$", line, re.IGNORECASE)
        if match:
            touches += [t.strip(" `") for t in re.split(r"[,\s]+", match.group(1)) if t.strip(" `")]
        match = re.match(r"^\s*[-*]?\s*\**Stack:?\**:?\s*`?([a-z0-9-]+)`?", line, re.IGNORECASE)
        if match:
            stack = match.group(1).lower()
    return touches, stack


def parse_complexity(body: str) -> str | None:
    """The task's "Complexity: S|M|L" line, written by the Planner (Issue #19)."""
    for line in body.splitlines():
        match = re.match(r"^\s*[-*]?\s*\**Complexity:?\**:?\s*`?([SML])\b", line, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None


def model_for(complexity: str | None, catalogue: dict) -> str:
    """S and M run on the role's model; L runs on opus. Never fable."""
    models = catalogue.get("complexity_models", {"S": "sonnet", "M": "sonnet", "L": "opus"})
    return models.get(complexity or "M", models.get("M", "sonnet"))


def literal_prefix(pattern: str) -> str:
    """The directory part of a glob before its first wildcard: 'apps/web/src/**' -> 'apps/web/src'."""
    pattern = pattern.strip().lstrip("./")
    cut = WILDCARD.search(pattern)
    prefix = pattern[: cut.start()] if cut else pattern
    return prefix.rstrip("/")


def module_of(pattern: str, modules: list[dict]) -> dict | None:
    """The deepest module whose path contains the glob's literal prefix."""
    prefix = literal_prefix(pattern)
    candidates = [m for m in modules
                  if m["path"] == "." or prefix == m["path"] or prefix.startswith(m["path"] + "/")]
    if not candidates:
        return None
    depth = lambda m: 0 if m["path"] == "." else m["path"].count("/") + 1  # noqa: E731
    deepest = max(depth(m) for m in candidates)
    candidates = [m for m in candidates if depth(m) == deepest]
    # Several builds in one directory (for example pom.xml and package.json): use the extension.
    language = EXTENSIONS.get(Path(pattern).suffix.lower())
    return next((m for m in candidates if language in m["languages"]), candidates[0])


def skills_of(specialist: str, catalogue: dict) -> list[str]:
    base = catalogue.get("base_skills", ["development", "testing"])
    return base + catalogue.get("specialists", {}).get(specialist, {}).get("skills", [])


def select(profile: dict, touches: list[str], stack: str | None, catalogue: dict) -> dict:
    specialists = catalogue.get("specialists", {})
    fallback = catalogue.get("routing", {}).get("fallback", "developer")
    modules = profile.get("modules", [])

    if stack:
        if stack in specialists:
            return {"decision": "explicit", "specialist": stack, "skills": skills_of(stack, catalogue),
                    "modules": [], "reason": f"the task declares Stack: {stack}"}
        unknown = f"Stack: {stack} is not in the catalogue; "
    else:
        unknown = ""

    touched = []
    for pattern in touches:
        module = module_of(pattern, modules)
        if module and module not in touched:
            touched.append(module)
    if not touched and len({m["specialist"] for m in modules}) == 1:
        touched = modules[:1]

    chosen = []
    for module in touched:
        if module["specialist"] not in chosen:
            chosen.append(module["specialist"])
    paths = [m["path"] for m in touched]

    if len(chosen) == 1:
        return {"decision": "single", "specialist": chosen[0], "skills": skills_of(chosen[0], catalogue),
                "modules": paths, "reason": unknown + f"touched modules {paths} belong to {chosen[0]}"}
    if len(chosen) > 1:
        skills = []
        for specialist in chosen:
            skills += [s for s in skills_of(specialist, catalogue) if s not in skills]
        return {"decision": "split", "specialist": fallback, "skills": skills, "modules": paths,
                "candidates": chosen,
                "reason": unknown + f"the task touches modules of {chosen}; ask the Planner to split it by stack, "
                                    f"or run the generalist with every listed skill"}
    return {"decision": "fallback", "specialist": fallback, "skills": skills_of(fallback, catalogue),
            "modules": [], "reason": unknown + "no touched path belongs to a detected module"}


def issue_body(number: int, repo: str | None) -> str:
    command = ["gh", "issue", "view", str(number), "--json", "body", "--jq", ".body"]
    if repo:
        command += ["--repo", repo]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f"error: gh issue view {number} failed: {result.stderr.strip()}")
    return result.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--profile", help="stack profile written by detect_stack.py")
    source.add_argument("--root", help="detect the profile from this repository root instead")
    parser.add_argument("--touches", default="", help="comma-separated globs from the task's Touches line")
    parser.add_argument("--stack", help="explicit specialist id (the task's Stack line)")
    parser.add_argument("--issue", type=int, help="read Touches and Stack from this task Issue with gh")
    parser.add_argument("--repo", help="owner/repo for --issue")
    parser.add_argument("--summary", action="store_true", help="list the specialists the repository needs")
    parser.add_argument("--complexity", choices=("S", "M", "L"), help="the task's Complexity line")
    args = parser.parse_args(argv)

    catalogue = detect_stack.load_catalogue()
    if args.profile:
        profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    else:
        profile = detect_stack.detect(Path(args.root or "."), catalogue=catalogue)

    if args.summary:
        needed: dict[str, list[str]] = {}
        for module in profile.get("modules", []):
            needed.setdefault(module["specialist"], []).append(module["path"])
        print(json.dumps({"specialists": needed or {catalogue.get("routing", {}).get("fallback", "developer"): []}},
                         indent=2))
        return 0

    touches = [t.strip() for t in args.touches.split(",") if t.strip()]
    stack = args.stack
    if args.issue:
        body = issue_body(args.issue, args.repo)
        issue_touches, issue_stack = parse_task(body)
        args.complexity = args.complexity or parse_complexity(body)
        touches = touches or issue_touches
        stack = stack or issue_stack
    result = select(profile, touches, stack, catalogue)
    result["complexity"] = args.complexity or "M"
    result["model"] = model_for(args.complexity, catalogue)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
