# Marketplace GTM Analytics: Vom Lead zum aktiven Verkäufer

> Eine Go-to-Market-Analyse für einen **zweiseitigen B2B-Marktplatz**: vom ersten Kontakt im Marketing über den Abschluss im Vertrieb bis zum ersten Umsatz des Verkäufers.
> Umgesetzt mit Python, DuckDB/SQL und Streamlit, auf Basis **echter** Marktplatzdaten (Olist, Brasilien, 2016–2018).

*English version: [README.md](README.md)*

**Worum geht es?** Ich schaue mir den ganzen GTM-Funnel eines Marktplatzes an: Welche Kanäle bringen gute Leads? Wo verlieren wir Kunden? Welche Segmente lohnen sich? Und wie testet man sauber, ob eine Maßnahme wirklich wirkt? Am Ende jeder Analyse steht eine konkrete **Handlungsempfehlung**. Ein reiner Report ohne Empfehlung hilft keinem Team weiter.

---

## 1. Der geschäftliche Hintergrund

Olist ist ein Marktplatz. Er verbindet kleine und mittlere Händler (Verkäufer) mit den großen E-Commerce-Plattformen in Brasilien. Um zu wachsen, muss Olist drei Dinge schaffen:

1. **Verkäufer gewinnen** (Angebotsseite): Das Marketing bringt Leads (MQLs), der Vertrieb (SDRs/SRs) macht daraus Abschlüsse.
2. **Verkäufer aktivieren**: Ein Abschluss ist erst dann etwas wert, wenn der Verkäufer auch wirklich verkauft.
3. **Käufer bedienen** (Nachfrageseite): Kunden bestellen und kommen im besten Fall wieder.

Das ist das typische Problem jedes B2B-Marktplatzes: **Marketing, Sales und Product sind jeweils nur für einen Teil des Funnels verantwortlich. Das Wachstum hängt aber von der ganzen Kette ab.** Dieses Projekt baut deshalb eine gemeinsame Datenbasis, auf die sich alle drei Teams verlassen können.

```text
Marketing                  Sales                      Product / Marktplatz
───────────────────────    ───────────────────────    ──────────────────────────────────
Kanal → Landingpage → MQL → SDR/SR → Abschluss → Erster Verkauf → GMV → Wiederkauf
  (origin)                          (won_date)    (Aktivierung)           (Retention)
```

---

## 2. Die Fragen an die Daten

Jede Frage gehört zu einer typischen Aufgabe im Bereich GTM & Insights. In der Spalte **„Was die Daten hergeben“** steht, was man mit diesen Daten sagen kann und was nicht. Diese Spalte habe ich *vor* der Analyse geschrieben, damit ich mir die Ergebnisse später nicht schönrede.

