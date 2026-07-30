## item_080_rendre_la_chaine_ci_cd_conteneurisee_tracable - Rendre la chaine CI/CD conteneurisee tracable
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Supply chain
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- La qualite Python est verifiee, mais le build image n'est pas un gate de PR et les actions/deploiements reposent encore sur des references mutables ou des tags.

# Scope
- In:
  - Build Docker et smoke test de l'image dans la CI.
  - Actions GitHub epinglees par SHA avec version lisible en commentaire.
  - Scan de vulnerabilites selon un seuil explicite.
  - Publication et verification de SBOM/provenance.
  - Deploiement par digest d'image.
- Out:
  - Changement d'hebergeur ou de registre.
  - Signature de code hors chaine GitHub actuelle.

# Acceptance criteria
- AC1: Chaque PR construit l'image et execute un smoke test healthcheck sous utilisateur non-root.
- AC2: Les actions sont epinglees, le scan applique le seuil documente et les artefacts SBOM/provenance sont conserves.
- AC3: Le deploiement utilise le digest produit par le job de publication.

# AC Traceability
- request-AC5 -> This backlog slice. Proof: AC1: Chaque PR construit l'image et execute un smoke test healthcheck sous utilisateur non-root.
- request-AC2 -> This backlog slice. Evidence needed: Une suite HTTP demarre le serveur reel et couvre cookies, CSRF, corps trop volumineux, redirections, isolation de deux clients, rapports, limites de debit et comportement derriere proxy.
- request-AC3 -> This backlog slice. Evidence needed: La file de jobs est bornee, sa saturation est restituee clairement, les transitions et echecs sont observables, et le redemarrage conserve une experience retryable coherente.
- request-AC4 -> This backlog slice. Evidence needed: Les API keys stockees disposent d'un format versionne avec key_id, d'une rotation transactionnelle testee et d'un chemin de migration v1 vers AES-GCM v2.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_017_hardening_de_production_claimlens_suivi`
- Architecture decision(s): (none yet)
- Request: `req_013_finaliser_le_hardening_web_et_operationnel_de_claimlens`
- Primary task(s): `task_017_orchestrer_le_suivi_de_hardening_web_et_operationnel_claimlens`

# AI Context
- Summary: Rendre la chaine CI/CD conteneurisee tracable
- Keywords: scaffolded-backlog, rendre la chaine ci/cd conteneurisee tracable, implementation-ready
- Use when: Implementing the scaffolded slice for Rendre la chaine CI/CD conteneurisee tracable.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_017_orchestrer_le_suivi_de_hardening_web_et_operationnel_claimlens`

# Notes
- Task `task_017_orchestrer_le_suivi_de_hardening_web_et_operationnel_claimlens` was finished via `logics-manager flow finish task` on 2026-07-30.
