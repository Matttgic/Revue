# Revue API — compatibilité de contrats et écarts envers Clairvoyance

Source originale : `Purple-Wraith/clairvoyance-backend`.
Service indépendant Revue : <https://revue-api-tawny.vercel.app/>.
Projet Vercel : `revue-api`, sans modification des autres projets.

## Ce qui fonctionne réellement

Le backend Python est implémenté dans `api_revue/app.py`. Le déploiement
Vercel est READY et son comportement a été vérifié depuis une machine GitHub
Actions distincte : `GET /health`, `GET /revue/parity`,
`GET /nhl/schedule?game_date=2026-10-10` renvoient HTTP 200 avec JSON.

Signatures GET présentes et vérifiées par tests de contrat :

- `GET /health` : statut de vie du processus ; n'est **pas** un indicateur
  de santé de tous les fournisseurs de données.
- `GET /nhl/schedule?game_date=YYYY-MM-DD` : calendrier NHL public de Revue,
  champs de la réponse originale, avec ID ESPN uniquement quand il est
  **réconcilié strictement** par équipe et début UTC avec le calendrier source.
- `GET /mlb/schedule?game_date=YYYY-MM-DD` : matchs MLB ESPN connus dans
  Revue, champs source, dates des fixtures. Pas de lanceur ou cotes inventés.
- `GET /mlb/games/{espn_id}` : détail sur les seuls matchs ESPN présents
  dans les snapshots Revue.
- `GET /nhl/teams`, `GET /nhl/goalies?min_games=1`, `GET /nhl/skaters?team=ANA` : statistiques saisonnières NHL officielles avec les champs indisponibles laissés à `null` ; aucune composition annoncée.
- `GET /nhl/moneypuck?situation=all` : statistiques MoneyPuck de saison en snapshot horodaté, pas du direct.
- `GET /nhl/moneypuck/live` : nouvelle récupération directe de fichiers CSV MoneyPuck équipes et gardiens ; vérifiée avec HTTP 200 en production. Pas un flux de matchs et pas encore identique aux filtres/champs Clairvoyance ; aucun titulaire confirmé.
- `GET /revue/predictions?game_date=YYYY-MM-DD` : **route propre à Revue**, disponible sur Vercel. Elle calcule les probabilités NHL/MLB avec la même formule backend que Clairvoyance, mais exclusivement à partir des snapshots Revue horodatés. NHL : identifiants ESPN vérifiés, xG 5v5, Elo proxy et gardiens historiques avec audit temporel ; MLB : Elo rejoué sur les résultats officiels ESPN avant match. Seuls les matchs futurs (au moins 20 minutes) sont publiés, aucun prix n'est inventé. L'endpoint renvoie HTTP 503 si aucune prévision sûre n'existe. [Interface mobile](../docs/predictions-revue.html) · [tests HTTP et anti-fuite](../tests/test_api_revue_research_predictions.py).
- `GET /predictions/?game_date=YYYY-MM-DD` : signature prévue mais
  intentionnellement **HTTP 503**, car les inputs Elo, gardiens et marchés
  de la base originale ne sont pas identiques et ne doivent pas être simulés.

Endpoint propre à Revue : `GET /revue/parity` pour lire le niveau réel
de reproduction, sans chiffre global trompeur.

**Important :** quatorze signatures GET sur les vingt-quatre routes originales sont
déclarées, dont trois routes de picks simulés ; `/predictions/` refuse volontairement de produire un résultat sans données équivalentes. Cela ne veut pas dire que
14/24 routes sont **fonctionnellement identiques** : l'identité complète de
toutes les réponses, la pagination, les erreurs et les données historiques
doit être vérifiée. L'audit strict maintient donc
`end_to_end_verified_equivalent_routes: 0`.

## Picks : suivi fictif compatible avec les champs source (10 octobre 2026)

Trois routes GET supplémentaires reproduisent le **schéma** du suivi Clairvoyance,
mais pas ses données SQL : `GET /picks/` (filtres `status`, `sport`,
`game_date`), `GET /picks/stats` (filtres `sport`, `bet_type`) et
`GET /picks/{pick_id}`. Les seuls enregistrements admissibles sont des
**simulations NHL/MLB** du registre Revue `engine-v2-ledger.json`, avec une
chronologie pré-match valide et un marché vérifié. Les autres compétitions,
les règles de marchés incertaines et CFB sont exclus. Aucune mutation
(`POST /picks/`, `PATCH /picks/{pick_id}/void`) n'est disponible.