| # | Aufgabe | Frage | Methode | Was die Daten hergeben |
|---|---|---|---|---|
| Q1 | **GTM-Performance überwachen** | Wie viele Leads werden zu Abschlüssen, wie lange dauert ein Deal, und wie entwickelt sich das von Monat zu Monat? | KPI-Baum, monatlicher Funnel, festes 60-Tage-Fenster | Neue Kohorten hatten noch wenig Zeit zum Abschließen. Deshalb vergleiche ich feste Zeitfenster und nicht „irgendwann gewonnen“ |
| Q2 | **Kanal-Performance** | Welche Kanäle bringen Leads, die *abschließen*? Und welche bringen Verkäufer, die auch wirklich *verkaufen*? | Conversion, Aktivierung und 90-Tage-GMV pro Kanal, Wilson-Konfidenzintervalle | Kleine Kanäle (n < 100) zeige ich mit Intervall und nicht als Rangliste |
| Q3 | **Tracking & Datenqualität** | Bei wie vielen Leads fehlt die Herkunft, und verfälscht das unsere Kanal-Entscheidungen? | Anteil `unknown`/fehlend, Vergleich der Conversion | Bei 14,5 % der Leads ist die Herkunft unklar, und genau diese Leads schließen *überdurchschnittlich* oft ab |
| Q4 | **Segmente vergleichen** | Welche Segmente (z. B. `health_beauty` vs. `car_accessories`) schließen schneller ab, werden öfter aktiv und bringen mehr GMV? | Segment-Benchmark für gewonnene Deals | Das Segment kennen wir nur bei **gewonnenen** Deals. Verglichen wird also die *Qualität der Abschlüsse*, nicht die Conversion |
| Q5 | **Kohorten + Vorher/Nachher** | Ist die Conversion von 2017 auf 2018 wirklich gestiegen, oder liegt das nur an den Daten? | Monatliche Lead-Kohorten, feste Fenster, Prüfung der Datenabdeckung | Siehe H1: Ein einfacher Vorher-/Nachher-Vergleich führt hier in die Irre |
| Q6 | **Win/Loss für Sales Enablement** | Was unterscheidet Leads, die abschließen, von denen, die es nicht tun? Und gewonnene Verkäufer, die aktiv werden, von denen, die nie verkaufen? | Logistische Regression, Vergleich gewonnen vs. aktiviert (Lead-Typ, Geschäftstyp, Vertriebsmitarbeiter) | Es gibt keine Verlustgründe. „Verloren“ heißt hier: MQL ohne Abschluss |
| Q7 | **Wirkung von Content** | Welche Landingpages konvertieren am besten, und sind die Unterschiede statistisch belastbar? | Chi-Quadrat-Test, Tests pro Seite mit Benjamini-Hochberg-Korrektur | Bei 495 Landingpages geht es nicht ohne Korrektur für multiples Testen |
| Q8 | **Experiment-Design (A/B-Test)** | Wenn wir eine neue Landingpage testen: Wie viele Leads und wie viele Wochen brauchen wir, und wie werten wir den Test aus? | Power-Analyse, simulierter A/B-Test mit bekanntem Effekt, Entscheidung über Konfidenzintervall | Die Experiment-Daten sind **simuliert** und klar so markiert. Sie zeigen, dass die Methode funktioniert, mehr nicht |
| Q9 | **Aktivierung im Marktplatz** | Wie viele gewonnene Verkäufer machen einen ersten Verkauf, wie schnell, und woran erkennt man das vorher? | Aktivierungsrate, Zeit bis zum ersten Verkauf, 90-Tage-GMV | Bestellungen mit Artikeln gibt es nur bis zum 3. September 2018. Ein volles 90-Tage-Fenster haben nur Deals bis etwa 5. Juni 2018 |
| Q10 | **Retention auf der Käuferseite** | Kommen Käufer wieder? Wie sieht das Wiederkaufverhalten je Kohorte aus? | Retention-Matrix nach Kundenkohorten | Gezählt wird über `customer_unique_id` (`customer_id` ist pro Bestellung neu) |
| Q11 | **Automatisiertes Reporting** | Kann sich der wöchentliche GTM-Report selbst erstellen, damit mehr Zeit für Empfehlungen bleibt? | KPI-Pipeline per Skript, dazu eine KI-Zusammenfassung der Auffälligkeiten, die ein Mensch prüft | Die KI beschreibt nur Zahlen, die vorher berechnet wurden. Sie rechnet nie selbst |

---

## 3. Die Daten im Überblick

Quelle: Kaggle, *Marketing Funnel by Olist* und *Brazilian E-Commerce Public Dataset by Olist*.

| Tabelle | Zeilen | Zeitraum | Für welche Fragen |
|---|---|---|---|
| Marketing Qualified Leads | 8.000 | Jun 2017 – Mai 2018 (erster Kontakt) | Q1–Q3, Q5–Q8 |
| Abgeschlossene Deals | 842 | Dez 2017 – Nov 2018 (Abschlussdatum) | Q1, Q4, Q6, Q9 |
| Bestellungen | 99.441 | Sep 2016 – Okt 2018 (mit Artikeln nur bis 3. Sep 2018) | Q9, Q10 |
| Bestellpositionen, Verkäufer, Kunden, Produkte, Zahlungen, Bewertungen | — | — | Q9, Q10 |

Die wichtigsten Zahlen aus dem ersten Daten-Check:

- **Lead-to-Win-Conversion:** 842 / 8.000 = **10,5 %**
- **Dauer bis zum Abschluss:** im Median 14 Tage (Mittelwert 48 Tage, es gibt also einige sehr lange Deals)
- **Aktivierung:** Nur **45 %** der gewonnenen Verkäufer verkaufen jemals etwas (51 % bei Verkäufern mit vollem 90-Tage-Fenster)
- **Zeit vom Abschluss bis zum ersten Verkauf:** im Median 44 Tage
- **GMV-Konzentration:** Die besten 10 % der neuen Verkäufer machen **83 %** des gesamten GMV aller neuen Verkäufer in den ersten 90 Tagen
- **Wiederkaufrate:** Nur **3,1 %** der Kunden bestellen mehr als einmal

