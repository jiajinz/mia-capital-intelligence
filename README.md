# ✈️ MIA Capital Intelligence

**Airport Infrastructure & Capital Projects Explorer**

Explore Miami-Dade County airport projects, see reported cost estimates and contract spending, and trace the figures back to the original reports.

**[🚀 Open live app](https://mia-capital-intelligence.streamlit.app/)**

## 🔎 What you can explore

- **Project directory.** Search and filter 222 source records from two quarterly infrastructure reports. Open a record to see its original wording and source page.
- **Cost estimates.** See which projects have the largest reported estimates within a selected quarterly report.
- **Contract spending.** View reported monthly and cumulative expenditures for four contracts from July through September 2026.

## 📄 Sources and coverage

The explorer is an independent data project based on public Miami-Dade County records. Project estimates and contract expenditures are presented separately, with links to the official PDFs. [Source audit](docs/SOURCE_AUDIT.md) · [Financial methodology](docs/FINANCIAL_FEASIBILITY.md)

## Run locally

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run streamlit_app.py --server.address 127.0.0.1
```

Open the local URL printed by Streamlit. [Operating guide and validation](docs/RUN_PUBLIC_DIRECTORY.md)
