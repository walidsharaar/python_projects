"""Small stand-ins for database objects, so pipeline logic can be tested without PostgreSQL."""


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self._result = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.conn.executed.append(sql)
        if self.conn.fail_on and self.conn.fail_on in sql:
            raise RuntimeError(f"SQL failed: {self.conn.fail_on}")
        if "FROM meta.dq_rule" in sql:
            self._result = [r for r in self.conn.rules if r[0] in self.conn.rules_for(params)]
        else:
            self._result = [(self.conn.values.get(sql, 0),)]

    def fetchall(self):
        return self._result

    def fetchone(self):
        return self._result[0]


class FakeConnection:
    """Records SQL, commits and rollbacks. rules: (rule_id, text, severity, blocking, threshold, check_sql)."""

    def __init__(self, rules=(), values=None, phases=None, fail_on=None):
        self.rules = list(rules)
        self.values = values or {}
        self.phases = phases or {}
        self.fail_on = fail_on
        self.executed = []
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def rules_for(self, params):
        phase = params[0] if params else None
        return {r[0] for r in self.rules if self.phases.get(r[0], "silver") == phase}

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class FakeEngine:
    def __init__(self, conn):
        self.conn = conn

    def raw_connection(self):
        return self.conn
