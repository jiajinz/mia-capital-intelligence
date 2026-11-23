"""Read-only public directory for controlled MDAD source observations."""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mia_capital_intelligence.app_tabs.app_common import (  # noqa: E402
    PAGE_STYLE, initialize_explore_route, published_registry, render_record_page,
)
from mia_capital_intelligence.app_tabs.dashboard import render_dashboard  # noqa: E402
from mia_capital_intelligence.app_tabs.explore import render_explore_tab  # noqa: E402
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

explore_tab, dashboard_tab, coverage_tab, spending_tab, traffic_tab = st.tabs([
    "Explore", "Dashboard", "Sources & coverage", "Spending", "Traffic",
], default="Explore")
with explore_tab:
    render_explore_tab(registry, latest_report)
with dashboard_tab:
    render_dashboard(registry, reports, latest_report)
with coverage_tab:
    render_coverage(registry)
with spending_tab:
    render_spending_tab(ROOT)
with traffic_tab:
    render_traffic_tab()

st.divider()
st.caption(ATTRIBUTION)
