"""Translation tests. Run from the project root:
    python -m unittest discover tests

They fail when:
    - a text exists in English but is missing or empty in another language
    - a language has a key that English does not have (typo or leftover)
    - the {placeholders} differ between languages (the page would crash)
    - the code uses a key that is not in the translation file
"""

import ast
import json
import re
import string
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "src" / "i18n" / "translations.json").read_text(encoding="utf-8"))
TEXTS = DATA["texts"]
ENGLISH = TEXTS["en"]


def placeholders(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


class TranslationTests(unittest.TestCase):
    def test_every_language_is_declared(self):
        self.assertEqual(set(DATA["languages"]), set(TEXTS))

    def test_no_key_missing_or_empty(self):
        for code, texts in TEXTS.items():
            with self.subTest(language=code):
                missing = [k for k in ENGLISH if not str(texts.get(k, "")).strip()]
                self.assertEqual(missing, [], f"{code}: missing or empty keys")

    def test_no_extra_keys(self):
        for code, texts in TEXTS.items():
            with self.subTest(language=code):
                self.assertEqual(sorted(set(texts) - set(ENGLISH)), [], f"{code}: keys not in English")

    def test_same_placeholders(self):
        for code, texts in TEXTS.items():
            for key, text in ENGLISH.items():
                with self.subTest(language=code, key=key):
                    self.assertEqual(placeholders(texts[key]), placeholders(text))

    def test_every_key_used_in_code_exists(self):
        used = set()
        pattern = re.compile(r"""\btr?\(\s*f?["']([a-z0-9_.{}]+)["']""")
        for path in list((ROOT / "app").rglob("*.py")) + list((ROOT / "src").rglob("*.py")):
            for key in pattern.findall(path.read_text(encoding="utf-8")):
                if "{" not in key:                  # f-string keys: see the KPI test below
                    used.add(key)
        self.assertGreater(len(used), 20, "the search found almost no keys; is the pattern broken?")
        self.assertEqual(sorted(used - set(ENGLISH)), [])

    def test_kpi_tiles_on_pages_have_texts(self):
        """Each page declares its tiles in a constant TILES. Read it without running the page."""
        kpi_keys, sections = set(), set()
        for path in (ROOT / "app" / "views").rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "TILES" for t in node.targets):
                    for section, keys in ast.literal_eval(node.value):
                        sections.add(section)
                        kpi_keys |= set(keys)
        self.assertGreater(len(kpi_keys), 0, "no TILES constant found in app/views")
        for key in sorted(kpi_keys):
            with self.subTest(kpi=key):
                self.assertIn(f"kpi.{key}.name", ENGLISH)
                self.assertIn(f"kpi.{key}.help", ENGLISH)
        self.assertEqual(sorted(sections - set(ENGLISH)), [])

    def test_kpi_keys_have_name_and_help(self):
        kpis = {k.split(".")[1] for k in ENGLISH if k.startswith("kpi.")}
        for kpi in kpis:
            with self.subTest(kpi=kpi):
                self.assertIn(f"kpi.{kpi}.name", ENGLISH)
                self.assertIn(f"kpi.{kpi}.help", ENGLISH)


if __name__ == "__main__":
    unittest.main()
