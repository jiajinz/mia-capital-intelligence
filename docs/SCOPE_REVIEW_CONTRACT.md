# Scope review contract for the proposed Exhibit B pilot

This originated as the Stage 0 design response to P1-02. The owner has authorized Stage 1A, which implements this comparability contract through a metric-specific execution gate. Stage 1B scope review and authorization remain pending. Stage 1A returns eligible source values and provenance. The delta requirements below apply to future change outputs. See REVIEW_DISPOSITIONS.md for the schema and executable review procedure.

## Candidate and disposition

Create one candidate for each of the 107 same-exhibit exact-token pairs, including pairs with identical amounts. Preserve the two source row identities, version checksums, raw descriptions and estimates, and memo coverage dates. Each candidate starts as `held`, with financial and milestone comparison fields null.

A review record must identify the candidate and both immutable source rows and contain a disposition (`held`, `comparable`, or `excluded`), reviewer identity, review date, reason, supporting evidence references, and an evidence-specific follow-up question. `comparable` requires explicit confirmation of equivalent project scope, estimate measure and estimate basis. A shared identifier, similar wording, unchanged amount or successful extraction supplies no approval by itself.

A review referring to a different source version, row or exhibit is invalid. An absent, incomplete or unverifiable approval leaves the candidate held. A numeric delta requires a valid comparable disposition and two verified usable amounts. A relative delta additionally requires a positive earlier amount. Review evidence and extraction evidence have separate statuses. Record any revision to a disposition and its rationale.

The 3 earlier-only and 5 later-only rows receive a presence disposition, their original evidence and a follow-up question. All comparison delta fields are null. Presence changes alone do not establish project start, completion, cancellation, consolidation or program transfer.

## Real cases awaiting review

- **CA176A**, 260526 B p. 11 and 261402 B p. 12. Both estimates are 3,191,832 USD. The later description adds `Ph2`, and CA176B appears only in later B p. 12. Keep CA176A held. Ask which portion of the earlier seating scope belongs to CA176A and CA176B and whether the estimate basis is equivalent.
- **T180B**, 260526 B p. 11 and 261402 B p. 12. Preserve the reported estimates 914,627,764 and 1,066,231,593 USD. T180D appears only in earlier B p. 11, with a D60 apron/utilities description and estimate 163,567,943 USD. Keep T180B held until evidence confirms the relationship and estimate basis. Ask whether D60 apron/utilities scope changed allocation between the two identifiers. Keep the published comparison fields null while held.
- **BA133A**, 260526 B p. 11 and 261402 B p. 12. The description changes from perimeter protection to phase 2 security cameras. Keep held pending evidence of scope and estimate-basis continuity.
- **CA096A** appears in earlier Exhibit A and later Exhibit B. The first pilot's earlier-only/later-only results reflect its selected exhibit boundary. A cross-exhibit linkage requires separate reviewed evidence and owner approval.

The numerical differences in the historical Stage 0 audit are arithmetic illustrations before scope approval. They do not grant any comparable disposition.

## Stage 1A acceptance and remaining human work

The implemented tests require absent approval, wrong-version evidence, equal amounts and incomplete basis confirmation to yield zero approved comparison rows. The real gate demonstrates held CA176A and T180B, later-only CA176B and earlier-only T180D, all 107 held dispositions and the 8 one-sided records. Synthetic tests exercise explicit metric approval. Human row confirmation and substantive approval remain pending. Stage 1B must separately review any derived change output and its publication rules.
