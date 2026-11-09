# Decisions

## D001 — Begin with one exhibit from Directive 241354

**Stage 0 decision, subject to Stage 1 review.** Use Exhibit B of 260526 and 261402 for a narrow Capital Improvement Program slice. The official documents share the directive, exhibit name, project token and estimate column. The memo periods are adjacent and 107 project tokens overlap within B. Some pairs change scope, so exact matching is a candidate step and a material change requires row and scope verification.

Keep Exhibit A and September's Aviation Capital Program issue in the audited catalog. A overlaps B and includes pipeline and placeholder rows. September's financial figures use contract grain and one report month. Adding new source issues or publishing a cross-series mapping requires owner review.

## D002 — Report periods, financial measures and evidence

**Accepted Stage 0 guardrails.** Index by explicit memo coverage for the quarterly pair while retaining printed exhibit fiscal-year labels. Store memo, introduction, acceptance and reporting dates separately. Treat individual exhibit data freeze dates as unknown. Keep total estimates, adopted/approved budgets, award values, period/cumulative expenditures and structural/electrical ROM measures separate.

Preserve raw source rows and attach review status at field and match level. A repeated identifier in different exhibits can refer to the same scope. An ID that disappears can reflect scope or reporting changes. Stage 1 may show verified estimate differences, source presence differences and withheld comparisons with specific follow-up questions. Progress deltas, inferred delay, awarded-vs-estimated comparisons and funding-gap amounts remain out of scope. Defer public milestone rules until the date status and like-for-like scope are confirmed.

## D003 — Use DuckDB for the relational slice when its inputs pass review

