# Marketplace GTM Analytics: From Lead to Active Seller

> End-to-end Go-to-Market analysis of a **two-sided marketplace with a B2B seller side**: from the first marketing touchpoint, through the sales close, to the seller's first revenue.
> Built with Python, DuckDB/SQL and Streamlit on **real** marketplace data (Olist, Brazil, 2016–2018).

*Deutsche Version: [README.de.md](README.de.md)*

---

## 1. Business context

Olist is a marketplace that connects small and mid-sized merchants (sellers) with large Brazilian e-commerce channels. To grow, it has to:

1. **Acquire sellers** (supply side): marketing generates leads (MQLs), and sales reps (SDRs/SRs) convert them into closed deals.
2. **Activate sellers**: a closed deal only creates value once the seller actually starts selling.
3. **Serve buyers** (demand side): customers place orders and, ideally, come back.

This is the typical GTM problem of any marketplace that acquires business sellers: **Marketing, Sales and Product each own one part of the funnel, but growth depends on the whole chain.** This project builds one shared, trusted data foundation across all three.

```text
Marketing                 Sales                      Product / Marketplace
──────────────────────    ───────────────────────    ─────────────────────────────
Channel → Landing page → MQL → SDR/SR → Closed deal → First sale → GMV → Buyer repeat
   (origin)                         (won_date)        (activation)          (retention)
```

---

## 2. Business questions

Each question maps to a typical responsibility of a GTM & Insights analyst. The **"Validity check"** column records what the data can and cannot support. It was written *before* the analysis so that the conclusions stay honest.

| # | GTM responsibility | Business question | Method | Validity check |
|---|---|---|---|---|
| Q1 | **GTM performance monitoring** | What is our lead-to-win conversion, how long does a deal take, and how does this develop month by month? | KPI tree, monthly funnel, fixed 60-day conversion window | Recent cohorts are right-censored, so we compare fixed windows instead of raw "won ever" |
| Q2 | **Channel performance** | Which acquisition channels deliver leads that *close*, and which deliver sellers that actually *sell*? | Conversion + activation + 90-day GMV per channel, Wilson confidence intervals | Small channels (n < 100) are reported with intervals, not as rankings |
| Q3 | **Tracking & data quality** | How much of the funnel is unattributed, and does it distort channel decisions? | Share of `unknown`/missing origin, conversion comparison | 14.5% of all leads (14.4% of 2018 leads) have no usable origin, and they convert *above* average |
| Q4 | **Segment comparison** | Which business segments (e.g. `health_beauty` vs `car_accessories`) close faster, activate more and generate more GMV? | Segment benchmarking on won deals | Segments are only known for **won** deals, so this compares *quality of wins*, not conversion |
| Q5 | **Cohort analysis + before/after** | Did conversion really improve between 2017 and 2018, or is it a data artifact? | Monthly lead cohorts, fixed windows, data coverage checks | See observation H1: a naive before/after comparison would be misleading |
| Q6 | **Win/loss for sales enablement** | What separates leads that close from leads that don't, and wins that activate from wins that don't? | Logistic regression (origin, landing page, month), won-vs-activated comparison (lead type, business type, SDR) | No explicit loss reasons exist, so "loss" = MQL without a closed deal |
| Q7 | **Content effectiveness** | Which landing pages convert best, and are the differences statistically real? | Chi-square test, pairwise z-tests with Benjamini–Hochberg correction | 495 landing pages, so a multiple-testing correction is mandatory |
| Q8 | **Experiment design (A/B test)** | If we test a new landing page, how many leads and how many weeks do we need, and how would we evaluate it? | Power analysis, simulated A/B test with known true effect, CI-based decision | The experiment data is **simulated** and clearly labelled; it is used to validate the method, not to claim results |
| Q9 | **Marketplace activation** | How many won sellers make a first sale, how fast, and what predicts it? | Activation rate, time-to-first-sale, 90-day GMV | Order items end on 3 Sep 2018 (later orders have no items), so only deals won before about 5 Jun 2018 get a full 90-day window |
| Q10 | **Demand-side retention** | Do buyers come back? How does repeat-purchase behaviour look across cohorts? | Customer cohort retention matrix | Uses `customer_unique_id` (not `customer_id`, which is per order) |
| Q11 | **Automated reporting** | Can the weekly GTM report build itself, so analyst time goes into recommendations? | Scripted KPI pipeline + LLM-generated summary of anomalies, reviewed by a human | The AI summary only describes pre-computed numbers and never computes them itself |

