# Simulated EventPro data / Simulierte EventPro-Daten

> **SYNTHETIC DATA.** Nothing here is Olist data or data of any real company. It exists to show methods that the real Olist data cannot support.

## Why a simulation?

The Olist data is real, but it has no web traffic, no marketing spend, no lost deals and no customer industries. A GTM analyst in an event-booking marketplace needs exactly those: SEO/GEO and content, channel cost, enterprise win/loss, and segments such as Pharma vs. Automotive. The simulation shows how I would analyse them. It does **not** produce findings about any real business.

## Rules

| Rule | How it is enforced |
|---|---|
| Never mix with Olist | Own folder `data/simulated/`, own database `database/simulation.duckdb`, every table starts with `sim_` (tested in `tests/test_simulation.py`) |
| Always visible as synthetic | Warning banner on the dashboard page, "SYNTHETIC DATA" at the top of `reports/analysis/07_simulated_eventpro.md` (tested) |
| Reproducible | Fixed seed (`SEED = 2026`) set inside `main()`, fixed period 1 Jan 2024 – 31 Dec 2025 (tested) |
| A planned story, found again by the analysis | Parameters below; `src/simulate.py` stops if the story is not in the data |

## Sources (as if exported from real systems)

| File | Like | Grain | Rows |
|---|---|---|---|
| `web_traffic_daily.csv` | GA4 export | day × channel | 5,117 |
| `crm_opportunities.csv` | CRM export (e.g. HubSpot/Salesforce) | opportunity | 1,318 (294 won, 968 lost, 56 open) |

## Planned story (the "truth" in the generator)

| Topic | What was planted | What the analysis finds |
|---|---|---|
| GEO | AI referrals grow from 20 to 220 sessions per weekday; they convert better (4.5 % quote rate vs 2.0 % organic) | 3.6 % of sessions, 8.6 % of bookings; organic −7.8 % YoY |
| Paid vs social | Social: cheap clicks, few bookings | Cost per booking: paid search about 275 EUR, social about 543 EUR |
| Seasonality | Peak Sep–Nov (Christmas parties), low Jan, Jul, Aug, Dec | Visible in the monthly data; 2025 vs 2024 compares full years |
| Tracking incident | 2–22 Jun 2025: 80 % of AI sessions recorded as "direct" | The alarm rule finds exactly these 3 weeks |
| Industry | Pharma +0.5 on the win logit, longer cycle, larger deals | Pharma 30.8 % and IT 28.5 % clearly above the 23.3 % average (IT by chance: not planted), Automotive 16.3 % clearly below |
| Response time | > 24 h: −0.9 on the logit; 4–24 h: −0.3 | Odds ratio 0.39 for > 24 h in the regression |
| Loss reasons | Automotive: price ×2.2; Pharma: no suitable venue ×1.8; slow answers: slow response ×3.5 | Automotive loses on price in 43 % vs 24 % |
| Automotive H2 2025 | −1.1 on the logit for deals created from 1 Jul 2025 | Confirmed with difference-in-differences: −14.9 points vs the other industries, p = 0.035. Size uncertain (n = 44 after July) |
| Data defects | 4 % missing industry, 8 % of lost deals without a reason | Shown as "unknown" / "not recorded", never hidden |

## What this does not prove

It proves that the **pipeline and the statistics** find a known pattern. It also shows the limits: IT software lands above average by chance (nothing was planted there), which is why every ranking needs intervals. It says nothing about real conversion rates, real costs or real win rates in the event business.

---

## Deutsch (kurz)

**SIMULIERTE DATEN.** Olist hat keinen Web-Traffic, keine Marketingkosten, keine verlorenen Deals und keine Branchen. Die Simulation zeigt, wie ich genau diese Fragen analysieren würde: SEO/GEO, Kanalkosten, Win/Loss bei Enterprise-Deals und Segmente wie Pharma und Automotive.

- **Getrennt von Olist:** eigener Ordner, eigene Datenbank, jede Tabelle beginnt mit `sim_`.
- **Immer sichtbar markiert:** Warnhinweis im Dashboard und im Bericht.
- **Reproduzierbar:** fester Seed und fester Zeitraum (2024–2025).
- **Geplante Geschichte:** Die Analyse muss sie wiederfinden, z. B. den Rückgang bei Automotive ab Juli 2025 (Vorher/Nachher mit Vergleichsgruppe). IT liegt zufällig über dem Schnitt, obwohl dort nichts geplant war. Deshalb braucht jede Rangfolge Konfidenzintervalle.

Die Simulation beweist, dass Pipeline und Statistik funktionieren. Über echte Zahlen im Event-Geschäft sagt sie nichts.
