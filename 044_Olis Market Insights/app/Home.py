"""Entry point of the dashboard.

Run from the project root (after src\\warehouse.py):
    streamlit run app\\Home.py

This file only does the setup that every page shares: page config,
language selector, text direction and navigation. The pages are in
app/views/. Their titles come from the translation file, so the
navigation changes language too.
"""

import streamlit as st

from data import data_dates, database_exists, reload
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
st.sidebar.button(tr("sidebar.reload"), on_click=reload)

pages = [
    st.Page("views/overview.py", title=tr("nav.overview"), url_path="overview", default=True),
    st.Page("views/marketing.py", title=tr("nav.marketing"), url_path="marketing"),
    st.Page("views/sellers.py", title=tr("nav.sellers"), url_path="sellers"),
    st.Page("views/experiments.py", title=tr("nav.experiments"), url_path="experiments"),
    st.Page("views/recommendations.py", title=tr("nav.recommendations"), url_path="recommendations"),
    st.Page("views/data_quality.py", title=tr("nav.data_quality"), url_path="data-quality"),
    st.Page("views/ask.py", title=tr("nav.ask"), url_path="ask"),
]
st.navigation(pages).run()
