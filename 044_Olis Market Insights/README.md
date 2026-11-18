# Marketplace GTM Analytics: From Lead to Active Seller

> End-to-end Go-to-Market analysis of a **two-sided B2B marketplace**: from the first marketing touchpoint, through the sales close, to the seller's first revenue.
> Built with Python, DuckDB/SQL and Streamlit on **real** marketplace data (Olist, Brazil, 2016–2018).

*Deutsche Version: [README.de.md](README.de.md)*

---

## 1. Business context

Olist is a marketplace that connects small and mid-sized merchants (sellers) with large Brazilian e-commerce channels. To grow, it has to:

1. **Acquire sellers** (supply side): marketing generates leads (MQLs), and sales reps (SDRs/SRs) convert them into closed deals.
2. **Activate sellers**: a closed deal only creates value once the seller actually starts selling.
3. **Serve buyers** (demand side): customers place orders and, ideally, come back.

This is the typical GTM problem of any B2B marketplace: **Marketing, Sales and Product each own one part of the funnel, but growth depends on the whole chain.** This project builds one shared, trusted data foundation across all three.

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
| Q3 | **Tracking & data quality** | How much of the funnel is unattributed, and does it distort channel decisions? | Share of `unknown`/missing origin, conversion comparison | 14.5% of leads have no usable origin, and they convert *above* average |
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

Headline numbers (from the initial data audit):

- **Lead-to-win conversion:** 842 / 8,000 = **10.5%**
- **Median sales cycle:** 14 days (mean 48, so a long tail)
- **Seller activation:** only **45%** of won sellers ever make a sale (51% for sellers with a full 90-day window)
- **Median time from close to first sale:** 44 days
- **GMV concentration:** the top 10% of new sellers generate **83%** of the GMV of all new sellers in their first 90 days
- **Buyer repeat rate:** only **3.1%** of customers order more than once

---

## 4. Preliminary observations (hypotheses to test)

These come from the initial data audit. They are **hypotheses**, not conclusions, and each will be confirmed or rejected in the analysis.

**H1: The 2017 → 2018 "conversion jump" is most likely a tracking artifact, not a success.**
Leads from 2017 show a 60-day conversion of **0.5%**, while leads from 2018 show **10.6%**. But the first `won_date` in the data is **5 Dec 2017**, so closed deals were probably only recorded from then on. A naive before/after comparison would celebrate a 20× improvement that never happened.
→ *Implication: before/after analyses need a data-coverage check first. Valid comparisons use 2018 cohorts only.*

**H2: Unattributed leads are high-intent leads, so tracking loss distorts channel decisions.**
`unknown` + missing origin = 1,159 leads (14.5%), converting at about **16–23%**, against 11.8% for organic search.
→ *Implication: fix attribution first (UTM parameters, landing-page tracking). Otherwise budget is shifted on incomplete data.*

**H3: Channels differ massively in quality, not just volume.**
Paid search (12.3%) and organic search (11.8%) convert similarly, while email (3.0%) and social (5.6%) convert at a fraction of that, although social delivers 1,350 leads.

**H4: A "won" deal is not a success: lead type predicts activation.**
`online_big` leads activate at **63%** (mean 90-day GMV ≈ 1,490 BRL), while `offline` leads activate at **29%** (≈ 80 BRL) and `industry` leads at 33%.
→ *Implication for sales enablement: qualify on activation likelihood, not only on closing likelihood.*

**H5: A few landing pages carry the funnel.**
The two largest landing pages (about 900 leads each) convert at about **19–20%**, while other high-traffic pages convert at 3–7%.

**H6: Classical A/B tests on lead-to-win are too slow at this volume.**
To detect an uplift from 12% to 14% (α = 0.05, power = 80%) we need about **4,400 leads per variant**. At about 1,200 MQLs per month that takes **7+ months**.
→ *Implication: test on faster upper-funnel metrics (MQL rate, SDR contact rate), use a sequential design, or use before/after with a control group (difference-in-differences).*

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
| Buyer repeat rate | Customers (`customer_unique_id`) with ≥ 2 orders ÷ all customers | Demand-side loyalty |

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

## 8. The executive screen

One screen, built like a story: **what is the problem → why → what do we do → how will we know.** Start it with `streamlit run app\Home.py`. Language selector in the sidebar: **English, Deutsch, فارسی / دری** (Persian runs right to left).

