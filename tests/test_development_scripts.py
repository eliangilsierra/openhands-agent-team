"""Tests for repo_map, impact_scan, checkpoint, pr_body and deps_check."""

import argparse
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import DEVELOPMENT, FIXTURES, git, load, temp_repo

repo_map = load(DEVELOPMENT, "repo_map")
impact_scan = load(DEVELOPMENT, "impact_scan")
checkpoint = load(DEVELOPMENT, "checkpoint")
pr_body = load(DEVELOPMENT, "pr_body")
deps_check = load(DEVELOPMENT, "deps_check")


class RepoMap(unittest.TestCase):
    def test_symbols_per_language(self):
        java = repo_map.symbols(FIXTURES / "spring-maven/src/main/java/com/example/orders/OrderService.java", "java")
        self.assertEqual(java[:3], ["@Service", "OrderService", "total"])
        python = repo_map.symbols(FIXTURES / "python/billing/invoices.py", "python")
        self.assertEqual(python, ["InvoiceError", "invoice_total"])
        kotlin = repo_map.symbols(FIXTURES / "android/app/src/main/java/com/example/notes/NotesViewModel.kt", "kotlin")
        self.assertEqual(kotlin, ["NotesViewModel", "count"])
        go = repo_map.symbols(FIXTURES / "go/stock.go", "go")
        self.assertEqual(go, ["Available"])
        ts = repo_map.symbols(FIXTURES / "angular/src/app/app.component.ts", "ts")
        self.assertEqual(ts, ["@Component", "AppComponent"])

    def test_focus_first_and_budget(self):
        text = repo_map.build(FIXTURES / "spring-maven", ["src/test/**"], 10_000)
        self.assertTrue(text.startswith("## focus (1 files)"))
        self.assertIn("OrderServiceTest.java [test]", text)
        small = repo_map.build(FIXTURES / "nextjs", [], 60)
        self.assertIn("more files omitted", small)


class ImpactScan(unittest.TestCase):
    def test_related_tests_and_untested_changes(self):
        holder, root = temp_repo({
            "src/cart/total.ts": "export const total = 1;\n",
            "src/cart/total.test.ts": "import { total } from './total';\n",
            "src/cart/discount.ts": "export const discount = 0;\n",
            "src/orders/OrderService.java": "class OrderService {}\n",
            "src/test/java/OrderServiceTest.java": "class OrderServiceTest {}\n",
            "tests/test_invoices.py": "from billing import invoices\n",
            "billing/invoices.py": "X = 1\n",
        })
        self.addCleanup(holder.cleanup)
        report = impact_scan.scan(root, ["src/cart/total.ts", "src/cart/discount.ts", "src/orders/OrderService.java",
                                         "billing/invoices.py", "README.md"])
        self.assertEqual(report["related_tests"]["src/cart/total.ts"], ["src/cart/total.test.ts"])
        self.assertEqual(report["related_tests"]["src/orders/OrderService.java"], ["src/test/java/OrderServiceTest.java"])
        self.assertEqual(report["related_tests"]["billing/invoices.py"], ["tests/test_invoices.py"])
        self.assertEqual(report["without_tests"], ["src/cart/discount.ts"])

    def test_changed_files_from_git(self):
        holder, root = temp_repo({"a.py": "x = 1\n"})
        self.addCleanup(holder.cleanup)
        git(root, "switch", "-q", "-c", "feature/2-y")
        (root / "b.py").write_text("y = 2\n", encoding="utf-8")
        self.assertEqual(impact_scan.changed_files(root, "main"), ["b.py"])


