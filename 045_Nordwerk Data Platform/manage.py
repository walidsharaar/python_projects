"""
Nordwerk Data Platform - one entry point for everything.

    python manage.py showcase          # the whole thing: database, pipeline, checks, tests
    python manage.py setup             # .env + start PostgreSQL in Docker and wait until it is ready
    python manage.py run [--generate]  # pipeline (--generate = create the source data first)
    python manage.py check             # health check: 14 target values
    python manage.py status            # last runs and current data quality
    python manage.py test [unit|db|e2e|all] [--cov]
    python manage.py lint              # code style (ruff)
    python manage.py demo fix|block|schema|mdm|reset

Every command returns exit code 0 on success, so it can be used in scripts and CI.
"""
import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable



def banner(text: str) -> None:
    print(f"\n{'=' * 70}\n  {text}\n{'=' * 70}", flush=True)


def sh(*cmd, check=True) -> int:
    """Run a command in the project folder and stream its output."""
    print(f"$ {' '.join(str(c) for c in cmd)}", flush=True)
    code = subprocess.call([str(c) for c in cmd], cwd=ROOT)
    if check and code != 0:
        sys.exit(code)
    return code


def ensure_env() -> None:
    env, example = ROOT / ".env", ROOT / ".env.example"
    if not env.exists():
        shutil.copy(example, env)
        print("Created .env from .env.example - set POSTGRES_PASSWORD there for anything but a local demo.")


def wait_for_db(timeout: int = 60) -> None:
    from etl.db import get_engine
    deadline = time.time() + timeout
    while True:
        try:
            with get_engine("postgres").connect():
                print("PostgreSQL is ready.")
                return
        except Exception as exc:  # noqa: BLE001 - keep trying until the timeout
            if time.time() > deadline:
                sys.exit(f"PostgreSQL not reachable after {timeout} s: {type(exc).__name__}. "
                         "Is Docker Desktop running? Is the port in .env free?")
            time.sleep(2)


def cmd_setup(args) -> None:
    banner("Setup: environment and database")
    ensure_env()
    if shutil.which("docker"):
        if sh("docker", "compose", "up", "-d", check=False) != 0:
            print("Docker did not start the database (is Docker Desktop running?) - trying the database in .env.")
    else:
        print("Docker not found - using the PostgreSQL configured in .env.")
    wait_for_db()



def cmd_run(args) -> int:
    banner("Pipeline" + (" (with new source data)" if args.generate else ""))
    return sh(PY, "-m", "etl.run_pipeline", *(["--generate"] if args.generate else []), check=args.strict)


def cmd_check(args) -> None:
    banner("Health check")
    sh(PY, "-m", "etl.healthcheck")


def cmd_status(args) -> None:
    from sqlalchemy import text

    from etl.db import get_engine
    banner("Last runs")
    with get_engine().connect() as conn:
        for r in conn.execute(text("SELECT run_id, status, started_at, dauer_sek, blockiert, fehler, warnungen "
                                   "FROM meta.v_lauf_historie LIMIT 5")):
            print(f"  run {r.run_id:>4}  {r.status:<22} {r.started_at:%d.%m.%Y %H:%M}  {r.dauer_sek or 0:>4} s  "
                  f"blocked {r.blockiert}  errors {r.fehler}  warnings {r.warnungen}")
        banner("Data quality (latest result per rule)")
        for r in conn.execute(text("SELECT rule_id, status, fehler_anzahl, blockierend, beschreibung "
                                   "FROM meta.v_dq_aktuell ORDER BY rule_id")):
            flag = "blocking" if r.blockierend else ""
            print(f"  {r.rule_id}  {r.status:<9} {r.fehler_anzahl:>8}  {flag:<8}  {r.beschreibung}")



def cmd_test(args) -> None:
    level = {"unit": ["-m", "unit"], "db": ["-m", "unit or db"], "e2e": ["-m", "e2e"], "all": []}[args.level]
    cov = ["--cov", "--cov-report=term", "--cov-report=html:logs/coverage"] if args.cov else []
    banner(f"Tests: {args.level}")
    sh(PY, "-m", "pytest", *level, *cov)


def cmd_lint(args) -> None:
    banner("Lint (ruff)")
    sh(PY, "-m", "ruff", "check", ".")


def sap(sql: str) -> None:
    from sqlalchemy import text

    from etl.db import get_engine
    with get_engine("src_sap_b1").begin() as conn:
        conn.execute(text(sql))
    print(f"SAP B1 changed: {sql[:90]}...")