---

## 3. Data at a glance

Source: Kaggle, *Marketing Funnel by Olist* + *Brazilian E-Commerce Public Dataset by Olist*.

| Table | Rows | Period | Used for |
|---|---|---|---|
| Marketing qualified leads | 8,000 | Jun 2017 – May 2018 (first contact) | Q1–Q3, Q5–Q8 |
| Closed deals | 842 | Dec 2017 – Nov 2018 (won date) | Q1, Q4, Q6, Q9 |
| Orders | 99,441 | Sep 2016 – Oct 2018 (with items only until 3 Sep 2018) | Q9, Q10 |
| Order items, sellers, customers, products, payments, reviews | — | — | Q9, Q10 |

Headline numbers (first data audit on all leads and all won sellers; the fair comparisons in section 9 use 2018 lead cohorts and sellers with a full 90-day window):

- **Lead-to-win conversion:** 842 / 8,000 = **10.5%** (won ever); **10.6%** within 60 days for 2018 cohorts (636 of 5,998)
- **Median sales cycle:** 14 days (mean 48, so a long tail)
- **Seller activation:** only **45%** of won sellers ever make a sale (51% for sellers with a full 90-day window)
- **Median time from close to first sale:** 44 days
- **GMV concentration:** the top 10% of new sellers generate **83%** of the GMV of all new sellers in their first 90 days
- **Buyer repeat rate:** only **3.1%** of customers (2,924 of 95,560) have two or more non-canceled orders

---

## 4. Preliminary observations (hypotheses to test)

These come from the initial data audit, which used all leads and all won sellers. They are **hypotheses**, not conclusions. Each one has a **Result** line with the tested number on the fair population (2018 lead cohorts, sellers with a full 90-day window). That is why some numbers differ from the audit.

**H1: The 2017 → 2018 "conversion jump" is most likely a tracking artifact, not a success.**
Leads from 2017 show a 60-day conversion of **0.5%**, while leads from 2018 show **10.6%**. But the first `won_date` in the data is **5 Dec 2017**, so closed deals were probably only recorded from then on. A naive before/after comparison would celebrate a 20× improvement that never happened.
→ *Implication: before/after analyses need a data-coverage check first. Valid comparisons use 2018 cohorts only.*

**Result: confirmed.** With both periods fully tracked, Jan–Feb 2018 converts at 10.9% and Mar–Apr 2018 at 11.8%: about +1 point, not 21×. (Finding 2)

**H2: Unattributed leads are high-intent leads, so tracking loss distorts channel decisions.**
`unknown` + missing origin = 1,159 leads (14.5%), converting at about **16–23%**, against 11.8% for organic search.
→ *Implication: fix attribution first (UTM parameters, landing-page tracking). Otherwise budget is shifted on incomplete data.*

**Result: confirmed.** 2018 cohorts: 861 of 5,998 leads (14.4%) have no channel, but they bring 160 of 636 60-day wins (25.2%), with a win rate of 18.6% vs 9.3% for tracked leads. 62% of them arrive through one landing page. (Finding 1)

**H3: Channels differ massively in quality, not just volume.**
Paid search (12.3%) and organic search (11.8%) convert similarly, while email (3.0%) and social (5.6%) convert at a fraction of that, although social delivers 1,350 leads.

**Result: confirmed, with a correction.** 2018 cohorts, 60-day window: paid search 11.6% vs organic search 11.5% (p = 0.95, no real difference), social 4.7% on 1,051 leads, email 3.2%. The audit numbers above used all months and "won ever". (Findings 3 and 7)

**H4: A "won" deal is not a success: lead type predicts activation.**
`online_big` leads activate at **63%** (mean 90-day GMV ≈ 1,490 BRL), while `offline` leads activate at **29%** (≈ 80 BRL) and `industry` leads at 33%.
→ *Implication for sales enablement: qualify on activation likelihood, not only on closing likelihood.*

**Result: confirmed.** Sellers with a full 90-day window: `online_big` 72%, `offline` 34%, `industry` 37%. The pattern holds in a logistic regression (odds ratio `offline` 0.36). `online_big` is 15% of sellers but 47% of 90-day GMV. (Finding 4)

**H5: A few landing pages carry the funnel.**
The two largest landing pages (about 900 leads each) convert at about **19–20%**, while other high-traffic pages convert at 3–7%.

