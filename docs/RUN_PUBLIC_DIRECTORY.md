# Run and inspect the public directory

This Airport Infrastructure & Capital Projects Explorer serves controlled source observations, with published evidence and explicit coverage.

## Start locally

From the repository root on macOS or Linux:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m streamlit run streamlit_app.py
```

Open the Local URL printed by Streamlit. The default port is 8501. The committed data/public/registry.json, source inventory and row controls are sufficient for public runtime operation. Raw PDFs, comparison decisions and a persistent database are unnecessary at runtime. The application performs no persistent data writes. Local browser preview is a smoke test and provides no hosting or deployment claim.

To rebuild the public inputs from verified originals, follow SOURCE_AUDIT.md's acquisition instructions, then run:

```sh
PYTHONPATH=src .venv/bin/python -m mia_capital_intelligence.public_registry build
PYTHONPATH=src .venv/bin/python -m mia_capital_intelligence.public_registry check
.venv/bin/python -m pytest -q
```

The builder validates all three cataloged source versions, loads only the two approved Exhibit B slices, checks every ID/amount pair, generates explicitly unverified candidate links and validates the complete artifact. It atomically replaces the JSON only after validation. A failed extraction preserves the prior artifact. Byte-identical inputs produce byte-identical output.

## Public acceptance walkthrough

1. In Project directory, search CA176A. Expect two source records, one for each reporting period. Select the later 261402 record. Its original description is MIA E Satellite Terminal Seating Ph2 and its reported total estimated cost is 3,191,832 USD.
2. Check the record's source coverage period, PDF p. 12, printed MDC012 and data row 41. Open Original wording and evidence to inspect the raw header, raw amount, description and checksum.
3. Open the official PDF link. Its URL ends in /261402.pdf#page=12. Confirm that the county report opens at page 12 of 13. Expand the same-ID section to see the earlier record as an unverified candidate association. It supplies no financial change or confirmed project history.
4. Clear the search and choose Unknown airport. Expect 15 source records. Choose TMB to see 6 records and filter to 261402 to see 3. Filtering changes the selectable record set as well as the table.
5. Enter an unmatched search term. Expect an explanatory empty-result message and continued access to the Sources & methodology tab.
6. In Sources & methodology, confirm 110, 112 and 0 indexed records for matters 260526, 261402 and 261400. Inspect the September report and its Cataloged only label. Review memo/acceptance dates, source URLs, indexed pages, checksum and limitations.

The results table supports horizontal scrolling on narrow viewports. The source selector and individual detail provide the full name and evidence even when table columns are outside the viewport. Detailed work categories, construction status, standalone facility classifications and milestone values remain unindexed and are labeled accordingly.

## PyCharm debugging

Use the repository .venv interpreter and project root as the working directory. Create a Python module run configuration for streamlit, with parameters run streamlit_app.py. No global settings changes are needed.

For the data path, create a module configuration for mia_capital_intelligence.public_registry with parameters build and PYTHONPATH set to the repository src directory. Break at source_records.load_exhibit_b, row_controls.validate_page_rows, public_registry.validate_registry and directory_queries.search_records. Inspect CA176A's document-specific source reference and the Decimal estimate. In the Streamlit run, break at render_detail to see the same source_ref become the PDF page URL.

## Validation evidence

The Stage 1 baseline has 115 passing tests. Stage 2 adds analytical, financial-research and chart-interaction regression cases; see REVIEW_PACKET.md for the current full-suite result. Streamlit AppTest covers the original nine UI scenarios, covering default rendering, real search/detail, filters, unknown airport, empty results, catalog-only coverage, versioned record links, stale links and corrupt-input error handling. Those tests supplement browser checks.

The app was also run on localhost, returned HTTP 200 and a healthy Streamlit response, and was inspected in the actual in-app browser. Browser actions verified CA176A search and source details, candidate wording, a direct official PDF opening at page 12, source coverage, an empty search and unknown-airport filtering. Screenshots are in docs/screenshots. They reflect the normal narrow in-app preview, with scrollable content. Other browsers, devices and Streamlit Community Cloud remain outside this verification pass.


## Stage 2 chart acceptance and debugging

1. Open Visual insights. Confirm one selected report (default 261402), memo August 6, 2026, coverage January–March 2026 and unknown project-data freeze date. The default chart shows 10 of 112 matching report rows, with zero unknown estimates.
2. Confirm T180B leads at $1,066,231,593. Click the V008B bar and confirm the source profile changes to its $896,021,864 estimate, matter 261402, PDF p. 13, printed MDC013, data row 6. Open its official page link.
3. Choose TMB. The matching population becomes three records in the same 112-row report. Choose report 260526 and confirm the denominator changes to 110. The chart never combines both reports. A filter-specific chart key prevents an old selection from carrying into a different population.
4. Use Explore a chart record by keyboard as an alternative to clicking bars. Expand Chart values and source pages for full descriptions, exact amounts and official evidence links. Empty chart search has an explicit state; unknown airport records remain available.
5. Confirm both directory and chart profiles show source dates, missing status/milestones, raw evidence and unresolved same-ID associations. The owner primary description is accompanied by a current-availability line so the roadmap is not mistaken for implemented progress/spending features.

In PyCharm, keep the same repository-local interpreter and Streamlit module configuration. Break at estimate_insights.largest_estimates: inspect matter_id and DirectoryFilters before SQL executes. Step into directory_queries.search_records and examine DECIMAL(18,2), the bound report parameter, exact Decimal results and stable ordering. Back in largest_estimates, inspect snapshot_count, matching_count, missing_count and the limited rows. Break at estimate_figure to inspect exact customdata versus float bar coordinates. Break at selected_source_ref after clicking a bar, then render_detail to trace the same immutable key to the source page. AppTest exercises the event adapter using a simulated return value; actual chart clicks require a browser.

For debugging outside Streamlit, configure pytest for tests/test_estimate_insights.py. Synthetic missing-value cases are tests only; never alter production registry values to debug a chart. The financial study checker is a separate script run configuration, scripts/check_financial_feasibility.py. Its inputs are docs/research/financial_snapshots.json, not public runtime data. FINANCIAL_FEASIBILITY.md explains the source and date limitations.

API references: [Streamlit 1.51 chart selection contract](https://docs.streamlit.io/1.51.0/develop/api-reference/charts/st.plotly_chart) and [Plotly horizontal bar charts](https://plotly.com/python/horizontal-bar-charts/). Plotly renders the validated query result; it does not query or validate the PDFs itself.
