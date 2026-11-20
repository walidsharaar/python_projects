# Nordwerk Data Platform – Step-by-Step Instructions

Every step from an empty computer to the finished data platform, in the order the project was built.
Each step lists what it builds, the files involved, the commands, and how to check the result.

Windows PowerShell, run in the VS Code terminal unless noted otherwise.

> **Two rules that prevent most problems**
> 1. Before any `python` or `pip` command, the terminal line must start with `(.venv)`.
> 2. Commands go in the **terminal**. Python and SQL code go in the **editor** (a file tab), never in the terminal.
>
> To create or open a file in the editor: `code <path\filename>`, paste the content, save with `Ctrl + S`.
> The full content of every file is in the repository.

---

## Overview

| Step | What | Result |
|---|---|---|
| 1 | Install and check the tools | Python, Docker, Git, VS Code ready |
| 2 | Windows fixes | venv activation and `git` work |
| 3 | Project folder and Python environment | `.venv`, packages, folders |
| 4 | Database in Docker | PostgreSQL 17 on port 5433 |
| 5 | Credentials in `.env` and shared DB helper | `etl/db.py` |
| 6 | Git and GitHub | project in the monorepo |
| 7 | Source A: SAP Business One | database `src_sap_b1` |
| 8 | Source B: CSV export | `data/landing/company_b` |
| 9 | Source C: Excel file | `data/landing/sustainability` |
| 10 | Bronze layer | 11 raw tables, run log |
| 11 | Silver layer | 7 clean tables, MDM mapping |
| 12 | Data quality checks | 12 rules, result log |
| 13 | Gold layer | star schema, 2 fact tables |
| 14 | Pipeline: one command | `etl/run_pipeline.py` |
| 15 | Health check | `sql/checks/healthcheck.sql` |
| 16 | Demo: fix errors at the source | `Data quality: success` |
| 17 | Connect VS Code to the database | browse tables, run SQL |
| — | Daily start routine, Docker, Git, troubleshooting | reference at the end |

---

## Step 1 – Install and check the tools

Install: **Python 3.12**, **Docker Desktop**, **Git**, **VS Code**.
VS Code extensions: **Python** (Microsoft) and **PostgreSQL** (Microsoft, `ms-ossdata.vscode-pgsql`).

Check, one command at a time:

```powershell
python --version
docker --version
git --version
```

 Each prints a version number.

---

## Step 2 – Windows fixes (only if needed)

**2.1 PowerShell blocks `.venv\Scripts\activate`** ("running scripts is disabled on this system"):

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**2.2 `git --version` prints nothing or opens Notepad** (an empty stray file named `git`):

```powershell
Get-Command git -All | Format-List Name, Source          # shows C:\WINDOWS\system32\git first
Get-Item C:\WINDOWS\system32\git | Format-List Length     # Length 0 = empty leftover, safe to rename
```

Open an **administrator** window (Start → type PowerShell → right-click → Run as administrator):

```powershell
Rename-Item C:\WINDOWS\system32\git git.bak               # in PowerShell
```
```cmd
ren C:\Windows\System32\git git.bak                       :: if the window is Command Prompt (cmd)
```

Back in VS Code, open a **new** terminal:

```powershell
git --version
```

 `git version 2.x`

---

## Step 3 – Project folder and Python environment

```powershell
cd D:\Projects\Python\python_projects
mkdir "045_Nordwerk Data Platform"
cd "045_Nordwerk Data Platform"
code .
```

In the VS Code terminal:

```powershell
python -m venv .venv                       # create ONCE
.venv\Scripts\activate                     # in every new terminal
python -m pip --version                    #  path contains \.venv\
```

```powershell
python -m pip install pandas faker sqlalchemy "psycopg[binary]" python-dotenv openpyxl
python -m pip freeze | Set-Content -Encoding utf8 requirements.txt
mkdir generator, etl, sql, data, docs
```

Tell VS Code to use the project's Python: `Ctrl + Shift + P` → **Python: Select Interpreter** →
`...\045_Nordwerk Data Platform\.venv\Scripts\python.exe`

