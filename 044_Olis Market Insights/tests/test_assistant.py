"""Tests for 'Ask the data' that run WITHOUT Ollama. Run from the project root:
    python -m unittest discover tests

They check that the assistant fails cleanly when the local model is not
running, and that the prompt contains the project's facts and the rules.
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import assistant  # noqa: E402

FACTS = {"kpis": {"lead_to_win_rate_60d_tracked": {"value": 0.106, "unit": "rate"}},
         "findings": [{"n": 1, "title": "A quarter of all wins cannot be credited to a channel"}]}


class AssistantTests(unittest.TestCase):
    def setUp(self):
        self.real_host = assistant.HOST
        assistant.HOST = "http://127.0.0.1:9"          # a port where nothing listens

    def tearDown(self):
        assistant.HOST = self.real_host

    def test_status_when_ollama_is_not_running(self):
        state = assistant.status()
        self.assertFalse(state["running"])
        self.assertFalse(state["model_ready"])

    def test_ask_fails_cleanly_without_ollama(self):
        reply = assistant.ask("Why do we lose most leads?", FACTS, "en")
        self.assertFalse(reply["ok"])
        self.assertIsNone(reply["answer"])
        self.assertIn("not reachable", reply["error"])

    def test_prompt_contains_facts_rules_and_language(self):
        for lang, name in [("en", "English"), ("de", "German"), ("fa", "Persian")]:
            prompt = assistant.system_prompt(FACTS, lang)
            self.assertIn(name, prompt)
            self.assertIn("Do not invent numbers", prompt)
            self.assertIn(json.dumps(FACTS, ensure_ascii=False), prompt)


if __name__ == "__main__":
    unittest.main()
