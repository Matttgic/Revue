# Modèles de Revue

Deux familles strictement séparées :

1. **Reproductions** (`modeles/reproduction/`) : réécritures indépendantes de fonctions d'un dépôt tiers. Elles sont vérifiées par comparaison exacte avec l'original sur des entrées identiques. Elles ne contiennent aucun choix propre à Revue.
2. **Modèles Revue** (`modeles/simulations/`) : modèles originaux de recherche, non calibrés. Ils sont suivis de façon prospective : prévision figée avant le match, puis réglée sur le score officiel.

**Statut commun à tous : aucun modèle n'a démontré de rentabilité.** Une parité de formule ou un bon Brier ne prouve pas un avantage contre le marché. Seuls des paris pré-match, à des cotes réellement observées et en nombre suffisant, peuvent le faire.

## 1. Reproductions — Clairvoyance (Purple-Wraith/clairvoyance-backend)

Catalogue strict : [docs/parite-modeles-clairvoyance.json](../docs/parite-modeles-clairvoyance.json) (44 fonctions, parité de formule vérifiée à chaque exécution du workflow `parite-clairvoyance-predictor.yml`). Détails et règles : [modeles/reproduction/README.md](../modeles/reproduction/README.md).

| Domaine | Fonctions originales | Fichier Revue | Vérificateur |
|---|---|---|---|
| MLB / NHL (backend) | `predict_mlb_game`, `predict_nhl_game` (Elo, xG MoneyPuck, gardien) | [clairvoyance_predictor.py](../modeles/reproduction/clairvoyance_predictor.py) | `outils/clairvoyance/verifier_parite_clairvoyance.py` |
| NBA / NFL / football (frontend) | `nbaMC`, `nbaGetBayes`, `nbaEns`, `nbaEloWP`, `nflMC`, `_nflBayes`, `nflEns`, `_soccerMC`, `_socMarketBlend` | [frontend_clairvoyance.js](../modeles/reproduction/frontend_clairvoyance.js) | `outils/clairvoyance/verify_clairvoyance_frontend.js` |
| NHL (frontend) | `nhlMC`, `nhlEns`, gardiens et forme | [frontend_clairvoyance_nhl.js](../modeles/reproduction/frontend_clairvoyance_nhl.js), […_nhl_goalie_form.js](../modeles/reproduction/frontend_clairvoyance_nhl_goalie_form.js) | `verify_clairvoyance_nhl*.js` |
| Football | xG, Poisson, handicap asiatique, forme, FBref / Ligue des champions | `frontend_clairvoyance_soccer_*.js` | `verify_clairvoyance_soccer_*.js` |
| Hockey européen (Liiga, SHL, NLA, Extraliga) | taux de buts, Monte-Carlo, ensembles, mélange marché | `frontend_clairvoyance_euro_hockey*.js`, `…_hockey_market.js` | `verify_clairvoyance_euro_hockey*.js`, `…_hockey_market.js` |
| NBA props / blessures | `_generateNBAProps`, `_modelLineForProp`, `computeInjuryImpact`, plafond `MARKET_P_CEILING` | `frontend_clairvoyance_nba_props.js`, `…_player_line.js`, `…_injury_impact.js`, `…_market_ceiling.js` | `verify_clairvoyance_nba_props.js`, … |
| Prétraitement NBA (backend) | saison, sélection des stats, ratings d'équipes, niveaux de joueurs ; parseur ESPN | [clairvoyance_nba_source.py](../modeles/reproduction/clairvoyance_nba_source.py), [clairvoyance_nba_espn_source.py](../modeles/reproduction/clairvoyance_nba_espn_source.py) | `verifier_parite_nba_source.py`, `verifier_parite_nba_espn_source.py` |
| Données et contrôle | parseur MoneyPuck, gardiens ESPN, classificateur de chronologie des verrouillages | `clairvoyance_moneypuck_parser.py`, `clairvoyance_nhl_goalies_source.py`, `clairvoyance_lock_timing.py` | `verifier_parite_moneypuck_source.py`, `verifier_parite_timing_clairvoyance.py` |

