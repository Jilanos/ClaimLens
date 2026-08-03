## req_016_finaliser_l_espace_d_analyse_claimlens_et_ses_livrables_lisibles - Finaliser l'espace d'analyse ClaimLens et ses livrables lisibles
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: analysis-workspace
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Rendre l'état de l'analyse lisible sans recharger manuellement la page.
- Agrandir de 80 % l'icône de marque dans le bandeau supérieur.
- Remplacer l'affichage d'un chemin interne de transcript par un accès sûr et utilisable au transcript nettoyé.
- Permettre de fermer l'espace d'analyse et le résultat terminé, puis de le rouvrir depuis l'historique.
- Fournir un brief lisible directement dans un navigateur et exportable dans un format non-Markdown.
- Supprimer le choix de langue du rapport de l'interface et du flux de création.

# Context
- La page Process utilise actuellement un script de polling inline, bloqué par la CSP de production script-src 'self'.
- Le navigateur ne peut pas ouvrir de manière sûre le dossier /data/outputs/transcripts du serveur ; l'accès doit être un endpoint authentifié de lecture ou de téléchargement.
- Les cinq étapes sont captions, clean_transcript, analysis, brief et source_verification.
- Les runs sont déjà conservés dans SQLite et la page History les rend accessibles.

# Acceptance criteria
- AC1: Une analyse active actualise les cinq étapes, les erreurs et le brief sans rechargement manuel sous la CSP de production stricte.
- AC2: L'icône ClaimLens du bandeau supérieur est 80 % plus grande sans casser l'alignement ou la navigation mobile.
- AC3: Le transcript nettoyé expose un lien autorisé de lecture ou téléchargement, sans afficher ni tenter d'ouvrir le chemin local du serveur.
- AC4: Une analyse terminée peut être masquée depuis l'espace de travail, reste disponible dans Recent analyses et peut être rouverte avec son résultat.
- AC5: Un brief terminé est lisible dans le navigateur et téléchargeable en HTML autonome, sans nécessiter d'éditeur Markdown.
- AC6: Le formulaire de création ne contient plus Report language et les analyses nouvelles utilisent la langue de rapport configurée par défaut.
- AC7: Des tests navigateur ou d'intégration vérifient le rafraîchissement réel sous CSP, les contrôles de visibilité, les autorisations d'accès aux fichiers et les nouveaux exports.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_020_espace_d_analyse_termine_reouvrable_et_lisible`
- Architecture decision(s): (none yet)

# References
- src/claimlens/web.py
- tests/test_analysis_briefs_web.py
- docs/deployment-paulmondou-infra.md
- /home/paul/dev/paulmondou-infra/Caddyfile

# AI Context
- Summary: Finaliser l'espace d'analyse ClaimLens et ses livrables lisibles
- Keywords: request-chain-scaffold, finaliser l'espace d'analyse claimlens et ses livrables lisibles, development-ready
- Use when: You need to implement or review the scaffolded workflow for Finaliser l'espace d'analyse ClaimLens et ses livrables lisibles.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_087_rendre_le_suivi_d_analyse_compatible_csp_et_observable`
- `item_088_simplifier_le_bandeau_et_le_lancement_d_analyse`
- `item_089_fournir_les_transcripts_et_briefs_comme_livrables_lisibles`
- `item_090_masquer_et_reouvrir_les_analyses_terminees`
