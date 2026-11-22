"""Data quality: how a result is rated, how a phase is checked, what counts as blocking."""
from unittest.mock import MagicMock

import pytest

from etl import run_dq
from etl.run_dq import DqResult, blocked, check_phase, rate, save_results
from tests.unit.fakes import FakeConnection


@pytest.mark.parametrize("wert, schwelle, schwere, blockierend, expected", [
    (0, 0, "ERROR", True, "OK"),
    (0, 0, "WARN", False, "OK"),
    (1, 0, "ERROR", True, "BLOCKIERT"),
    (1, 0, "ERROR", False, "ERROR"),
    (1, 0, "WARN", False, "WARN"),
    (1, 0, "WARN", True, "BLOCKIERT"),          # blocking wins over severity
    (30, 30, "ERROR", True, "OK"),              # threshold itself is still OK
    (31, 30, "ERROR", True, "BLOCKIERT"),
    (0.004, 0.01, "ERROR", True, "OK"),         # rounding tolerance in euro
])
def test_rate(wert, schwelle, schwere, blockierend, expected):
    assert rate(wert, schwelle, schwere, blockierend) == expected


def test_blocked_lists_only_blocking_results():
    results = [DqResult("DQ01", "", 78, "ERROR"), DqResult("DQ14", "", 50, "BLOCKIERT"),
               DqResult("DQ02", "", 0, "OK"), DqResult("DQ12", "", 3, "BLOCKIERT")]
    assert blocked(results) == ["DQ14", "DQ12"]


def test_blocked_empty_when_all_fine():
    assert blocked([DqResult("DQ01", "", 0, "OK")]) == []


RULES = [
    ("DQ01", "Kunde unbekannt", "ERROR", False, 0, "check-1"),
    ("DQ03", "EAN fehlt", "WARN", False, 0, "check-3"),
    ("DQ07", "Zeilenabgleich", "ERROR", True, 0, "check-7"),
    ("DQ12", "Silver = Gold", "ERROR", True, 0.01, "check-12"),
]
PHASES = {"DQ12": "gold"}


def test_check_phase_runs_only_rules_of_that_phase():
    conn = FakeConnection(RULES, values={"check-1": 5, "check-3": 0, "check-7": 0}, phases=PHASES)
    results = check_phase(conn, "silver")
    assert [r.rule_id for r in results] == ["DQ01", "DQ03", "DQ07"]
    assert "check-12" not in conn.executed


def test_check_phase_rates_every_rule():
    conn = FakeConnection(RULES, values={"check-1": 5, "check-3": 2, "check-7": 1}, phases=PHASES)
    status = {r.rule_id: r.status for r in check_phase(conn, "silver")}
    assert status == {"DQ01": "ERROR", "DQ03": "WARN", "DQ07": "BLOCKIERT"}


def test_check_phase_treats_null_as_zero():
    conn = FakeConnection(RULES, values={"check-12": None}, phases=PHASES)
    assert check_phase(conn, "gold")[0].status == "OK"


def test_check_phase_never_commits():
    conn = FakeConnection(RULES, phases=PHASES)
    check_phase(conn, "silver")
    assert conn.commits == 0 and conn.rollbacks == 0


def test_save_results_writes_one_row_per_rule():
    engine = MagicMock()
    conn = engine.begin.return_value.__enter__.return_value
    save_results(engine, 7, [DqResult("DQ01", "x", 78, "ERROR"), DqResult("DQ02", "y", 0, "OK")])
    params = [c.args[1] for c in conn.execute.call_args_list]
    assert params == [{"run_id": 7, "rule_id": "DQ01", "wert": 78, "status": "ERROR"},
                      {"run_id": 7, "rule_id": "DQ02", "wert": 0, "status": "OK"}]


def test_standalone_check_changes_nothing(monkeypatch):
    conn = FakeConnection(RULES, phases=PHASES)
    monkeypatch.setattr(run_dq, "get_engine", lambda: MagicMock(raw_connection=lambda: conn))
    run_dq.main()
    assert conn.commits == 0 and conn.rollbacks == 1 and conn.closed
