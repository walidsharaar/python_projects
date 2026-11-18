"""Step 7: automated GTM report in English, German and Persian.

Run from the project root (after src\\warehouse.py):
    python src\\weekly_report.py                 # all languages, no AI
    python src\\weekly_report.py --lang de       # one language
    python src\\weekly_report.py --ai            # add an AI summary (optional)

Output: reports/weekly/gtm_report_<data end>_<lang>.md

Rules (the same as for the dashboard):
    - Every number comes from the KPI layer and the marts. The report
      calculates only the anomaly check for the latest month.
    - The report is complete without AI. The AI summary is optional,
      gets ONLY the numbers this script already calculated, must not
      calculate new ones, and is labelled as a draft for human review.
    - It opens the warehouse read-only, so it runs while the dashboard runs.
"""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.i18n import fmt_date, fmt_month, fmt_num, fmt_pct, languages, t  # noqa: E402

# Default warehouse; set GTM_WAREHOUSE (or pass --database) to use another copy
DEFAULT_DB = Path(os.environ.get("GTM_WAREHOUSE", ROOT / "database" / "warehouse.duckdb"))
OUTPUT_DIR = ROOT / "reports" / "weekly"
REPORT_KPIS = ["mql_count", "lead_to_win_rate_60d_tracked", "sales_cycle_median_days",
               "unattributed_win_share", "seller_activation_rate_full_window",
               "time_to_first_sale_median_days", "gmv_90d_per_won_seller", "buyer_repeat_rate"]
ALPHA = 0.05            # threshold for "clear change" in the anomaly check
DQ_THRESHOLD = 0.05     # data quality gaps below 5 % of their records are not listed
TOP_FINDINGS = [1, 2, 3]
AI_MODEL = "claude-opus-5-5"


# ------------------------------------------------------------------ data
def load(db_path: Path) -> dict:
    with duckdb.connect(str(db_path), read_only=True) as con:
        return {
            "kpis": con.execute("SELECT * FROM mart_kpi_summary").df().set_index("kpi_key"),
            "monthly": con.execute("SELECT * FROM mart_gtm_monthly WHERE deal_tracking_complete "
                                   "ORDER BY cohort_month").df(),
            "dq": con.execute("SELECT * FROM mart_data_quality").df(),
            "data_end": con.execute("SELECT MAX(purchased_at) FROM fct_order_items").fetchone()[0],
        }


def latest_month_check(monthly) -> dict:
    """Latest tracked month vs all earlier tracked months together (two-proportion z-test)."""
    last, earlier, before = monthly.iloc[-1], monthly.iloc[:-1], monthly.iloc[-2]
    won_earlier, leads_earlier = int(earlier["won_60d"].sum()), int(earlier["leads"].sum())
    _, p = proportions_ztest([int(last["won_60d"]), won_earlier], [int(last["leads"]), leads_earlier])
    return {
        "month": last["cohort_month"],
        "leads": int(last["leads"]),
        "leads_change": last["leads"] / before["leads"] - 1,
        "rate": float(last["lead_to_win_rate_60d"]),
        "rate_earlier": won_earlier / leads_earlier,
        "p_value": float(p),
        "clear_change": bool(p < ALPHA),
    }


# ------------------------------------------------------------- formatting
def kpi_value(row, lang: str) -> tuple[str, str]:
    """Value and basis of one KPI, formatted for the language (same rules as the dashboard)."""
    unit = row["unit"]
    if unit == "rate":
        return fmt_pct(row["value"], lang), t("basis.ratio", lang, num=fmt_num(row["numerator"], lang),
                                              den=fmt_num(row["denominator"], lang))
    if unit == "brl":
        return t("unit.brl", lang, value=fmt_num(row["value"], lang)), t("basis.n", lang, n=fmt_num(row["denominator"], lang))
    if unit == "days":
        return t("unit.days", lang, value=fmt_num(row["value"], lang)), t("basis.n", lang, n=fmt_num(row["numerator"], lang))
    return fmt_num(row["value"], lang), ""


