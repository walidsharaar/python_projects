# GTM-Report: 3. Sep. 2018

_Automatisch erstellt am 19. Nov. 2026 aus der KPI-Schicht (database/warehouse.duckdb). Daten: echte, öffentliche Daten von Olist, tatsächliches Datenende 3. Sep. 2018._

## 1. Die wichtigsten Kennzahlen

| Kennzahl | Wert | Basis |
|---|---|---|
| MQLs | 8.000 |  |
| Vertragsquote (60 Tage) | 10,6 % | 636 von 5.998 |
| Verkaufszyklus (Median) | 14 Tage | n = 841 |
| Verträge ohne bekannten Kanal | 25,2 % | 160 von 636 |
| Aktivierungsrate der Verkäufer | 51,4 % | 345 von 671 |
| Zeit bis zum ersten Verkauf (Median) | 44 Tage | n = 379 |
| GMV in 90 Tagen pro gewonnenem Verkäufer | 507 BRL | n = 671 |
| Wiederkaufrate | 3,1 % | 2.924 von 95.560 |

## 2. Der letzte Monat im Vergleich mit früheren Monaten

Nur Lead-Monate mit vollständig erfassten Abschlüssen. Der letzte Monat wird mit allen früheren erfassten Monaten zusammen verglichen, mit einem Test für zwei Anteile.

- Leads im Mai 2018: 1.303 (−3,6 % im Vergleich zum Vormonat).
- Vertragsquote (60 Tage) im Mai 2018: 7,8 %. Frühere erfasste Monate zusammen: 11,4 % (p < 0,001).

> Deutliche Veränderung: Der Unterschied ist wahrscheinlich kein Zufall. Zuerst prüfen, ob er echt ist (Tracking, Kanal-Mix, eine neue Landingpage), bevor jemand handelt.

## 3. Hinweise zur Datenqualität

Bekannte Lücken, die mindestens 5 % ihrer Datensätze betreffen. Alle Zahlen in diesem Report berücksichtigen sie schon.

- Deals ohne angegebenen Umsatz (0 in der Quelle): 797 von 842 (94,7 %). Betrifft: Jedes Lead-Scoring auf Basis des Umsatzes.
- Leads aus Monaten ohne Erfassung der Abschlüsse: 2.002 von 8.000 (25,0 %). Betrifft: Monatliche Trends der Vertragsquote.
- Gewonnene Deals ohne Verhaltensprofil: 177 von 842 (21,0 %). Betrifft: Analyse des Verhaltens.
- Verkäufer ohne volles 90-Tage-Fenster: 171 von 842 (20,3 %). Betrifft: Aktivierung und GMV in 90 Tagen.
- Leads ohne Kanal: 1.159 von 8.000 (14,5 %). Betrifft: Vergleich der Kanäle.

## 4. Empfohlene Maßnahmen (Top 3)

1. **Ein Viertel aller Abschlüsse lässt sich keinem Kanal zuordnen.** Zuerst das Tracking auf der Landingpage b76ef374 reparieren, danach den Kanal zum Pflichtfeld machen. Bis dahin kein Budget zwischen organischer Suche und Paid Search verschieben. _So messen wir es: Anteil der Leads ohne Kanal, pro Monat._
2. **Trend-Reports können Veränderungen zeigen, die es nie gab.** Trend-Grafiken mit dem ersten vollständig erfassten Monat beginnen. Monate ohne vollständige Erfassung oder ohne volles 90-Tage-Fenster grau darstellen. Jeder Vorher-/Nachher-Vergleich beginnt mit einer Prüfung der Datenabdeckung. _So messen wir es: Jede Trend-Grafik nutzt die Kennzeichen für Erfassung und Zeitfenster._
3. **Social bringt Menge, aber keine Verkäufer.** Zielgruppen und Budget von Social zusammen mit den Kostendaten prüfen. Die Social-Landingpages nicht neu gestalten: Sie sind so gut, wie man es für den Kanal erwartet. _So messen wir es: Aktive Verkäufer pro 1.000 Leads je Kanal._

## 5. Zusammenfassung (KI-Entwurf, muss von einem Menschen geprüft werden)

Keine KI-Zusammenfassung. Mit --ai ausführen, um eine hinzuzufügen (braucht das Paket anthropic und einen API-Schlüssel).

---

_Definitionen aller Kennzahlen: docs/kpi_definitions.md. Belege für die Maßnahmen: README, Abschnitt 9, und reports/analysis._
