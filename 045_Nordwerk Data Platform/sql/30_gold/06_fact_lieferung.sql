-- Delivery fact. Grain: one order line. Shares the dimensions with fact_verkauf.
DROP TABLE IF EXISTS gold.fact_lieferung CASCADE;

CREATE TABLE gold.fact_lieferung AS
SELECT
    a.liefertermin                                      AS datum,
    a.firma_id,
    COALESCE(dk.kunde_sk,   -1)                         AS kunde_sk,
    COALESCE(da.artikel_sk, -1)                         AS artikel_sk,
    a.auftrag_nr,
    a.auftrag_pos,
    a.menge_bestellt_stueck,
    a.menge_geliefert_stueck,
    a.menge_geliefert_stueck >= a.menge_bestellt_stueck AS ist_vollstaendig_geliefert,
    a.ist_storniert,
    a.ist_faellig
FROM silver.auftrag a
LEFT JOIN silver.kunde_map m  ON m.kunde_key         = a.kunde_key
LEFT JOIN gold.dim_kunde   dk ON dk.konzern_kunde_id = m.konzern_kunde_id
LEFT JOIN gold.dim_artikel da ON da.artikel_key      = a.artikel_key;

ALTER TABLE gold.fact_lieferung
    ADD PRIMARY KEY (firma_id, auftrag_nr, auftrag_pos),
    ADD FOREIGN KEY (datum)      REFERENCES gold.dim_datum   (datum),
    ADD FOREIGN KEY (firma_id)   REFERENCES gold.dim_firma   (firma_id),
    ADD FOREIGN KEY (kunde_sk)   REFERENCES gold.dim_kunde   (kunde_sk),
    ADD FOREIGN KEY (artikel_sk) REFERENCES gold.dim_artikel (artikel_sk);