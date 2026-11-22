"""
Shared run log and logging for every pipeline step.
- one row in meta.etl_run per pipeline run (start, end, status, message)
- log lines go to the console and to logs/pipeline.log
"""
import logging
from pathlib import Path

from sqlalchemy import text

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def get_logger(name: str = "nordwerk") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:                      # configure only once
        LOG_DIR.mkdir(exist_ok=True)
        fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S")
        for handler in (logging.StreamHandler(), logging.FileHandler(LOG_DIR / "pipeline.log", encoding="utf-8")):
            handler.setFormatter(fmt)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def start_run(engine, layer: str = "pipeline") -> int:
    with engine.begin() as conn:
        return conn.execute(
            text("INSERT INTO meta.etl_run (layer, status) VALUES (:layer, 'running') RETURNING run_id"),
            {"layer": layer},
        ).scalar()


def finish_run(engine, run_id: int, status: str, message: str | None = None) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE meta.etl_run SET status = :status, finished_at = now(), message = :msg "
                 "WHERE run_id = :run_id"),
            {"status": status, "msg": message, "run_id": run_id},
        )
