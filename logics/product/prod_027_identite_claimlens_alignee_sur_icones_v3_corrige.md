## prod_027_identite_claimlens_alignee_sur_icones_v3_corrige - Identite ClaimLens alignee sur Icones V3 corrige
> Date: 2026-08-06
> Status: Proposed
> Related request: `req_024_remplacer_les_assets_claimlens_par_les_masters_icones_v3_corriges`
> Related backlog: `item_104_servir_les_masters_claimlens_en_png_dark_et_light`, `item_105_publier_la_version_1_8_4_apres_remplacement_des_assets`
> Related task: `task_028_remplacer_les_assets_claimlens_par_les_masters_icones_v3_corriges`
> Related architecture: (none yet)
> Reminder: Update status, linked refs, scope, decisions, success signals, and open questions when you edit this doc.

# Overview
Servir les masters approuves en PNG, avec la variante adaptee au theme du visiteur.

# Goals
- Une variante d'icone et d'embleme par theme.
- Des accesseurs et des types MIME coherents avec le format reellement servi.

# Non-goals
- Introduire un selecteur de theme manuel.

# Scope and guardrails
- In: scaffolded request, product, backlog, orchestration task, validation, and handoff context.
- Out: unrelated workflow docs and implementation of generated tasks.

# Key product decisions
- Use structured input as the source of truth for generated docs.
- Keep generated write paths local and repo-bounded.

# Success signals
- Generated docs pass lint and audit without broad manual rewrites.
- Context-pack output can be handed to an implementation agent directly.

# References
- Product back-reference: `req_024_remplacer_les_assets_claimlens_par_les_masters_icones_v3_corriges`
- Task back-reference: `task_028_remplacer_les_assets_claimlens_par_les_masters_icones_v3_corriges`
