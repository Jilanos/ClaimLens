## item_077_fiabiliser_l_identite_client_derriere_le_reverse_proxy_et_tester_le_serveur_http - Fiabiliser l'identite client derriere le reverse proxy et tester le serveur HTTP
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Web security
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- La limite anonyme derive d'un X-Real-IP forgeable si le proxy ne l'ecrase pas.
- Les garanties web ne sont pas validees sur le vrai serveur HTTP.

# Scope
- In:
  - Contrat proxy de confiance et configuration Caddy explicite.
  - Resolution d'IP client defensive dans l'application.
  - Tests HTTP multi-client avec serveur ephemere et cas de spoofing.
- Out:
  - Refonte visuelle du Process page.
  - Modification du modele de verdict des sources.

# Acceptance criteria
- AC1: X-Real-IP est ecrase par Caddy et n'est honore par ClaimLens que depuis un proxy de confiance configure.
- AC2: Les requetes directes avec headers forwarded forges ne contournent pas le budget anonyme.
- AC3: Les tests HTTP couvrent cookies invites, CSRF, limite de taille, deux clients, autorisation des rapports, redirections et rate limiting.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: X-Real-IP est ecrase par Caddy et n'est honore par ClaimLens que depuis un proxy de confiance configure.
- request-AC2 -> This backlog slice. Proof: AC2: Les requetes directes avec headers forwarded forges ne contournent pas le budget anonyme.
- request-AC3 -> This backlog slice. Evidence needed: La file de jobs est bornee, sa saturation est restituee clairement, les transitions et echecs sont observables, et le redemarrage conserve une experience retryable coherente.
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
- Summary: Fiabiliser l'identite client derriere le reverse proxy et tester le serveur HTTP
- Keywords: scaffolded-backlog, fiabiliser l'identite client derriere le reverse proxy et tester le serveur http, implementation-ready
- Use when: Implementing the scaffolded slice for Fiabiliser l'identite client derriere le reverse proxy et tester le serveur HTTP.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_017_orchestrer_le_suivi_de_hardening_web_et_operationnel_claimlens`

# Notes
- Task `task_017_orchestrer_le_suivi_de_hardening_web_et_operationnel_claimlens` was finished via `logics-manager flow finish task` on 2026-07-30.
