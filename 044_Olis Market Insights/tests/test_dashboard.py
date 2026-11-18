"""Dashboard smoke test: every page renders in every language without errors.

Run from the project root (needs the warehouse, so after src\\warehouse.py):
    python -m unittest discover tests

Streamlit's AppTest runs the app without a browser. It cannot judge how a
page LOOKS (layout, right-to-left), only that it runs and shows the expected
elements. Look at it yourself with: streamlit run app\\Home.py
"""

import json
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
HOME = str(ROOT / "app" / "Home.py")
LANGUAGES = list(json.loads((ROOT / "src" / "i18n" / "translations.json")
                            .read_text(encoding="utf-8"))["languages"])


@unittest.skipUnless((ROOT / "database" / "warehouse.duckdb").exists(),
                     "warehouse missing: run src/clean.py and src/warehouse.py first")
class DashboardTests(unittest.TestCase):
    def render(self, lang: str) -> AppTest:
        at = AppTest.from_file(HOME, default_timeout=60)
        at.session_state["lang"] = lang
        return at.run()

    def test_overview_renders_in_every_language(self):
        for lang in LANGUAGES:
            with self.subTest(language=lang):
                at = self.render(lang)
                self.assertEqual(len(at.exception), 0, [e.message for e in at.exception])
                self.assertEqual(len(at.error), 0)
                self.assertEqual(len(at.metric), 7, "expected 7 KPI tiles")
                self.assertEqual(len(at.get("plotly_chart")), 2, "expected 2 charts")

    def test_language_changes_text_not_numbers(self):
        """The same KPI must show the same number in every language (only the format differs)."""
        digits = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
        values = {}
        for lang in LANGUAGES:
            at = self.render(lang)
            # keep only the digits: '10.6%', '10,6 %' and '۱۰٫۶٪' all become '106'
            values[lang] = ["".join(ch for ch in m.value.translate(digits) if ch.isdigit()) for m in at.metric]
        for lang in LANGUAGES[1:]:
            self.assertEqual(values[lang], values[LANGUAGES[0]], f"{lang} shows different numbers")


if __name__ == "__main__":
    unittest.main()
