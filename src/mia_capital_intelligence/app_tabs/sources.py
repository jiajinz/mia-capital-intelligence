"""Sources & Coverage tab: source documents, record counts and the Concourse D case study."""

import pandas as pd
import streamlit as st

from mia_capital_intelligence.app_tabs.app_common import (
    profile_permalink, render_record_summary, report_period,
)
from mia_capital_intelligence.directory_queries import source_detail
from mia_capital_intelligence.operations_updates import OPERATIONS_MATTER, operations_updates
from mia_capital_intelligence.public_registry import PublicRegistry


CASE_REFS = (
    "260526:eaf845f4fb746a69940f38fe4655d27b56ab42effdbf9cfdd1dbc746a0fba878:B:11:63",
    "261402:84751b451da8b7d5e06cad6b1c24c870e563de5669c5f07325033c446bbaeb2a:B:12:65",
    "260526:eaf845f4fb746a69940f38fe4655d27b56ab42effdbf9cfdd1dbc746a0fba878:B:11:64",
)


def render_coverage(registry: PublicRegistry) -> None:
    st.subheader("Sources & Coverage")
    st.caption("Underlying records are published by Miami-Dade County.")
    st.markdown("[Data update history](https://github.com/jiajinz/mia-capital-intelligence/blob/main/docs/DATA_UPDATES.md)")
    if set(CASE_REFS).issubset(row.source_ref for row in registry.records):
        with st.expander("Case study · Concourse D west extension"):
            st.write(
                "Both reports list T180B with the same building expansion and apron description. "
                "The earlier report separately lists T180D for D60 apron and utilities."
            )
            for column, reference in zip(st.columns(2), CASE_REFS[:2], strict=True):
                with column:
                    render_record_summary(registry, reference, show_scope=True)
            earlier_apron = source_detail(registry, CASE_REFS[2])
            st.link_button("Open the earlier T180D source record", profile_permalink(earlier_apron["source_ref"]))
    st.write(
        f"The directory contains {len(registry.records)} source records from Exhibit B of two quarterly reports. "
        "Each record represents one entry in one report."
    )
    st.dataframe(pd.DataFrame([
        {"Matter": row["matter_id"], "Report coverage": report_period(row["period_start"], row["period_end"]),
         "Source records": row["indexed_record_count"]}
        for row in registry.catalog
    ]), hide_index=True, width="stretch")
    sources = {row["matter_id"]: row for row in registry.catalog}
    st.session_state.setdefault("coverage_source", next(iter(sources)))
    matter = st.radio(
        "Inspect a source document", list(sources), horizontal=True,
        format_func=lambda key: f"{key} · {sources[key]['title']}", key="coverage_source",
    )
    source = sources[matter]
    with st.container(border=True):
        st.subheader(source["title"])
        st.caption(source["publishing_organization"])
        st.write(f"**Reporting period**  {source['period_start']} to {source['period_end']}")
        st.write(f"**Memo date**  {source['memo_date']} · **Board acceptance**  {source['accepted_date']}")
        if source["indexed_pdf_pages"]:
            pages = ", ".join(map(str, source["indexed_pdf_pages"]))
            st.write(f"**Source records**  {source['indexed_record_count']} source records from Exhibit B, PDF pages {pages}.")
        if matter == OPERATIONS_MATTER and (updates := operations_updates(registry)):
            st.write(f"**Dashboard**  {len(updates)} project updates from the report narrative, PDF pages 5–7.")
        if matter == "261400":
            st.write("**Contract spending**  Exhibit B, PDF page 30, and the Summary of Changes, pages 21–22.")
        st.link_button("Open official source document", source["url"], type="primary")
        st.link_button("Open county legislative record", source["matter_url"])
