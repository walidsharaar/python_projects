"""Step 5.2: experiments. How big and how long must an A/B test be,
and how do we read the result?

Part 1 uses REAL volumes from the warehouse.
Parts 2 and 3 use SIMULATED data with a known true effect. They show
that the method works; they say nothing about Olist's real results.
"""

from pathlib import Path

import duckdb
import numpy as np
from scipy.stats import norm

from stats_utils import evaluate_ab, minimum_detectable_rate, sample_size_per_group

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "warehouse.duckdb"
OUTPUT = ROOT / "reports" / "analysis" / "06_experiments.md"
RNG = np.random.default_rng(7)     # fixed seed: same simulation every run
N_SIM = 2_000
WAIT_FOR_OUTCOME_MONTHS = 2        # a lead needs up to 60 days before we know if it closed


# -------------------------------------------------- 1. real volumes
def real_volumes(con) -> dict:
    leads_per_month, win_rate = con.execute("""
        SELECT AVG(leads), SUM(won_60d) / SUM(leads)
        FROM mart_gtm_monthly WHERE deal_tracking_complete
    """).fetchone()
    page = con.execute("""
        SELECT COUNT(*) / COUNT(DISTINCT cohort_month), AVG(is_won_within_60d::INT)
        FROM fct_leads
        WHERE landing_page_id LIKE 'e492ee5e%'
          AND cohort_month >= DATE '2018-01-01'
    """).fetchone()
    return {"leads_per_month": leads_per_month, "win_rate": win_rate,
            "page_leads_per_month": page[0], "page_rate": page[1]}


def duration_months(n_per_group: int, leads_per_month: float) -> float:
    """Months to collect both groups, plus the wait until the outcome is known."""
    return 2 * n_per_group / leads_per_month + WAIT_FOR_OUTCOME_MONTHS


def sample_size_section(v: dict) -> list[str]:
    out = [f"  Real baseline (2018): {v['leads_per_month']:,.0f} MQLs per month, "
           f"60-day win rate {v['win_rate']:.1%}",
           "",
           "  A) Test on ALL leads (e.g. a new lead form for every channel), 50/50 split:",
           f"  {'from -> to':<16}{'uplift':>8}{'n per group':>13}{'months':>8}"]
    base = round(v["win_rate"], 3)
    for target in (base + 0.01, base + 0.02, base + 0.03, base + 0.05):
        n = sample_size_per_group(base, target)
        out.append(f"  {f'{base:.1%} -> {target:.1%}':<16}{f'+{target - base:.0%}':>8}"
                   f"{n:>13,}{duration_months(n, v['leads_per_month']):>8.1f}")
    out.append("  'months' = time to collect both groups + 2 months until the outcome is known")

    # H6 as written in the README: 12 % -> 14 %
    n_h6 = sample_size_per_group(0.12, 0.14)
    out += ["", f"  H6 check (README: 12 % -> 14 %): {n_h6:,} leads per group, "
                f"{duration_months(n_h6, v['leads_per_month']):.1f} months -> H6 confirmed"]

    # Finding #6: the weak landing page
    p, lpm = v["page_rate"], v["page_leads_per_month"]
    n_page = sample_size_per_group(p, 0.098)
    out += ["",
            f"  B) Test on page e492ee5e only ({lpm:.0f} leads per month, win rate {p:.1%}):",
            f"     Even a big jump to the channel expectation (9.8 %) needs {n_page:,} leads per group",
            f"     = {duration_months(n_page, lpm):.0f} months. Too slow to decide anything.",
            "     What a 6-month test on this page CAN detect:"]
    n_6m = int(lpm * 6 / 2)
    out.append(f"     {n_6m} leads per group -> only a jump from {p:.1%} to "
               f"{minimum_detectable_rate(p, n_6m):.1%} or more")
    # Same relative uplift (+20 %) measured on two metrics of the same page
    visits, form_rate, lift = 2_000, 0.03, 1.20
    n_form = sample_size_per_group(form_rate, form_rate * lift)
    months_form = 2 * n_form / visits                  # no waiting: a form is sent or not
    n_win = sample_size_per_group(p, p * lift)
    months_win = duration_months(n_win, lpm)
    out += ["",
            "  C) Faster metric, same page, same relative uplift of +20 %",
            f"     (ILLUSTRATIVE assumptions: {visits:,} visits per month, {form_rate:.0%} send the form;",
            "      this dataset has no web data)",
            f"     Lead-to-win  {p:.1%} -> {p * lift:.1%}: {n_win:>7,} leads per group  "
            f"= {months_win:>4.0f} months",
            f"     Form rate    {form_rate:.1%} -> {form_rate * lift:.1%}: {n_form:>7,} visits per group "
            f"= {months_form:>4.0f} months",
            f"     -> about {months_win / months_form:.0f}x faster, but still slow at this traffic.",
            "     Options: test bigger changes, test on high-traffic pages first,",
            "     or accept a lower certainty level for low-risk changes."]
    return out


