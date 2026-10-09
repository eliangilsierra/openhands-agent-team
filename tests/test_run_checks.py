import json
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import DEVELOPMENT, load

run_checks = load(DEVELOPMENT, "run_checks")
PY = f'"{sys.executable}"'


class ParseCounts(unittest.TestCase):
    def test_runners(self):
        samples = {
            "Tests:       1 failed, 2 skipped, 40 passed, 43 total": {"passed": 40, "failed": 1, "skipped": 2},
            "      Tests  2 failed | 40 passed | 1 skipped (43)": {"passed": 40, "failed": 2, "skipped": 1},
            "===== 3 failed, 10 passed, 1 skipped, 1 error in 2.31s =====": {"passed": 10, "failed": 4, "skipped": 1},
            "[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0\n[INFO] Tests run: 12, Failures: 1, Errors: 1, Skipped: 2":
                {"passed": 8, "failed": 2, "skipped": 2},
            "Passed!  - Failed:     0, Passed:    12, Skipped:     1, Total:    13": {"passed": 12, "failed": 0, "skipped": 1},
            "5 tests completed, 1 failed, 1 skipped": {"passed": 3, "failed": 1, "skipped": 1},
            "ok  \texample.com/a\t0.1s\nFAIL\texample.com/b\t0.2s": {"packages_ok": 1, "packages_failed": 1},
        }
        for output, expected in samples.items():
            with self.subTest(output=output[:30]):
                self.assertEqual(run_checks.parse_counts(output), expected)

    def test_unknown_output(self):
        self.assertEqual(run_checks.parse_counts("Compiled successfully"), {})

    def test_colours_are_ignored(self):
        self.assertEqual(run_checks.parse_counts("\x1b[32m===== 2 passed in 0.1s =====\x1b[0m")["passed"], 2)


class RunAndCompare(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def cmd(self, code: str) -> str:
        return f"{PY} -c \"{code}\""

    def test_statuses_tail_and_redaction(self):
        secret = "ghp_" + "a" * 36
        failing = run_checks.run("test", self.cmd(f"import sys; print('{secret}'); sys.exit(1)"), self.dir, 30, 10, None)
        self.assertEqual(failing["status"], "FAIL")
        self.assertNotIn(secret, " ".join(failing["tail"]))
        self.assertIn("[REDACTED:github-token]", " ".join(failing["tail"]))
        missing = run_checks.run("lint", "definitely-not-a-command-xyz", self.dir, 30, 10, None)
        self.assertEqual(missing["status"], "BLOCKED")
        slow = run_checks.run("build", self.cmd("import time; time.sleep(5)"), self.dir, 1, 10, None)
        self.assertEqual((slow["status"], slow["note"]), ("BLOCKED", "timed out after 1s"))

    def test_cli_baseline_compare_and_markdown(self):
        baseline = self.dir / "baseline.json"
        after = self.dir / "after.json"
        passing = "test=" + self.cmd("print('===== 5 passed in 0.1s =====')")
        fewer = "test=" + self.cmd("print('===== 4 passed in 0.1s =====')")
        self.assertEqual(run_checks.main(["--root", str(self.dir), "--cmd", passing, "--baseline", "--out", str(baseline)]), 0)
        code = run_checks.main(["--root", str(self.dir), "--cmd", fewer, "--compare", str(baseline), "--out", str(after)])
        self.assertEqual(code, 1, "losing a test is a regression")
        record = json.loads(after.read_text(encoding="utf-8"))
        self.assertIn("fewer tests", record["regressions"][0])
        table = run_checks.to_markdown(record, json.loads(baseline.read_text(encoding="utf-8")))
        self.assertIn("| Command | Result |", table)
        self.assertIn("PASS - 4 passed, 0 failed (baseline PASS, 5 passed)", table)

    def test_profile_module_and_skipped_checks(self):
        profile = self.dir / "profile.json"
        (self.dir / "web").mkdir()
        profile.write_text(json.dumps({"modules": [
            {"path": "web", "commands": {"test": self.cmd("import os; print(os.path.basename(os.getcwd()))")}},
            {"path": "api", "commands": {}}]}), encoding="utf-8")
        out = self.dir / "out.json"
        code = run_checks.main(["--root", str(self.dir), "--profile", str(profile), "--module", "web", "--out", str(out)])
        self.assertEqual(code, 0)
        record = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(record["results"][0]["tail"][-1], "web", "commands run inside the module")
        self.assertIn("lint", record["skipped_checks"])
        with self.assertRaises(SystemExit):
            run_checks.main(["--root", str(self.dir), "--profile", str(profile)])  # several modules, none chosen


if __name__ == "__main__":
    unittest.main()
