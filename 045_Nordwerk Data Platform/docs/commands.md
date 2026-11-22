# Nordwerk Data Platform – Step-by-Step Instructions (v2)

Every step from an empty computer to the finished data platform, plus the demos for the presentation.
Windows PowerShell, run in the VS Code terminal unless noted otherwise.

> **Short way (everything with one command, once Python and Docker Desktop are installed):**
>
> ```powershell
> cd "D:\Projects\Python\python_projects\045_Nordwerk Data Platform"
> .\run.ps1                 # venv, packages, database, pipeline, health check, lint, 229 tests
> .\run.ps1 demo block      # any manage.py command
> ```
>
> The steps below explain what happens and give every command on its own.

> **Two rules that prevent most problems**
> 1. Before any `python` or `pip` command, the terminal line must start with `(.venv)`.
> 2. Commands go in the **terminal**. Python and SQL code go in the **editor** (a file tab), never in the terminal.

---

## Overview

| Step | What | Result |
|---|---|---|
| 1–6 | Tools, Windows fixes, venv, Docker, `.env`, Git | environment ready |
| 7 | Upgrade an existing v1 database | clean start for v2 |
| 8 | Run the pipeline | sources generated, all layers built and checked |
| 9 | Health check | 14 × OK |
| 10 | Tests | 229 tests passed |
| 11 | Power BI | report with current data |
| 12 | Demo 1: fix errors at the source | DQ01 and DQ04 disappear |
| 13 | Demo 2: bad delivery is stopped | run blocked, report keeps the last good data |
| 14 | Demo 3: a source changes its structure | load stops with a clear message |
| 15 | Demo 4: manual MDM match | one customer, two systems |
| 16 | Connect VS Code to the database | browse tables, run SQL |
| — | Reference: daily start, Docker, single steps, Git, troubleshooting | |

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

✅ Each prints a version number.

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

✅ `git version 2.x`

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
python -m pip --version                    # ✅ path contains \.venv\
```

```powershell
python -m pip install -r requirements.txt   # exact versions: the test data depends on them
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
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      retries: 10

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
logs/
__pycache__/
.pytest_cache/
.env
sql/scratch.sql
**/.pbi/cache.abf
**/.pbi/localSettings.json
```

**Start the database:**

```powershell
docker compose config            # ✅ real values instead of ${...}
docker compose up -d
docker ps                        # ✅ postgres:17 ... 0.0.0.0:5433->5432/tcp
```

**Shared connection helper** `etl/db.py` (function `get_engine(database=None)`, reads `.env`):

```powershell
code etl\db.py
python -m etl.db                 # ✅ PostgreSQL 17.x (Debian ...) on x86_64-pc-linux-gnu
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
git status                                 # ✅ .env must NOT be listed
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

## Step 7 – Upgrade an existing v1 database

v2 changes keys, bronze tables and the rule table. Start with an empty database **once**:

```powershell
docker compose down -v          # ⚠️ deletes the database volume (all data is generated again anyway)
docker compose up -d
docker ps                       # ✅ postgres:17 ... (healthy)  0.0.0.0:5433->5432/tcp
python -m pip install -r requirements.txt
```

> The source database `src_sap_b1` is created automatically by the generator. No `CREATE DATABASE` needed.

---

## Step 8 – Run the pipeline

```powershell
python -m etl.run_pipeline --generate      # first run: create the source data, then build everything
python -m etl.run_pipeline                 # every later run: sources stay as they are
$LASTEXITCODE                              # ✅ 0
```

What happens, in this order:

| Step | What it does |
|---|---|
| Generate | SAP B1 tables, CSV export, Excel file – fixed reference date 20.11.2026, same data on every run |
| Setup | schemas, run log, DQ rules (`sql/00_setup`) |
| MDM | unit mapping, manual customer matches, stable key tables (`sql/10_mdm`) |
| Bronze | append-only history `bronze.*_hist`, view `bronze.*` = latest load, schema check |
| Silver + checks | built in **one transaction**, 13 rules check it **before commit** |
| Gold + checks | built in one transaction, 2 rules check it before commit |

✅ Last line: `Run n finished: success_with_findings (DQ01 ERROR, DQ03 WARN, DQ04 ERROR, DQ05 WARN, DQ06 WARN, DQ08 WARN)`

These six findings are **built into the test data on purpose** – they are the story of the data quality page.
The log is also written to `logs/pipeline.log`.

Run history (VS Code query editor):

```sql
SELECT * FROM meta.v_lauf_historie;
SELECT * FROM meta.v_dq_aktuell ORDER BY rule_id;
```

---

## Step 9 – Health check

Open `sql/checks/healthcheck.sql` in VS Code, connected to `nordwerk_dwh`, run it.
Or in the terminal:

```powershell
Get-Content sql\checks\healthcheck.sql | docker compose exec -T postgres psql -U nordwerk -d nordwerk_dwh
```

Shortest: `python manage.py check` → ✅ `14 of 14 OK`, exit code 0.

✅ 14 rows, all `OK`. The expected numbers never change because the test data is fixed.

---

## Step 10 – Tests

Three levels, chosen by folder:

| Level | Command | Tests | Needs | Time |
|---|---|---|---|---|
| Unit | `python manage.py test unit` | 126 | nothing | ~3 s |
| Unit + database | `python manage.py test db` | 207 | PostgreSQL | ~10 s |
| End-to-end only | `python manage.py test e2e` | 22 | PostgreSQL | ~45 s |
| Everything | `python manage.py test all` | 229 | PostgreSQL | 1–4 min |
| Everything + coverage | `python manage.py test all --cov` | 229 | PostgreSQL | 1–4 min |

✅ `229 passed`. Coverage report: `logs\coverage\index.html` (open in the browser).

Single tests with pytest directly:

```powershell
pytest tests/unit/test_pipeline_logic.py -v           # one file
pytest -k "blocked"                                    # all tests with "blocked" in the name
pytest tests/db/test_dq_rules.py -k DQ14 -v            # one rule
pytest -x --lf                                         # stop at first failure, rerun last failures
```

Code style: `python manage.py lint` → ✅ `All checks passed!`

On GitHub the same runs on every push (`.github/workflows/nordwerk.yml` in the **repository root**):
job 1 = lint + unit tests, job 2 = empty PostgreSQL, pipeline from scratch, health check, database and end-to-end
tests with coverage. Check: GitHub → repository → **Actions** → ✅ both jobs green.

> The database and end-to-end tests rebuild your warehouse with `--generate` and restore it afterwards.

---

## Step 11 – Power BI

Open `powerbi\Nordwerk.pbix` → **Refresh**.
Server `localhost:5433`, database `nordwerk_dwh`, user `nordwerk`, password from `.env`, **Use encrypted connection: off**.

All measures to copy: `docs\powerbi_measures.md`. Connection details: `powerbi\README.md`.
If a gold column the report needs is renamed, `pytest tests/db/test_gold_contract.py` fails first.

---

## Step 12 – Demo 1: fix errors at the source

Shortcut: `python manage.py demo fix` (does all of this step). Afterwards: `python manage.py demo reset`.

The master data team corrects SAP B1; the next run cleans everything up.

```powershell
# DQ01: create the missing customer C99999
docker compose exec postgres psql -U nordwerk -d src_sap_b1 -c "INSERT INTO ocrd (cardcode, cardname, cardtype, city, zipcode, country, createdate, updatedate) VALUES ('C99999', 'Neukunde Muster GmbH', 'C', 'Köln', '50667', 'DE', CURRENT_DATE, CURRENT_DATE);"

# DQ04: give the duplicate item its own EAN
docker compose exec postgres psql -U nordwerk -d src_sap_b1 -c "UPDATE oitm SET codebars = '4012345000016' WHERE itemcode = 'A00045';"

python -m etl.run_pipeline       # ✅ DQ01 OK, DQ04 OK
```

Power BI → Refresh: the data quality page now shows both rules green, "Umsatz ohne Kunde" is 0.

---

## Step 13 – Demo 2: a bad delivery is stopped

Shortcut: `python manage.py demo block` (does all of this step). Afterwards: `python manage.py demo reset`.

Half of the invoice lines go missing in the source (e.g. a broken export):

```powershell
docker compose exec postgres psql -U nordwerk -d src_sap_b1 -c "DELETE FROM inv1 WHERE docentry::int % 2 = 0;"
python -m etl.run_pipeline       # ✅ BLOCKIERT DQ14 Ladevolumen ... 50  →  Run n BLOCKED
$LASTEXITCODE                    # ✅ 1
```

Silver is rolled back, gold is untouched: **Power BI still shows the last good data** (14,910 sales lines).
The blocked run and its DQ results are in `meta.v_lauf_historie` and `meta.v_dq_aktuell`.

---

## Step 14 – Demo 3: a source changes its structure

Shortcut: `python manage.py demo schema` (does all of this step). Afterwards: `python manage.py demo reset`.

```powershell
docker compose exec postgres psql -U nordwerk -d src_sap_b1 -c "ALTER TABLE ocrd DROP COLUMN zipcode;"
python -m etl.run_pipeline       # ✅ SchemaDriftError: bronze.sap_b1_ocrd: source no longer delivers ['zipcode']
```

A **new** column in a source is only logged as a warning and ignored until silver uses it.

**Restore the original data after the demos:**

