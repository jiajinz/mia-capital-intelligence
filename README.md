# ✈️ MIA Capital Intelligence

**Airport Infrastructure & Capital Projects Explorer**

Explore airport improvements, reported project costs, and contract spending from Miami-Dade County. This independent data project makes public reports easier to browse by linking each figure and project update to its original page. It is not affiliated with or endorsed by Miami International Airport or Miami-Dade County. Its colors and typefaces follow the public website of Miami International Airport for familiarity only.

**[🚀 Open live app](https://mia-capital-intelligence.streamlit.app/)**

## 🔎 What you can explore

- **Project directory.** Search and filter 222 source records from two quarterly infrastructure reports. Open a record to see its original wording and source page.
- **Airport operations.** Browse five reported improvements at Miami International Airport by service area, including security, gates and connections, baggage, and runways.
- **Cost estimates.** See which projects have the largest reported estimates within a selected quarterly report.
- **Contract spending.** View reported monthly and cumulative expenditures for four contracts from July through September 2026.

## 📄 Sources and coverage

[Sources & methodology](docs/SOURCES_AND_METHODS.md) explains what the reports cover, what each amount means, and how monthly and cumulative spending relate.

[Data updates](docs/DATA_UPDATES.md) lists included PDFs and records newly discovered or revised official files, with reporting periods and source links.

## Run locally

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run streamlit_app.py --server.address 127.0.0.1
```

Open the local URL printed by Streamlit.

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

The summary reports line and branch coverage separately. Measurement includes application, package and runtime script code, including unexecuted files. Tests, temporary files and the coverage reporting helper are excluded. Reports remain under the ignored `tmp/coverage/` directory. Integration tests use pinned local PDFs in `data/raw/` and `MIA_STUDY_PDF_DIR`; tests requiring unavailable originals are skipped.

The discovery workflow reports coverage for its three discovery modules and two entry scripts in the Actions summary. Its `discovery-test-coverage` artifact contains JSON, XML and HTML reports and is retained for 30 days.