1. **Headline:** one sentence with live numbers: "Of every 1,000 new leads, about 106 sign a contract and about 55 start selling."
2. **Five KPIs**, each with *how it is calculated* written under the number:

   | KPI | How it is calculated | Why it matters |
   |---|---|---|
   | New leads per month | new leads in fully tracked months ÷ number of months | Volume coming from Marketing |
   | Contract rate (60 days) | leads that signed within 60 days ÷ all leads | Does Sales turn leads into contracts? |
   | Seller activation rate | signed sellers with at least one order ÷ all signed sellers | A contract only has value if the seller sells |
   | Time to first sale (median) | middle value of the days from contract to first order | How fast onboarding works |
   | Contracts without a known channel | contracts from leads without a channel ÷ all contracts | Can we trust the channel numbers? |

3. **Funnel:** what happens to 1,000 new leads.
4. **Three tabs.** *For executives:* the four main KPIs, the funnel, and the actions ranked by what is at stake (e.g. "+37 active sellers if social leads converted like search leads"), each with owner and success measure (`mart_opportunities`). *For marketing:* a channel scorecard with a verdict per channel (Grow / Watch / Review spend / Fix tracking / Too little data, with the rule written under the table, `mart_channel_scorecard`), and three landing page actions. *Ask the data:* the local AI.
5. **Ask the data:** a free, local AI model (Ollama) answers questions using only the numbers on the screen.
6. **Glossary:** every technical word (MQL, GMV, median, confidence interval, p-value, cohort, A/B test …) in one plain sentence.

Rules behind it: the screen opens the warehouse read-only, calculates no KPI itself (all numbers come from `sql/marts/`), and all texts live in `src/i18n/translations.json`.

### How the screen answers the job description

| On the screen | What the job asks for |
|---|---|
| KPIs and funnel | "Du überwachst laufend unsere GTM-Performance … von Funnel-Analysen über Kanal-Performance bis zu Conversion-Raten" |
| 1. Which channels bring sellers who really sell? | "Kanal-Performance", "Traffic-Kanäle optimieren" |
| 2. Who starts selling after signing? | "Cohort- und Funnel-Analysen über Kundensegmente", "Win/Loss-Analysen … für unser Sales Enablement" |
| 3. Is something changing right now? | "Mit Vorher-/Nachher-Vergleichen misst Du, ob Maßnahmen wirklich wirken" |
| 4. Can we trust the numbers? | "eine gemeinsame Datenbasis, auf die sich alle verlassen können" |
| Story cards | "immer mit konkreten Handlungsempfehlungen statt reinen Reports" |
| Ask the data and the GTM report | "KI- und automatisierungsgestützte Reporting-Infrastruktur" |
| A/B test planning (analysis 06) | "Hypothesen … in Experimente und A/B-Tests übersetzen" |

### Ask the data: setup (once, free)

```powershell
winget install Ollama.Ollama
ollama pull gemma3:4b
```

Ollama then runs in the background. The model runs on the laptop, so no data leaves it and no API key is needed. Another model can be set with the environment variable `OLLAMA_MODEL`. Without Ollama, the screen shows these instructions instead of the question box.

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
# 5. Executive screen (English, German, Persian)
streamlit run app\Home.py
# 6. GTM report as Markdown in reports\weekly\ (add --ai for an optional AI summary;
#    that needs "pip install anthropic" and an API key, the report is complete without it)
python src\weekly_report.py
# 7. Tests: translations, the executive screen in every language, the report
python -m unittest discover tests
```

---

## 11. Project status

- [x] Step 1: Setup, data download, data audit, business questions
- [x] Step 2: Profiling & cleaning
- [x] Step 3: Data model (DuckDB) & KPI layer
- [x] Step 4: Funnel, channel, segment & win/loss analysis, findings & recommendations
- [x] Step 5: Cohorts & experiment module
- [x] Step 6: Streamlit dashboard in English, German and Persian (Farsi/Dari)
- [x] Step 7: Automated GTM report in three languages with optional AI summary

---

## Data source & licence

- [Marketing Funnel by Olist](https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist)
- [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

Both are licensed **CC BY-NC-SA 4.0**. The raw data is not included in this repository; download it from Kaggle.

## Author

**Walid Sharaar**, Data Analyst / BI Engineer, Hamburg
[LinkedIn](https://www.linkedin.com/in/walidsharaar/) · [GitHub](https://github.com/walidsharaar)
