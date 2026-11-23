# Data updates

This log records the official PDFs included in MIA Capital Intelligence and the data taken from them. Dates identify dataset updates; reporting periods describe the source material. Page numbers refer to PDF pages.

## 2026-11-17 — Current source inventory

This entry documents the existing dataset as of November 17, 2026. It does not represent five PDFs newly added on this date. Their original ingestion dates are not recorded here.

The dataset uses **six distinct PDFs**: three quarterly infrastructure reports and three monthly Aviation Capital Program reports. They provide **332 quarterly report entries**, **12 contract-month records covering four contracts**, and **five airport operations updates**. Operations updates reuse one of the quarterly PDFs.

### Quarterly project records

- **Third Quarterly Report — October–December 2025.** [Official PDF, matter 260526](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/260526.pdf#page=11). Exhibit B, pages 11–12: **110 report entries**, including project IDs, descriptions and reported total cost estimates.
  - File version (SHA-256): `eaf845f4fb746a69940f38fe4655d27b56ab42effdbf9cfdd1dbc746a0fba878`.
- **Fourth Quarterly Report — January–March 2026.** [Official PDF, matter 261402](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261402.pdf#page=12). Exhibit B, pages 12–13: **112 report entries**, including project IDs, descriptions and reported total cost estimates.
  - File version (SHA-256): `84751b451da8b7d5e06cad6b1c24c870e563de5669c5f07325033c446bbaeb2a`.
- **Fifth Quarterly Report — April–June 2026.** [Official PDF, matter 261824](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261824.pdf#page=15). Memo dated November 17, 2026 (Agenda Item 2(B)(6)), accepted by the Board of County Commissioners on November 17, 2026. Exhibit B, pages 15–16: **110 report entries**, including project IDs, descriptions and reported total cost estimates.
  - File version (SHA-256): `63ebc1cea03e8bdc7a557c3af66d3df050fd01ea3cb38bc4e0f74a2e7e6cfbd6`.
  - Verification: an independent reviewer accepted the source with conditions. Every Exhibit B row was extracted twice, by a table-grid extractor and by a character-position extractor, and the two agreed on all 110 IDs and amounts. Pages 1, 2, 12, 13, 15 and 16 were checked by eye; pages 3 to 11 and 14 were rendered only.

Each entry is one row in one report. The same project ID can appear in more than one period; 332 entries is not a count of unique projects.

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

### 2026-11-22T02:20:20+00:00 — Discovered

**Oct**

- Reporting period: 2025-10-01 to 2025-10-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Airport%20Stats/October%202025%20Monthly%20%20Calendar%20Yr%20Traffic%20Report.pdf>) · 1 PDF pages.
- SHA-256: `7e3368b0d52a6db994cfa88682193043d7d30dc7718b32d6efc16f5e8db877ee`.
- Dataset: admitted in the monthly traffic series (`data/traffic/`), not in the project registry. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/14).

### 2026-11-22T02:20:20+00:00 — Discovered

**Jul**

- Reporting period: 2025-07-01 to 2025-07-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Airport%20Stats/July%202025%20Monthly%20%20Calendar%20Yr%20Traffic%20Report.pdf>) · 1 PDF pages.
- SHA-256: `fcda35d15229611fc7a0f79222e13d828c227c2862559b95e34542eb2a027239`.
- Dataset: admitted in the monthly traffic series (`data/traffic/`), not in the project registry. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/14).

### 2026-11-22T02:20:20+00:00 — Discovered

**Feb**

- Reporting period: 2026-02-01 to 2026-02-28.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Airport%20Stats/FY%202025-2026/February%202026%20Monthly%20%20Calendar%20Yr%20Traffic%20Report.pdf>) · 1 PDF pages.
- SHA-256: `bcd78015fd2526edb4328fdf0a3049d292f05df14f67baa8454a900ac70ea6c1`.
- Dataset: admitted in the monthly traffic series (`data/traffic/`), not in the project registry. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/14).

