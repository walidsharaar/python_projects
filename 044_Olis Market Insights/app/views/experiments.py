"""Page 4: Experiments. Plan an A/B test and read a finished one.

Uses the same functions as analysis/06_experiments.py (analysis/stats_utils.py),
so the calculator and the analysis can never disagree. Defaults come from the
KPI layer (current win rate, leads per month).
"""

import sys

import streamlit as st

from data import kpis
from ui import ROOT, lang, tr
from src.i18n import fmt_num, fmt_pct

sys.path.insert(0, str(ROOT / "analysis"))
from stats_utils import evaluate_ab, sample_size_per_group  # noqa: E402

code = lang()
k = kpis()

st.title(tr("exp.title"))
st.write(tr("exp.intro"))

# ------------------------------------------------------- 1. plan a test
st.subheader(tr("exp.plan.title"))
baseline_default = round(k.loc["lead_to_win_rate_60d_tracked", "value"] * 100, 1)
volume_default = int(round(k.loc["mql_per_month_tracked", "value"]))

c1, c2, c3 = st.columns(3)
baseline = c1.number_input(tr("exp.plan.baseline"), 0.1, 99.0, baseline_default, 0.1, key="exp_baseline")
target = c2.number_input(tr("exp.plan.target"), 0.1, 99.0, round(baseline_default + 2, 1), 0.1, key="exp_target")
volume = c3.number_input(tr("exp.plan.volume"), 10, 100_000, volume_default, 10, key="exp_volume")
c4, c5, c6 = st.columns(3)
alpha = c4.selectbox(tr("exp.plan.alpha"), [0.05, 0.10, 0.01], key="exp_alpha",
                     format_func=lambda a: fmt_pct(a, code, 0))
power = c5.selectbox(tr("exp.plan.power"), [0.80, 0.90], key="exp_power",
                     format_func=lambda p: fmt_pct(p, code, 0))
wait = c6.number_input(tr("exp.plan.wait"), 0, 12, 2, 1, help=tr("exp.plan.wait_help"), key="exp_wait")

if abs(target - baseline) < 1e-9:
    st.warning(tr("exp.plan.invalid"))
else:
    n = sample_size_per_group(baseline / 100, target / 100, alpha=alpha, power=power)
    months = 2 * n / volume + wait
    m1, m2, m3 = st.columns(3)
    m1.metric(tr("exp.plan.n"), fmt_num(n, code), border=True)
    m2.metric(tr("exp.plan.total"), fmt_num(2 * n, code), border=True)
    m3.metric(tr("exp.plan.months"), tr("exp.plan.months_value", value=fmt_num(months, code, 1)), border=True)
    (st.warning if months > 12 else st.success)(tr("exp.plan.slow") if months > 12 else tr("exp.plan.ok"))

# ---------------------------------------------- 2. read a finished test
st.subheader(tr("exp.read.title"))
st.write(tr("exp.read.intro"))
r1, r2, r3, r4 = st.columns(4)
won_a = r1.number_input(tr("exp.read.won_a"), 0, 1_000_000, 394, key="exp_won_a")
n_a = r2.number_input(tr("exp.read.n_a"), 1, 1_000_000, 3_835, key="exp_n_a")
won_b = r3.number_input(tr("exp.read.won_b"), 0, 1_000_000, 470, key="exp_won_b")
n_b = r4.number_input(tr("exp.read.n_b"), 1, 1_000_000, 3_835, key="exp_n_b")

if won_a > n_a or won_b > n_b:
    st.warning(tr("exp.read.invalid"))
else:
    res = evaluate_ab(int(won_a), int(n_a), int(won_b), int(n_b))
    points = lambda v: fmt_num(v * 100, code, 1)                     # 0.02 -> "2.0" points
    e1, e2 = st.columns(2)
    e1.metric(tr("exp.read.diff"), tr("exp.points", value=points(res["diff"])), border=True)
    e1.caption(tr("exp.read.ci", low=points(res["ci_low"]), high=points(res["ci_high"])))
    e2.metric(tr("exp.read.p"), fmt_num(res["p_value"], code, 4), border=True)
    if res["ci_low"] > 0:
        st.success(tr("exp.read.ship"))
    elif res["ci_high"] < 0:
        st.error(tr("exp.read.keep"))
    else:
        st.info(tr("exp.read.unclear"))

st.divider()
st.subheader(tr("exp.lessons.title"))
st.write(tr("exp.lessons.text"))