def signed_pct(rate: float, lang: str) -> str:
    return ("+" if rate >= 0 else "−") + fmt_pct(abs(rate), lang)


def build_report(data: dict, check: dict, lang: str, ai_text: str | None, ai_status: str) -> str:
    tr = lambda key, **v: t(key, lang, **v)
    k = data["kpis"]
    lines = [f"# {tr('report.title')}: {fmt_date(data['data_end'], lang)}", "",
             f"_{tr('report.meta', today=fmt_date(date.today(), lang), data_end=fmt_date(data['data_end'], lang))}_", ""]

    # 1. KPIs
    lines += [f"## {tr('report.kpis.title')}", "",
              f"| {tr('report.kpis.kpi')} | {tr('report.kpis.value')} | {tr('report.kpis.basis')} |",
              "|---|---|---|"]
    for key in REPORT_KPIS:
        value, basis = kpi_value(k.loc[key], lang)
        lines.append(f"| {tr(f'kpi.{key}.name')} | {value} | {basis} |")

    # 2. latest month
    month = fmt_month(check["month"], lang)
    lines += ["", f"## {tr('report.latest.title')}", "", tr("report.latest.intro"), "",
              "- " + tr("report.latest.leads", month=month, leads=fmt_num(check["leads"], lang),
                        change=signed_pct(check["leads_change"], lang)),
              "- " + tr("report.latest.rate", month=month, rate=fmt_pct(check["rate"], lang),
                        earlier=fmt_pct(check["rate_earlier"], lang), p=fmt_num(check["p_value"], lang, 3)),
              "", f"> {tr('report.latest.alert' if check['clear_change'] else 'report.latest.normal')}"]

    # 3. data quality
    dq = data["dq"].assign(share=lambda d: d["records"] / d["total_records"])
    dq = dq[dq["share"] >= DQ_THRESHOLD].sort_values("share", ascending=False)
    lines += ["", f"## {tr('report.dq.title')}", "", tr("report.dq.intro", threshold=fmt_pct(DQ_THRESHOLD, lang, 0)), ""]
    lines += ["- " + tr("report.dq.line", check=tr(f"dq.check.{r.check_key}"), records=fmt_num(r.records, lang),
                        total=fmt_num(r.total_records, lang), share=fmt_pct(r.share, lang),
                        affects=tr(f"dq.affects.{r.affects}"))
              for r in dq.itertuples()]

    # 4. actions
    lines += ["", f"## {tr('report.actions.title')}", ""]
    for n in TOP_FINDINGS:
        lines += [f"{n}. **{tr(f'finding.{n}.title')}.** {tr(f'finding.{n}.action')} "
                  f"_{tr('rec.measure')}: {tr(f'finding.{n}.measure')}._"]

    # 5. optional AI summary
    lines += ["", f"## {tr('report.ai.title')}", ""]
    if ai_text:
        lines += [f"_{tr('report.ai.note', model=AI_MODEL)}_", "", ai_text]
    else:
        lines += [tr("report.ai.refused" if ai_status == "refused" else "report.ai.skipped")]

    lines += ["", "---", "", f"_{tr('report.footer')}_", ""]
    return "\n".join(lines)


# ------------------------------------------------------------ AI summary
def facts_for_ai(data: dict, check: dict) -> dict:
    """The ONLY input the model gets: numbers this script already calculated."""
    k = data["kpis"]
    return {
        "kpis": {key: {"value": round(float(k.loc[key, "value"]), 4), "unit": k.loc[key, "unit"],
                       "numerator": float(k.loc[key, "numerator"]),
                       "denominator": None if pd.isna(k.loc[key, "denominator"])
                       else float(k.loc[key, "denominator"])}
                 for key in REPORT_KPIS},
        "latest_month_check": {**check, "month": str(check["month"])[:10],
                               "rate": round(check["rate"], 4), "rate_earlier": round(check["rate_earlier"], 4),
                               "leads_change": round(check["leads_change"], 4), "p_value": round(check["p_value"], 4)},
        "data_quality": data["dq"].to_dict(orient="records"),
        "top_actions": [t(f"finding.{n}.title", "en") for n in TOP_FINDINGS],
    }