**Architecture decision before adoption.** For Stage 1, choose a single local DuckDB connection over validated Parquet when the work needs repeatable snapshot joins, SQL review and a read-only query layer. DuckDB can query Parquet directly and store fixed-point `DECIMAL` amounts. This keeps rebuildable data files separate from views. Use exact arithmetic for subtraction and an explicitly rounded relative change. DuckDB division of decimals produces floating-point results, so compute displayed financial percentages using Python `Decimal` or document a tested rounding contract. [DuckDB Parquet](https://duckdb.org/docs/stable/data/parquet/overview) · [DuckDB numeric types](https://duckdb.org/docs/stable/sql/data_types/numeric)

SQLite can easily hold this row volume and supports transactional application state. Its type affinity and separate Parquet load would add conversion and schema work for this read-heavy use. A safe SQLite alternative would store integer cents and load validated files explicitly. Pandas alone works for Stage 0 or a two-file profiling script. A Pandas merge with cardinality validation can also support a small pilot. Repeated reconciliation joins, exception queries and a future app query boundary justify SQL for the proposed slice. [SQLite datatypes](https://www.sqlite.org/datatype3.html) · [Pandas merge](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html)

No database or analytical dependencies are needed for the Stage 0 metadata gate. Before implementation, confirm DuckDB and the Parquet writer work in the repository's Python 3.13 environment and verify a repeatable build with explicit validation. If the reviewed use case shrinks to a one-off comparison, revisit the SQL dependency. Use a read-only application connection or in-memory views on immutable inputs and avoid reliance on runtime file writes.

## D004 — Stage 1 acceptance criteria

**Proposed, externally reviewed with conditions, pending owner authorization.** The smallest useful result is a reproducible, local, read-only review query for the two Exhibit B snapshots. It can serve all three future workspaces without a dashboard.

1. Reacquire or read the two pinned originals. Verify both hashes, all four exhibit page counts and sums, and every project row against a second visual or transcribed pass. Persist reviewed snapshot and evidence records as reproducible inputs. Each row needs provenance and an extraction status. Publish a validation log.
2. Check uniqueness on snapshot and exhibit and validate all evidence references. Apply the [scope review contract](SCOPE_REVIEW_CONTRACT.md) to all 107 pairs, including unchanged amounts. Default to held with null deltas. Comparable approval requires a named reviewer, reason, both immutable evidence rows and affirmative confirmation of scope, measure and estimate basis. Retain the 3 earlier-only and 5 later-only rows with presence dispositions and null deltas. Include CA176A/B, T180B/T180D and BA133A in review.
3. Use DuckDB SQL for an ordered exact-ID full outer join and a reviewed estimate-difference result. Show previous and current amounts, signed delta, relative delta when defined, both evidence locators, detection rule, review status and one follow-up question. Presence-only rows carry no financial delta. Use stable sorting and explicit materiality semantics. The first slice may sort all verified differences by absolute magnitude with no threshold until the owner reviews a materiality policy.
4. Provide reproducible tests for project ID stability, duplicate and missing values, referential integrity, exact cents, ordering, cross-period joins and deterministic outputs. Fail before publishing a replacement dataset if any identity or reconciliation check breaks. Use unit fixtures only for tests.
5. Demonstrate T180B as either a scope-approved candidate or an explicitly withheld pair with both source rows. Demonstrate T180D as earlier-only. Keep public dashboards, progress deltas, consolidated estimates, cross-series linking, and monthly financial findings outside the first slice.

This yields one defensible analyst workflow. A scoped overview counts verified B rows, the review query identifies changes worth following up, and a project history query shows the two underlying snapshots and evidence.

## D005 — Address review defects within Stage 0

**Accepted corrective decision, November 8, 2026.** Reproduce the shared-filter omission and establish a frozen, independent row control for the four Exhibit B pages. Compare ordered ID/amount associations before emitting a source's success summaries. Preserve the raw grid's non-heading tokens independently of the anchor regex. The control uses PDFium, a separate PDF engine and ID discovery method from the profiler. Record its provenance and remaining human verification requirements in [AUDIT_CONTROLS.md](AUDIT_CONTROLS.md). This is an audit correction, with no analytical snapshot publication.

Accept P1-02 as a business-definition defect. Establish the explicit disposition and approval contract now. Its executable query gate, complete candidate review records and acceptance tests belong to Stage 1 after owner authorization. Accept P2-01's acquisition concern and validate the downloaded temporary file before replacement in the documented sequential workflow.

## D006 — Implement Stage 1A as a versioned, metric-specific gate

**Authorized Stage 1A, November 8, 2026.** The owner's new instruction narrows the earlier D004 plan to comparability approval. Implement identity matching, evidence and disposition validation, and eligible source-value queries. Stage 1B retains any future estimated-change calculation and publication rules. The existing contract's null-delta policy remains applicable to future change outputs. Stage 1A expresses withholding through an empty approved relation and provides separate source observations.

Preserve the contract outcomes `held`, `comparable` and `excluded`. Excluded represents a human rejection/non-comparability decision. Empty decision input explicitly defaults all 107 pairs to held with unassigned reviewer and timestamp. A comparable disposition is metric-specific. A full pair may have one approved metric and another unreviewed metric. All six evidence dimensions and both versioned source references are required for each approved metric. Human review provides the substantive assertions. The system validates their structure and applicability.

Keep one active review per pair in a version-controlled JSON bundle with JSON Schema 2020-12, contract version 1.0. Require timezone-aware decision/verification timestamps and verified evidence no later than its decision. Parse timestamps explicitly because JSON Schema format checks may otherwise depend on optional packages. Reject duplicate JSON fields, duplicate/conflicting decisions, unknown references and stale versions. Any technical error invalidates the entire bundle for that execution, while retaining input and validation evidence. This conservative policy avoids partially trusted bundles.

Use typed source observations loaded from the pinned PDF rows, with every ordered ID/amount pair reconciled to the existing CSV controls. The second PDFium checker remains independently runnable. Keep the existing source rows as rebuildable inputs and use an in-memory DuckDB connection with parameterized full outer joins and a checked-in metric-eligibility query. This stage needs no persistent database or Parquet publication. DECIMAL(18,2) and Python Decimal preserve financial precision. Eligibility rows are inserted only after complete validation, and the connection is closed after each evaluated report.

Pin DuckDB 1.4.3 and jsonschema 4.25.1 after confirming local Python 3.13 compatibility. Preserve the existing PDF audit pins. The real gate reads only total estimated cost. The dictionary's current approved budget metric is included in the schema and synthetic tests solely to verify field-specific isolation. The September financial report remains outside the gate's data scope.

## D007 — Approved pivot to a public transparency directory

**Owner-approved product pivot.** PRODUCT_VISION.md replaces the internal project-controls direction as the primary mission. Retain D001–D006 and the comparison approval implementation as historical and reusable integrity work. Showing an individual validated source observation needs no comparability decision. Shared project IDs yield explicitly unverified candidate links, while verified project entities require separate identity evidence.

The Stage 1 registry preserves documents, individual source records, an empty verified-project/membership relation, candidate identity links and source evidence. It indexes only the four controlled Exhibit B pages and catalogs the already audited September report with zero indexed project records. IDs and estimates are cross-checked against the frozen controls. Descriptions retain the extracted source-row wording. Detailed categories, status, facility classifications and milestones remain unindexed, and their absence is visible.

Use a single version-controlled JSON input rebuilt from the existing PDF loader and row controls. Validate its source-inventory digest, document versions, ordered ID/amount associations and candidate links before loading it. Rebuild in memory and atomically replace one validated artifact so extraction failures preserve the previous file. The public runtime reads this artifact, inventory and controls and needs no raw PDFs or persistent writes. Source URLs remain direct official links.

Reuse the existing exact-ID SQL for candidate links without invoking comparison approvals. Use parameterized DuckDB search over source records, with a small fixed sort whitelist. Pandas is limited to presenting search results. Map airport codes only when an unambiguous explicit MIA, OPF, TMB or X51 token appears in the original description. Preserve unknown locations and all source rows. Current counts are source-record counts and provide no unique-project or complete-airport-budget measure.

## D008 — Read-only Streamlit source profiles and explicit public coverage

**Stage 1 interface decision.** Use one Streamlit app with directory/detail and source-coverage sections. Reuse the validated public registry and parameterized source-record search. Cache only the immutable registry object, with a fresh in-memory DuckDB connection per search. Render exact currency strings in Pandas tables. Keep source-record selection and versioned deep links explicit, and retain candidate associations as separate observations.

Index only the fields that pass the current controls. Show project IDs, source descriptions and total estimated cost with report/page provenance. Use source program classification and documented airport tokens. Detailed type, status, standalone facilities and milestone fields remain unindexed. The interface provides unknown, empty-result and failed-validation states, and the catalog exposes both partial indexing and catalog-only reports.

Streamlit 1.51.0 and Pandas 2.3.3 were installed in the repository-local environment and tested under Python 3.13.1. The app reads the checked-in artifact and performs no persistent runtime data writes. Local browser QA and simulated AppTest cover the vertical slice. Hosting remains a separate explicitly approved action. Record operating instructions in RUN_PUBLIC_DIRECTORY.md.

## D009 — Integrated explorer and a single-document estimate insight

**Owner-authorized Stage 2A/2B, November 8, 2026.** Adopt the Airport Infrastructure & Capital Projects Explorer positioning. Replace repetitive institutional disclaimers in active product copy with source attribution and an independent-data-project note in Methodology. D007's earlier transparency positioning is historical.

Reuse the immutable public registry, existing source profiles, parameterized DuckDB search and all comparison controls. Add one Plotly discovery adapter, pinned at 6.3.1, rather than a new service or database. Rank one explicitly selected indexed Exhibit B report. Filter before ranking; retain report, filtered and missing-value denominators. Source periods are memorandum coverage, not known data-freeze dates. Estimates are neither spending nor approved budgets. Keep Decimal ordering and exact hover/table values; convert only graphical coordinates to float. Chart events must resolve a versioned reference within the active ranking. Provide a keyboard-accessible selector and exact-value evidence table.

Use the same detail renderer for directory and chart discoveries. Expose reported costs, source dates, original evidence and unavailable progress fields without creating project histories. Candidate links remain unresolved observations. No synthetic context, cost-growth claim or physical progress metric is added.

## D010 — Bounded monthly financial feasibility and next review gate

**Study-only source authorization.** Inspect official July 261147, August 261399 and the already cataloged September 261400, without adding either new source to the public inventory or registry. Store transparent research transcriptions under docs/research, with financial/summary locators, hashes, original headings and cell strings. A separate research checker reconciles all five monetary columns, each row, summary statements and consecutive contract balances using Decimal. The checker is not a production ingestion contract or proof of independently reviewed transcription.

The financial exhibit uses contract grain. Treat the explicit E20 double-hyphen/single-hyphen correspondence as a documented study alias. Resolve financial dashes only from explicit same-issue summary zeros. Preserve reported-month labels separately from memo dates and unknown ledger cutoffs. Reinspection of V009A procurement fields shows that its OMB description spans multiple airports while its specific Project Name / Description agrees with TMB. Different field granularity does not establish a contradiction or a quarterly project link.

The three sampled issues support conditional feasibility for a small contract history inside the existing explorer, not a standalone airport financial dashboard. Stage 2C should prioritize reported monthly and cumulative expenditures after independent transcription review, production source approval and financial schema/controls. Milestones require forecast/actual and status evidence first. Stop after Stage 2A/2B for independent review; do not implement financial charts automatically.

## D011 — Close out Stage 2 profile links and financial source bindings

The explorer URL represents browsing. Each directory or chart profile renders its own **Open profile permalink** from that record's versioned reference. A single valid `?record=` opens that exact profile independently of search and chart filters. Invalid, empty or ambiguous record links show a warning and a directory recovery link. Preserve existing valid references and use the same contract for related records. Surface the evidence links at the start of the profile and show current availability before the product description. Plot the estimate axis in USD millions while preserving exact unscaled hover, table and profile values.

The baseline research checker verified hashes and arithmetic. Independent review found that wrong page and row locators, an unrelated zero note and balanced row reassociation could survive that check. With pinned PDFs, the study checker now validates document and page identity, reads the ordered financial cells and matches each summary contract block at its exact issue, page and row. The no-PDF mode checks arithmetic and static pins. The closeout corrects August's cumulative heading and records A19-MDAD-01's unresolved airport attribution. Named human sign-off remains pending.

The Stage 2C approval package in FINANCIAL_FEASIBILITY.md specifies three pinned financial slices and their supporting summary pages, four contracts, one reported monthly expenditure chart and one exact monthly/cumulative table. The owner must authorize those production sources and accept reviewed definitions and evidence before implementation.

## D012 — Owner-authorized Stage 2C and financial display gate

Stage 2C and the three production source slices received approval on November 8, 2026. The three slices are July matter 261147 Exhibit B p. 28 and summary pp. 19–20, August matter 261399 Exhibit B p. 29 and summary pp. 20–21, and September matter 261400 Exhibit B p. 30 and summary pp. 21–22. Scope is four contracts, one monthly USD bar chart and an exact monthly/cumulative table with original links.

Move the single evidence artifact to data/financial/snapshots.v1.json and add the versioned financial definitions. Reuse the Package A pinned PDF controls for canonical, atomic build verification. The runtime checks the pinned artifact digest and reconciled Decimal amounts. The source-row identity and contract key remain separate. This sample preserves the explicit E20 alias, the four corroborated summary zeros and unknown accounting cutoff and basis.

Independent human review is a separate ordinary-display gate. A locally provisioned named attestation must bind the exact artifact digest, definition version and all twelve versioned source rows. Its completion timestamp must be timezone-aware and elapsed. A server flag and explicit loopback address permit deliberate local review with a pending banner. The ordinary view hides financial values when the gate fails. No client parameter can affect that decision.

The named confirmation was recorded in the local attestation. The ordinary view was verified with the preview flag unset. Keep the review record in local operator state and provision it separately for each installation.

## D013 — Source-only release preparation

Use a committed source export for release verification. Keep project explanations focused on product behavior, public sources and reproducible steps. Browser error messages provide an availability notice and leave detailed diagnostics to operator tools. Provision the financial attestation separately from the source export so the named review stays in private operator configuration.

## D014 — Configure financial review on Streamlit Community Cloud

Use the existing public GitHub repository as the deployment source. Store the financial attestation in the nested `financial_review.attestation_json` setting in Streamlit Secrets. The same validator checks the local file and the configured secret. When the review setting is absent, use the local file. When the configured review is invalid or stale, keep ordinary financial display closed. Keep the attestation, local Secrets file and hosted Secrets value outside Git. Add the app URL after hosted verification.

The owner approved public hosting. The deployment uses Python 3.13 and exposes the explorer at `mia-capital-intelligence.streamlit.app`. The README links to that verified endpoint. Hosted contract spending was verified with the existing attestation provisioned in Streamlit Secrets. Future financial input versions still require review before ordinary display.

## D015 — Portfolio walkthrough and evidence

Open the explorer on the estimate ranking. Keep the full-report estimate distribution in an expandable section and let a selected range open the directory with the same report and range. Show two source records side by side within one report, with their own amounts, descriptions and source pages.

Explain cumulative spending using the prior expenditures reported in July, the sum of the three reviewed monthly amounts and the reported September cumulative amount. Keep the explanation inside the existing financial display gate. Present T180B as a held evidence case. The original pages establish the reported observations and the presence of T180D in the earlier indexed exhibit. Comparable D60 scope and estimate basis remain unresolved.
