# Stage 2B — Financial data feasibility

## Finding and recommendation

**Conditional feasibility for a small contract spending-history section.** Three consecutive reported months, July–September 2026, contain the same four contracts and compatible financial columns. All 12 contract arithmetic checks, 15 printed column totals and eight contract roll-forwards reconcile to the cent. This is a bounded research result, not production ingestion or independent human sign-off. No financial chart or contract/project join is published.

Recommend Stage 2C focus on reported-month **contract spending history** inside the existing explorer, after independent review and owner authorization. Start with monthly bars and a separately labeled cumulative line, selectable by contract. Four contracts do not justify a standalone Financial Explorer or an airport-wide spending claim. Milestones and additional project integration remain valuable later work, but lack an equivalent controlled field set today.

## Official sources and coverage

The [official airport report index](https://www.miami-airport.com/transparency_report.asp) describes reporting under Ordinance 19-122, which limits the series to capital projects approved under that ordinance. It lists July, August and September 2026. The financial exhibit population is narrower still: four contract rows in each sampled issue. It is not a census of all MDAD capital activity, and not the quarterly infrastructure Exhibit B project population.

- [July, matter 261147](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261147.pdf): 43 pages, 7,334,076 bytes; memo September 1, 2026. Financial Exhibit B PDF p. 28 / printed MDC028 / Page 1 of 1. Month label on the preceding Exhibit B cover p. 27; Summary of Changes pp. 19–20. SHA-256 `355c1d4d130e9b8a0eeed6f160131fd6bc8db4b10ba5e75818a60a849bc02a62`.
- [August, matter 261399](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261399.pdf): 49 pages, 6,084,317 bytes; memo October 6, 2026. Financial Exhibit B PDF p. 29 / MDC029 / Page 1 of 1; month cover p. 28; summary pp. 20–21. SHA-256 `c62074ae4fdccda48bc716a399d585d8246e8d36a929633ef3afefe6c5505bbe`.
- [September, matter 261400](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261400.pdf): 40 pages, 3,916,380 bytes; memo October 6, 2026. Financial Exhibit B PDF p. 30 / MDC030 / Page 1 of 1; month cover p. 29; summary pp. 21–22. SHA-256 `ae45ec3eeaf1f54df04ad2255ed9ec3c0f3f647d3b2570b39272ff75efe9f9ae`.

Acquired the two additional official PDFs for this study on November 8, 2026 into temporary local storage. September uses the already pinned original. Study sources are isolated in [research/financial_snapshots.json](research/financial_snapshots.json); the production inventory, registry and 222 project observations remain unchanged. Raw PDFs are untracked. No claim is made that September is the latest available issue; three consecutive issues suffice for this bounded study.

## Identity, financial definitions and dates

The financial row order is stable: A19-MDAD-02, A19-MDAD-01, E20-MDAD--03 and MDAD-CIP-V009A. The E20 identifier has a double hyphen in all three financial exhibits and a single hyphen in each Summary of Changes. The research evidence records both and an explicit alias to E20-MDAD-03. This is an exhibit-specific correspondence, not a generic punctuation-removal rule. All four IDs and descriptions were checked across the three issues. No quarterly project ID membership is established.

Each issue separates FY 2025–2026 Adopted Budget Amount, Current Approved Budget Amount, Prior Expenditures, Current Month Expenditures and Cumulative Expenditures to Date. August prints “Current Cumulative Expenditures to Date”; the summary and arithmetic support the same cumulative measure in this sample. Budgets stay constant across these issues: adopted $60,442,012.75 and approved $57,887,327.75 for these four rows. They must not be summed across months. MDAD-CIP-V009A accounts for the adopted/approved difference; its financial approved budget is $13,301,531.00, distinct from the procurement award figure $13,301,531.44.

The month comes from the Exhibit B cover and Summary of Changes, not memo or legislative action dates. [August's legislative record](https://www.miamidade.gov/govaction/matter.asp?file=true&matter=261399) lists introduction August 6 and acceptance October 6. This does not independently establish a bank/cash/ledger cutoff. Label future charts “reported month” and “reported expenditures.” The sources do not establish cash-versus-accrual accounting or transaction dates. Avoid claiming independently audited actual cash payments. These expenditure fields are distinct from estimated total project costs; consistency is established only for this sampled series.

## Reconciliation evidence

All amounts below are USD. Source financial row locators and original visual cell strings are retained per contract and document, with original column headings and summary-page evidence. These are agent visual transcriptions, not outputs from an approved production extractor. Independent human review remains pending.

- July: prior $40,982,760.80 + current month $537,673.09 = cumulative $41,520,433.89. Monthly components in financial row order: $80,212.05; $138,453.39; $319,007.65; $0.00.
- August: prior $41,520,433.89 + current month $206,061.07 = cumulative $41,726,494.96. Monthly components: $103,511.27; $1,566.00; $100,983.80; $0.00.
- September: prior $41,726,494.96 + current month $194,680.63 = cumulative $41,921,175.59. Monthly components: $98,135.01; $96,545.62; $0.00; $0.00.

For A19-MDAD-02, July cumulative $13,469,396.41 equals August prior. August cumulative $13,572,907.68 equals September prior; adding September's $98,135.01 yields $13,671,042.69. All other contract roll-forwards also agree. A cumulative series includes pre-July expenditures; summing July–September monthly bars does not reproduce the September cumulative amount without the opening balance.

MDAD-CIP-V009A has a dash in each financial monthly cell; E20 has a dash in September. Every such resolution uses a separate, explicit $0.00 on that month's Summary of Changes. No general dash-to-zero rule is applied. Unknowns must remain null when corroborating evidence is unavailable.

Financial pages were rendered, rotated to readable landscape orientation and visually inspected in full, including headings, four row associations, five monetary columns, totals and printed page labels. Summary text was cross-checked for the expenditure amounts and zeros. The research checker uses Decimal and independently tests arithmetic, summary agreement, population, printed totals and roll-forwards. Arithmetic agreement alone cannot prove source transcription or accounting completeness.

Reproduce:

```sh
.venv/bin/python scripts/check_financial_feasibility.py
.venv/bin/python -m pytest -q tests/test_financial_feasibility.py
# Optional: verify all downloaded file identities as well (names 261147.pdf, 261399.pdf, 261400.pdf):
.venv/bin/python scripts/check_financial_feasibility.py --pdf-dir /path/to/study-pdfs
```

Download only from the explicit official URLs above, verify size/hash before use, and keep originals outside commits. Reacquisition may produce revised bytes; treat that as a new document version and re-review.

## Feasibility of planned insights

**Monthly spending trend — conditionally supported.** Twelve reported contract-month observations exist and reconcile. Publish only after independent transcription review and a controlled financial input contract with immutable sources, aliases, zero evidence, coverage and month semantics. Three points support a short history, not a trend forecast. Gaps must not be interpolated.

**Cumulative spending — conditionally supported.** The series reconciles by contract with a documented opening balance. Keep it separate from monthly spending and never sum cumulative snapshots. Chart corrections or restatements must remain visible in later issues.

**Budget vs. spent — conditionally supported at contract grain.** Current approved budget and cumulative expenditures coexist in the same financial row. Any percentage is expenditure utilization of that contract budget. It is not physical construction completion. Do not mix adopted budgets or original awards into that denominator.

**Project progress timeline — deferred.** The financial table has Project Phase “Awarded,” Estimated Completion Date, expenditure threshold indicators and comments. MDAD-CIP-V009A simultaneously says “Awarded,” estimated completion 06/08/24 and “Project closed.” These are distinct source fields, not a reliable physical-completion measurement. Forecast dates must not become actual milestones, and expenditure threshold marks must not become construction progress. Extract and verify date semantics and corroborating completion evidence before publishing timelines.

**Airport improvements by facility/category — deferred beyond the current explicit airport-token facet.** Quarterly descriptions support limited airport classification, with unknowns preserved. Detailed facilities and categories have no approved structured extraction. Financial contract descriptions can span multiple services/facilities and do not supply trustworthy project membership.

## Integration limitations and next gate

No tested contract-to-quarterly-project association was established. A19-MDAD-02 covers professional facility services; E20 is mapping/LiDAR services. Neither should become a single infrastructure project. For V009A, September's financial description and procurement Project Name / Description both refer to TMB runway mitigation. The procurement OMB Project Description is broader: it lists work at Opa-Locka, Homestead and TMB under OMB project 2000001049 (Exhibit A, PDF pp. 24 and 28). This is evidence of different field granularity, not a demonstrated contradiction. It does not establish membership in a quarterly infrastructure project. A contract ID can anchor financial snapshots without proving a capital-project mapping.

Before Stage 2C publication, independently review all 12 rows, confirm the explicit alias and reported-month semantics, approve the study sources for production, define a fail-closed financial schema and row controls, and verify any additional months separately. Carry evidence and unknown accounting cutoffs into the UI. Integrate a small Contract spending history section using existing source profiles; keep project membership unresolved until documentary identifiers support it. Milestone work and broader source integration should follow as separately scoped increments.