### 2026-11-22T02:20:20+00:00 — Discovered

**May**

- Reporting period: 2026-05-01 to 2026-05-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Airport%20Stats/FY%202025-2026/May%202026%20Monthly%20%20Calendar%20Yr%20Traffic%20Report.pdf>) · 1 PDF pages.
- SHA-256: `28b27b9678872627d51ae6cae6457ed69eed12180c938f39c4f947e2754192e0`.
- Dataset: admitted in the monthly traffic series (`data/traffic/`), not in the project registry. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/14).

### 2026-11-22T02:20:20+00:00 — Discovered

**Aug**

- Reporting period: 2026-08-01 to 2026-08-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Airport%20Stats/FY%202025-2026/August%202026%20Monthly%20%20Calendar%20Yr%20Traffic%20Report.pdf>) · 1 PDF pages.
- SHA-256: `8c4da02bef5bfe276bb7111cf564deb4a816f292aab0cfdd3a393896c7bba7e8`.
- Dataset: admitted in the monthly traffic series (`data/traffic/`), not in the project registry. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/14).

### 2026-11-22T02:20:20+00:00 — Discovered

**Apr**

- Reporting period: 2026-04-01 to 2026-04-30.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Airport%20Stats/FY%202025-2026/April%202026%20Monthly%20%20Calendar%20Yr%20Traffic%20Report.pdf>) · 1 PDF pages.
- SHA-256: `6643bd26aae19fa141bde4f3cf2d19a0a0f0beacac27d58aaf11a86b3e4acb3a`.
- Dataset: admitted in the monthly traffic series (`data/traffic/`), not in the project registry. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/14).

### 2026-11-22T02:20:20+00:00 — Discovered

**Dec**

- Reporting period: 2025-12-01 to 2025-12-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Traffic%20Reports/2025/December%202025%20Monthly%20%20Calendar%20Yr%20Traffic%20Report.pdf>) · 1 PDF pages.
- SHA-256: `b196b18fd716cf9136c8cc58a757a9d875a4602687dd9a35a3f05593bef5c5e9`.
- Dataset: admitted in the monthly traffic series (`data/traffic/`), not in the project registry. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/14).

### 2026-11-22T02:20:20+00:00 — Discovered

**Mar**

- Reporting period: 2026-03-01 to 2026-03-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Airport%20Stats/FY%202025-2026/March%202026%20Monthly%20%20Calendar%20Yr%20Traffic%20Report.pdf>) · 1 PDF pages.
- SHA-256: `9291c0d6f847da1a778dc59489e04411c289751d45ba742e9e339f99076bae03`.
- Dataset: admitted in the monthly traffic series (`data/traffic/`), not in the project registry. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/14).

### 2026-11-22T02:20:20+00:00 — Discovered

**Sep**

- Reporting period: 2026-09-01 to 2026-09-30.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Airport%20Stats/FY%202025-2026/September%202026%20Monthly%20%20Calendar%20Yr%20Traffic%20Report.pdf>) · 1 PDF pages.
- SHA-256: `c83971ae53024236c4532ac76512e9ca28eef864e86ea4f99215fb6388d825f4`.
- Dataset: admitted in the monthly traffic series (`data/traffic/`), not in the project registry. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/14).

### 2026-11-22T02:20:20+00:00 — Discovered

**Jan**

- Reporting period: 2026-01-01 to 2026-01-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Airport%20Stats/FY%202025-2026/January%202026%20Monthly%20%20Calendar%20Yr%20Traffic%20Report.pdf>) · 1 PDF pages.
- SHA-256: `86bfac65411576b66676f1175277feb43918a84722960e8b63523306ecc477fc`.
- Dataset: admitted in the monthly traffic series (`data/traffic/`), not in the project registry. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/14).

### 2026-11-22T02:20:20+00:00 — Discovered

**Aug**

