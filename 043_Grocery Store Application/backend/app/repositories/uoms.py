def list_uoms(connection):
    return connection.execute("SELECT uom_id AS id, uom_name AS name FROM uom ORDER BY uom_id").fetchall()
