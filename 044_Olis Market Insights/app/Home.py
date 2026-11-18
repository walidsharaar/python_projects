"""Entry point of the dashboard: one executive screen in English, German and Persian.

Run from the project root (after src\\warehouse.py and the analysis scripts):
    streamlit run app\\Home.py

This file only does the shared setup: page config, language selector, text
direction and data facts in the sidebar. The screen itself is app/views/executive.py.
"""

import streamlit as st

from data import data_dates, database_exists, reload
from ui import apply_direction, lang, language_selector, tr
from src.i18n import fmt_date

st.set_page_config(page_title="Marketplace GTM Analytics", layout="wide")

language_selector()
apply_direction()

st.sidebar.title(tr("app.title"))
st.sidebar.caption(tr("app.tagline"))

if not database_exists():
    st.error(tr("error.no_database"))
    st.stop()

st.sidebar.caption(tr("sidebar.data_note", data_end=fmt_date(data_dates()["data_end"], lang())))
st.sidebar.button(tr("sidebar.reload"), on_click=reload)

st.navigation([st.Page("views/executive.py", title=tr("exec.title"), url_path="executive", default=True)],
              position="hidden").run()
