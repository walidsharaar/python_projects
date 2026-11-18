"""The GTM screen: one headline, then three tabs.

    For executives   4 KPIs, the funnel, and the actions ranked by what is at stake
    For marketing    channel scorecard with a verdict per channel, landing page actions
    Ask the data     a free local AI model (Ollama) answers from the same numbers

Rules: every number comes from sql/marts (mart_opportunities, mart_channel_scorecard,
mart_executive_funnel, mart_kpi_summary ...); texts are in src/i18n/translations.json.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import (analysis_result, channel_scorecard, channels, data_quality, executive_funnel,
                  gtm_monthly, kpis, opportunities)
from ui import COLORS, SERIES, kpi_tile, lang, tr
from src import assistant, insights
from src.i18n import fmt_month, fmt_num, fmt_p, fmt_pct

# KPI tiles (read by tests/test_translations.py)
TILES = [
    ("exec.title", ["lead_to_win_rate_60d_tracked", "seller_activation_rate_full_window",
                    "time_to_first_sale_median_days", "unattributed_win_share"]),
]
VERDICT_COLOR = {"grow": COLORS["series_1"], "watch": SERIES[2], "review": SERIES[1],
                 "fix_tracking": COLORS["muted"], "too_little": COLORS["muted"]}
GLOSSARY = ["lead", "contract", "activation", "gmv", "median", "range", "p", "channel", "cohort", "ab"]

code = lang()
SEPARATORS = ",." if code == "de" else ".,"
k, funnel, monthly = kpis(), executive_funnel(), gtm_monthly()
check = insights.latest_month_check(monthly)
month = fmt_month(check["month"], code)


def layout(fig: go.Figure, height: int, x_format: str | None = None, legend: bool = True) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), showlegend=legend,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", separators=SEPARATORS,
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0), barcornerradius=4)
    fig.update_xaxes(tickformat=x_format, gridcolor=COLORS["grid"], zeroline=False)
    fig.update_yaxes(showgrid=False)
    return fig


def num(v) -> str:
    return "–" if pd.isna(v) else fmt_num(v, code)


def pct(v, digits: int = 1) -> str:
    return "–" if pd.isna(v) else fmt_pct(v, code, digits)


# ------------------------------------------------------------- headline
st.title(tr("exec.title"))
st.markdown("#### " + tr("exec.headline", won=num(funnel.loc["won", "per_1000_leads"]),
                         active=num(funnel.loc["activated", "per_1000_leads"]),
                         not_active=pct(1 - funnel.loc["activated", "rate_from_previous"], 0)))
tab_exec, tab_mkt, tab_ask = st.tabs([tr("tab.exec"), tr("tab.marketing"), tr("tab.ask")])

# ======================================================== FOR EXECUTIVES
with tab_exec:
    for _, keys in TILES:
        for column, key in zip(st.columns(len(keys)), keys):
            if key == "lead_to_win_rate_60d_tracked":
                diff = check["rate"] - check["rate_earlier"]
                kpi_tile(column, k, key,
                         delta=("-" if diff < 0 else "+") + tr("exec.points", value=fmt_num(abs(diff) * 100, code, 1)),
                         delta_note=tr("exec.delta.latest", month=month))
            else:
                kpi_tile(column, k, key)

    left, right = st.columns([2, 3])
    with left:
        st.subheader(tr("exec.funnel.title"))
        stages = [("leads", "exec.funnel.leads"), ("won", "exec.funnel.won"), ("activated", "exec.funnel.activated")]
        values = [funnel.loc[s, "per_1000_leads"] for s, _ in stages]
        fig = go.Figure(go.Funnel(y=[tr(lbl) for _, lbl in stages], x=values, marker=dict(color=COLORS["series_1"]),
                                  text=[num(v) for v in values], textinfo="text", hoverinfo="skip",
                                  connector=dict(line=dict(color=COLORS["grid"]))))
        st.plotly_chart(layout(fig, 240, legend=False), width="stretch")
        st.caption(tr("exec.funnel.gmv", gmv=tr("unit.brl", value=num(funnel.loc["gmv_90d_brl", "per_1000_leads"]))))

    with right:
        st.subheader(tr("exec.actions.title"))
        for row in opportunities().itertuples():
            values = dict(contracts=num(row.contracts_at_stake), sellers=num(row.active_sellers_at_stake),
                          base=num(row.base), now=pct(row.rate_now), benchmark=pct(row.rate_benchmark), month=month)
            with st.container(border=True):
                badge = f" · _{tr('exec.actions.first')}_" if row.priority == 1 else ""
                st.markdown(f"**{num(row.priority)}. {tr(f'opp.{row.action_key}.title', **values)}**{badge}")
                st.markdown(tr(f"opp.{row.action_key}.impact", **values))
                if row.action_key == "check_latest_month":
                    action, measure = tr("exec.chg.do"), tr("exec.chg.measure")
                else:
                    action, measure = tr(f"finding.{row.finding}.action"), tr(f"finding.{row.finding}.measure")
                st.caption(f"→ {action}  \n{tr('exec.card.measure')}: {measure} · "
                           f"{tr('exec.card.owner')}: {tr(f'team.{row.owner}')}")
        st.caption(tr("exec.actions.note"))

# ========================================================= FOR MARKETING
with tab_mkt:
    sc = channel_scorecard().copy()
    sc["label"] = sc["origin"].map(lambda o: tr(f"channel.{o}"))
    overall = sc["overall_active_per_1000"].iloc[0]

    st.subheader(tr("mkt.score.title"))
    st.dataframe(pd.DataFrame({
        tr("mkt.col.channel"): sc["label"],
        tr("mkt.col.verdict"): [tr(f"verdict.{v}") for v in sc["verdict"]],
        tr("mkt.col.leads_month"): [num(v) for v in sc["leads_per_month"]],
        tr("mkt.col.rate"): [pct(v) for v in sc["lead_to_win_rate"]],
        tr("mkt.col.range"): [f"{pct(lo)} – {pct(hi)}" for lo, hi in zip(sc["lead_to_win_ci_low"], sc["lead_to_win_ci_high"])],
        tr("mkt.col.active"): [num(v) for v in sc["activated_per_1000_leads"]],
    }), hide_index=True, width="stretch")
    st.caption(tr("mkt.rule", overall=num(overall)))

    chart_col, side_col = st.columns([3, 2])
    with chart_col:
        st.markdown(f"**{tr('mkt.chart.title')}**")
        c = sc.dropna(subset=["activated_per_1000_leads"]).sort_values("activated_per_1000_leads")
        fig = go.Figure()
        for verdict in ["grow", "watch", "review", "fix_tracking", "too_little"]:   # fixed order, fixed colors
            part = c[c["verdict"] == verdict]
            if len(part):
                fig.add_bar(x=part["activated_per_1000_leads"], y=part["label"], orientation="h",
                            name=tr(f"verdict.{verdict}"), marker_color=VERDICT_COLOR[verdict],
                            hovertemplate="%{customdata}<extra></extra>",
                            customdata=[tr("exec.ch.hover", channel=lbl, value=num(v), rate=pct(r))
                                        for lbl, v, r in zip(part["label"], part["activated_per_1000_leads"],
                                                             part["lead_to_win_rate"])])
        fig.add_vline(x=overall, line_dash="dot", line_color=COLORS["ink_secondary"],
                      annotation_text=tr("mkt.chart.overall", value=num(overall)), annotation_position="top")
        fig.update_yaxes(categoryorder="array", categoryarray=list(c["label"]))
        st.plotly_chart(layout(fig, 400), width="stretch")

    with side_col:
        st.markdown(f"**{tr('mkt.pages.title')}**")
        pages = analysis_result("landing_pages")
        if pages is None:
            st.info(tr("common.run_analysis", script="analysis\\03_landing_pages.py"))
        else:
            differs = pages[pages["p_fair_bh"] < 0.05]
            top = pages.sort_values("untracked_leads", ascending=False).iloc[0]
            lines = [tr("mkt.pages.fix", page=top["page"],
                        share=pct(top["untracked_leads"] / k.loc["unattributed_lead_share", "numerator"], 0))]
            above = differs[differs["rate"] > differs["expected"]]
            below = differs[differs["rate"] < differs["expected"]]
            if len(above):
                best = above.assign(gap=above["rate"] - above["expected"]).sort_values("gap").iloc[-1]
                lines.append(tr("mkt.pages.learn", page=best["page"], rate=pct(best["rate"]), expected=pct(best["expected"])))
            if len(below):
                weak = below.assign(gap=below["rate"] - below["expected"]).sort_values("gap").iloc[0]
                lines.append(tr("mkt.pages.weak", page=weak["page"], rate=pct(weak["rate"]), expected=pct(weak["expected"])))
            for line in lines:
                st.markdown(f"- {line}")

        st.markdown(f"**{tr('mkt.month.title')}**")
        key = "exec.chg.happened_alert" if check["clear_change"] else "exec.chg.happened_normal"
        (st.warning if check["clear_change"] else st.info)(
            tr(key, month=month, rate=pct(check["rate"]), earlier=pct(check["rate_earlier"]),
               p=fmt_p(check["p_value"], code)) + " " + tr("exec.chg.do"))

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