---

## 4. Erste Beobachtungen (Hypothesen)

Diese Punkte sind mir beim ersten Daten-Check aufgefallen. Es sind **Hypothesen**, keine Ergebnisse. Die Prüfung steht in Abschnitt 9.

**H1: Der „Conversion-Sprung“ von 2017 auf 2018 ist wahrscheinlich ein Tracking-Problem und kein Erfolg.**
Leads aus 2017 haben eine 60-Tage-Conversion von **0,5 %**, Leads aus 2018 dagegen **10,6 %**. Der erste Abschluss in den Daten ist aber vom **5. Dezember 2017**. Vermutlich wurden Abschlüsse erst ab diesem Zeitpunkt erfasst. Wer hier einfach vorher und nachher vergleicht, feiert eine Verbesserung um das 20-Fache, die es nie gab.
→ *Was daraus folgt: Vor jedem Vorher-/Nachher-Vergleich muss man prüfen, ob die Daten für beide Zeiträume vollständig sind. Sinnvoll vergleichen lassen sich nur die Kohorten aus 2018.*

**H2: Leads ohne Herkunft sind besonders gute Leads. Fehlendes Tracking verfälscht also die Kanal-Entscheidungen.**
`unknown` und fehlende Herkunft zusammen: 1.159 Leads (14,5 %). Sie konvertieren mit **16–23 %**, organische Suche zum Vergleich mit 11,8 %.
→ *Was daraus folgt: Zuerst die Attribution reparieren (UTM-Parameter, Tracking der Landingpages). Sonst verschiebt man Budget auf Basis unvollständiger Daten.*

**H3: Die Kanäle unterscheiden sich stark in der Qualität, nicht nur in der Menge.**
Paid Search (12,3 %) und organische Suche (11,8 %) konvertieren ähnlich gut. E-Mail (3,0 %) und Social (5,6 %) liegen weit darunter, obwohl Social 1.350 Leads bringt.

**H4: Ein gewonnener Deal ist noch kein Erfolg. Der Lead-Typ zeigt, wer später wirklich verkauft.**
Leads vom Typ `online_big` werden zu **63 %** aktiv (im Schnitt rund 1.490 BRL GMV in 90 Tagen). Bei `offline` sind es nur **29 %** (rund 80 BRL), bei `industry` 33 %.
→ *Was daraus folgt für den Vertrieb: Leads nicht nur danach bewerten, ob sie abschließen, sondern auch danach, ob sie später aktiv werden.*

**H5: Wenige Landingpages tragen den ganzen Funnel.**
Die zwei größten Landingpages (je etwa 900 Leads) konvertieren mit **19–20 %**. Andere Seiten mit viel Traffic kommen nur auf 3–7 %.

**H6: Klassische A/B-Tests auf Lead-to-Win dauern bei diesem Volumen zu lange.**
Um eine Steigerung von 12 % auf 14 % nachzuweisen (α = 0,05, Power = 80 %), braucht man etwa **4.400 Leads pro Variante**. Bei rund 1.200 MQLs im Monat dauert das **mehr als 7 Monate**.
→ *Was daraus folgt: Auf schnellere Kennzahlen weiter oben im Funnel testen (MQL-Rate, SDR-Kontaktrate), ein sequenzielles Design nutzen oder vorher/nachher mit Kontrollgruppe vergleichen (Difference-in-Differences).*

---

## 5. KPI-Definitionen (eine Definition für alle)

Die vollständigen Definitionen auf Deutsch und Englisch stehen in [docs/kpi_definitions.md](docs/kpi_definitions.md). Die Zahlen kommen aus der Tabelle `mart_kpi_summary`.

