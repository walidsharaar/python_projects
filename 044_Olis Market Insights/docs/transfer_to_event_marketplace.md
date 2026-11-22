# From Olist to an event-booking marketplace / Von Olist auf einen Event-Marktplatz

This project uses real Olist data. This page shows how the same methods would work for a B2B event-booking marketplace, where companies book locations for Christmas parties, trainings or meetings. Everything about the event business here is an **assumption for illustration**, not knowledge of any real company's data.

*Deutsche Version: siehe unten.*

---

## 1. Same structure, different product

| Olist (this project) | Event-booking marketplace | Same method |
|---|---|---|
| Seller (merchant) | Location / event provider | Supply-side acquisition funnel |
| MQL → closed deal | Provider lead → signed contract | Lead-to-win rate, 60-day window |
| First non-canceled order | First confirmed booking | Activation rate, time to first sale |
| 90-day GMV per seller | Booking value in the first 90 days per location | Value per acquired provider |
| Buyer (`customer_unique_id`) | Booking company | Repeat booking rate, cohorts |
| Lead type (`online_big`, `offline`) | Location type (hotel, restaurant, conference centre) | Activation by segment |
| Business segment | Customer industry (Pharma, Automotive, IT) | Cohort and funnel by segment |
| Landing page | Landing page / city page / SEO page | Conversion with multiple-testing correction |

What does **not** transfer: the absolute numbers. A 51 % activation rate for Brazilian merchants says nothing about event locations.

## 2. KPIs the event business adds

| KPI | Formula | Why |
|---|---|---|
| Inquiry-to-offer rate | Inquiries with ≥ 1 offer ÷ inquiries | Shows whether supply answers demand |
| Offer-to-booking rate | Bookings ÷ inquiries with an offer | Core demand-side conversion |
| Provider response time (median) | Offer time − inquiry time | Slow answers lose bookings |
| Location activation (90 days) | New locations with ≥ 1 confirmed booking within 90 days ÷ new locations | Same logic as seller activation |
| Repeat booking rate (12 months) | Companies with ≥ 2 bookings in 12 months ÷ booking companies | B2B loyalty; events are seasonal, so 12 months, not 30 days |
| Cancellation rate | Cancelled bookings ÷ confirmed bookings | Guardrail for growth KPIs |

Seasonality matters more than at Olist: Christmas parties concentrate demand in Q4, so year-over-year comparisons must use the same weeks.

## 3. Win/loss for enterprise deals

Olist only records won deals, so this project can compare *wins that activate* with *wins that don't*. A real win/loss analysis needs CRM fields:

- every opportunity, including **lost** ones, with stage dates
- loss reason (structured list, not free text), competitor if known
- deal size, customer industry, company size, number of events per year
- sales rep and lead source

Method: win rate by segment with confidence intervals → logistic regression on win/loss → short interviews with lost customers to check the reasons. Output for Sales Enablement: which segments to prioritise, and which objections need better answers.

## 4. Measuring SEO and GEO

| Question | Data | KPI |
|---|---|---|
| Are we visible in search? | Google Search Console | Impressions, clicks, CTR, average position per page and query |
| Does search traffic convert? | GA4 (landing page + conversion event) | Inquiries per session by landing page |
| Are AI assistants sending traffic? (GEO) | GA4 referrer | Sessions and inquiries from AI referrers (e.g. chatgpt.com, perplexity.ai, gemini.google.com, copilot.microsoft.com) as their own channel |
| Are we mentioned in AI answers? | Fixed prompt list, checked regularly | Share of prompts where the brand or a location is named |
| Does new content work? | Content cohorts by publish month | Inquiries per page after 30 / 90 days |

Limit: some AI traffic arrives without a referrer and looks like direct traffic. This is the same tracking-gap problem as finding 1 in this project, so it needs the same treatment: measure the gap first, then decide.

## 5. Minimal tracking plan

| Event | Key properties |
|---|---|
| `search_performed` | city, date, guests, event type, channel |
| `location_viewed` | location_id, position in results |
| `inquiry_submitted` | inquiry_id, location_ids, company_id, budget, landing page, UTM |
| `offer_received` | inquiry_id, location_id, offer value, response time |
| `booking_confirmed` | booking_id, inquiry_id, value, company industry |
| `booking_cancelled` | booking_id, reason |

## 6. First 90 days with this playbook

1. **Weeks 1–4:** check tracking and attribution (how much of the funnel has no channel?), write down one definition per KPI.
2. **Weeks 5–8:** location activation and inquiry-to-booking funnel by segment and city.
3. **Weeks 9–12:** automated weekly GTM report with a Data Engineer, AI summary only on pre-computed numbers.

