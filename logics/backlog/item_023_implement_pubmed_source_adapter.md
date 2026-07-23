## item_023_implement_pubmed_source_adapter - Implement PubMed source adapter
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: PubMed retrieval
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Health/science verification needs biomedical literature retrieval from PubMed.
- The adapter must be testable without live NCBI calls.

# Scope
- In:
  - Implement PubMed search/fetch boundary using configured NCBI key when present.
  - Map PubMed metadata into SourceCandidate.
  - Respect configured result limits and timeouts.
  - Add mocked tests for successful, empty, and failure responses.
- Out:
  - Full MeSH expansion.
  - Clinical guideline ranking.
  - Live PubMed CI tests.

# Acceptance criteria
- AC1: PubMed adapter returns normalized candidates for a claim query.
- AC2: Empty PubMed responses produce no-source results without crashing verification.
- AC3: Adapter tests run without network access.
- AC4: NCBI keys are read from runtime/config inputs and not persisted.

# AC Traceability
- request-AC2 -> This backlog slice. Proof: AC1: PubMed adapter returns normalized candidates for a claim query.
- request-AC3 -> This backlog slice. Proof: AC2: Empty PubMed responses produce no-source results without crashing verification.
- request-AC10 -> This backlog slice. Proof: AC3: Adapter tests run without network access.
- request-AC4 -> This backlog slice. Evidence needed: Each checked claim receives one non-binary verdict: supported, contradicted, mixed, unclear, or not_checked.
- request-AC5 -> This backlog slice. Evidence needed: Each verdict stores cited evidence snippets separated into supporting and contradicting evidence where available.
- request-AC6 -> This backlog slice. Evidence needed: Evidence assessment includes a concise rationale and a human-review disclaimer for health/science outputs.
- request-AC7 -> This backlog slice. Evidence needed: The Markdown brief renderer can produce a source-verified variant with citations, evidence snippets, verdicts, and a visible source-verification status.
- request-AC8 -> This backlog slice. Evidence needed: The local HTML process page shows the verification step status, failure causes, verdict summaries, source counts, and links to verified outputs.
- request-AC9 -> This backlog slice. Evidence needed: The implementation remains local-first and VPS-ready: API keys are runtime/config inputs only, host/path settings remain configurable, and generated outputs do not persist secrets.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_005_claimlens_advanced_source_verification_mode`
- Architecture decision(s): (none yet)
- Request: `req_004_advanced_source_verification_mode`
- Primary task(s): `task_005_orchestrate_advanced_source_verification_mode`

# AI Context
- Summary: Implement PubMed source adapter
- Keywords: scaffolded-backlog, implement pubmed source adapter, implementation-ready
- Use when: Implementing the scaffolded slice for Implement PubMed source adapter.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_005_orchestrate_advanced_source_verification_mode`

# Notes
- Task `task_005_orchestrate_advanced_source_verification_mode` was finished via `logics-manager flow finish task` on 2026-07-23.