| KPI | Definition | Warum so |
|---|---|---|
| MQL | Ein Lead in `marketing_qualified_leads` mit einem Datum für den ersten Kontakt | Hier beginnt der Sales-Funnel |
| Lead-to-Win-Rate (60 T.) | MQLs, die innerhalb von 60 Tagen nach dem ersten Kontakt abschließen ÷ alle MQLs der Kohorte | Mit einem festen Fenster kann man alte und neue Kohorten fair vergleichen |
| Sales Cycle | `won_date` − `first_contact_date` in Tagen (als Median) | Der Median wird durch einzelne sehr lange Deals nicht verzerrt |
| Aktivierungsrate | Gewonnene Verkäufer mit mindestens einer nicht stornierten Bestellung ÷ alle gewonnenen Verkäufer | Trennt „unterschrieben“ von „verkauft wirklich“ |
| Zeit bis zum ersten Verkauf | Datum der ersten Bestellung − `won_date` in Tagen | Zeigt, wie schnell das Onboarding läuft |
| 90-Tage-GMV pro Verkäufer | Summe der Artikelpreise in den ersten 90 Tagen nach `won_date` | Ein vergleichbarer Wert pro gewonnenem Verkäufer |
| Wiederkaufrate | Kunden (`customer_unique_id`) mit mindestens 2 nicht stornierten Bestellungen ÷ alle Kunden mit mindestens einer | Treue auf der Käuferseite |

---

## 6. Datenqualität und Grenzen

Das steht bewusst am Anfang. Einer Datenbasis kann man nur vertrauen, wenn man ihre Grenzen kennt.

- **Keine Verlustgründe:** „Verloren“ heißt nur: MQL ohne Abschluss. Für echte Verlustgründe bräuchte man CRM-Daten.
- **Deal-Merkmale gibt es nur bei gewonnenen Deals:** Segment, Lead-Typ und Geschäftstyp erklären deshalb nicht die Conversion, sondern nur die Qualität der Abschlüsse.
- **`declared_monthly_revenue` ist nicht brauchbar:** Rund 95 % der Werte sind 0.
- **`has_company`, `has_gtin`, `average_stock`, `declared_product_catalog_size`:** Etwa 92 % der Werte fehlen. Diese Spalten nutze ich nicht.
- **`lead_behaviour_profile`:** 21 % fehlen, außerdem gibt es Mehrfachwerte wie `"cat, wolf"`.
- **Rechtszensierung:** Neue Leads und Deals hatten weniger Zeit, um abzuschließen oder aktiv zu werden. Deshalb arbeite ich mit festen Zeitfenstern.
- **Ein Deal hat einen negativen Sales Cycle** (Abschluss vor dem ersten Kontakt). Er wird markiert und nicht mitgezählt.
- **Lücke in der Abdeckung:** Abschlüsse gibt es erst ab Dezember 2017 (siehe H1).
- **Tatsächliches Datenende:** Die letzte Bestellung ist vom 17. Oktober 2018, die letzte Bestellung *mit Artikeln* aber vom 3. September 2018. Alle 90-Tage-Fenster rechnen mit dem zweiten Datum.
- **Kontext:** Brasilianischer E-Commerce, 2016–2018. Die *Methoden* lassen sich auf andere Marktplätze übertragen, die absoluten Zahlen nicht.

---

## 7. Aufbau

```text
data/raw (CSV-Dateien von Kaggle)
      │  src/check_data.py    → Dateien vollständig? Zeilen, Schlüssel, Zeiträume
      │  src/profile_data.py  → Profil pro Spalte (docs/data_profile.md)
      │  src/clean.py         → Datentypen, versteckte Lücken, Qualitäts-Flags
      ▼
data/processed (bereinigte Parquet-Dateien, Rohdaten bleiben unverändert)
      │  src/warehouse.py     → führt das SQL aus und prüft Granularität und GMV
      ▼
DuckDB (database/warehouse.duckdb)
      │  sql/warehouse/       → Staging → Dimensionen → Fakten
      │  sql/marts/           → KPI-Schicht
      ▼
┌───────────────────────────┬──────────────────────────────┬───────────────────────────────┐
│ analysis/                 │ app/ (Streamlit)             │ src/weekly_report.py          │
│ Belege pro Frage          │ Dashboard auf EN / DE / FA   │ GTM-Report auf EN / DE / FA   │
│ → reports/analysis/       │ Texte: src/i18n/             │ + optionale KI-Zusammenfassung│
│ → data/results/           │                              │ → reports/weekly/             │
└───────────────────────────┴──────────────────────────────┴───────────────────────────────┘
```

**Stack:** Python (pandas, scipy, statsmodels), DuckDB (SQL), Streamlit + Plotly.

---

## 8. Seiten im Dashboard

