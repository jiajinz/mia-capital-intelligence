# Independent review packet — Public transparency Stage 1

## Product definition and authorized boundary

MIA Capital Intelligence is an independent Public Airport Infrastructure & Capital Projects Transparency Explorer, with no affiliation with MDAD or HNTB. It helps residents, researchers, journalists, contractors and other users find and understand information dispersed across public records. The owner approved this pivot in the existing repository. The product makes no claim about MDAD's internal systems.

Stage 1 delivers a working local Streamlit Project Directory, a source-record detail and an honest source catalog. Individual validated source observations are publishable without cross-report comparison approval. Verified project identities and analytical comparisons retain separate evidence requirements. PRODUCT_VISION.md records the retained integrity infrastructure, deferred optional comparisons and removal of internal management workflows from the current product scope. Historical decisions D001–D006 and the comparison contract remain available.

## Acceptance criteria and result

- A current product vision and roadmap exist, and persistent project guidance reflects the approved pivot.
- The existing 73 Stage 0/1A tests remain valid. All 222 controlled Exhibit B ID/amount associations and page controls remain intact.
- A registry separates source documents, document-scoped observations, empty verified-project/membership relations, candidate identity links and source evidence. No candidate becomes a verified entity automatically.
- A functioning Streamlit app supports literal keyword/ID search, airport/source filters, stable sorting, unknown and empty/error states, source-specific details and official PDF pages.
- The source catalog shows 110, 112 and zero indexed records, publication/acceptance date roles, original URLs, source versions, validation scope and gaps.
- A real CA176A record was traced end-to-end through the local interface to the official PDF page in a browser. Rebuild, test, screenshot and manual acceptance evidence are provided.
- Local commits preserve the unrelated README edit. Stage 1 stops here for independent product and technical review.

## Actual coverage and model

The existing inventory catalogs [260526](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/260526.pdf), [261402](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261402.pdf) and [261400](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261400.pdf). The directory indexes only Exhibit B from the first two, preserving 110 and 112 rows. Their memo periods are October–December 2025 and January–March 2026. The September capital report is cataloged only, with zero indexed project rows. The first public posting dates and project-data freeze dates remain unconfirmed.

There are 222 source observations, 107 unverified same-ID candidate links and zero verified cross-document project identities. The 3 earlier-only and 5 later-only rows remain searchable. Counts describe source records, not a unique airport-project or complete capital-program population. The airport facets contain MIA 187, OPF 12, TMB 6, X51 2 and unknown 15 observations, based only on explicit unambiguous source-description tokens.

The source record key includes matter ID, full document SHA-256, exhibit, PDF position and physical row ordinal. The artifact preserves original descriptions, raw estimate/header, exact parsed Decimal and row bounding boxes. Separate verified_projects and project_memberships arrays remain empty. Candidate links reuse the exact-ID SQL matcher and retain candidate_unverified status. PUBLIC_REGISTRY_MODEL.md documents grains, uniqueness, financial meaning and validation boundaries.

## Implementation and important files

- `src/mia_capital_intelligence/public_registry.py:161` provides build_registry, with validate_registry at line 96 and load_registry at line 196. It reuses the existing pinned PDF loader and row controls, validates inventory/version identities and all ordered ID/amount associations, and atomically replaces one complete JSON artifact after successful validation. Failed extraction preserves the previous file.
- `data/public/registry.json` is the reproducible source-derived input. It has no synthetic production rows. Runtime validation uses only this file, the inventory and row controls; original PDFs and review-disposition files are unnecessary for public operation.
- `src/mia_capital_intelligence/directory_queries.py:59` provides parameterized search, with source_detail at line 104, explicit airport classification and exact currency formatting. `sql/directory.sql` returns one observation per source_ref with a fixed sort whitelist. It creates no historical change metric. DuckDB connections are ephemeral and per query.
- `streamlit_app.py:94` renders Project directory, with render_detail at line 30 and source coverage at line 161. It presents a selectable source-record detail, raw evidence/verification notes and an explicitly unresolved candidate association. Pandas formats result tables, with financial values already rendered as exact currency strings. `.streamlit/config.toml` supplies a restrained local theme.
- `tests/test_public_registry.py` covers public integrity and queries. `tests/test_streamlit_directory.py` exercises public UI paths through Streamlit AppTest. The pre-existing extraction and approval tests are preserved.
- `docs/RUN_PUBLIC_DIRECTORY.md`, `docs/PUBLIC_STAGE_1_AUDIT.md` and `docs/PRODUCT_VISION.md` give operation, audit evidence and current product scope. PROJECT_STATE.md, DECISIONS.md, the dictionary and source/approval contracts retain relevant lineage and boundaries.

## End-to-end example

Use the later CA176A observation from matter 261402, Exhibit B, PDF p. 12, printed MDC012, data row 41. The original description is MIA E Satellite Terminal Seating Ph2 and Total Estimated Cost is 3,191,832 USD. The source reference is 261402:84751b451da8b7d5e06cad6b1c24c870e563de5669c5f07325033c446bbaeb2a:B:12:41.

