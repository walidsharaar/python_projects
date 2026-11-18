"""Page 5: Recommendations. The nine findings from README section 9, filterable by team.

The texts are in the translation file (finding.N.*). The order is the
priority order of the README: finding 1 affects how reliable all others are.
"""

import streamlit as st

from ui import tr

# Metadata only: the words are in src/i18n/translations.json
FINDINGS = [
    {"n": 1, "teams": ["marketing", "data"], "confidence": "high"},
    {"n": 2, "teams": ["data", "leadership"], "confidence": "high"},
    {"n": 3, "teams": ["marketing"], "confidence": "medium"},
    {"n": 4, "teams": ["sales", "product"], "confidence": "mixed"},
    {"n": 5, "teams": ["sales", "product"], "confidence": "medium"},
    {"n": 6, "teams": ["marketing", "product"], "confidence": "medium"},
    {"n": 7, "teams": ["marketing"], "confidence": "low"},
    {"n": 8, "teams": ["sales", "leadership"], "confidence": "high"},
    {"n": 9, "teams": ["sales"], "confidence": "medium"},
]
TEAMS = ["marketing", "sales", "product", "data", "leadership"]

st.title(tr("rec.title"))
st.write(tr("rec.intro"))

selected = st.multiselect(tr("rec.filter"), TEAMS, default=TEAMS, key="rec_teams",
                          format_func=lambda team: tr(f"team.{team}"))
shown = [f for f in FINDINGS if set(f["teams"]) & set(selected)]
if not shown:
    st.info(tr("rec.none"))

for f in shown:
    n = f["n"]
    with st.container(border=True):
        st.markdown(f"#### {n}. {tr(f'finding.{n}.title')}")
        st.markdown(f"**{tr('rec.action')}:** {tr(f'finding.{n}.action')}")
        st.markdown(f"**{tr('rec.measure')}:** {tr(f'finding.{n}.measure')}")
        c1, c2 = st.columns(2)
        c1.caption(f"{tr('rec.owner')}: " + ", ".join(tr(f"team.{t}") for t in f["teams"]))
        c2.caption(f"{tr('rec.confidence')}: {tr(f'confidence.{f["confidence"]}')}")
