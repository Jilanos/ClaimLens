## item_063_make_web_action_rate_limits_proxy_aware_and_durable - Make web action rate limits proxy-aware and durable
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Deployment security
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The Caddy deployment makes the proxy IP the direct client address, so the current process-local limiter pools every user's quota and resets on restart.

# Scope
- In:
  - Define a trusted-proxy client identity contract.
  - Rate limit by authenticated account/session or validated client identity.
  - Persist or centralize state according to the supported deployment topology.
- Out:
  - Trusting arbitrary X-Forwarded-For headers from the public network.
  - Introducing user billing or subscription quotas.

# Acceptance criteria
- Two users behind Caddy do not share an action quota solely because they share a proxy.
- Direct requests cannot spoof another client's rate-limit identity.

# AC Traceability
- request-AC3 -> This backlog slice. Proof: Two users behind Caddy do not share an action quota solely because they share a proxy.
- request-AC4 -> This backlog slice. Proof: Direct requests cannot spoof another client's rate-limit identity.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_014_reliable_claimlens_jobs_and_evidence_aware_reports`
- Architecture decision(s): (none yet)
- Request: `req_010_harden_claimlens_production_reliability_and_verification_integrity`
- Primary task(s): `task_011_orchestrate_production_reliability_and_verification_integrity_hardening`

# AI Context
- Summary: Make web action rate limits proxy-aware and durable
- Keywords: scaffolded-backlog, make web action rate limits proxy-aware and durable, implementation-ready
- Use when: Implementing the scaffolded slice for Make web action rate limits proxy-aware and durable.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_011_orchestrate_production_reliability_and_verification_integrity_hardening`

# Notes
- Task `task_011_orchestrate_production_reliability_and_verification_integrity_hardening` was finished via `logics-manager flow finish task` on 2026-07-24.
