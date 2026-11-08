# MIA Capital Intelligence

- The approved primary product is a Public Airport Infrastructure & Capital Projects Transparency Explorer. See docs/PRODUCT_VISION.md. Stage 1 is the public directory vertical slice. Stop for independent review before Stage 2.
- Individually validated source observations may be displayed publicly without cross-report comparison approval. Keep source records, candidate associations and verified project identities distinct. Counts must state their grain and reporting coverage.
- Preserve the comparison contract for analytical claims. Shared IDs alone establish candidate associations only. Public presentation must retain source evidence and meaningful unknown states.

- Work within this repository. Preserve user files and Git history. Keep unrelated repositories and global configuration outside the project.
- This independent portfolio project uses public records. Identify the source coverage and disclose that the project is independent of MDAD and HNTB.
- Write code, tests, comments, and repository documentation in English. Explain each meaningful milestone to the owner in Chinese.
- Read docs/PROJECT_STATE.md, docs/DECISIONS.md, and docs/REVIEW_PACKET.md before working. Stage 0 ends at external review. Start Stage 1 only after owner clearance. Obtain owner review for new sources, major architecture changes, financial definition changes, and scope expansion.
- Separate acquisition, extraction, validation, analytical modeling, rules, queries, and presentation. Prefer a small Python 3.13 src package with typed interfaces, explicit data contracts, and pytest. Use a repository-local environment.
- Keep the source URL, document version and SHA-256, report period, page index and printed labels, table, row locator, raw field and value, transformations, and verification status.
- Use decimal currency arithmetic. Keep estimates, adopted and approved budgets, contract awards, expenditures, and maintenance ROM amounts distinct. Preserve unknowns and surface duplicate, missing, and conflicting rows.
- Require comparable periods, measures, project identity, and scope before evaluating changes. Reconcile against the original tables and manually review material changes and management-critical findings. Describe review flags as requests for follow-up.
- Keep validated inputs reproducible. The eventual Streamlit app is read-only. Keep synthetic fixtures separate from production data and omit raw PDFs, virtual environments, secrets, caches, and generated databases from commits.
- At each milestone inspect, design, implement, validate, self-review, and update the state, decisions, and independent review packet. Evaluate external findings against the repository before adopting them.
- Use Conventional Commits for validated milestones. Inspect the staged diff before committing. Report the branch, hash, subject, changed files, validation, and outstanding issues. Push, merge, rebase shared history, force-push, release, or tag only with explicit approval.
