"""Shared building blocks for all dashboard pages: language, layout, KPI tiles, colors."""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:                 # so that "src.i18n" can be imported
    sys.path.insert(0, str(ROOT))

from src.i18n import fmt_num, fmt_pct, is_rtl, languages, t  # noqa: E402

# Colors from the validated reference palette (dataviz skill, references/palette.md).
# Charts only use these roles; status colors are never used for data series.
COLORS = {
    "series_1": "#2a78d6",      # categorical slot 1 (blue)
    "muted": "#898781",         # recessive: data that is not comparable
    "ink_secondary": "#52514e", # reference marks (e.g. "expected"), not a data series
    "grid": "#e1e0d9",
}
# Categorical slots in fixed order (never cycled, never re-ordered by rank)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
# Sequential blue ramp for magnitude (heatmaps): light = low, dark = high
SEQUENTIAL_BLUE = [[0.0, "#cde2fb"], [0.25, "#86b6ef"], [0.5, "#3987e5"],
                   [0.75, "#1c5cab"], [1.0, "#0d366b"]]


def lang() -> str:
    return st.session_state.get("lang", "en")


def tr(key: str, **values) -> str:
    """Translate in the current language."""
    return t(key, lang(), **values)


def language_selector() -> None:
    options = list(languages())
    st.sidebar.selectbox(
        t("sidebar.language", lang()),
        options,
        format_func=lambda code: languages()[code]["label"],
        key="lang",
    )


def apply_direction() -> None:
    """Persian is written right to left. Charts keep left-to-right axes."""
    if is_rtl(lang()):
        st.markdown(
            """<style>
            .stMainBlockContainer, [data-testid="stSidebarContent"] { direction: rtl; text-align: right; }
            [data-testid="stPlotlyChart"], .stDataFrame { direction: ltr; }
            </style>""",
            unsafe_allow_html=True,
        )


def kpi_tile(column, kpis, key: str, delta: str | None = None, delta_note: str | None = None,
             spark: list | None = None) -> None:
    """One KPI tile: value, how it is calculated, the basis (numerator/denominator), help text.

    The calculation (exec.formula.<key>) and the basis are in the help tooltip (?),
    so the tile stays clean but anyone can answer "how did you calculate this?".
    In German and Persian the help also shows the English term.
    delta: an optional change, e.g. "-3.6 pts"; spark: values for a small trend line.
    """
    row = kpis.loc[key]
    code = lang()
    unit = row["unit"]
    if unit == "rate":
        value = fmt_pct(row["value"], code)
        basis = tr("basis.ratio", num=fmt_num(row["numerator"], code), den=fmt_num(row["denominator"], code))
    elif unit == "brl":                        # average over sellers -> base is the denominator
        value = tr("unit.brl", value=fmt_num(row["value"], code))
        basis = tr("basis.n", n=fmt_num(row["denominator"], code))
    elif unit == "days":                       # median over cases -> base is the numerator
        value = tr("unit.days", value=fmt_num(row["value"], code))
        basis = tr("basis.n", n=fmt_num(row["numerator"], code))
    else:                                      # plain count: the value is its own base
        value, basis = fmt_num(row["value"], code), ""
    help_text = tr(f"kpi.{key}.help")
    if code != "en":
        help_text += "\n\n" + tr("common.english_term", term=t(f"kpi.{key}.name", "en"))
    # The formula goes into the help tooltip (?), so the tile stays clean
    how = tr("exec.how", formula=tr(f"exec.formula.{key}")) + (f" ({basis})" if basis else "")
    help_text = how + "\n\n" + help_text
    column.metric(tr(f"kpi.{key}.name"), value, delta=delta, help=help_text, border=True,
                  delta_description=delta_note, chart_data=spark, chart_type="line")