Start mit `streamlit run app\Home.py`. In der Seitenleiste lässt sich die Sprache wählen: **English, Deutsch, فارسی / دری** (bei Persisch läuft der Text von rechts nach links). Auf Deutsch und Persisch zeigt die Hilfe zu jeder Kennzahl auch den englischen Begriff.

1. **GTM-Überblick:** 7 KPI-Kacheln mit Zähler und Nenner, Leads und Win-Rate in 60 Tagen nach Monat (Monate ohne Erfassung grau)
2. **Marketing & Kanäle:** Tracking-Lücke, Win-Rate pro Kanal mit 95-%-Konfidenzintervall, aktive Verkäufer pro 1.000 Leads, Landingpages im Vergleich mit ihrem Kanal-Mix (einfacher gegen korrigierten Test)
3. **Verkäufer & Kohorten:** Aktivierung in 30 / 60 / 90 Tagen, Aktivierung und GMV-Anteil nach Lead-Typ, Heatmap zur Kundenbindung
4. **Experimente:** Rechner für Stichprobe und Dauer (Startwerte aus dem echten Lead-Volumen), Auswertung eines fertigen A/B-Tests mit Entscheidungsregel
5. **Empfehlungen:** die neun Ergebnisse, nach Team filterbar
6. **Datenqualität:** jede bekannte Lücke mit betroffenen Datensätzen und den Kennzahlen, die sie beeinflusst
7. **Frag die Daten:** Fragen zu den Zahlen, beantwortet von einem kostenlosen, lokalen KI-Modell (Ollama, Modell `gemma3:4b`). Es bekommt nur die berechneten Fakten, und jede Antwort ist als KI-Antwort markiert. Einmalig einrichten: `winget install Ollama.Ollama`, dann `ollama pull gemma3:4b`.

Die meisten Seiten enden mit einer **„Und jetzt?“-Box**. Regeln hinter dem Dashboard: Es öffnet das Warehouse nur zum Lesen und mit einer kurzen Verbindung pro Abfrage (deshalb kann `src\warehouse.py` laufen, während es offen ist; danach „Daten neu laden“ klicken). Es berechnet selbst keine Kennzahl, und alle Texte stehen in `src/i18n/translations.json`.

---

## 9. Ergebnisse & Empfehlungen

Sortiert nach Priorität: Das erste Ergebnis entscheidet darüber, wie verlässlich alle anderen sind. Alle Raten stammen aus fairen Vergleichsgruppen (Lead-Kohorten aus 2018, Verkäufer mit vollem 90-Tage-Fenster). Die Belege stehen in [reports/analysis/](reports/analysis/). Ohne Marketingkosten lassen sich CAC und ROI nicht berechnen. Deshalb verspricht keine Zeile einen Geldbetrag.

