"""Technical writing skill: documentation audit (Issue #25)."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import ROOT, load, write_tree

docs_audit = load(ROOT / "skills" / "technical-writing" / "scripts", "docs_audit")
build_project_template = load(ROOT / "scripts", "build_project_template")

GOOD_README = """# Shop

Online shop for small stores.

## Getting started

Run `npm ci`.

## Usage

See [the guide](docs/how-to/deploy.md).

## Development

Read [AGENTS.md](AGENTS.md).

## Documentation

[Index](docs/README.md)

## License

MIT
"""

STRUCTURE = {
    "AGENTS.md": "# Agents\n",
    "src/app.ts": "export const app = 1;\n",
    "docs/README.md": "# Docs\n\n- [Deploy](how-to/deploy.md)\n- [Design](architecture/README.md#overview)\n",
    "docs/tutorials/README.md": "# Tutorials\n\n[Index](../README.md)\n",
    "docs/how-to/deploy.md": "# Deploy\n\nEdit `src/app.ts` and run it.\n",
    "docs/reference/README.md": "# Reference\n",
    "docs/explanation/README.md": "# Explanation\n",
    "docs/architecture/README.md": "# Architecture\n\n## Overview\n\n```mermaid\nflowchart LR\n  a --> b\n```\n",
    "docs/decisions/README.md": "# Decisions\n",
}


def audit(files: dict, **kwargs) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmp:
        write_tree(Path(tmp), files)
        return docs_audit.audit(Path(tmp), **kwargs)


def kinds(findings: list[dict]) -> set[tuple[str, str]]:
    return {(f["check"], f["severity"]) for f in findings}


class DocsAudit(unittest.TestCase):
    def test_clean_repository(self):
        findings = audit({"README.md": GOOD_README, **STRUCTURE})
        errors = [f for f in findings if f["severity"] == "error"]
        self.assertEqual(errors, [])

    def test_missing_structure_and_readme_sections(self):
        findings = audit({"README.md": "# Shop\n\nText.\n\n## Usage\n\nx\n"})
        self.assertIn(("structure", "error"), kinds(findings))
        missing = {f["message"] for f in findings if f["check"] == "readme"}
        self.assertTrue(any("getting started" in m for m in missing))
        self.assertTrue(any("licence" in m for m in missing))
        self.assertFalse(any("'usage'" in m for m in missing))

    def test_broken_links_and_anchors(self):
        files = {"README.md": GOOD_README, **STRUCTURE,
                 "docs/how-to/broken.md": "# Broken\n\n[x](missing.md) [y](../architecture/README.md#nope) [ok](https://example.org)\n"}
        findings = audit(files, only={"links"})
        messages = [f["message"] for f in findings]
        self.assertIn("broken link missing.md", messages)
        self.assertIn("missing anchor ../architecture/README.md#nope", messages)
        self.assertEqual(len(findings), 2, "external links and valid anchors are not reported")

    def test_template_placeholders_are_not_links(self):
        files = {"docs/x.md": "[ADR](../decisions/ADR-<NNNN>-<slug>.md) and [ADR](ADR-NNNN-title.md)\n"}
        self.assertEqual(audit(files, only={"links"}), [])

    def test_orphans_and_stale_paths(self):
        files = {"README.md": GOOD_README, **STRUCTURE,
                 "docs/explanation/lonely.md": "# Lonely\n\nSee `src/missing.ts` and `feature/` branches.\n"}
        findings = audit(files, only={"orphans", "stale-paths"})
        self.assertIn(("orphans", "warning"), kinds(findings))
        stale = [f["message"] for f in findings if f["check"] == "stale-paths"]
        self.assertEqual(stale, ["`src/missing.ts` does not exist in the repository"], "branch names are not paths")

    def test_mermaid_and_code_blocks(self):
        files = {"docs/a.md": "```mermaid\nflowchat LR\n  a --> b\n```\n\n```text\n[not a link](nowhere.md)\n```\n"}
        findings = audit(files, only={"mermaid", "links"})
        self.assertEqual(kinds(findings), {("mermaid", "error")})

    def test_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_tree(Path(tmp), {"README.md": GOOD_README, **STRUCTURE})
            with mock.patch("builtins.print") as printed:
                self.assertEqual(docs_audit.main([tmp, "--json"]), 0)
            self.assertEqual(json.loads(printed.call_args[0][0])["errors"], 0)
            write_tree(Path(tmp), {"docs/how-to/deploy.md": "[x](gone.md)\n"})
            with mock.patch("builtins.print"):
                self.assertEqual(docs_audit.main([tmp]), 1)


class TemplateDocs(unittest.TestCase):
    def test_project_template_passes_the_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            build_project_template.build(out, "octo", "Octo", "octo/openhands-agent-team", "agent-team-project-template", "2026")
            for folder in ("tutorials", "how-to", "reference", "explanation", "design", "architecture", "decisions", "research"):
                self.assertTrue((out / "docs" / folder / "README.md").is_file(), folder)
            findings = docs_audit.audit(out)
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
