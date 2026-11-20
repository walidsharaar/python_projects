-- Latest result per rule: this is what the "Datenqualität" report page shows
CREATE OR REPLACE VIEW meta.v_dq_aktuell AS
SELECT DISTINCT ON (d.rule_id)
    d.rule_id,
    r.beschreibung,
    r.schwere,
    r.objekt,
    d.fehler_anzahl,
    d.status,
    d.geprueft_am,
    d.run_id
FROM meta.dq_result d
JOIN meta.dq_rule r ON r.rule_id = d.rule_id
ORDER BY d.rule_id, d.geprueft_am DESC;