> Never run `python -m venv .venv` while `(.venv)` is active: it breaks the venv.
> Never write `pip freeze > requirements.txt`: `>` saves UTF-16, which Git shows as binary.

---

## Step 4 – Database in Docker

Start **Docker Desktop** and wait for "Engine running".

Create `docker-compose.yml` in the project folder:

```powershell
code docker-compose.yml
```

```yaml
services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "${POSTGRES_PORT}:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

> Port **5433** on the PC, because a local Windows PostgreSQL 18 already uses 5432.
> Check with `Get-Service *postgres*`.

The values come from `.env` (Step 5). Start the database after Step 5.

---

## Step 5 – Credentials in `.env` and shared DB helper

**`.env`** (real values, stays on your PC):

```powershell
code .env
```
```
POSTGRES_USER=nordwerk
POSTGRES_PASSWORD=<your-password>
POSTGRES_DB=nordwerk_dwh
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
```

**`.env.example`** (same names, dummy password, goes to GitHub):

```powershell
code .env.example
```
```
POSTGRES_USER=nordwerk
POSTGRES_PASSWORD=change-me
POSTGRES_DB=nordwerk_dwh
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
```

**`.gitignore`**:

```powershell
code .gitignore
```
```
.venv/
data/
__pycache__/
.env
sql/scratch.sql
```

**Start the database:**

```powershell
docker compose config            #  real values instead of ${...}
docker compose up -d
docker ps                        #  postgres:17 ... 0.0.0.0:5433->5432/tcp
```

**Shared connection helper** `etl/db.py` (function `get_engine(database=None)`, reads `.env`):

```powershell
code etl\db.py
python -m etl.db                 #  PostgreSQL 17.x (Debian ...) on x86_64-pc-linux-gnu
```

> If the password is changed later: `docker compose down -v` then `docker compose up -d`
> (Postgres sets the password only on a fresh volume; this deletes all data).

---

## Step 6 – Git and GitHub (monorepo)

The project is one folder in the existing repository `walidsharaar/python_projects`.
There must be **no** separate `.git` inside the project folder.

Once per computer:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
```

If `git init` was run inside the project folder by mistake:

```powershell
Remove-Item -Recurse -Force .git           # removes only the inner repository, not your files
```

First commit:

```powershell
git add .
git status                                 #  .env must NOT be listed
git commit -m "045 Nordwerk Data Platform: project setup"
git push
```

From now on, after every step:

```powershell
git add .
git commit -m "045: <what changed>"
git push
```

---

## Step 7 – Source A: SAP Business One (Company A, Nordwerk Haushalt GmbH)

Create the source database that plays Company A's SAP B1 server:

```powershell
docker compose exec postgres psql -U nordwerk -d nordwerk_dwh -c "CREATE DATABASE src_sap_b1;"
```

 `CREATE DATABASE`

File: `generator/company_a_b1.py`
Builds the B1 tables (lowercase names): `ocrd` customers, `oitb` item groups, `oitm` items,
`ordr`/`rdr1` orders, `oinv`/`inv1` invoices, with deliberate data problems
(missing EAN, duplicate EAN, unknown customer C99999, intercompany customers, duplicate customer,
partial deliveries).

```powershell
code generator\company_a_b1.py
python -m generator.company_a_b1
```


```
ocrd: 203 | oitb: 3 | oitm: 45 | ordr: 2000 | rdr1: 6050 | oinv: 1939 | inv1: 5865
```

Checks:

