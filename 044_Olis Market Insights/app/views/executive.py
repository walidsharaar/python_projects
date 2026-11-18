"""The GTM screen: one headline, then three tabs. Visual first, little text.

    For executives   KPIs with trend lines, funnel, monthly trend, actions by impact, who sells
    For marketing    KPIs, channel quality quadrant, lead mix, scorecard table, landing pages
    Ask the data     a free local AI model (Ollama) answers from the same numbers

Rules: every number comes from sql/marts or saved analysis results; texts are in
src/i18n/translations.json; formulas sit in the (?) tooltip of each KPI tile.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import (analysis_result, channel_monthly, channel_scorecard, channels, data_quality,
                  executive_funnel, gtm_monthly, kpis, opportunities)
from ui import COLORS, SERIES, kpi_tile, lang, tr
from src import assistant, insights
from src.i18n import fmt_month, fmt_num, fmt_pct

# KPI tiles (read by tests/test_translations.py)
TILES = [
    ("tab.exec", ["lead_to_win_rate_60d_tracked", "seller_activation_rate_full_window",
                  "time_to_first_sale_median_days", "unattributed_win_share"]),
    ("tab.marketing", ["mql_per_month_tracked", "lead_to_win_rate_60d_tracked", "unattributed_lead_share"]),
]
VERDICTS = ["grow", "watch", "review", "fix_tracking", "too_little"]            # fixed order
VERDICT_COLOR = {"grow": SERIES[0], "watch": SERIES[2], "review": SERIES[1],
                 "fix_tracking": COLORS["muted"], "too_little": COLORS["grid"]}
MIX_ORDER = ["organic_search", "paid_search", "social", "direct_traffic", "unknown", "other"]
GLOSSARY = ["lead", "contract", "activation", "gmv", "median", "range", "p", "channel", "cohort", "ab"]

code = lang()
SEPARATORS = ",." if code == "de" else ".,"
k, funnel, monthly = kpis(), executive_funnel(), gtm_monthly()
tracked = monthly[monthly["deal_tracking_complete"]].copy()
tracked["label"] = [fmt_month(d, code) for d in tracked["cohort_month"]]
check = insights.latest_month_check(monthly)
month = fmt_month(check["month"], code)


def layout(fig: go.Figure, height: int, x_format=None, y_format=None, legend=True, title=None) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=40 if title else 25, b=10), showlegend=legend,
                      title=dict(text=title, font=dict(size=14)) if title else None,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", separators=SEPARATORS,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0), barcornerradius=4)
    fig.update_xaxes(tickformat=x_format, gridcolor=COLORS["grid"], zeroline=False)
    fig.update_yaxes(tickformat=y_format, gridcolor=COLORS["grid"], zeroline=False)
    return fig


def num(v) -> str:
    return "–" if pd.isna(v) else fmt_num(v, code)


def pct(v, digits: int = 1) -> str:
    return "–" if pd.isna(v) else fmt_pct(v, code, digits)


def tiles(section: str, extra=None) -> None:
    keys = dict(TILES)[section]
    cols = st.columns(len(keys) + (1 if extra else 0))
    for column, key in zip(cols, keys):
        if key == "lead_to_win_rate_60d_tracked":
            diff = check["rate"] - check["rate_earlier"]
            kpi_tile(column, k, key, spark=list(tracked["lead_to_win_rate_60d"]),
                     delta=("-" if diff < 0 else "+") + tr("exec.points", value=fmt_num(abs(diff) * 100, code, 1)),
                     delta_note=tr("exec.delta.latest", month=month))
        elif key == "mql_per_month_tracked":
            kpi_tile(column, k, key, spark=list(tracked["leads"]))
        else:
            kpi_tile(column, k, key)
    if extra:
        extra(cols[-1])


# ------------------------------------------------------------------ headline
st.title(tr("exec.title"))
st.markdown(tr("exec.headline", won=num(funnel.loc["won", "per_1000_leads"]),
               active=num(funnel.loc["activated", "per_1000_leads"]),
               not_active=pct(1 - funnel.loc["activated", "rate_from_previous"], 0)))
tab_exec, tab_mkt, tab_ask = st.tabs([tr("tab.exec"), tr("tab.marketing"), tr("tab.ask")])

# ============================================================ FOR EXECUTIVES
with tab_exec:
    tiles("tab.exec")
    c1, c2, c3 = st.columns(3)

    # funnel: what happens to 1,000 leads
    stages = [("leads", "exec.funnel.leads"), ("won", "exec.funnel.won"), ("activated", "exec.funnel.activated")]
    values = [funnel.loc[s, "per_1000_leads"] for s, _ in stages]
    fig = go.Figure(go.Funnel(y=[tr(lbl) for _, lbl in stages], x=values, marker=dict(color=SERIES[0]),
                              text=[num(v) for v in values], textinfo="text", hoverinfo="skip",
                              connector=dict(line=dict(color=COLORS["grid"]))))
    c1.plotly_chart(layout(fig, 280, legend=False, title=tr("exec.funnel.title")), width="stretch")

    # monthly trend: two small charts, one measure each (never two y-axes)
    fig = go.Figure(go.Bar(x=tracked["label"], y=tracked["leads"], marker_color=SERIES[0],
                           hovertemplate="%{x}: %{y:,}<extra></extra>"))
    c2.plotly_chart(layout(fig, 280, legend=False, title=tr("x.trend.leads")), width="stretch")
    is_latest = tracked["cohort_month"] == check["month"]
    fig = go.Figure(go.Scatter(x=tracked["label"], y=tracked["lead_to_win_rate_60d"], mode="lines+markers",
                               line=dict(color=SERIES[0], width=2),
                               marker=dict(size=9, color=[SERIES[1] if (l and check["clear_change"]) else SERIES[0]
                                                          for l in is_latest]),
                               hovertemplate="%{x}: %{y:.1%}<extra></extra>"))
    fig.add_hline(y=check["rate_earlier"], line_dash="dot", line_color=COLORS["muted"],
                  annotation_text=tr("x.avg"), annotation_position="bottom right")
    fig.update_yaxes(rangemode="tozero")
    c3.plotly_chart(layout(fig, 280, y_format=".0%", legend=False, title=tr("x.trend.rate")), width="stretch")

    d1, d2 = st.columns(2)
    # impact: active sellers at stake per action (tracking is a precondition, shown in contracts)
    opp = opportunities().dropna(subset=["active_sellers_at_stake"]).sort_values("active_sellers_at_stake")
    labels = [tr(f"opp.{a}.title", month=month) for a in opp["action_key"]]
    fig = go.Figure(go.Bar(x=opp["active_sellers_at_stake"], y=labels, orientation="h", marker_color=SERIES[0],
                           text=["+" + num(v) for v in opp["active_sellers_at_stake"]], textposition="outside",
                           customdata=[tr(f"team.{o}") for o in opp["owner"]],
                           hovertemplate="%{y}<br>+%{x:.0f} · %{customdata}<extra></extra>"))
    fig.update_xaxes(title=tr("x.impact.axis"))
    d1.plotly_chart(layout(fig, 300, legend=False, title=tr("x.impact.title")), width="stretch")
    fix = opportunities().set_index("action_key").loc["fix_tracking"]
    d1.caption("1. " + tr("opp.fix_tracking.title") + " – " +
               tr("opp.fix_tracking.impact", contracts=num(fix["contracts_at_stake"]), now=pct(fix["rate_now"])))

    # who sells: activation by business type with the likely range
    types = analysis_result("lead_types")
    if types is not None:
        s = types.assign(label=types["lead_group"].map(lambda g: tr(f"lead_type.{g}"))).sort_values("activation_rate")
        fig = go.Figure(go.Scatter(
            x=s["activation_rate"], y=s["label"], mode="markers",
            marker=dict(size=11, color=[COLORS["muted"] if v else SERIES[0] for v in s["is_small"]]),
            error_x=dict(type="data", symmetric=False, color=COLORS["muted"], thickness=2, width=0,
                         array=s["ci_high"] - s["activation_rate"], arrayminus=s["activation_rate"] - s["ci_low"]),
            hovertemplate="%{y}: %{x:.0%}<extra></extra>"))
        fig.add_vline(x=k.loc["seller_activation_rate_full_window", "value"], line_dash="dot",
                      line_color=COLORS["muted"], annotation_text=tr("x.avg"), annotation_position="top")
        d2.plotly_chart(layout(fig, 300, x_format=".0%", legend=False, title=tr("x.types.title")), width="stretch")

# ============================================================= FOR MARKETING
with tab_mkt:
    sc = channel_scorecard().copy()
    sc["label"] = sc["origin"].map(lambda o: tr(f"channel.{o}"))
    overall = sc["overall_active_per_1000"].iloc[0]
    tiles("tab.marketing",
          extra=lambda col: col.metric(tr("mkt.col.active"), num(overall), border=True,
                                       help=tr("exec.funnel.note")))

    m1, m2 = st.columns(2)
    # quadrant: does the channel close (x) and do its sellers sell (y)? bubble = volume
    q = sc.dropna(subset=["activation_rate"])
    fig = go.Figure()
    for verdict in VERDICTS:
        part = q[q["verdict"] == verdict]
        if len(part):
            fig.add_scatter(x=part["lead_to_win_rate"], y=part["activation_rate"], mode="markers+text",
                            name=tr(f"verdict.{verdict}"), text=part["label"], textposition="top center",
                            marker=dict(size=part["leads"], sizemode="area", sizeref=2 * q["leads"].max() / 55 ** 2,
                                        color=VERDICT_COLOR[verdict], line=dict(width=1, color="white")),
                            hovertemplate="%{text}<br>%{x:.1%} · %{y:.0%}<extra></extra>")
    fig.add_vline(x=k.loc["lead_to_win_rate_60d_tracked", "value"], line_dash="dot", line_color=COLORS["muted"])
    fig.add_hline(y=k.loc["seller_activation_rate_full_window", "value"], line_dash="dot", line_color=COLORS["muted"])
    fig.update_xaxes(title=tr("x.quad.x"))
    fig.update_yaxes(title=tr("x.quad.y"))
    m1.plotly_chart(layout(fig, 420, x_format=".0%", y_format=".0%", title=tr("x.quad.title")), width="stretch")

    # lead mix per month (stacked, fixed channel order and colors)
    mix = channel_monthly()
    fig = go.Figure()
    mix_colors = SERIES + ["#eda100", COLORS["muted"], COLORS["grid"]]
    for color, group in zip(mix_colors, MIX_ORDER):
        part = mix[mix["channel_group"] == group]
        fig.add_bar(x=[fmt_month(d, code) for d in part["cohort_month"]], y=part["leads"],
                    name=tr(f"channel.{group}"), marker_color=color,
                    hovertemplate=tr(f"channel.{group}") + ": %{y:,}<extra></extra>")
    fig.update_layout(barmode="stack", bargap=0.3)
    m2.plotly_chart(layout(fig, 420, title=tr("x.mix.title")), width="stretch")

    # scorecard table with in-cell bars
    st.markdown(f"**{tr('x.table.title')}**")
    table = pd.DataFrame({
        tr("mkt.col.channel"): sc["label"],
        tr("mkt.col.verdict"): [tr(f"verdict.{v}") for v in sc["verdict"]],
        tr("mkt.col.leads_month"): sc["leads_per_month"].round(0),
        tr("mkt.col.rate"): sc["lead_to_win_rate"] * 100,
        tr("mkt.col.active"): sc["activated_per_1000_leads"].round(0),
    })
    st.dataframe(table, hide_index=True, width="stretch", column_config={
        tr("mkt.col.rate"): st.column_config.ProgressColumn(format="%.1f %%", min_value=0, max_value=30),
        tr("mkt.col.active"): st.column_config.ProgressColumn(format="%.0f", min_value=0,
                                                              max_value=float(sc["activated_per_1000_leads"].max())),
        tr("mkt.col.leads_month"): st.column_config.NumberColumn(format="%.0f"),
    })
    st.caption(tr("mkt.rule", overall=num(overall)))

    # landing pages: actual vs expected for their channel mix
    pages = analysis_result("landing_pages")
    if pages is not None:
        p = pages.sort_values("rate")
        fig = go.Figure()
        fig.add_scatter(x=p["expected"], y=p["page"], mode="markers", name=tr("x.pages.expected"),
                        marker=dict(symbol="diamond-open", size=11, color=COLORS["ink_secondary"], line=dict(width=2)))
        fig.add_scatter(x=p["rate"], y=p["page"], mode="markers", name=tr("x.pages.actual"),
                        marker=dict(size=11, color=[SERIES[0] if d else COLORS["muted"] for d in p["p_fair_bh"] < 0.05]),
                        hovertemplate="%{y}: %{x:.1%}<extra></extra>")
        fig.update_yaxes(categoryorder="array", categoryarray=list(p["page"]), showgrid=False)
        st.plotly_chart(layout(fig, 460, x_format=".0%", title=tr("x.pages.title")), width="stretch")

# ========================================================= ASK THE DATA
with tab_ask:
    st.write(tr("assistant.intro"))
    state = assistant.status()
    if not state["running"]:
        st.info(tr("assistant.offline", model=state["model"]))
    elif not state["model_ready"]:
        st.warning(tr("assistant.no_model", model=state["model"]))
    else:
        facts = insights.facts(k, funnel.reset_index(), channels(), check, data_quality(),
                               analysis_result("lead_types"),
                               [{"n": f["n"], "title": tr(f"finding.{f['n']}.title"),
                                 "action": tr(f"finding.{f['n']}.action"), "teams": f["teams"]}
                                for f in insights.FINDINGS])
        facts["actions_ranked_by_impact"] = opportunities().drop(columns=["owner"]).round(3).to_dict(orient="records")
        facts["channel_scorecard"] = channel_scorecard()[["origin", "verdict", "leads_per_month",
                                                         "activated_per_1000_leads"]].round(1).to_dict(orient="records")
        history = st.session_state.setdefault("chat", [])
        question = None
        for i, column in enumerate(st.columns(3), start=1):
            if column.button(tr(f"assistant.example.{i}"), key=f"example_{i}"):
                question = tr(f"assistant.example.{i}")
        question = st.chat_input(tr("assistant.placeholder")) or question
        for turn in history:
            with st.chat_message(turn["role"]):
                st.markdown(turn["content"])
        if question:
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"), st.spinner(tr("assistant.thinking")):
                reply = assistant.ask(question, facts, code, history)
                if reply["ok"]:
                    st.caption(tr("assistant.label", model=state["model"]))
                    st.markdown(reply["answer"])
                    history += [{"role": "user", "content": question},
                                {"role": "assistant", "content": reply["answer"]}]
                else:
                    st.warning(tr("assistant.error", error=reply["error"]))

with st.expander(tr("glossary.title")):
    for term in GLOSSARY:
        st.markdown(tr(f"glossary.{term}"))
