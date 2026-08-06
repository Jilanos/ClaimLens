## item_104_servir_les_masters_claimlens_en_png_dark_et_light - Servir les masters ClaimLens en PNG dark et light
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: High
> Theme: Brand asset integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- L'icone et l'embleme sont des SVG issus d'un lot errone et ne s'adaptent pas au theme.

# Scope
- In:
  - `static/claimlens-icon-{light,dark}.png` depuis `claimlens/claimlens-icon-{light,dark}.png`
  - `static/claimlens-emblem-{light,dark}.png` depuis `claimlens/claimlens-emblem-{light,dark}.png`
  - `static/paulmondou-emblem.png` depuis `paulmondou/paulmondou-emblem.png`
  - Mise a jour de `assets.py`: accesseurs par variante et type MIME `image/png`
  - Mise a jour de `web.py`: routes statiques, `<link rel=icon>` avec media query et bascule de l'embleme
- Out:
  - Retirer les deux SVG avant d'avoir bascule toutes les references.
  - Modifier la palette de couleurs de l'application.
  - Ajouter un fond, une plaque de couleur ou un cartouche derriere un asset transparent.

# Acceptance criteria
- AC1: Les cinq PNG correspondent aux masters attendus.
- AC2: Plus aucune route ni accesseur ne declare `image/svg+xml` pour ces assets.
- AC3: La bonne variante s'affiche en theme clair comme en theme sombre.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Les cinq PNG correspondent aux masters attendus.
- request-AC2 -> This backlog slice. Proof: AC2: Plus aucune route ni accesseur ne declare `image/svg+xml` pour ces assets.
- request-AC3 -> This backlog slice. Proof: AC3: La bonne variante s'affiche en theme clair comme en theme sombre.
- request-AC4 -> This backlog slice. Proof: AC3: La bonne variante s'affiche en theme clair comme en theme sombre.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_027_identite_claimlens_alignee_sur_icones_v3_corrige`
- Architecture decision(s): (none yet)
- Request: `req_024_remplacer_les_assets_claimlens_par_les_masters_icones_v3_corriges`
- Primary task(s): `task_028_remplacer_les_assets_claimlens_par_les_masters_icones_v3_corriges`

# AI Context
- Summary: Servir les masters ClaimLens en PNG dark et light
- Keywords: scaffolded-backlog, servir les masters claimlens en png dark et light, implementation-ready
- Use when: Implementing the scaffolded slice for Servir les masters ClaimLens en PNG dark et light.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.
