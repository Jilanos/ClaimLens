# Audit & Revue — ClaimLens

_Date : 2026-07-23 — Portée : `main` @ `feb6c4e` (fin Milestone 2 / skeleton local)_

## Résumé

Le projet est un skeleton propre et cohérent pour un pipeline CLI Python (YouTube → briefs sourcés).
La base est saine : typage strict, dataclasses immuables, schéma SQLite bien pensé, tests verts et
linting propre. Aucun secret n'est commité. Le code est **prêt à être commité et poussé**.

| Contrôle            | Résultat                     |
| ------------------- | ---------------------------- |
| Tests (`pytest`)    | ✅ 7 passés                   |
| Lint (`ruff`)       | ✅ All checks passed          |
| Secrets commités    | ✅ Aucun (`.env` ignoré)      |
| Working tree        | ✅ Propre avant cet audit     |
| Structure / docs    | ✅ README + ROADMAP cohérents |

## Points forts

- **Config typée et immuable** : `dataclass(frozen=True)` pour toute la configuration, séparation
  claire TOML + variables d'environnement, valeurs par défaut sensées.
- **Schéma SQLite solide** : clés étrangères avec `ON DELETE CASCADE`, index sur les colonnes de
  requête, contrainte `UNIQUE` sur `transcripts(video_id, source)`, table `schema_metadata` versionnée.
- **CLI extensible** : commandes placeholder stables pour les milestones à venir, messages explicites.
- **Hygiène repo** : `.gitignore` couvre `.env`, `data/`, `outputs/`, caches et bases `*.sqlite3` ;
  `.env.example` fourni ; version alignée entre `pyproject.toml` et `__init__.py` (0.1.0).

## Constats

### 🟡 Mineur

1. **Connexions SQLite non fermées** — `src/claimlens/db.py:150`, `db.py:156`
   `with sqlite3.connect(...) as connection:` gère la transaction (commit/rollback) mais **ne ferme
   pas** la connexion. Sur un usage répété (futurs milestones), fuite de descripteurs.
   _Correctif :_ envelopper avec `contextlib.closing(connect(path))` ou fermer explicitement.

2. **Résolution de config dépendante du CWD** — `src/claimlens/config.py:61-62`
   `repo_root = Path.cwd()` et le chemin par défaut `config/claimlens.example.toml` sont relatifs au
   répertoire courant. Un `claimlens` installé et lancé ailleurs ne trouvera pas la config par défaut.
   _Correctif :_ résoudre relativement au package ou documenter que la CLI doit tourner à la racine.

3. **Override d'environnement incomplet** — `src/claimlens/config.py:68-71`
   Seul `CLAIMLENS_DB` surcharge un chemin ; `outputs`/`transcripts`/`briefs` ne sont pas surchargeables.
   Acceptable pour le MVP, mais incohérent — à uniformiser si besoin plus tard.

### 🔵 Info / futur

4. **Pas de vraie migration de schéma** — `db.py:8`, `db.py:131`
   `SCHEMA_VERSION` existe mais `init_db` ne fait que `CREATE ... IF NOT EXISTS` et réécrit toujours
   `'1'`. Un futur passage à `version 2` n'aura aucun chemin de migration. À prévoir avant tout
   changement de schéma en production.

5. **Pas de CI** — aucun workflow (GitHub Actions) n'exécute `ruff`/`pytest` automatiquement.
   `.mypy_cache/` est ignoré mais `mypy` n'est ni déclaré ni configuré.

6. **Validation de config non défensive** — `config.py:82-83`
   `int(...)` sur des valeurs TOML lèvera une exception peu explicite si le fichier est malformé.
   Non bloquant pour le MVP.

## Recommandation

**Feu vert pour commit + push.** Les constats mineurs (1–3) sont des améliorations à planifier via le
backlog Logics, pas des bloquants. Suggestion d'ordre de priorité : (1) fermeture des connexions,
(5) CI minimale, puis (4) migrations avant tout changement de schéma.