```powershell
python -m etl.run_pipeline --generate    # ✅ success_with_findings, health check 14 × OK
```

---

## Step 15 – Demo 4: manual MDM match

Shortcut: `python manage.py demo mdm` (does all of this step). Afterwards: `python manage.py demo reset`.

Company B has a typo in one postcode (58974 instead of 58947), so the automatic match (name + postcode) fails.
The MDM team adds one row to `mdm.kunde_override` (see `sql/10_mdm/02_kunde_override.sql`):

```sql
SELECT kunde_key, konzern_kunde_id, match_methode, match_grund
FROM silver.kunde_map WHERE kunde_key IN ('A-C10151', 'B-K-4011');
-- ✅ both rows: the same konzern_kunde_id, B-K-4011 with match_methode 'manuell'
```

Without that row, rule **DQ13** reports the pair as a possible duplicate. Customer IDs (`GK…`) and surrogate keys
are stored in `mdm` and stay the same on every run – a new customer gets a new number, nobody else's changes.

---

## Step 16 – Connect VS Code to the database

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
| Data warehouse | `nordwerk_dwh` (schemas `bronze`, `mdm`, `silver`, `gold`, `meta`) |
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
| `docker compose exec postgres psql -U nordwerk -d nordwerk_dwh` | interactive SQL (`\dt silver.*`, `\d gold.fact_verkauf`, `\q`) |

## Single steps

| Step | Command |
|---|---|
| Source A / B / Excel | `python -m generator.company_a_b1` · `company_b_csv` · `sustainability_excel` |
| Setup / MDM | `python -m etl.run_sql sql/00_setup` · `python -m etl.run_sql sql/10_mdm` |
| Bronze only | `python -m etl.load_bronze` |
| Check the current data (changes nothing) | `python -m etl.run_dq` |
| Everything | `python -m etl.run_pipeline [--generate]` |
| Health check | `python manage.py check` |
| Runs and data quality | `python manage.py status` |
| Tests | `python manage.py test unit\|db\|e2e\|all [--cov]` |
| Demos | `python manage.py demo fix\|block\|schema\|mdm\|reset` |

> Silver and gold are only built by `run_pipeline`: they are always built **and checked** together.

## Git

```powershell
git status
git add .
git commit -m "045: short description"
git push
git ls-files                    # .env must NOT be listed
```

## Project structure

```
python_projects/
├── .github/workflows/nordwerk.yml      CI: tests on every push
└── 045_Nordwerk Data Platform/
    ├── .env / .env.example / .gitignore
    ├── docker-compose.yml
    ├── manage.py / run.ps1 / Makefile    one entry point for everything
    ├── requirements.txt / pyproject.toml
    ├── data/landing/                   (generated, not in Git)
    ├── logs/                           (pipeline.log, not in Git)
    ├── docs/commands.md
    ├── generator/                      common.py, company_a_b1.py, company_b_csv.py, sustainability_excel.py
    ├── etl/                            db, runlog, run_sql, load_bronze, run_dq, run_pipeline, healthcheck
    ├── sql/
    │   ├── 00_setup/   schemas, run log, DQ tables, rules, views
    │   ├── 10_mdm/     unit mapping, manual matches, stable keys
    │   ├── 20_silver/  01_firma … 06_auftrag
    │   ├── 30_gold/    01_dim_firma … 06_fact_lieferung
    │   └── checks/     healthcheck.sql
    ├── tests/                          unit/ (no database), db/ (rolled back), e2e/ (real pipeline runs)
    └── powerbi/                        Nordwerk.pbix, README.md
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `running scripts is disabled on this system` | PowerShell execution policy | Step 2.1 |
| `git --version` opens Notepad | empty file `C:\Windows\System32\git` | Step 2.2 |
| `ensurepip ... non-zero exit status` | venv created while a venv was active | `deactivate`, `Remove-Item -Recurse -Force .venv`, create again |
| lines start with `>>` | unclosed quote, or code pasted into the terminal | `Ctrl + C` |
| **German** password error from Postgres | Windows PostgreSQL on 5432 | use port **5433** |
| `No module named 'etl'` | script started as a file path | `python -m etl.run_pipeline` from the project folder |
| `Run n BLOCKED` | a blocking rule failed | expected in Demo 2; otherwise see `meta.v_dq_aktuell` |
| `SchemaDriftError` | a source column is missing | expected in Demo 3; otherwise adapt the source or silver |
| `column ... does not exist` / key errors after the upgrade | old v1 database | Step 7 (`docker compose down -v`) |
| health check numbers differ | other package versions | `python -m pip install -r requirements.txt`, run with `--generate` |
| `Run n BLOCKED ... DQ14` right after the upgrade | v1 data in the run log | Step 7 |
