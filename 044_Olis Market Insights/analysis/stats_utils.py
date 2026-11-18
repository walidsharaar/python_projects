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
