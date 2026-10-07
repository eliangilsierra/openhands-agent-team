import unittest

from helpers import FIXTURES, ROUTING, load

detect_stack = load(ROUTING, "detect_stack")
select_specialist = load(ROUTING, "select_specialist")
CATALOGUE = detect_stack.load_catalogue()
MONOREPO = detect_stack.detect(FIXTURES / "monorepo")


def select(touches, stack=None, profile=MONOREPO):
    return select_specialist.select(profile, touches, stack, CATALOGUE)


class SelectSpecialist(unittest.TestCase):
    def test_single_module(self):
        result = select(["services/orders/src/main/java/**"])
        self.assertEqual(result["decision"], "single")
        self.assertEqual(result["specialist"], "developer-java-spring")
        self.assertEqual(result["skills"], ["development", "testing", "stack-java-spring"])

    def test_deepest_module_wins_over_the_workspace_root(self):
        result = select(["apps/web/app/orders/**"])
        self.assertEqual(result["specialist"], "developer-nextjs")
        self.assertIn("stack-react", result["skills"])

    def test_cross_stack_task_is_split(self):
        result = select(["apps/web/app/**", "services/orders/src/**"])
        self.assertEqual(result["decision"], "split")
        self.assertEqual(result["specialist"], "developer")
        self.assertEqual(sorted(result["candidates"]), ["developer-java-spring", "developer-nextjs"])
        self.assertIn("stack-nextjs", result["skills"])
        self.assertIn("stack-java-spring", result["skills"])

    def test_explicit_stack_wins(self):
        result = select(["apps/web/**"], stack="developer-react")
        self.assertEqual((result["decision"], result["specialist"]), ("explicit", "developer-react"))

    def test_unknown_explicit_stack_is_ignored(self):
        result = select(["services/orders/**"], stack="developer-cobol")
        self.assertEqual(result["specialist"], "developer-java-spring")
        self.assertIn("not in the catalogue", result["reason"])

    def test_single_module_repository_needs_no_touches(self):
        profile = detect_stack.detect(FIXTURES / "android")
        result = select([], profile=profile)
        self.assertEqual(result["specialist"], "developer-kotlin-android")

    def test_nothing_detected_falls_back_to_generalist(self):
        result = select(["docs/**"], profile={"modules": []})
        self.assertEqual((result["decision"], result["specialist"]), ("fallback", "developer"))

    def test_extension_disambiguates_builds_in_one_directory(self):
        profile = {"modules": [
            {"path": ".", "languages": ["typescript"], "specialist": "developer-react"},
            {"path": ".", "languages": ["java"], "specialist": "developer-java-spring"},
        ]}
        self.assertEqual(select(["src/main/java/**/*.java"], profile=profile)["specialist"], "developer-java-spring")
        self.assertEqual(select(["src/ui/**/*.tsx"], profile=profile)["specialist"], "developer-react")

    def test_parse_task_lines(self):
        body = ("## Technical approach\nUse the repository.\n"
                "Touches: `services/orders/src/**`, services/orders/pom.xml\n"
                "- **Stack:** `developer-java-spring`\n")
        touches, stack = select_specialist.parse_task(body)
        self.assertEqual(touches, ["services/orders/src/**", "services/orders/pom.xml"])
        self.assertEqual(stack, "developer-java-spring")

    def test_every_catalogue_stack_is_routable(self):
        priority = CATALOGUE["routing"]["priority"]
        for specialist_id, spec in CATALOGUE["specialists"].items():
            for key in spec["stacks"]:
                self.assertIn(key, priority)
                self.assertEqual(detect_stack.specialist_for([key], CATALOGUE), specialist_id)


if __name__ == "__main__":
    unittest.main()
