"""Step 9: SIMULATED EventPro data for the questions Olist cannot answer.

Run from the project root:
    python src\\simulate.py

Why this exists:
    The Olist data is real, but it has no web traffic, no marketing spend,
    no lost deals and no industries. The Event Inc. job asks exactly about
    those: SEO/GEO and content, channel cost, win/loss for enterprise deals
    and segments such as Pharma vs. Automotive.

Rules (see docs/simulation.md):
    - Every number here is SYNTHETIC. It never mixes with the Olist data:
      own folder (data/simulated), own database (database/simulation.duckdb),
      every table starts with sim_, every page shows a warning banner.
    - The data has a planned story (written below and in docs/simulation.md).
      The analysis must find it again; that is how the method is tested.
    - Same seed and fixed reference date: every run gives the same data.

What happens:
    1. Generate two "exports": GA4-style daily web traffic per channel
       and CRM opportunities (won, lost, open).
    2. Write them as CSV to data/simulated/ (like a real source delivery).
    3. Load them into database/simulation.duckdb and run sql/simulation/*.sql.
    4. Validate: grain, totals, and that the planned story is really in the data.
"""

from datetime import date, timedelta
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "simulated"
SQL_DIR = ROOT / "sql" / "simulation"
DB_PATH = ROOT / "database" / "simulation.duckdb"

SEED = 2026
START = date(2024, 1, 1)
REFERENCE_DATE = date(2025, 12, 31)          # "today" in the simulation: two full years

# Planned tracking incident: after a website release, the AI referrer was lost
# and 80 % of AI-referral sessions were recorded as "direct".
INCIDENT_START, INCIDENT_END, INCIDENT_SHARE = date(2025, 6, 2), date(2025, 6, 22), 0.80

# Corporate events: bookings peak in autumn (Christmas parties) and spring.
SEASON = {1: 0.75, 2: 0.90, 3: 1.00, 4: 1.05, 5: 1.05, 6: 0.95,
          7: 0.75, 8: 0.80, 9: 1.20, 10: 1.35, 11: 1.25, 12: 0.70}

# channel: sessions per weekday at start, at end (two years later),
#          session -> quote request rate, quote -> booking rate, cost per session (EUR)
CHANNELS = {
    "organic_search": (1400, 1190, 0.020, 0.25, 0.00),   # slowly losing traffic to AI answers
    "ai_referral":    (20,   220,  0.045, 0.30, 0.00),   # GEO: ChatGPT, Perplexity, Gemini
    "paid_search":    (600,  620,  0.025, 0.22, 1.30),
    "direct":         (700,  760,  0.030, 0.30, 0.00),
    "social":         (500,  520,  0.006, 0.15, 0.40),   # cheap traffic, few bookings
    "email":          (150,  160,  0.035, 0.28, 0.00),
    "referral":       (120,  130,  0.022, 0.25, 0.00),
}

INDUSTRIES = {"pharma": 0.16, "automotive": 0.18, "it_software": 0.24,
              "finance_insurance": 0.17, "consulting": 0.15, "public_sector": 0.06, None: 0.04}
INDUSTRY_EFFECT = {"pharma": 0.5, "automotive": -0.4, "it_software": 0.1,
                   "finance_insurance": 0.0, "consulting": -0.1, "public_sector": -0.3, None: 0.0}
SIZES = {"250-999": 0.50, "1000-4999": 0.35, "5000+": 0.15}
SIZE_VALUE = {"250-999": 6_000, "1000-4999": 12_000, "5000+": 25_000}   # median deal value EUR
LOSS_REASONS = {"price": 0.25, "competitor": 0.20, "no_suitable_venue": 0.15,
                "slow_response": 0.10, "event_cancelled": 0.15, "no_decision": 0.15}


def days() -> list[date]:
    n = (REFERENCE_DATE - START).days + 1
    return [START + timedelta(d) for d in range(n)]


def progress(d: date) -> float:
    """0 at the start, 1 at the reference date."""
    return (d - START).days / (REFERENCE_DATE - START).days