**Result: partly confirmed.** In 2018 cohorts the two largest pages have 751 and 726 leads and convert at 19.2% and 19.6%. But 71% of the leads on page b76ef374 are untracked, and after adjusting for the channel mix and a Benjamini–Hochberg correction only 3 of 18 pages really differ from their channel. (Finding 6)

**H6: Classical A/B tests on lead-to-win are too slow at this volume.**
To detect an uplift from 12% to 14% (α = 0.05, power = 80%) we need about **4,400 leads per variant**. At about 1,200 MQLs per month that takes **7+ months**.
→ *Implication: test on faster upper-funnel metrics (MQL rate, SDR contact rate), use a sequential design, or use before/after with a control group (difference-in-differences).*

**Result: confirmed.** The power analysis gives 4,433 leads per group, so about 9.4 months including the 2 months until the outcome is known. (reports/analysis/06_experiments.md)

---

## 5. KPI definitions (single source of truth)

| KPI | Definition | Why this definition |
|---|---|---|
| MQL | A lead in `marketing_qualified_leads` with a first contact date | Entry point of the sales funnel |
| Lead-to-win rate (60d) | MQLs won within 60 days of first contact ÷ all MQLs in the cohort | A fixed window makes old and new cohorts comparable |
| Sales cycle | `won_date` − `first_contact_date`, in days (median reported) | The median is robust against the long tail |
| Seller activation rate | Won sellers with ≥ 1 non-cancelled order ÷ won sellers | Separates "signed" from "selling" |
| Time to first sale | First order date − `won_date`, in days | Onboarding speed |
| 90-day GMV per won seller | Sum of item prices in the first 90 days after `won_date` | A comparable value metric per acquired seller |
| Buyer repeat rate | Customers (`customer_unique_id`) with ≥ 2 non-canceled orders ÷ customers with ≥ 1 non-canceled order | Demand-side loyalty |

---

## 6. Data quality and limitations

Documented up front, because a trustworthy data foundation starts with knowing its limits.

- **No loss reasons:** "lost" means an MQL with no closed deal. Loss reasons would need CRM data.
- **Deal attributes exist only for won deals:** segment, lead type and business type cannot explain conversion, only the quality of wins.
- **`declared_monthly_revenue` is unusable:** about 95% of the values are 0.
- **`has_company`, `has_gtin`, `average_stock`, `declared_product_catalog_size`:** about 92% missing, so they are excluded.
- **`lead_behaviour_profile`:** 21% missing, with multi-labels such as `"cat, wolf"`.
- **Right-censoring:** recent leads and deals have had less time to convert or activate, so fixed windows are used.
- **One deal has a negative sales cycle** (won before first contact), which is flagged and excluded.
- **Coverage gap:** closed deals start in Dec 2017 (see H1).
- **Effective data end:** the last order is from 17 Oct 2018, but the last order *with items* is from 3 Sep 2018. All 90-day windows use the second date.
- **Context:** Brazilian e-commerce, 2016–2018. The *methods* transfer to other marketplaces, but the absolute numbers do not.

---

## 7. Architecture

```text
data/raw (CSV from Kaggle)
      │  src/check_data.py    → files complete? row counts, keys, date ranges
      │  src/profile_data.py  → profile per column (docs/data_profile.md)
      │  src/clean.py         → types, hidden missing values, data-quality flags
      ▼
data/processed (cleaned Parquet, raw files never changed)
      │  src/warehouse.py     → runs the SQL below and validates grain and GMV
      ▼
DuckDB (database/warehouse.duckdb)
      │  sql/warehouse/       → staging → dimensions → facts
      │                         (fct_leads, fct_order_items, fct_orders, fct_seller_activation)
      │  sql/marts/           → KPI layer (mart_kpi_summary, mart_gtm_monthly,
      │                         mart_channel_performance)
      ▼
┌───────────────────────────┬──────────────────────────────┬──────────────────────────────┐
│ analysis/                 │ app/ (Streamlit)             │ src/weekly_report.py         │
│ evidence per question     │ dashboard in EN / DE / FA    │ GTM report in EN / DE / FA   │
│ → reports/analysis/       │ texts: src/i18n/             │ + optional AI summary        │
│ → data/results/           │                              │ → reports/weekly/            │
└───────────────────────────┴──────────────────────────────┴──────────────────────────────┘
```

KPI definitions in English and German: [docs/kpi_definitions.md](docs/kpi_definitions.md).

