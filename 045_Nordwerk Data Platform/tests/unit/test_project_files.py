"""
Static checks of the SQL files and the rule catalogue - no database needed.
They catch mistakes before anything runs: a table that is not dropped before it is rebuilt,
a rule without phase, a blocking rule that is only a warning, a password in the code.
"""
import re
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[2]
SQL = PROJECT / "sql"


# ---------------------------------------------------------------- SQL layout
def test_layers_exist_in_order():
    assert [p.name for p in sorted(SQL.iterdir()) if p.is_dir()] == \
        ["00_setup", "10_mdm", "20_silver", "30_gold", "checks"]


@pytest.mark.parametrize("folder", ["00_setup", "10_mdm", "20_silver", "30_gold"])
def test_sql_files_are_numbered_and_unique(folder):
    names = [f.name for f in (SQL / folder).glob("*.sql")]
    assert names and all(re.match(r"^\d{2}_[a-z0-9_]+\.sql$", n) for n in names)
    assert len({n[:2] for n in names}) == len(names)


@pytest.mark.parametrize("path", sorted((SQL / "20_silver").glob("*.sql")) + sorted((SQL / "30_gold").glob("*.sql")),
                         ids=lambda p: p.name)
def test_layer_files_can_be_rerun(path):
    """Every table a layer creates is dropped first: a rerun never fails on 'already exists'."""
    sql = path.read_text(encoding="utf-8")
    created = re.findall(r"CREATE TABLE (\w+\.\w+)", sql)
    for table in created:
        assert re.search(rf"DROP TABLE IF EXISTS {re.escape(table)}", sql), f"{table} is not dropped first"


def test_mdm_and_setup_never_drop_data():
    for path in list((SQL / "00_setup").glob("*.sql")) + list((SQL / "10_mdm").glob("*.sql")):
        assert "DROP TABLE" not in path.read_text(encoding="utf-8").upper(), path.name


def test_no_credentials_in_code():
    for path in PROJECT.rglob("*.py"):
        if ".venv" in path.parts:
            continue
        assert not re.search(r"password\s*=\s*['\"][^'\"]+['\"]", path.read_text(encoding="utf-8"), re.I), path


# ---------------------------------------------------------------- DQ rule catalogue
RULES = (SQL / "00_setup" / "03_dq_rules.sql").read_text(encoding="utf-8")
RULE_ROWS = re.findall(r"\('(DQ\d{2})', '([^']+)', '(ERROR|WARN)', '([^']+)', '(silver|gold)', (true|false), ([\d.]+),",
                       RULES)


def test_all_rules_are_parsed():
    assert len(RULE_ROWS) == len(re.findall(r"\('DQ\d{2}'", RULES)) == 15


def test_rule_ids_unique():
    ids = [r[0] for r in RULE_ROWS]
    assert len(ids) == len(set(ids))


def test_blocking_rules_are_errors():
    assert all(r[2] == "ERROR" for r in RULE_ROWS if r[5] == "true")


def test_gold_rules_read_gold():
    for rule_id, *_ , phase, _b, _t in RULE_ROWS:
        if phase == "gold":
            block = RULES[RULES.index(f"('{rule_id}'"):]
            assert "gold." in block[:block.index("$$)")], rule_id
