-- Sales fact. Grain: one invoice line.
DROP TABLE IF EXISTS gold.fact_verkauf CASCADE;

CREATE TABLE gold.fact_verkauf AS
SELECT
    v.beleg_datum                       AS datum,
    v.firma_id,
    COALESCE(dk.kunde_sk,   -1)         AS kunde_sk,       -- -1 = unknown customer
    COALESCE(da.artikel_sk, -1)         AS artikel_sk,     -- -1 = unknown item
    v.beleg_nr,
    v.beleg_pos,
    v.belegart,
    v.menge_stueck,
    v.umsatz_netto,
    v.kosten,
    v.umsatz_netto - v.kosten           AS deckungsbeitrag,
    COALESCE(k.ist_konzern, false)      AS ist_intercompany
FROM silver.verkauf v
LEFT JOIN silver.kunde     k  ON k.kunde_key         = v.kunde_key
LEFT JOIN silver.kunde_map m  ON m.kunde_key         = v.kunde_key
LEFT JOIN gold.dim_kunde   dk ON dk.konzern_kunde_id = m.konzern_kunde_id
LEFT JOIN gold.dim_artikel da ON da.artikel_key      = v.artikel_key;

ALTER TABLE gold.fact_verkauf
    ADD PRIMARY KEY (firma_id, beleg_nr, beleg_pos),
    ADD FOREIGN KEY (datum)      REFERENCES gold.dim_datum   (datum),
    ADD FOREIGN KEY (firma_id)   REFERENCES gold.dim_firma   (firma_id),
    ADD FOREIGN KEY (kunde_sk)   REFERENCES gold.dim_kunde   (kunde_sk),
    ADD FOREIGN KEY (artikel_sk) REFERENCES gold.dim_artikel (artikel_sk);

CREATE INDEX ON gold.fact_verkauf (datum);
CREATE INDEX ON gold.fact_verkauf (kunde_sk);
CREATE INDEX ON gold.fact_verkauf (artikel_sk);