# Project state

## Stage 2C — Public deployment verified

- Product: MIA Capital Intelligence, the Airport Infrastructure & Capital Projects Explorer. Sources & methodology attributes the published project records to Miami-Dade County. The explorer is an independent data project.
- Branch main. Stage 2C starts at Package A closeout `0d3e0dc91f6bed925a24516a1c3636a753d40699`. The Stage 2C commit uses the subject `feat(finance): add gated contract spending history`.
- On November 8, 2026 the owner explicitly authorized Stage 2C and exactly three production slices. These are 261147 financial p. 28 and summaries pp. 19–20, 261399 financial p. 29 and summaries pp. 20–21, and 261400 financial p. 30 and summaries pp. 21–22. See FINANCIAL_FEASIBILITY.md for the pinned hashes.
- The completed Contract spending history view offers four contract selections, one monthly USD chart and an exact monthly/cumulative table with evidence links. Its population is 12 contract-month rows for July–September 2026. Four dashes have explicit summary zero evidence. The accounting cutoff and basis are unknown. A19-MDAD-01 airport attribution and contract-to-project links remain unresolved.
- The local attestation validates for all 12 source rows, definition version `contract-expenditures-1.0` and input SHA-256 `3c90df7ea841061823781be3aa6a388f18c82d51fcf317c3d7f7b261a11622be`. Ordinary browser rendering was verified with the local review flag unset. The attestation is ignored by Git. Other installations need the reviewed record provisioned separately. See RUN_PUBLIC_DIRECTORY.md for the operating steps.
- The 222-observation quarterly registry is a separate artifact. The two project report populations remain 110 and 112, with 107 unverified candidate associations and zero verified cross-document project entities. The registry rebuild matches SHA-256 `56882b86f80101623eca8f33bf0cd8918c67cde588a3f55487d9f0cf7a72c5ab`.
- Python 3.13.1 full regression passed 160 tests with pinned study PDFs. Financial and quarterly rebuilds matched tracked bytes. PDF bindings, 12 row equations, 15 column totals, eight roll-forwards and four explicit zeros reconciled. Dependency and compilation checks passed.
- Browser QA covered the default gate with a preview-like query parameter, local pending-review banner, four choices, the A19-MDAD-02 September $98,135.01 monthly and $13,671,042.69 cumulative values, and the E20 September summary evidence. The approved-path app test uses a synthetic attestation in a temporary directory.
- The original release candidate passed a clean source-only startup and browser check in a fresh Python 3.13 environment. The clean suite passed 143 tests and skipped 17 PDF integration tests. All 160 tests passed with the pinned originals.
- The [public Streamlit deployment](https://mia-capital-intelligence.streamlit.app/) uses `main` and Python 3.13. The hosted directory, source link and estimate chart passed browser checks. After provisioning the existing attestation through Streamlit Secrets, the hosted financial view displayed all four contracts for July through September 2026 with monthly and cumulative values and official source links. The full local suite passed 164 tests with pinned PDFs.

## Portfolio explorer follow-up

- The local release candidate opens on Visual insights, with a compact source panel beside the ranking. Its estimate distribution counts indexed records within one report and opens a directory scoped to the chosen estimate range. The directory offers side-by-side source observations when one report is selected.
- The gated financial view explains the reported opening amount, July through September expenditures and September cumulative amount for each contract. The explanation uses the existing reviewed rows and links to the official financial pages.
- The T180B case uses the exact two source records and the earlier T180D record to explain the unresolved D60 scope. The comparison remains held pending equivalent scope and estimate-basis evidence.
- The full local suite passed 166 tests with the pinned PDFs. Browser checks covered the report-scoped directory, comparison links, financial explanation and 390 CSS pixel layout.
