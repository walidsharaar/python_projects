"""Page 7: Ask the data. A free local AI model (Ollama) answers questions about the numbers.

The model only gets the facts calculated by the project (src/insights.py),
never raw data, and every answer is labelled as AI-generated, to be checked.
"""

import streamlit as st

from data import analysis_result, channels, data_quality, executive_funnel, gtm_monthly, kpis
from ui import lang, tr
from src import assistant, insights

code = lang()
st.title(tr("assistant.title"))
st.write(tr("assistant.intro"))

state = assistant.status()
if not state["running"]:
    st.info(tr("assistant.offline", model=state["model"]))
    st.stop()
if not state["model_ready"]:
    st.warning(tr("assistant.no_model", model=state["model"]))
    st.stop()

facts = insights.facts(
    kpis(), executive_funnel().reset_index(), channels(), insights.latest_month_check(gtm_monthly()),
    data_quality(), analysis_result("lead_types"),
    [{"n": f["n"], "title": tr(f"finding.{f['n']}.title"), "action": tr(f"finding.{f['n']}.action"),
      "teams": f["teams"]} for f in insights.FINDINGS])

history = st.session_state.setdefault("chat", [])
question = None
for i, column in enumerate(st.columns(3), start=1):
    if column.button(tr(f"assistant.example.{i}"), key=f"example_{i}"):
        question = tr(f"assistant.example.{i}")
question = st.chat_input(tr("assistant.placeholder")) or question

for turn in history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])
if question:
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"), st.spinner(tr("assistant.thinking")):
        reply = assistant.ask(question, facts, code, history)
        if reply["ok"]:
            st.caption(tr("assistant.label", model=state["model"]))
            st.markdown(reply["answer"])
            history += [{"role": "user", "content": question}, {"role": "assistant", "content": reply["answer"]}]
        else:
            st.warning(tr("assistant.error", error=reply["error"]))
