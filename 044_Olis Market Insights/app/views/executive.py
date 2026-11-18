"""The executive screen: one data story from the problem to the action.

    1. Headline      one sentence, every number from the data
    2. 5 KPI tiles   value, how it is calculated, change of the latest month
    3. Funnel        what happens to 1,000 new leads
    4. 4 questions   each: one chart, details for one item, and a story card
                     (What happened -> Why -> What to do -> How we will know -> Who acts)
    5. Ask the data  a local AI model answers from the same numbers
    6. Glossary      every technical word in one plain sentence

Rules: nothing is calculated here that the KPI layer should calculate; the
texts are in src/i18n/translations.json; numbers enter texts as placeholders.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import analysis_result, channels, data_dates, data_quality, executive_funnel, gtm_monthly, kpis
from ui import COLORS, SERIES, kpi_tile, lang, tr
from src import assistant, insights
from src.i18n import fmt_date, fmt_month, fmt_num, fmt_p, fmt_pct

# KPI tiles on this screen (read by tests/test_translations.py)
TILES = [
    ("exec.title", ["mql_per_month_tracked", "lead_to_win_rate_60d_tracked",
                    "seller_activation_rate_full_window", "time_to_first_sale_median_days",
                    "unattributed_win_share"]),
]
# Which finding answers which question (README section 9)
QUESTION_FINDING = {"channels": 3, "segments": 4, "trust": 1}
TRUST_CHECKS = ["leads_before_tracking", "sellers_without_full_window"]   # the untracked share is in the card
GLOSSARY = ["lead", "contract", "activation", "gmv", "median", "range", "p", "channel", "cohort", "ab"]

code = lang()
SEPARATORS = ",." if code == "de" else ".,"
k, funnel, ch, monthly = kpis(), executive_funnel(), channels(), gtm_monthly()
check = insights.latest_month_check(monthly)
types = analysis_result("lead_types")
pages = analysis_result("landing_pages")
dates = data_dates()


def layout(fig: go.Figure, height: int, x_format: str | None = None, y_format: str | None = None,
           legend: bool = True) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), showlegend=legend,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", separators=SEPARATORS,
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0), barcornerradius=4)
    fig.update_xaxes(tickformat=x_format, gridcolor=COLORS["grid"], zeroline=False)
    fig.update_yaxes(tickformat=y_format, gridcolor=COLORS["grid"], zeroline=False)
    return fig


def story_card(column, happened: str, why: str, do: str, measure: str, teams: list[str]) -> None:
    with column.container(border=True):
        for title, text in [("exec.card.happened", happened), ("exec.card.why", why),
                            ("exec.card.do", do), ("exec.card.measure", measure)]:
            st.markdown(f"**{tr(title)}**  \n{text}")
        st.caption(f"{tr('exec.card.owner')}: " + ", ".join(tr(f"team.{t}") for t in teams))


def finding_card(column, n: int, happened: str, why: str) -> None:
    meta = next(f for f in insights.FINDINGS if f["n"] == n)
    story_card(column, happened, why, tr(f"finding.{n}.action"), tr(f"finding.{n}.measure"), meta["teams"])


def points(diff: float) -> str:
    return ("-" if diff < 0 else "+") + tr("exec.points", value=fmt_num(abs(diff) * 100, code, 1))


# ------------------------------------------------------------ 1. headline
st.title(tr("exec.title"))
won, active = funnel.loc["won", "per_1000_leads"], funnel.loc["activated", "per_1000_leads"]
st.markdown("#### " + tr("exec.headline", won=fmt_num(won, code), active=fmt_num(active, code),
                         not_active=fmt_pct(1 - funnel.loc["activated", "rate_from_previous"], code, 0)))

# ------------------------------------------------------------- 2. KPI tiles
for _, keys in TILES:
    for column, key in zip(st.columns(len(keys)), keys):
        if key == "lead_to_win_rate_60d_tracked":         # the only KPI with a monthly trend
            kpi_tile(column, k, key, delta=points(check["rate"] - check["rate_earlier"]),
                     delta_note=tr("exec.delta.latest", month=fmt_month(check["month"], code)))
        else:
            kpi_tile(column, k, key)

# ---------------------------------------------------------------- 3. funnel
st.subheader(tr("exec.funnel.title"))
left, right = st.columns([3, 2])
stages = [("leads", "exec.funnel.leads"), ("won", "exec.funnel.won"), ("activated", "exec.funnel.activated")]
labels = [tr(label) for _, label in stages]
values = [funnel.loc[stage, "per_1000_leads"] for stage, _ in stages]
fig = go.Figure(go.Funnel(
    y=labels, x=values, marker=dict(color=COLORS["series_1"]),
    text=[fmt_num(v, code) for v in values], textinfo="text", textposition="inside",
    customdata=[tr("exec.funnel.hover", stage=lbl, value=fmt_num(v, code)) for lbl, v in zip(labels, values)],
    hovertemplate="%{customdata}<extra></extra>", connector=dict(line=dict(color=COLORS["grid"])),
))
left.plotly_chart(layout(fig, 260, legend=False), width="stretch")
right.markdown(tr("exec.funnel.gmv", gmv=tr("unit.brl", value=fmt_num(funnel.loc["gmv_90d_brl", "per_1000_leads"], code))))
right.caption(tr("exec.funnel.note"))

# ------------------------------------------------------------ 4. questions
st.subheader(tr("exec.questions.title"))
tab_channels, tab_segments, tab_change, tab_trust = st.tabs(
    [tr("exec.q.channels"), tr("exec.q.segments"), tr("exec.q.change"), tr("exec.q.trust")])

# 4.1 channels ------------------------------------------------------------
with tab_channels:
    chart, card = st.columns([3, 2])
    c = ch.dropna(subset=["activated_per_1000_leads"]).copy()
    c["label"] = c["origin"].map(lambda o: tr(f"channel.{o}"))
    c = c.sort_values("activated_per_1000_leads")
    fig = go.Figure()
    comparable = ~c["is_small_seller_sample"] & c["is_attributed"]
    for ok, name, color in [(True, tr("exec.ch.enough"), COLORS["series_1"]),
                            (False, tr("exec.ch.small"), COLORS["muted"])]:
        part = c[comparable == ok]
        fig.add_bar(x=part["activated_per_1000_leads"], y=part["label"], orientation="h", name=name,
                    marker_color=color, hovertemplate="%{customdata}<extra></extra>",
                    customdata=[tr("exec.ch.hover", channel=lbl, value=fmt_num(v, code), rate=fmt_pct(r, code))
                                for lbl, v, r in zip(part["label"], part["activated_per_1000_leads"],
                                                     part["lead_to_win_rate"])])
    fig.update_yaxes(categoryorder="array", categoryarray=list(c["label"]), showgrid=False)
    chart.markdown(f"**{tr('exec.ch.chart')}**")
    chart.plotly_chart(layout(fig, 380), width="stretch")

    pick = chart.selectbox(tr("exec.detail.pick"), list(c.sort_values("leads", ascending=False)["origin"]),
                           format_func=lambda o: tr(f"channel.{o}"), key="exec_channel")
    r = ch.set_index("origin").loc[pick]
    chart.info(tr("exec.detail.channel", channel=tr(f"channel.{pick}"), leads=fmt_num(r["leads"], code),
                  won=fmt_num(r["won"], code), rate=fmt_pct(r["lead_to_win_rate"], code),
                  low=fmt_pct(r["lead_to_win_ci_low"], code), high=fmt_pct(r["lead_to_win_ci_high"], code),
                  sellers=fmt_num(r["won_sellers_full_window"], code),
                  activation="–" if pd.isna(r["activation_rate"]) else fmt_pct(r["activation_rate"], code, 0)))

    # Compare only real channels with enough sellers. "unknown" / "not_tracked" are the
    # tracking gap (question 4), not a channel anyone can invest in.
    big = c[~c["is_small_seller_sample"] & c["is_attributed"]]
    best, worst = big.iloc[-1], big.iloc[0]
    finding_card(card, QUESTION_FINDING["channels"],
                 tr("exec.ch.happened", best=best["label"], best_value=fmt_num(best["activated_per_1000_leads"], code),
                    worst=worst["label"], worst_value=fmt_num(worst["activated_per_1000_leads"], code)),
                 tr("exec.ch.why"))

# 4.2 segments ------------------------------------------------------------
with tab_segments:
    chart, card = st.columns([3, 2])
    if types is None:
        chart.info(tr("common.run_analysis", script="analysis\\02_win_vs_activation.py"))
    else:
        s = types.copy()
        s["label"] = s["lead_group"].map(lambda g: tr(f"lead_type.{g}"))
        s = s.sort_values("activation_rate")
        fig = go.Figure()
        for small, name, color, symbol in [(False, tr("exec.ch.enough"), COLORS["series_1"], "circle"),
                                           (True, tr("exec.ch.small"), COLORS["muted"], "circle-open")]:
            part = s[s["is_small"] == small]
            fig.add_scatter(x=part["activation_rate"], y=part["label"], mode="markers", name=name,
                            marker=dict(color=color, size=11, symbol=symbol, line=dict(width=2, color=color)),
                            error_x=dict(type="data", symmetric=False, color=color, thickness=2, width=0,
                                         array=part["ci_high"] - part["activation_rate"],
                                         arrayminus=part["activation_rate"] - part["ci_low"]),
                            hovertemplate="%{customdata}<extra></extra>",
                            customdata=[tr("exec.seg.hover", type=lbl, rate=fmt_pct(v, code),
                                           low=fmt_pct(lo, code), high=fmt_pct(hi, code))
                                        for lbl, v, lo, hi in zip(part["label"], part["activation_rate"],
                                                                  part["ci_low"], part["ci_high"])])
        fig.update_yaxes(categoryorder="array", categoryarray=list(s["label"]), showgrid=False)
        fig.update_xaxes(rangemode="tozero")
        chart.markdown(f"**{tr('exec.seg.chart')}**")
        chart.plotly_chart(layout(fig, 340, x_format=".0%"), width="stretch")

        pick = chart.selectbox(tr("exec.detail.pick"), list(s.sort_values("sellers", ascending=False)["lead_group"]),
                               format_func=lambda g: tr(f"lead_type.{g}"), key="exec_type")
        r = s.set_index("lead_group").loc[pick]
        chart.info(tr("exec.detail.type", type=r["label"], sellers=fmt_num(r["sellers"], code),
                      rate=fmt_pct(r["activation_rate"], code), low=fmt_pct(r["ci_low"], code),
                      high=fmt_pct(r["ci_high"], code), seller_share=fmt_pct(r["seller_share"], code, 0),
                      gmv_share=fmt_pct(r["gmv_share"], code, 0)))

        big = s[~s["is_small"]]
        best, worst = big.iloc[-1], big.iloc[0]
        finding_card(card, QUESTION_FINDING["segments"],
                     tr("exec.seg.happened", best=best["label"], best_rate=fmt_pct(best["activation_rate"], code, 0),
                        worst=worst["label"], worst_rate=fmt_pct(worst["activation_rate"], code, 0)),
                     tr("exec.seg.why"))

# 4.3 is something changing? ----------------------------------------------
with tab_change:
    chart, card = st.columns([3, 2])
    m = monthly[monthly["deal_tracking_complete"]].copy()
    m["label"] = [fmt_month(d, code) for d in m["cohort_month"]]
    m["latest"] = m["cohort_month"] == check["month"]
    fig = go.Figure()
    latest_color = SERIES[1] if check["clear_change"] else COLORS["series_1"]
    for is_latest, name, color in [(False, tr("exec.chg.normal"), COLORS["series_1"]),
                                   (True, tr("exec.chg.latest"), latest_color)]:
        part = m[m["latest"] == is_latest]
        fig.add_bar(x=part["label"], y=part["lead_to_win_rate_60d"], name=name, marker_color=color,
                    hovertemplate="%{customdata}<extra></extra>",
                    customdata=[tr("exec.chg.hover", month=lbl, rate=fmt_pct(v, code), won=fmt_num(w, code),
                                   leads=fmt_num(n, code))
                                for lbl, v, w, n in zip(part["label"], part["lead_to_win_rate_60d"],
                                                        part["won_60d"], part["leads"])])
    fig.add_hline(y=check["rate_earlier"], line_dash="dot", line_color=COLORS["muted"])
    fig.update_xaxes(categoryorder="array", categoryarray=list(m["label"]), showgrid=False)
    fig.update_layout(bargap=0.35)
    chart.markdown(f"**{tr('exec.chg.chart')}**")
    chart.plotly_chart(layout(fig, 320, y_format=".0%"), width="stretch")
    chart.caption(tr("exec.chg.note", start=fmt_date(dates["tracking_start"], code)))

    pick = chart.selectbox(tr("exec.detail.pick"), list(m["cohort_month"])[::-1],
                           format_func=lambda d: fmt_month(d, code), key="exec_month")
    r = m.set_index("cohort_month").loc[pick]
    chart.info(tr("exec.detail.month", month=fmt_month(pick, code), leads=fmt_num(r["leads"], code),
                  won=fmt_num(r["won_60d"], code), rate=fmt_pct(r["lead_to_win_rate_60d"], code)))

    happened_key = "exec.chg.happened_alert" if check["clear_change"] else "exec.chg.happened_normal"
    story_card(card,
               tr(happened_key, month=fmt_month(check["month"], code), rate=fmt_pct(check["rate"], code),
                  earlier=fmt_pct(check["rate_earlier"], code),
                  p=fmt_p(check["p_value"], code)),
               tr("exec.chg.why"), tr("exec.chg.do"), tr("exec.chg.measure"), ["data", "marketing"])

# 4.4 can we trust the numbers? -------------------------------------------
with tab_trust:
    chart, card = st.columns([3, 2])
    lead_share, win_share = k.loc["unattributed_lead_share", "value"], k.loc["unattributed_win_share", "value"]
    bars = [(tr("exec.tr.leads"), lead_share), (tr("exec.tr.wins"), win_share)]
    fig = go.Figure(go.Bar(x=[v for _, v in bars], y=[lbl for lbl, _ in bars], orientation="h",
                           marker_color=COLORS["series_1"], text=[fmt_pct(v, code) for _, v in bars],
                           textposition="outside", hoverinfo="skip"))
    fig.update_xaxes(rangemode="tozero")
    chart.markdown(f"**{tr('exec.tr.chart')}**")
    chart.plotly_chart(layout(fig, 200, x_format=".0%", legend=False), width="stretch")

    # Only the gaps that affect the numbers on this screen (the full list is in the report)
    dq = data_quality().set_index("check_key").loc[TRUST_CHECKS].reset_index()
    dq = dq.assign(share=dq["records"] / dq["total_records"])
    for row in dq.itertuples():
        chart.markdown(f"- {tr(f'dq.check.{row.check_key}')}: {fmt_pct(row.share, code)} "
                       f"→ {tr(f'dq.affects.{row.affects}')}")
    chart.caption(tr("exec.tr.limits", end=fmt_date(dates["data_end"], code)))

    if pages is not None and pages["untracked_leads"].sum() > 0:
        top = pages.sort_values("untracked_leads", ascending=False).iloc[0]
        top_share = top["untracked_leads"] / k.loc["unattributed_lead_share", "numerator"]
        happened = tr("exec.tr.happened", lead_share=fmt_pct(lead_share, code), win_share=fmt_pct(win_share, code),
                      top_page_share=fmt_pct(top_share, code, 0), page=top["page"])
    else:
        happened = tr("common.run_analysis", script="analysis\\03_landing_pages.py")
    finding_card(card, QUESTION_FINDING["trust"], happened, tr("exec.tr.why"))

# ----------------------------------------------------------- 5. ask the data
st.divider()
st.subheader(tr("assistant.title"))
st.write(tr("assistant.intro"))

facts = insights.facts(k, funnel.reset_index(), ch, check, data_quality(), types,
                       [{"n": f["n"], "title": tr(f"finding.{f['n']}.title"),
                         "action": tr(f"finding.{f['n']}.action"), "teams": f["teams"],
                         "confidence": f["confidence"]} for f in insights.FINDINGS])
state = assistant.status()
if not state["running"]:
    st.info(tr("assistant.offline", model=state["model"]))
elif not state["model_ready"]:
    st.warning(tr("assistant.no_model", model=state["model"]))
else:
    history = st.session_state.setdefault("chat", [])
    examples = st.columns(3)
    question = None
    for i, column in enumerate(examples, start=1):
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
                history += [{"role": "user", "content": question}, {"role": "assistant", "content": reply["answer"]}]
            else:
                st.warning(tr("assistant.error", error=reply["error"]))

# ---------------------------------------------------------------- 6. glossary
with st.expander(tr("glossary.title")):
    for term in GLOSSARY:
        st.markdown(tr(f"glossary.{term}"))
