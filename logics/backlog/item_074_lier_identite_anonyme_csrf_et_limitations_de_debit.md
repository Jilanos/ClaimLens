## item_074_lier_identite_anonyme_csrf_et_limitations_de_debit - Lier identite anonyme, CSRF et limitations de debit
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 95
> Confidence: 95
> Progress: 100%
> Complexity: High
> Theme: security
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Un client anonyme peut renouveler son cookie et contourner le rate limit.
- Le CSRF guest est partage globalement.

# Scope
- In:
  - Cookie visiteur emis avant les actions couteuses
  - CSRF par visiteur
  - Limitation proxy/IP adaptee
  - Tests d'integration d'abus
- Out:
  - Changement de fournisseur d'identite

# Acceptance criteria
- Un renouvellement de cookie ne contourne plus la limite.
- Les tests couvrent CSRF et rate limit anonymes.

# AC Traceability
- request-Les controles de securite sont verifies par tests automatises. -> This backlog slice. Proof: Un renouvellement de cookie ne contourne plus la limite.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_016_securisation_et_fiabilisation_de_claimlens`
- Architecture decision(s): (none yet)
- Request: `req_012_remedier_aux_constats_de_l_audit_technique_2026_07_25`
- Primary task(s): `task_013_orchestrer_la_remediation_de_l_audit_claimlens`

# AI Context
- Summary: Lier identite anonyme, CSRF et limitations de debit
- Keywords: scaffolded-backlog, lier identite anonyme, csrf et limitations de debit, implementation-ready
- Use when: Implementing the scaffolded slice for Lier identite anonyme, CSRF et limitations de debit.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: high
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_014_lier_identite_anonyme_csrf_et_limitations_de_debit`

# Notes
- Task `task_014_lier_identite_anonyme_csrf_et_limitations_de_debit` was finished via `logics-manager flow finish task` on 2026-07-25.
- Task `task_013_orchestrer_la_remediation_de_l_audit_claimlens` was finished via `logics-manager flow finish task` on 2026-07-25.
