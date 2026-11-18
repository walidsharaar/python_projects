"""Translations and number formatting for the dashboard and reports.

All display text lives in translations.json, one key per text:
    t("exec.title", "de")  ->  "Vom Lead zum aktiven Verkäufer"

Code, SQL and column names stay English. Only what a person READS is
translated. Changing the language never changes a calculation.
"""

import json
from functools import lru_cache
from pathlib import Path

FILE = Path(__file__).with_name("translations.json")
DEFAULT_LANG = "en"

_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


@lru_cache(maxsize=1)
def _load() -> dict:
    return json.loads(FILE.read_text(encoding="utf-8"))


def languages() -> dict:
    """{'en': {'label': 'English', 'dir': 'ltr'}, ...} in display order."""
    return _load()["languages"]


def t(key: str, lang: str = DEFAULT_LANG, **values) -> str:
    """Text for a key in a language. Falls back to English, then to the key itself,
    so a missing translation is visible on screen instead of crashing the page."""
    texts = _load()["texts"]
    text = texts.get(lang, {}).get(key) or texts[DEFAULT_LANG].get(key) or f"[{key}]"
    return text.format(**values) if values else text


def is_rtl(lang: str) -> bool:
    return languages().get(lang, {}).get("dir") == "rtl"


# ------------------------------------------------------------- numbers
def fmt_num(value: float, lang: str, digits: int = 0) -> str:
    """1234.5 -> en '1,234.5' | de '1.234,5' | fa '۱٬۲۳۴٫۵'"""
    s = f"{value:,.{digits}f}"
    if lang == "de":
        return s.replace(",", "_").replace(".", ",").replace("_", ".")
    if lang == "fa":
        return s.replace(",", "٬").replace(".", "٫").translate(_PERSIAN_DIGITS)
    return s


def fmt_pct(rate: float, lang: str, digits: int = 1) -> str:
    """0.105 -> en '10.5%' | de '10,5 %' | fa '۱۰٫۵٪'"""
    number = fmt_num(rate * 100, lang, digits)
    return {"de": f"{number} %", "fa": f"{number}٪"}.get(lang, f"{number}%")


def fmt_p(p: float, lang: str) -> str:
    """0.0234 -> 'p = 0.023' | 0.00001 -> 'p < 0.001' (never 'p = 0.000', which looks like an error)"""
    return f"p < {fmt_num(0.001, lang, 3)}" if p < 0.001 else f"p = {fmt_num(p, lang, 3)}"


def fmt_date(date, lang: str) -> str:
    """2018-09-03 -> en '3 Sep 2018' | de '3. Sep. 2018' | fa '۳ سپتامبر ۲۰۱۸'"""
    day = f"{date.day}." if lang == "de" else str(date.day)
    if lang == "fa":
        day = day.translate(_PERSIAN_DIGITS)
    return f"{day} {fmt_month(date, lang)}"


def fmt_month(date, lang: str) -> str:
    """2018-03-01 -> en 'Mar 2018' | de 'März 2018' | fa 'مارس ۲۰۱۸'"""
    name = t(f"month.{date.month}", lang)
    year = str(date.year).translate(_PERSIAN_DIGITS) if lang == "fa" else str(date.year)
    return f"{name} {year}"