def generate_web(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for d in days():
        weekday = 1.0 if d.weekday() < 5 else 0.45
        for channel, (start, end, quote_rate, booking_rate, cost) in CHANNELS.items():
            p = progress(d)
            level = start * (end / start) ** p if channel == "ai_referral" else start + (end - start) * p
            sessions = int(rng.poisson(level * SEASON[d.month] * weekday))
            quotes = int(rng.binomial(sessions, quote_rate))
            bookings = int(rng.binomial(quotes, booking_rate))
            values = rng.lognormal(np.log(7_000), 0.6, bookings)
            cpc = cost * (1.10 if d.year == 2025 else 1.0) * rng.uniform(0.9, 1.1)
            rows.append([d, channel, sessions, quotes, bookings, values, round(sessions * cpc, 2)])

    web = pd.DataFrame(rows, columns=["date", "channel", "sessions", "quote_requests",
                                      "bookings", "values", "spend_eur"])
    # Planned tracking incident: move most AI-referral traffic to "direct"
    hit = (web["channel"] == "ai_referral") & web["date"].between(INCIDENT_START, INCIDENT_END)
    for i in web.index[hit]:
        j = web.index[(web["date"] == web.at[i, "date"]) & (web["channel"] == "direct")][0]
        s, q, b = (int(web.at[i, c]) for c in ("sessions", "quote_requests", "bookings"))
        # Move whole visitors: the moved quotes are a subset of the moved sessions, and the moved
        # bookings a subset of the moved quotes. Then the funnel stays valid in both rows.
        moved_s = int(rng.binomial(s, INCIDENT_SHARE))
        moved_q = int(rng.hypergeometric(q, s - q, moved_s)) if moved_s else 0
        moved_b = int(rng.hypergeometric(b, q - b, moved_q)) if moved_q else 0
        for col, moved in (("sessions", moved_s), ("quote_requests", moved_q), ("bookings", moved_b)):
            web.at[i, col] -= moved
            web.at[j, col] += moved
        vals = web.at[i, "values"]
        web.at[j, "values"] = np.concatenate([web.at[j, "values"], vals[:moved_b]])
        web.at[i, "values"] = vals[moved_b:]

    web["booking_value_eur"] = web["values"].map(lambda v: round(float(np.sum(v)), 2))
    return web.drop(columns="values")



def pick(rng, options: dict, size: int) -> np.ndarray:
    keys = list(options)
    idx = rng.choice(len(keys), size=size, p=np.array(list(options.values())) / sum(options.values()))
    return np.array([keys[i] for i in idx], dtype=object)


def generate_crm(rng: np.random.Generator) -> pd.DataFrame:
    created = [d for d in days() if d.weekday() < 5 for _ in range(rng.poisson(2.5))]
    n = len(created)
    industry = pick(rng, INDUSTRIES, n)
    size = pick(rng, SIZES, n)
    response_h = np.round(rng.lognormal(np.log(6), 1.3, n), 1)
    channels = list(CHANNELS)
    lead_channel = rng.choice(channels, n, p=[0.30, 0.06, 0.20, 0.22, 0.06, 0.08, 0.08])

    rows = []
    for k in range(n):
        c, ind, sz, resp = created[k], industry[k], size[k], response_h[k]
        event = pick(rng, {"christmas_party": 0.45 if c.month in (8, 9, 10, 11) else 0.10,
                           "conference": 0.25, "training": 0.30, "team_event": 0.25}, 1)[0]
        logit = np.log(0.28 / 0.72) + INDUSTRY_EFFECT[ind] + (0.2 if sz == "5000+" else 0.0)
        logit += -0.9 if resp > 24 else (-0.3 if resp > 4 else 0.0)
        if ind == "automotive" and c >= date(2025, 7, 1):    # planned: budget cuts in automotive
            logit -= 1.1
        won = rng.random() < 1 / (1 + np.exp(-logit))

        cycle_median = 21 * (1.6 if ind == "pharma" else 2.0 if ind == "public_sector" else 1.0)
        cycle = max(1, int(rng.lognormal(np.log(cycle_median), 0.6)))
        closed = c + timedelta(cycle)
        value = SIZE_VALUE[sz] * (1.4 if ind == "pharma" else 1.0) * rng.lognormal(0, 0.5)

        if closed > REFERENCE_DATE:
            status, closed, reason = "open", None, None
        elif won:
            status, reason = "won", None
        else:
            status = "lost"
            weights = dict(LOSS_REASONS)
            if ind == "automotive":
                weights["price"] *= 2.2
            if ind == "pharma":
                weights["no_suitable_venue"] *= 1.8
            if resp > 24:
                weights["slow_response"] *= 3.5
            reason = pick(rng, weights, 1)[0]
            if rng.random() < 0.08:                          # planned defect: not recorded in the CRM
                reason = None
        rows.append([f"OPP-{k + 1:05d}", c, closed, status, ind, sz, event, lead_channel[k],
                     round(float(value), 2), float(resp), reason, f"R{rng.integers(1, 9):02d}"])

    return pd.DataFrame(rows, columns=[
        "opportunity_id", "created_date", "closed_date", "status", "industry", "company_size",
        "event_type", "lead_channel", "deal_value_eur", "first_response_hours", "loss_reason", "sales_rep"])



def build_database() -> duckdb.DuckDBPyConnection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    for name in ("web_traffic_daily", "crm_opportunities"):
        path = (OUT_DIR / f"{name}.csv").as_posix()
        con.execute(f"CREATE OR REPLACE TABLE sim_stg_{name} AS SELECT * FROM read_csv_auto('{path}')")
    for sql_file in sorted(SQL_DIR.glob("*.sql")):
        con.execute(sql_file.read_text(encoding="utf-8"))
        print(f"  ran {sql_file.name}")
    return con


GRAIN = {
    "sim_channel_monthly": ["month", "channel"],
    "sim_channel_summary": ["channel"],
    "sim_ai_referral_weekly": ["week"],
    "sim_winloss_industry": ["industry"],
    "sim_loss_reasons": ["industry", "loss_reason"],
    "sim_response_time": ["response_bucket"],
    "sim_kpi_summary": ["kpi_key"],
}


def validate(con, web: pd.DataFrame, crm: pd.DataFrame) -> None:
    one = lambda sql: con.execute(sql).fetchone()[0]
    for table, cols in GRAIN.items():
        keys = ", ".join(cols)
        dup = one(f"SELECT COUNT(*) FROM (SELECT {keys} FROM {table} GROUP BY ALL HAVING COUNT(*) > 1)")
        assert dup == 0, f"{table}: grain ({keys}) is not unique"
    # Totals must survive the SQL layer unchanged (no rows lost or doubled)
    assert one("SELECT SUM(sessions) FROM sim_channel_monthly") == web["sessions"].sum()
    assert one("SELECT SUM(bookings) FROM sim_channel_monthly") == web["bookings"].sum()
    assert one("SELECT SUM(opportunities) FROM sim_winloss_industry") == len(crm)

    # The planned story must be in the data (otherwise the demo would show noise)
    rate = dict(con.execute("SELECT industry, win_rate FROM sim_winloss_industry").fetchall())
    assert rate["pharma"] > rate["automotive"], "story: pharma should win more often than automotive"
    slow, fast = (one(f"SELECT win_rate FROM sim_response_time WHERE response_bucket = '{b}'")
                  for b in ("over_24h", "under_4h"))
    assert slow < fast, "story: slow first response should lower the win rate"
    june = one("SELECT MIN(ai_share) FROM sim_ai_referral_weekly WHERE is_incident")
    may = one("SELECT AVG(ai_share) FROM sim_ai_referral_weekly WHERE week BETWEEN '2025-05-01' AND '2025-05-31'")
    assert june < 0.5 * may, "story: the tracking incident should be visible"
    print("  validation passed: grain, totals and planned story")


def main() -> None:
    rng = np.random.default_rng(SEED)          # seed inside main(): same data on every run
    print("Generating SIMULATED EventPro data (not Olist, not Event Inc.) ...")
    web = generate_web(rng)
    crm = generate_crm(rng)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    web.to_csv(OUT_DIR / "web_traffic_daily.csv", index=False)
    crm.to_csv(OUT_DIR / "crm_opportunities.csv", index=False)
    print(f"  web_traffic_daily.csv  {len(web):>6,} rows  ({START} to {REFERENCE_DATE})")
    print(f"  crm_opportunities.csv  {len(crm):>6,} rows  "
          f"(won {sum(crm.status == 'won'):,}, lost {sum(crm.status == 'lost'):,}, open {sum(crm.status == 'open'):,})")

    with build_database() as con:
        validate(con, web, crm)
        print("\nSimulated KPIs (sim_kpi_summary):")
        for key, value, unit in con.execute("SELECT kpi_key, value, unit FROM sim_kpi_summary ORDER BY kpi_key").fetchall():
            shown = f"{value:.1%}" if unit == "rate" else f"{value:,.0f}"
            print(f"  {key:<34} {shown:>12}")
    print(f"\nDone: {DB_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
