"""Dashboard tab: operations updates and reported estimates by size."""

from datetime import date

import streamlit as st

from mia_capital_intelligence.app_tabs.app_common import (
    profile_permalink, render_estimate_distribution, report_period,
)
from mia_capital_intelligence.estimate_insights import largest_estimates
from mia_capital_intelligence.operations_updates import OPERATING_AREAS, OPERATIONS_MATTER, operations_updates
from mia_capital_intelligence.public_registry import PublicRegistry


def render_dashboard(registry: PublicRegistry, reports: dict, latest_report: str) -> None:
    st.header("Airport Operations")
    st.write("Operations updates from the county's quarterly report, grouped by area.")
    source = reports.get(OPERATIONS_MATTER)
    if source:
        period = report_period(source["period_start"], source["period_end"])
        memo_date = date.fromisoformat(source["memo_date"])
        st.caption(f"Miami-Dade County · {period} report · Memo dated {memo_date:%b %d, %Y} · "
                   f"[Official report]({source['url']})")
        area = st.radio("Choose an area", ("All areas", *OPERATING_AREAS),
                        horizontal=True, key="dashboard_area")
        st.subheader("Operations updates")
        matches = [update for update in operations_updates(registry)
                   if area == "All areas" or update.area == area]
        if not matches:
            st.info("No operations updates in this view.")
            st.link_button("Explore project records", "?", type="tertiary")
        for update in matches:
            with st.container(border=True):
                st.caption(f"{update.area} · {update.project_id}")
                st.markdown(f"### {update.title}")
                st.write(update.description)
                st.markdown(
                    f"[View project]({profile_permalink(update.source_ref)}) · "
                    f"[Read report update]({source['url']}#page={update.memo_page})"
                )
    else:
        st.info("No operations updates in this view.")
        st.link_button("Explore project records", "?", type="tertiary")

    with st.expander("Reported Estimates by Size"):
        choices = sorted(reports, key=lambda matter: reports[matter]["period_end"], reverse=True)
        matter = st.selectbox("Estimate report period", choices, index=choices.index(latest_report),
                              format_func=lambda key: report_period(reports[key]["period_start"],
                                                                  reports[key]["period_end"]),
                              key="dashboard_estimate_report")
        estimate_source = reports[matter]
        ranking = largest_estimates(registry, matter, limit=1)
        estimate_period = report_period(estimate_source["period_start"], estimate_source["period_end"])
        st.caption(f"{estimate_period} · All airports · {ranking.snapshot_count} report entries · "
                   f"[Official report]({estimate_source['url']})")
        if ranking.missing_count:
            st.caption(f"{ranking.missing_count} without a reported estimate")
        render_estimate_distribution(ranking, estimate_source, None, show_context=False)
