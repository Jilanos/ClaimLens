## item_018_design_optional_advanced_source_verification_mode - Design optional advanced source verification mode
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Advanced verification
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Source retrieval and claim assessment remain valuable but should not block the base MVP.
- The architecture needs extension points now to avoid a rewrite later.

# Scope
- In:
  - Document the optional `advanced_source_verification` mode.
  - Define source adapters for PubMed, Semantic Scholar, and curated web search as future interfaces.
  - Define how claims move from not-checked to verdict-assessed.
  - Keep base brief generation compatible with later citations and verdicts.
- Out:
  - Implementing live PubMed/Semantic Scholar calls in the base MVP.
  - Automated medical/legal/financial authority claims without human review.

# Acceptance criteria
- AC1: Architecture docs describe how advanced verification plugs into the run after LLM analysis.
- AC2: The base data model can represent source-unverified and source-verified briefs.
- AC3: The option is disabled by default and does not affect base MVP execution.

# AC Traceability
- request-AC7 -> This backlog slice. Proof: AC1: Architecture docs describe how advanced verification plugs into the run after LLM analysis.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_004_claimlens_single_video_local_first_mvp`
- Architecture decision(s): (none yet)
- Request: `req_003_mvp_single_video_local_first_pipeline`
- Primary task(s): `task_004_orchestrate_single_video_local_first_mvp`

# AI Context
- Summary: Design optional advanced source verification mode
- Keywords: scaffolded-backlog, design optional advanced source verification mode, implementation-ready
- Use when: Implementing the scaffolded slice for Design optional advanced source verification mode.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.
