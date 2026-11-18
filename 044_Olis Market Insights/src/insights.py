"""Insights shared by the dashboard, the report and the AI assistant.

One implementation for each piece of logic, so the executive screen, the
GTM report and the assistant can never tell three different stories:
    latest_month_check()  is the latest tracked month different from earlier ones?
    facts()               everything the AI assistant may use, as plain numbers
"""

import pandas as pd
from statsmodels.stats.proportion import proportions_ztest

ALPHA = 0.05

# The nine findings (README section 9): who acts and how sure we are.
# The words are in src/i18n/translations.json (finding.N.title / action / measure).
FINDINGS = [
    {"n": 1, "teams": ["marketing", "data"], "confidence": "high"},
    {"n": 2, "teams": ["data", "leadership"], "confidence": "high"},
    {"n": 3, "teams": ["marketing"], "confidence": "medium"},
    {"n": 4, "teams": ["sales", "product"], "confidence": "mixed"},
    {"n": 5, "teams": ["sales", "product"], "confidence": "medium"},
    {"n": 6, "teams": ["marketing", "product"], "confidence": "medium"},
    {"n": 7, "teams": ["marketing"], "confidence": "low"},
    {"n": 8, "teams": ["sales", "leadership"], "confidence": "high"},
    {"n": 9, "teams": ["sales"], "confidence": "medium"},
]


def latest_month_check(monthly: pd.DataFrame) -> dict:
    """Latest tracked lead month against all earlier tracked months together.

    monthly: mart_gtm_monthly, only rows with deal_tracking_complete, sorted by month.
    Two-proportion z-test on the 60-day win rate.
    """
    monthly = monthly[monthly["deal_tracking_complete"]].sort_values("cohort_month")
    last, earlier, before = monthly.iloc[-1], monthly.iloc[:-1], monthly.iloc[-2]
    won_earlier, leads_earlier = int(earlier["won_60d"].sum()), int(earlier["leads"].sum())
    _, p = proportions_ztest([int(last["won_60d"]), won_earlier], [int(last["leads"]), leads_earlier])
    return {
        "month": last["cohort_month"],
        "leads": int(last["leads"]),
        "leads_change": float(last["leads"] / before["leads"] - 1),
        "rate": float(last["lead_to_win_rate_60d"]),
        "rate_earlier": won_earlier / leads_earlier,
        "p_value": float(p),
        "clear_change": bool(p < ALPHA),
    }


def _records(df: pd.DataFrame, columns: list[str], digits: int = 4) -> list[dict]:
    out = df[columns].copy()
    for col in out.select_dtypes("number").columns:
        out[col] = out[col].round(digits)
    return out.astype(object).where(out.notna(), None).to_dict(orient="records")


def facts(kpis: pd.DataFrame, funnel: pd.DataFrame, channels: pd.DataFrame, check: dict,
          data_quality: pd.DataFrame, lead_types: pd.DataFrame | None = None,
          findings: list[dict] | None = None) -> dict:
    """The ONLY input the AI assistant gets. Rates are fractions (0.106 = 10.6 %)."""
    return {
        "note": "Olist marketplace data (Brazil, 2016-2018). Rates are fractions. GMV is not revenue. "
                "No marketing spend data, so CAC and ROI are unknown.",
        "kpis": {key: {"value": round(float(row["value"]), 4), "unit": row["unit"],
                       "numerator": None if pd.isna(row["numerator"]) else float(row["numerator"]),
                       "denominator": None if pd.isna(row["denominator"]) else float(row["denominator"])}
                 for key, row in kpis.iterrows()},
        "funnel_per_1000_leads": _records(funnel, ["stage_key", "per_1000_leads", "rate_from_previous"], 2),
        "channels": _records(channels, ["origin", "leads", "won", "lead_to_win_rate", "lead_to_win_ci_low",
                                        "lead_to_win_ci_high", "is_small_sample", "won_sellers_full_window",
                                        "activation_rate", "activated_per_1000_leads", "is_small_seller_sample"]),
        "lead_types": None if lead_types is None else _records(
            lead_types, ["lead_group", "sellers", "activation_rate", "ci_low", "ci_high", "seller_share", "gmv_share"]),
        "latest_month_check": {**check, "month": str(check["month"])[:10]},
        "data_quality": _records(data_quality, ["check_key", "records", "total_records", "affects"]),
        "findings": findings or [],
    }
