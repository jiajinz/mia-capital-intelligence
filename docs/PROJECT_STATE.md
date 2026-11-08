# Project state

## Stage 1A — Comparability gate ready for independent review

- Owner authorization covers Stage 1A only, an auditable project-comparability gate. Stage 1B scope review and authorization remain pending.
- Branch `main`. The preceding corrected baseline is `5da1fa1c07b2df95b7de7513d4e9f223a86c025f`. The Stage 1A unit is the commit titled `feat(review): enforce auditable metric comparability gate`. Resolve it with `git log -1 --format='%H %s' -- src/mia_capital_intelligence/comparability.py`.
- Sources remain the same three official PDFs in the inventory. The gate loads only the four controlled Exhibit B pages from 260526 and 261402. All 222 source rows pass the independent row controls and retain version, page, ordinal, cell text, measure and memo-period lineage. Project data freeze dates remain unknown.
- Actual dispositions are 107 default-held pairs, 0 approved pairs, 0 excluded pairs, 0 approved metric comparisons. No reviewer identity, decision timestamp or substantive sign-off has been supplied. Three earlier-only and five later-only rows remain visible as presence observations.
- Implemented typed source/amount contracts, stable version-specific pair IDs, strict review JSON schema, evidence/reference validation, and a DuckDB eligibility query. One metric's approval supplies no approval for another metric or project. Any technical error empties the submitted bundle's eligibility relation.
- The read-only CLI produces deterministic source, candidate, disposition, blocked and approved views through one gate. Stage 1A emits eligible source values and approval provenance. Change calculation belongs to a separately reviewed Stage 1B scope.
- Python 3.13.1, DuckDB 1.4.3 and jsonschema 4.25.1 work locally. The full suite has 73 passing tests. See STAGE_1A_AUDIT.md for reconciliation, leakage inspection and reproduction commands.
- A pre-existing README edit remains unchanged and excluded from this milestone. Its SHA-256 remains `dd3de625834f0d17e7602a685bffe679cf2343abef1253c6418019a2d9616c8b`. Public affiliation wording remains an owner review item. This project is independent of MDAD and HNTB.
- Next steps are external review of the gate, human consideration of HUMAN_REVIEW_PACKET.md and explicit agreement on Stage 1B scope. Human row-by-row sign-off, estimate-basis confirmation and project scope approval remain open. Positive approval examples are synthetic tests only.
