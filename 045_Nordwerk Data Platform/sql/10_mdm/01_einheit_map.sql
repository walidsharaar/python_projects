-- One place for the unit vocabulary: every source unit -> one group unit.
-- A new unit in a source = one new row here, no code change.
CREATE TABLE IF NOT EXISTS mdm.einheit_map (
    quellsystem   TEXT NOT NULL,
    quell_einheit TEXT NOT NULL,
    einheit       TEXT NOT NULL CHECK (einheit IN ('STK', 'KRT', 'PAL')),
    PRIMARY KEY (quellsystem, quell_einheit)
);

INSERT INTO mdm.einheit_map (quellsystem, quell_einheit, einheit) VALUES
    ('sap_b1', 'Stk',     'STK'),
    ('sap_b1', 'Krt',     'KRT'),
    ('sap_b1', 'Pal',     'PAL'),
    ('erp_b',  'Rolle',   'STK'),
    ('erp_b',  'Karton',  'KRT'),
    ('erp_b',  'Palette', 'PAL')
ON CONFLICT (quellsystem, quell_einheit) DO UPDATE SET einheit = EXCLUDED.einheit;
