"""Page 2: Marketing & channels. Channel quality, tracking gap and landing pages.

Reads mart_channel_performance, mart_kpi_summary and the result table of
analysis/03_landing_pages.py. Nothing is recalculated here.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import analysis_result, channels, kpis
from ui import COLORS, kpi_tile, lang, tr
from src.i18n import fmt_num, fmt_pct

# KPI tiles on this page (read by tests/test_translations.py)
TILES = [
    ("marketing.section.tracking", ["unattributed_lead_share", "unattributed_win_share"]),
]

code = lang()
SEPARATORS = ",." if code == "de" else ".,"


def base_layout(fig: go.Figure, height: int, x_format: str) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", separators=SEPARATORS,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
        xaxis=dict(tickformat=x_format, gridcolor=COLORS["grid"], zeroline=False, rangemode="tozero"),
        yaxis=dict(showgrid=False),
    )
    return fig


def channel_name(origin: str) -> str:
    return tr(f"channel.{origin}")


st.title(tr("marketing.title"))
st.write(tr("marketing.intro"))


k = kpis()
for section, keys in TILES:
    st.subheader(tr(section))
    columns = st.columns(len(keys) + 1)
    for column, key in zip(columns, keys):
        kpi_tile(column, k, key)
    columns[-1].warning(tr("marketing.tracking.warning"))

st.subheader(tr("marketing.channels.title"))
ch = channels().sort_values("lead_to_win_rate").copy()      # ascending: best ends up on top
ch["label"] = ch["origin"].map(channel_name)
ch["hover"] = [tr("marketing.channels.hover", channel=lbl, rate=fmt_pct(r, code),
                  low=fmt_pct(lo, code), high=fmt_pct(hi, code),
                  won=fmt_num(w, code), leads=fmt_num(n, code))
               for lbl, r, lo, hi, w, n in zip(ch["label"], ch["lead_to_win_rate"], ch["lead_to_win_ci_low"],
                                               ch["lead_to_win_ci_high"], ch["won"], ch["leads"])]

fig = go.Figure()
for small, name, color, symbol in [(False, tr("marketing.channels.rankable"), COLORS["series_1"], "circle"),
                                   (True, tr("marketing.channels.small"), COLORS["muted"], "circle-open")]:
    part = ch[ch["is_small_sample"] == small]
    fig.add_scatter(
        x=part["lead_to_win_rate"], y=part["label"], mode="markers", name=name,
        marker=dict(color=color, size=10, symbol=symbol, line=dict(width=2, color=color)),
        error_x=dict(type="data", symmetric=False, color=color, thickness=2, width=0,
                     array=part["lead_to_win_ci_high"] - part["lead_to_win_rate"],
                     arrayminus=part["lead_to_win_rate"] - part["lead_to_win_ci_low"]),
        customdata=part["hover"], hovertemplate="%{customdata}<extra></extra>",
    )
overall = k.loc["lead_to_win_rate_60d_tracked", "value"]
fig.add_vline(x=overall, line_dash="dot", line_color=COLORS["muted"],
              annotation_text=f"{tr('marketing.channels.overall')}: {fmt_pct(overall, code)}",
              annotation_position="top")
fig.update_yaxes(categoryorder="array", categoryarray=list(ch["label"]))
st.plotly_chart(base_layout(fig, 420, ".0%"), width="stretch")
st.caption(tr("marketing.channels.caption"))


st.subheader(tr("marketing.activated.title"))
act = ch.dropna(subset=["activated_per_1000_leads"]).sort_values("activated_per_1000_leads").copy()
act["hover"] = [tr("marketing.activated.hover", channel=lbl, value=fmt_num(v, code),
                   sellers=fmt_num(s, code))
                for lbl, v, s in zip(act["label"], act["activated_per_1000_leads"], act["won_sellers_full_window"])]
fig = go.Figure()
for small, name, color in [(False, tr("marketing.activated.enough"), COLORS["series_1"]),
                           (True, tr("marketing.activated.small"), COLORS["muted"])]:
    part = act[act["is_small_seller_sample"] == small]
    fig.add_bar(x=part["activated_per_1000_leads"], y=part["label"], orientation="h", name=name,
                marker_color=color, customdata=part["hover"], hovertemplate="%{customdata}<extra></extra>")
fig.update_layout(barcornerradius=4, bargap=0.35)
fig.update_yaxes(categoryorder="array", categoryarray=list(act["label"]))
st.plotly_chart(base_layout(fig, 400, ",d"), width="stretch")
st.caption(tr("marketing.activated.caption"))

with st.expander(tr("common.show_table")):
    table = ch.sort_values("leads", ascending=False)
    st.dataframe(pd.DataFrame({
        tr("marketing.table.channel"): table["label"],
        tr("marketing.table.leads"): [fmt_num(v, code) for v in table["leads"]],
        tr("marketing.table.won"): [fmt_num(v, code) for v in table["won"]],
        tr("marketing.table.rate"): [fmt_pct(v, code) for v in table["lead_to_win_rate"]],
        tr("marketing.table.ci"): [f"{fmt_pct(lo, code)} – {fmt_pct(hi, code)}"
                                   for lo, hi in zip(table["lead_to_win_ci_low"], table["lead_to_win_ci_high"])],
        tr("marketing.table.sellers"): [fmt_num(v, code) for v in table["won_sellers_full_window"]],
        tr("marketing.table.activation"): ["–" if pd.isna(v) else fmt_pct(v, code, 0)
                                           for v in table["activation_rate"]],
        tr("marketing.table.activated"): ["–" if pd.isna(v) else fmt_num(v, code)
                                          for v in table["activated_per_1000_leads"]],
    }), hide_index=True, width="stretch")

st.info(f"**{tr('common.so_what')}** {tr('marketing.so_what.text')}")


st.divider()
st.subheader(tr("marketing.pages.title"))
st.write(tr("marketing.pages.intro"))

pages = analysis_result("landing_pages")
if pages is None:
    st.info(tr("common.run_analysis", script="analysis\\03_landing_pages.py"))
    st.stop()

pages = pages.copy()
pages["differs"] = pages["p_fair_bh"] < 0.05
c1, c2, _ = st.columns(3)
c1.metric(tr("marketing.pages.naive"), fmt_num(int((pages["p_naive"] < 0.05).sum()), code),
          help=tr("marketing.pages.naive_help"), border=True)
c2.metric(tr("marketing.pages.fair"), fmt_num(int(pages["differs"].sum()), code),
          help=tr("marketing.pages.fair_help"), border=True)
c1.caption(tr("basis.n", n=fmt_num(len(pages), code)))
c2.caption(tr("basis.n", n=fmt_num(len(pages), code)))

pages = pages.sort_values("rate")
pages["hover"] = [tr("marketing.pages.hover", page=p, rate=fmt_pct(r, code), low=fmt_pct(lo, code),
                     high=fmt_pct(hi, code), expected=fmt_pct(e, code), channel=channel_name(o),
                     share=fmt_pct(s, code, 0), leads=fmt_num(n, code))
                  for p, r, lo, hi, e, o, s, n in zip(pages["page"], pages["rate"], pages["ci_low"], pages["ci_high"],
                                                      pages["expected"], pages["main_origin"],
                                                      pages["main_origin_share"], pages["leads"])]
fig = go.Figure()
for differs, name, color in [(True, tr("marketing.pages.observed_differs"), COLORS["series_1"]),
                             (False, tr("marketing.pages.observed_same"), COLORS["muted"])]:
    part = pages[pages["differs"] == differs]
    fig.add_scatter(
        x=part["rate"], y=part["page"], mode="markers", name=name,
        marker=dict(color=color, size=10),
        error_x=dict(type="data", symmetric=False, color=color, thickness=2, width=0,
                     array=part["ci_high"] - part["rate"], arrayminus=part["rate"] - part["ci_low"]),
        customdata=part["hover"], hovertemplate="%{customdata}<extra></extra>",
    )
fig.add_scatter(x=pages["expected"], y=pages["page"], mode="markers", name=tr("marketing.pages.expected"),
                marker=dict(symbol="diamond-open", size=11, color=COLORS["ink_secondary"], line=dict(width=2)),
                hoverinfo="skip")
fig.update_yaxes(categoryorder="array", categoryarray=list(pages["page"]))
st.plotly_chart(base_layout(fig, 560, ".0%"), width="stretch")
st.caption(tr("marketing.pages.caption"))

# Where the untracked leads arrive
st.subheader(tr("marketing.pages.untracked_title"))
verdict = {True: "above", False: "below"}
table = pages.sort_values("untracked_leads", ascending=False)
st.dataframe(pd.DataFrame({
    tr("marketing.pages.table.page"): table["page"],
    tr("marketing.pages.table.leads"): [fmt_num(v, code) for v in table["leads"]],
    tr("marketing.pages.table.untracked"): [fmt_num(v, code) for v in table["untracked_leads"]],
    tr("marketing.pages.table.rate"): [fmt_pct(v, code) for v in table["rate"]],
    tr("marketing.pages.table.expected"): [fmt_pct(v, code) for v in table["expected"]],
    tr("marketing.pages.table.verdict"): [tr(f"marketing.pages.verdict.{verdict[r > e]}") if d
                                          else tr("marketing.pages.verdict.none")
                                          for d, r, e in zip(table["differs"], table["rate"], table["expected"])],
    tr("marketing.pages.table.channel"): [f"{channel_name(o)} ({fmt_pct(s, code, 0)})"
                                          for o, s in zip(table["main_origin"], table["main_origin_share"])],
}), hide_index=True, width="stretch")
st.caption(tr("marketing.pages.untracked_caption"))