---

# Deutsch

Dieses Projekt nutzt echte Daten von Olist. Diese Seite zeigt, wie dieselben Methoden bei einem B2B-Marktplatz für Event-Buchungen funktionieren würden. Alles zum Event-Geschäft ist eine **Annahme zur Veranschaulichung**, kein Wissen über die Daten eines echten Unternehmens.

## 1. Gleiche Struktur, anderes Produkt

| Olist (dieses Projekt) | Event-Marktplatz | Gleiche Methode |
|---|---|---|
| Verkäufer | Location / Event-Anbieter | Funnel zur Gewinnung von Anbietern |
| MQL → Abschluss | Anbieter-Lead → unterschriebener Vertrag | Lead-to-Win-Rate, 60-Tage-Fenster |
| Erste nicht stornierte Bestellung | Erste bestätigte Buchung | Aktivierungsrate, Zeit bis zur ersten Buchung |
| 90-Tage-GMV pro Verkäufer | Buchungswert der ersten 90 Tage pro Location | Wert pro gewonnenem Anbieter |
| Käufer (`customer_unique_id`) | Buchendes Unternehmen | Wiederbuchungsrate, Kohorten |
| Lead-Typ | Location-Typ (Hotel, Restaurant, Tagungszentrum) | Aktivierung nach Segment |
| Segment | Branche des Kunden (Pharma, Automotive, IT) | Kohorten und Funnel nach Segment |
| Landingpage | Landingpage / Städteseite / SEO-Seite | Conversion mit Korrektur für multiples Testen |

Nicht übertragbar sind die absoluten Zahlen.

## 2. Zusätzliche KPIs im Event-Geschäft

- **Anfrage-zu-Angebot-Rate:** Anfragen mit mindestens einem Angebot ÷ alle Anfragen
- **Angebot-zu-Buchung-Rate:** Buchungen ÷ Anfragen mit Angebot
- **Antwortzeit der Anbieter (Median):** Zeit vom Eingang der Anfrage bis zum Angebot
- **Location-Aktivierung (90 Tage):** neue Locations mit mindestens einer Buchung in 90 Tagen ÷ neue Locations
- **Wiederbuchungsrate (12 Monate):** Unternehmen mit mindestens 2 Buchungen in 12 Monaten ÷ buchende Unternehmen
- **Stornoquote:** stornierte ÷ bestätigte Buchungen (Guardrail-KPI)

Saison ist wichtiger als bei Olist: Weihnachtsfeiern bündeln die Nachfrage im vierten Quartal. Vergleiche mit dem Vorjahr nur über dieselben Wochen.

## 3. Win/Loss bei Enterprise-Deals

Nötig sind CRM-Daten: alle Opportunities inklusive **verlorener**, Verlustgrund als feste Liste, Wettbewerber, Deal-Größe, Branche, Unternehmensgröße, Events pro Jahr, Vertriebsmitarbeiter, Lead-Quelle. Vorgehen: Win-Rate nach Segment mit Konfidenzintervall → logistische Regression → kurze Gespräche mit verlorenen Kunden. Ergebnis für Sales Enablement: welche Segmente Priorität haben und welche Einwände bessere Antworten brauchen.

## 4. SEO und GEO messen

- **Search Console:** Impressionen, Klicks, CTR, Position pro Seite und Suchbegriff
- **GA4:** Anfragen pro Sitzung nach Landingpage
- **GEO:** Traffic und Anfragen von KI-Assistenten (z. B. chatgpt.com, perplexity.ai) als eigener Kanal; regelmäßige Prüfung einer festen Prompt-Liste, ob die Marke genannt wird
- **Content-Kohorten:** Anfragen pro Seite nach 30 und 90 Tagen

Grenze: Ein Teil des KI-Traffics kommt ohne Referrer an und sieht aus wie Direktzugriff. Das ist dasselbe Problem wie Ergebnis 1 in diesem Projekt: erst die Lücke messen, dann entscheiden.

## 5. Die ersten 90 Tage

1. **Woche 1–4:** Tracking und Attribution prüfen, eine Definition pro KPI festlegen.
2. **Woche 5–8:** Location-Aktivierung und Funnel von der Anfrage bis zur Buchung nach Segment und Stadt.
3. **Woche 9–12:** automatischer wöchentlicher GTM-Report zusammen mit einem Data Engineer, KI-Zusammenfassung nur auf berechneten Zahlen.
