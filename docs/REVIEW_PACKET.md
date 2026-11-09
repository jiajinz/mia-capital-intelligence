# Independent review packet — Stage 2

## Result and authorized scope

The owner authorized an integrated Airport Infrastructure & Capital Projects Explorer: improved source-specific profiles, one Largest Reported Project Cost Estimates Plotly chart, and a bounded feasibility study of consecutive official monthly financial reports. These are delivered locally. The project is independent and attributes underlying information to Miami-Dade County. No official branding is used.

The current experience includes discovery, source dates, financial meaning, direct evidence and clear unavailable progress fields. It retains 222 source observations and 107 unresolved candidate links. The project profiles preserve report-level evidence and unresolved identity. The gated contract chart has its own record grain. The primary marketing description is accompanied by a current-availability line. PRODUCT_VISION.md defines the product positioning.

Stage 2A and 2B conclusions and Package A closeout evidence are recorded below. The owner subsequently authorized the Stage 2C slice, which passed named review and ordinary-mode browser verification in the local installation.

## Release readiness verification

The release candidate started from a source-only export in a fresh Python 3.13 environment. The browser showed 222 project source records and the expected pending financial review notice in the unprovisioned export. Dependency checks passed. The clean suite passed 143 tests with 17 PDF integration skips. The suite with pinned originals and the local attestation passed all 160 tests. The published registry failure test verifies that a filesystem error produces only the availability notice.