| # | Ergebnis | Beleg | Empfehlung | Verantwortlich | Erwartete Wirkung | So messen wir es | Sicherheit |
|---|---|---|---|---|---|---|---|
| 1 | **Ein Viertel aller Abschlüsse lässt sich keinem Kanal zuordnen.** Der größte Teil der Lücke kommt von einer einzigen Landingpage | Leads ohne Kanal: 14,4 % der Leads, aber 25,2 % der Abschlüsse in 60 Tagen (Win-Rate 18,6 % statt 9,3 %). 62 % davon kommen über die Seite `b76ef374`. Je nach Annahme verschieben sich die Kanal-Raten um bis zu 3 Punkte (4.1, 4.3, 4.4) | Zuerst das Tracking auf `b76ef374` reparieren (UTM-Parameter und Referrer ins Lead-Formular übergeben), danach den Kanal zum Pflichtfeld machen. Bis dahin kein Budget zwischen organischer Suche und Paid Search verschieben | Marketing Ops + Data Engineering | Mit einer Maßnahme ist der größte Teil der Lücke geschlossen. Kanal-Entscheidungen beruhen auf dem ganzen Funnel | `attributed_share` pro Monat in `mart_gtm_monthly` | hoch |
| 2 | **Trend-Reports können Veränderungen zeigen, die es nie gab** | Einfacher Vergleich 2017 → 2018: 21-fache „Verbesserung“. Fairer Vergleich (Jan–Feb gegen Mär–Apr 2018): +0,9 Punkte. Die Aktivierung fällt bei Verkäufern ab Juni 2018 auf 0 %, nur weil die Daten enden (4.4) | Alle Trend-Grafiken im Januar 2018 beginnen lassen. Monate ohne vollständiges Tracking oder ohne volles 90-Tage-Fenster grau darstellen. Jeder Vorher-/Nachher-Vergleich beginnt mit einer Prüfung der Datenabdeckung | Analytics (Dashboard) + CPO | Kein falscher Erfolg und kein falscher Alarm im Management-Reporting | Das Dashboard nutzt überall `deal_tracking_complete` und `has_full_90d_window` | hoch |
| 3 | **Social bringt Menge, aber keine Verkäufer** | 1.051 Leads, Win-Rate 4,7 % (KI 4–6 %), 22 aktive Verkäufer pro 1.000 Leads gegenüber 57–69 bei der Suche. Bleibt in allen Szenarien der schwächste große Kanal. Die Social-Landingpages sind genau so gut, wie man es für den Kanal erwartet (4.1, 4.3, 4.4) | Zielgruppen und Budget von Social zusammen mit den Kostendaten prüfen. Die Social-Landingpages nicht neu gestalten: Das Problem ist nicht die Seite | Marketing | Budget geht in Kanäle mit etwa dreimal mehr aktiven Verkäufern pro Lead | Aktive Verkäufer pro 1.000 Leads je Kanal | mittel (keine Kostendaten) |
| 4 | **Lead-Typ und Geschäftstyp zeigen, wer wirklich verkaufen wird** | Aktivierung: `online_big` 72 %, `offline` 34 %, `industry` 37 %. Das gilt auch im Regressionsmodell (Odds Ratio `offline` 0,36, Hersteller 0,58). `online_big` sind 15 % der Verkäufer, bringen aber 47 % des 90-Tage-GMV. `offline` sind 12 % der Verkäufer und bringen 2 % (4.2) | Sales: In den Zielen aktive Verkäufer zählen, nicht nur unterschriebene, und den Lead-Typ zur Priorisierung nutzen. Product: Onboarding-Hilfe für Offline-, Industrie- und Hersteller-Kunden. Diese Leads nicht ablehnen: Das Modell erklärt nur wenig (Pseudo-R² 0,06) | Sales + Product | Mehr gewonnene Verkäufer, die wirklich verkaufen. Weniger Aufwand für Deals, die nie aktiv werden | `seller_activation_rate_full_window` pro Lead-Typ, neue Kohorten gegen frühere | hoch (Muster), mittel (Wirkung der Maßnahme) |
| 5 | **Deals, die lange dauern, werden seltener aktiv** | Abschluss nach mehr als 30 Tagen: 43 % Aktivierung, Abschluss innerhalb einer Woche: 56 % (Odds Ratio 0,59, p = 0,02) (4.2) | Deals mit mehr als 30 Tagen Verkaufszyklus markieren und in den ersten Wochen ein Onboarding-Gespräch einplanen | Sales + Product | Unsichere Verkäufer bekommen früher Hilfe | Aktivierung der markierten Deals gegen frühere vergleichbare Deals | mittel |
| 6 | **Zwei Landingpages sind klar besser als ihr Kanal, eine ist klar schlechter** | Nach Bereinigung um den Kanal und Benjamini-Hochberg-Korrektur unterscheiden sich 3 von 18 Seiten (ohne Korrektur: 8). `22c29808` +8,2 Punkte, `40dec9f3` +6,8 Punkte, `e492ee5e` −6,1 Punkte (2018 etwa 13 Abschlüsse unter Erwartung, Obergrenze) (4.3) | Herausfinden, was die zwei starken Seiten anders machen, und das ohne A/B-Test auf `e492ee5e` übernehmen: Bei rund 40 Leads im Monat würde sogar ein Test über die Formular-Abschlüsse länger als ein Jahr dauern (5.2). Einzelne Elemente lieber auf Seiten mit viel Traffic testen. Risiko: Ohne Kontrollgruppe kann eine spätere Veränderung auch von der Saison oder vom Kanal-Mix kommen | Marketing / Content + Product | Bessere Conversion auf einer organischen Seite mit rund 40 Leads im Monat | Win-Rate von `e492ee5e` im Vergleich zur Erwartung für ihren Kanal, ab den nächsten Kohorten | mittel |
| 7 | **Paid Search konvertiert nicht besser als die organische Suche** | Win-Rate 11,6 % gegen 11,5 % (p = 0,95). Aktivierung 60 % gegen 49 %, aber p = 0,049 in einem explorativen Test, und die Reihenfolge dreht sich je nach Attributions-Szenario (4.1, 4.4) | Kein Budget wegen „besserer Conversion“ verschieben. Die Aktivierung pro Kanal nach der Tracking-Reparatur (#1) mit neuen Kohorten erneut prüfen | Marketing | Keine Budget-Entscheidung auf Basis von Zufall | Aktivierung pro Kanal, neue Kohorten | niedrig |
| 8 | **Die Daten geben keine Rangliste der Vertriebsmitarbeiter her** | Aktivierung pro Mitarbeiter: 38–59 %. Nach Bereinigung um den Lead-Mix gibt es keinen Unterschied (p = 0,47), niemand liegt außerhalb seines Intervalls (4.2) | Die reine Aktivierungsrate pro Mitarbeiter nicht im Mitarbeitergespräch verwenden. Falls nötig, Ist gegen Erwartung für den jeweiligen Lead-Mix zeigen | Vertriebsleitung | Faire Bewertung, niemand wird für seinen Lead-Mix oder den Zufall verantwortlich gemacht | – | hoch |
| 9 | **Das Verhaltensprofil sagt nichts über die Aktivierung** | `cat`, `eagle`, `wolf`, `shark`: kein Unterschied (p = 0,57) (4.2) | Mit Sales klären, wie viel Zeit das Feld kostet. Wenn es nur dafür gepflegt wird, darauf verzichten | Sales | Zeitersparnis in jedem Deal | – | mittel |

---

## 10. So startest du das Projekt (Windows)

```powershell
git clone https://github.com/walidsharaar/python_projects.git
cd "python_projects\044_Olis Market Insights"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1. Beide Olist-Datensätze von Kaggle laden und alle CSV-Dateien nach data\raw\ entpacken
# 2. Daten prüfen, profilieren und bereinigen
python src\check_data.py
python src\profile_data.py
python src\clean.py
# 3. DuckDB-Warehouse und KPI-Schicht bauen (stoppt, wenn eine Prüfung fehlschlägt)
python src\warehouse.py
# 4. Analysen ausführen (die Belege landen in reports\analysis\)
python analysis\01_channel_quality.py
python analysis\02_win_vs_activation.py
python analysis\03_landing_pages.py
python analysis\04_tracking_data_quality.py
python analysis\05_cohorts.py
python analysis\06_experiments.py
# 5. Dashboard (Englisch, Deutsch, Persisch)
streamlit run app\Home.py
# 6. GTM-Report als Markdown in reports\weekly\ (mit --ai kommt eine optionale KI-Zusammenfassung dazu;
#    dafür braucht es "pip install anthropic" und einen API-Schlüssel, der Report ist auch ohne sie vollständig)
python src\weekly_report.py
# 7. Tests: Übersetzungen, jede Dashboard-Seite in jeder Sprache, der Report
python -m unittest discover tests
```

---

## 11. Projektstand

- [x] Schritt 1: Setup, Daten-Download, Daten-Check, Fragen an die Daten
- [x] Schritt 2: Profiling & Bereinigung
- [x] Schritt 3: Datenmodell (DuckDB) & KPI-Schicht
- [x] Schritt 4: Funnel-, Kanal-, Segment- und Win/Loss-Analyse, Ergebnisse & Empfehlungen
- [x] Schritt 5: Kohorten & Experiment-Modul
- [x] Schritt 6: Streamlit-Dashboard auf Englisch, Deutsch und Persisch (Farsi/Dari)
- [x] Schritt 7: Automatischer GTM-Report in drei Sprachen mit optionaler KI-Zusammenfassung

---

## Datenquelle & Lizenz

- [Marketing Funnel by Olist](https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist)
- [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

Beide Datensätze stehen unter der Lizenz **CC BY-NC-SA 4.0**. Die Rohdaten liegen nicht in diesem Repository. Bitte lade sie direkt von Kaggle herunter.

## Autor

**Walid Sharaar**, Data Analyst / BI Engineer, Hamburg
[LinkedIn](https://www.linkedin.com/in/walidsharaar/) · [GitHub](https://github.com/walidsharaar)
