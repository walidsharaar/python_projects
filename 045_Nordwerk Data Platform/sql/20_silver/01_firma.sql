-- Group companies. Small and stable, so we maintain it by hand.
DROP TABLE IF EXISTS silver.firma CASCADE;

CREATE TABLE silver.firma (
    firma_id    TEXT PRIMARY KEY,
    firma_name  TEXT NOT NULL,
    quellsystem TEXT NOT NULL
);

INSERT INTO silver.firma (firma_id, firma_name, quellsystem) VALUES
    ('A', 'Nordwerk Haushalt GmbH',   'sap_b1'),
    ('B', 'Nordwerk Beutel GmbH',     'erp_b'),
    ('C', 'Nordwerk Handschuhe GmbH', 'api_c');   -- source follows later