class Checkpoint(unittest.TestCase):
    def test_update_merge_and_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            checks = state / "checks.json"
            checks.write_text(json.dumps({"results": [{"name": "test", "status": "PASS", "command": "npm test",
                                                       "counts": {"passed": 3, "failed": 0}}]}), encoding="utf-8")
            base = ["--item", "43", "--state-dir", str(state)]
            checkpoint.main(base + ["--goal", "Throttle logins", "--branch", "feature/43-throttle", "--done", "baseline"])
            checkpoint.main(base + ["--done", "regression test", "--commit", "abc1234", "--validation", str(checks),
                                    "--blocker", "staging DB unavailable"])
            text = (state / "items" / "43.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("**Checkpoint** · Developer · item #43"))
        self.assertIn("- **Goal:** Throttle logins", text)
        self.assertIn("- [x] baseline\n- [x] regression test", text)
        self.assertIn("- **Last pushed commit:** abc1234", text)
        self.assertIn("- test: PASS, 3 passed, 0 failed (`npm test`)", text)
        self.assertIn("staging DB unavailable", text)

    def test_mirror_edits_the_existing_comment(self):
        calls = []

        def fake_gh(*args, stdin=None):
            calls.append(args)
            if args[:2] == ("api", "repos/o/r/issues/43/comments"):
                return json.dumps([[{"id": 7, "body": "**Checkpoint** · Developer · old", "html_url": "u7"}]])
            return "{}"

        with mock.patch.object(checkpoint, "gh", side_effect=fake_gh):
            self.assertEqual(checkpoint.mirror(43, "Developer", "body", "o/r"), "edited comment u7")
        self.assertEqual(calls[-1][:3], ("api", "-X", "PATCH"))


class PrBody(unittest.TestCase):
    def args(self, **overrides):
        values = dict(issue=43, part_of=40, adr=["ADR-0007"], summary="Throttle logins.", interpretation=[],
                      change=["auth: throttle"], architecture=None, checks=None, baseline=None, test_note=[],
                      security=None, docs=None, breaking=None, guard_ok=True)
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_every_template_section_in_order(self):
        body = pr_body.render(self.args(), "feature/43-login-throttle")
        template = (Path(__file__).resolve().parent.parent / ".github" / "pull_request_template.md").read_text(encoding="utf-8")
        expected = [line for line in template.splitlines() if line.startswith("## ")]
        self.assertEqual([line for line in body.splitlines() if line.startswith("## ")], expected)
        self.assertIn("Closes #43 · Part of #40 · ADR-0007", body)
        self.assertEqual(body.count("Closes #"), 1)
        self.assertIn("## Security considerations\n\nNone", body)

    def test_checklist_ticks_only_what_evidence_proves(self):
        with tempfile.TemporaryDirectory() as tmp:
            checks = Path(tmp) / "c.json"
            checks.write_text(json.dumps({"results": [{"name": "test", "command": "npm test", "status": "PASS",
                                                       "counts": {"passed": 4, "failed": 0}}]}), encoding="utf-8")
            body = pr_body.render(self.args(checks=str(checks)), "feature/43-login-throttle")
            wrong_branch = pr_body.render(self.args(checks=str(checks), guard_ok=False), "feature/44-other")
        self.assertIn("- [x] Branch follows", body)
        self.assertIn("- [x] Tests, lint and build pass", body)
        self.assertIn("- [ ] Every acceptance criterion", body)
        self.assertIn("| `npm test` | PASS - 4 passed, 0 failed |", body)
        self.assertIn("- [ ] Branch follows", wrong_branch)
        self.assertIn("- [ ] No secrets", wrong_branch)


class DepsCheck(unittest.TestCase):
    NOW = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)

    def fake(self, licences, published, vulns):
        def fetch(url, payload=None):
            if "api.osv.dev" in url:
                return {"vulns": [{"id": v} for v in vulns]}
            if "/versions/" in url:
                return {"licenses": licences, "publishedAt": published}
            return {"versions": [{"versionKey": {"version": "1.2.0"}, "isDefault": True, "publishedAt": published}]}
        return fetch

    def evaluate(self, *fake_args):
        with mock.patch.object(deps_check, "fetch", side_effect=self.fake(*fake_args)):
            return deps_check.evaluate("npm", "left-pad", None, now=self.NOW)

    def test_verdicts(self):
        self.assertEqual(self.evaluate(["MIT"], "2026-06-01T00:00:00Z", [])["verdict"], "OK")
        self.assertEqual(self.evaluate(["GPL-3.0-only"], "2026-06-01T00:00:00Z", [])["verdict"], "REVIEW")
        self.assertEqual(self.evaluate(["MIT"], "2022-01-01T00:00:00Z", [])["verdict"], "REVIEW")
        self.assertEqual(self.evaluate([], "2026-06-01T00:00:00Z", [])["verdict"], "REVIEW")
        rejected = self.evaluate(["MIT"], "2026-06-01T00:00:00Z", ["GHSA-1234"])
        self.assertEqual((rejected["verdict"], rejected["version"]), ("REJECT", "1.2.0"))

    def test_network_failure_is_blocked(self):
        import urllib.error
        with mock.patch.object(deps_check, "fetch", side_effect=urllib.error.URLError("offline")):
            self.assertEqual(deps_check.main(["--ecosystem", "npm", "--name", "x"]), 2)


if __name__ == "__main__":
    unittest.main()