def demo_fix() -> None:
    print("The master data team creates the missing customer and fixes the duplicate EAN in SAP B1.")
    sap("INSERT INTO ocrd (cardcode, cardname, cardtype, city, zipcode, country, createdate, updatedate) "
        "VALUES ('C99999', 'Neukunde Muster GmbH', 'C', 'Köln', '50667', 'DE', CURRENT_DATE, CURRENT_DATE)")
    sap("UPDATE oitm SET codebars = '4012345000016' WHERE itemcode = 'A00045'")
    sh(PY, "-m", "etl.run_pipeline")
    print("-> DQ01 and DQ04 are OK now. Refresh Power BI: 'Umsatz ohne Kunde' is 0.")


def demo_block() -> None:
    print("A broken export: half of the invoice lines are missing.")
    sap("DELETE FROM inv1 WHERE docentry::int % 2 = 0")
    sh(PY, "-m", "etl.run_pipeline", check=False)
    print("-> Run BLOCKED by DQ14 (exit code 1). Gold is unchanged: Power BI keeps the last good data.")
    print("   Restore the source data afterwards: python manage.py demo reset")


def demo_schema() -> None:
    print("SAP B1 no longer delivers the column 'zipcode'.")
    sap("ALTER TABLE ocrd DROP COLUMN zipcode")
    sh(PY, "-m", "etl.run_pipeline", check=False)
    print("-> SchemaDriftError: the load stops before anything is changed.")
    print("   Restore the source data afterwards: python manage.py demo reset")


def demo_mdm() -> None:
    from sqlalchemy import text

    from etl.db import get_engine
    from etl.run_pipeline import build_layer
    from etl.runlog import start_run
    engine = get_engine()
    print("Without the manual match, the customer with the postcode typo is counted twice:")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM mdm.kunde_override"))
    results = build_layer(engine, start_run(engine, "demo"), "silver")
    print(f"-> DQ13: {next(r.status for r in results if r.rule_id == 'DQ13')}  (possible duplicate reported)")
    print("Restoring the manual match from sql/10_mdm/02_kunde_override.sql ...")
    sh(PY, "-m", "etl.run_pipeline")


def demo_reset() -> None:
    print("Back to the original test data.")
    sh(PY, "-m", "etl.run_pipeline", "--generate")


DEMOS = {"fix": demo_fix, "block": demo_block, "schema": demo_schema, "mdm": demo_mdm, "reset": demo_reset}


def cmd_demo(args) -> None:
    banner(f"Demo: {args.name}")
    DEMOS[args.name]()



def cmd_showcase(args) -> None:
    start = time.perf_counter()
    cmd_setup(args)
    cmd_run(argparse.Namespace(generate=True, strict=True))
    cmd_check(args)
    cmd_status(args)
    cmd_lint(args)
    cmd_test(argparse.Namespace(level="all", cov=True))
    banner(f"Done in {time.perf_counter() - start:.0f} s")
    print("  Power BI:  open powerbi/Nordwerk.pbix and click Refresh")
    print("  Coverage:  logs/coverage/index.html")
    print("  Demos:     python manage.py demo fix | block | schema | mdm | reset")



def main() -> None:
    parser = argparse.ArgumentParser(prog="manage.py", description="Nordwerk Data Platform")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("showcase", help="everything: database, pipeline, checks, tests").set_defaults(func=cmd_showcase)
    sub.add_parser("setup", help="create .env, start PostgreSQL, wait until ready").set_defaults(func=cmd_setup)
    p = sub.add_parser("run", help="run the pipeline")
    p.add_argument("--generate", action="store_true", help="create the source data first")
    p.set_defaults(func=cmd_run, strict=True)
    sub.add_parser("check", help="health check").set_defaults(func=cmd_check)
    sub.add_parser("status", help="last runs and data quality").set_defaults(func=cmd_status)
    p = sub.add_parser("test", help="run tests")
    p.add_argument("level", nargs="?", default="all", choices=["unit", "db", "e2e", "all"])
    p.add_argument("--cov", action="store_true", help="with coverage report")
    p.set_defaults(func=cmd_test)
    sub.add_parser("lint", help="code style").set_defaults(func=cmd_lint)
    p = sub.add_parser("demo", help="interview demos")
    p.add_argument("name", choices=list(DEMOS))
    p.set_defaults(func=cmd_demo)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
