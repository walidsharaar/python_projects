"""'Ask the data': answers questions about the GTM numbers with a local model (Ollama).

Free and private: the model runs on this computer through Ollama
(https://ollama.com), so no data leaves the laptop and there is no API key.
Only Python's standard library is used, so no extra package is needed.

Setup (once):
    1. Install Ollama:        winget install Ollama.Ollama
    2. Download a model:      ollama pull gemma3:4b
    3. Ollama then runs in the background on http://localhost:11434

Settings (optional environment variables):
    OLLAMA_HOST   default http://localhost:11434
    OLLAMA_MODEL  default gemma3:4b  (a small model that also writes German and Persian)

Rules for the answers (in the system prompt and in the code):
    - The model gets ONLY the facts calculated by the project (src/insights.py).
    - It must not invent or calculate new numbers, and must say when the
      facts do not answer the question.
    - It separates facts from possible explanations.
    - The dashboard labels every answer as AI-generated and to be checked.
"""

import json
import os
import urllib.error
import urllib.request

HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")
# On a laptop without a graphics card, the first answer (model loading) can take minutes
TIMEOUT_SECONDS = float(os.environ.get("OLLAMA_TIMEOUT", "300"))
MAX_HISTORY = 6          # earlier question/answer pairs sent along, to keep the prompt small

LANGUAGE_NAMES = {"en": "English", "de": "German", "fa": "Persian (Farsi/Dari)"}


def _request(path: str, payload: dict | None = None, timeout: float = 5) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{HOST}{path}", data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def status() -> dict:
    """Is Ollama running, and is the model downloaded? Never raises."""
    try:
        models = [m.get("name", "") for m in _request("/api/tags").get("models", [])]
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return {"running": False, "model_ready": False, "model": MODEL}
    ready = any(name == MODEL or name.split(":")[0] == MODEL for name in models)
    return {"running": True, "model_ready": ready, "model": MODEL, "models": models}


def compact(facts: dict) -> dict:
    """Only the essentials, so a small model on a laptop answers in reasonable time.

    Every value still comes from the project's facts; nothing is added.
    """
    keep_channel = ("origin", "leads", "lead_to_win_rate", "activation_rate", "activated_per_1000_leads")
    return {
        "note": facts.get("note"),
        "kpis": {key: v["value"] for key, v in facts.get("kpis", {}).items()},
        "funnel_per_1000_leads": facts.get("funnel_per_1000_leads"),
        "channels": [{c: ch.get(c) for c in keep_channel} for ch in facts.get("channels") or []],
        "latest_month_check": facts.get("latest_month_check"),
        "findings": [f.get("title") for f in facts.get("findings") or []],
    }


def system_prompt(facts: dict, lang: str) -> str:
    return (
        "You are a data analyst who explains a Go-to-Market dashboard to an executive. "
        f"Always answer in {LANGUAGE_NAMES.get(lang, 'English')}, in short, plain business language "
        "(CEFR B1-B2), at most 150 words.\n"
        "Rules:\n"
        "1. Use ONLY the facts in the JSON below. Do not invent numbers and do not calculate new ones; "
        "you may quote numbers from the JSON. Rates are fractions: 0.106 means 10.6 %.\n"
        "2. If the facts do not answer the question, say so clearly and name the data that would be needed.\n"
        "3. Separate what the data shows from possible explanations. Call explanations hypotheses to check.\n"
        "4. When you recommend something, name who should act (Marketing, Sales, Product or Data) "
        "and how success would be measured, using the findings in the JSON.\n"
        "5. GMV is not revenue. There is no marketing spend data, so never talk about CAC or ROI as known.\n"
        "FACTS (JSON):\n" + json.dumps(compact(facts), ensure_ascii=False, default=str, separators=(",", ":"))
    )


def ask(question: str, facts: dict, lang: str, history: list[dict] | None = None) -> dict:
    """Ask one question. Returns {"ok": bool, "answer": str | None, "error": str | None}.

    history: earlier turns as [{"role": "user"|"assistant", "content": "..."}].
    """
    messages = [{"role": "system", "content": system_prompt(facts, lang)}]
    messages += (history or [])[-2 * MAX_HISTORY:]
    messages.append({"role": "user", "content": question})
    try:
        reply = _request("/api/chat", {
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.2},   # low: we want sober answers, not creative ones
        }, timeout=TIMEOUT_SECONDS)
    except urllib.error.HTTPError as e:
        return {"ok": False, "answer": None, "error": f"Ollama returned HTTP {e.code}"}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"ok": False, "answer": None, "error": f"Ollama is not reachable at {HOST} ({e})"}
    answer = (reply.get("message") or {}).get("content", "").strip()
    return {"ok": bool(answer), "answer": answer or None, "error": None if answer else "empty answer"}
