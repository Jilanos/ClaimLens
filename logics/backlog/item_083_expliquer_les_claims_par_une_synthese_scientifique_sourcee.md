## item_083_expliquer_les_claims_par_une_synthese_scientifique_sourcee - Expliquer les claims par une synthèse scientifique sourcée
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Evidence interpretation
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Les listes Checked Claims sont trop denses et un verdict unclear ne renseigne pas l'utilisateur sur l'état de la science disponible.

# Scope
- In:
  - En-tête compact par claim avec signaux supporting, contradicting et verdict, avec icônes sobres accessibles.
  - Synthèse LLM fondée sur les articles récupérés, exprimant portée, convergence, limites et absence éventuelle de lien direct.
  - Sources et limites éditoriales conservées à côté de la synthèse.
- Out:
  - Diagnostic, conseil médical, changement du corpus externe disponible.

# Acceptance criteria
- AC1: Les signaux de chaque claim sont compréhensibles au premier coup d'œil sans dépendre d'émojis seuls.
- AC2: Un claim unclear avec des articles récupérés inclut une synthèse de ce que dit la recherche proche plutôt qu'un simple constat d'absence de verdict.
- AC3: La synthèse distingue explicitement le niveau de lien avec le claim et préserve les avertissements de prudence.
- AC4: Les tests couvrent supporting, contradicting, mixed et unclear avec preuves proches mais non décisives.

# AC Traceability
- request-AC5 -> This backlog slice. Proof: `test_every_claim_leads_with_a_compact_signal_line`, `test_an_unclear_claim_still_explains_what_the_nearby_research_shows` and `test_claim_signals_render_as_labelled_pills_without_emoji`.
- request-AC7 -> This backlog slice. Proof: supporting, contradicting, mixed and unclear are parametrised in `tests/test_verification.py`.
- request-AC1 -> This backlog slice. Evidence needed: L'en-tête de l'application affiche le numéro de version courant et inclut un accès Recent analyses dans la barre supérieure ; cet accès n'est plus présenté sous l'espace de travail.
- request-AC2 -> This backlog slice. Evidence needed: Pendant toute analyse non terminale, la chaîne complète des étapes métier est visible en permanence. Les données Step, Status, Details et Output sont placées dans un panneau dépliable ; Background actions et Cleaned transcript preview ne sont plus visibles dans l'interface.
- request-AC3 -> This backlog slice. Evidence needed: Après un rechargement de page, l'interface récupère et affiche sans état périmé le statut terminal, les étapes terminées et les résultats du dernier run concerné.
- request-AC4 -> This backlog slice. Evidence needed: Une analyse terminée affiche directement un brief HTML accessible et mis en page. Sur écran desktop, le brief exploite une colonne droite de la vue à deux colonnes ; le titre ClaimLens et le titre de la vidéo sont visuellement distincts, et les métadonnées techniques sont en bas du brief.
- request-AC6 -> This backlog slice. Evidence needed: Les appels Semantic Scholar respectent automatiquement retry-after et cooldown, avec attente et retry bornés. Les rate limits transitoires ne sont plus exposées comme Adapter errors dans un résultat normalement récupérable.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Delivery notes
- Each claim opens with a `Signals:` line rendered as labelled pills (supporting, contradicting, verdict); meaning never rides on a pictogram.
- `OpenAIClaimSynthesizer` in `src/claimlens/evidence.py` writes one paragraph from the retrieved records only, stored on `claims.evidence_synthesis`, and is wired into both the web job and the CLI.
- A claim with retrieved records but no verdict still gets the paragraph; when synthesis is unavailable the brief says so rather than implying one.

# Links
- Product brief(s): `prod_018_espace_d_analyse_et_brief_scientifique_orientes_lecture`
- Architecture decision(s): (none yet)
- Request: `req_014_rendre_l_analyse_claimlens_lisible_scientifique_et_fiable_en_production`
- Primary task(s): `task_018_orchestrer_la_lisibilite_et_la_fiabilite_du_brief_claimlens`

# AI Context
- Summary: Expliquer les claims par une synthèse scientifique sourcée
- Keywords: scaffolded-backlog, expliquer les claims par une synthèse scientifique sourcée, implementation-ready
- Use when: Implementing the scaffolded slice for Expliquer les claims par une synthèse scientifique sourcée.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_018_orchestrer_la_lisibilite_et_la_fiabilite_du_brief_claimlens`

# Notes
- Task `task_018_orchestrer_la_lisibilite_et_la_fiabilite_du_brief_claimlens` was finished via `logics-manager flow finish task` on 2026-08-02.
