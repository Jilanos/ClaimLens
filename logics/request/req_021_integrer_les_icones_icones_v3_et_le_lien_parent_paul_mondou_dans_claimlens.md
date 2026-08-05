## req_021_integrer_les_icones_icones_v3_et_le_lien_parent_paul_mondou_dans_claimlens - Integrer les icones Icones V3 et le lien parent Paul Mondou dans ClaimLens
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: Branding
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Utiliser les assets ClaimLens du corpus Icones V3 pour l'icone d'onglet et l'embleme.
- Utiliser les assets Paul Mondou du corpus Icones V3 pour le lien parent.

# Context
- Le dossier source est le corpus local Icones V3 fourni par l'operateur; les chemins references ici sont internes a ce corpus pour respecter les regles Logics.
- Assets attendus: claimlens/claimlens-icon-light.svg, claimlens/claimlens-icon-dark.svg, claimlens/claimlens-emblem-light.svg, claimlens/claimlens-emblem-dark.svg, puis les assets paulmondou pour le lien parent.
- ClaimLens a deja une demande liee au remplacement de l'avatar par un lien Paul Mondou; ce corpus precise la variante Icones V3 et les surfaces favicon/embleme.

# Acceptance criteria
- AC1: L'icone d'onglet ClaimLens utilise l'asset ClaimLens Icones V3.
- AC2: L'embleme ClaimLens visible dans l'interface utilise l'asset ClaimLens Icones V3.
- AC3: Le lien vers Paul Mondou utilise l'identite Paul Mondou Icones V3 et conserve sa destination parent.
- AC4: Les assets necessaires sont integres au repo ClaimLens et ne dependent pas du dossier local au runtime.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_025_identite_claimlens_alignee_sur_icones_v3`
- Architecture decision(s): (none yet)

# References
- Corpus externe Icones V3/claimlens/
- Corpus externe Icones V3/paulmondou/
- logics/request/req_020_remplacer_l_avatar_de_compte_par_le_lien_paul_mondou.md
- logics/scaffold/parent-site-emblem-navigation.json

# AI Context
- Summary: Integrer les icones Icones V3 et le lien parent Paul Mondou dans ClaimLens
- Keywords: request-chain-scaffold, integrer les icones icones v3 et le lien parent paul mondou dans claimlens, development-ready
- Use when: You need to implement or review the scaffolded workflow for Integrer les icones Icones V3 et le lien parent Paul Mondou dans ClaimLens.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_100_remplacer_favicon_et_embleme_claimlens_par_icones_v3`
- `item_101_finaliser_le_lien_paul_mondou_avec_l_identite_icones_v3`
