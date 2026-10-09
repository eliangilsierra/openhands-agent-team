#!/usr/bin/env python3
"""Assemble the project template repository from the target-repository kit (ADR-0004).

The template repository (for example agent-team-project-template) is never edited by hand: it is
this script's output, so it cannot drift from templates/target-repo/ and the team's forms. To update
it, run the script into a clone of the template repository and open a Pull Request there.

Usage:
    python scripts/build_project_template.py --out DIR --owner OWNER --holder "NAME" \
        [--team-repo OWNER/openhands-agent-team] [--template-name agent-team-project-template] [--year YYYY]

Tokens filled here: {{team_repo}}, {{template_repo}}, and in LICENSE/CODEOWNERS the template's own
{{year}}, {{holder}} and {{owner}}. {{project_name}} stays: bootstrap.sh fills it in each new project.

Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KIT = ROOT / "templates" / "target-repo"

# (source, destination) pairs; a directory source copies its files recursively.
LAYOUT = [
    (KIT / "AGENTS.md", "AGENTS.md"),
    (KIT / "CLAUDE.md", "CLAUDE.md"),
    (KIT / "PROJECT_README.md", "README.md"),
    (KIT / "LICENSE", "LICENSE"),
    (KIT / ".gitignore", ".gitignore"),
    (KIT / ".gitattributes", ".gitattributes"),
    (KIT / ".editorconfig", ".editorconfig"),
    (KIT / ".gitleaks.toml", ".gitleaks.toml"),
    (KIT / ".github" / "CODEOWNERS", ".github/CODEOWNERS"),
    (KIT / ".github" / "dependabot.yml", ".github/dependabot.yml"),
    (KIT / ".github" / "labels.json", ".github/labels.json"),
    (KIT / ".github" / "workflows" / "pr-conventions.yml", ".github/workflows/pr-conventions.yml"),
    (KIT / ".github" / "workflows" / "secret-scan.yml", ".github/workflows/secret-scan.yml"),
    (KIT / ".github" / "workflows" / "ci.yml", ".github/workflows/ci.yml"),
    (KIT / ".github" / "workflows" / "ci.yml", ".github/ci-templates/node.yml"),
    (KIT / "ci", ".github/ci-templates"),
    (ROOT / ".github" / "pull_request_template.md", ".github/pull_request_template.md"),
    (KIT / "docs", "docs"),
    (KIT / "scripts" / "bootstrap.sh", "scripts/bootstrap.sh"),
]
ISSUE_FORMS = ROOT / ".github" / "ISSUE_TEMPLATE"
# config.yml points to the team repository's security advisories; projects keep GitHub's default.
SKIPPED_FORMS = {"config.yml"}
REQUIRED_TOKENS_FILLED = ("{{team_repo}}", "{{template_repo}}", "{{year}}", "{{holder}}", "{{owner}}")


def files_of(source: Path, destination: str) -> list[tuple[Path, str]]:
    if source.is_dir():
        return [(path, f"{destination}/{path.relative_to(source).as_posix()}")
                for path in sorted(source.rglob("*")) if path.is_file()]
    return [(source, destination)]


def plan() -> list[tuple[Path, str]]:
    entries = [pair for source, destination in LAYOUT for pair in files_of(source, destination)]
    entries += [(form, f".github/ISSUE_TEMPLATE/{form.name}") for form in sorted(ISSUE_FORMS.glob("*.yml"))
                if form.name not in SKIPPED_FORMS]
    return entries


def render(text: str, values: dict[str, str]) -> str:
    for token, value in values.items():
        text = text.replace(token, value)
    return text


def build(out: Path, owner: str, holder: str, team_repo: str, template_name: str, year: str) -> list[str]:
    values = {"{{team_repo}}": team_repo, "{{template_repo}}": f"{owner}/{template_name}",
              "{{year}}": year, "{{holder}}": holder, "{{owner}}": owner}
    written = []
    for source, destination in plan():
        target = out / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix in (".png", ".jpg", ".ico", ".jar"):
            shutil.copyfile(source, target)
        else:
            text = render(source.read_text(encoding="utf-8").replace("\r\n", "\n"), values)
            leftover = [t for t in REQUIRED_TOKENS_FILLED if t in text]
            if leftover:
                raise ValueError(f"{destination}: unfilled tokens {leftover}")
            with target.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
        written.append(destination)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, help="directory to write (for example a clone of the template repository)")
    parser.add_argument("--owner", required=True, help="GitHub owner of the template repository")
    parser.add_argument("--holder", required=True, help="copyright holder of the template's MIT licence")
    parser.add_argument("--team-repo", help="owner/name of the team repository (default: <owner>/openhands-agent-team)")
    parser.add_argument("--template-name", default="agent-team-project-template")
    parser.add_argument("--year", default=str(dt.date.today().year))
    args = parser.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    written = build(out, args.owner, args.holder, args.team_repo or f"{args.owner}/openhands-agent-team",
                    args.template_name, args.year)
    print(f"Wrote {len(written)} files to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
