-- Manual customer matches by the master data team.
-- Automatic matching uses the normalised name + postcode. When that fails (typo, rename),
-- MDM links the source customer to the customer it really is. An override always wins.
CREATE TABLE IF NOT EXISTS mdm.kunde_override (
    kunde_key      TEXT PRIMARY KEY,           -- source customer, e.g. 'B-K-4011'
    ziel_kunde_key TEXT NOT NULL,              -- the customer it is the same as, e.g. 'A-C10151'
    grund          TEXT NOT NULL,
    angelegt_von   TEXT NOT NULL,
    angelegt_am    DATE NOT NULL DEFAULT CURRENT_DATE
);

INSERT INTO mdm.kunde_override (kunde_key, ziel_kunde_key, grund, angelegt_von, angelegt_am) VALUES
    ('B-K-4011', 'A-C10151', 'PLZ-Tippfehler im Kundenstamm Gesellschaft B (58974 statt 58947)', 'MDM', DATE '2026-11-18')
ON CONFLICT (kunde_key) DO NOTHING;
