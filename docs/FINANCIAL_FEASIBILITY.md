# Stage 2B — Financial data feasibility

## Finding and recommendation

**Conditional feasibility for a small contract spending-history section.** Three consecutive reported months, July–September 2026, contain the same four contracts and compatible financial columns. All 12 contract arithmetic checks, 15 printed column totals and eight contract roll-forwards reconcile to the cent. This is a bounded research result, not production ingestion or independent human sign-off. No financial chart or contract/project join is published.

Recommend Stage 2C focus on reported-month **contract spending history** inside the existing explorer, after independent review and owner authorization. The approval package below defines the proposed monthly bar chart and exact-value table for the four sampled contracts.

## Official sources and coverage

The [official airport report index](https://www.miami-airport.com/transparency_report.asp) describes reporting under Ordinance 19-122, which limits the series to capital projects approved under that ordinance. It lists July, August and September 2026. The financial exhibit population is narrower still: four contract rows in each sampled issue. It is not a census of all MDAD capital activity, and not the quarterly infrastructure Exhibit B project population.

- [July, matter 261147](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261147.pdf): 43 pages, 7,334,076 bytes; memo September 1, 2026. Financial Exhibit B PDF p. 28 / printed MDC028 / Page 1 of 1. Month label on the preceding Exhibit B cover p. 27; Summary of Changes pp. 19–20. SHA-256 `355c1d4d130e9b8a0eeed6f160131fd6bc8db4b10ba5e75818a60a849bc02a62`.
- [August, matter 261399](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261399.pdf): 49 pages, 6,084,317 bytes; memo October 6, 2026. Financial Exhibit B PDF p. 29 / MDC029 / Page 1 of 1; month cover p. 28; summary pp. 20–21. SHA-256 `c62074ae4fdccda48bc716a399d585d8246e8d36a929633ef3afefe6c5505bbe`.
- [September, matter 261400](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261400.pdf): 40 pages, 3,916,380 bytes; memo October 6, 2026. Financial Exhibit B PDF p. 30 / MDC030 / Page 1 of 1; month cover p. 29; summary pp. 21–22. SHA-256 `ae45ec3eeaf1f54df04ad2255ed9ec3c0f3f647d3b2570b39272ff75efe9f9ae`.

Acquired the two additional official PDFs for this study on November 8, 2026 into temporary local storage. September uses the already pinned original. Study sources are isolated in [research/financial_snapshots.json](research/financial_snapshots.json); the production inventory, registry and 222 project observations remain unchanged. Raw PDFs are untracked. No claim is made that September is the latest available issue; three consecutive issues suffice for this bounded study.

## Identity, financial definitions and dates

The financial row order is stable: A19-MDAD-02, A19-MDAD-01, E20-MDAD--03 and MDAD-CIP-V009A. The E20 identifier has a double hyphen in all three financial exhibits and a single hyphen in each Summary of Changes. The research evidence records both and an explicit alias to E20-MDAD-03. This is an exhibit-specific correspondence, not a generic punctuation-removal rule. All four IDs and descriptions were checked across the three issues. No quarterly project ID membership is established. A19-MDAD-01 has an unresolved airport attribution. Its financial row reads “MIA Terminal Wide Re-roofing and Lightning System Upgrades”. Summary row 1 on the first summary page in each issue adds “Miami Executive Airport”. The research records preserve both descriptions and a null airport attribution.

Each issue separates FY 2025–2026 Adopted Budget Amount, Current Approved Budget Amount, Prior Expenditures, Current Month Expenditures and Cumulative Expenditures to Date. Reinspection of August PDF p. 29 / MDC029 confirms the exact heading “Cumulative Expenditures to Date”. “Current” appears in “Current Approved Budget Amount” and “Current Month Expenditures”. Budgets stay constant across these issues: adopted $60,442,012.75 and approved $57,887,327.75 for these four rows. They must not be summed across months. MDAD-CIP-V009A accounts for the adopted/approved difference; its financial approved budget is $13,301,531.00, distinct from the procurement award figure $13,301,531.44.

The month comes from the Exhibit B cover and Summary of Changes, not memo or legislative action dates. [August's legislative record](https://www.miamidade.gov/govaction/matter.asp?file=true&matter=261399) lists introduction August 6 and acceptance October 6. This does not independently establish a bank/cash/ledger cutoff. Label future charts “reported month” and “reported expenditures.” The sources do not establish cash-versus-accrual accounting or transaction dates. Avoid claiming independently audited actual cash payments. These expenditure fields are distinct from estimated total project costs; consistency is established only for this sampled series.

## Reconciliation evidence

All amounts below are USD. Source financial row locators and original visual cell strings are retained per contract and document, with original column headings and summary-page evidence. These are agent visual transcriptions, not outputs from an approved production extractor. Independent human review remains pending.

- July: prior $40,982,760.80 + current month $537,673.09 = cumulative $41,520,433.89. Monthly components in financial row order: $80,212.05; $138,453.39; $319,007.65; $0.00.
- August: prior $41,520,433.89 + current month $206,061.07 = cumulative $41,726,494.96. Monthly components: $103,511.27; $1,566.00; $100,983.80; $0.00.
- September: prior $41,726,494.96 + current month $194,680.63 = cumulative $41,921,175.59. Monthly components: $98,135.01; $96,545.62; $0.00; $0.00.

For A19-MDAD-02, July cumulative $13,469,396.41 equals August prior. August cumulative $13,572,907.68 equals September prior; adding September's $98,135.01 yields $13,671,042.69. All other contract roll-forwards also agree. A cumulative series includes pre-July expenditures; summing July–September monthly bars does not reproduce the September cumulative amount without the opening balance.

MDAD-CIP-V009A has a dash in each financial monthly cell; E20 has a dash in September. Every such resolution uses a separate, explicit $0.00 on that month's Summary of Changes. No general dash-to-zero rule is applied. Unknowns must remain null when corroborating evidence is unavailable.

The financial pages were visually inspected in landscape orientation. Closeout rechecked the pinned originals and extracted the three financial pages and six summary pages using PDFium. Study evidence records one-based PDF pages and financial data-row ordinals, ordered monetary headings and original cell strings. Summary locators are one-based row ordinals within the corresponding page. The summary contract ID, description and three expenditure cells come from that row. For E20 the financial row is 3 in each issue and its summary row is 1 on PDF pp. 20, 21 and 22 respectively. V009A's dash is on financial row 4 in each issue and its explicit zero is in summary row 3 on pp. 19, 20 and 21. E20's September dash is corroborated by its own summary row on p. 22. The structured resolution token is `summary_explicit_zero`.

Without `--pdf-dir`, the checker validates static issue and heading pins and reconciles study values with Decimal. At baseline d6d4f1e even the PDF identity check accepted a wrong page, wrong summary locator, unrelated dash note and a balanced three-issue reassociation of both A19 contracts. With `--pdf-dir`, the closeout checker first pins each matter, month, SHA-256 and exhibit pages. It then reads the pinned bytes, checks the five printed headings in order and compares each raw financial cell, description, contract ID, row ordinal and total with the extracted record. Each summary contract block must match its issue month, page, ordinal, raw ID, description and expenditure cells. July's font-encoded hyphen and layout whitespace are normalized. The comparison catches unchanged-total row swaps and rejects zero evidence borrowed from a different contract. This parser is specific to the three pinned layouts. Independent named human confirmation is pending.

Reproduce:

```sh
.venv/bin/python scripts/check_financial_feasibility.py
.venv/bin/python -m pytest -q tests/test_financial_feasibility.py
# Source-binding verification requires pinned files named 261147.pdf, 261399.pdf and 261400.pdf.
.venv/bin/python scripts/check_financial_feasibility.py --pdf-dir /path/to/study-pdfs
MIA_STUDY_PDF_DIR=/path/to/study-pdfs .venv/bin/python -m pytest -q tests/test_financial_feasibility.py
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

## Stage 2C approval package

- Approve production use of exactly July 2026 matter 261147 Exhibit B PDF p. 28 and summary pp. 19–20, August 2026 matter 261399 Exhibit B p. 29 and summary pp. 20–21, and September 2026 matter 261400 Exhibit B p. 30 and summary pp. 21–22. The exact versions and hashes are listed above. The quarterly registry and its coverage remain separate.
- Approve one read-only Contract spending history section. It would offer four selections (A19-MDAD-02, A19-MDAD-01, E20-MDAD-03 and MDAD-CIP-V009A), one USD bar chart of reported monthly expenditures for July–September 2026, and a table of exact monthly and cumulative values, reported months and original evidence links. Default to A19-MDAD-02, which has three reported monthly values. The chart scope is the sampled contract series. Cumulative charts, budget ratios, milestones, project links, airport-wide totals and hosting are separate decisions.
- Accept the definitions and named independent human review of the 12 financial and summary rows, all five monetary headings, the three scoped E20 alias bindings and four explicit summary zeros. Review A19-MDAD-01's ambiguous description and preserve the unresolved attribution. Reported month comes from the issue. Ledger cutoff and cash/accrual basis remain unknown. Keep future gaps explicit.
- Authorize implementation only after the preceding decisions. The production input would require versioned row keys, exact Decimal values, named evidence sign-off and fail-closed replacement checks. The Package A research control and the successful reconciliation leave the named human review and production authorization pending.
