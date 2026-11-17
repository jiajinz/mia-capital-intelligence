# Sources and methodology

MIA Capital Intelligence brings Miami-Dade County airport reports into a searchable explorer. Project profiles link to the original pages so readers can check descriptions, estimates, and updates in context.

## Report discovery and update history

A daily source check reads the [MDAD monthly report directory](https://www.miami-airport.com/transparency_report.asp) and the [county's legislative keyword search](https://www.miamidade.gov/govaction/keywordsearch.asp) for infrastructure reports under Directive 241354. It searches the current and previous calendar years and revisits known PDF addresses. File hashes distinguish exact copies from different versions, including revisions at the same address. A weekly unconditional download checks known files independently of HTTP cache headers.

If the keyword search fails, the monitor also checks up to three recently posted [BCC agendas](https://www.miamidade.gov/govaction/agendas.asp?Action=Agendas&Oper=DisplayList). The run retains an incomplete-coverage status until the keyword search recovers.

The [data update log](DATA_UPDATES.md) lists current sources and subsequent discovery events. **Discovered** identifies a candidate file; its project and financial records enter the application only through a separate dataset update. Reporting periods come from the PDF's explicit report label or date range. Unknown periods remain unknown. Checks with no file changes leave the log unchanged.

The source monitor downloads PDFs into temporary working storage. Newly discovered or revised file bytes are saved in the Actions artifact named `official-report-pdfs`, with a 30-day retention period. Repeat checks of unchanged known PDF addresses do not save another copy. The repository stores source links, hashes, metadata and accepted extracted records; raw PDFs are excluded from Git. Official PDF links remain available in the log and project profiles. Artifact storage is temporary; a permanent cloud archive is not configured.

## Availability

A scheduled browser check visits the public app every six hours and verifies that project records load. Streamlit Community Cloud puts apps to sleep after 12 hours without traffic, and a sleeping app shows a wake-up button. Automated visits are a best-effort measure, and scheduled checks can be delayed or disabled after a public repository is inactive for 60 days. [Streamlit hosting](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app#app-hibernation) · [Scheduled checks](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

## Projects and estimates

The directory shows **222 report entries** from the Capital Improvement Program tables in two quarterly infrastructure reports. Each entry is one row in one report. An ID can appear in both reports, so the entry count does not represent a count of unique projects.

- **October–December 2025:** 110 entries from [matter 260526, Exhibit B, pages 11–12](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/260526.pdf#page=11).
- **January–March 2026:** 112 entries from [matter 261402, Exhibit B, pages 12–13](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261402.pdf#page=12).

**Reported total cost estimate** is the dollar amount listed for an entry in Exhibit B. The estimate chart groups those amounts into bands and counts entries within each band. Project profiles show the estimate from the selected report. Airport labels use the airport code in the published project description. When the description does not identify a single airport, the airport is shown as unknown.

## Airport operations

The Dashboard includes five updates for Miami International Airport from the January–March 2026 report. The cards summarize the work described in the memo, such as replacing checkpoint equipment in stages or adding gates. **View project** opens the corresponding Exhibit B record. **Read report update** opens the memo page that describes the work. [Matter 261402, memo pages 5–7](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261402.pdf#page=5)

## Contract spending

The spending view covers **four contracts** across the following three monthly Aviation Capital Program reports:

- **July 2026:** [Financial table, page 28](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261147.pdf#page=28) · [Summary of Changes, pages 19–20](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261147.pdf#page=19)
- **August 2026:** [Financial table, page 29](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261399.pdf#page=29) · [Summary of Changes, pages 20–21](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261399.pdf#page=20)
- **September 2026:** [Financial table, page 30](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261400.pdf#page=30) · [Summary of Changes, pages 21–22](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261400.pdf#page=21)

**Monthly expenditures** come from the current-month column in the financial table. A dash is shown as $0.00 only when the same contract's monthly summary explicitly reports zero. The month label follows the report. The accounting cutoff and accounting basis are unknown.

**Cumulative expenditures** come from the to-date column. For a contract, its cumulative amount through September equals expenditures reported before July plus the expenditures reported for July, August, and September. Cumulative amounts already include prior spending. The view reports amounts per contract in USD and keeps them distinct from the quarterly project estimates.
