# Public registry model and evidence contract

## Grains and constraints

- **Source document** has grain matter ID plus PDF SHA-256. The source inventory supplies the title, official URL, period basis, memo/introduction/acceptance dates, PDF size and page boundaries. The catalog adds publishing organization, indexed pages, indexed record counts, validation coverage and explicit gaps. The JSON artifact pins the inventory-byte digest and all three PDF versions.
- **Source record** has grain source version, exhibit, one-based PDF position and physical data-row ordinal. Its versioned source_ref is the public detail key. Project ID, original description, raw/parsed metric, header and row bounding box remain attached to that reference. Uniqueness and complete page controls are validated before display.
- **Verified project** represents an identity spanning source observations. The verified_projects relation and project_memberships relation are empty in this slice. The loader rejects unreviewed additions. The directory counts source records and supplies no unique-airport-project count.
- **Candidate link** connects exactly two source references with the same project token in the selected Exhibit B reports. The existing SQL matcher supplies these 107 connections and preserves their candidate_unverified status. The eight one-sided records remain independently indexed and acquire no cancellation or project-lifecycle inference.
- **Evidence** remains available through source metadata, original row/cell text, checksum, printed and PDF page labels, row ordinal, bounding box and direct official page URL. A source description is extracted wording. Independent frozen row controls cover project ID and estimate associations, and do not establish engineering scope or cross-document identity.

## Financial and classification semantics

The single public financial metric is Total Estimated Cost in USD from an individual report. It is parsed exactly with Decimal and queried as DECIMAL(18,2). UI tables contain formatted currency strings to avoid floating-point conversion in presentation. The directory supplies no cost delta, budget/spending aggregate, progress percentage or schedule conclusion.

Project names use the source description with whitespace and literal HTML entities normalized for readability. The original text is retained in evidence. Airport classification requires a unique explicit MIA, OPF, TMB or X51 token in that original description. Multiple or absent tokens yield unknown. Source report titles do not assign an airport to all contained rows. Program classification comes from the source section Capital Improvement Program. Detailed project type, separate facility fields, status and milestones remain unindexed.

## Build and query boundaries

public_registry.build_registry reuses the pinned source loader and row controls. It validates the artifact in memory before replacing one JSON file atomically. The committed artifact is reproducible source-derived input, with no synthetic production rows. The original PDFs remain ignored local acquisition inputs.

public_registry.load_registry validates artifact provenance and reconciles its rows to the controls using only tracked files. It is independent of analytical review dispositions. directory_queries.search_records builds an ephemeral DuckDB table for one query and binds every search/filter value. The sort order comes from a fixed whitelist. directory.sql returns one observation per source_ref. No financial comparison join is part of this public query.

The source catalog is derived from the inventory and actual record counts, so a cataloged report with no indexed rows stays at zero. Adding new reports needs explicit source evaluation and a deliberate update to the extraction/control contract. Verified identity mappings need their own evidence and review. These are proposed later-stage improvements.
