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

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report June 2026**

- Reporting period: 2026-06-01 to 2026-06-30.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20June%202026.pdf>) · 52 PDF pages.
- SHA-256: `c2221718e0f404ae78f0aacfcee9bf8aed9b0a8b3dc41547f37064a1ba22d4b2`.
- Dataset: not included. No project or financial records added by this event.

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report March 2026**

- Reporting period: 2026-03-01 to 2026-03-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20March%202026.pdf>) · 40 PDF pages.
- SHA-256: `fcf814857da9d4e7dd0ce1c69cb44da5c1c5c5729fbdf50bc0cc33100211f68b`.
- Dataset: not included. No project or financial records added by this event.

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report July 2026**

- Reporting period: 2026-07-01 to 2026-07-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20July%202026%20(signed).pdf>) · 43 PDF pages.
- SHA-256: `cd016776309074279ca1383b59270c771ea01557e20e09a08510465b9f8506d4`.
- Dataset: not included. No project or financial records added by this event.

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report January 2026**

- Reporting period: 2026-01-01 to 2026-01-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20January%202026.pdf>) · 37 PDF pages.
- SHA-256: `15284d9367414226e16ded7e87936a08c35c168643d966f283b0a40098da56a9`.
- Dataset: not included. No project or financial records added by this event.

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report February 2026**

- Reporting period: 2026-02-01 to 2026-02-28.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20February%202026.pdf>) · 37 PDF pages.
- SHA-256: `bc641aafc83b1c0593435350778aa2c8a190e8ed0e0a4a3d58709dc9ce79265c`.
- Dataset: not included. No project or financial records added by this event.

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report December 2025**

- Reporting period: 2025-12-01 to 2025-12-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2025/Dec%202025/Aviation%20Capital%20Program%20Report%20-%20December%202025.pdf>) · 33 PDF pages.
- SHA-256: `0383ec0829c386c26a961035acd65e3b04d355b00c65afed366e67cd7945be08`.
- Dataset: not included. No project or financial records added by this event.

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report November 2025**

- Reporting period: 2025-11-01 to 2025-11-30.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2025/Nov%202025/Aviation%20Capital%20Program%20Report%20-%20November%202025.pdf>) · 39 PDF pages.
- SHA-256: `72d79e3e0670ba66ab68a4cadace857f75c3a3920c10610ec2b949f75adb9219`.
- Dataset: not included. No project or financial records added by this event.

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report May 2026**

- Reporting period: 2026-05-01 to 2026-05-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20May%202026.pdf>) · 45 PDF pages.
- SHA-256: `247f1f22a8afb6681bd0720b98cbb59c8432b9299af2a546acdd6f6addc3446a`.
- Dataset: not included. No project or financial records added by this event.

### 2026-11-22T01:57:34+00:00 — Discovered

**FIRST QUARTERLY REPORT: INVESTIGATIONS OF INTERNAL INFRASTRUCTURE AT MIAMI INTERNATIONAL AIRPORT, BCC DIRECTIVE NO. 241354** · Matter 250801

- Reporting period: Unknown.
- [Official PDF](<https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2025/250801.pdf>) · 13 PDF pages.
- SHA-256: `28e8fb4f88c9e6e71ab77a74640a5905945c73c71c9b5b9f6a6ab3e6dfb50aba`.
- Dataset: not included. No project or financial records added by this event.

### 2026-11-22T01:57:34+00:00 — Discovered

**SECOND QUARTERLY REPORT: INVESTIGATIONS OF INTERNAL INFRASTRUCTURE AT MIAMI INTERNATIONAL AIRPORT - DIRECTIVE NO. 241354** · Matter 251828

- Reporting period: Unknown.
- [Official PDF](<https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2025/251828.pdf>) · 11 PDF pages.
- SHA-256: `45df96abe887208befb474f5566d014d0bed7230dce22b4f47a5e5ada1e0d33c`.
- Dataset: not included. No project or financial records added by this event.

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report October 2026**

- Reporting period: 2026-10-01 to 2026-10-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20October%202026%20(signed).pdf>) · 46 PDF pages.
- SHA-256: `a6b17346aa1bcad75d375193dad1490d4e351c60e9ddc909527f2875a1c7abec`.
- Dataset: not included. No project or financial records added by this event.

### 2026-11-22T01:57:34+00:00 — Discovered

**FIFTH QUARTERLY REPORT: INVESTIGATIONS OF INTERNAL INFRASTRUCTURE AT MIAMI INTERNATIONAL AIRPORT: DIRECTIVE NO. 241354** · Matter 261824

- Reporting period: 2026-04-01 to 2026-06-30.
- [Official PDF](<https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261824.pdf>) · 16 PDF pages.
- SHA-256: `63ebc1cea03e8bdc7a557c3af66d3df050fd01ea3cb38bc4e0f74a2e7e6cfbd6`.
- Dataset: not included. No project or financial records added by this event.

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report September 2026**

- Reporting period: 2026-09-01 to 2026-09-30.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20September%202026%20(signed).pdf>) · 40 PDF pages.
- SHA-256: `117d7cbf8f4fc9f714c750ae4013c003108f89f2a3e6c4e3f43a48725676fd6b`.
- Dataset: not included. No project or financial records added by this event.

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report August 2026**

- Reporting period: 2026-08-01 to 2026-08-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20August%202026%20(signed).pdf>) · 49 PDF pages.
- SHA-256: `5aced677855357b0b4b53d49bb2e0c594e94a82345e67649910427c815ce0f08`.
- Dataset: not included. No project or financial records added by this event.

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report April 2026**

- Reporting period: 2026-04-01 to 2026-04-30.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20April%202026.pdf>) · 45 PDF pages.
- SHA-256: `e6ad998608ca58925e9e7d9165db6ea47e70ffc10a6f27becfbc1413bf551384`.
- Dataset: not included. No project or financial records added by this event.

<!-- END DISCOVERY EVENTS -->
