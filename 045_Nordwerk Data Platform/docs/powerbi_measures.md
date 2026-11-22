# Power BI: Kennzahlen (DAX)

Alle Kennzahlen des Berichts zum Kopieren. In Power BI Desktop: Tabelle `_Kennzahlen` auswählen → **Neues Measure** →
die Zeile `Name = …` einfügen. Format und Anzeigeordner stehen jeweils darüber.

Tabellen in Power BI (Quelle → Name): `gold.fact_verkauf` → **Verkauf**, `gold.fact_lieferung` → **Lieferung**,
`gold.dim_datum` → **Datum**, `gold.dim_kunde` → **Kunde**, `gold.dim_artikel` → **Artikel**, `gold.dim_firma` → **Firma**,
`meta.v_dq_aktuell` → **Datenqualität**.


## 1 Umsatz & DB

**Umsatz** – Nettoumsatz aus Rechnungen, Gutschriften abgezogen, inkl. Intercompany  
Format: `#,0 €`

```dax
Umsatz =
    SUM ( Verkauf[umsatz_netto] )
```

**Kosten** – Wareneinsatz: Menge in Stück mal Kosten je Stück  
Format: `#,0 €`

```dax
Kosten =
    SUM ( Verkauf[kosten] )
```

**Deckungsbeitrag** – Umsatz minus Wareneinsatz  
Format: `#,0 €`

```dax
Deckungsbeitrag =
    [Umsatz] - [Kosten]
```

**DB %** – Deckungsbeitrag im Verhältnis zum Umsatz  
Format: `0.0 %`

```dax
DB % =
    DIVIDE ( [Deckungsbeitrag], [Umsatz] )
```

**Umsatz Konzern** – Umsatz mit externen Kunden: Verkäufe zwischen Konzerngesellschaften eliminiert  
Format: `#,0 €`

```dax
Umsatz Konzern =
    CALCULATE ( [Umsatz], Verkauf[ist_intercompany] = FALSE () )
```

**Umsatz Intercompany** – Umsatz mit anderen Konzerngesellschaften  
Format: `#,0 €`

```dax
Umsatz Intercompany =
    CALCULATE ( [Umsatz], Verkauf[ist_intercompany] = TRUE () )
```

**Anteil Intercompany** – Anteil des Intercompany-Umsatzes am Gesamtumsatz  
Format: `0.0 %`

```dax
Anteil Intercompany =
    DIVIDE ( [Umsatz Intercompany], [Umsatz] )
```

**Deckungsbeitrag Konzern** – Deckungsbeitrag mit externen Kunden  
Format: `#,0 €`

```dax
Deckungsbeitrag Konzern =
    CALCULATE ( [Deckungsbeitrag], Verkauf[ist_intercompany] = FALSE () )
```

**DB % Konzern** – Deckungsbeitragsmarge mit externen Kunden  
Format: `0.0 %`

```dax
DB % Konzern =
    DIVIDE ( [Deckungsbeitrag Konzern], [Umsatz Konzern] )
```

**Menge Stück** – Verkaufte Menge in Stück  
Format: `#,0`

```dax
Menge Stück =
    SUM ( Verkauf[menge_stueck] )
```


## 2 Zeitvergleich

**Datenbeginn** – Erstes Rechnungsdatum im Datenbestand  
Format: `dd.MM.yyyy`

```dax
Datenbeginn =
    MIN ( Datum[datenbeginn] )
```

**Datenstand** – Letztes Rechnungsdatum im Datenbestand (Stichtag)  
Format: `dd.MM.yyyy`

```dax
Datenstand =
    MAX ( Datum[datenstand] )
```

**Zeitraum bis** – Ende des gewählten Zeitraums, höchstens bis zum Datenstand  
Format: `dd.MM.yyyy`

```dax
Zeitraum bis =
    MIN ( MAX ( Datum[datum] ), [Datenstand] )
```

**Umsatz Konzern VJ** – Konzernumsatz im gleichen Zeitraum des Vorjahres, bis zum gleichen Tag. Leer, wenn das Vorjahr nicht vollständig in den Daten liegt.  
Format: `#,0 €`

```dax
Umsatz Konzern VJ =
    VAR beginn = MAX ( MIN ( Datum[datum] ), [Datenbeginn] )
    VAR ende = [Zeitraum bis]
    VAR beginnVJ = EDATE ( beginn, -12 )
    VAR endeVJ = EDATE ( ende, -12 )
    RETURN
    IF (
        beginnVJ >= [Datenbeginn] && ende >= beginn,
        CALCULATE ( [Umsatz Konzern], DATESBETWEEN ( Datum[datum], beginnVJ, endeVJ ) )
    )
```

**Umsatz Konzern Δ VJ %** – Veränderung zum vergleichbaren Vorjahreszeitraum  
Format: `+0.0 %;-0.0 %;0.0 %`

```dax
Umsatz Konzern Δ VJ % =
    VAR vj = [Umsatz Konzern VJ]
    RETURN
    IF ( NOT ISBLANK ( vj ), DIVIDE ( [Umsatz Konzern] - vj, vj ) )
```

