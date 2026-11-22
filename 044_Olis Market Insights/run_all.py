"""Run the whole project with one command: check -> profile -> clean -> warehouse -> analyses
-> simulation -> report -> tests.
Stops at the first failing step, so nobody presents numbers from a half-built warehouse.

Usage (from the project folder):
    python run_all.py                    # everything
    python run_all.py --from warehouse   # start at a later step (raw data already cleaned)
    python run_all.py --dry-run          # only show the steps
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_FILE = ROOT / "logs" / "run_all.log"

# (step name, command arguments after the Python interpreter)
STEPS: list[tuple[str, list[str]]] = [
    ("check", ["src/check_data.py"]),
    ("profile", ["src/profile_data.py"]),
    ("clean", ["src/clean.py"]),
    ("warehouse", ["src/warehouse.py"]),
    ("channel_quality", ["analysis/01_channel_quality.py"]),
    ("win_vs_activation", ["analysis/02_win_vs_activation.py"]),
    ("landing_pages", ["analysis/03_landing_pages.py"]),
    ("tracking_data_quality", ["analysis/04_tracking_data_quality.py"]),
    ("cohorts", ["analysis/05_cohorts.py"]),
    ("experiments", ["analysis/06_experiments.py"]),
    # SIMULATED EventPro data (separate database, clearly labelled; see docs/simulation.md)
    ("simulate", ["src/simulate.py"]),
    ("simulated_eventpro", ["analysis/07_simulated_eventpro.py"]),
    ("weekly_report", ["src/weekly_report.py"]),
    ("tests", ["-m", "unittest", "discover", "tests"]),
]
STEP_NAMES = [name for name, _ in STEPS]


def log(message: str) -> None:
    """Print a line and append it to logs/run_all.log."""
    print(message, flush=True)
    LOG_FILE.parent.mkdir(exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(message + "\n")


def run_step(name: str, args: list[str]) -> tuple[bool, float]:
    """Run one step as a subprocess in the project folder. Returns (ok, seconds)."""
    start = time.perf_counter()
    result = subprocess.run([sys.executable, *args], cwd=ROOT)
    return result.returncode == 0, time.perf_counter() - start


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the GTM project end to end.")
    parser.add_argument("--from", dest="start", choices=STEP_NAMES, default=STEP_NAMES[0],
                        help="first step to run (default: %(default)s)")
    parser.add_argument("--dry-run", action="store_true", help="only list the steps")
    opts = parser.parse_args()

    steps = STEPS[STEP_NAMES.index(opts.start):]
    if opts.dry_run:
        for i, (name, args) in enumerate(steps, 1):
            print(f"{i:>2}. {name:<22} python {' '.join(args)}")
        return 0

    log(f"\n=== run_all started {datetime.now():%Y-%m-%d %H:%M:%S} ===")
    results: list[tuple[str, bool, float]] = []
    for i, (name, args) in enumerate(steps, 1):
        log(f"\n--- [{i}/{len(steps)}] {name} ---")
        ok, seconds = run_step(name, args)
        results.append((name, ok, seconds))
        if not ok:
            break

    log("\n=== Summary ===")
    for name, ok, seconds in results:
        log(f"  {'OK  ' if ok else 'FAIL'}  {name:<22} {seconds:6.1f} s")
    total = sum(s for _, _, s in results)
    if all(ok for _, ok, _ in results) and len(results) == len(steps):
        log(f"All {len(steps)} steps passed in {total:.0f} s. Start the dashboard: streamlit run app\\Home.py")
        return 0
    failed = results[-1][0]
    log(f"Stopped at '{failed}'. Fix the error above, then continue with: python run_all.py --from {failed}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
