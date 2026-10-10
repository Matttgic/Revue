# Revue Match Center — écart fonctionnel avec Clairvoyance

## Résultat du 10 octobre 2026

La page `docs/match-center.html` rassemble maintenant un **calendrier de
matchs multisports** avec recherche, sélection par ligue, trois horizons
(aujourd'hui / demain / 72 heures), probabilités comparées par modèle et
cotes françaises observées. C'est une interface originale, non une copie
du HTML/CSS de Clairvoyance.

Lors du premier traitement à 04 h 37 (Europe/Paris), le rapport
`docs/match-center-latest.json` donnait :

- 126 rencontres futures réparties entre 14 compétitions (**CFB exclu**) ;
- 90 rencontres auxquelles au moins un modèle de recherche avait été associé ;
- 9 rencontres avec une cote H2H/1X2 française récente et vérifiable ;
- aucun pari EV certifié, ni simulation présentée comme mise réelle.

Ces effectifs **ne sont pas des garanties de couverture** : ils changent
selon la date, les retards des API et la disponibilité des marchés.

## Provenance et méthode

Le code `outils/match_center_revue.py` assemble uniquement les propres
rapports Revue, sans republier les picks de Clairvoyance :

1. `docs/multisports-latest.json` : calendrier de base et modèles score.
2. `docs/football-advanced-shadow.json` : deuxième projection football.
3. `docs/nhl-clairvoyance-shadow-latest.json` : formule NHL ciblée reproduite,
   proxy Elo Revue et modèle NHL Prudent, avec audit temporel obligatoire.
4. `docs/ensemble-mc-bayes-latest.json` : autre modèle indépendant sur certains
   sports, uniquement si la prévision est complète.
5. `docs/engine-v2-latest.json` : cotes observées de bookmakers français.

Les rapprochements exigent **même compétition, même identifiant de rencontre,
mêmes deux adversaires et même instant UTC**. Un prix doit avoir été effectivement
collecté avant le début du match, daté au plus de 24 heures, avec les sélections
complètes du marché H2H/1X2. Le score, le bookmaker, la cote, le résultat et
l'existence même d'une rencontre ne sont jamais inventés.

Les marchés NHL dont le règlement en prolongation n'est pas certifié sont
marqués non vérifiés. **Aucune EV n'est déduite** d'une juxtaposition de
probabilités de recherche non calibrées et de règles de marché différentes.

Les données du frontend sont régénérées par GitHub Actions toutes les heures
sans appel API premium additionnel. La génération n'interroge que les derniers
instantanés déjà présents dans le dépôt ; par conséquent un prix ancien ne
devient jamais un cours en direct.

## Résultats réels et historique prudent

Le Match Center consomme aussi le registre immuable
`docs/nhl-shadow-ledger.json`. Le module de résultats n'accepte que les
matchs officiellement réglés : prévision verrouillée au moins 20 minutes avant
la rencontre, résultat NHL concordant et règlement déclaré après le début du
match. Toute rencontre au score incohérent, antidatée ou dont la date de
résolution se situe dans le futur est exclue.

Ce panneau affiche le score et les probabilités NHL originales figées de Revue.
Il montre le nombre d'événements encore **en attente**, sans inventer des
résultats d'autres sports. Aucune ligne n'est présentée comme un pari misé.

## Comparaison qualitative avec le dépôt source

Le dépôt public `Purple-Wraith/clairvoyance-backend` comprend une application
web centrale, des prévisions pour diverses ligues, un historique de sélections,
des données joueurs, des calendriers, un tableau de rendement et des éléments
de surveillance. Il publie notamment `docs/data.json`,
`docs/engine_performance.json` et `docs/sport_performance.json`.

Revue dispose maintenant d'une navigation et d'un tableau de matchs similaires
**sur le plan des familles de fonctions**, mais **ne reproduit toujours pas**
de bout en bout :

- les choix de sélections et leur validation rentable ;
- les scores réellement live pour toutes les ligues ;
- la profondeur des données de joueurs, blessures et compositions ;
- les règles complètes des cotes et les historiques de clôture ;
- les données sous licence Opta ;
- l'historique de milliers de sélections avec horaires verrouillés vérifiables ;
- les 2,6 Mo de frontend de l'autre dépôt au pixel près et ses parcours complets.

La source Clairvoyance publie dans son rapport de performance des résultats
incluant des paris verrouillés **après le début du match** et d'autres dont la
chronologie est inconnue. Il serait trompeur d'importer ces chiffres comme
preuve de performance prospective de Revue.

## Vérifications et limites

- Tests de correspondance des matchs et de la présence des cotes
  `tests/test_match_center_revue.py` ;
- Vérification des liens, des scripts et des garde-fous de l'interface
  `tests/test_site_arena.py` ;
- Workflow `.github/workflows/match-center-revue.yml` ;
- Workflow GitHub Pages après le rafraîchissement
  `.github/workflows/deploy-pages.yml`.

**La ressemblance du tableau de bord est distincte de la fidélité des
algorithmes.** Le pourcentage d'avancement global est une estimation de
couverture fonctionnelle, non une mesure objective d'identité de deux sites
ni un taux de réussite des modèles. Aucun droit de réutiliser automatiquement
le code du site source n'est supposé du seul fait qu'il soit public.
