"""Usage report and complexity-based model choice (Issue #19)."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import ROOT, ROUTING, load

usage_report = load(ROOT / "skills" / "orchestration" / "scripts", "usage_report")
detect_stack = load(ROUTING, "detect_stack")
select_specialist = load(ROUTING, "select_specialist")


def run(agent, item, models, minutes, cost, day="2026-10-09", repo="o/shop", tokens=(10, 500, 4000, 2000)):
    i, o, cr, cw = tokens
    return {"kind": "coordinator" if agent == "coordinator" else "subagent", "agent": agent, "repo": repo,
            "item": item, "stage": "in-development", "end": f"{day}T10:00:00Z", "duration_s": minutes * 60,
            "models": models, "calls": 3, "tool_calls": 5, "compactions": 0, "cost_usd": cost,
            "tokens": {"input": i, "output": o, "cache_read": cr, "cache_write": cw}}


LEDGER = [
    run("developer-java-spring", 43, {"claude-sonnet-5-5": 3}, 20, 1.5),
    run("developer-java-spring", 43, {"claude-opus-5-5": 1}, 10, 2.0),
    run("qa-engineer", 43, {"claude-haiku-5-5": 2}, 5, 0.05),
    run("coordinator", None, {"claude-sonnet-5-5": 4}, 2, 0.4, day="2026-10-10"),
    run("developer-react", 44, {"claude-sonnet-5-5": 2}, 15, 1.0, repo="o/web"),
]


class UsageReport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = Path(self.tmp.name) / "ledger.jsonl"
        self.ledger.write_text("\n".join(json.dumps(r) for r in LEDGER) + "\nnot json\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_aggregate_by_agent_item_model_repo_and_day(self):
        records = usage_report.load(self.ledger)
        self.assertEqual(len(records), 5, "a corrupt line is skipped")
        by_agent = usage_report.aggregate(records, "agent")
        self.assertEqual(by_agent["developer-java-spring"]["runs"], 2)
        self.assertAlmostEqual(by_agent["developer-java-spring"]["cost_usd"], 3.5)
        self.assertEqual(usage_report.aggregate(records, "item")["(coordination)"]["runs"], 1)
        self.assertAlmostEqual(usage_report.aggregate(records, "model")["claude-opus-5-5"]["cost_usd"], 2.0)
        self.assertEqual(set(usage_report.aggregate(records, "repo")), {"o/shop", "o/web"})
        self.assertEqual(set(usage_report.aggregate(records, "day")), {"2026-10-09", "2026-10-10"})

    def test_filters(self):
        records = usage_report.load(self.ledger)
        self.assertEqual(len(usage_report.select(records, None, None, 43)), 3)
        self.assertEqual(len(usage_report.select(records, None, "o/web", None)), 1)
        self.assertEqual(len(usage_report.select(records, "2026-10-10", None, None)), 1)

    def test_github_line_is_short_and_has_no_detail(self):
        line = usage_report.github_line(usage_report.select(usage_report.load(self.ledger), None, None, 43), " #43")
        self.assertLess(len(line), 200)
        self.assertTrue(line.startswith("Usage #43: 3 runs, 35 min"))
        self.assertIn("~$3.55 API-eq", line)
        self.assertNotIn("developer-java-spring", line)

    def test_cli_formats(self):
        with mock.patch("builtins.print") as printed:
            usage_report.main(["--ledger", str(self.ledger), "--item", "99", "--format", "github"])
        self.assertEqual(printed.call_args[0][0], "Usage #99: no runs recorded")
        with mock.patch("builtins.print") as printed:
            usage_report.main(["--ledger", str(self.ledger), "--by", "model", "--format", "json"])
        data = json.loads(printed.call_args[0][0])
        self.assertIn("claude-haiku-5-5", data["groups"])
        self.assertAlmostEqual(data["total"]["cost_usd"], 4.95)
        table = usage_report.table(usage_report.aggregate(usage_report.load(self.ledger), "agent"), "agent")
        self.assertTrue(table.splitlines()[2].startswith("| developer-java-spring |"), "sorted by cost")


class ComplexityModels(unittest.TestCase):
    def test_complexity_line_and_models(self):
        catalogue = detect_stack.load_catalogue()
        self.assertEqual(catalogue["complexity_models"], {"S": "sonnet", "M": "sonnet", "L": "opus"})
        self.assertEqual(select_specialist.parse_complexity("Touches: a/**\nComplexity: L (migration)"), "L")
        self.assertIsNone(select_specialist.parse_complexity("no line"))
        self.assertEqual(select_specialist.model_for("L", catalogue), "opus")
        self.assertEqual(select_specialist.model_for(None, catalogue), "sonnet")
        self.assertNotIn("fable", json.dumps(catalogue).lower())


if __name__ == "__main__":
    unittest.main()
