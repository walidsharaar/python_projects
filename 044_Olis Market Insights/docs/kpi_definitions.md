# KPI definitions / KPI-Definitionen

One definition per KPI. The numbers live in the table `mart_kpi_summary` (built by `sql/marts/30_mart_kpi_summary.sql`). This file explains what they mean. It deliberately contains no values, so it can never be out of date.

Eine Definition pro KPI. Die Zahlen stehen in der Tabelle `mart_kpi_summary`. Diese Datei erklärt, was sie bedeuten, und enthält bewusst keine Werte.

| kpi_key | English | Deutsch | Numerator / Zähler | Denominator / Nenner | Owner | Watch out / Achtung |
|---|---|---|---|---|---|---|
| `mql_count` | MQLs | MQLs (qualifizierte Leads) | Leads in `fct_leads` | – | Marketing | Counts volume, not quality |
| `lead_to_win_rate` | Lead-to-win rate (ever) | Lead-to-Win-Rate (gesamt) | Won leads | All leads | Sales | Recent leads had less time to close. Do not use for trends |
| `lead_to_win_rate_60d` | Lead-to-win rate (60 days) | Lead-to-Win-Rate (60 Tage) | Leads won within 0–60 days of first contact | All leads | Sales | Deals are only recorded from 5 Dec 2017. Compare only months with `deal_tracking_complete` |
| `lead_to_win_rate_60d_tracked` | Lead-to-win rate (60 days, tracked months) | Lead-to-Win-Rate (60 Tage, erfasste Monate) | Leads won within 0–60 days, only months with `deal_tracking_complete` | All leads of those months | Sales | **The headline number for dashboards.** Fair, because every month in it was fully tracked |
| `sales_cycle_median_days` | Sales cycle (median) | Verkaufszyklus (Median) | Won deals, without the 1 negative cycle | – | Sales | Median, because the mean is pulled up by a few long deals |
| `seller_activation_rate` | Seller activation rate | Aktivierungsrate der Verkäufer | Won sellers with ≥ 1 non-canceled order | All won sellers | Product / Sales | Mixes sellers with and without a full 90-day window |
| `seller_activation_rate_full_window` | Seller activation rate (full window) | Aktivierungsrate (volles Zeitfenster) | Activated sellers won ≥ 90 days before data end | Sellers won ≥ 90 days before data end | Product / Sales | Use this one for comparisons |
| `time_to_first_sale_median_days` | Time to first sale (median) | Zeit bis zum ersten Verkauf (Median) | Activated sellers | – | Product | Only sellers who sold; the others have no value |
| `gmv_90d_per_won_seller` | 90-day GMV per won seller | GMV in 90 Tagen pro gewonnenem Verkäufer | Sum of item prices in the first 90 days, non-canceled | Won sellers with full window, incl. sellers with 0 | Product | GMV is not revenue. Very concentrated: a few sellers drive the average |
| `buyer_repeat_rate` | Buyer repeat rate | Wiederkaufrate | Customers (`customer_unique_id`) with ≥ 2 non-canceled orders | Customers with ≥ 1 non-canceled order | Product / CRM | Never use `customer_id`: it is new for every order |

## Decisions / Entscheidungen

| Date | Decision | Reason |
|---|---|---|
| 2026-11-18 | Activation and repeat rate exclude `canceled` orders only | `unavailable` orders have no items, so excluding them changes nothing (45.01 % both ways) |
| 2026-11-18 | Customers with only canceled orders are not counted as buyers | They never bought anything. Same logic as activation |
| 2026-11-18 | 90-day KPIs use sellers with `has_full_90d_window` only | Late sellers activate at 20 % vs. 51 % only because they had less time |

## Not measurable with this data / Mit diesen Daten nicht messbar

CAC, CPL, ROAS and marketing ROI need marketing spend per channel. Revenue and take rate need commission data. Real loss reasons need CRM fields. Search-to-quote and SEO performance need web tracking (GA4, Search Console).
