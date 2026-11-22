"""Page 3: Sellers & cohorts. Activation speed, lead types and buyer retention.

Reads mart_seller_activation_curve, mart_buyer_retention, mart_kpi_summary
and the result table of analysis/02_win_vs_activation.py.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import activation_curve, analysis_result, buyer_retention, kpis
from ui import COLORS, SEQUENTIAL_BLUE, SERIES, kpi_tile, lang, tr
from src.i18n import fmt_month, fmt_num, fmt_pct

# KPI tiles on this page (read by tests/test_translations.py)
TILES = [
    ("sellers.section.activation", ["seller_activation_rate_full_window", "time_to_first_sale_median_days",
                                    "gmv_90d_per_won_seller"]),
]
MIN_SELLERS_PER_MONTH = 20     # Dec 2017 has 3 won sellers: one seller would move the line by 33 points
MIN_COHORT = 1_000             # same rule as analysis/05_cohorts.py
SHOW_MONTHS = 12

code = lang()
SEPARATORS = ",." if code == "de" else ".,"


def layout(fig: go.Figure, height: int, x_format: str | None = None, y_format: str | None = None) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", separators=SEPARATORS,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
    )
    fig.update_xaxes(tickformat=x_format, gridcolor=COLORS["grid"], zeroline=False)
    fig.update_yaxes(tickformat=y_format, gridcolor=COLORS["grid"], zeroline=False)
    return fig


st.title(tr("sellers.title"))
st.write(tr("sellers.intro"))

k = kpis()
for section, keys in TILES:
    st.subheader(tr(section))
    for column, key in zip(st.columns(len(keys)), keys):
        kpi_tile(column, k, key)


st.subheader(tr("sellers.curve.title"))
curve = activation_curve()
curve = curve[(curve["observable_sellers"] == curve["won_sellers"])        # whole month observable
              & (curve["won_sellers"] >= MIN_SELLERS_PER_MONTH)].copy()
curve["month_label"] = [fmt_month(d, code) for d in curve["won_month"]]
months = list(dict.fromkeys(curve.sort_values("won_month")["month_label"]))

fig = go.Figure()
for color, days in zip(SERIES, (30, 60, 90)):                              # fixed slot per window
    part = curve[curve["window_days"] == days]
    name = tr("sellers.curve.days", days=fmt_num(days, code))
    hover = [tr("sellers.curve.hover", month=m, rate=fmt_pct(r, code), days=fmt_num(days, code),
                sellers=fmt_num(n, code))
             for m, r, n in zip(part["month_label"], part["activation_rate"], part["won_sellers"])]
    fig.add_scatter(x=part["month_label"], y=part["activation_rate"], mode="lines+markers", name=name,
                    line=dict(color=color, width=2), marker=dict(size=8, color=color),
                    customdata=hover, hovertemplate="%{customdata}<extra></extra>")
    if len(part):                                                          # direct label at the line end
        fig.add_annotation(x=part["month_label"].iloc[-1], y=part["activation_rate"].iloc[-1], text=name,
                           xanchor="left", xshift=8, showarrow=False, font=dict(color=COLORS["ink_secondary"]))
fig.update_xaxes(categoryorder="array", categoryarray=months, showgrid=False)
fig.update_yaxes(rangemode="tozero")
st.plotly_chart(layout(fig, 340, y_format=".0%"), width="stretch")
st.caption(tr("sellers.curve.caption", min=fmt_num(MIN_SELLERS_PER_MONTH, code)))


types = analysis_result("lead_types")
if types is None:
    st.info(tr("common.run_analysis", script="analysis\\02_win_vs_activation.py"))
else:
    types = types.copy()
    types["label"] = types["lead_group"].map(lambda g: tr(f"lead_type.{g}"))

    st.subheader(tr("sellers.types.title"))
    t1 = types.sort_values("activation_rate")
    fig = go.Figure()
    for small, name, color, symbol in [(False, tr("sellers.types.enough"), COLORS["series_1"], "circle"),
                                       (True, tr("sellers.types.small"), COLORS["muted"], "circle-open")]:
        part = t1[t1["is_small"] == small]
        hover = [tr("sellers.types.hover", type=lbl, rate=fmt_pct(r, code), low=fmt_pct(lo, code),
                    high=fmt_pct(hi, code), activated=fmt_num(a, code), sellers=fmt_num(n, code))
                 for lbl, r, lo, hi, a, n in zip(part["label"], part["activation_rate"], part["ci_low"],
                                                 part["ci_high"], part["activated"], part["sellers"])]
        fig.add_scatter(x=part["activation_rate"], y=part["label"], mode="markers", name=name,
                        marker=dict(color=color, size=10, symbol=symbol, line=dict(width=2, color=color)),
                        error_x=dict(type="data", symmetric=False, color=color, thickness=2, width=0,
                                     array=part["ci_high"] - part["activation_rate"],
                                     arrayminus=part["activation_rate"] - part["ci_low"]),
                        customdata=hover, hovertemplate="%{customdata}<extra></extra>")
    overall = k.loc["seller_activation_rate_full_window", "value"]
    fig.add_vline(x=overall, line_dash="dot", line_color=COLORS["muted"],
                  annotation_text=f"{tr('sellers.types.overall')}: {fmt_pct(overall, code)}",
                  annotation_position="top")
    fig.update_yaxes(categoryorder="array", categoryarray=list(t1["label"]), showgrid=False)
    fig.update_xaxes(rangemode="tozero")
    st.plotly_chart(layout(fig, 340, x_format=".0%"), width="stretch")

    st.subheader(tr("sellers.value.title"))
    t2 = types.sort_values("gmv_share")
    fig = go.Figure()
    for color, col, key in [(SERIES[0], "seller_share", "sellers.value.sellers"),
                            (SERIES[1], "gmv_share", "sellers.value.gmv")]:
        hover = [tr("sellers.value.hover", type=lbl, series=tr(key), share=fmt_pct(v, code))
                 for lbl, v in zip(t2["label"], t2[col])]
        fig.add_bar(x=t2[col], y=t2["label"], orientation="h", name=tr(key), marker_color=color,
                    customdata=hover, hovertemplate="%{customdata}<extra></extra>")
    fig.update_layout(barmode="group", barcornerradius=4, bargap=0.3, bargroupgap=0.1)
    fig.update_yaxes(categoryorder="array", categoryarray=list(t2["label"]), showgrid=False)
    st.plotly_chart(layout(fig, 420, x_format=".0%"), width="stretch")
    st.caption(tr("sellers.value.caption"))

st.info(f"**{tr('common.so_what')}** {tr('sellers.so_what.text')}")


st.divider()
st.subheader(tr("sellers.retention.title"))
r = buyer_retention()
r = r[(r["cohort_customers"] >= MIN_COHORT) & r["month_number"].between(1, SHOW_MONTHS)].copy()
r["cohort_label"] = [fmt_month(d, code) for d in r["cohort_month"]]
r["month_label"] = [tr("sellers.retention.month", n=fmt_num(n, code)) for n in r["month_number"]]
r["hover"] = [tr("sellers.retention.hover", cohort=c, month=m, rate=fmt_pct(v, code, 2),
                 active=fmt_num(a, code), buyers=fmt_num(b, code))
              for c, m, v, a, b in zip(r["cohort_label"], r["month_label"], r["retention_rate"],
                                       r["active_customers"], r["cohort_customers"])]
rows = list(dict.fromkeys(r.sort_values("cohort_month")["cohort_label"]))
cols = [tr("sellers.retention.month", n=fmt_num(n, code)) for n in range(1, SHOW_MONTHS + 1)]
z = r.pivot(index="cohort_label", columns="month_label", values="retention_rate").reindex(index=rows, columns=cols)
hover = r.pivot(index="cohort_label", columns="month_label", values="hover").reindex(index=rows, columns=cols)

fig = go.Figure(go.Heatmap(
    z=z.values, x=cols, y=rows, colorscale=SEQUENTIAL_BLUE, zmin=0, xgap=2, ygap=2,
    customdata=hover.values, hovertemplate="%{customdata}<extra></extra>", hoverongaps=False,
    colorbar=dict(tickformat=".1%", thickness=12),
))
fig.update_yaxes(autorange="reversed", title=tr("sellers.retention.cohort"))
st.plotly_chart(layout(fig, 560), width="stretch")
st.caption(tr("sellers.retention.caption", min=fmt_num(MIN_COHORT, code)))

with st.expander(tr("common.show_table")):
    table = z.map(lambda v: "" if pd.isna(v) else fmt_pct(v, code, 2))
    st.dataframe(table.rename_axis(tr("sellers.retention.cohort")), width="stretch")

st.info(f"**{tr('common.so_what')}** {tr('sellers.retention.so_what')}")
