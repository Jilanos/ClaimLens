## item_079_rendre_les_secrets_applicatifs_rotatifs_et_migrables - Rendre les secrets applicatifs rotatifs et migrables
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Secrets management
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- AES-GCM v2 protege les nouvelles ecritures, mais les anciennes valeurs v1 restent sans migration pilotee et la cle de chiffrement ne peut pas etre tournee sans interruption.

# Scope
- In:
  - Format de secret versionne avec key_id.
  - Configuration d'une cle active et de cles de lecture transitoires.
  - Commande transactionnelle de rotation avec verification et migration v1 vers v2.
  - Tests de rotation, mauvaise cle, corruption, rollback et compatibilite v1.
- Out:
  - Migration obligatoire vers un secret manager externe.
  - Changement du modele BYO key.

# Acceptance criteria
- AC1: Chaque nouvelle valeur chiffree contient une version et un key_id exploitables.
- AC2: La rotation rechiffre toutes les lignes eligibles dans une transaction et echoue sans ecriture partielle.
- AC3: Les secrets v1 sont migres vers v2 et le retrait de la compatibilite v1 est documente.

# AC Traceability
- request-AC4 -> This backlog slice. Proof: AC1: Chaque nouvelle valeur chiffree contient une version et un key_id exploitables.
- request-AC2 -> This backlog slice. Evidence needed: Une suite HTTP demarre le serveur reel et couvre cookies, CSRF, corps trop volumineux, redirections, isolation de deux clients, rapports, limites de debit et comportement derriere proxy.
- request-AC3 -> This backlog slice. Evidence needed: La file de jobs est bornee, sa saturation est restituee clairement, les transitions et echecs sont observables, et le redemarrage conserve une experience retryable coherente.
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
- Summary: Rendre les secrets applicatifs rotatifs et migrables
- Keywords: scaffolded-backlog, rendre les secrets applicatifs rotatifs et migrables, implementation-ready
- Use when: Implementing the scaffolded slice for Rendre les secrets applicatifs rotatifs et migrables.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_017_orchestrer_le_suivi_de_hardening_web_et_operationnel_claimlens`

# Notes
- Task `task_017_orchestrer_le_suivi_de_hardening_web_et_operationnel_claimlens` was finished via `logics-manager flow finish task` on 2026-07-30.
