"""Read-only public directory for controlled MDAD source observations."""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mia_capital_intelligence.app_tabs.app_common import (  # noqa: E402
    PAGE_STYLE, SECTION_KEY, SECTIONS, initialize_explore_route, published_registry, render_record_page,
)
from mia_capital_intelligence.app_tabs.explore import render_explore_tab  # noqa: E402
from mia_capital_intelligence.app_tabs.overview import render_overview  # noqa: E402
from mia_capital_intelligence.app_tabs.sources import render_coverage  # noqa: E402
from mia_capital_intelligence.app_tabs.spending import render_spending_tab  # noqa: E402
from mia_capital_intelligence.app_tabs.traffic import render_traffic_tab  # noqa: E402

st.set_page_config(page_title="MIA Capital Intelligence", page_icon="✈", layout="wide")
ATTRIBUTION = "Records are attributed to their publishing organizations."
st.html(PAGE_STYLE)

try:
    registry = published_registry()
except (ValueError, OSError, KeyError):
    st.title("MIA Capital Intelligence")
    st.error("The published data could not be validated. Project records are unavailable until the data is repaired.")
    st.stop()

if "record" in st.query_params:
    render_record_page(registry)
    st.stop()

reports = {source["matter_id"]: source for source in registry.catalog if source["indexed_record_count"]}
latest_report = max(reports, key=lambda matter: reports[matter]["period_end"])
initialize_explore_route(reports)

st.title("MIA Capital Intelligence")
section = st.radio("Section", SECTIONS, horizontal=True, key=SECTION_KEY, label_visibility="collapsed")
if section == SECTIONS[0]:
    render_overview(registry, reports, latest_report, ROOT)
elif section == SECTIONS[1]:
    render_explore_tab(registry, latest_report)
elif section == SECTIONS[2]:
    render_coverage(registry)
elif section == SECTIONS[3]:
    render_spending_tab(ROOT)
else:
    render_traffic_tab()

st.divider()
st.caption(ATTRIBUTION)
