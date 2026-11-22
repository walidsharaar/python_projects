-- Stable keys. Once a group customer or an item has a key, it keeps it on every rebuild,
-- whatever else changes. Reports, bookmarks and other systems can rely on them.
CREATE SEQUENCE IF NOT EXISTS mdm.konzern_kunde_nr;

CREATE TABLE IF NOT EXISTS mdm.konzern_kunde (
    match_key        TEXT PRIMARY KEY,         -- normalised name + '|' + postcode
    konzern_kunde_id TEXT NOT NULL UNIQUE,     -- 'GK00001', never reused
    angelegt_am      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS mdm.artikel_nr;

CREATE TABLE IF NOT EXISTS mdm.artikel_schluessel (
    artikel_key TEXT PRIMARY KEY,              -- 'A-A00001', 'B-MB-0001'
    artikel_sk  INT  NOT NULL UNIQUE,
    angelegt_am TIMESTAMPTZ NOT NULL DEFAULT now()
);
