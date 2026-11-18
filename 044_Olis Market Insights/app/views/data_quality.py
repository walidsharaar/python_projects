"""Page 6: Data quality. Every known gap, how big it is and what it affects.

Reads mart_data_quality. Making limits visible is part of a data base that
people can trust; it is not a footnote.
"""

import pandas as pd
import streamlit as st

from data import data_dates, data_quality
from ui import lang, tr
from src.i18n import fmt_date, fmt_num, fmt_pct

code = lang()
st.title(tr("dq.title"))
st.write(tr("dq.intro"))

# ------------------------------------------------------ data period
st.subheader(tr("dq.dates.title"))
dates = data_dates()
c1, c2 = st.columns(2)
c1.metric(tr("dq.dates.tracking_start"), fmt_date(dates["tracking_start"], code),
          help=tr("dq.dates.help_tracking"), border=True)
c2.metric(tr("dq.dates.data_end"), fmt_date(dates["data_end"], code),
          help=tr("dq.dates.help_end"), border=True)

# ---------------------------------------------------------- checks
dq = data_quality().copy()
dq["share"] = dq["records"] / dq["total_records"]
dq = dq.sort_values("share", ascending=False)
st.dataframe(pd.DataFrame({
    tr("dq.table.check"): [tr(f"dq.check.{c}") for c in dq["check_key"]],
    tr("dq.table.records"): [fmt_num(v, code) for v in dq["records"]],
    tr("dq.table.of"): [fmt_num(v, code) for v in dq["total_records"]],
    tr("dq.table.share"): [fmt_pct(v, code) for v in dq["share"]],
    tr("dq.table.affects"): [tr(f"dq.affects.{a}") for a in dq["affects"]],
}), hide_index=True, width="stretch")

# ----------------------------------------------- what we cannot measure
st.subheader(tr("dq.missing.title"))
st.warning(tr("dq.missing.text"))
