"""Tests for the automated GTM report (without AI). Run from the project root:
    python -m unittest discover tests
"""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import weekly_report as report  # noqa: E402
from src.i18n import languages  # noqa: E402

MISSING_TEXT = re.compile(r"\[[a-z_]+\.[a-z0-9_.]+\]")


@unittest.skipUnless(report.DEFAULT_DB.exists(), "warehouse missing: run src/warehouse.py first")
class WeeklyReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = report.load(report.DEFAULT_DB)
        cls.check = report.latest_month_check(cls.data["monthly"])

    def test_report_in_every_language_has_all_sections_and_texts(self):
        for lang in languages():
            with self.subTest(language=lang):
                text = report.build_report(self.data, self.check, lang, None, "skipped")
                self.assertEqual(MISSING_TEXT.findall(text), [], "texts missing in the translation file")
                self.assertEqual(text.count("\n## "), 5, "expected 5 sections")
                for key in report.REPORT_KPIS:
                    self.assertIn(report.t(f"kpi.{key}.name", lang), text)

    def test_anomaly_check_uses_only_tracked_months(self):
        self.assertTrue(self.data["monthly"]["deal_tracking_complete"].all())
        self.assertGreaterEqual(len(self.data["monthly"]), 2)
        self.assertTrue(0 <= self.check["p_value"] <= 1)

    def test_ai_input_contains_only_calculated_numbers(self):
        facts = report.facts_for_ai(self.data, self.check)
        self.assertEqual(set(facts), {"kpis", "latest_month_check", "data_quality", "top_actions"})
        self.assertEqual(set(facts["kpis"]), set(report.REPORT_KPIS))


if __name__ == "__main__":
    unittest.main()