```powershell
docker compose exec postgres psql -U nordwerk -d src_sap_b1 -c "SELECT cardcode, cardname, city FROM ocrd LIMIT 5;"
docker compose exec postgres psql -U nordwerk -d src_sap_b1 -c "SELECT COUNT(*) AS items, COUNT(codebars) AS with_ean, COUNT(DISTINCT codebars) AS distinct_ean FROM oitm;"
docker compose exec postgres psql -U nordwerk -d src_sap_b1 -c "SELECT COUNT(*) AS orphan_orders FROM ordr o LEFT JOIN ocrd c ON c.cardcode = o.cardcode WHERE c.cardcode IS NULL;"
docker compose exec postgres psql -U nordwerk -d src_sap_b1 -c "SELECT COUNT(*) AS mismatches FROM ordr o JOIN (SELECT docentry, SUM(linetotal) AS s FROM rdr1 GROUP BY docentry) l ON l.docentry = o.docentry WHERE ABS(o.doctotal - l.s) > 0.01;"
docker compose exec postgres psql -U nordwerk -d src_sap_b1 -c "SELECT SUM(r.quantity) AS ordered, SUM(i.quantity) AS invoiced, ROUND(100.0 * SUM(i.quantity) / SUM(r.quantity), 2) AS delivery_rate_pct FROM inv1 i JOIN rdr1 r ON r.docentry = i.baseentry AND r.linenum = i.baseline;"
```

 `45 | 41 | 40` items · about 27 orphan orders · `0` mismatches · delivery rate about 97 %

> Always run scripts as modules from the project folder: `python -m generator.company_a_b1`,
> not `python generator\company_a_b1.py` (otherwise `ModuleNotFoundError: No module named 'etl'`).

---

## Step 8 – Source B: CSV export (Company B, Nordwerk Beutel GmbH)

File: `generator/company_b_csv.py`
Writes `kunden.csv`, `artikel.csv`, `verkaeufe.csv` like a German ERP export:
`;` separator, decimal comma, `dd.mm.yyyy`, Windows-1252. 60 shops are also Company A customers
under different numbers; credit notes (GS) are negative; about 1 % duplicate rows.

```powershell
code generator\company_b_csv.py
python -m generator.company_b_csv
```

 `kunden.csv: 141` · `artikel.csv: 12` · `verkaeufe.csv: 2972`

Check (read correctly with pandas):

```powershell
python -c "import pandas as pd; df = pd.read_csv('data/landing/company_b/verkaeufe.csv', sep=';', decimal=',', encoding='cp1252'); print(df.head()); print('duplicate rows:', df.duplicated().sum())"
```

 `duplicate rows: 29`

> In VS Code the file shows `M�llbeutel`: bottom-right status bar → **UTF-8** → **Reopen with Encoding** → **Western (Windows 1252)**.

---

## Step 9 – Source C: Excel file (sustainability team)

File: `generator/sustainability_excel.py`
Writes `rezyklatanteile.xlsx`: title rows above the table (headers in row 4), percentages partly
typed as text (`"45 %"`), an unknown item `A09999`, three items with a second row valid from 2026.

```powershell
code generator\sustainability_excel.py
python -m generator.sustainability_excel
```

 `rezyklatanteile.xlsx: 61 rows`

Check:

```powershell
python -c "import pandas as pd; df = pd.read_excel('data/landing/sustainability/rezyklatanteile.xlsx', header=3); print(df.head(8)); print(df['Rezyklatanteil'].map(type).value_counts())"
```

