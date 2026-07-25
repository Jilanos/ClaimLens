# Audit technique - ClaimLens

Date : 2026-07-25  
Revision auditee : `cde218b` (`main`)  
Perimetre : pipeline, analyse LLM, verification scientifique, serveur web, authentification,
stockage de secrets, SQLite, tests, conteneur et CI/CD.

## Verdict

ClaimLens est passe d'un MVP local a une application deployable raisonnablement structuree. Les
correctifs du precedent audit sont visibles : CSRF, sessions, jobs asynchrones, limite de requete,
WAL SQLite, rapports controles par proprietaire, erreurs reseau bornees et gouvernance Logics saine.

La mise en production reste exposee a quatre risques significatifs : protections anonymes
contournables, stockage cryptographique maison, promesse de verification superieure a ce que le
moteur sait conclure, et absence de tests HTTP de bout en bout sur le vrai serveur.

## Verifications executees

| Controle | Resultat |
| --- | --- |
| Ruff | OK |
| Pytest | 75 tests passes |
| `logics-manager health` | 114 documents, aucun signal |
| `logics-manager audit` | OK, 0 blocage, 0 avertissement |
| `logics-manager lint` | OK |
| Etat Git initial | Propre sur `main` |

## Constats prioritaires

### P0 - Le rate limiting anonyme est contournable

L'identite anonyme repose sur `claimlens_guest`. Lorsqu'aucun cookie n'existe, `_context()` genere
un nouveau token a chaque requete. Le cookie n'est pose qu'apres certaines actions reussies. Un
attaquant peut donc renouveler son identite a chaque tentative de login ou requete rejetee et
contourner la limite SQLite.

Cela affaiblit directement la protection contre le brute force et l'abus des actions couteuses.

Solution :

- emettre le cookie visiteur des le premier GET, y compris `/login` ;
- conserver une deuxieme limite au reverse proxy par IP/plage pour l'authentification ;
- separer les budgets `login`, `register`, appels LLM et fournisseurs de transcript ;
- ajouter un test HTTP qui enchaine des echecs sans cookie preexistant.

### P0 - Le CSRF invite est partage par tout le processus

`guest_csrf_token` est genere une seule fois au demarrage puis reutilise par tous les visiteurs non
authentifies. Un visiteur peut donc apprendre le jeton d'un autre visiteur. `SameSite=Lax` limite
certains scenarios, mais le controle n'est pas lie a une identite et ne constitue pas une vraie
protection CSRF pour les actions anonymes ou le login.

Solution : associer un jeton CSRF aleatoire a chaque cookie visiteur, stocke sous forme de digest ou
signe avec un secret serveur, puis le comparer en temps constant.

### P1 - Le bouton de test de trois fournisseurs ne teste rien

Pour OpenAI, Semantic Scholar et NCBI, l'action `test_api_key` resout la cle puis renseigne
`tested_at` sans appel distant. L'interface peut donc presenter comme testee une cle invalide,
expiree ou sans droits. Seule la cle Supadata est effectivement verifiee.

Solution :

- implementer un appel minimal et peu couteux par fournisseur ;
- stocker `test_status`, le code d'erreur normalise et la date ;
- ne jamais traduire la seule presence/dechiffrabilite d'une cle en test reussi ;
- couvrir les reponses 401, 403, 429 et timeout.

### P1 - La verification scientifique ne produit pas de polarite native

`assess_claim_evidence()` ne classe un element que si le candidat contient
`metadata.assessment_polarity`. Les adaptateurs PubMed et Semantic Scholar ne renseignent jamais ce
champ. Avec le code de production, des sources peuvent etre trouvees mais le verdict restera
`unclear`; les verdicts `supported`, `contradicted` ou `mixed` ne sont accessibles qu'avec un
adaptateur externe ou de test qui fournit deja la conclusion.

Ce comportement est prudent, mais les termes "source-verified brief" et certains textes produit
peuvent faire croire a une verification semantique.

Solution :

- renommer le mode actuel en "recherche de sources candidates" ;
- ou ajouter une etape d'evaluation explicite, auditable, ancree sur abstracts complets ;
- afficher separement pertinence de recherche, polarite, qualite de source et niveau de preuve ;
- conserver le disclaimer et interdire tout vocabulaire medical conclusif sans revue humaine.

### P1 - Chiffrement de secrets cryptographique maison

