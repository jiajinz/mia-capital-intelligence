# Independent review packet — Public transparency Stage 1

## Current registry unit

The owner approved a product pivot to the Public Airport Infrastructure & Capital Projects Transparency Explorer and a Stage 1 public-directory vertical slice. PRODUCT_VISION.md defines the public audience, accessibility problem, roadmap and disposition of the former internal-controls features. The historical Stage 1A packet below describes retained comparison infrastructure.

The registry unit preserves 222 controlled document-scoped source records, 107 unverified same-ID candidate associations and eight one-sided records. The separate verified-project and membership relations are empty. Three official documents are cataloged, with 110, 112 and zero indexed records. Individual observation display requires no comparability approval.

`public_registry.py` builds a deterministic, validated JSON artifact from the pinned originals and atomically replaces it after successful checks. It verifies source inventory/version identities, every ordered ID/amount association, unique source keys and candidate links. `directory_queries.py` provides literal parameterized SQL search, source/airport filters, stable sorting and individual source evidence. The public runtime needs no raw PDFs or review records. Airport codes are mapped only from unambiguous explicit tokens, leaving 15 observations unknown.

The 73-test prior baseline passed. The new registry unit has 31 passing tests covering registry corruption, source provenance, same-total swaps, source/page URLs, missing and ambiguous airports, identity separation, search/filter/sort behavior, exact amounts, raw-PDF-free operation, deterministic rebuilds and failed-build preservation. All 222 rows remain searchable. The Streamlit interface and browser acceptance are the next authorized unit, so Stage 1 is still in progress.

Registry unit subject `feat(data): publish controlled public source registry`, branch `main`. The preceding baseline is `1b36c5c30330f03591526a541ad770aa329bce6f`. The existing README edit is preserved and excluded. Review the model grains, unknown-airport policy and candidate/verified distinction before assessing the public interface. Historical comparison contracts retain their analytical scope.

## Historical Stage 1A packet

This independent public-records portfolio project has no affiliation with MDAD or HNTB. The owner authorized Stage 1A only. The preceding corrected baseline is `5da1fa1c07b2df95b7de7513d4e9f223a86c025f`.

## Objective and acceptance

Implement an auditable, fail-closed decision about whether a candidate's specific metric may enter an approved cross-report comparison. Preserve all Stage 0 controls. Require explicit human assertions for project identity, scope, financial metric, estimate basis, reporting period and original rows. Identity or amount matching supplies no approval. Retain held, excluded, unmatched, raw evidence and technical-error outputs. Provide a human review packet, meaningful regressions and a read-only local query boundary.

Stage 1A outputs eligible original values and provenance. Derived changes belong to the separately reviewed Stage 1B scope. The prior scope contract's null-delta requirement remains applicable to future change outputs. The implemented contract uses held/comparable/excluded and versioned metric-specific approval. All 107 real candidates explicitly default to held.

## Implemented files and flow

1. `source_records.load_exhibit_b` in `src/mia_capital_intelligence/source_records.py:19` verifies the pinned PDF bytes, page boundaries and every ordered ID/amount control. It returns 222 typed observations with original descriptions, headers, raw amounts, exact Decimal values, row locators and document context. `comparability_model.py` defines source documents, source records and amount observations. Physical source references include the full PDF checksum; pair IDs hash the ordered earlier/later references.
2. `sql/candidates.sql` performs a parameterized same-exhibit full outer exact-ID join. Before SQL, `comparability._source_errors` rejects invalid source versions, duplicate source or project keys, invalid financial values and overlapping/reversed memo periods. The join yields 107 candidates and 8 one-sided records.
3. `schemas/review_dispositions.schema.json` defines version 1.0. `data/review_dispositions.json` contains empty evidence/decision arrays, which explicitly invokes the default-held rule. `comparability._schema_errors` validates structure and timestamps, and `_review_errors` checks references, uniqueness and six evidence dimensions per approved metric. Human assertions remain attributed input claims.
4. `comparability.evaluate_gate` at `src/mia_capital_intelligence/comparability.py:179` inserts metric-specific grants into an initially empty `eligible_metrics` relation only after ALL technical validations pass. `sql/approved_metrics.sql` joins those grants to usable exact-decimal observations for the same metric and unit. Any technical failure invalidates the whole bundle for the run, leaves source evidence available, and returns zero approved metric rows.
5. `review_gate.main` at `src/mia_capital_intelligence/review_gate.py:70` is the shared read-only entry point. Section and project filters operate after gate evaluation. Every run returns contract/schema/review provenance and technical status. Held projects are inspectable as two individual observations. The connection is in memory and closes after evaluation.
6. `docs/REVIEW_DISPOSITIONS.md` gives schema, decision entry and PyCharm instructions. `docs/HUMAN_REVIEW_PACKET.md` presents seven real examples. `docs/STAGE_1A_AUDIT.md` records the reconciliation, test counts and deterministic-output digest. `docs/DECISIONS.md`, `docs/PROJECT_STATE.md`, `docs/DATA_DICTIONARY.md`, `docs/SCOPE_REVIEW_CONTRACT.md` and `docs/SOURCE_AUDIT.md` reflect the authorized boundary.

## Actual result

- Source rows 222. Candidate pairs 107. Held 107, approved pairs 0, excluded pairs 0, approved metrics 0. No actual reviewer or decision timestamp was supplied. Missing substantive review evidence explains all default holds.
- Earlier-only 3, AC053A, BA026A and T180D. Later-only 5, CA096A, CA176B, DA142A, GA025A and W057A. These are reporting-presence observations.
- All four Exhibit B page controls and all 222 ordered source-ID/amount associations remain unchanged. Earlier controls are 66 / 2,955,660,025 USD and 44 / 3,446,491,140 USD. Later controls are 68 / 3,356,850,420 USD and 44 / 3,406,481,145 USD. There are zero missing estimates in this controlled slice.
- The real bundle has zero technical validation errors. All 107 cost-comparison slots are blocked. Empty evidence/decision input is a valid held result, without fabricated sign-off.

