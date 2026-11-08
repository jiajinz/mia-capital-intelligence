"""Read-only public directory for controlled MDAD source observations."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mia_capital_intelligence.directory_queries import (  # noqa: E402
    DirectoryFilters, SORTS, format_usd, search_records, source_detail,
)
from mia_capital_intelligence.public_registry import AIRPORTS, PublicRegistry, load_registry  # noqa: E402

st.set_page_config(page_title="MIA Capital Intelligence", page_icon="✈", layout="wide")


@st.cache_resource(show_spinner=False)
def published_registry() -> PublicRegistry:
    """Cache immutable published inputs, with a fresh in-memory SQL query per search."""
    return load_registry(ROOT)


def report_label(source: dict) -> str:
    return f"{source['period_start']} to {source['period_end']} · {source['matter_id']}"


def render_detail(registry: PublicRegistry, source_ref: str) -> None:
    detail = source_detail(registry, source_ref)
    source = detail["source"]
    with st.container(border=True):
        st.caption(f"SOURCE RECORD · {detail['project_id']} · {source['matter_id']}")
        st.subheader(detail["project_name"])
        value, context = st.columns([1, 2], gap="large")
        with value:
            st.metric("Total estimated cost · reported USD", format_usd(detail["estimate_usd"]))
            st.caption("Estimate as reported in this document.")
            st.write(f"**Airport**  {detail['airport_name']}")
            st.write("**Program**  Capital Improvement Program")
            st.caption("Detailed project type, status and milestones are not indexed.")
        with context:
            st.write("**Source report**")
            st.write(source["title"])
            st.write(f"Report coverage · {source['period_start']} to {source['period_end']}")
            st.caption("Coverage follows the memorandum. The project-data snapshot date is unconfirmed.")
            st.write(f"PDF page {detail['pdf_page']} · printed {detail['printed_page']} · data row {detail['row_ordinal']}")
            st.link_button(
                f"Open official PDF · page {detail['pdf_page']}",
                detail["source_page_url"], type="primary",
            )
            st.caption(detail["validation_status"] + ".")
        with st.expander("Original wording and evidence"):
            st.write("**Original project description**")
            st.text(detail["description_raw"])
            st.write("**Original estimate header and cell**")
            st.text(detail["estimate_header"] + "\n" + detail["estimate_raw"])
            st.caption(detail["description_status"] + ".")
            st.caption(detail["airport_evidence"] + ".")
            st.write(f"Printed fiscal-year caption · {source['matter_id']}")
            caption = (
                "FY 2024- 2025; for Period October 2025 - December 2025"
                if source["matter_id"] == "260526" else "FY 2025- 2026"
            )
            st.text(caption)
            st.write("**Document SHA-256**")
            st.code(source["sha256"], language=None)
            st.write("**Versioned source-row reference**")
            st.code(detail["source_ref"], language=None)
            st.caption("The project identity across documents is unresolved. This profile represents one source record.")
        if detail["candidate_source_refs"]:
            with st.expander("Same ID in another report · identity unresolved"):
                st.write(
                    "The shared ID is a candidate association. These records remain separate observations. "
                    "Their engineering scope and estimate basis require additional evidence before comparison."
                )
                for related_ref in detail["candidate_source_refs"]:
                    related = source_detail(registry, related_ref)
                    st.write(
                        f"**{related['project_id']} · {related['source']['matter_id']}**  "
                        f"{related['project_name']}"
                    )
                    st.write(
                        f"{related['source']['period_start']} to {related['source']['period_end']} · "
                        f"Source-reported estimate {format_usd(related['estimate_usd'])}"
                    )
                    st.link_button(
                        f"Open related official source · page {related['pdf_page']}",
                        related["source_page_url"],
                    )


def render_directory(registry: PublicRegistry) -> None:
    sources = {row["matter_id"]: row for row in registry.catalog}
    st.subheader("Project directory")
    st.write("Search publicly reported project records and open the original evidence.")
    query = st.text_input(
        "Search project ID, name or facility",
        placeholder="Try CA176A, chiller, boarding bridges or TMB",
        key="search",
    )
    airport_column, report_column, sort_column = st.columns([1, 2, 2])
    with airport_column:
        airport = st.selectbox(
            "Airport", [None, *AIRPORTS, "Unknown"], key="airport",
            format_func=lambda code: (
                "All airports" if code is None else
                "Unknown airport" if code == "Unknown" else f"{code} · {AIRPORTS[code]}"
            ),
        )
    with report_column:
        matter = st.selectbox(
            "Source report", [None, *[key for key, row in sources.items() if row["indexed_record_count"]]],
            format_func=lambda key: "All indexed reports" if key is None else report_label(sources[key]),
            key="source_report",
        )
    with sort_column:
        sort = st.selectbox("Sort records", list(SORTS), key="sort")
    results = search_records(registry, DirectoryFilters(query, airport, matter, sort))
    st.caption(
        f"{len(results)} matching source records of {len(registry.records)} indexed records · "
        "Source program: Capital Improvement Program. Counts refer to report rows; cross-report identities remain unresolved."
    )
    if not results:
        st.info("No source records match these filters. Try a shorter keyword or select all airports and reports.")
        return
    frame = pd.DataFrame([
        {"Project ID": row["project_id"], "Reported project description": row["project_name"],
         "Airport": row["airport_code"] or "Unknown",
         "Reporting period": f"{row['period_start']} to {row['period_end']}",
         "Reported estimate (USD)": format_usd(row["estimate_usd"]),
         "Source": row["matter_id"], "PDF page": row["pdf_page"]}
        for row in results
    ])
    st.dataframe(
        frame, hide_index=True, height=min(330, 40 + 35 * len(results)), width="stretch",
        column_config={
            "Reported project description": st.column_config.TextColumn(width="large"),
            "Reporting period": st.column_config.TextColumn(width="medium"),
        },
    )
    refs = [row["source_ref"] for row in results]
    by_ref = {row["source_ref"]: row for row in results}
    requested = st.query_params.get("record")
    if requested and requested not in {row.source_ref for row in registry.records}:
        st.warning("This record link is outside the current registry version. Choose an available result.")
    selected = st.selectbox(
        "Open a source record", refs,
        index=refs.index(requested) if requested in refs else 0,
        format_func=lambda ref: (
            f"{by_ref[ref]['project_id']} · {by_ref[ref]['matter_id']} · "
            f"{by_ref[ref]['project_name'][:110]}"
        ),
        key="selected_record",
    )
    st.query_params["record"] = selected
    render_detail(registry, selected)


def render_coverage(registry: PublicRegistry) -> None:
    st.subheader("Sources & data coverage")
    st.write(
        "Three official documents are cataloged. The directory indexes only Exhibit B in two infrastructure reports. "
        "This subset does not establish full airport project or capital-budget coverage."
    )
    st.dataframe(pd.DataFrame([
        {"Matter": row["matter_id"], "Report coverage": f"{row['period_start']} to {row['period_end']}",
         "Indexed records": row["indexed_record_count"], "Indexing coverage": row["indexing_status"]}
        for row in registry.catalog
    ]), hide_index=True, width="stretch")
    sources = {row["matter_id"]: row for row in registry.catalog}
    matter = st.selectbox(
        "Inspect a source document", list(sources),
        format_func=lambda key: f"{key} · {sources[key]['title']}",
        key="coverage_source",
    )
    source = sources[matter]
    with st.container(border=True):
        st.subheader(source["title"])
        st.caption(source["publishing_organization"])
        st.write(f"**Indexed records**  {source['indexed_record_count']} · {source['indexing_status']}")
        st.write(source["coverage_limit"])
        st.write(f"**Validation coverage**  {source['validation_status']}")
        if source["indexed_record_count"]:
            st.caption(
                "Original file identity was verified at registry build. Descriptions retain extracted source wording. "
                "Independent controls cover project IDs and estimates; scope and cross-report identity remain under review."
            )
        else:
            st.caption("Original file identity was verified at registry build. Its project rows are outside this public index.")
        st.write(f"**Reporting period**  {source['period_start']} to {source['period_end']}")
        st.write(f"**Memo date**  {source['memo_date']} · **Board acceptance**  {source['accepted_date']}")
        st.caption("The first public posting date and project-data freeze dates are unconfirmed.")
        pages = ", ".join(map(str, source["indexed_pdf_pages"])) or "None"
        st.write(f"**Indexed PDF pages**  {pages} · **Document pages**  {source['page_count']}")
        st.link_button("Open official source document", source["url"], type="primary")
        st.link_button("Open county legislative record", source["matter_url"])
        with st.expander("Document version and verification"):
            st.code(source["sha256"], language=None)
            st.write(f"SHA-256 · {source['size_bytes']:,} source bytes · matter {matter}")


st.title("MIA Capital Intelligence")
st.markdown("### Public airport infrastructure & capital projects")
st.write("Discover publicly reported projects, understand the source context and verify the original evidence.")
st.caption("Independent portfolio project · No affiliation with MDAD or HNTB.")
try:
    registry = published_registry()
except (ValueError, OSError, KeyError) as error:
    st.error("The published data could not be validated. Project records are unavailable until the data is repaired.")
    with st.expander("Data validation details"):
        st.text(str(error))
    st.stop()

st.caption(
    f"{len(registry.records)} source records · "
    f"{sum(row['indexed_record_count'] > 0 for row in registry.catalog)} partially indexed reports · "
    f"{len(registry.catalog)} cataloged documents · "
    "Source-reported estimates in USD"
)
directory_tab, coverage_tab = st.tabs(["Project directory", "Sources & coverage"])
with directory_tab:
    render_directory(registry)
with coverage_tab:
    render_coverage(registry)
st.divider()
st.caption(
    "Source observations retain their reporting context. Detailed status and milestone fields are not indexed in this slice. "
    "Candidate links provide navigation context; cross-report analytical comparisons require separate verification."
)
