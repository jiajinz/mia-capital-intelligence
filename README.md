# MIA Capital Intelligence

**An independent, read-only explorer of public records for Miami-Dade airport infrastructure.**

Find airport improvements, see the costs and spending that official reports publish, and check every figure against the page it came from.

**[🚀 Open the live explorer](https://mia-capital-intelligence.streamlit.app/)**

## What you can explore today

- **Project directory.** Search and filter 332 source records from three quarterly infrastructure reports. Each record shows its original wording, reported estimate, report period and page link.
- **Airport operations.** Five reported improvements at Miami International Airport, grouped by service area: security, gates and connections, baggage and runways. Each links to the memo page and the exhibit row it comes from.
- **Estimate distribution.** See how reported cost estimates are spread within one quarterly report. Selecting a range opens the matching records.
- **Contract spending.** Reported monthly and cumulative expenditures for four contracts, July to September 2026. Ordinary display of financial values requires an independent review record; without one, the view stays closed.

Facility-level details (type, status, milestones) are not yet indexed. The explorer says so rather than filling the gap.

## How the data stays current

- **Discovery.** A scheduled job checks official MIA and county sources each day for new or revised reports. It records each candidate file with its hash, size and reporting period, and proposes changes as pull requests.
- **Review before publication.** Nothing enters the public dataset without a human review. The explorer is read-only and reads only a versioned, validated dataset.
- **Availability.** A scheduled browser check visits the public app every six hours and confirms that records load.

Every public figure keeps its source: the official URL, file hash, page index and printed labels. Estimates, budgets, awards, expenditures and maintenance figures are kept separate and never summed across different meanings.

## AI agents in the workflow

The project uses AI agents as development tooling: monitoring official sources, running verification checks, preparing review packs and drafting analysis. They do not publish data or change public records. Each agent works in a bounded area, and the owner approves every admission, merge and publication.

## Monthly traffic and forecasts (internal research)

Monthly airport traffic reports (passengers, cargo, seats and aircraft movements) are collected and verified for 199 of the 201 months from January 2010 to September 2026. July 2010 has no source page yet, and June 2013 is held for review. They are not yet shown in the explorer. A separate forecasting track evaluates simple models on these series with pre-registered rules and reports every result, including the ones that do not beat the baseline. Forecasts stay internal until reviewed.

## Repository guide

- [Sources and methodology](docs/SOURCES_AND_METHODS.md): what each report covers, what each amount means, and how monthly and cumulative spending relate.
- [Data updates](docs/DATA_UPDATES.md): the official files included, discovery events and dataset changes, with dates and source links.

## Engineering

- **Stack.** Python 3.13, Streamlit, DuckDB for SQL over validated inputs, Plotly for charts, pdfplumber and PDFium for independent PDF extraction, and GitHub Actions for scheduled checks.
- **Verification.** Exact decimal arithmetic, row-level controls checked against a second PDF engine, reconciliation of totals and roll-forwards, and fail-closed display gates.
- **Tests.** The full suite runs in CI. Coverage is reported separately for lines and branches.

## Run locally

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run streamlit_app.py --server.address 127.0.0.1
```

Open the local URL that Streamlit prints.

## Test coverage

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m coverage erase
.venv/bin/python -m coverage run -m pytest
.venv/bin/python -m coverage combine
.venv/bin/python -m coverage json
.venv/bin/python -m coverage html
.venv/bin/python scripts/report_test_coverage.py
```

Reports are written to the ignored `tmp/coverage/` directory. Integration tests use pinned local PDFs in `data/raw/` and `MIA_STUDY_PDF_DIR`. Tests that need unavailable originals are skipped.

The discovery workflow reports coverage for its discovery modules in the Actions summary. The `discovery-test-coverage` artifact is kept for 30 days.
