## item_099_remplacer_l_avatar_de_navigation_par_l_embleme_paul_mondou - Remplacer l'avatar de navigation par l'emblème Paul Mondou
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Low
> Theme: Navigation et identité parent
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-08-04

# Problem
- L'initiale de l'e-mail n'offre aucune action de compte et encombre l'extrémité de la navigation.
- ClaimLens ne propose pas de chemin visuel vers son site parent.

# Scope
- In:
  - Ajouter l'emblème transparent fourni sous un chemin d'asset pérenne et adapté au packaging du projet.
  - Modifier _nav et les styles associés pour substituer le lien parent à .avatar, sur les vues authentifiées puis, par décision opérateur du 2026-08-04, aussi sur les vues invité.
  - Rendre le lien sûr, accessible et responsive; couvrir ce contrat par les tests web existants.
- Out:
  - Modification de l'e-mail affiché, du bouton Logout, de Login, d'API keys ou de l'autorisation.
  - Changement du logo ClaimLens, favicon ou de la navigation centrale.
  - Chargement d'assets depuis le chemin source hors dépôt en production.

# Acceptance criteria
- AC1: _nav ne construit plus le span .avatar, ni l'initiale calculée à partir de context.email.
- AC2: Un unique lien d'emblème présent dans la zone .navuser, en session comme en invité, utilise href="https://paulmondou.fr" et l'asset versionné dérivé de paulmondou-emblem-dark-transparent.png.
- AC3: Le lien porte aria-label="Visit paulmondou.fr" et navigue dans l'onglet courant, sans target ni rel (décision opérateur du 2026-08-04, v1.8.1: quitter la page plutôt qu'ouvrir un onglet, ce qui rend noopener sans objet); son focus visible respecte le style de navigation.
- AC4: Le style réserve une boîte carrée stable d'environ 30 px, conserve l'aspect ratio de l'emblème et reste utilisable sous le breakpoint mobile existant.
- AC5: La suite de tests vérifie le HTML connecté et invité, les attributs de sécurité/accessibilité du lien et l'absence de avatar/initiale.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: _nav ne construit plus le span .avatar, ni l'initiale calculée à partir de context.email.
- request-AC2 -> This backlog slice. Proof: AC2: Un unique lien d'emblème présent dans la zone .navuser, en session comme en invité, utilise href="https://paulmondou.fr" et l'asset versionné dérivé de paulmondou-emblem-dark-transparent.png.
- request-AC3 -> This backlog slice. Proof: AC3: Le lien porte aria-label="Visit paulmondou.fr" et navigue dans l'onglet courant, sans target ni rel (décision opérateur du 2026-08-04, v1.8.1: quitter la page plutôt qu'ouvrir un onglet, ce qui rend noopener sans objet); son focus visible respecte le style de navigation.
- request-AC4 -> This backlog slice. Proof: AC4: Le style réserve une boîte carrée stable d'environ 30 px, conserve l'aspect ratio de l'emblème et reste utilisable sous le breakpoint mobile existant.
- request-AC5 -> This backlog slice. Proof: AC5: La suite de tests vérifie le HTML connecté et invité, les attributs de sécurité/accessibilité du lien et l'absence de avatar/initiale.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_024_navigation_claimlens_reliee_au_site_parent`
- Architecture decision(s): (none yet)
- Request: `req_020_remplacer_l_avatar_de_compte_par_le_lien_paul_mondou`
- Primary task(s): `task_024_livrer_le_lien_parent_paul_mondou_dans_la_navigation_claimlens`

# AI Context
- Summary: Remplacer l'avatar de navigation par l'emblème Paul Mondou
- Keywords: scaffolded-backlog, remplacer l'avatar de navigation par l'emblème paul mondou, implementation-ready
- Use when: Implementing the scaffolded slice for Remplacer l'avatar de navigation par l'emblème Paul Mondou.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_024_livrer_le_lien_parent_paul_mondou_dans_la_navigation_claimlens`

# Notes
- Task `task_024_livrer_le_lien_parent_paul_mondou_dans_la_navigation_claimlens` was finished via `logics-manager flow finish task` on 2026-08-04.
