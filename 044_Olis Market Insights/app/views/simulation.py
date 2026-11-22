"""Page: EventPro simulation. SEO/GEO, channel cost and enterprise win/loss.

SYNTHETIC DATA from src/simulate.py, read from database/simulation.duckdb.
It never mixes with the Olist warehouse. The banner at the top is required:
nobody may mistake these numbers for real results. Nothing is calculated
here; every number comes from sql/simulation or analysis/07.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import (analysis_result, simulation_exists, sim_ai_weekly, sim_channels, sim_kpis,
                  sim_loss_reasons, sim_response_time, sim_winloss)
from ui import COLORS, SEQUENTIAL_BLUE, SERIES, kpi_tile, lang, tr
from src.i18n import fmt_num, fmt_pct

# KPI tiles on this page (read by tests/test_translations.py)
TILES = [
    ("sim.section.kpis", ["sim_ai_referral_booking_share_2025", "sim_cost_per_booking_paid_2025",
                          "sim_enterprise_win_rate", "sim_loss_reason_missing_share"]),
]

code = lang()
SEPARATORS = ",." if code == "de" else ".,"


def layout(fig: go.Figure, height: int, x_format: str | None = None) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=30, b=10), separators=SEPARATORS,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
        xaxis=dict(tickformat=x_format, gridcolor=COLORS["grid"], zeroline=False),
        yaxis=dict(showgrid=False),
    )
    return fig


st.warning(tr("sim.banner"), icon="⚠️")
st.title(tr("sim.title"))
st.write(tr("sim.intro"))

if not simulation_exists():
    st.info(tr("sim.missing"))
    st.stop()


k = sim_kpis()
for section, keys in TILES:
    st.subheader(tr(section))
    for column, key in zip(st.columns(len(keys)), keys):
        kpi_tile(column, k, key)


st.subheader(tr("sim.geo.title"))
ch = sim_channels().sort_values("booking_share_2025").copy()
ch["label"] = ch["channel"].map(lambda c: tr(f"sim.channel.{c}"))
fig = go.Figure()
for col, name, color in [("session_share_2025", tr("sim.geo.sessions"), SERIES[0]),
                         ("booking_share_2025", tr("sim.geo.bookings"), SERIES[1])]:
    fig.add_bar(x=ch[col], y=ch["label"], orientation="h", name=name, marker_color=color,
                text=[fmt_pct(v, code) for v in ch[col]], textposition="outside",
                hovertemplate="%{y}: %{text}<extra>" + name + "</extra>")
fig.update_layout(barmode="group")
st.plotly_chart(layout(fig, 420, ".0%"), width="stretch")
organic = ch.set_index("channel").loc["organic_search", "sessions_yoy"]
st.caption(tr("sim.geo.caption", org_yoy=fmt_pct(abs(organic), code)))


st.subheader(tr("sim.tracking.title"))
w = sim_ai_weekly()
fig = go.Figure()
fig.add_scatter(x=w["week"], y=w["ai_share"], mode="lines", name=tr("sim.tracking.ai_share"),
                line=dict(color=SERIES[0], width=2))
incident = w[w["is_incident"]]
fig.add_vrect(x0=incident["week"].min(), x1=incident["week"].max() + pd.Timedelta(days=6),
              fillcolor=COLORS["muted"], opacity=0.2, line_width=0,
              annotation_text=tr("sim.tracking.incident"), annotation_position="top left")
fig = layout(fig, 320)
fig.update_yaxes(tickformat=".0%", showgrid=True, gridcolor=COLORS["grid"])
fig.update_xaxes(showgrid=False)
st.plotly_chart(fig, width="stretch")
st.caption(tr("sim.tracking.caption"))


st.subheader(tr("sim.channels.title"))
table = ch.sort_values("sessions_2025", ascending=False)
st.dataframe(
    {
        tr("sim.col.channel"): list(table["label"]),
        tr("sim.col.sessions"): [fmt_num(v, code) for v in table["sessions_2025"]],
        tr("sim.col.yoy"): [("+" if v > 0 else "") + fmt_pct(v, code) for v in table["sessions_yoy"]],
        tr("sim.col.per_1000"): [fmt_num(v * 1000, code, 1) for v in table["booking_per_session_2025"]],
        tr("sim.col.cost"): [tr("unit.eur", value=fmt_num(v, code)) if v == v else "–"
                             for v in table["cost_per_booking_2025"]],
    },
    hide_index=True, width="stretch",
)


st.subheader(tr("sim.winloss.title"))
wl = sim_winloss().sort_values("win_rate").copy()
wl["label"] = wl["industry"].map(lambda i: tr(f"sim.industry.{i}"))
wl["hover"] = [tr("sim.winloss.hover", industry=lbl, rate=fmt_pct(r, code), low=fmt_pct(lo, code),
                  high=fmt_pct(hi, code), won=fmt_num(w_, code), decided=fmt_num(w_ + l_, code))
               for lbl, r, lo, hi, w_, l_ in zip(wl["label"], wl["win_rate"], wl["win_rate_ci_low"],
                                                 wl["win_rate_ci_high"], wl["won"], wl["lost"])]
fig = go.Figure()
fig.add_scatter(x=wl["win_rate"], y=wl["label"], mode="markers",
                marker=dict(color=SERIES[0], size=10),
                error_x=dict(type="data", symmetric=False, color=SERIES[0], thickness=2, width=0,
                             array=wl["win_rate_ci_high"] - wl["win_rate"],
                             arrayminus=wl["win_rate"] - wl["win_rate_ci_low"]),
                customdata=wl["hover"], hovertemplate="%{customdata}<extra></extra>", showlegend=False)
overall = k.loc["sim_enterprise_win_rate", "value"]
fig.add_vline(x=overall, line_dash="dot", line_color=COLORS["muted"],
              annotation_text=f"{tr('sim.winloss.overall')}: {fmt_pct(overall, code)}", annotation_position="top")
st.plotly_chart(layout(fig, 360, ".0%"), width="stretch")
st.caption(tr("sim.winloss.caption"))


st.subheader(tr("sim.response.title"))
rt = sim_response_time()
fig = go.Figure()
fig.add_bar(x=[tr(f"sim.response.{b}") for b in rt["response_bucket"]], y=rt["win_rate"],
            marker_color=SERIES[0], text=[fmt_pct(v, code) for v in rt["win_rate"]], textposition="outside",
            error_y=dict(type="data", symmetric=False, color=COLORS["ink_secondary"], thickness=1.5,
                         array=rt["win_rate_ci_high"] - rt["win_rate"],
                         arrayminus=rt["win_rate"] - rt["win_rate_ci_low"]),
            hovertemplate="%{x}: %{text}<extra></extra>")
fig = layout(fig, 320)
fig.update_yaxes(tickformat=".0%", rangemode="tozero")
st.plotly_chart(fig, width="stretch")
reg = analysis_result("sim_winloss_regression")
odds = "–"
if reg is not None and (reg["term"] == "response = c_over_24h").any():
    odds = fmt_num(reg.loc[reg["term"] == "response = c_over_24h", "odds_ratio"].iloc[0], code, 2)
st.caption(tr("sim.response.caption", odds=odds))


st.subheader(tr("sim.reasons.title"))
lr = sim_loss_reasons()
pivot = lr.pivot_table(index="loss_reason", columns="industry", values="share", fill_value=0)
pivot = pivot.loc[pivot.mean(axis=1).sort_values().index]
fig = go.Figure(go.Heatmap(
    z=pivot.values, x=[tr(f"sim.industry.{i}") for i in pivot.columns],
    y=[tr(f"sim.reason.{r}") for r in pivot.index], colorscale=SEQUENTIAL_BLUE,
    text=[[fmt_pct(v, code, 0) for v in row] for row in pivot.values], texttemplate="%{text}",
    hovertemplate="%{y} · %{x}: %{text}<extra></extra>", showscale=False))
st.plotly_chart(layout(fig, 380), width="stretch")
st.caption(tr("sim.reasons.caption"))


st.subheader(tr("common.so_what"))
st.info(tr("sim.so_what.text"))
