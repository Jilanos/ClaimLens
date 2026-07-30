## item_078_borner_et_observer_la_file_de_jobs_web - Borner et observer la file de jobs web
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Operations
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- La file en memoire n'a pas de limite explicite ni de signaux de saturation et les transitions sont insuffisamment exploitables en production.

# Scope
- In:
  - Limite configuree de jobs actifs et en attente.
  - Refus controle avec message actionnable lors de la saturation.
  - Metriques ou endpoint operationnel pour etats, durees et echecs.
  - Tests de saturation, interruption et relance apres redemarrage.
- Out:
  - File externe persistante.
  - Execution multi-replica.

# Acceptance criteria
- AC1: Une action au-dela de la capacite est refusee sans creer de job orphelin.
- AC2: L'operateur peut observer jobs queued/running/failed, durees et raison du dernier echec.
- AC3: Un job interrompu au redemarrage est retryable et ne bloque plus son action.

# AC Traceability
- request-AC3 -> This backlog slice. Proof: AC1: Une action au-dela de la capacite est refusee sans creer de job orphelin.
- request-AC2 -> This backlog slice. Evidence needed: Une suite HTTP demarre le serveur reel et couvre cookies, CSRF, corps trop volumineux, redirections, isolation de deux clients, rapports, limites de debit et comportement derriere proxy.
- request-AC4 -> This backlog slice. Evidence needed: Les API keys stockees disposent d'un format versionne avec key_id, d'une rotation transactionnelle testee et d'un chemin de migration v1 vers AES-GCM v2.
- request-AC5 -> This backlog slice. Evidence needed: La CI valide aussi l'image Docker; les actions, artefacts SBOM/provenance et le deploiement d'image sont rendus tracables et reproductibles.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_017_hardening_de_production_claimlens_suivi`
- Architecture decision(s): (none yet)
- Request: `req_013_finaliser_le_hardening_web_et_operationnel_de_claimlens`
- Primary task(s): `task_017_orchestrer_le_suivi_de_hardening_web_et_operationnel_claimlens`

# AI Context
- Summary: Borner et observer la file de jobs web
- Keywords: scaffolded-backlog, borner et observer la file de jobs web, implementation-ready
- Use when: Implementing the scaffolded slice for Borner et observer la file de jobs web.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_017_orchestrer_le_suivi_de_hardening_web_et_operationnel_claimlens`

# Notes
- Task `task_017_orchestrer_le_suivi_de_hardening_web_et_operationnel_claimlens` was finished via `logics-manager flow finish task` on 2026-07-30.