**Stack:** Python (pandas, scipy, statsmodels), DuckDB (SQL), Streamlit + Plotly.

---

## 8. Dashboard pages

Start with `streamlit run app\Home.py`. Language selector in the sidebar: **English** and **Deutsch**. Persian (فارسی / دری, right to left) is included as an extra. In German and Persian, every KPI's help text also shows the English term.

1. **GTM overview:** 7 KPI tiles with numerator and denominator, leads and 60-day win rate by month (untracked months greyed out)
2. **Marketing & channels:** tracking gap, win rate per channel with 95 % confidence interval, activated sellers per 1,000 leads, landing pages against their channel mix (naive vs. corrected test)
3. **Sellers & cohorts:** activation within 30 / 60 / 90 days, activation and GMV share by lead type, buyer retention heatmap
4. **Experiments:** sample size and duration calculator (defaults from the real lead volume), evaluation of a finished A/B test with a decision rule
5. **Recommendations:** the nine findings, filterable by team
6. **Data quality:** every known gap with records affected and the KPIs it affects
7. **EventPro simulation (SYNTHETIC):** what Olist cannot show: SEO/GEO channel mix (AI answers as their own channel), cost per booking, a tracking-incident check, enterprise win/loss by industry with confidence intervals, win rate by response time, loss reasons. A warning banner on top makes clear that every number is simulated (section 11).
8. **Ask the data:** questions about the numbers, answered by a free local AI model (Ollama, model `gemma3:4b`). It gets only the calculated facts, and every answer is labelled as AI-generated. Setup once: `winget install Ollama.Ollama`, then `ollama pull gemma3:4b`.

Most pages end with a **"So what?"** box. Rules behind the dashboard: it opens the warehouse read-only with a short connection per query (so `src\warehouse.py` can run while it is open; use "Reload data" afterwards), it calculates no KPI itself, and all display text lives in `src/i18n/translations.json`.

---

## 9. Findings & recommendations

Ordered by priority: the first finding affects how reliable all the others are. All rates are from fair populations (2018 lead cohorts, sellers with a full 90-day window). The evidence for each row is in [reports/analysis/](reports/analysis/). Without marketing spend we cannot calculate CAC or ROI, so no row promises a money amount.

