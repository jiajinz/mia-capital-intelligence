# Stage 1A reconciliation and eligibility audit

This independent portfolio project has no affiliation with MDAD or HNTB. The audited scope is the local comparability gate for the two pinned Directive 241354 Exhibit B snapshots. No substantive human approval was supplied.

## Actual result

- Source observations 222, split into 110 earlier and 112 later records.
- Candidate pairs 107. Held 107, comparable 0, excluded 0, approved metric comparisons 0.
- Earlier-only records 3, AC053A, BA026A and T180D.
- Later-only records 5, CA096A, CA176B, DA142A, GA025A and W057A.
- Blocked candidate/metric slots 107. Each is the total-estimated-cost metric without explicit identity, scope, measure, basis and period approval.
- Source and review technical validation errors 0 for the checked-in empty review bundle. All reviewers and decision timestamps remain unassigned.

The original four page controls were reproduced with zero missing estimates. Earlier 260526 p. 11 contains 66 records and 2,955,660,025 USD, and p. 12 contains 44 records and 3,446,491,140 USD. Later 261402 p. 12 contains 68 records and 3,356,850,420 USD, and p. 13 contains 44 records and 3,406,481,145 USD. These are extraction reconciliation values, with the reporting-boundary and overlap caveats recorded in SOURCE_AUDIT.md. The gate validates each ID/amount association before any candidate or eligibility query.

## Test and compatibility evidence

Python 3.13.1, DuckDB 1.4.3, jsonschema 4.25.1, pdfplumber 0.11.9 and pypdfium2 5.14.0 ran in the local virtual environment. The full suite passed **73 tests**, comprising the 25 unchanged Stage 0 tests and 48 new gate/integration cases. Four of the Stage 0 tests and three new tests execute the pinned PDF inputs. Package consistency and Python compilation checks were performed. The review schema passed Draft202012Validator.check_schema.

New tests exercise equal-ID/name/value default holds, metric-specific approval, held/excluded paths, all six evidence dimensions, named and unassigned decisions, invalid outcomes, timezone-aware timestamps, duplicate and conflicting decisions/evidence, unknown references, changed checksums, source duplicates and exhibit boundaries, report-period order, unknown or unusable financial values, one-sided presence, deterministic results and all public view paths. Synthetic positive examples preserve cents through DuckDB DECIMAL(18,2). Additional cases prove that one pair's approval grants no other pair or metric and that a later invalid metric cannot leave an earlier grant visible.

## Independent output inspection

Two fresh complete CLI executions produced byte-identical JSON with SHA-256 `b11d10d56a1c4f220b00c021473edca7122458429a24f95baba5e4b25b13ee2b`. A separate JSON inspection asserted 222 unique source references, 107 held pairs with empty approved-metric lists and null reviewer/timestamp, an empty approved-comparisons relation, 107 blocked metric slots, and no validation errors. Each one-sided record carried only report-presence semantics. The approved SQL relation is empty under the real bundle.

The schema-byte SHA-256 is `cc7837dbf2abaa0fb5062d61295316b98333ee9e137ef662869a807d05c43c6b`. The canonical parsed review-bundle SHA-256 is `af2839852eec58361777ab25f7c697b3539d3f23a35cd73e293443fcbfc1aae5`. The report includes these identities and the original PDF checksums. Equivalent input bytes and the same implementation reproduce the output, with no runtime timestamp added to decisions.

The separate PDFium command matched all 222 frozen controls. The original profiler retained all ten quarterly page controls and the established candidate/presence counts. All three local PDF byte identities still match the inventory.

## Reproduction

From the repository root with the three previously verified originals in data/raw:

```sh
.venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m pytest -q
PYTHONPATH=src .venv/bin/python scripts/check_exhibit_b_controls.py
PYTHONPATH=src .venv/bin/python scripts/profile_infrastructure.py
PYTHONPATH=src .venv/bin/python -m mia_capital_intelligence.review_gate --section approved_comparisons
PYTHONPATH=src .venv/bin/python -m mia_capital_intelligence.review_gate --project CA176A
PYTHONPATH=src .venv/bin/python -m mia_capital_intelligence.review_gate --section unmatched_records
```

For byte reproducibility, redirect two full CLI runs into separate ignored temporary files and compare them with `cmp`. SOURCE_AUDIT.md provides verified-before-replacement acquisition instructions for a fresh checkout. REVIEW_DISPOSITIONS.md gives a real unassigned draft and the review procedure. HUMAN_REVIEW_PACKET.md supplies source locations and specific questions.

## Limits and Stage 1B recommendation

The implementation checks technical completeness and lineage. Human reviewers must supply substantive identity, scope, metric, basis and period confirmation. Machine agreement on all 222 cells does not supply human row sign-off. All 107 pairs currently lack approval and produce zero eligible comparisons, including same-price CA176A. Source memo periods do not establish project data freeze dates. The existing broader source-audit caveats remain applicable.

Recommend a conditional go for reviewing a narrowly defined Stage 1B scope after independent acceptance of Stage 1A. Stage 1B still needs owner authorization and an explicit policy for change outputs from approved metrics. With the current real review bundle, any such approved change relation must remain empty. The human review queue is already useful for locating evidence and asking scope questions, with positive approval paths demonstrated only through labeled synthetic tests.
