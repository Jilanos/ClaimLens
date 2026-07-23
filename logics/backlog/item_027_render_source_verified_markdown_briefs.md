## item_027_render_source_verified_markdown_briefs - Render source-verified Markdown briefs
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Verified brief generation
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The current brief renderer only supports unverified analysis output.
- Reviewers need a clear verified variant with citations and evidence snippets.

# Scope
- In:
  - Render source-verified status in Markdown briefs.
  - Include each checked claim, verdict, rationale, supporting evidence snippets, contradicting evidence snippets, and citations.
  - Keep base not-advanced-source-verified brief rendering compatible.
  - Add snapshot-style rendering tests.
- Out:
  - CMS publishing.
  - Full HTML report export.
  - Citation formatting beyond stable Markdown links and source metadata.

# Acceptance criteria
- AC1: Verified brief output includes visible source-verification status.
- AC2: Each checked claim section lists verdict, rationale, supporting snippets, contradicting snippets, and citations.
- AC3: Brief rendering is idempotent.
- AC4: Rendering tests run without network access.

# AC Traceability
- request-AC5 -> This backlog slice. Proof: AC1: Verified brief output includes visible source-verification status.
- request-AC6 -> This backlog slice. Proof: AC2: Each checked claim section lists verdict, rationale, supporting snippets, contradicting snippets, and citations.
- request-AC7 -> This backlog slice. Proof: AC3: Brief rendering is idempotent.
- request-AC9 -> This backlog slice. Proof: AC4: Rendering tests run without network access.
- request-AC10 -> This backlog slice. Proof: AC4: Rendering tests run without network access.
- request-AC8 -> This backlog slice. Evidence needed: The local HTML process page shows the verification step status, failure causes, verdict summaries, source counts, and links to verified outputs.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_005_claimlens_advanced_source_verification_mode`
- Architecture decision(s): (none yet)
- Request: `req_004_advanced_source_verification_mode`
- Primary task(s): `task_005_orchestrate_advanced_source_verification_mode`

# AI Context
- Summary: Render source-verified Markdown briefs
- Keywords: scaffolded-backlog, render source-verified markdown briefs, implementation-ready
- Use when: Implementing the scaffolded slice for Render source-verified Markdown briefs.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_005_orchestrate_advanced_source_verification_mode`

# Notes
- Task `task_005_orchestrate_advanced_source_verification_mode` was finished via `logics-manager flow finish task` on 2026-07-23.
