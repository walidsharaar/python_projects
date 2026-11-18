"""Entry point of the dashboard.

Run from the project root (after src\\warehouse.py):
    streamlit run app\\Home.py

This file only does the setup that every page shares: page config,
language selector, text direction and navigation. The pages are in
app/views/. Their titles come from the translation file, so the
navigation changes language too.
"""

import streamlit as st

from data import data_dates, database_exists
from ui import apply_direction, lang, language_selector, tr
from src.i18n import fmt_month

st.set_page_config(page_title="Marketplace GTM Analytics", layout="wide")

language_selector()
apply_direction()

st.sidebar.title(tr("app.title"))
st.sidebar.caption(tr("app.tagline"))

if not database_exists():
    st.error(tr("error.no_database"))
    st.stop()

st.sidebar.caption(tr("sidebar.data_note", data_end=fmt_month(data_dates()["data_end"], lang())))

pages = [
    st.Page("views/overview.py", title=tr("nav.overview"), url_path="overview", default=True),
]
st.navigation(pages).run()