**Δ VJ Anzeige** – Veränderung zum Vorjahr als Text; – wenn kein vergleichbares Vorjahr vorliegt

```dax
Δ VJ Anzeige =
    VAR d = [Umsatz Konzern Δ VJ %]
    RETURN
    IF ( ISBLANK ( d ), "–", FORMAT ( d, "+0.0 %;-0.0 %;0.0 %", "de-DE" ) )
```

**Umsatz Konzern Monat** – Konzernumsatz nur für vollständige Monate (Trendlinie)  
Format: `#,0 €`

```dax
Umsatz Konzern Monat =
    IF ( MIN ( Datum[ist_vollstaendiger_monat] ) = 1, [Umsatz Konzern] )
```

**Umsatz Konzern VJ Monat** – Konzernumsatz im gleichen Monat des Vorjahres, nur wenn beide Monate vollständig sind  
Format: `#,0 €`

```dax
Umsatz Konzern VJ Monat =
    VAR vollstaendig = MIN ( Datum[ist_vollstaendiger_monat] )
    VAR vjVollstaendig =
    CALCULATE ( MIN ( Datum[ist_vollstaendiger_monat] ), SAMEPERIODLASTYEAR ( Datum[datum] ) )
    RETURN
    IF (
        vollstaendig = 1 && vjVollstaendig = 1,
        CALCULATE ( [Umsatz Konzern], SAMEPERIODLASTYEAR ( Datum[datum] ) )
    )
```


## 3 Kunden

**Anzahl Kunden** – Externe Konzernkunden mit Umsatz, ohne Unbekannt  
Format: `#,0`

```dax
Anzahl Kunden =
    CALCULATE ( DISTINCTCOUNT ( Verkauf[kunde_sk] ), Verkauf[kunde_sk] <> -1, Verkauf[ist_intercompany] = FALSE () )
```

**Umsatz je Kunde** – Durchschnittlicher Konzernumsatz je Kunde  
Format: `#,0 €`

```dax
Umsatz je Kunde =
    DIVIDE ( CALCULATE ( [Umsatz Konzern], Verkauf[kunde_sk] <> -1 ), [Anzahl Kunden] )
```

**Anteil Mehrfachkunden** – Anteil des Konzernumsatzes mit Kunden, die bei mehreren Gesellschaften kaufen  
Format: `0.0 %`

```dax
Anteil Mehrfachkunden =
    DIVIDE ( CALCULATE ( [Umsatz Konzern], Kunde[anzahl_firmen] >= 2 ), [Umsatz Konzern] )
```


## 4 Lieferquote

**Lieferquote Menge** – Gelieferte durch bestellte Stück; nur fällige, nicht stornierte Aufträge  
Format: `0.0 %`

```dax
Lieferquote Menge =
    VAR geliefert =
    CALCULATE (
        SUM ( Lieferung[menge_geliefert_stueck] ),
        Lieferung[ist_faellig] = TRUE (),
        Lieferung[ist_storniert] = FALSE ()
    )
    VAR bestellt =
    CALCULATE (
        SUM ( Lieferung[menge_bestellt_stueck] ),
        Lieferung[ist_faellig] = TRUE (),
        Lieferung[ist_storniert] = FALSE ()
    )
    RETURN
    DIVIDE ( geliefert, bestellt )
```

**Lieferquote Positionen** – Anteil vollständig gelieferter Auftragspositionen  
Format: `0.0 %`

```dax
Lieferquote Positionen =
    VAR alle =
    CALCULATE ( COUNTROWS ( Lieferung ),
        Lieferung[ist_faellig] = TRUE (),
        Lieferung[ist_storniert] = FALSE ()
    )
    VAR vollstaendig =
    CALCULATE ( COUNTROWS ( Lieferung ),
        Lieferung[ist_faellig] = TRUE (),
        Lieferung[ist_storniert] = FALSE (),
        Lieferung[ist_vollstaendig_geliefert] = TRUE ()
    )
    RETURN
    DIVIDE ( vollstaendig, alle )
```

**Lieferquote Ziel** – Zielwert für die Lieferquote (Menge)  
Format: `0.0 %`

```dax
Lieferquote Ziel =
    0.98
```

**Lieferquote Monat** – Lieferquote (Menge) nur für vollständige Monate (Trendlinie)  
Format: `0.0 %`

```dax
Lieferquote Monat =
    IF ( MIN ( Datum[ist_vollstaendiger_monat] ) = 1, [Lieferquote Menge] )
```

**Lieferquote Ziel Monat** – Ziellinie im Trend  
Format: `0.0 %`

```dax
Lieferquote Ziel Monat =
    IF ( NOT ISBLANK ( [Lieferquote Monat] ), [Lieferquote Ziel] )
```


## 5 Datenqualität

**DQ Fehler** – Prüfregeln mit Status ERROR im letzten Lauf  
Format: `#,0`

```dax
DQ Fehler =
    CALCULATE ( COUNTROWS ( 'Datenqualität' ), 'Datenqualität'[status] IN { "ERROR", "BLOCKIERT" } )
```

