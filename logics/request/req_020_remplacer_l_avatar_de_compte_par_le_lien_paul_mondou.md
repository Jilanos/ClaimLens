## req_020_remplacer_l_avatar_de_compte_par_le_lien_paul_mondou - Remplacer l'avatar de compte par le lien Paul Mondou
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: Low
> Theme: Navigation et identité parent
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.
> Indicators reviewed: 2026-08-04

# Needs
- Retirer de l'extrémité droite de la barre supérieure la pastille qui affiche l'initiale de l'adresse e-mail.
- Donner un accès explicite et discret au site parent paulmondou.fr au même emplacement, par son emblème.

# Context
- La pastille actuelle est le span .avatar construit par _nav pour une session authentifiée; l'e-mail, le bouton Logout et les liens d'application doivent rester disponibles.
- La source approuvée de l'emblème est paulmondou-emblem-dark-transparent.png (PNG RGBA, 311 x 311) dans le répertoire personnel indiqué.
- ClaimLens est servi derrière paulmondou.fr; l'asset doit donc être embarqué ou servi par ClaimLens sans dépendre d'un chemin WSL/Windows ni d'un proxy externe au runtime.

# Acceptance criteria
- AC1: Une session authentifiée ne rend plus la pastille circulaire ni aucune initiale issue de l'adresse e-mail dans la barre supérieure.
- AC2: La partie droite de la barre supérieure affiche un emblème Paul Mondou cliquable qui cible exactement https://paulmondou.fr.
- AC3: Le lien parent est accessible au clavier, possède un nom accessible explicite, navigue dans l'onglet courant vers le site parent (révision opérateur du 2026-08-04, v1.8.1: le nouvel onglet initialement demandé est abandonné, donc rel="noopener noreferrer" devient sans objet), et n'altère ni Logout ni les liens existants.
- AC4: L'emblème est copié dans un asset versionné du projet, conserve sa transparence, est net et proportionné dans l'en-tête desktop et mobile, sans provoquer de débordement ou de saut de mise en page.
- AC5: Des tests de rendu couvrent les états connecté et invité, l'absence de l'avatar et les attributs exacts du lien parent.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_024_navigation_claimlens_reliee_au_site_parent`
- Architecture decision(s): (none yet)

# References
- src/claimlens/web.py (_nav et styles .navuser/.avatar)
- /home/paul/dev/WORK/perso/Icones/paulmondou/paulmondou-emblem-dark-transparent.png

# AI Context
- Summary: Remplacer l'avatar de compte par le lien Paul Mondou
- Keywords: request-chain-scaffold, remplacer l'avatar de compte par le lien paul mondou, development-ready
- Use when: You need to implement or review the scaffolded workflow for Remplacer l'avatar de compte par le lien Paul Mondou.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_099_remplacer_l_avatar_de_navigation_par_l_embleme_paul_mondou`
