# Independent review packet — Stage 2A/2B

## Result and authorized scope

The owner authorized an integrated Airport Infrastructure & Capital Projects Explorer: improved source-specific profiles, one Largest Reported Project Cost Estimates Plotly chart, and a bounded feasibility study of consecutive official monthly financial reports. These are delivered locally. The project is independent and attributes underlying information to Miami-Dade County. No official branding is used.

The current experience includes discovery, source dates, financial meaning, direct evidence and clear unavailable progress fields. It retains 222 source observations and 107 unresolved candidate links. It publishes no verified cross-report entity, historical estimate difference, financial chart, cost overrun, delay or physical-progress conclusion. The primary marketing description is accompanied by a current-availability line. PRODUCT_VISION.md is authoritative; the owner's pending README edit remains untouched.

Stage 2 stops for independent review. Proposed Stage 2C is a small contract spending-history section, subject to source approval and reviewed financial controls. No standalone Financial Explorer, hosting or production ingestion expansion has been performed.

## Acceptance and implementation

- **Profiles:** streamlit_app.render_detail is shared by directory and chart. It explains the source-record grain and estimate meaning; shows project description, documented airport, program, source coverage, memo/acceptance dates, PDF/printed page and row; retains raw description/header/value and versioned reference; exposes missing progress/milestones and separately navigable same-ID observations. Candidate identity remains unresolved.
- **Single-report chart:** estimate_insights.largest_estimates requires an indexed matter and ranks existing parameterized DuckDB search results using exact Decimal amounts. Airport/keyword filters apply before the top-N limit. Snapshot, filtered and missing-value denominators are explicit. The default report is 261402 (112 indexed rows); 260526 is selectable (110). No combined population or sum is created.
- **Plotly adapter:** estimate_figure converts only graphical coordinates to float. Exact currency strings, descriptions, immutable references and PDF pages remain in customdata. Bars open the same evidence profile; a keyboard-accessible selector and exact-value source-link table provide alternatives. Chart keys depend on filters, and selected_source_ref accepts only a single reference inside the active ranking. A retained event cannot override a subsequent manual selector choice.
- **Read-only architecture:** existing registry validation, all ordered page controls, candidate SQL and the comparison gate are unchanged. The app still uses tracked validated inputs, ephemeral SQL and no raw PDFs or persistent database writes. Plotly 6.3.1 is pinned in requirements.txt and pyproject.toml. No architecture service or financial definition is replaced.
- **Research:** FINANCIAL_FEASIBILITY.md evaluates the requested five chart types and eight financial questions. docs/research/financial_snapshots.json is explicitly study evidence, not a public dataset. scripts/check_financial_feasibility.py uses Decimal for row arithmetic, all five column totals, summary agreement and contract roll-forwards. Additional source PDFs remain outside commits and outside the production catalog.

## Production source coverage and integrity

The public registry still indexes only Exhibit B from [260526](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/260526.pdf) (PDF pp. 11–12, 110 rows) and [261402](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261402.pdf) (pp. 12–13, 112 rows). Their memo coverage periods are October–December 2025 and January–March 2026. Project-table freeze dates and first public posting dates remain unknown. [261400](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261400.pdf) remains cataloged only, with zero indexed public rows.

All four page ID/amount controls remain intact: 66 / $2,955,660,025; 44 / $3,446,491,140; 68 / $3,356,850,420; 44 / $3,406,481,145. These extraction controls are not an airport-budget measure. The registry hash remains `56882b86f80101623eca8f33bf0cd8918c67cde588a3f55487d9f0cf7a72c5ab`. No registry, inventory, row control or comparison disposition is changed.

Airport classification remains explicit unambiguous source tokens only: MIA 187, OPF 12, TMB 6, X51 2, unknown 15 across both reports. Detailed categories/facilities, status and milestones remain unindexed. Chart rows are document observations with reported project IDs, not verified unique entities across reports.

## Financial findings and limitations

Three consecutive official report labels, July–September 2026, contain the same four financial contract rows. All 12 prior-plus-monthly checks, 15 printed column totals and eight contract roll-forwards reconcile. Monthly totals are $537,673.09, $206,061.07 and $194,680.63; cumulative totals are $41,520,433.89, $41,726,494.96 and $41,921,175.59. These are limited contract totals, not all-airport spending.

The research preserves original financial headers and visually transcribed cells, explicit E20-MDAD--03 / E20-MDAD-03 alias evidence, dashed cells resolved only by the same issue's explicit summary zero, financial and summary page locators, document hashes and unknown ledger cutoffs. All three financial pages were rendered and inspected; summaries were cross-checked. Optional byte verification against all three local PDFs passes. Independent human transcription review is still pending. Arithmetic is not evidence of accounting completeness or an audited cash-payment basis.

V009A procurement reinspection distinguishes its TMB-specific Project Name / Description from the broader OMB project description covering multiple airports (September PDF pp. 24 and 28). That difference in field grain does not prove a conflict or quarterly project association. No financial contract was merged with a quarterly project. Report-month labels, memo dates and legislative dates remain distinct.

FINANCIAL_FEASIBILITY.md records source URLs, byte counts, hashes, pages, reproduction commands and the roadmap. Monthly bars and cumulative lines are conditionally feasible at contract grain; same-row approved-budget utilization is also possible with explicit definitions. Utilization cannot be construction completion. Milestone timelines and detailed facility/category insights need controlled fields and reliable semantics first.

## Validation and actual UI inspection

Full regression: **136 passed**, Python 3.13.1. The original 115 remain, with only UI assertions adapted to the authorized positioning and new tab layout. Added 10 estimate-query/selection cases, nine financial-research cases and two UI chart cases. Regressions cover report isolation, filtered denominators, unknown/zero amounts, invalid populations/limits, exact hover values, stale/multiple selections, accessible selection, chart empty state and persistent-event/manual-selection behavior. Research mutations test missing/duplicate contracts, wrong amounts/totals, missing zero evidence, summary disagreement, non-reconciling roll-forward and reordered months.

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

Outstanding: independent human financial review; unknown ledger/project freeze dates; unresolved cross-report identity; unindexed physical progress and detailed classification; legacy README wording; device/hosting QA. The owner README SHA-256 remains `dd3de625834f0d17e7602a685bffe679cf2343abef1253c6418019a2d9616c8b`, excluded from commits.

## Git handoff

Branch main, Stage 1 baseline `57e12f8ec78f5d725ed1c670d6eac4f5f88ff520`. Stage 2 uses local Conventional Commits with subjects `feat(explorer): integrate source profiles and estimate discovery` and `feat(research): reconcile monthly financial feasibility and review handoff`. Resolve final hashes with `git log -2 --format='%H %s'`; this avoids embedding a commit's own hash in its contents. Inspect each commit and the preserved README working-tree change separately. No push, deployment, tag, merge or history rewrite was performed.
