# Audit — VCheque/Football-Betting

- **URL :** https://github.com/VCheque/Football-Betting
- **Auteur :** VCheque
- **Commit audité :** `62158a22ad12da23825f4e4674397ddddf945972` (main, 2026-10-09)
- **Consultation :** 2026-10-09
- **Licence :** aucune licence de code repérée (métadonnées GitHub et arborescence examinées). **Ne pas copier ni redistribuer le code ou les CSV tiers** sans licence ou autorisation.
- **Technologies :** Python, Streamlit, XGBoost, pandas, scikit-learn, GitHub Actions, CSV.
- **État :** dépôt actif; mises à jour le 2026-10-09; pas de suite de tests ni de publication de backtest indépendant repérées dans l'arborescence.
- **Décision Revue :** retenir plusieurs idées dans `recherche/`, **pas de validation de rentabilité**.

## Architecture effectivement constatée

| Source | Fonction |
|---|---|
| [xgboost_models.py](https://github.com/VCheque/Football-Betting/blob/main/sports_betting/xgboost_models.py) | 20 variables et entraînement d'un classifieur XGBoost 1N2; Elo, classement, états chronologiques |
| [generate_bet_combinations.py](https://github.com/VCheque/Football-Betting/blob/main/sports_betting/generate_bet_combinations.py) | estimateur 1N2 heuristique **distinct du XGBoost**, table EV, combinés |
| [fetch_top6_data.py](https://github.com/VCheque/Football-Betting/blob/main/sports_betting/fetch_top6_data.py) | extraction/harmonisation résultats et cotes football-data.co.uk sur 6 ligues |
| [fetch_player_stats.py](https://github.com/VCheque/Football-Betting/blob/main/sports_betting/fetch_player_stats.py) | stats joueurs Understat, ou API-Football avec clé |
| [app.py](https://github.com/VCheque/Football-Betting/blob/main/app.py) | dashboard Streamlit, équipes/joueurs, predictions et constructeur de tickets |
| [.github/workflows](https://github.com/VCheque/Football-Betting/tree/main/.github/workflows) | deux rafraîchissements automatisés des matchs et joueurs |

Les ligues documentées : Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Primeira Liga. Au moment de l'examen, `refresh_metadata.json` annonce **10 750** lignes matchs (2026-10-09) mais les statistiques joueurs datent du **2026-03-23** (2 660 enregistrements) ; la mise à jour hebdomadaire ne peut donc pas être considérée comme effective sur cette seule preuve.

## Forces à conserver

1. **Variables construites avant le résultat**, pour l'essentiel : Elo d'équipes, forme récente, buts, tirs cadrés, force domicile/extérieur, classement, repos, fatigue.
2. **Moteur 1N2 indépendant des règles de sélection**, objectif multiclasses explicite, pondération dégressive de l'historique.
3. **Séparation par composants** : collecte, normalisation, prédiction, interface, génération des tickets.
4. **Automatisation déclarée** : workflows programmés 4 fois par jour pour matchs et une fois par semaine pour joueurs.
5. **Traçabilité utile** des coefficients et paramètres d'apprentissage.

## Défauts et risques prioritaires

### P0 — Les « cotes » du constructeur de tickets sont synthétiques

Dans [app.py](https://github.com/VCheque/Football-Betting/blob/main/app.py#L3468-L3508), le constructeur prend une probabilité initiale `q`, la réduit à `p = clip(0.85q, .01, .99)`, puis crée sa propre « cote » `d = round(max(1.01, 0.95/p), 2)`. L'EV affichée est `p*d-1`.

**Conséquence algébrique :** hors arrondi et plancher, `EV = p*(0.95/p)-1 = -0.05`, toujours -5 % ; sur 2 paris indépendants à ces prix l'EV serait `0.95²-1 = -9.75 %` avant effets d'arrondi. Ce ne sont **pas** des cotes bookmaker observées; classer les tickets selon cette EV n'identifie pas de value. L'interface contient également une option de cote « implicite » calculée à partir de sa propre probabilité.

**Correctif exigé :** imposer une cote réelle, un bookmaker, un marché/ligne exact, un timestamp et une source autorisée avant toute décision EV.

### P0 — Calibration revendiquée sans implémentation effective du modèle 1N2

Le README annonce une calibration isotone après XGBoost. Dans `train_match_model`, le code visible entraîne seulement `XGBClassifier.fit` et renvoie directement ses probabilités dans `predict_match_proba`, sans `IsotonicRegression` ni `CalibratedClassifierCV` dans ce parcours. Ne pas appeler ses probabilités « calibrées » sans preuve métrique.

**Correctif :** train / calibration / test découpés chronologiquement ; log loss, Brier multiclasses, courbes de calibration, comparaison au consensus bookmaker sans marge.

### P1 — Deux systèmes de prédiction différents

`generate_bet_combinations.py` calcule un score à poids fixes (rangs, points, attaque, défense, H2H, etc.), transforme ce score via une fonction logistique et le taux de nul de la ligue, puis choisit des cotes historiques. Ce **n'est pas** le classifieur XGBoost du tableau principal. Le lecteur doit les évaluer séparément, sans leur attribuer les mêmes performances.

### P1 — Corrélation et probabilités des combinés

Le générateur multiplie `p_i` pour estimer `P(tous gagnants)`. Il élimine plusieurs sélections du même match, ce qui est utile, mais n'exclut pas les dépendances fortes entre rencontres ou l'incertitude de calibration. **Aucun combiné n'est justifié sans prix bookmaker et sans contrôle des corrélations.**

### P1 — Temps de disponibilité / vérification hors échantillon

- `build_context` inclut les matchs avec résultat sur la **même date calendrier** que le « as-of »; sans heures exactes, cela peut introduire des résultats indisponibles au moment de certains matchs.
- En entraînement, plusieurs matchs de la même journée sont parcourus successivement; l'horodatage date seule ne garantit pas que le score d'une rencontre déjà traitée était connu avant les autres.
- Aucun rapport comparatif documenté de ROI, CLV, Brier/log loss, variance, drawdown, validation strictement hors échantillon n'a été trouvé dans ce dépôt.
- Le constructeur a une probabilité de repli fixe (0.40/0.25/0.35) si un calcul échoue : ne jamais la traiter comme une prédiction exploitable.

### P1 — Qualité des données et adéquation France

- `derby_flag` décrit « même ville » mais sa liste mélange derbys locaux et rivalités géographiquement différentes (ex. Paris SG – Lens). Renommer ou documenter correctement.
- Certaines variables de blessure et de composition sont facultatives; leur absence peut aboutir à des valeurs neutres.
- Les cotes source `B365/PS/Max/Avg` ne garantissent ni prix actuellement prenable ni présence d'un bookmaker autorisé en France.
- Selon les [conditions affichées par Football-Data](https://www.football-data.co.uk/data.php), les CSV gratuits sont présentés pour usage individuel et le site restreint les produits commerciaux ou l'entraînement de produits de données via bots/scrapers/IA. Les droits des usages automatisés et de redistribution doivent être vérifiés avant ingestion, archivage ou partage. Le fournisseur avertit aussi de la fiabilité de cotes Pinnacle à partir de juillet 2025.

## Recherche acceptée dans Revue

| ID | Sujet | Emplacement |
|---|---|---|
| REV-VCHEQUE-01 | Prévisions football XGBoost et Elo | [Fiche](../recherche/football/xgboost-elo-1n2.md) |
| REV-VCHEQUE-02 | Audit des signaux EV et cotes observées | [Fiche](../recherche/football/cotes-reelles-et-value.md) |
| REV-VCHEQUE-03 | Architecture d'actualisation et traçabilité | [Fiche](../recherche/transversales/pipeline-football-data.md) |
| REV-VCHEQUE-04 | Combinés, indépendance et risque | [Fiche](../recherche/football/combine-correlations.md) |

## Évaluation

**Score /100 : non attribué**, faute de mesures de validation et de tests reproductibles. Intérêt documentaire **élevé**; qualité d'implémentation des cotes pour value betting **insuffisante**. **Pas de code tiers ni de données copiés**, faute de licence explicite.

## Prochaines étapes

1. Comparer Elo seul, XGBoost et dé-marge des bookmakers, avec validation chronologique.
2. Construire des **cotes réelles horodatées**, issues de flux autorisés en France.
3. Ajouter un contrôle de calibration et des tests anti-fuite avant le backtest.
4. Lancer un historique prospectif paper (signaux immuables, pas de mise) puis comparer ROI et CLV.
5. Demander licence/autorisation à l'auteur avant toute reprise substantielle du code.
