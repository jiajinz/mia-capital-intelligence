# Data updates

This log records the official PDFs included in MIA Capital Intelligence and the data taken from them. Dates identify dataset updates; reporting periods describe the source material. Page numbers refer to PDF pages.

## 2026-11-17 — Current source inventory

This entry documents the existing dataset as of November 17, 2026. It does not represent five PDFs newly added on this date. Their original ingestion dates are not recorded here.

The dataset uses **five distinct PDFs**: two quarterly infrastructure reports and three monthly Aviation Capital Program reports. They provide **222 quarterly report entries**, **12 contract-month records covering four contracts**, and **five airport operations updates**. Operations updates reuse one of the quarterly PDFs.

### Quarterly project records

- **Third Quarterly Report — October–December 2025.** [Official PDF, matter 260526](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/260526.pdf#page=11). Exhibit B, pages 11–12: **110 report entries**, including project IDs, descriptions and reported total cost estimates.
  - File version (SHA-256): `eaf845f4fb746a69940f38fe4655d27b56ab42effdbf9cfdd1dbc746a0fba878`.
- **Fourth Quarterly Report — January–March 2026.** [Official PDF, matter 261402](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261402.pdf#page=12). Exhibit B, pages 12–13: **112 report entries**, including project IDs, descriptions and reported total cost estimates.
  - File version (SHA-256): `84751b451da8b7d5e06cad6b1c24c870e563de5669c5f07325033c446bbaeb2a`.

Each entry is one row in one report. The same project ID can appear in both periods; 222 entries is not a count of unique projects.

### Contract spending records

Each monthly source contributes four contract records, with reported budgets and monthly, prior and cumulative expenditures. These records cover selected financial rows rather than the entire monthly report.

- **July 2026 Aviation Capital Program Report.** [Official PDF, matter 261147](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261147.pdf#page=28). Financial Exhibit B, page 28; supporting Summary of Changes, pages 19–20: **four contract-month records**.
  - File version (SHA-256): `355c1d4d130e9b8a0eeed6f160131fd6bc8db4b10ba5e75818a60a849bc02a62`.
- **August 2026 Aviation Capital Program Report.** [Official PDF, matter 261399](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261399.pdf#page=29). Financial Exhibit B, page 29; supporting Summary of Changes, pages 20–21: **four contract-month records**.
  - File version (SHA-256): `c62074ae4fdccda48bc716a399d585d8246e8d36a929633ef3afefe6c5505bbe`.
- **September 2026 Aviation Capital Program Report.** [Official PDF, matter 261400](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261400.pdf#page=30). Financial Exhibit B, page 30; supporting Summary of Changes, pages 21–22: **four contract-month records**.
  - File version (SHA-256): `ae45ec3eeaf1f54df04ad2255ed9ec3c0f3f647d3b2570b39272ff75efe9f9ae`.

The four contracts are A19-MDAD-02, A19-MDAD-01, E20-MDAD-03 and MDAD-CIP-V009A. Definitions and the treatment of reported dashes are described in [Sources and methodology](SOURCES_AND_METHODS.md#contract-spending).

### Airport operations updates

**Five updates** use the [Fourth Quarterly Report, matter 261402, memo pages 5–7](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261402.pdf#page=5), covering January–March 2026. They describe projects BA013A, CA004A, X078A, AB040A and Y118A and link to their corresponding Exhibit B records. This uses the same PDF version listed above.

The Dashboard implementation is documented in [PR #8](https://github.com/jiajinz/mia-capital-intelligence/pull/8).

<!-- BEGIN DISCOVERY EVENTS -->
## Report discovery history

These events track official files found by the source monitor. A discovered or revised file is not added to the application dataset by this log.

No discovery events recorded yet.

<!-- END DISCOVERY EVENTS -->
