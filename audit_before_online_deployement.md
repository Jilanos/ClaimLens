# Audit ClaimLens — Avant mise en ligne

> Date : 2026-07-24
> Périmètre : audit fonctionnel, UI/UX/design, et technique (DB, sécurité, robustesse)
> Contexte de déploiement cible fourni : hébergement sur VPS perso, accès HTTPS sécurisé + login,
> **aucune clé API disponible côté serveur**, grosse refonte visuelle à venir, besoin d'un
> **affichage du rapport final + téléchargement**.

État actuel du code : `ruff check` OK, `pytest` 33/33 OK. Le socle est propre et testé.
L'audit ci-dessous porte sur l'écart entre cet état « MVP local-first » et une mise en ligne réelle.

---

## 0. Synthèse & verdict

ClaimLens est aujourd'hui un **MVP local mono-utilisateur** bien structuré (séparation claire
CLI / pipeline / DB / web, boundaries mockables, tests déterministes). **Il n'est PAS prêt pour
une mise en ligne en l'état.** Le serveur `web.py` est un `http.server` de démo : **aucune
authentification, aucun TLS, aucune protection CSRF, aucune limite de débit, aucune limite de
taille de requête**. Ce sont des bloquants absolus dès que le port est joignable par un tiers.

Deux points structurants à trancher **avant** la refonte visuelle :

1. **« Pas de clé API dispo » entre en conflit frontal avec la valeur du produit.** Le cœur de
   l'app (analyse LLM) *exige* une clé OpenAI. Sans clé serveur, chaque visiteur devra coller
   sa propre clé OpenAI dans votre site — friction énorme + problème de confiance. Voir §1.1.
2. **La récupération de sous-titres depuis un VPS échoue très souvent** (YouTube bloque les IP
   datacenter). C'est un risque de fiabilité majeur, spécifique à l'hébergement. Voir §1.4.

Priorité recommandée : **Sécurité (§3) → Modèle clé API/coûts (§1.1) → Fonctionnalité rapport
+ download (§2.2) → Robustesse DB/serveur (§3.6-3.8) → Refonte UI (§2)**.

Légende sévérité : 🔴 Bloquant mise en ligne · 🟠 Majeur · 🟡 Mineur / amélioration

---

## 1. Axe fonctionnel (intérêt de l'app, biais, manque de données, limites)

### 1.1 🔴 Le modèle « pas de clé API » casse le cœur du produit
- L'étape d'analyse (`analysis.py`) est obligatoire pour produire un brief et **requiert
  `OPENAI_API_KEY`**. Sans clé côté serveur, il ne reste que deux options, toutes deux à décider :
  - **BYO-key** : l'utilisateur colle sa clé OpenAI dans le formulaire web (`web.py:253`). Coller
    une clé secrète dans le site d'un tiers est un anti-pattern de confiance, et la clé transite
    dans le corps POST (loggable par un reverse-proxy mal configuré).
  - **Clé serveur avec quotas** : nécessite auth + rate limiting + suivi de coûts par utilisateur,
    sinon la facture OpenAI est ouverte à quiconque a un login.
- **Décision produit à prendre explicitement.** Recommandation : clé serveur + login + quota par
  compte, ou basculer vers un fournisseur/route où *vous* maîtrisez la clé. Documentez le choix.

### 1.2 🟠 Vérification des sources scientifiquement fragile (risque de biais/désinformation)
- `verification.py:_snippet_polarity` détermine « supports / contradicts » par **simple présence
  de mots-clés** (`"increased risk"` → supports, `"reduced risk"` → contradicts). C'est faux dans
  de nombreux cas : « reduced risk » *soutient* souvent une allégation. Sur des sujets santé, cela
  peut produire des verdicts trompeurs affichés comme « supported/contradicted ».
- Pour PubMed, `abstract_or_snippet = title` (`verification.py:126`) : **aucun résumé réel n'est
  récupéré**, la « preuve » se réduit à un recoupement de mots du *titre*.
- Les scores de confiance (`0.55`, `0.65`, `0.35`) sont **codés en dur** : fausse précision.
- Point positif : `HUMAN_REVIEW_DISCLAIMER` est présent et injecté dans les briefs. À conserver et
  rendre très visible dans l'UI refondue.
