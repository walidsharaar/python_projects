"""Tests for run_all.py. They need no data: every step must point to a real script, the order must be
check -> clean -> warehouse -> analyses, and the runner must stop with exit code 1 when a step fails."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import run_all  # noqa: E402


class RunAllTests(unittest.TestCase):
    def test_every_step_script_exists(self):
        for name, args in run_all.STEPS:
            if args[0] == "-m":  # the test step runs a module, not a file
                continue
            with self.subTest(step=name):
                self.assertTrue((ROOT / args[0]).is_file(), f"missing script: {args[0]}")

    def test_order_check_first_warehouse_before_analyses_tests_last(self):
        scripts = [args[0] for _, args in run_all.STEPS]
        self.assertEqual(scripts[0], "src/check_data.py")
        warehouse = scripts.index("src/warehouse.py")
        first_analysis = min(i for i, s in enumerate(scripts) if s.startswith("analysis/"))
        self.assertLess(warehouse, first_analysis)
        self.assertEqual(run_all.STEPS[-1][0], "tests")

    def _run(self, steps_code: str, argv: list[str]) -> subprocess.CompletedProcess:
        log = Path(tempfile.mkdtemp()) / "run_all.log"
        code = (
            "import sys, pathlib, run_all\n"
            f"run_all.LOG_FILE = pathlib.Path({str(log)!r})\n"
            f"run_all.STEPS = {steps_code}\n"
            "run_all.STEP_NAMES = [n for n, _ in run_all.STEPS]\n"
            f"sys.argv = ['run_all.py', *{argv!r}]\n"
            "sys.exit(run_all.main())\n"
        )
        return subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)

    def test_stops_at_first_failing_step(self):
        result = self._run(
            "[('fails', ['-c', 'import sys; sys.exit(3)']), ('after', ['-c', 'print(\"SHOULD NOT RUN\")'])]", [])
        self.assertEqual(result.returncode, 1)
        self.assertIn("Stopped at 'fails'", result.stdout)
        self.assertNotIn("SHOULD NOT RUN", result.stdout)

    def test_all_steps_pass(self):
        result = self._run("[('a', ['-c', 'pass']), ('b', ['-c', 'pass'])]", [])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("All 2 steps passed", result.stdout)

    def test_from_skips_earlier_steps(self):
        result = self._run(
            "[('a', ['-c', 'print(\"STEP A\")']), ('b', ['-c', 'print(\"STEP B\")'])]", ["--from", "b"])
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("STEP A", result.stdout)
        self.assertIn("STEP B", result.stdout)


if __name__ == "__main__":
    unittest.main()
