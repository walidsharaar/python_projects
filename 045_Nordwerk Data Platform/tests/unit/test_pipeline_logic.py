"""
Orchestration: the core promise of the pipeline, tested without a database.
- a layer is committed only if no blocking rule fails
- otherwise it is rolled back, the results are still saved, and Blocked is raised
- a crash rolls back too
- the exit code tells a scheduler what happened
"""
from unittest.mock import MagicMock

import pytest

from etl import run_dq, run_pipeline
from etl.run_dq import DqResult
from tests.unit.fakes import FakeConnection, FakeEngine


@pytest.fixture()
def layer(monkeypatch):
    """Patch the SQL and DQ calls of build_layer; return what was recorded."""
    calls = {"saved": None, "layer_sql": None}

    def fake_run_layer(conn, path):
        calls["layer_sql"] = path.name
        if conn.fail_on:
            raise RuntimeError("syntax error in SQL")

    def set_results(results):
        monkeypatch.setattr(run_dq, "check_phase", lambda conn, phase: results)

    monkeypatch.setattr(run_pipeline, "run_layer", fake_run_layer)
    monkeypatch.setattr(run_dq, "save_results", lambda eng, run_id, res: calls.update(saved=(run_id, res)))
    calls["set_results"] = set_results
    return calls


def test_layer_is_committed_when_checks_pass(layer):
    conn = FakeConnection()
    layer["set_results"]([DqResult("DQ01", "", 78, "ERROR"), DqResult("DQ02", "", 0, "OK")])
    results = run_pipeline.build_layer(FakeEngine(conn), 3, "silver")
    assert conn.commits == 1 and conn.rollbacks == 0 and conn.closed
    assert layer["layer_sql"] == "20_silver"
    assert [r.rule_id for r in results] == ["DQ01", "DQ02"]


def test_gold_layer_uses_gold_folder(layer):
    layer["set_results"]([])
    run_pipeline.build_layer(FakeEngine(FakeConnection()), 3, "gold")
    assert layer["layer_sql"] == "30_gold"


def test_blocking_rule_rolls_back_and_raises(layer):
    conn = FakeConnection()
    layer["set_results"]([DqResult("DQ14", "", 50, "BLOCKIERT")])
    with pytest.raises(run_pipeline.Blocked, match="DQ14"):
        run_pipeline.build_layer(FakeEngine(conn), 3, "silver")
    assert conn.commits == 0 and conn.rollbacks == 1 and conn.closed


def test_results_are_saved_even_when_blocked(layer):
    layer["set_results"]([DqResult("DQ14", "", 50, "BLOCKIERT")])
    with pytest.raises(run_pipeline.Blocked):
        run_pipeline.build_layer(FakeEngine(FakeConnection()), 9, "silver")
    run_id, results = layer["saved"]
    assert run_id == 9 and results[0].rule_id == "DQ14"


def test_sql_error_rolls_back_and_propagates(layer):
    conn = FakeConnection(fail_on="x")
    with pytest.raises(RuntimeError, match="syntax"):
        run_pipeline.build_layer(FakeEngine(conn), 3, "silver")
    assert conn.commits == 0 and conn.rollbacks == 1 and conn.closed
    assert layer["saved"] is None


# ---------------------------------------------------------------- main(): status and exit code
@pytest.fixture()
def pipeline(monkeypatch):
    """Replace every step of main() so only the control flow remains."""
    state = {"finish": None, "silver": [], "gold": [], "raise": None}
    monkeypatch.setattr(run_pipeline, "run_sql_path", lambda path: None)
    monkeypatch.setattr(run_pipeline, "get_engine", lambda: MagicMock())
    monkeypatch.setattr(run_pipeline, "start_run", lambda engine: 42)
    monkeypatch.setattr(run_pipeline.load_bronze, "main", lambda run_id: None)
    monkeypatch.setattr(run_pipeline, "finish_run",
                        lambda engine, run_id, status, msg=None: state.update(finish=(run_id, status, msg)))

    def fake_build(engine, run_id, layer):
        if state["raise"] and state["raise"][0] == layer:
            raise state["raise"][1]
        return state[layer]

    monkeypatch.setattr(run_pipeline, "build_layer", fake_build)
    monkeypatch.setattr("sys.argv", ["run_pipeline"])
    return state


def exit_code(func):
    with pytest.raises(SystemExit) as exc:
        func()
    return exc.value.code


def test_clean_run_is_success_exit_0(pipeline):
    pipeline["silver"] = [DqResult("DQ02", "", 0, "OK")]
    assert exit_code(run_pipeline.main) == 0
    assert pipeline["finish"] == (42, "success", None)


def test_findings_are_published_exit_0(pipeline):
    pipeline["silver"] = [DqResult("DQ01", "", 78, "ERROR"), DqResult("DQ03", "", 5, "WARN")]
    assert exit_code(run_pipeline.main) == 0
    assert pipeline["finish"] == (42, "success_with_findings", "DQ01 ERROR, DQ03 WARN")


def test_blocked_run_exit_1(pipeline):
    pipeline["raise"] = ("silver", run_pipeline.Blocked("silver not published, blocking rule(s): DQ14"))
    assert exit_code(run_pipeline.main) == 1
    assert pipeline["finish"][1] == "blocked"


def test_crash_is_logged_as_failed_exit_1(pipeline):
    pipeline["raise"] = ("gold", RuntimeError("disk full"))
    assert exit_code(run_pipeline.main) == 1
    assert pipeline["finish"][1:] == ("failed", "disk full")


def test_generate_flag_creates_sources_first(pipeline, monkeypatch):
    called = []
    monkeypatch.setattr(run_pipeline, "generate_sources", lambda: called.append(True))
    monkeypatch.setattr("sys.argv", ["run_pipeline", "--generate"])
    exit_code(run_pipeline.main)
    assert called == [True]
