# Marketplace GTM Analytics: From Lead to Active Seller

> End-to-end Go-to-Market analysis of a **two-sided B2B marketplace**: from the first marketing touchpoint, through the sales close, to the seller's first revenue.
> Built with Python, DuckDB/SQL and Streamlit on **real** marketplace data (Olist, Brazil, 2016–2018).

*Deutsche Version: [README.md](README.md)*

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
| Q9 | **Marketplace activation** | How many won sellers make a first sale, how fast, and what predicts it? | Activation rate, time-to-first-sale, 90-day GMV | Order data ends Oct 2018, so only deals won before Jul 2018 get a full 90-day window |
| Q10 | **Demand-side retention** | Do buyers come back? How does repeat-purchase behaviour look across cohorts? | Customer cohort retention matrix | Uses `customer_unique_id` (not `customer_id`, which is per order) |
| Q11 | **Automated reporting** | Can the weekly GTM report build itself, so analyst time goes into recommendations? | Scripted KPI pipeline + LLM-generated summary of anomalies, reviewed by a human | The AI summary only describes pre-computed numbers and never computes them itself |

---

## 3. Data at a glance

Source: Kaggle, *Marketing Funnel by Olist* + *Brazilian E-Commerce Public Dataset by Olist*.

| Table | Rows | Period | Used for |
|---|---|---|---|
| Marketing qualified leads | 8,000 | Jun 2017 – May 2018 (first contact) | Q1–Q3, Q5–Q8 |
| Closed deals | 842 | Dec 2017 – Nov 2018 (won date) | Q1, Q4, Q6, Q9 |
| Orders | 99,441 | Sep 2016 – Oct 2018 | Q9, Q10 |
| Order items, sellers, customers, products, payments, reviews | — | — | Q9, Q10 |

Headline numbers (from the initial data audit):

- **Lead-to-win conversion:** 842 / 8,000 = **10.5%**
- **Median sales cycle:** 14 days (mean 48, so a long tail)
- **Seller activation:** only **45%** of won sellers ever make a sale (51% for deals won before Jul 2018)
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
- **Context:** Brazilian e-commerce, 2016–2018. The *methods* transfer to other marketplaces, but the absolute numbers do not.

---

## 7. Architecture

```text
data/raw (CSV from Kaggle)
      │  src/ingest.py        → load + schema checks
      ▼
data/processed (cleaned parquet)
      │  src/clean.py         → types, dedup, outliers, data-quality flags
      ▼
DuckDB (warehouse.duckdb)
      │  sql/                 → staging → marts (fct_leads, fct_sellers, fct_orders)
      ▼
┌───────────────────────────┬──────────────────────────────┐
│ app/ (Streamlit)          │ src/weekly_report.py         │
│ interactive dashboard     │ automated KPI report         │
│                           │ + AI summary (human-reviewed)│
└───────────────────────────┴──────────────────────────────┘
```

**Stack:** Python (pandas, scipy, statsmodels), DuckDB (SQL), Streamlit + Plotly.

---

## 8. Dashboard pages

1. **GTM overview:** KPI tiles, monthly funnel, trend vs. previous period
2. **Channels & attribution:** conversion, activation and GMV per channel, with confidence intervals
3. **Segments & win/loss:** segment benchmarks, drivers of winning and activation
4. **Cohorts:** lead cohorts (60-day conversion) and buyer retention matrix
5. **Experiments:** sample-size calculator + A/B test evaluation (simulated)
6. **Recommendations:** the top actions, each with evidence and expected impact

Every page ends with a **"So what?"** box: the recommendation, the evidence, and the confidence level.

---

## 9. Findings & recommendations

*To be completed after the analysis. Format for each finding:*

| Finding | Evidence | Recommendation | Owner | Expected impact | Confidence |
|---|---|---|---|---|---|
| … | … | … | Marketing / Sales / Product | … | High / Medium / Low |

---

## 10. How to run (Windows)

```powershell
git clone https://github.com/walidsharaar/python_projects.git
cd "python_projects\044_Olis Market Insights"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1. Download both Olist datasets from Kaggle and unzip all CSVs into data\raw\
# 2. Check the download
python src\check_data.py
```

Further scripts (pipeline, dashboard) are added step by step, see project status.

---

## 11. Project status

- [x] Step 1: Setup, data download, data audit, business questions
- [ ] Step 2: Profiling & cleaning
- [ ] Step 3: Data model (DuckDB) & KPI layer
- [ ] Step 4: Funnel, channel, segment & win/loss analysis
- [ ] Step 5: Cohorts & experiment module
- [ ] Step 6: Streamlit dashboard
- [ ] Step 7: Automated weekly report with AI summary

---

## Data source & licence

- [Marketing Funnel by Olist](https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist)
- [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

Both are licensed **CC BY-NC-SA 4.0**. The raw data is not included in this repository; download it from Kaggle.

## Author

**Walid Sharaar**, Data Analyst / BI Engineer, Hamburg
[LinkedIn](https://www.linkedin.com/in/walidsharaar/) · [GitHub](https://github.com/walidsharaar)
