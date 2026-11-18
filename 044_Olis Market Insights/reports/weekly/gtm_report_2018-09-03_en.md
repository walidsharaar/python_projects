# GTM report: 3 Sep 2018

_Created automatically on 18 Nov 2026 from the KPI layer (database/warehouse.duckdb). Data: real public data from Olist, effective data end 3 Sep 2018._

## 1. Main KPIs

| KPI | Value | Basis |
|---|---|---|
| MQLs | 8,000 |  |
| Lead-to-win rate (60 days) | 10.6% | 636 of 5,998 |
| Sales cycle (median) | 14 days | n = 841 |
| Wins without a channel | 25.2% | 160 of 636 |
| Seller activation rate | 51.4% | 345 of 671 |
| Time to first sale (median) | 44 days | n = 379 |
| 90-day GMV per won seller | 507 BRL | n = 671 |
| Buyer repeat rate | 3.1% | 2,924 of 95,560 |

## 2. Latest month compared with earlier months

Only lead months with complete deal tracking. The latest month is compared with all earlier tracked months together, with a two-proportion test.

- Leads in May 2018: 1,303 (−3.6% compared with the month before).
- 60-day win rate in May 2018: 7.8%. Earlier tracked months together: 11.4% (p = 0.000).

> Clear change: the difference is unlikely to be chance. Check first whether it is real (tracking, channel mix, a new landing page) before acting on it.

## 3. Data quality warnings

Known gaps that affect at least 5% of their records. All numbers in this report already take them into account.

- Deals without declared revenue (0 in the source): 797 of 842 (94.7%). Affects: Any lead scoring based on revenue.
- Leads from months without deal tracking: 2,002 of 8,000 (25.0%). Affects: Monthly trends of the win rate.
- Won deals without behaviour profile: 177 of 842 (21.0%). Affects: Behaviour analysis.
- Sellers without a full 90-day window: 171 of 842 (20.3%). Affects: Activation and 90-day GMV.
- Leads without a channel: 1,159 of 8,000 (14.5%). Affects: Channel comparison.

## 4. Recommended actions (top 3)

1. **A quarter of all wins cannot be credited to a channel.** Fix the source tracking on landing page b76ef374 first, then make the channel a required field. Until then, do not move budget between organic and paid search. _How we measure it: Share of leads without a channel, per month._
2. **Trend reports can show changes that never happened.** Start trend charts with the first fully tracked month, grey out months without complete tracking or without a full 90-day window, and start every before/after comparison with a coverage check. _How we measure it: Every trend chart uses the tracking and window flags._
3. **Social brings volume, not sellers.** Review social targeting and spend together with the cost data. Do not redesign the social landing pages: they perform as expected for their channel. _How we measure it: Activated sellers per 1,000 leads by channel._

## 5. Summary (AI draft, to be reviewed by a person)

No AI summary. Run with --ai to add one (needs the anthropic package and an API key).

---

_Definitions of every KPI: docs/kpi_definitions.md. Evidence for the actions: README section 9 and reports/analysis._