## Evidence for external review

The three official PDF versions and their SHA-256 digests remain pinned in `data/source_inventory.json`. The gate uses only [260526 Exhibit B pp. 11–12](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/260526.pdf#page=11) and [261402 Exhibit B pp. 12–13](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261402.pdf#page=12). Memo coverage periods remain October–December 2025 and January–March 2026. The project data freeze dates remain unknown. All frozen row controls are shareable in `data/audit/exhibit_b_row_controls.csv`.

- **CA176A**, earlier B p. 11 row 42 and later B p. 12 row 41. Both original estimates are 3,191,832 USD. The later description adds Ph2, with later-only CA176B on p. 12 row 42 at 2,229,920 USD. CA176A remains held despite equal values. Ask which seating scope belongs to each identifier.
- **T180B**, earlier B p. 11 row 63 at 914,627,764 USD and later B p. 12 row 65 at 1,066,231,593 USD. Earlier-only T180D is p. 11 row 64 at 163,567,943 USD with a D60 apron/utilities description. Preserve the two T180B observations and ask whether the same scope and estimate basis apply. The gate emits zero approved T180B comparisons.
- **BA133A**, earlier B p. 11 row 36 and later B p. 12 row 34. The description changes from perimeter protection to phase 2 security cameras. It remains held pending scope/basis evidence.
- **AA005A / AA022A** have matching identifiers, descriptions and amounts in these rows. Both remain held because successful matching does not supply substantive project and estimate-basis review. See the human packet for precise source references and follow-up questions.

## Tests and independent result inspection

The full suite passes 73 tests under Python 3.13.1, with DuckDB 1.4.3 and jsonschema 4.25.1. The 25 Stage 0 tests are preserved. New tests exercise all six evidence dimensions, default held behavior, explicit synthetic approvals and exclusions, metric-specific permission, stale checksums and references, schema/status errors, duplicate/conflicting reviews, timezones, source cardinality, unusable amounts, period ordering, one-sided records and deterministic results. Real-input integration verifies counts, CA176A/T180B holds, CA176B/T180D presence, no approval leakage and a nonzero CLI exit for malformed decisions.

Synthetic tests prove an approved cost metric can return exact cents while a budget metric stays blocked. A separate case approves one pair while a second remains held. A later invalid metric also blocks an earlier otherwise valid grant. No real positive approval is claimed.

Two full real CLI executions produced byte-identical JSON. Independent parsing checked the empty approved relation, every held pair's empty metric list and null reviewer/timestamp, unique source references and presence semantics. The exact output digest and schema/input identities are in STAGE_1A_AUDIT.md. The separate PDFium checker matched all 222 controls and the original profiler reproduced its ten page controls. Dependency consistency, Python compilation, JSON Schema validity and staged whitespace checks were also performed.

## Reproduce and inspect

```sh
.venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m pytest -q
PYTHONPATH=src .venv/bin/python scripts/check_exhibit_b_controls.py
PYTHONPATH=src .venv/bin/python scripts/profile_infrastructure.py
PYTHONPATH=src .venv/bin/python -m mia_capital_intelligence.review_gate --section approved_comparisons
PYTHONPATH=src .venv/bin/python -m mia_capital_intelligence.review_gate --project CA176A
PYTHONPATH=src .venv/bin/python -m mia_capital_intelligence.review_gate --section unmatched_records
```

For a reviewer without a checkout, share this packet, STAGE_1A_AUDIT.md, HUMAN_REVIEW_PACKET.md, the review schema, disposition instructions, row controls and the Stage 1A Git diff. The public PDF links above allow direct source inspection. SOURCE_AUDIT.md describes acquisition and checksum verification. In PyCharm debug `evaluate_gate` before eligible-metric insertion, then inspect the empty real grants and the approved SQL result. The synthetic metric-isolation test demonstrates the positive path.

## Known limits and review questions

1. Does every supported query view preserve the distinction between raw source observations, submitted human claims, technical validation and actual eligibility? Can an unapproved pair or metric enter the approved SQL relation through any normal entry point?
2. Are the six evidence dimensions, source references, date rules and one-active-decision policy sufficient for this local pilot? The software checks supplied assertions and attribution fields. Humans remain responsible for the truth and adequacy of scope/basis evidence.
3. Is the conservative whole-bundle invalidation policy appropriate? One malformed or incomplete approval currently blocks all grants for that execution. Valid source inputs and candidate coverage remain inspectable.
4. Is the proposed Stage 1B scope ready for owner review? All real candidates still lack substantive approval, human row-by-row confirmation remains pending, and source freeze dates remain unknown. Approved change outputs would remain empty with this bundle.

Ranked next improvements are external gate review, evidence-based consideration of the real human packet, then agreement on a tightly scoped Stage 1B change-output contract. Human review and sign-off are required before publishing substantive comparisons.

## Commit and handoff

Branch `main`. Stage 1A subject `feat(review): enforce auditable metric comparability gate`. Resolve the exact hash with `git log -1 --format='%H %s' -- src/mia_capital_intelligence/comparability.py` and inspect `git show <resolved-hash>`. The original Stage 0 baseline is `55f6e39e630c18dc5e61672965dfef4bf7b72e3c`; its corrective commit is `5da1fa1c07b2df95b7de7513d4e9f223a86c025f`.

The pre-existing README modification is unchanged and excluded. Its preserved byte digest is recorded in STAGE_1A_AUDIT.md. Stage 1B remains subject to external acceptance of this gate, scope review and explicit owner authorization.
