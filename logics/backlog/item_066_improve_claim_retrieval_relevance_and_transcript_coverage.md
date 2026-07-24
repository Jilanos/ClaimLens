## item_066_improve_claim_retrieval_relevance_and_transcript_coverage - Improve claim retrieval relevance and transcript coverage
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Evidence quality
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The first twelve filtered words of a claim are often a poor scholarly query, and long video analysis omits the middle of the transcript without a report-level coverage signal.

# Scope
- In:
  - Define domain-aware retrieval query generation and claim/time budgets.
  - Chunk and consolidate long transcripts or disclose omitted coverage in every affected report.
  - Add representative fitness and long-transcript fixtures.
- Out:
  - Replacing human expert review for health or science claims.

# Acceptance criteria
- The verification workflow records the final retrieval query and its adapter selection for auditability.
- A long transcript report states its coverage or derives claims from all chunks.

# AC Traceability
- request-AC8 -> This backlog slice. Proof: The verification workflow records the final retrieval query and its adapter selection for auditability.
- request-AC9 -> This backlog slice. Proof: A long transcript report states its coverage or derives claims from all chunks.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_014_reliable_claimlens_jobs_and_evidence_aware_reports`
- Architecture decision(s): (none yet)
- Request: `req_010_harden_claimlens_production_reliability_and_verification_integrity`
- Primary task(s): `task_011_orchestrate_production_reliability_and_verification_integrity_hardening`

# AI Context
- Summary: Improve claim retrieval relevance and transcript coverage
- Keywords: scaffolded-backlog, improve claim retrieval relevance and transcript coverage, implementation-ready
- Use when: Implementing the scaffolded slice for Improve claim retrieval relevance and transcript coverage.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_011_orchestrate_production_reliability_and_verification_integrity_hardening`

# Notes
- Task `task_011_orchestrate_production_reliability_and_verification_integrity_hardening` was finished via `logics-manager flow finish task` on 2026-07-24.
