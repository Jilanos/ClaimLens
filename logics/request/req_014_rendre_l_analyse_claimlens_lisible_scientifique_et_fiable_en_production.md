## req_014_rendre_l_analyse_claimlens_lisible_scientifique_et_fiable_en_production - Rendre l'analyse ClaimLens lisible, scientifique et fiable en production
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Analysis workspace and evidence quality
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Suivre une analyse en cours sans avoir à ouvrir des détails techniques, et obtenir l'état réellement actuel après rafraîchissement.
- Lire immédiatement un brief clair et mis en page dans l'interface, plutôt qu'un document Markdown brut.
- Comprendre ce que la recherche scientifique proche d'un claim indique, même lorsqu'elle ne permet pas de trancher strictement le verdict.
- Éviter les erreurs visibles de cooldown et de rate limit Semantic Scholar pendant une analyse normale.

# Context
- La clé Semantic Scholar de production est attendue et ne constitue pas un défaut à traiter dans ce périmètre.
- Le précédent espace d'analyse (req_011) est terminé ; cette demande affine ses décisions d'ergonomie et de fiabilité.
- Le produit reste en anglais côté interface, avec une expérience desktop prioritaire et responsive.

# Acceptance criteria
- AC1: L'en-tête de l'application affiche le numéro de version courant et inclut un accès Recent analyses dans la barre supérieure ; cet accès n'est plus présenté sous l'espace de travail.
- AC2: Pendant toute analyse non terminale, la chaîne complète des étapes métier est visible en permanence. Les données Step, Status, Details et Output sont placées dans un panneau dépliable ; Background actions et Cleaned transcript preview ne sont plus visibles dans l'interface.
- AC3: Après un rechargement de page, l'interface récupère et affiche sans état périmé le statut terminal, les étapes terminées et les résultats du dernier run concerné.
- AC4: Une analyse terminée affiche directement un brief HTML accessible et mis en page. Sur écran desktop, le brief exploite une colonne droite de la vue à deux colonnes ; le titre ClaimLens et le titre de la vidéo sont visuellement distincts, et les métadonnées techniques sont en bas du brief.
- AC5: Chaque checked claim présente d'abord un résumé compact et non décoratif des signaux supporting, contradicting et du verdict, suivi d'un texte LLM sourcé expliquant ce que la recherche voisine indique, y compris lorsque le verdict demeure unclear.
- AC6: Les appels Semantic Scholar respectent automatiquement retry-after et cooldown, avec attente et retry bornés. Les rate limits transitoires ne sont plus exposées comme Adapter errors dans un résultat normalement récupérable.
- AC7: Les tests couvrent les états de rafraîchissement, le rendu desktop et mobile, le brief HTML, le résumé scientifique des claims et le comportement de retry/cooldown des providers.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_018_espace_d_analyse_et_brief_scientifique_orientes_lecture`
- Architecture decision(s): (none yet)

# References
- Feedback utilisateur du 2026-08-02 sur l'espace d'analyse et Semantic Scholar
- logics/product/prod_015_focused_english_language_claimlens_analysis_workspace.md

# AI Context
- Summary: Rendre l'analyse ClaimLens lisible, scientifique et fiable en production
- Keywords: request-chain-scaffold, rendre l'analyse claimlens lisible, scientifique et fiable en production, development-ready
- Use when: You need to implement or review the scaffolded workflow for Rendre l'analyse ClaimLens lisible, scientifique et fiable en production.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_081_rendre_l_etat_de_l_analyse_continu_et_exact_apres_rafraichissement`
- `item_082_recomposer_la_navigation_et_le_brief_html_en_espace_desktop_a_deux_colonnes`
- `item_083_expliquer_les_claims_par_une_synthese_scientifique_sourcee`
- `item_084_respecter_les_cooldowns_semantic_scholar_avant_de_signaler_une_erreur_provider`
