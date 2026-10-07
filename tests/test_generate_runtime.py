"""The generated runtime matches config/, and the validator catches drift."""

import json
import unittest
from unittest import mock

from helpers import ROOT, load

generate_runtime = load(ROOT / "scripts", "generate_runtime")
validate_repository = load(ROOT / "scripts", "validate_repository")


class GenerateRuntime(unittest.TestCase):
    def test_committed_files_are_up_to_date(self):
        self.assertEqual(generate_runtime.check(), [])

    def test_specialists_inherit_the_developer(self):
        files = generate_runtime.plan()
        agent = files[generate_runtime.AGENTS_DIR / "developer-java-spring.md"]
        fm = validate_repository.yaml.safe_load(agent.split("---")[1])
        self.assertEqual(fm["skills"], ["development", "testing", "stack-java-spring"])
        self.assertEqual(fm["isolation"], "worktree")
        self.assertEqual((fm["model"], fm["maxTurns"]), ("sonnet", 120))
        self.assertNotIn("Agent", fm["tools"], "subagents never spawn subagents")
        self.assertIn("Restriction level R4", agent)
        self.assertIn("## Your stack", agent)
        self.assertIn("STATUS: DONE | BLOCKED | PARTIAL | FAILED", agent)

    def test_generalist_loads_stack_skills_on_demand(self):
        developer = generate_runtime.plan()[generate_runtime.AGENTS_DIR / "developer.md"]
        self.assertIn("generalist of the Developer role", developer)

    def test_catalogue_json_and_hook_levels(self):
        files = generate_runtime.plan()
        catalogue = json.loads(files[generate_runtime.CATALOGUE_JSON])
        self.assertEqual(len(catalogue["specialists"]), 11)
        self.assertEqual(catalogue["base_skills"], ["development", "testing"])
        lib = files[generate_runtime.LIB]
        for spec_id in catalogue["specialists"]:
            if spec_id != "developer":
                self.assertIn(f"'{spec_id}': 'R4',", lib)

    def test_check_reports_drift(self):
        real = generate_runtime.plan()
        target = generate_runtime.AGENTS_DIR / "developer-go.md"
        drifted = {**real, target: real[target] + "edited by hand\n"}
        with mock.patch.object(generate_runtime, "plan", return_value=drifted):
            problems = generate_runtime.check()
        self.assertEqual(problems, ["templates/runtime/claude/agents/developer-go.md is out of date"])


class Validator(unittest.TestCase):
    def test_repository_is_valid(self):
        with mock.patch("builtins.print"):
            self.assertEqual(validate_repository.main(), 0)

    def test_skill_scripts_are_allowed_but_other_source_is_not(self):
        pattern = validate_repository.SKILL_SCRIPT
        self.assertTrue(pattern.match("skills/development/scripts/run_checks.py"))
        self.assertFalse(pattern.match("skills/development/run_checks.py"))
        self.assertFalse(pattern.match("src/app.py"))

    def test_github_slug(self):
        self.assertEqual(validate_repository.github_slug("3. Developer specialists"), "3-developer-specialists")


if __name__ == "__main__":
    unittest.main()