Le prix du registre, en décimal, est converti et arrondi en `odds`
**américain entier**, comme l'exige le schéma original. De très petits écarts
arithmétiques peuvent en résulter. `amount`, `pnl`, `roi` sont
**exclusivement des unités fictives**, jamais des euros misés ni un bilan
de l'original. L'ID `paper-000001` devient l'entier `1` : il ne s'agit
**jamais** de la clé SQL de Clairvoyance. L'ID ESPN NHL n'est exposé
que si l'appariement officiel est strictement vérifié ; sinon `null`.
Le header `X-Revue-Parity` rend ces limites vérifiables.
Voir `tests/test_api_paper_picks.py`.

## Percée : identifiants NHL/ESPN

Le rapport `docs/parite-nhl-espn-id-map.json` est créé depuis une copie
temporaire et en lecture seule de Clairvoyance. Il joint les événements par
clubs et coup d'envoi identiques ; **18 matchs/18** ont reçu une correspondance
ESPN ↔ NHL lors du premier cycle. Exemple :
`BOS – PHI` : `2026020070` côté NHL officiel ↔
`401892469` côté ESPN / Clairvoyance.

L'API retourne désormais l'identifiant ESPN réellement confirmé, et répond
HTTP 503 si une correspondance requise est absente : elle ne prétend plus
que les identifiants officiels NHL sont des identifiants ESPN.

Le code et la plateforme ne republient ni les cotes américaines, ni
les pronostics, ni les statuts de gardiens de la source originale. Les
identifiants de base SQL d'origine `id` restent inconnus : nos `id`
numériques sont **dérivés des ESPN IDs** et ne sont pas les clés SQL originales.

## Vérification et exploitation

- Tests de fixtures et sources : `tests/test_api_clairvoyance_fixtures.py`.
- Tests serveur HTTP FastAPI : `tests/test_api_clairvoyance_http.py`.
- GitHub Action : `.github/workflows/clairvoyance-api-contracts.yml`.
- Test distant de l'API Vercel : `.github/workflows/api-vercel-smoke.yml`.
- Correspondance NHL ESPN : `outils/parite_calendrier_nhl_espn.py`,
  `tests/test_parite_calendrier_nhl_espn.py` ; source temporaire uniquement.
- Tableau réel de l'identité : `docs/reproduction-exacte.html`.
- Dépendances : `requirements.txt` (Vercel), `requirements-api.txt` (CI).

La plateforme réutilise les fichiers produits par les Actions Revue. Une
redéploiement GitHub/Vercel peut être nécessaire pour refléter leur dernière
version ; ce n'est pas une API de résultats en continu. L'exactitude temporelle
est préservée : les données périmées (>8 heures pour les rencontres et >2
heures pour les scores) sont refusées, plutôt que silencieusement remplacées.

## Routes administrateur et exécutions réelles (11 octobre 2026)

- `GET /admin/status` et `GET /admin/logs` conservent les **signatures** de lecture de Clairvoyance. Faute de base `DailyLog` originale, les cinq scrapers originaux restent `null`, le prochain passage du scheduler `null` et les logs SQL une liste vide. Ce sont des **inconnues**, jamais de faux succès.
- `GET /revue/workflows` expose séparément un instantané vérifié des exécutions GitHub Actions réelles du projet, avec dates, liens `github.com`, dernier succès/échec et filtres `workflow`/`limit`. Ce sont **des jobs Revue**, pas les scrapers SQL de Clairvoyance.
- Source statique et historique réel sur Pages : `docs/github-workflows-latest.json`, généré par `outils/github_actions_monitor.py`; observabilité en HTML `docs/operations.html`.
- La couverture des routes **déclarées** atteint 16/24, soit 66,7 %. Aucune équivalence complète de bout en bout n'est encore établie. L'API Vercel peut être en retard tant que la limitation du compte bloque son redéploiement.

## Reste avant une reproduction complète

1. La base SQL originale et ses 24 comportements API : la signature de dix routes est présente, mais l'identité de leurs résultats n'est pas prouvée ; restent notamment les statuts admin, l'historique des picks, Elo MLB et des correspondances statistiques exactes.
2. L'équivalence sur mêmes snapshots des cotes, MoneyPuck 5v5/all,
   des gardiens utilisés, des classements Elo, des blessures et des règles.
3. Les vrais résultats de prédictions finales pour un même événement,
   vérifiés et contrôlés à la même date/heure.
4. La reproduction indépendante des interactions et écrans du frontend
   original (plus de 2,6 Mo et des centaines d'éléments nommés), sans copier
   le code ou des actifs protégés par l'absence de licence explicite.
5. Des historiques plurisaison et des vérifications de complétude/saisonnalité.

**L'objectif reste 100 % de fidélité mesurée, pas 100 % de fonctionnalités
similaires. Cette version ne l'a pas encore atteint.**