- Reporting period: 2025-08-01 to 2025-08-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Airport%20Stats/August%202025%20Monthly%20%20Calendar%20Yr%20Traffic%20Report.pdf>) · 1 PDF pages.
- SHA-256: `ca1e9f294c1a34cf47713269bc224d7504aaae75f9a2d8b6cf242204d7c1d75a`.
- Dataset: admitted in the monthly traffic series (`data/traffic/`), not in the project registry. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/14).

### 2026-11-22T02:20:20+00:00 — Discovered

**Jul**

- Reporting period: 2026-07-01 to 2026-07-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Airport%20Stats/FY%202025-2026/July%202026%20Monthly%20%20Calendar%20Yr%20Traffic%20Report.pdf>) · 1 PDF pages.
- SHA-256: `bbeb9c0b864e1aec3f61e6f9a4e46aa624c19898ef261906c9ab4a28dfef8d1d`.
- Dataset: admitted in the monthly traffic series (`data/traffic/`), not in the project registry. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/14).

### 2026-11-22T02:20:20+00:00 — Discovered

**Nov**

- Reporting period: 2025-11-01 to 2025-11-30.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Traffic%20Reports/2025/November%202025%20Monthly%20%20Calendar%20Yr%20Traffic%20Report.pdf>) · 1 PDF pages.
- SHA-256: `a1d8d78fe82d132e84c63ed816040f1f1b7db7ed49fd232a0513e1d969f241f1`.
- Dataset: admitted in the monthly traffic series (`data/traffic/`), not in the project registry. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/14).

### 2026-11-22T02:20:20+00:00 — Discovered

**Sep**

- Reporting period: 2025-09-01 to 2025-09-30.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Airport%20Stats/September%202025%20Monthly%20%20Calendar%20Yr%20Traffic%20Report%20(002).pdf>) · 1 PDF pages.
- SHA-256: `066a8c77226ecefea5d9cc38c6c93a11d59216c124fc1f53f9d8d61bf5743789`.
- Dataset: admitted in the monthly traffic series (`data/traffic/`), not in the project registry. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/14).

### 2026-11-22T02:20:20+00:00 — Discovered

**Jun**

- Reporting period: 2026-06-01 to 2026-06-30.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Airport%20Stats/FY%202025-2026/June%202026%20Monthly%20%20Calendar%20Yr%20Traffic%20Report.pdf>) · 1 PDF pages.
- SHA-256: `da5577ed1f85fa11e75b40d28ec4c07396838fb40532978de61470cca16d81e4`.
- Dataset: admitted in the monthly traffic series (`data/traffic/`), not in the project registry. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/14).

### 2026-11-22T02:05:50+00:00 — Discovered

**Aviation Capital Program Report March 2025**

- Reporting period: 2025-03-01 to 2025-03-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2025/Mar%202025/March%202025%20Aviation%20Capital%20Program%20Report.pdf>) · 33 PDF pages.
- SHA-256: `6e24f37f806d115d5d08d8003d37b5d558c4b9043313dd5a912d998e7dd46206`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T02:05:50+00:00 — Discovered

**Aviation Capital Program Report April 2025**

- Reporting period: 2025-04-01 to 2025-04-30.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2025/Apr%202025/April%202025%20Aviation%20Capital%20Program%20Report.pdf>) · 34 PDF pages.
- SHA-256: `7f6a13200b6440f51f124cefa8dc6e33e4bfc8ba759d3e520193d4ca42c3e25d`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T02:05:50+00:00 — Discovered

**Aviation Capital Program Report June 2025**

- Reporting period: 2025-06-01 to 2025-06-30.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2025/June%202025/Aviation%20Capital%20Program%20Report%20-%20June%202025.pdf>) · 36 PDF pages.
- SHA-256: `272998468d2749732d38d6d9596054d9d37fd192691a8eed170e044c4bea3882`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T02:05:50+00:00 — Discovered

**Aviation Capital Program Report October 2025**

