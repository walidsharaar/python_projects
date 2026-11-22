# Power BI report

`Nordwerk.pbix` – the report, built in Power BI Desktop. It reads only the gold layer and `meta.v_dq_aktuell`.

| Setting | Value |
|---|---|
| Connector | PostgreSQL database |
| Server | `localhost:5433` |
| Database | `nordwerk_dwh` |
| Data connectivity mode | Import |
| Login | Database → user and password from `.env`; "Use encrypted connection" off |

Pages (German and English): Übersicht · Kunden · Lieferquote · Datenqualität.
All measures with descriptions: [`docs/powerbi_measures.md`](../docs/powerbi_measures.md).
The columns the report needs are protected by a test: `tests/db/test_gold_contract.py` (`REPORT_CONTRACT`).

Refresh after every pipeline run: open the file → **Refresh**.