`secrets.py` implemente PBKDF2, un flux XOR derive de SHA-256 et HMAC avec la meme cle. Le schema
semble authentifie et utilise des nonces aleatoires, mais il n'est ni standard ni audite, et ne
prevoit pas proprement rotation, version de cle ou migration. Pour des cles API de production, le
cout de maintenance et le risque d'erreur future sont injustifies.

Solution :

- utiliser AES-GCM ou ChaCha20-Poly1305 via une bibliotheque maintenue ;
- introduire un identifiant de cle et une version de format ;
- fournir une commande de rotation re-chiffrant les lignes ;
- tester troncature, corruption, mauvaise version et rotation ;
- idealement utiliser un secret manager et ne stocker que les cles reellement necessaires.

### P1 - Pas de test de bout en bout du serveur HTTP

Les tests valident surtout les fonctions de rendu, la base et les services. Ils ne demarrent pas le
`ThreadingHTTPServer` pour verifier cookies, redirections, limites de corps, CSRF, telechargement,
en-tetes, isolation entre deux clients et concurrence des jobs. Les deux constats P0 sont precisement
des defauts d'integration invisibles avec les tests actuels.

Solution : creer une fixture serveur sur port aleatoire et tester deux clients independants avec une
bibliotheque HTTP.

### P1 - Processus web artisanal et capacite limitee

Le serveur standard et un `ThreadPoolExecutor(max_workers=2)` global conviennent a une instance
personnelle, mais n'offrent ni arret gracieux des jobs, ni file externe, ni fonctionnement
multi-replica. Un redemarrage marque les jobs interrompus, sans reprise. La documentation mentionne
cette limite, mais la capacite et les objectifs de disponibilite ne sont pas formalises.

Solution :

- garder une seule instance tant que la file reste en memoire ;
- ajouter profondeur de file, duree et taux d'echec aux metriques ;
- refuser proprement au-dela d'une taille de file ;
- migrer vers une file persistante seulement si la charge le justifie.

### P2 - Le conteneur s'execute en root

Le Dockerfile ne cree pas d'utilisateur applicatif. `cap_drop` et `no-new-privileges` dans Compose
sont utiles, mais ne remplacent pas un UID non privilegie, notamment en cas d'execution hors de ce
Compose.

Solution : creer un utilisateur dedie, preparer `/data` avec les bons droits et ajouter un
`HEALTHCHECK` directement dans l'image.

### P2 - Hygiene des sessions et donnees techniques

Les sessions expirees ne sont pas purgees et `last_seen_at` est ecrit sur chaque requete
authentifiee. Les evenements de limite sont purges lors des actions, mais il n'existe pas de tache
generale de maintenance ni de politique de retention pour runs, transcripts et rapports.

Solution : ajouter une commande de maintenance idempotente, documenter la retention et limiter la
frequence de mise a jour de `last_seen_at`.

### P2 - Supply chain et couverture de versions

La CI courante ne teste que Python 3.11 alors que l'image utilise 3.12. Les images et actions sont
referencees par tags mutables, sans SBOM ni scan de vulnerabilites.

Solution : matrice 3.11/3.12, images pinnees par digest, actions pinnees par SHA, SBOM et scan de
l'image publiee.

### P2 - Modules devenus tres volumineux

`web.py` depasse 2 100 lignes et `db.py` 1 700 lignes. La separation fonctionnelle existe, mais ces
deux modules concentrent trop de responsabilites pour continuer a evoluer sans regressions.

Solution : extraire progressivement routes/auth/jobs/rendu et schema/migrations/repositories, en
s'appuyant sur les tests existants et sans rearchitecture globale.

## Plan recommande

### Avant la prochaine exposition publique

- Lier cookie visiteur, CSRF et rate limiting ; ajouter une limite IP au proxy.
- Ajouter les tests HTTP multi-client correspondants.
- Corriger l'etiquetage du test de cles et le vocabulaire de verification.

### Iteration suivante

- Remplacer le chiffrement maison et definir la rotation.
- Executer le conteneur sans privileges.
- Ajouter observabilite des jobs, retention et maintenance.

### Ensuite

- Decomposer `web.py` et `db.py`.
- Renforcer la supply chain et tester Python 3.12 en CI.
- Evaluer scientifiquement le moteur de polarite avant de promettre des verdicts.

## Points forts a conserver

- Tests rapides, deterministes et lint propre.
- Logics completement sain et workflows clos.
- SQL parametre, WAL et transactions explicites.
- Cloisonnement des runs et rapports par utilisateur ou visiteur.
- Erreurs reseau bornees et verification volontairement conservative.