The source loader verifies the PDF bytes and reads this cell. The frozen independent control confirms its ID/amount pair. The public builder stores the original row with its versioned reference. Searching CA176A in Streamlit returns two separately labeled report observations. Selecting the 261402 record shows its estimate, coverage and original page link. That link was clicked in the actual browser and opened the county report at page 12 of 13. The earlier CA176A record remains a candidate association, with no confirmed project history or cost-growth claim.

## Reconciliation and tests

The full suite passed **115 tests** on Python 3.13.1. It preserves the 73-test baseline and adds 33 registry/query cases plus 9 Streamlit AppTest cases. New regressions cover duplicated/missing rows, amount swaps with unchanged sums, wrong source versions/pages, invented verified identities, missing/invalid estimates, ambiguous airports, original PDF URLs, literal keyword filtering, deterministic sorting/rebuilds, raw-PDF-free runtime and failed-build preservation. UI tests cover real search/detail, filters, unknowns, empty results, catalog-only reports, versioned deep links, stale links and a safe corrupt-input error state.

All four source page controls remain 66 / 2,955,660,025 USD, 44 / 3,446,491,140 USD, 68 / 3,356,850,420 USD and 44 / 3,406,481,145 USD, with zero missing estimates. These are extraction controls, with no aggregate public-budget inference. Two rebuilds reproduce the committed registry bytes, SHA-256 56882b86f80101623eca8f33bf0cd8918c67cde588a3f55487d9f0cf7a72c5ab. Dependency consistency, compilation and whitespace checks also passed. All source byte identities remain pinned and raw PDFs remain untracked.

## Run, preview and browser evidence

```sh
.venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m pytest -q
PYTHONPATH=src .venv/bin/python -m mia_capital_intelligence.public_registry check
.venv/bin/python -m streamlit run streamlit_app.py
```

The local Streamlit health endpoint returned ok and the app returned HTTP 200. Actual browser inspection verified CA176A search/detail, candidate labeling, the official page opening, source coverage, empty results and the Unknown airport filter. AppTest is simulated-runtime verification and supplements those actual browser actions. The normal in-app browser viewport was narrow; the result table supports horizontal scrolling. Other devices/browsers and Community Cloud remain unverified.

- [Search results and detail entry](screenshots/directory.jpg)
- [Selected source evidence and page link](screenshots/project-detail.jpg)
- [Official report opening at PDF page 12](screenshots/official-source-page.jpg)
- [Source catalog with 110 / 112 / 0 indexed records](screenshots/source-coverage.jpg)

RUN_PUBLIC_DIRECTORY.md gives exact manual acceptance and PyCharm run/debug steps. For a fresh rebuild, use the verified-before-replacement acquisition procedure in SOURCE_AUDIT.md, then run the public_registry build command. The read-only app serves the checked-in artifact and relies on no persistent runtime data writes.

## Self-review, limitations and ranked improvements

1. **Public user.** The search-to-original-document flow is demonstrable. Narrow screens require horizontal scrolling, and only source program classification is indexed. Prioritize short usability observations, then evidence-backed facility and category enrichment.
2. **Data engineer.** Every displayed estimate and ID is tied to a controlled source row and source version. Description wording is extracted and retained; independent controls cover ID/amount associations. Candidate identity remains unresolved. New fields and reports require deliberate extraction controls and source review. Regenerate the trusted artifact with the builder and review it in Git.
3. **Hiring manager.** The slice integrates real public PDF evidence, Python validation, exact financial handling, SQL search, reproducible input builds and a public Streamlit workflow. The corpus remains small and manually selected. A scoped discovery/acquisition workflow would provide the next integration demonstration after product review.

Detailed work categories, standalone facility classifications, construction status and milestones remain unindexed, with explicit UI wording. No financial change, engineering-risk rating, project delay, cancellation inference or incompatible aggregate is published. Human verification of cross-document identity and substantive comparison basis remains a separate later capability.

The pre-existing README edit remains byte-for-byte unchanged and excluded, with SHA-256 dd3de625834f0d17e7602a685bffe679cf2343abef1253c6418019a2d9616c8b. README retains historical product wording while PRODUCT_VISION.md provides the authoritative approved direction.

## Git and Stage 2 handoff

Branch main. Data/registry unit c47a793, feat(data): publish controlled public source registry. Resolve its full hash with git log -1 --format='%H %s' -- data/public/registry.json. The UI unit uses subject feat(app): add public project directory and source profiles, resolved with git log -1 --format='%H %s' -- streamlit_app.py. The preceding baseline is 1b36c5c30330f03591526a541ad770aa329bce6f. Review the two local commits and this packet; no hosting action is part of this milestone.

Recommend a conditional go for Stage 2 scope review after independent product and technical acceptance. The highest-value next work is targeted usability and source-backed classification enrichment, followed by a small evaluated source-discovery expansion. Keep public observations accessible while retaining the identity and comparison evidence boundaries. Stop after this Stage 1 handoff.