**DQ Warnungen** – Prüfregeln mit Status WARN im letzten Lauf  
Format: `#,0`

```dax
DQ Warnungen =
    CALCULATE ( COUNTROWS ( 'Datenqualität' ), 'Datenqualität'[status] = "WARN" )
```

**DQ Regeln OK** – Prüfregeln ohne Befund im letzten Lauf  
Format: `#,0`

```dax
DQ Regeln OK =
    CALCULATE ( COUNTROWS ( 'Datenqualität' ), 'Datenqualität'[status] = "OK" )
```

**Positionen ohne Kunde** – Verkaufspositionen, deren Kunde im Kundenstamm fehlt  
Format: `#,0`

```dax
Positionen ohne Kunde =
    CALCULATE ( COUNTROWS ( Verkauf ), Verkauf[kunde_sk] = -1 )
```

**Umsatz ohne Kunde** – Umsatz der Verkaufspositionen ohne Kundenzuordnung  
Format: `#,0 €`

```dax
Umsatz ohne Kunde =
    CALCULATE ( [Umsatz], Verkauf[kunde_sk] = -1 )
```

**DQ Statusfarbe** – Hintergrundfarbe der Statusspalte

```dax
DQ Statusfarbe =
    SWITCH (
    SELECTEDVALUE ( 'Datenqualität'[status] ),
    "BLOCKIERT", "#F4B6A6",
    "ERROR", "#FBE3DC",
    "WARN", "#FBF1D6",
    "OK", "#DDF1EE"
    )
```


## 6 Story

**Story overview DE** – Erkenntnis-Titel der Seite overview (DE)

```dax
Story overview DE =
    "Konzernumsatz bis "
    & FORMAT ( [Zeitraum bis], "dd.MM.yyyy" )
    & ": "
    & FORMAT ( [Umsatz Konzern] / 1000000, "0.00", "de-DE" )
    & " Mio. €"
    & IF ( ISBLANK ( [Umsatz Konzern Δ VJ %] ), " – kein vergleichbares Vorjahr in den Daten", " (" & FORMAT ( [Umsatz Konzern Δ VJ %], "+0.0 %;-0.0 %", "de-DE" ) & " ggü. Vorjahr)" )
```

**Story overview EN** – Erkenntnis-Titel der Seite overview (EN)

```dax
Story overview EN =
    "Group revenue to "
    & FORMAT ( [Zeitraum bis], "dd MMM yyyy", "en-US" )
    & ": "
    & FORMAT ( [Umsatz Konzern] / 1000000, "0.00", "en-US" )
    & "M €"
    & IF ( ISBLANK ( [Umsatz Konzern Δ VJ %] ), " – no comparable prior year in the data", " (" & FORMAT ( [Umsatz Konzern Δ VJ %], "+0.0%;-0.0%", "en-US" ) & " vs. prior year)" )
```

**Story customers DE** – Erkenntnis-Titel der Seite customers (DE)

```dax
Story customers DE =
    FORMAT ( [Anteil Mehrfachkunden], "0 %", "de-DE" )
    & " des Konzernumsatzes entfallen auf Kunden, die bei beiden Gesellschaften kaufen"
```

**Story customers EN** – Erkenntnis-Titel der Seite customers (EN)

```dax
Story customers EN =
    FORMAT ( [Anteil Mehrfachkunden], "0%", "en-US" )
    & " of group revenue comes from customers who buy from both companies"
```

**Story delivery DE** – Erkenntnis-Titel der Seite delivery (DE)

```dax
Story delivery DE =
    "Lieferquote "
    & FORMAT ( [Lieferquote Menge], "0.0 %", "de-DE" )
    & IF ( [Lieferquote Menge] >= [Lieferquote Ziel], " – Ziel von 98 % erreicht", " – Ziel von 98 % verfehlt" )
```

**Story delivery EN** – Erkenntnis-Titel der Seite delivery (EN)

```dax
Story delivery EN =
    "Delivery rate "
    & FORMAT ( [Lieferquote Menge], "0.0%", "en-US" )
    & IF ( [Lieferquote Menge] >= [Lieferquote Ziel], " – 98% target met", " – 98% target missed" )
```

**Story quality DE** – Erkenntnis-Titel der Seite quality (DE)

```dax
Story quality DE =
    FORMAT ( [Positionen ohne Kunde], "0" )
    & " Verkaufspositionen über "
    & FORMAT ( [Umsatz ohne Kunde] / 1000, "#,0", "de-DE" )
    & " Tsd. € ohne Kundenzuordnung – Kunde im SAP-Kundenstamm anlegen"
```

**Story quality EN** – Erkenntnis-Titel der Seite quality (EN)

```dax
Story quality EN =
    FORMAT ( [Positionen ohne Kunde], "0" )
    & " sales lines worth "
    & FORMAT ( [Umsatz ohne Kunde] / 1000, "#,0", "en-US" )
    & "k € have no customer – create the customer in the SAP master data"
```