**Pas encore reproduit :** la couche de sélection des paris (`sportCalibrate` et la correction adaptative, `_evalMkts` / `tier()`, les règles de `auto_lock_settle.py`). Voir [l'analyse du 11/10](../analyses/2026-10-11_Clairvoyance_verification_rentabilite_et_reproduction.md).

## 2. Modèles Revue (recherche, non calibrés)

| Modèle | Fichier | Méthode | Suivi publié |
|---|---|---|---|
| NHL indépendant | [nhl_independant.py](../modeles/simulations/nhl_independant.py) · [doc](../modeles/simulations/NHL-INDEPENDANT-README.md) | Elo + taux de buts régularisés + Poisson | [nhl-model-latest.json](../docs/nhl-model-latest.json) |
| NHL joueurs | [nhl_joueurs_independant.py](../modeles/simulations/nhl_joueurs_independant.py) · [doc](../modeles/simulations/NHL-JOUEURS-README.md) | Probabilités de props joueurs (alignements non confirmés) | [nhl-players-latest.json](../docs/nhl-players-latest.json) |
| Multisports v0.1 | [multisports_independant.py](../modeles/simulations/multisports_independant.py) · [doc](../modeles/simulations/MULTISPORTS-README.md) | Elo + modèles de score par sport | [multisports-latest.json](../docs/multisports-latest.json) |
| Ensemble MC / Bayes | [ensemble_montecarlo_bayes.py](../modeles/simulations/ensemble_montecarlo_bayes.py) | Elo + Beta-Binomial + Monte-Carlo à graine fixe | [ensemble-mc-bayes-performance.json](../docs/ensemble-mc-bayes-performance.json) |
| Équipes avancé | [equipes_avance_multisports.py](../modeles/simulations/equipes_avance_multisports.py) | Modèle d'équipe multisports | [equipes-avance-shadow.json](../docs/equipes-avance-shadow.json) |
| Football avancé | [football_avance_independant.py](../modeles/simulations/football_avance_independant.py) · [doc](../modeles/simulations/FOOTBALL-AVANCE-README.md) | Elo glissant + buts, xG sous licence optionnel | [football-shadow-performance.json](../docs/football-shadow-performance.json) |
| Football stats ESPN | [football_espn_statistiques.py](../modeles/simulations/football_espn_statistiques.py) | Agrégats de stats de match ESPN (pas Opta) | [football-espn-team-features.json](../docs/football-espn-team-features.json) |
| NBA prior | [nba_prior_espn.py](../modeles/simulations/nba_prior_espn.py) | Prior de début de saison issu du classement précédent | [nba-prior-shadow.json](../docs/nba-prior-shadow.json) |
| Sports individuels et Liiga | [sports_individuels_et_liiga.py](../modeles/simulations/sports_individuels_et_liiga.py) · [doc](../modeles/simulations/SPORTS_INDIVIDUELS_README.md) | Tennis, MMA, Liiga | [individual-prospective-performance.json](../docs/individual-prospective-performance.json) |

Comparaison hors échantillon de tous les modèles : [phase13-modeles-evaluation-latest.json](../docs/phase13-modeles-evaluation-latest.json) (Brier, log-loss par ligue sur résultats officiels).

## Ajouter un modèle

1. **Reproduction** : `modeles/reproduction/`, accompagnée d'un vérificateur dans `outils/clairvoyance/` (ou d'un groupe dédié pour une autre source). Le vérificateur compare la sortie à celle de l'original. Tant que la parité n'est pas prouvée, le statut reste « en attente de parité ».
2. **Modèle Revue** : `modeles/simulations/` avec une doc `NOM-README.md`, des tests dans `tests/` et un suivi prospectif (`outils/suivi/`). Le modèle n'est jamais réentraîné sur les matchs qu'il prédit.
3. Ajouter une ligne ici.
