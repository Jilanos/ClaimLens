## item_025_persist_verification_evidence_and_verdict_state - Persist verification evidence and verdict state
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Evidence data model
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The existing sources and claim_sources tables are not sufficient to store cited supporting and contradicting evidence snippets.
- Verified briefs need auditable evidence records, not only final verdict strings.

# Scope
- In:
  - Add minimal schema extensions or new tables for verification runs and evidence snippets.
  - Persist source adapter, matched claim, snippet text, evidence polarity, rationale, and retrieval metadata.
  - Update claim verdicts without losing not_checked history where evidence is insufficient.
  - Add migration/idempotency tests.
- Out:
  - Large document storage.
  - Full-text paper archival.
  - Destructive migrations without tests.

# Acceptance criteria
- AC1: Source candidates and evidence snippets are queryable by video, claim, and verification run.
- AC2: Supporting and contradicting evidence snippets are represented separately.
- AC3: Verdict state supports supported, contradicted, mixed, unclear, and not_checked.
- AC4: Schema changes are idempotent and covered by tests.

# AC Traceability
- request-AC3 -> This backlog slice. Proof: AC1: Source candidates and evidence snippets are queryable by video, claim, and verification run.
- request-AC4 -> This backlog slice. Proof: AC2: Supporting and contradicting evidence snippets are represented separately.
- request-AC5 -> This backlog slice. Proof: AC3: Verdict state supports supported, contradicted, mixed, unclear, and not_checked.
- request-AC9 -> This backlog slice. Proof: AC4: Schema changes are idempotent and covered by tests.
- request-AC6 -> This backlog slice. Evidence needed: Evidence assessment includes a concise rationale and a human-review disclaimer for health/science outputs.
- request-AC7 -> This backlog slice. Evidence needed: The Markdown brief renderer can produce a source-verified variant with citations, evidence snippets, verdicts, and a visible source-verification status.
- request-AC8 -> This backlog slice. Evidence needed: The local HTML process page shows the verification step status, failure causes, verdict summaries, source counts, and links to verified outputs.
- request-AC10 -> This backlog slice. Evidence needed: Tests cover adapter query construction, mocked PubMed/Semantic Scholar responses, source persistence, verdict assessment, verified brief rendering, and HTML process-state rendering without live network calls.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_005_claimlens_advanced_source_verification_mode`
- Architecture decision(s): (none yet)
- Request: `req_004_advanced_source_verification_mode`
- Primary task(s): `task_005_orchestrate_advanced_source_verification_mode`

# AI Context
- Summary: Persist verification evidence and verdict state
- Keywords: scaffolded-backlog, persist verification evidence and verdict state, implementation-ready
- Use when: Implementing the scaffolded slice for Persist verification evidence and verdict state.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_005_orchestrate_advanced_source_verification_mode`

# Notes
- Task `task_005_orchestrate_advanced_source_verification_mode` was finished via `logics-manager flow finish task` on 2026-07-23.