> Generator order matters: A first, then B and Excel (they read Company A's data).
> All three set their random seed inside `main()`, so every run produces the same data.

---

## Step 10 – Bronze layer

Copies every source 1:1 into `nordwerk_dwh.bronze`, all values as text, with
`_source_system`, `_source_object`, `_run_id`, `_load_ts`. Every run is logged in `meta`.

Files:
- `sql/00_setup/01_schemas.sql` – schemas `bronze`, `silver`, `gold`, `meta`; tables `meta.etl_run`, `meta.load_log`
- `etl/run_sql.py` – runs a `.sql` file or all files of a folder in name order
- `etl/load_bronze.py` – extract (SQL / CSV / Excel) and load into bronze

```powershell
mkdir sql\00_setup
code sql\00_setup\01_schemas.sql
code etl\run_sql.py
python -m etl.run_sql sql/00_setup              #  ok: sql\00_setup\01_schemas.sql

code etl\load_bronze.py
python -m etl.load_bronze
```

 11 tables, `Run 1 finished: success`

Checks:

```powershell
docker compose exec postgres psql -U nordwerk -d nordwerk_dwh -c "SELECT run_id, layer, status, started_at, finished_at FROM meta.etl_run;"
docker compose exec postgres psql -U nordwerk -d nordwerk_dwh -c "SELECT belegdatum, menge, einzelpreis, _source_system, _run_id FROM bronze.erp_b_verkaeufe LIMIT 3;"
```

 `success` · raw values like `19.08.2026` and `2639,42` (still text)

---

## Step 11 – Silver layer

Cleans, types and harmonises all sources in SQL. Every file does `DROP` + `CREATE` (idempotent).

| File | Builds |
|---|---|
| `sql/20_silver/01_firma.sql` | group companies A, B, C |
| `sql/20_silver/02_artikel.sql` | items of A + B, one unit vocabulary STK/KRT/PAL |
| `sql/20_silver/03_kunde.sql` | `silver.norm_name()`, customers, MDM mapping `kunde_map`, intercompany flag |
| `sql/20_silver/04_verkauf.sql` | all invoice lines A + B, deduplicated, in pieces, with cost |
| `sql/20_silver/05_rezyklat.sql` | recycled share with `gueltig_ab` / `gueltig_bis` |
| `sql/20_silver/06_auftrag.sql` | order lines of A with delivered quantity (for the delivery rate) |

```powershell
mkdir sql\20_silver
code sql\20_silver\01_firma.sql
code sql\20_silver\02_artikel.sql
code sql\20_silver\03_kunde.sql
code sql\20_silver\04_verkauf.sql
code sql\20_silver\05_rezyklat.sql
code sql\20_silver\06_auftrag.sql
python -m etl.run_sql sql/20_silver
```

 6 × `ok`

Checks:

```powershell
docker compose exec postgres psql -U nordwerk -d nordwerk_dwh -c "SELECT firma_id, einheit, COUNT(*) AS artikel, COUNT(ean) AS mit_ean FROM silver.artikel GROUP BY firma_id, einheit ORDER BY 1, 2;"
docker compose exec postgres psql -U nordwerk -d nordwerk_dwh -c "SELECT COUNT(*) AS quell_kunden, COUNT(DISTINCT konzern_kunde_id) AS konzern_kunden FROM silver.kunde_map;"
docker compose exec postgres psql -U nordwerk -d nordwerk_dwh -c "SELECT firma_id, kundennr, kundenname, konzern_firma_id FROM silver.kunde WHERE ist_konzern;"
docker compose exec postgres psql -U nordwerk -d nordwerk_dwh -c "SELECT (SELECT COUNT(*) FROM bronze.erp_b_verkaeufe) AS bronze, (SELECT COUNT(*) FROM silver.verkauf WHERE firma_id = 'B') AS silver;"
docker compose exec postgres psql -U nordwerk -d nordwerk_dwh -c "SELECT firma_id, SUM(umsatz_netto) AS umsatz, ROUND(100 * SUM(umsatz_netto - kosten) / SUM(umsatz_netto), 1) AS db_prozent FROM silver.verkauf GROUP BY firma_id;"
docker compose exec postgres psql -U nordwerk -d nordwerk_dwh -c "SELECT COUNT(*) AS zeilen, COUNT(rezyklat_pct) AS mit_zahl, COUNT(*) FILTER (WHERE NOT artikel_bekannt) AS unbekannte_artikel FROM silver.rezyklat;"
```

 57 items · 344 → 283 group customers · 3 intercompany customers · `2972 | 2943` · DB % about 35 / 32 · `61 | 61 | 1`

---

## Step 12 – Data quality checks

Rules are **data**: each rule is a SQL query returning the number of rows that break it (0 = OK).
Results go to `meta.dq_result`. If an **ERROR** rule finds problems, the run is `failed`.

| File | Content |
|---|---|
| `sql/40_dq/01_dq_tables.sql` | `meta.dq_rule`, `meta.dq_result` |
| `sql/40_dq/02_dq_rules.sql` | rules DQ01–DQ11 (upsert with `ON CONFLICT`) |
| `sql/40_dq/03_dq_views.sql` | view `meta.v_dq_aktuell` (latest result per rule) |
| `sql/40_dq/04_dq_rules_gold.sql` | rule DQ12 (revenue silver = gold), added in Step 13 |
| `etl/run_dq.py` | runs all active rules, returns `success` / `failed` |

```powershell
mkdir sql\40_dq
code sql\40_dq\01_dq_tables.sql
code sql\40_dq\02_dq_rules.sql
code sql\40_dq\03_dq_views.sql
python -m etl.run_sql sql/40_dq

code etl\run_dq.py
python -m etl.run_dq
```

 Expected with the test data:

```
ERROR DQ01 Verkauf mit unbekanntem Kunden: 90
ERROR DQ04 EAN mehrfach vergeben: 1
WARN  DQ03 7 · DQ05 1 · DQ06 1 · DQ08 29
OK    all others
DQ run …: failed (2 rule(s) with status ERROR)
```

`failed` here means the **data** has problems, not the code.

---

## Step 13 – Gold layer (star schema)

| File | Builds |
|---|---|
| `sql/30_gold/01_dim_firma.sql` | company dimension |
| `sql/30_gold/02_dim_datum.sql` | calendar, German month and weekday names, ISO week |
| `sql/30_gold/03_dim_kunde.sql` | one row per group customer, golden-record name, `-1` = Unbekannter Kunde |
| `sql/30_gold/04_dim_artikel.sql` | items with current recycled share, `-1` = Unbekannter Artikel |
| `sql/30_gold/05_fact_verkauf.sql` | grain: invoice line; surrogate keys, Deckungsbeitrag, intercompany flag, FKs, indexes |
| `sql/30_gold/06_fact_lieferung.sql` | grain: order line; delivered vs. ordered pieces |

```powershell
mkdir sql\30_gold
code sql\30_gold\01_dim_firma.sql
code sql\30_gold\02_dim_datum.sql
code sql\30_gold\03_dim_kunde.sql
code sql\30_gold\04_dim_artikel.sql
code sql\30_gold\05_fact_verkauf.sql
code sql\30_gold\06_fact_lieferung.sql
python -m etl.run_sql sql/30_gold

code sql\40_dq\04_dq_rules_gold.sql
python -m etl.run_sql sql/40_dq
python -m etl.run_dq                        #  12 rules, DQ12 OK
```

Checks (VS Code query editor):

```sql
SELECT COUNT(*), MIN(datum), MAX(datum) FROM gold.dim_datum;
SELECT COUNT(*) FROM gold.dim_kunde;                                   -- 284
SELECT COUNT(*), SUM(umsatz_netto) FROM gold.fact_verkauf WHERE kunde_sk = -1;   -- 90 lines

SELECT COALESCE(f.firma_id, 'Konzern gesamt')                    AS firma,
       SUM(f.umsatz_netto)                                       AS umsatz_einzelgesellschaft,
       SUM(f.umsatz_netto) FILTER (WHERE f.ist_intercompany)     AS davon_intercompany,
       SUM(f.umsatz_netto) FILTER (WHERE NOT f.ist_intercompany) AS umsatz_konzern
FROM gold.fact_verkauf f
GROUP BY ROLLUP (f.firma_id)
ORDER BY f.firma_id NULLS LAST;

SELECT ROUND(100.0 * SUM(menge_geliefert_stueck) / SUM(menge_bestellt_stueck), 2) AS mengen_lieferquote,
       ROUND(100.0 * AVG(CASE WHEN ist_vollstaendig_geliefert THEN 1 ELSE 0 END), 2) AS positions_lieferquote
FROM gold.fact_lieferung
WHERE ist_faellig AND NOT ist_storniert;
```

---

## Step 14 – Pipeline: everything with one command

File: `etl/run_pipeline.py`
Order: (generate) → setup → bronze → silver → gold → DQ rules → DQ checks.
Strategy "publish and flag": gold is always updated; exit code 1 if an ERROR rule fails.

```powershell
code etl\run_pipeline.py
python -m etl.run_pipeline --generate       # new source data + all layers (~25 s)
$LASTEXITCODE                               # 1 with the test data (expected)
python -m etl.run_pipeline                  # all layers from the existing sources
python -m etl.run_pipeline --help
```

Reproducibility check: run `--generate` twice. `rdr1 6050`, `inv1 5865`, `verkaeufe.csv 2972`,
`DQ01 90`, `DQ08 29` must be identical both times.

> If the numbers differ between runs: the random seed was set at import time.
> `Faker.seed(SEED)` / `random.seed(SEED)` belong at the start of each generator's `main()`.

---

## Step 15 – Health check

File: `sql/checks/healthcheck.sql` – 9 expected-value checks across all layers.

```powershell
mkdir sql\checks
code sql\checks\healthcheck.sql
```

Run it in the VS Code query editor (connected to `nordwerk_dwh`).
 All 9 rows `ok = true` (with the original test data).

---

## Step 16 – Demo: fix errors at the source

The master data team corrects SAP B1; the next pipeline run cleans everything up.

```powershell
# fix DQ01: create the missing customer
docker compose exec postgres psql -U nordwerk -d src_sap_b1 -c "INSERT INTO ocrd (cardcode, cardname, cardtype, city, zipcode, country, createdate, updatedate) VALUES ('C99999', 'Neukunde Muster GmbH', 'C', 'Köln', '50667', 'DE', CURRENT_DATE, CURRENT_DATE);"

# fix DQ04: give the duplicate item its own EAN
docker compose exec postgres psql -U nordwerk -d src_sap_b1 -c "UPDATE oitm SET codebars = '4012345000016' WHERE itemcode = (SELECT MAX(itemcode) FROM oitm WHERE codebars = (SELECT codebars FROM oitm WHERE codebars IS NOT NULL GROUP BY codebars HAVING COUNT(*) > 1));"

# run WITHOUT --generate
python -m etl.run_pipeline                  #  Data quality: success
$LASTEXITCODE                               #  0
```

History of a rule (VS Code query editor):

```sql
SELECT d.run_id, r.started_at, d.status, d.fehler_anzahl
FROM meta.dq_result d JOIN meta.etl_run r ON r.run_id = d.run_id
WHERE d.rule_id = 'DQ01' ORDER BY d.run_id;
```

Restore the original test data afterwards:

```powershell
python -m etl.run_pipeline --generate
```

---

## Step 17 – Connect VS Code to the database

Elephant icon (PostgreSQL extension) → **Add Connection**:

| Field | Value |
|---|---|
| Server name | `localhost` |
| Authentication | Password |
| User name | `nordwerk` |
| Password | from `.env` |
| Database name | `nordwerk_dwh` |
| Connection name | `Nordwerk (Docker)` |
| **Advanced → Port** | **`5433`** |

Or tab **Connection String**: `postgresql://nordwerk:<password>@localhost:5433/nordwerk_dwh`

**Test Connection** → **Save & Connect**.
Right-click a table → **Select Top 1000**. Right-click the database → **New Query**.

> A **German** error message ("Passwort-Authentifizierung … fehlgeschlagen") means you reached the
> Windows PostgreSQL on port 5432. Set the port to 5433.

---

# Reference

## Daily start routine

1. Start **Docker Desktop**, wait for "Engine running".
2. In VS Code:

```powershell
cd "D:\Projects\Python\python_projects\045_Nordwerk Data Platform"
.venv\Scripts\activate
docker compose up -d
```

## Connection details

| | Value |
|---|---|
| Host / Port | `localhost` / **`5433`** |
| User | `nordwerk` |
| Password | see `.env` |
| Data warehouse | `nordwerk_dwh` (schemas `bronze`, `silver`, `gold`, `meta`) |
| Company A source | `src_sap_b1` |

## Docker

| Command | What it does |
|---|---|
| `docker compose up -d` | start the database |
| `docker ps` | list running containers |
| `docker compose stop` | stop, keep the data |
| `docker compose down` | remove the container, keep the data |
| `docker compose down -v` | remove the container **and delete all data** ⚠️ |
| `docker compose logs postgres` | database log |
| `docker compose config` | configuration with values from `.env` |
| `docker compose exec postgres psql -U nordwerk -d nordwerk_dwh` | interactive SQL (`\dt silver.*`, `\d gold.fact_verkauf`, `\q`) |

## Single pipeline steps

| Step | Command |
|---|---|
| Source A | `python -m generator.company_a_b1` |
| Source B | `python -m generator.company_b_csv` |
| Source Excel | `python -m generator.sustainability_excel` |
| Setup | `python -m etl.run_sql sql/00_setup` |
| Bronze | `python -m etl.load_bronze` |
| Silver | `python -m etl.run_sql sql/20_silver` |
| Gold | `python -m etl.run_sql sql/30_gold` |
| DQ rules | `python -m etl.run_sql sql/40_dq` |
| DQ checks | `python -m etl.run_dq` |
| One SQL file | `python -m etl.run_sql sql/30_gold/05_fact_verkauf.sql` |
| Everything | `python -m etl.run_pipeline [--generate]` |

## Git

```powershell
git status
git add .
git commit -m "045: short description"
git push
git log --oneline -5
git show --stat HEAD
git ls-files                    # .env must NOT be listed
```

## Project structure

```
045_Nordwerk Data Platform/
├── .env / .env.example / .gitignore
├── docker-compose.yml
├── requirements.txt
├── data/landing/               (generated, not in Git)
├── docs/
├── generator/
│   ├── company_a_b1.py
│   ├── company_b_csv.py
│   └── sustainability_excel.py
├── etl/
│   ├── db.py
│   ├── run_sql.py
│   ├── load_bronze.py
│   ├── run_dq.py
│   └── run_pipeline.py
└── sql/
    ├── 00_setup/   01_schemas.sql
    ├── 20_silver/  01_firma … 06_auftrag
    ├── 30_gold/    01_dim_firma … 06_fact_lieferung
    ├── 40_dq/      01_dq_tables … 04_dq_rules_gold
    └── checks/     healthcheck.sql
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `running scripts is disabled on this system` | PowerShell execution policy | Step 2.1 |
| `git --version` opens Notepad | empty file `C:\Windows\System32\git` | Step 2.2 |
| `ensurepip ... non-zero exit status` | venv created while a venv was active | `deactivate`, `Remove-Item -Recurse -Force .venv`, create again |
| lines start with `>>` | unclosed quote, or code pasted into the terminal | `Ctrl + C` |
| `no configuration file provided` | `docker-compose.yml` missing or in a subfolder | `Get-ChildItem -Name`, create it in the project folder |
| **German** password error from Postgres | Windows PostgreSQL on 5432 | use port **5433** |
| `relation "x" does not exist` | table not created, or file not saved | `Ctrl + S`, run the step again |
| `No module named 'dotenv'` | venv not active | `.venv\Scripts\activate`, `python -m pip install python-dotenv` |
| `No module named 'etl'` | script started as a file path | `python -m generator.company_a_b1` from the project folder |
| `does not have a commit checked out` | inner `.git` in the project folder | `Remove-Item -Recurse -Force .git` |
| `IndentationError` / `'return' outside function` | wrong indentation | `def` at the left edge, body 4 spaces |
| numbers differ between runs | seed set at import time | seeds in `main()` |
| `requirements.txt` shown as binary | written with `>` (UTF-16) | `pip freeze \| Set-Content -Encoding utf8 requirements.txt` |
| `UPDATE 0` in the demo | nothing left to fix | expected after the first update |
| `Data quality: failed` | an ERROR rule found a problem in the data | expected with the test data, see `meta.v_dq_aktuell` |
