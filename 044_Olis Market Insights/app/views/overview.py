"""Page 1: GTM overview. Headline KPIs and the monthly lead trend."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import data_dates, gtm_monthly, kpis
from ui import COLORS, kpi_tile, lang, tr
from src.i18n import fmt_month, fmt_num, fmt_pct

# KPI tiles on this page: (section title key, [kpi_key, ...]).
# tests/test_translations.py reads this constant to check every tile has texts.
TILES = [
    ("overview.section.funnel", ["mql_count", "lead_to_win_rate_60d_tracked", "sales_cycle_median_days"]),
    ("overview.section.sellers", ["seller_activation_rate_full_window", "time_to_first_sale_median_days",
                                  "gmv_90d_per_won_seller"]),
    ("overview.section.buyers", ["buyer_repeat_rate"]),
]

code = lang()
st.title(tr("overview.title"))
st.write(tr("overview.intro"))

# ------------------------------------------------------------ KPI tiles
k = kpis()
for section, keys in TILES:
    st.subheader(tr(section))
    columns = st.columns(3)
    for column, key in zip(columns, keys):
        kpi_tile(column, k, key)

# --------------------------------------------------------- monthly trend
st.subheader(tr("overview.trend.title"))
m = gtm_monthly().copy()
m["month_label"] = [fmt_month(d, code) for d in m["cohort_month"]]
m["hover_leads"] = [tr("overview.trend.hover_leads", month=lbl, leads=fmt_num(n, code))
                    for lbl, n in zip(m["month_label"], m["leads"])]
m["hover_win"] = [tr("overview.trend.hover_win", month=lbl, rate=fmt_pct(r, code),
                     won=fmt_num(w, code), leads=fmt_num(n, code))
                  for lbl, r, w, n in zip(m["month_label"], m["lead_to_win_rate_60d"], m["won_60d"], m["leads"])]

groups = [
    (True, tr("overview.trend.complete"), COLORS["series_1"]),
    (False, tr("overview.trend.incomplete"), COLORS["muted"]),
]


def bar_chart(value_col: str, hover_col: str, y_title: str, y_format: str, show_legend: bool) -> go.Figure:
    """One measure per chart: never two y-axes on one chart."""
    fig = go.Figure()
    for tracked, name, color in groups:
        part = m[m["deal_tracking_complete"] == tracked]
        fig.add_bar(x=part["month_label"], y=part[value_col], name=name, marker_color=color,
                    customdata=part[hover_col], hovertemplate="%{customdata}<extra></extra>",
                    showlegend=show_legend)
    fig.update_layout(
        height=260, margin=dict(l=10, r=10, t=10, b=10), bargap=0.35, barcornerradius=4,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        separators=",." if code == "de" else ".,",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis=dict(categoryorder="array", categoryarray=list(m["month_label"]), showgrid=False),
        yaxis=dict(title=y_title, tickformat=y_format, gridcolor=COLORS["grid"], zeroline=False),
    )
    return fig


st.plotly_chart(bar_chart("leads", "hover_leads", tr("overview.trend.leads"), ",d", True),
                width="stretch")
st.plotly_chart(bar_chart("lead_to_win_rate_60d", "hover_win", tr("overview.trend.win"), ".0%", False),
                width="stretch")
st.caption(tr("overview.trend.caption", tracking_start=fmt_month(data_dates()["tracking_start"], code)))

with st.expander(tr("common.show_table")):
    st.dataframe(pd.DataFrame({
        tr("overview.table.month"): m["month_label"],
        tr("overview.table.leads"): [fmt_num(v, code) for v in m["leads"]],
        tr("overview.table.won"): [fmt_num(v, code) for v in m["won_60d"]],
        tr("overview.table.rate"): [fmt_pct(v, code) for v in m["lead_to_win_rate_60d"]],
        tr("overview.table.tracked"): [tr("common.yes") if v else tr("common.no")
                                       for v in m["deal_tracking_complete"]],
    }), hide_index=True, width="stretch")

# ------------------------------------------------------------- so what?
st.info(f"**{tr('common.so_what')}** {tr('overview.so_what.text')}")