| # | Finding | Evidence | Recommendation | Owner | Expected impact | How we measure | Confidence |
|---|---|---|---|---|---|---|---|
| 1 | **A quarter of all wins cannot be credited to a channel**, and most of the gap comes from one landing page | Untracked leads: 14.4 % of leads, but 25.2 % of 60-day wins (win rate 18.6 % vs 9.3 %). 62 % of them arrive via page `b76ef374`. Channel win rates move by up to 3 points depending on the assumption (4.1, 4.3, 4.4) | Fix source tracking on `b76ef374` first (UTM and referrer passed into the lead form), then make the channel a required field. Until then, no budget shifts between organic and paid search | Marketing Ops + Data Engineering | Most of the gap closed with one fix. Channel decisions based on the full funnel | `attributed_share` per month in `mart_gtm_monthly` | High |
| 2 | **Trend reports can show changes that never happened** | Naive 2017 → 2018: 21× "improvement". Fair comparison (Jan–Feb vs Mar–Apr 2018): +0.9 points. Activation drops to 0 % for sellers won after May 2018 only because the data ends (4.4) | Start all trend charts in Jan 2018. Show months without complete tracking or without a full 90-day window greyed out. Every before/after comparison starts with a coverage check | Analytics (dashboard) + CPO | No false success or false alarm in management reporting | Dashboard uses `deal_tracking_complete` and `has_full_90d_window` everywhere | High |
| 3 | **Social brings volume, not sellers** | 1,051 leads, win rate 4.7 % (CI 4–6 %), 22 activated sellers per 1,000 leads vs 57–69 for search. Stays lowest in all attribution scenarios. The social landing pages perform exactly as expected for the channel (4.1, 4.3, 4.4) | Review social targeting and spend together with the cost data. Do not redesign the social landing pages: the page is not the problem | Marketing | Budget moves to channels with about 3× more activated sellers per lead | Activated sellers per 1,000 leads by channel | Medium (no cost data) |
| 4 | **Lead type and business type predict who will actually sell** | Activation: `online_big` 72 %, `offline` 34 %, `industry` 37 %. Holds in the regression (odds ratio `offline` 0.36, manufacturer 0.58). `online_big` = 15 % of sellers but 47 % of 90-day GMV; `offline` = 12 % of sellers, 2 % of GMV (4.2) | Sales: count activated sellers in targets, not only signed ones, and use lead type for prioritisation. Product: onboarding support for offline, industry and manufacturer sellers. Do not reject these leads: the model explains little (pseudo R² 0.06) | Sales + Product | More signed sellers who really sell. Less effort spent on deals that never activate | `seller_activation_rate_full_window` per lead type, new cohorts vs. earlier cohorts | High (pattern), Medium (effect of the action) |
| 5 | **Deals that take long to close activate less** | Closed after more than 30 days: 43 % activation vs 56 % within a week (odds ratio 0.59, p = 0.02) (4.2) | Flag deals with a sales cycle over 30 days for an onboarding check-in in the first weeks | Sales + Product | Earlier help for hesitant sellers | Activation of flagged deals vs. earlier comparable deals | Medium |
| 6 | **Two landing pages clearly beat their channel, one is clearly worse** | After channel adjustment and Benjamini-Hochberg correction, 3 of 18 pages differ (naive test: 8). `22c29808` +8.2 points, `40dec9f3` +6.8 points, `e492ee5e` −6.1 points (about 13 wins below expectation in 2018, upper bound) (4.3) | Find out what the two strong pages do differently and apply it to `e492ee5e` without an A/B test: at about 40 leads a month, even a test on form completion would take more than a year (5.2). Test single elements on high-traffic pages instead. Risk: without a control group, a later change can also come from season or channel mix | Marketing / Content + Product | Better conversion on an organic page with ~40 leads per month | Win rate of `e492ee5e` against its channel expectation, from the next cohorts on | Medium |
| 7 | **Paid search does not convert better than organic search** | Win rate 11.6 % vs 11.5 % (p = 0.95). Activation 60 % vs 49 %, but p = 0.049 in an exploratory test and the ranking flips under attribution scenarios (4.1, 4.4) | Do not shift budget on "conversion". Re-check activation by channel after the tracking fix (#1) with new cohorts | Marketing | Avoids a budget decision based on noise | Activation by channel, new cohorts | Low |
| 8 | **The data does not support a ranking of sales reps** | Raw activation per rep: 38–59 %. After adjusting for the lead mix: no difference (p = 0.47); no rep outside their interval (4.2) | Do not use raw activation per rep in performance reviews. If needed, report observed vs. expected for the lead mix | Sales leadership | Fair reviews; no blame for lead mix or chance | – | High |
| 9 | **The behaviour profile does not predict activation** | `cat`, `eagle`, `wolf`, `shark`: no difference (p = 0.57) (4.2) | Ask Sales how much time the field costs. If it is used only for this purpose, stop maintaining it | Sales | Time saved in each deal | – | Medium |

---

## 10. How to run (Windows)

**One command** (after the CSVs are in `data\raw\`): `.\run.ps1` creates `.venv` if needed, installs the requirements and runs every step below in order. It stops at the first failing step and tells you where to continue (`.\run.ps1 --from warehouse`). `.\run.ps1 --dry-run` only lists the steps.

Step by step:

```powershell
git clone https://github.com/walidsharaar/python_projects.git
cd "python_projects\044_Olis Market Insights"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1. Download both Olist datasets from Kaggle and unzip all CSVs into data\raw\
# 2. Check, profile and clean the data
python src\check_data.py
python src\profile_data.py
python src\clean.py
# 3. Build the DuckDB warehouse and KPI layer (stops if a validation fails)
python src\warehouse.py
# 4. Run the analyses (evidence goes to reports\analysis\)
python analysis\01_channel_quality.py
python analysis\02_win_vs_activation.py
python analysis\03_landing_pages.py
python analysis\04_tracking_data_quality.py
python analysis\05_cohorts.py
python analysis\06_experiments.py
# 4b. SIMULATED EventPro data + analysis (no Kaggle data needed, clearly labelled)
python src\simulate.py
python analysis\07_simulated_eventpro.py
# 5. Dashboard (English, German, Persian)
streamlit run app\Home.py
# 6. GTM report as Markdown in reports\weekly\ (add --ai for an optional AI summary;
#    that needs "pip install anthropic" and an API key, the report is complete without it)
python src\weekly_report.py
# 7. Tests: translations, every dashboard page in every language, the report
python -m unittest discover tests
```

---

## 11. Transfer to an event-booking marketplace

The data is from Olist, but the structure is the same for any B2B marketplace that books locations or services: win providers, get them to a first booking, and bring companies back. [docs/transfer_to_event_marketplace.md](docs/transfer_to_event_marketplace.md) shows how each method maps (seller → location, order → booking), which KPIs an event business adds (inquiry-to-offer, provider response time, repeat booking within 12 months), what a real enterprise win/loss analysis needs from the CRM, and how to measure SEO and GEO.

### Simulated demonstration (synthetic data, not Olist, not any real company)

Olist has no web traffic, no marketing spend, no lost deals and no customer industries. To show the methods for exactly these questions, `src/simulate.py` generates a **clearly labelled synthetic** event marketplace ("EventPro", Jan 2024 – Dec 2025, fixed seed). It lives in its own folder (`data/simulated/`), its own database (`database/simulation.duckdb`, every table `sim_…`) and its own dashboard page with a warning banner. It never mixes with the Olist numbers. The data has a **planned story**, and `analysis/07_simulated_eventpro.py` has to find it again; that is how the method is tested. Details: [docs/simulation.md](docs/simulation.md), evidence: [reports/analysis/07_simulated_eventpro.md](reports/analysis/07_simulated_eventpro.md).

What the analysis finds in the simulated data:

- **GEO:** AI answers bring 3.6 % of sessions but 8.6 % of bookings (2.9× the bookings per session of organic search). Organic search sessions −7.8 % vs 2024.
- **Tracking check:** a simple rule (weekly share below half of the last 8 weeks' median) finds exactly the three planted incident weeks in June 2025, when AI traffic was recorded as "direct".
- **Win/loss:** only Pharma (30.8 %) and IT (28.5 %) are clearly above the average of 23.3 %, only Automotive (16.3 %) clearly below; the rest overlap and are not ranked. A first answer after more than 24 h goes with lower odds of winning (odds ratio 0.39, with industry, size and event type held constant), which is an association, not proof.
- **Loss reasons:** Automotive loses on price in 43 % of lost deals vs 24 % elsewhere; 6.3 % of lost deals have no reason recorded.
- **Before/after with a comparison group:** Automotive fell from 19.2 % to 4.5 % for deals created from July 2025, while the other industries stayed flat (+0.3 points). Difference-in-differences: −14.9 points, interaction odds ratio 0.20, p = 0.035. The direction is confirmed; the size is uncertain (only 44 decided deals after July).

---

## 12. How I worked with a coding agent

I built this project together with an AI coding agent (Claude), in small phases with a review after each one.

- **My part:** the business questions, the "validity check" column, the KPI definitions, the phase plan and the rules: raw data is never changed, every rate shows numerator and denominator, no number appears in a document unless a script measured it, and the AI summary in the report only describes pre-computed numbers.
- **The agent's part:** most of the Python and SQL code, written phase by phase.
- **Review:** after each phase I ran the code, compared the numbers across scripts, marts and README, and only then approved the next phase. Example: the all-months win rate (8.1 %) disagreed with the README findings, which led to the decision to report `lead_to_win_rate_60d_tracked` everywhere (decision log in [docs/kpi_definitions.md](docs/kpi_definitions.md)).

---

## 13. Project status

- [x] Step 1: Setup, data download, data audit, business questions
- [x] Step 2: Profiling & cleaning
- [x] Step 3: Data model (DuckDB) & KPI layer
- [x] Step 4: Funnel, channel, segment & win/loss analysis, findings & recommendations
- [x] Step 5: Cohorts & experiment module
- [x] Step 6: Streamlit dashboard in English, German and Persian (Farsi/Dari)
- [x] Step 7: Automated GTM report in three languages with optional AI summary
- [x] Step 8: One-command run (`run.ps1` / `run_all.py`), README consistency check, transfer to an event marketplace
- [x] Step 9: Simulated EventPro demonstration (SEO/GEO, channel cost, enterprise win/loss), clearly labelled and tested

---

## Data source & licence

- [Marketing Funnel by Olist](https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist)
- [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

Both are licensed **CC BY-NC-SA 4.0**. The raw data is not included in this repository; download it from Kaggle.

## Author

**Walid Sharaar**, Data Analyst / BI Engineer, Hamburg
[LinkedIn](https://www.linkedin.com/in/walidsharaar/) · [GitHub](https://github.com/walidsharaar)