# ---------------------------------------------- 2. simulated experiments
def z_test_p(won_a, n_a, won_b, n_b):
    """Vectorised two-proportion z-test (same idea as statsmodels, for 2,000 tests at once)."""
    pooled = (won_a + won_b) / (n_a + n_b)
    se = np.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))
    z = np.divide(won_b / n_b - won_a / n_a, se, out=np.zeros_like(se), where=se > 0)
    return 2 * norm.sf(np.abs(z))


def simulation_section() -> list[str]:
    p_a, p_b = 0.10, 0.12
    n = sample_size_per_group(p_a, p_b)

    # Real effect 10 % -> 12 %: how often does the test find it? (= power)
    real = z_test_p(RNG.binomial(n, p_a, N_SIM), n, RNG.binomial(n, p_b, N_SIM), n)
    # No effect at all (A/A test): how often do we get a false alarm? (= alpha)
    aa = z_test_p(RNG.binomial(n, p_a, N_SIM), n, RNG.binomial(n, p_a, N_SIM), n)
    # Too small: same real effect, but only a quarter of the sample
    small = z_test_p(RNG.binomial(n // 4, p_a, N_SIM), n // 4, RNG.binomial(n // 4, p_b, N_SIM), n // 4)

    # Peeking: A/A test, checked 20 times during the test, stop at the first p < 0.05
    looks = 20
    step = n // looks
    a = RNG.binomial(1, p_a, (N_SIM, looks * step)).reshape(N_SIM, looks, step).sum(axis=2).cumsum(axis=1)
    b = RNG.binomial(1, p_a, (N_SIM, looks * step)).reshape(N_SIM, looks, step).sum(axis=2).cumsum(axis=1)
    sizes = step * np.arange(1, looks + 1)
    p_each_look = z_test_p(a, sizes, b, sizes)
    peeking = (p_each_look < 0.05).any(axis=1)

    return [
        f"  SIMULATED: control 10 %, test 12 %, {n:,} leads per group, {N_SIM:,} experiments each",
        f"  {'situation':<58}{'significant':>12}{'should be':>11}",
        f"  {'Real effect, planned sample size (= power)':<58}{(real < 0.05).mean():>12.0%}{'~80 %':>11}",
        f"  {'No effect at all, A/A test (= false alarm rate)':<58}{(aa < 0.05).mean():>12.0%}{'~5 %':>11}",
        f"  {'Real effect, only 1/4 of the sample (underpowered)':<58}{(small < 0.05).mean():>12.0%}{'':>11}",
        f"  {'No effect, but checked 20 times and stopped at first p<0.05':<58}"
        f"{peeking.mean():>12.0%}{'~5 %':>11}",
        "",
        "  Lessons:",
        "  - With the planned sample size, a real effect is found about 4 times out of 5.",
        "  - Too small a test misses most real effects. 'Not significant' then means",
        "    'we don't know', not 'there is no effect'.",
        "  - Peeking at the result every few days and stopping when it looks good",
        f"    turns a 5 % false alarm rate into about {peeking.mean():.0%}. Decide the sample size first.",
    ]


# -------------------------------------------- 3. reading one finished test
def evaluation_section() -> list[str]:
    n = sample_size_per_group(0.10, 0.12)
    won_a = RNG.binomial(n, 0.10)
    won_b = RNG.binomial(n, 0.12)
    r = evaluate_ab(won_a, n, won_b, n)
    lift = r["diff"] / r["rate_a"]
    decision = ("ship B" if r["ci_low"] > 0 else
                "keep A" if r["ci_high"] < 0 else "no decision: the interval includes 0")
    return [
        "  SIMULATED example of one finished test (true effect: 10 % -> 12 %)",
        f"  A (control): {won_a:,} of {n:,} = {r['rate_a']:.1%}",
        f"  B (test):    {won_b:,} of {n:,} = {r['rate_b']:.1%}",
        f"  Difference B - A: {r['diff']:+.1%} points (relative {lift:+.0%}), "
        f"95% CI {r['ci_low']:+.1%} to {r['ci_high']:+.1%}, p = {r['p_value']:.4f}",
        f"  Decision rule (set BEFORE the test): ship B only if the whole interval is above 0 "
        f"-> {decision}",
        "  Before shipping, also check the guardrails: did activation or cancellations get worse",
        "  in group B? A higher win rate with worse sellers is not a success.",
    ]


def main() -> None:
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        v = real_volumes(con)
    sections = {
        "1. How many leads and how long? (real volumes)": sample_size_section(v),
        "2. Simulated experiments: power, false alarms, peeking": simulation_section(),
        "3. How to read one finished test": evaluation_section(),
    }
    for title, lines in sections.items():
        print(f"\n{title}")
        print("\n".join(lines))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    md = ["# Evidence: experiment design (Step 5.2)", "",
          "Generated by `analysis/06_experiments.py`. Part 1 uses real volumes. "
          "Parts 2 and 3 use **simulated** data with a known true effect.", ""]
    for title, lines in sections.items():
        md += [f"## {title}", "", "```text", *lines, "```", ""]
    OUTPUT.write_text("\n".join(md), encoding="utf-8")
    print(f"\nSaved: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
