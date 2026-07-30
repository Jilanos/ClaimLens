## task_017_orchestrer_le_suivi_de_hardening_web_et_operationnel_claimlens - Orchestrer le suivi de hardening web et operationnel ClaimLens
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
- [x] 1. Etablir et tester le contrat de confiance Caddy-vers-ClaimLens avant tout changement de limitation.
- [x] 2. Introduire la fixture HTTP et les tests multi-client, puis les utiliser comme garde-fou pour les lots web et jobs.
- [x] 3. Borner et instrumenter les jobs en conservant le modele mono-instance actuel.
- [x] 4. Livrer et valider la rotation transactionnelle des secrets, y compris la migration v1 vers v2.
- [x] 5. Durcir la CI/CD conteneurisee et valider le deploiement par digest en staging.
- [x] 6. Executer les validations de closeout et documenter les procedures operatoires.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_077_fiabiliser_l_identite_client_derriere_le_reverse_proxy_et_tester_le_serveur_http`
- `item_078_borner_et_observer_la_file_de_jobs_web`
- `item_079_rendre_les_secrets_applicatifs_rotatifs_et_migrables`
- `item_080_rendre_la_chaine_ci_cd_conteneurisee_tracable`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> This task. Proof: scaffold command generated the request-chain corpus.
- request-AC4 -> This task. Proof: optional context-pack handoff is supported.
- request-AC6 -> This task. Proof: dry-run and collision checks bound file changes.
- request-AC8 -> This task. Proof: CLI help documents the one-pass scaffold workflow.
- request-AC2 -> This task. Proof: `tests/test_hardening.py` starts the real HTTP server and validates health and guest-cookie delivery; proxy identity and request bounds remain covered by deterministic service tests.
- request-AC3 -> This task. Proof: `db.create_job(..., max_queued_jobs=...)` reserves capacity atomically, `/health/jobs` exposes job state, and `tests/test_hardening.py` proves saturation leaves no extra row.
- request-AC5 -> This task. Proof: CI builds and health-checks the Docker image, scans critical CVEs, checks the application UID, and release deployment consumes the build digest.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Run scaffold command tests.
- `ruff check .` and `pytest` passed: 82 tests.
- Docker image build, `/health` smoke test, and application UID 10001 process check passed locally.
- ruff check and pytest: 82 passed; Docker image build, health smoke test, and non-root application process check passed
- Finish workflow executed on 2026-07-30.
- Linked backlog/request close verification passed.

# Report
- Implementation complete.
- Finished on 2026-07-30.
- Linked backlog item(s): `item_077_fiabiliser_l_identite_client_derriere_le_reverse_proxy_et_tester_le_serveur_http`, `item_078_borner_et_observer_la_file_de_jobs_web`, `item_079_rendre_les_secrets_applicatifs_rotatifs_et_migrables`, `item_080_rendre_la_chaine_ci_cd_conteneurisee_tracable`
- Related request(s): `req_013_finaliser_le_hardening_web_et_operationnel_de_claimlens`

# AI Context
- Summary: Orchestrer le suivi de hardening web et operationnel ClaimLens
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_013_finaliser_le_hardening_web_et_operationnel_de_claimlens`
- Product brief(s): `prod_017_hardening_de_production_claimlens_suivi`
- Architecture decision(s): (none yet)
