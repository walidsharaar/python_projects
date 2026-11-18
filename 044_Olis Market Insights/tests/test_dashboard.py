"""Dashboard smoke tests: every page renders in every language without errors.

Run from the project root (needs the warehouse, so after src\\warehouse.py
and the analysis scripts):
    python -m unittest discover tests

Streamlit's AppTest runs the app without a browser. It cannot judge how a
page LOOKS (layout, right-to-left), only that it runs, shows the expected
elements and has no missing texts. Look at it yourself with:
    streamlit run app\\Home.py
"""

import json
import os
import re
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
HOME = str(ROOT / "app" / "Home.py")
LANGUAGES = list(json.loads((ROOT / "src" / "i18n" / "translations.json")
                            .read_text(encoding="utf-8"))["languages"])
# t() shows a missing text as "[some.key]"; it must never reach the screen
MISSING_TEXT = re.compile(r"\[[a-z_]+\.[a-z0-9_.]+\]")

# page file -> (number of KPI tiles / metrics, number of charts)
PAGES = {
    "views/overview.py": (7, 2),
    "views/marketing.py": (4, 3),
    "views/sellers.py": (3, 4),
    "views/experiments.py": (5, 0),
    "views/recommendations.py": (0, 0),
    "views/data_quality.py": (2, 0),
}


def visible_texts(at: AppTest) -> list[str]:
    texts = []
    for kind in ("title", "subheader", "markdown", "caption", "info", "warning", "success", "error"):
        texts += [str(e.value) for e in getattr(at, kind)]
    texts += [f"{m.label} {m.value}" for m in at.metric]
    for df in at.dataframe:
        frame = df.value
        texts += [str(c) for c in frame.columns] + [str(v) for v in frame.to_numpy().ravel()]
    return texts


@unittest.skipUnless(Path(os.environ.get("GTM_WAREHOUSE", ROOT / "database" / "warehouse.duckdb")).exists(),
                     "warehouse missing: run src/clean.py and src/warehouse.py first")
class DashboardTests(unittest.TestCase):
    def render(self, page: str, lang: str) -> AppTest:
        at = AppTest.from_file(HOME, default_timeout=90)
        at.session_state["lang"] = lang
        at.run()
        if page != "views/overview.py":              # overview is the default page
            at.switch_page(page).run()
        return at

    def test_every_page_in_every_language(self):
        for page, (metrics, charts) in PAGES.items():
            for lang in LANGUAGES:
                with self.subTest(page=page, language=lang):
                    at = self.render(page, lang)
                    self.assertEqual(len(at.exception), 0, [e.message for e in at.exception])
                    self.assertEqual(len(at.metric), metrics, "number of KPI tiles / metrics")
                    self.assertEqual(len(at.get("plotly_chart")), charts, "number of charts")
                    missing = [t for t in visible_texts(at) if MISSING_TEXT.search(t)]
                    self.assertEqual(missing, [], "texts missing in the translation file")

    def test_language_changes_text_not_numbers(self):
        """The same KPI must show the same number in every language (only the format differs)."""
        digits = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
        values = {}
        for lang in LANGUAGES:
            at = self.render("views/overview.py", lang)
            # keep only the digits: '10.6%', '10,6 %' and '۱۰٫۶٪' all become '106'
            values[lang] = ["".join(ch for ch in m.value.translate(digits) if ch.isdigit()) for m in at.metric]
        for lang in LANGUAGES[1:]:
            self.assertEqual(values[lang], values[LANGUAGES[0]], f"{lang} shows different numbers")


if __name__ == "__main__":
    unittest.main()
