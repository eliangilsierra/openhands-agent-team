"""UX design skill: rule search, checklists (web and Android) and WCAG contrast (Issue #24)."""

import csv
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import ROOT, load

SCRIPTS = ROOT / "skills" / "ux-design" / "scripts"
ux_search = load(SCRIPTS, "ux_search")
contrast = load(SCRIPTS, "contrast")


class Data(unittest.TestCase):
    def test_every_stack_shares_the_schema(self):
        header = ["No", "Category", "Guideline", "Description", "Do", "Don't", "Code Good", "Code Bad", "Severity", "Docs URL"]
        for path in sorted((ROOT / "skills" / "ux-design" / "data" / "stacks").glob("*.csv")):
            with path.open(encoding="utf-8", newline="") as handle:
                with self.subTest(stack=path.stem):
                    self.assertEqual(next(csv.reader(handle)), header)

    def test_android_rules_are_complete(self):
        rows = ux_search.load(stack="jetpack-compose")
        self.assertGreaterEqual(len(rows), 40)
        for row in rows:
            with self.subTest(rule=row["Guideline"]):
                self.assertIn(row["Severity"], {"High", "Medium", "Low"})
                self.assertTrue(row["Docs URL"].startswith(("https://developer.android.com/", "https://m3.material.io/")))
                self.assertTrue(row["Do"] and row["Don't"] and row["Code Good"])

    def test_vendored_data_has_its_notice(self):
        notice = (ROOT / "skills" / "ux-design" / "data" / "NOTICE.md").read_text(encoding="utf-8")
        self.assertIn("1deb97c72161528f6b7d84bc5117ae4be2e42735", notice)
        self.assertIn("MIT License", notice)


class Search(unittest.TestCase):
    def test_android_checklist_has_the_critical_mobile_rules(self):
        rules = ux_search.checklist("android", None, {"high"})
        titles = {ux_search.title(r) for r in rules}
        self.assertIn("Touch targets of at least 48dp", titles)
        self.assertIn("Content descriptions for meaningful images", titles)
        self.assertTrue(all(r["Severity"].lower() == "high" for r in rules))
        self.assertFalse(any(r.get("Platform") == "Web" for r in rules), "web-only rules stay out of Android checklists")
        self.assertFalse(any(r["source"] == "stack:react" for r in rules))

    def test_web_checklist_for_a_stack(self):
        rules = ux_search.checklist("web", "react", {"high"})
        self.assertTrue(any(r["source"] == "stack:react" for r in rules))
        self.assertFalse(any(r["source"] == "stack:jetpack-compose" for r in rules))

    def test_ranked_search(self):
        top = ux_search.bm25(ux_search.load(stack="jetpack-compose"), "lazy list keys")[0][1]
        self.assertEqual(top["Guideline"], "Stable keys in lazy lists")
        self.assertEqual(ux_search.bm25(ux_search.load("ux"), "qwxzv"), [])

    def test_cli(self):
        with mock.patch("sys.stdout.write") as write:
            self.assertEqual(ux_search.main(["--checklist", "--platform", "android", "--json"]), 0)
        self.assertIn("48dp", write.call_args[0][0])
        with self.assertRaises(SystemExit):
            ux_search.main(["--stack", "cobol", "buttons"])


class Contrast(unittest.TestCase):
    def test_reference_ratios(self):
        self.assertEqual(contrast.ratio("#000000", "#FFFFFF"), 21.0)
        self.assertEqual(contrast.ratio("#777777", "#FFFFFF"), 4.48)  # the classic just-below-AA gray
        self.assertEqual(contrast.ratio("#FFF", "#FFF"), 1.0)

    def test_compose_argb_and_alpha_blending(self):
        self.assertEqual(contrast.ratio("0xFF000000", "0xFFFFFFFF"), 21.0)
        half = contrast.ratio("#80000000", "#FFFFFF")  # 50% black over white
        self.assertTrue(3.0 < half < 4.5)

    def test_verdicts(self):
        v = contrast.verdict(4.48)
        self.assertEqual((v["text_aa"], v["large_text_aa"], v["non_text_aa"], v["text_aaa"]), (False, True, True, False))
        self.assertTrue(contrast.verdict(7.0)["text_aaa"])

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            contrast.parse("blue")
        with self.assertRaises(ValueError):
            contrast.ratio("#000", "#80FFFFFF")

    def test_cli_exit_codes_and_pairs_file(self):
        with mock.patch("builtins.print"):
            self.assertEqual(contrast.main(["#000000", "#FFFFFF"]), 0)
            self.assertEqual(contrast.main(["#777777", "#FFFFFF"]), 1)
            with tempfile.TemporaryDirectory() as tmp:
                pairs = Path(tmp) / "pairs.csv"
                pairs.write_text("# name,fg,bg\nbody,#1C1B1F,#FFFBFE\nhint,#9E9E9E,#FFFFFF\n", encoding="utf-8")
                self.assertEqual(contrast.main(["--pairs", str(pairs)]), 1)


if __name__ == "__main__":
    unittest.main()