The release review scanned the 17 project Markdown files, tracked source and configuration, and the visible text and metadata of ten documentation screenshots for local identity references. The export uses the committed tree. Host provisioning and ordinary-mode verification with the attestation are the next release steps. Follow the [source-only verification procedure](RUN_PUBLIC_DIRECTORY.md#verify-a-source-only-release-candidate).

Community Cloud preparation adds a server-side review setting. All 164 local tests passed with the pinned PDFs. App tests cover a valid secret with no local attestation and invalid or stale secrets with an otherwise valid local record. The ordinary view retains its existing gate and never displays the attestation.

The public deployment started under Python 3.13. An unauthenticated request reached the app with HTTP 200, and the sharing dialog confirmed public visibility. Browser checks verified 222 source records, two results for CA176A, the page 12 official PDF link for matter 261402, and the single-report estimate chart. Contract spending showed the expected pending-review message. Hosted verification of financial values follows Secrets provisioning.

## Stage 2C implementation and independent handoff

Stage 2C and its three production slices received approval on November 8, 2026. The authorized inputs are July 261147 p. 28 and summaries pp. 19–20, August 261399 p. 29 and summaries pp. 20–21, and September 261400 p. 30 and summaries pp. 21–22. FINANCIAL_FEASIBILITY.md records the source versions, full hashes and reported-month meaning.

The twelve Package A source rows were carried into `data/financial/snapshots.v1.json` with versioned definitions. Its SHA-256 is `3c90df7ea841061823781be3aa6a388f18c82d51fcf317c3d7f7b261a11622be`. The build reuses PDFium page, ordered cell, summary and version checks, then compares and writes canonical bytes atomically. A test swaps both A19 contracts' financial and summary values across all issues and verifies that the rejected rebuild preserves the previous artifact. Exact Decimal normalization occurs before chart geometry is converted to float. Versioned source row keys remain distinct from the four contract identifiers.

The runtime checks the artifact digest and arithmetic. The trusted local operator provisions `data/financial/review.json` only after a named independent human completes the review. The gate checks decision, definition version, exact digest, all twelve source keys, evidence reference and an elapsed, offset-aware completion time. It validates the attestation supplied by the operator. Human identity is established through the independent review process. A missing, invalid, stale or incomplete attestation blocks ordinary display. Synthetic attestations live only in test temporary directories. Local review is enabled by a process flag plus an explicit loopback bind, with a visible pending banner. Request parameters cannot enable it.

In actual browser QA at 1280 × 720, both local servers returned HTTP 200 and a healthy response. The ordinary app showed a pending review notice and no financial selector or chart despite `?local_review=1`. Local review showed the four choices and exact A19-MDAD-02 September values of $98,135.01 monthly and $13,671,042.69 cumulative. Selecting E20 showed $0.00 monthly and $5,543,728.88 cumulative for September, with corroborated-zero text. The evidence link opened the county summary at PDF p. 22, row 1. See [the local preview screenshot](screenshots/stage2c-local-review.jpg).

Observed **160 tests passed** with the three pinned study PDFs on Python 3.13.1. The financial and quarterly artifacts rebuilt byte-for-byte, and dependency consistency and compilation passed. The source checks reconciled 12 rows, 15 totals, eight roll-forwards and four corroborated zeros. AppTest covers ordinary approved rendering with a temporary synthetic attestation, as well as the pending gate and loopback review.

After the named human confirmation, the operator provisioned the ignored local attestation. The check command returned `approved` for the pinned input, definition version and all 12 rows. With the local review flag unset, the ordinary browser displayed the four-contract scope and the September A19-MDAD-02 row with $98,135.01 monthly and $13,671,042.69 cumulative, linked to the official financial page and summary.

```sh
MIA_STUDY_PDF_DIR=/tmp/mia-financial-study .venv/bin/python -m pytest -q
.venv/bin/python -m pip check
.venv/bin/python scripts/check_financial_feasibility.py --pdf-dir /tmp/mia-financial-study
PYTHONPATH=src .venv/bin/python -m mia_capital_intelligence.contract_spending check
MIA_FINANCIAL_LOCAL_REVIEW=1 .venv/bin/python -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8502
```

The build/cmp commands and exact reviewer-record fields are in [the operating guide](RUN_PUBLIC_DIRECTORY.md#stage-2c-contract-spending-history). Review all five definitions, the twelve financial and summary records, the three E20 aliases and the four explicit zeros. A19-MDAD-01 airport attribution, accounting basis and cutoff remain unknown. The source approval covers only the three pinned financial slices. Hosting remains a separate decision.

## Package A closeout against d6d4f1e

The directory search and chart previously selected separate records while the directory wrote its reference to the address bar. The browse route now has a neutral URL. Every source profile derives **Open profile permalink** and **Open official PDF** from its own selected record. Existing valid `?record=` links open a dedicated profile in a fresh session. Invalid, empty or repeated parameters show a recovery link. The profile precedes the chart value table so its two evidence links are near the selector. The chart uses USD millions for geometry and exact USD for hover, table and profile. Current availability precedes the roadmap wording.

The browser acceptance flow ran at 618 × 731. CA176A search showed the later $3,191,832 record and its own permalink. A native click on V008B opened a separate profile for $896,021,864 with matter 261402, PDF p. 13 / MDC013 / row 6. Its permalink opened the exact record in a fresh tab without filters. The official link opened page 13 of 13. The chart selector's ArrowDown, End and Enter keys selected V042A after V008B. TMB returned three of 112, then three of 110 after switching reports. An unmatched chart search showed the empty state and zero matches. The reviewer separately verified the stale-link recovery. See [closeout profile screenshot](screenshots/stage2-closeout-v008b.jpg) and [permalink and run instructions](RUN_PUBLIC_DIRECTORY.md#share-a-versioned-source-profile).

The August heading was corrected to “Cumulative Expenditures to Date”. A19-MDAD-01 retains both source descriptions and an unresolved airport attribution. The baseline checker accepted wrong financial and summary pages and an unrelated dash note even with verified PDF hashes. It also accepted a full-series swap of the two A19 contracts' financial and summary values. The revised research checker verifies pinned PDF bindings with `--pdf-dir` and rejects all these cases. It also rejects wrong financial headings, wrong summary rows and borrowed zero evidence. Without PDFs, the checker validates static pins and arithmetic. The balanced reassociation test deliberately shows why that mode cannot verify amounts against an original row. Named independent human confirmation of the transcriptions and financial definitions remains pending.

Verified on Python 3.13.1 with these commands:

```sh
MIA_STUDY_PDF_DIR=/tmp/mia-financial-study .venv/bin/python -m pytest -q
.venv/bin/python -m pip check
.venv/bin/python scripts/check_financial_feasibility.py --pdf-dir /tmp/mia-financial-study
PYTHONPATH=src .venv/bin/python - <<'PYCODE'
from pathlib import Path
from tempfile import TemporaryDirectory
from mia_capital_intelligence.public_registry import build_registry

with TemporaryDirectory() as directory:
    rebuilt = Path(directory) / "registry.json"
    build_registry(output=rebuilt)
    assert rebuilt.read_bytes() == Path("data/public/registry.json").read_bytes()
PYCODE
```

Observed 145 passing tests, no broken requirements, three successfully bound and reconciled study issues, and a byte-identical registry rebuild. Browser health returned `ok` and the app returned HTTP 200. The study PDF directory can be replaced with any local directory containing the three pinned matter-ID files. Without the environment variable, pytest skips the eight real-PDF study tests.

The subsequent owner approval covers the three pinned financial pages and their supporting summary pages, four contract selections, one monthly expenditure bar chart and an exact monthly/cumulative table. Named review and acceptance of definitions remain display gates. See [the exact approval scope](FINANCIAL_FEASIBILITY.md#stage-2c-approval-and-release-gate).

## Acceptance and implementation

- **Profiles:** streamlit_app.render_detail is shared by directory and chart. It explains the source-record grain and estimate meaning; shows project description, documented airport, program, source coverage, memo/acceptance dates, PDF/printed page and row; retains raw description/header/value and versioned reference; exposes missing progress/milestones and separately navigable same-ID observations. Candidate identity remains unresolved.
- **Single-report chart:** estimate_insights.largest_estimates requires an indexed matter and ranks existing parameterized DuckDB search results using exact Decimal amounts. Airport/keyword filters apply before the top-N limit. Snapshot, filtered and missing-value denominators are explicit. The default report is 261402 (112 indexed rows); 260526 is selectable (110). No combined population or sum is created.
- **Plotly adapter:** estimate_figure converts only graphical coordinates to float. Exact currency strings, descriptions, immutable references and PDF pages remain in customdata. Bars open the same evidence profile; a keyboard-accessible selector and exact-value source-link table provide alternatives. Chart keys depend on filters, and selected_source_ref accepts only a single reference inside the active ranking. A retained event cannot override a subsequent manual selector choice.
- **Read-only architecture:** existing registry validation, all ordered page controls, candidate SQL and the comparison gate are unchanged. The app still uses tracked validated inputs, ephemeral SQL and no raw PDFs or persistent database writes. Plotly 6.3.1 is pinned in requirements.txt and pyproject.toml. No architecture service or financial definition is replaced.
- **Research:** FINANCIAL_FEASIBILITY.md evaluates the requested five chart types and eight financial questions. The source records were transferred to data/financial/snapshots.v1.json for the gated Stage 2C view. scripts/check_financial_feasibility.py uses Decimal for row arithmetic, all five column totals, summary agreement and contract roll-forwards. Additional source PDFs remain outside commits and outside the production catalog.

## Production source coverage and integrity

The public registry still indexes only Exhibit B from [260526](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/260526.pdf) (PDF pp. 11–12, 110 rows) and [261402](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261402.pdf) (pp. 12–13, 112 rows). Their memo coverage periods are October–December 2025 and January–March 2026. Project-table freeze dates and first public posting dates remain unknown. [261400](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261400.pdf) remains cataloged only, with zero indexed public rows.

All four page ID/amount controls remain intact: 66 / $2,955,660,025; 44 / $3,446,491,140; 68 / $3,356,850,420; 44 / $3,406,481,145. These extraction controls are not an airport-budget measure. The registry hash remains `56882b86f80101623eca8f33bf0cd8918c67cde588a3f55487d9f0cf7a72c5ab`. No registry, inventory, row control or comparison disposition is changed.

Airport classification remains explicit unambiguous source tokens only: MIA 187, OPF 12, TMB 6, X51 2, unknown 15 across both reports. Detailed categories/facilities, status and milestones remain unindexed. Chart rows are document observations with reported project IDs, not verified unique entities across reports.

## Financial findings and limitations

Three consecutive official report labels, July–September 2026, contain the same four financial contract rows. All 12 prior-plus-monthly checks, 15 printed column totals and eight contract roll-forwards reconcile. Monthly totals are $537,673.09, $206,061.07 and $194,680.63; cumulative totals are $41,520,433.89, $41,726,494.96 and $41,921,175.59. These are limited contract totals, not all-airport spending.

The research preserves original financial headers and visually transcribed cells, explicit E20-MDAD--03 / E20-MDAD-03 alias evidence, dashed cells resolved only by the same issue's explicit summary zero, financial and summary page locators, document hashes and unknown ledger cutoffs. All three financial pages were rendered and inspected; summaries were cross-checked. Closeout PDF source-binding verification against all three local PDFs passes. Independent human transcription review is still pending. Arithmetic is not evidence of accounting completeness or an audited cash-payment basis.

V009A procurement reinspection distinguishes its TMB-specific Project Name / Description from the broader OMB project description covering multiple airports (September PDF pp. 24 and 28). That difference in field grain does not prove a conflict or quarterly project association. No financial contract was merged with a quarterly project. Report-month labels, memo dates and legislative dates remain distinct.

FINANCIAL_FEASIBILITY.md records source URLs, byte counts, hashes, pages, reproduction commands and the roadmap. Monthly bars and cumulative lines are conditionally feasible at contract grain; same-row approved-budget utilization is also possible with explicit definitions. Utilization cannot be construction completion. Milestone timelines and detailed facility/category insights need controlled fields and reliable semantics first.

## Validation and actual UI inspection

The original Stage 2 baseline passed **136 tests**, Python 3.13.1. The original 115 remain, with only UI assertions adapted to the authorized positioning and new tab layout. Added 10 estimate-query/selection cases, nine financial-research cases and two UI chart cases. Regressions cover report isolation, filtered denominators, unknown/zero amounts, invalid populations/limits, exact hover values, stale/multiple selections, accessible selection, chart empty state and persistent-event/manual-selection behavior. Research mutations test missing/duplicate contracts, wrong amounts/totals, missing zero evidence, summary disagreement, non-reconciling roll-forward and reordered months.

Streamlit AppTest simulates runtime and chart event return values. Actual browser QA separately verifies a native Plotly bar click. The local app returned HTTP 200 and a healthy Streamlit response. In the normal 618 × 731 browser viewport, selecting V008B changed the profile to $896,021,864, matter 261402, PDF p. 13 / MDC013 / row 6. Clicking its official link opened page 13 of 13 in the county PDF viewer. Airport filtering to TMB showed three matching records in the 112-row report; switching to the earlier report retained one report and a 110-row denominator. Five/ten-bar display limits were inspected. The chart fits the normal narrow viewport; longer source tables scroll horizontally. Other browser/device sizes and hosting remain unverified.

Screenshots:

- [Single-report estimate chart and denominators](screenshots/stage2-estimate-insights.jpg)
- [V008B profile after native bar selection](screenshots/stage2-project-profile.jpg)
- [Official PDF opening at page 13](screenshots/stage2-official-source.jpg)
- [Updated product positioning](screenshots/stage2-explorer.jpg)

Dependency consistency, Python compilation, registry check, source byte identity check and git diff --check pass. RUN_PUBLIC_DIRECTORY.md supplies startup, browser acceptance and PyCharm breakpoint steps. Preview teardown is part of this local-only workflow.

## Reviewer focus and self-review

1. **Product:** Does one-report ranking help discover projects and lead naturally to understandable evidence? The narrow browser stacks controls and profiles vertically; confirm this tradeoff with users. Status and future spending capabilities must not be inferred from marketing copy.
2. **Data correctness:** Verify the snapshot population and source-row grain, Decimal ranking, chart event identity and unchanged registry. Independently transcribe the 12 financial rows and review the explicit alias/zero evidence before any public financial ingestion. Do not confuse broad OMB descriptions with specific contract or quarterly project membership.
3. **Engineering:** Reproduce all checks with the local environment. The small adapter reuses the existing query boundary. Financial study inputs and validation are deliberately isolated; they are not yet a strict production schema. Additional months, restatements or mixed accounting definitions need their own controls.

The Stage 2 handoff recorded unknown ledger and project freeze dates, unresolved cross-report identity, unindexed physical progress and detailed classification, and pending hosting verification.

## Git handoff

Branch main, Stage 1 baseline `57e12f8ec78f5d725ed1c670d6eac4f5f88ff520`. The Stage 2 history begins with `feat(explorer): integrate source profiles and estimate discovery` and `feat(research): reconcile monthly financial feasibility and review handoff`. Use the local commits after the baseline to trace the implementation.
