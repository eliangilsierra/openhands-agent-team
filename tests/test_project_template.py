"""Project template build and integration-branch resolution (ADR-0004, Issue #17)."""

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from helpers import DEVELOPMENT, ROOT, git, load, temp_repo

build_project_template = load(ROOT / "scripts", "build_project_template")
branches = load(DEVELOPMENT, "branches")

REQUIRED = [
    "AGENTS.md", "CLAUDE.md", "README.md", "LICENSE", ".gitignore", ".gitattributes", ".editorconfig",
    ".gitleaks.toml", ".github/CODEOWNERS", ".github/dependabot.yml", ".github/labels.json",
    ".github/pull_request_template.md", ".github/workflows/pr-conventions.yml",
    ".github/workflows/secret-scan.yml", ".github/workflows/ci.yml", ".github/ISSUE_TEMPLATE/task.yml",
    ".github/ci-templates/node.yml", ".github/ci-templates/java-maven.yml", ".github/ci-templates/android.yml",
    "docs/architecture/README.md", "docs/decisions/README.md", "docs/research/README.md", "scripts/bootstrap.sh",
]


class BuildProjectTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        build_project_template.build(cls.out, "octo-owner", "Octo Owner", "octo-owner/openhands-agent-team",
                                     "agent-team-project-template", "2026")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def read(self, name):
        return (self.out / name).read_text(encoding="utf-8")

    def test_every_required_file_exists(self):
        for name in REQUIRED:
            with self.subTest(name=name):
                self.assertTrue((self.out / name).is_file())
        self.assertFalse((self.out / ".github/ISSUE_TEMPLATE/config.yml").exists())

    def test_mit_licence_and_owner(self):
        licence = self.read("LICENSE")
        self.assertTrue(licence.startswith("MIT License"))
        self.assertIn("Copyright (c) 2026 Octo Owner", licence)
        self.assertIn("* @octo-owner", self.read(".github/CODEOWNERS"))

    def test_tokens_left_for_bootstrap_only(self):
        for path in self.out.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                for token in build_project_template.REQUIRED_TOKENS_FILLED:
                    self.assertNotIn(token, text, f"{path.name} keeps {token}")
        self.assertIn("{{project_name}}", self.read("AGENTS.md"))
        self.assertIn("--template octo-owner/agent-team-project-template", self.read("README.md"))
        self.assertIn("https://github.com/octo-owner/openhands-agent-team", self.read("AGENTS.md"))

    def test_labels_match_the_workflow_config(self):
        labels = json.loads(self.read(".github/labels.json"))
        workflow = yaml.safe_load((ROOT / "config" / "workflow.yaml").read_text(encoding="utf-8"))
        self.assertEqual({label["name"] for label in labels}, set(workflow["labels"]))
        self.assertTrue(all(len(label["color"]) == 6 for label in labels))

    def test_forms_and_checks_are_the_team_ones(self):
        self.assertEqual(self.read(".github/pull_request_template.md"),
                         (ROOT / ".github" / "pull_request_template.md").read_text(encoding="utf-8"))
        pr_check = yaml.safe_load(self.read(".github/workflows/pr-conventions.yml"))
        self.assertIn("pr-conventions", pr_check["jobs"])
        for workflow in (".github/workflows/ci.yml", ".github/workflows/secret-scan.yml"):
            on = yaml.safe_load(self.read(workflow))[True]  # PyYAML reads the key "on" as True
            self.assertEqual(on["push"]["branches"], ["main", "develop"])

    def test_readme_template_section_is_marked_for_removal(self):
        readme = self.read("README.md")
        self.assertLess(readme.index("<!-- template:start -->"), readme.index("<!-- template:end -->"))
        self.assertIn("bootstrap.sh --dry-run", readme)

    def test_bootstrap_configures_both_branches(self):
        script = self.read("scripts/bootstrap.sh")
        for needle in ("protect-main main merge", "protect-develop develop squash", "default_branch=develop",
                       "secret_scanning_push_protection", "--dry-run", "labels.json", "required_linear_history"):
            self.assertIn(needle, script)


class IntegrationBranch(unittest.TestCase):
    def clone(self, default_branch):
        holder, origin = temp_repo({"README.md": "x\n"})
        self.addCleanup(holder.cleanup)
        if default_branch != "main":
            git(origin, "branch", default_branch)
            git(origin, "symbolic-ref", "HEAD", f"refs/heads/{default_branch}")
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        target = Path(work.name) / "clone"
        git(Path(work.name), "clone", "-q", str(origin), str(target))
        return target

    def test_default_branch_is_the_integration_branch(self):
        self.assertEqual(branches.integration_ref(str(self.clone("develop"))), "origin/develop")
        self.assertEqual(branches.integration_ref(str(self.clone("main"))), "origin/main")

    def test_without_origin_head_it_falls_back_to_develop_then_main(self):
        clone = self.clone("main")
        git(clone, "remote", "set-head", "origin", "--delete")
        self.assertEqual(branches.integration_ref(str(clone)), "origin/main")
        git(clone, "update-ref", "refs/remotes/origin/develop", "HEAD")
        self.assertEqual(branches.integration_ref(str(clone)), "origin/develop")


if __name__ == "__main__":
    unittest.main()