- Reporting period: 2025-10-01 to 2025-10-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2025/Oct%202025/Aviation%20Capital%20Program%20Report%20-%20October%202025.pdf>) · 31 PDF pages.
- SHA-256: `8c2653e7c73e31fc0fd2cfd09e5ab8c423788da5c96ce3bb45a50ec911947a4e`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T02:05:50+00:00 — Discovered

**Aviation Capital Program Report July 2025**

- Reporting period: 2025-07-01 to 2025-07-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2025/July/Aviation%20Capital%20Program%20Report%20-%20July%202025.pdf>) · 31 PDF pages.
- SHA-256: `31623e9a276f26fae54fd2a750ef4a88f6af8d468df2e0923baa9ed360c488d7`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T02:05:50+00:00 — Discovered

**Aviation Capital Program Report February 2025**

- Reporting period: Unknown.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2025/Feb%202025/February%202025%20Aviation%20Capital%20Program%20Report.pdf>) · 32 PDF pages.
- SHA-256: `d78ca250bc23def7fd6aa3c9d9851e412319046bebf379ee581594cc75bab86c`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T02:05:50+00:00 — Discovered

**Aviation Capital Program Report September 2025**

- Reporting period: 2025-09-01 to 2025-09-30.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2025/Sept%202025/Aviation%20Capital%20Program%20Report%20-%20September%202025.pdf>) · 33 PDF pages.
- SHA-256: `05bd511e097c82a71319fad1b971cef44c52dafcf7d633af93f37ec62b40870e`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T02:05:50+00:00 — Discovered

**Aviation Capital Program Report January 2025**

- Reporting period: Unknown.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/Aviation%20Capital%20Program%20Report%20-%20January%202025.pdf>) · 36 PDF pages.
- SHA-256: `54af991da764a83ed3a1185730dbfd8a509dba67c4e5525a3bae9bb69819ed2f`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T02:05:50+00:00 — Discovered

**Aviation Capital Program Report August 2025**

- Reporting period: 2025-08-01 to 2025-08-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2025/August/Aviation%20Capital%20Program%20Report%20-%20August%202025.pdf>) · 42 PDF pages.
- SHA-256: `c5d25b15b9b06644529820cf244cc2ee694a4ba981445f9dd0e31a96376dc07b`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T02:05:50+00:00 — Discovered

**Aviation Capital Program Report May 2025**

- Reporting period: 2025-05-01 to 2025-05-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2025/May%202025/Aviation%20Capital%20Program%20Report%20-%20May%202025.pdf>) · 36 PDF pages.
- SHA-256: `624cbbce7edd2b64bb69dbd6cc0ab103ca6c98919a07fdbe91e8c6119d87a0a3`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report June 2026**

- Reporting period: 2026-06-01 to 2026-06-30.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20June%202026.pdf>) · 52 PDF pages.
- SHA-256: `c2221718e0f404ae78f0aacfcee9bf8aed9b0a8b3dc41547f37064a1ba22d4b2`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report March 2026**

- Reporting period: 2026-03-01 to 2026-03-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20March%202026.pdf>) · 40 PDF pages.
- SHA-256: `fcf814857da9d4e7dd0ce1c69cb44da5c1c5c5729fbdf50bc0cc33100211f68b`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report July 2026**

- Reporting period: 2026-07-01 to 2026-07-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20July%202026%20(signed).pdf>) · 43 PDF pages.
- SHA-256: `cd016776309074279ca1383b59270c771ea01557e20e09a08510465b9f8506d4`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report January 2026**

- Reporting period: 2026-01-01 to 2026-01-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20January%202026.pdf>) · 37 PDF pages.
- SHA-256: `15284d9367414226e16ded7e87936a08c35c168643d966f283b0a40098da56a9`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report February 2026**

- Reporting period: 2026-02-01 to 2026-02-28.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20February%202026.pdf>) · 37 PDF pages.
- SHA-256: `bc641aafc83b1c0593435350778aa2c8a190e8ed0e0a4a3d58709dc9ce79265c`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report December 2025**

