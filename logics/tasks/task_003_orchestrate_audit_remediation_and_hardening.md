## task_003_orchestrate_audit_remediation_and_hardening - Orchestrate Audit Remediation and Hardening
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [x] 1. Start with deterministic SQLite connection closure because it is the most direct runtime reliability finding.
- [x] 2. Add the minimal CI quality gate so future remediation work is automatically checked.
- [x] 3. Harden or document the configuration loading contract, including path overrides and malformed numeric values.
- [x] 4. Document the schema migration policy before any schema version 2 work begins.
- [x] 5. Run local validation, update affected Logics docs at each meaningful wave, and close the chain only after lint, tests, and Logics validation pass.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_010_close_sqlite_connections_deterministically`
- `item_011_harden_configuration_loading_contract`
- `item_012_add_minimal_ci_quality_gate`
- `item_013_document_schema_migration_policy`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> `item_010_close_sqlite_connections_deterministically`. Proof: `contextlib.closing` wraps helper-owned SQLite connections and tests assert close calls.
- request-AC2 -> `item_011_harden_configuration_loading_contract`. Proof: README documents the repository-root default config contract and tests cover default loading.
- request-AC3 -> `item_011_harden_configuration_loading_contract`. Proof: all configured path fields have environment overrides covered by tests.
- request-AC4 -> `item_011_harden_configuration_loading_contract`. Proof: invalid pipeline integer values raise `ConfigError` with the invalid key in the message.
- request-AC5 -> `item_012_add_minimal_ci_quality_gate`. Proof: `.github/workflows/ci.yml` runs `ruff check .` and `pytest` on push and pull request events.
- request-AC6 -> `item_013_document_schema_migration_policy`. Proof: README documents the schema version 1 contract and the migration requirement before schema version 2.
- request-AC7 -> `item_011_harden_configuration_loading_contract`, `item_013_document_schema_migration_policy`. Proof: README and ROADMAP document operator-facing config and schema policy changes.
- request-AC8 -> `item_010_close_sqlite_connections_deterministically`, `item_011_harden_configuration_loading_contract`, `item_012_add_minimal_ci_quality_gate`, `item_013_document_schema_migration_policy`. Proof: `.venv/bin/ruff check .`, `.venv/bin/pytest`, `logics-manager lint --require-status`, and workflow audit passed locally.

# Validation
- `.venv/bin/ruff check .` passed.
- `.venv/bin/pytest` passed: 10 passed.
- `logics-manager lint --require-status` passed.
- `logics-manager audit --legacy-cutoff-version 1.1.0 --group-by-doc` passed.
- .venv/bin/ruff check . passed; .venv/bin/pytest passed: 10 passed; logics-manager lint --require-status passed; logics-manager audit --legacy-cutoff-version 1.1.0 --group-by-doc passed before closeout preflight
- Finish workflow executed on 2026-07-23.
- Linked backlog/request close verification passed.

# Report
- Implemented deterministic SQLite connection closure, path override consistency, clear config integer errors, minimal CI, and schema migration policy documentation.
- Finished on 2026-07-23.
- Linked backlog item(s): `item_010_close_sqlite_connections_deterministically`, `item_011_harden_configuration_loading_contract`, `item_012_add_minimal_ci_quality_gate`, `item_013_document_schema_migration_policy`
- Related request(s): `req_002_audit_remediation_and_hardening`

# AI Context
- Summary: Orchestrate Audit Remediation and Hardening
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_002_audit_remediation_and_hardening`
- Product brief(s): `prod_003_claimlens_audit_remediation_and_hardening`
- Architecture decision(s): (none yet)