- Reco : soit fiabiliser (récupérer les vrais abstracts, remplacer l'heuristique par un jugement
  LLM ancré sur l'abstract), soit **rétrograder le vocabulaire** en « éléments à charge / à
  décharge trouvés » sans verdict tranché tant que la méthode reste heuristique.

### 1.3 🟠 Biais et non-déterminisme de l'analyse LLM
- Passe unique `gpt-4o-mini`, pas de `temperature`, pas de `seed`, pas de garde anti-hallucination :
  rien ne garantit que les « notable_claims » extraits figurent réellement dans le transcript.
- Pas de plafond de longueur du transcript envoyé (`analysis.py:104`) : coût token non borné +
  risque de dépassement de contexte sur longues vidéos.
- Reco : borner/chunker le transcript, fixer `temperature=0`, et faire re-citer chaque claim avec
  un extrait du transcript pour l'ancrage.

### 1.4 🔴 Fiabilité de l'extraction des sous-titres en hébergement
- `youtube.py:fetch_transcript` utilise `youtube-transcript-api`. **Depuis une IP de VPS/datacenter,
  YouTube bloque fréquemment ces requêtes** (« no transcript / IP blocked »), même quand les
  sous-titres existent. Ce qui marche en local peut échouer systématiquement en ligne.
- Langue forcée à `["en"]` (`youtube.py:61`) : les vidéos non-anglaises échouent ou renvoient une
  mauvaise piste.
- Pas de fallback audio (choix MVP assumé) → beaucoup de vidéos sans sous-titres = arrêt sec.
- Reco : tester tôt depuis le VPS cible ; prévoir proxy/rotation ou clé d'un service tiers ;
  rendre la langue configurable ; message d'erreur explicite déjà présent (bien).

### 1.5 🟡 Scraping de pages chaîne YouTube fragile et hors périmètre MVP
- `latest_channel_videos` / `_extract_json_object` parsent `ytInitialData` du HTML : casse à chaque
  changement de balisage YouTube, et zone grise CGU. Non utilisé par le flux MVP mono-vidéo mais
  présent et exposé via `transcribe`. À isoler ou retirer avant mise en ligne.

### 1.6 🟡 Manque de données / métadonnées
- Le titre de la vidéo n'est pas récupéré dans le flux `run-video` (`pipeline.py:69` met `title =
  video_id`). Le brief affiche un ID au lieu du titre → rapport moins lisible.
- Aucune date, auteur, durée réels dans le brief mono-vidéo.

---

## 2. Axe UI / UX / Design

### 2.1 🟠 Rendu et expérience actuels très rudimentaires
- HTML rendu côté serveur avec CSS inline (`web.py:103-123`), **rechargement complet à chaque
  action**, zéro JavaScript.
- **Aucun retour pendant les opérations longues** : l'analyse peut prendre ~1 min (timeout 60 s),
  l'utilisateur voit un POST « qui rame » sans spinner ni progression.
- Thème clair uniquement, responsive minimal (juste `max-width`), champs sans `<label>` (seulement
  des `placeholder` → accessibilité faible), contraste à revérifier.
- La refonte visuelle prévue devrait s'appuyer sur : états de chargement, statuts de steps en
  quasi-temps-réel (polling ou SSE), thème clair/sombre, labels accessibles.

### 2.2 🔴 Affichage du rapport final + téléchargement : ABSENT (demande explicite)
- Le brief est écrit sur disque (`outputs/briefs/<id>.md`) et l'UI **n'affiche que le chemin en
  texte brut** (`web.py:278`) — non cliquable, non servi, non téléchargeable.
- Il n'existe **aucune route** pour visualiser ou télécharger le rapport depuis le web.
- À construire : une route `GET /brief?...` qui (a) rend le Markdown en HTML dans la page, et (b)
  propose un téléchargement (`.md`, et idéalement `.pdf`/`.html`).
- ⚠️ **Sécurité** : servir des fichiers impose une protection stricte contre le *path traversal*
  (ne jamais concaténer un paramètre utilisateur au chemin ; résoudre par `video_id` validé et
  vérifier que le chemin résolu reste dans `outputs/briefs`).

### 2.3 🟡 Détails UX
- Le `<select>` liste tous les runs sans pagination (`web.py:90`).
- Les erreurs s'affichent en notice rouge avec le **texte brut de l'exception** (`web.py:47`) :
  peut fuiter des chemins internes ; à remplacer par des messages maîtrisés.
- Pas de lien direct vers la vidéo source ni d'aperçu du transcript nettoyé dans l'UI.

---

## 3. Axe technique (sécurité, DB, casses potentielles)

### 3.1 🔴 Aucune authentification ni TLS dans le serveur applicatif
- `serve_process_page` (`web.py:23`) démarre un `ThreadingHTTPServer` **sans login, sans HTTPS,
  sans session**. Toute personne joignant le port peut créer des runs et déclencher des appels
  OpenAI payants.
- Vous prévoyez « HTTPS + login » : à faire via un **reverse-proxy (nginx/Caddy/Traefik)** en
  frontal (TLS + auth). Mais l'app doit **écouter uniquement sur `127.0.0.1`** et ne jamais être
  bindée directement sur `0.0.0.0`. Vérifier `CLAIMLENS_HOST` en prod.

### 3.2 🔴 Aucune protection CSRF
- Toutes les mutations passent par des `<form method="post">` sans jeton CSRF (`web.py:35`). Une
  fois derrière un login, un site tiers pourrait déclencher des actions (création de run, analyse
  payante) au nom de l'utilisateur connecté. Ajouter un token CSRF par session + `SameSite`.

### 3.3 🔴 Pas de limite de taille de requête (DoS mémoire)
- `length = int(self.headers.get("Content-Length", "0"))` puis `self.rfile.read(length)`
  (`web.py:36-37`) : un `Content-Length` énorme fait lire tout le corps en mémoire ; un
  `Content-Length` non numérique lève une `ValueError` non gérée → 500. Plafonner la taille et
  valider l'en-tête.

### 3.4 🟠 Pas de rate limiting / contrôle d'abus
- Créer un run déclenche un fetch YouTube sortant + un appel OpenAI payant. Sans limitation, un
  utilisateur (même authentifié) peut faire exploser les coûts ou faire blacklister l'IP du VPS
  par YouTube. À traiter au niveau proxy et/ou applicatif (quota par compte).

### 3.5 🟠 Exécution synchrone bloquante des tâches longues
- Analyse et vérification tournent **dans le thread de la requête HTTP** (`web.py:_run_action`),
  jusqu'à 60 s (OpenAI) + timeouts des adapters. Requêtes concurrentes → threads bloqués, aucune
  reprise, aucun statut « en cours » persistant fiable. Pour le web, passer à un **modèle de job
  asynchrone** (file de tâches + polling de statut), ce qui règle aussi l'UX §2.1.

### 3.6 🟠 SQLite non configuré pour la concurrence
- `db.connect` (`db.py:224`) n'active **ni WAL ni `busy_timeout`**. Sous accès web concurrents
  (`ThreadingHTTPServer` + écritures multiples), erreurs « database is locked » probables.
- Reco minimale : `PRAGMA journal_mode=WAL;` et `PRAGMA busy_timeout=5000;` à la connexion.
- Positif : chaque opération ouvre/ferme proprement sa connexion (`closing`), et `foreign_keys=ON`.

### 3.7 🟠 Robustesse des appels réseau (analysis.py / verification.py)
- `analysis.py:70` ne gère que `HTTPError` : un **timeout / erreur réseau (`URLError`,
  `socket.timeout`) n'est pas capturé** → exception brute remonte à l'utilisateur.
- `analysis.py:75` : `body["choices"][0]["message"]["content"]` sans garde — si OpenAI renvoie une
  forme d'erreur ou `choices` vide → `KeyError`/`IndexError` non explicite.
- `verification.py:_search_all` (`:329`) **avale toutes les exceptions adapter silencieusement**
  (`except Exception: continue`) : impossible de distinguer « aucune source » d'un « adapter en
  erreur ». Ajouter du logging.

### 3.8 🟠 Fiabilité de la config en production
- `load_config` fixe `repo_root = Path.cwd()` et cherche `config/claimlens.example.toml` **relatif
  au cwd** (`config.py:68-69`). Sous systemd/reverse-proxy, le cwd n'est pas garanti → config
  silencieusement ignorée (valeurs par défaut). Utiliser un chemin absolu / variable d'env dédiée.
- Bind par défaut `127.0.0.1:8765` : bon défaut, mais s'assurer qu'aucun override ne le passe en
  public (cf §3.1).

### 3.9 🟡 Migrations de schéma ad hoc
- `SCHEMA_VERSION = 3` mais `_migrate_schema` (`db.py:242`) applique des `ADD COLUMN` **sans lire
  la version stockée** ni gérer de destructif. Idempotent aujourd'hui, mais le README exige « un
  chemin de migration testé avant la v4 » : à formaliser (table de versions + steps versionnés)
  avant toute évolution de schéma en prod, sinon risque de casse sur base existante.

### 3.10 🟡 Effets de bord d'idempotence
- `upsert_analysis` (`db.py:580`) supprime les claims `not_checked` puis **crée un nouveau
  `summary` à chaque analyse** (pas d'upsert) : accumulation non bornée de summaries/claims au fil
  des ré-analyses. Sans impact fonctionnel immédiat (on prend `latest_analysis`), mais la base
  grossit. Deux onglets lançant l'analyse en parallèle → double appel OpenAI (pas d'idempotence
  sur le statut de step).

### 3.11 🟡 Divers
- Fuite de détails d'exception vers le client (`web.py:47`) — cf §2.3.
- Aucun logging structuré / journal d'accès (`log_message` est neutralisé, `web.py:55`) : pas
  d'audit ni de diagnostic en prod.
- CI teste sur Python 3.11 ; le venv local est en 3.14 — aligner les versions testées.
- Positif sécurité : la clé API n'est **pas** persistée en DB/briefs/transcripts (vérifié), le
  `.gitignore` exclut bien `data/`, `outputs/`, `.env`, `*.sqlite3` ; aucun secret ni base n'est
  suivi par git (`data/jackhwoods-test.sqlite3` est untracked). SQL entièrement paramétré (pas
  d'injection). HTML échappé via `html.escape` (pas de XSS évident).

---

## 4. Plan d'action priorisé (avant / pendant / après refonte)

**Bloquants à traiter AVANT toute exposition réseau :**
1. Trancher le modèle de clé OpenAI (serveur+quota vs BYO-key) — §1.1.
2. Reverse-proxy TLS + login ; app bindée sur `127.0.0.1` uniquement — §3.1.
3. CSRF + limite de taille de requête + validation `Content-Length` — §3.2, §3.3.
4. Valider tôt l'extraction de sous-titres **depuis le VPS cible** (risque blocage IP) — §1.4.

**À faire avec la refonte (fonctionnalités demandées) :**
5. Route d'affichage HTML du rapport + téléchargement (`.md`/`.pdf`), avec anti-path-traversal — §2.2.
6. Modèle de job asynchrone + statuts en temps réel + états de chargement — §3.5, §2.1.
7. Rate limiting / quota par compte + suivi de coûts OpenAI — §3.4.

**Robustesse / qualité :**
8. SQLite WAL + `busy_timeout` — §3.6.
9. Capturer `URLError`/timeouts et réponses OpenAI malformées ; logger les erreurs d'adapters — §3.7.
10. Config par chemin absolu / env dédiée — §3.8.
11. Borner la longueur du transcript, `temperature=0`, ancrage des claims — §1.3.

**Qualité scientifique / éthique :**
12. Fiabiliser la vérification de sources ou rétrograder le vocabulaire des verdicts ; garder le
    disclaimer très visible — §1.2.
13. Récupérer titre/métadonnées réels de la vidéo pour des rapports lisibles — §1.6.
14. Isoler ou retirer le scraping de chaînes hors MVP — §1.5.

**Formaliser :**
15. Politique de migration de schéma testée avant v4 — §3.9.
16. Logging structuré + journal d'accès + alignement versions CI/venv — §3.11.
