"""Tests for the SIMULATED EventPro data (src/simulate.py). Run from the project root:
    python -m unittest discover tests

They need no Kaggle data. They check that:
    - the generator is reproducible (same seed -> same data)
    - the planned story and the planned defects are really in the data
    - the simulation never touches the Olist warehouse
    - every simulated table is clearly named sim_ and every report says SYNTHETIC
"""

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import simulate  # noqa: E402


class GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(simulate.SEED)
        cls.web = simulate.generate_web(rng)
        cls.crm = simulate.generate_crm(rng)

    def test_reproducible(self):
        rng = np.random.default_rng(simulate.SEED)
        web2 = simulate.generate_web(rng)
        self.assertTrue(self.web.equals(web2), "same seed must give the same web data")

    def test_two_full_years_every_channel_every_day(self):
        days = (simulate.REFERENCE_DATE - simulate.START).days + 1
        self.assertEqual(len(self.web), days * len(simulate.CHANNELS))
        self.assertEqual(self.web["date"].min(), simulate.START)
        self.assertEqual(self.web["date"].max(), simulate.REFERENCE_DATE)

    def test_funnel_never_grows(self):
        self.assertTrue((self.web["quote_requests"] <= self.web["sessions"]).all())
        self.assertTrue((self.web["bookings"] <= self.web["quote_requests"]).all())
        self.assertTrue((self.web[["sessions", "quote_requests", "bookings"]] >= 0).all().all())

    def test_crm_rules(self):
        crm = self.crm
        self.assertTrue(crm["opportunity_id"].is_unique)
        self.assertTrue(set(crm["status"]) <= {"won", "lost", "open"})
        self.assertTrue(crm.loc[crm.status == "open", "closed_date"].isna().all(), "open deals have no close date")
        self.assertTrue(crm.loc[crm.status != "lost", "loss_reason"].isna().all(), "only lost deals have a reason")
        closed = crm[crm.status != "open"]
        self.assertTrue((closed["closed_date"] >= closed["created_date"]).all(), "no deal closes before it starts")

    def test_planned_defects_exist(self):
        lost = self.crm[self.crm.status == "lost"]
        self.assertGreater(lost["loss_reason"].isna().mean(), 0.03, "planned: some loss reasons not recorded")
        self.assertGreater(self.crm["industry"].isna().mean(), 0.01, "planned: some industries missing")


@unittest.skipUnless(simulate.DB_PATH.exists(), "simulation missing: run python src/simulate.py first")
class SimulationDatabaseTests(unittest.TestCase):
    def setUp(self):
        import duckdb
        self.con = duckdb.connect(str(simulate.DB_PATH), read_only=True)

    def tearDown(self):
        self.con.close()

    def test_separate_from_olist(self):
        self.assertNotEqual(simulate.DB_PATH.name, "warehouse.duckdb")
        tables = [r[0] for r in self.con.execute("SHOW TABLES").fetchall()]
        self.assertTrue(all(t.startswith("sim_") for t in tables), f"every table must start with sim_: {tables}")

    def test_planned_story(self):
        one = lambda sql: self.con.execute(sql).fetchone()[0]
        ai_sessions = one("SELECT session_share_2025 FROM sim_channel_summary WHERE channel = 'ai_referral'")
        ai_bookings = one("SELECT booking_share_2025 FROM sim_channel_summary WHERE channel = 'ai_referral'")
        self.assertGreater(ai_bookings, 2 * ai_sessions, "GEO: AI answers convert far better than average")
        self.assertLess(one("SELECT sessions_yoy FROM sim_channel_summary WHERE channel = 'organic_search'"), 0)
        self.assertEqual(one("SELECT COUNT(*) FROM sim_ai_referral_weekly WHERE is_incident"), 3)

    def test_report_is_labelled(self):
        report = ROOT / "reports" / "analysis" / "07_simulated_eventpro.md"
        if report.exists():
            self.assertIn("SYNTHETIC DATA", report.read_text(encoding="utf-8")[:400])


if __name__ == "__main__":
    unittest.main()