def ai_summary(facts: dict, lang: str) -> tuple[str | None, str]:
    """Returns (text, status). Status: 'ok', 'refused' or 'skipped'. Never raises."""
    try:
        import anthropic          # optional dependency: pip install anthropic
    except ImportError:
        print("  AI summary skipped: the anthropic package is not installed (pip install anthropic).")
        return None, "skipped"

    language = languages()[lang]["label"]
    system = (
        "You write a short management summary of a Go-to-Market KPI report for a CPO. "
        f"Write in {language}, in plain, natural business language (CEFR B1-B2), at most 120 words, "
        "as 3 to 5 bullet points. Use ONLY the numbers in the JSON you receive; do not calculate, "
        "estimate or round to new numbers. Clearly separate facts from possible explanations, and "
        "name possible explanations as things to check, not as causes. Rates are fractions "
        "(0.106 means 10.6 %). GMV is not revenue."
    )
    try:
        client = anthropic.Anthropic()
        response = client.beta.messages.create(
            model=AI_MODEL,
            max_tokens=2000,
            output_config={"effort": "medium"},          # the default on this model, set explicitly
            betas=["server-side-fallback-2026-07-01"],   # on a refusal, the API retries on a fallback model
            fallbacks="default",
            system=system,
            messages=[{"role": "user", "content": json.dumps(facts, ensure_ascii=False, default=str)}],
        )
    except anthropic.AuthenticationError:
        print("  AI summary skipped: no valid API credentials (set ANTHROPIC_API_KEY or run ant auth login).")
        return None, "skipped"
    except anthropic.RateLimitError:
        print("  AI summary skipped: rate limited. The report is complete without it.")
        return None, "skipped"
    except anthropic.APIStatusError as e:
        print(f"  AI summary skipped: API error {e.status_code}.")
        return None, "skipped"
    except anthropic.APIConnectionError:
        print("  AI summary skipped: no connection to the API.")
        return None, "skipped"

    if response.stop_reason == "refusal":
        return None, "refused"
    text = "\n".join(block.text for block in response.content if block.type == "text").strip()
    return (text or None), ("ok" if text else "skipped")


# ------------------------------------------------------------------ main
def main() -> None:
    parser = argparse.ArgumentParser(description="Create the GTM report from the KPI layer.")
    parser.add_argument("--lang", choices=list(languages()), help="only this language (default: all)")
    parser.add_argument("--ai", action="store_true", help="add an AI summary (optional, needs anthropic)")
    parser.add_argument("--database", type=Path, default=DEFAULT_DB, help="warehouse file (default: %(default)s)")
    args = parser.parse_args()

    if not args.database.exists():
        raise SystemExit(f"Warehouse not found: {args.database}. Run src\\clean.py and src\\warehouse.py first.")

    data = load(args.database)
    check = latest_month_check(data["monthly"])
    facts = facts_for_ai(data, check) if args.ai else None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for lang in ([args.lang] if args.lang else list(languages())):
        ai_text, status = ai_summary(facts, lang) if args.ai else (None, "skipped")
        path = OUTPUT_DIR / f"gtm_report_{data['data_end']:%Y-%m-%d}_{lang}.md"
        path.write_text(build_report(data, check, lang, ai_text, status), encoding="utf-8")
        print(f"Saved: {path.relative_to(ROOT)}")

    flag = "CLEAR CHANGE" if check["clear_change"] else "no clear change"
    print(f"Latest month {check['month']:%Y-%m}: win rate {check['rate']:.1%} vs {check['rate_earlier']:.1%} "
          f"earlier (p = {check['p_value']:.3f}) -> {flag}")


if __name__ == "__main__":
    main()
