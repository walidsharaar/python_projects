"""Connection settings, SQL file runner and run log."""
import logging
from unittest.mock import MagicMock

import pytest

from etl import db, run_sql, runlog
from tests.unit.fakes import FakeConnection

ENV = {"POSTGRES_USER": "nordwerk", "POSTGRES_PASSWORD": "s3cret!", "POSTGRES_DB": "nordwerk_dwh",
       "POSTGRES_HOST": "dbhost", "POSTGRES_PORT": "5433"}


# ---------------------------------------------------------------- db.py
@pytest.fixture()
def env(monkeypatch):
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)


def test_engine_reads_everything_from_env(env):
    url = db.get_engine().url
    assert (url.username, url.host, url.port, url.database) == ("nordwerk", "dbhost", 5433, "nordwerk_dwh")
    assert url.drivername == "postgresql+psycopg"


def test_engine_uses_local_time_zone(env, monkeypatch):
    captured = {}
    monkeypatch.setattr(db, "create_engine", lambda url, **kw: captured.update(kw))
    db.get_engine()
    assert captured["connect_args"] == {"options": "-c timezone=Europe/Berlin -c jit=off"}


def test_engine_can_target_another_database(env):
    assert db.get_engine("src_sap_b1").url.database == "src_sap_b1"


def test_password_never_shows_in_logs(env):
    assert "s3cret" not in str(db.get_engine().url)


def test_special_characters_in_password_are_safe(env):
    assert db.get_engine().url.password == "s3cret!"


def test_missing_setting_fails_loudly(env, monkeypatch):
    monkeypatch.delenv("POSTGRES_HOST")
    with pytest.raises(KeyError, match="POSTGRES_HOST"):
        db.get_engine()


# ---------------------------------------------------------------- run_sql.py
@pytest.fixture()
def sql_dir(tmp_path):
    layer = tmp_path / "sql" / "20_silver"
    layer.mkdir(parents=True)
    for name, body in [("02_b.sql", "SELECT 2;"), ("01_a.sql", "SELECT 1;"), ("10_c.sql", "SELECT 10;")]:
        (layer / name).write_text(body, encoding="utf-8")
    (layer / "notes.txt").write_text("not sql")
    return layer


def test_sql_files_sorted_by_number(sql_dir):
    assert [f.name for f in run_sql.sql_files(sql_dir)] == ["01_a.sql", "02_b.sql", "10_c.sql"]


def test_single_file_is_accepted(sql_dir):
    assert run_sql.sql_files(sql_dir / "02_b.sql") == [sql_dir / "02_b.sql"]


def test_run_layer_executes_in_order_without_commit(sql_dir):
    conn = FakeConnection()
    run_sql.run_layer(conn, sql_dir)
    assert conn.executed == ["SELECT 1;", "SELECT 2;", "SELECT 10;"]
    assert conn.commits == 0


def test_run_layer_stops_at_first_error(sql_dir):
    conn = FakeConnection(fail_on="SELECT 2;")
    with pytest.raises(RuntimeError):
        run_sql.run_layer(conn, sql_dir)
    assert conn.executed == ["SELECT 1;", "SELECT 2;"]


def test_run_sql_path_commits_each_file(sql_dir, monkeypatch):
    conns = []

    def new_conn():
        conns.append(FakeConnection())
        return conns[-1]

    monkeypatch.setattr(run_sql, "get_engine", lambda: MagicMock(raw_connection=new_conn))
    run_sql.run_sql_path(sql_dir)
    assert [c.commits for c in conns] == [1, 1, 1] and all(c.closed for c in conns)


def test_run_sql_path_rolls_back_failed_file(sql_dir, monkeypatch):
    conn = FakeConnection(fail_on="SELECT 1;")
    monkeypatch.setattr(run_sql, "get_engine", lambda: MagicMock(raw_connection=lambda: conn))
    with pytest.raises(RuntimeError):
        run_sql.run_sql_path(sql_dir)
    assert conn.rollbacks == 1 and conn.closed


# ---------------------------------------------------------------- runlog.py
def test_logger_is_configured_only_once():
    first = runlog.get_logger()
    handlers = len(first.handlers)
    assert runlog.get_logger() is first and len(first.handlers) == handlers


def test_logger_writes_to_file(tmp_path, monkeypatch):
    monkeypatch.setattr(runlog, "LOG_DIR", tmp_path)
    logger = runlog.get_logger("nordwerk-test-file")
    logger.info("hello pipeline")
    for h in logger.handlers:
        h.flush()
    assert "hello pipeline" in (tmp_path / "pipeline.log").read_text(encoding="utf-8")
    for h in list(logger.handlers):
        h.close()
        logger.removeHandler(h)


def test_logger_level_is_info():
    assert runlog.get_logger().level == logging.INFO


def test_start_run_returns_new_id():
    engine = MagicMock()
    conn = engine.begin.return_value.__enter__.return_value
    conn.execute.return_value.scalar.return_value = 17
    assert runlog.start_run(engine, "pipeline") == 17
    assert conn.execute.call_args.args[1] == {"layer": "pipeline"}


def test_finish_run_sets_status_and_message():
    engine = MagicMock()
    conn = engine.begin.return_value.__enter__.return_value
    runlog.finish_run(engine, 17, "blocked", "DQ14")
    assert conn.execute.call_args.args[1] == {"status": "blocked", "msg": "DQ14", "run_id": 17}


# ---------------------------------------------------------------- healthcheck.py
def test_healthcheck_exit_code(monkeypatch, capsys):
    from etl import healthcheck
    monkeypatch.setattr(healthcheck, "run_checks", lambda: [("A", 1, 1, "OK"), ("B", 2, 3, "<<< PRÜFEN")])
    assert healthcheck.main() == 1
    assert "1 of 2 OK" in capsys.readouterr().out
    monkeypatch.setattr(healthcheck, "run_checks", lambda: [("A", 1, 1, "OK")])
    assert healthcheck.main() == 0