- Reporting period: 2025-12-01 to 2025-12-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2025/Dec%202025/Aviation%20Capital%20Program%20Report%20-%20December%202025.pdf>) · 33 PDF pages.
- SHA-256: `0383ec0829c386c26a961035acd65e3b04d355b00c65afed366e67cd7945be08`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report November 2025**

- Reporting period: 2025-11-01 to 2025-11-30.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2025/Nov%202025/Aviation%20Capital%20Program%20Report%20-%20November%202025.pdf>) · 39 PDF pages.
- SHA-256: `72d79e3e0670ba66ab68a4cadace857f75c3a3920c10610ec2b949f75adb9219`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report May 2026**

- Reporting period: 2026-05-01 to 2026-05-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20May%202026.pdf>) · 45 PDF pages.
- SHA-256: `247f1f22a8afb6681bd0720b98cbb59c8432b9299af2a546acdd6f6addc3446a`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T01:57:34+00:00 — Discovered

**FIRST QUARTERLY REPORT: INVESTIGATIONS OF INTERNAL INFRASTRUCTURE AT MIAMI INTERNATIONAL AIRPORT, BCC DIRECTIVE NO. 241354** · Matter 250801

- Reporting period: Unknown.
- [Official PDF](<https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2025/250801.pdf>) · 13 PDF pages.
- SHA-256: `28e8fb4f88c9e6e71ab77a74640a5905945c73c71c9b5b9f6a6ab3e6dfb50aba`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T01:57:34+00:00 — Discovered

**SECOND QUARTERLY REPORT: INVESTIGATIONS OF INTERNAL INFRASTRUCTURE AT MIAMI INTERNATIONAL AIRPORT - DIRECTIVE NO. 241354** · Matter 251828

- Reporting period: Unknown.
- [Official PDF](<https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2025/251828.pdf>) · 11 PDF pages.
- SHA-256: `45df96abe887208befb474f5566d014d0bed7230dce22b4f47a5e5ada1e0d33c`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report October 2026**

- Reporting period: 2026-10-01 to 2026-10-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20October%202026%20(signed).pdf>) · 46 PDF pages.
- SHA-256: `a6b17346aa1bcad75d375193dad1490d4e351c60e9ddc909527f2875a1c7abec`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T01:57:34+00:00 — Discovered

**FIFTH QUARTERLY REPORT: INVESTIGATIONS OF INTERNAL INFRASTRUCTURE AT MIAMI INTERNATIONAL AIRPORT: DIRECTIVE NO. 241354** · Matter 261824

- Reporting period: 2026-04-01 to 2026-06-30.
- [Official PDF](<https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261824.pdf>) · 16 PDF pages.
- SHA-256: `63ebc1cea03e8bdc7a557c3af66d3df050fd01ea3cb38bc4e0f74a2e7e6cfbd6`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report September 2026**

- Reporting period: 2026-09-01 to 2026-09-30.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20September%202026%20(signed).pdf>) · 40 PDF pages.
- SHA-256: `117d7cbf8f4fc9f714c750ae4013c003108f89f2a3e6c4e3f43a48725676fd6b`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report August 2026**

- Reporting period: 2026-08-01 to 2026-08-31.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20August%202026%20(signed).pdf>) · 49 PDF pages.
- SHA-256: `5aced677855357b0b4b53d49bb2e0c594e94a82345e67649910427c815ce0f08`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

### 2026-11-22T01:57:34+00:00 — Discovered

**Aviation Capital Program Report April 2026**

- Reporting period: 2026-04-01 to 2026-04-30.
- [Official PDF](<https://www.miami-airport.com/library/pdfdoc/Transparency_Reports/2026/CIP%20Monthly%20Report%20-%20April%202026.pdf>) · 45 PDF pages.
- SHA-256: `e6ad998608ca58925e9e7d9165db6ea47e70ffc10a6f27becfbc1413bf551384`.
- Dataset: not included. No project or financial records added by this event.
- [Discovery pull request](https://github.com/jiajinz/mia-capital-intelligence/pull/12).

<!-- END DISCOVERY EVENTS -->
