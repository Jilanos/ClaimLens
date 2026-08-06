## req_022_publier_les_derniers_assets_icones_v3_claimlens - Publier les derniers assets Icones V3 ClaimLens
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: Low
> Theme: UI
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Publier les derniers masters SVG ClaimLens pour l'icône d'onglet et l'emblème applicatif.

# Context
- Les sources sont `claimlens-icon-light.svg` et `claimlens-emblem-light.svg` du corpus Icones V3.
- Elles sont servies en same-origin par les routes statiques existantes.

# Acceptance criteria
- AC1: L'icône d'onglet sert le dernier SVG Icones V3.
- AC2: L'en-tête sert le dernier emblème SVG Icones V3.
- AC3: Les routes `/static/claimlens-icon.svg` et `/static/claimlens-emblem.svg` restent stables.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# References
- `logics_manager/flow.py`
- `logics_manager/assist.py`
- `tests/python/test_logics_manager_cli.py`

# AI Context
- Summary: Draft a bounded request for publier les derniers assets icones v3 claimlens.
- Keywords: request-draft, logics-manager, python runtime, bundled CLI
- Use when: You need a new bounded request doc for the Logics workflow.
- Skip when: The work already has an existing request or should go straight to a backlog slice.

# Backlog
- none
- `item_102_publier_les_derniers_assets_icones_v3_claimlens`
