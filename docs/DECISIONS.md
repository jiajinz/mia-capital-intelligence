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

Accept P1-02 as a business-definition defect. Establish the explicit disposition and approval contract now. Its executable query gate, complete candidate review records and acceptance tests belong to Stage 1 after owner authorization. Accept P2-01's acquisition concern and validate the downloaded temporary file before replacement in the documented sequential workflow. Retain the owner's uncommitted README edit and record its affiliation-disclosure question for owner consideration.
