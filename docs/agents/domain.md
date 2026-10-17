# Domain docs

This is a single-context repository: domain vocabulary belongs in root
`GLOSSARY.md`, and architectural decisions belong in `docs/adr/`.

Before exploring the codebase, read the glossary when present and ADRs relevant
to the task. If a glossary or ADR directory is absent, proceed silently; create
domain documents only when terminology or decisions actually need recording.

Use the glossary's vocabulary in issue titles, documentation, and code. If a
needed concept is missing, reconsider the term or note the gap for the
`domain-modeling` skill. Surface conflicts with an existing ADR explicitly before
proposing a different decision.

Use `README.md` for project navigation, `docs/architecture.md` for the platform
contract, and `docs/versions.md` and `docs/milestones.md` for recorded evidence.
Distinguish prepared configuration and static validation from observed host,
CUDA, Kubernetes, and inference results.
