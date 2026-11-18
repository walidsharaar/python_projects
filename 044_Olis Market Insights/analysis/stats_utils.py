"""Shared statistics helpers for the analysis scripts.

Keeping them in one place means every analysis computes intervals the
same way (same rule as one KPI definition in the KPI layer).
"""

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from statsmodels.stats.proportion import proportion_confint

RNG = np.random.default_rng(42)   # fixed seed: same bootstrap result every run


def wilson(successes: int, n: int) -> tuple[float, float]:
    """95 % Wilson interval for a rate, e.g. 30 activated out of 50."""
    low, high = proportion_confint(successes, n, alpha=0.05, method="wilson")
    return float(low), float(high)


def bootstrap_mean_ci(values: np.ndarray, n_boot: int = 5_000) -> tuple[float, float]:
    """95 % interval for a mean, without assuming a normal distribution."""
    samples = RNG.choice(values, size=(n_boot, len(values)), replace=True)
    means = samples.mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def rate_table(df: pd.DataFrame, group: str, outcome: str, min_n: int = 30) -> pd.DataFrame:
    """Rate of a yes/no outcome per group, with n and Wilson interval."""
    g = df.groupby(group, dropna=False)[outcome].agg(n="size", yes="sum").reset_index()
    g["rate"] = g["yes"] / g["n"]
    g[["ci_low", "ci_high"]] = [wilson(y, n) for y, n in zip(g["yes"], g["n"])]
    g["small"] = g["n"] < min_n
    return g.sort_values("rate", ascending=False)


def chi_square(df: pd.DataFrame, group: str, outcome: str) -> tuple[float, int, float]:
    """Is the outcome independent of the group? Returns chi2, df, p."""
    chi2, p, dof, _ = chi2_contingency(pd.crosstab(df[group], df[outcome]))
    return float(chi2), int(dof), float(p)


# ------------------------------------------------------------ experiments
# Used by analysis/06_experiments.py and later by the dashboard's
# sample size calculator, so both always give the same answer.

def sample_size_per_group(p_control: float, p_test: float,
                          alpha: float = 0.05, power: float = 0.80) -> int:
    """Leads needed IN EACH GROUP to detect p_control -> p_test (two-sided)."""
    from math import ceil
    from statsmodels.stats.power import NormalIndPower
    from statsmodels.stats.proportion import proportion_effectsize

    effect = proportion_effectsize(p_test, p_control)      # Cohen's h
    n = NormalIndPower().solve_power(effect_size=effect, alpha=alpha, power=power,
                                     ratio=1.0, alternative="two-sided")
    return ceil(n)


def minimum_detectable_rate(p_control: float, n_per_group: int,
                            alpha: float = 0.05, power: float = 0.80) -> float:
    """Smallest test rate (above p_control) a test with n_per_group can reliably detect."""
    from math import asin, sin, sqrt
    from statsmodels.stats.power import NormalIndPower

    h = NormalIndPower().solve_power(nobs1=n_per_group, alpha=alpha, power=power,
                                     ratio=1.0, alternative="two-sided")
    return sin(asin(sqrt(p_control)) + h / 2) ** 2           # invert Cohen's h


def evaluate_ab(won_a: int, n_a: int, won_b: int, n_b: int) -> dict:
    """Evaluate a finished A/B test: difference B - A, its 95 % interval, p-value."""
    from statsmodels.stats.proportion import (confint_proportions_2indep,
                                              test_proportions_2indep)

    low, high = confint_proportions_2indep(won_b, n_b, won_a, n_a,
                                           compare="diff", method="newcomb")
    p = test_proportions_2indep(won_b, n_b, won_a, n_a).pvalue
    return {"rate_a": won_a / n_a, "rate_b": won_b / n_b,
            "diff": won_b / n_b - won_a / n_a,
            "ci_low": float(low), "ci_high": float(high), "p_value": float(p)}
