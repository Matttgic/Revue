# Audit — lmchugh17/nfl-betting-model

- **URL originale :** [github.com/lmchugh17/nfl-betting-model](https://github.com/lmchugh17/nfl-betting-model)
- **Commit audité :** [`a92149902ce96283e2a484802c5632f18bb7760d`](https://github.com/lmchugh17/nfl-betting-model/commit/a92149902ce96283e2a484802c5632f18bb7760d) (`2026-10-11`, `Weekly predictions: 2026-10-11`)
- **Date d'audit :** 2026-10-11
- **Licence :** aucun fichier de licence repéré dans le commit; ne pas reprendre le code, le modèle ou les données sans autorisation explicite.
- **Maintenance :** activité visible sur `main` à la date de l'audit; le commit examiné publie les prédictions hebdomadaires.
- **Stack :** Python, scikit-learn, XGBoost, LightGBM, pandas, SQLite; actions GitHub; nflverse via `nflreadpy`.

## Avis

**À conserver comme piste de recherche, sans conclusion de rentabilité.** C'est un projet NFL complet et intéressant pour son double objectif — probabilité de victoire et marge prévue — et sa règle de ne pas miser quand le signal ATS calibré n'atteint pas le seuil de rentabilité. Sa propre documentation montre cependant un écart au marché sur le holdout, puis un suivi 2026 sous la ligne en erreur de marge et nettement déficitaire ATS. De plus, le réglage du nombre de plis a consulté le holdout, et les variables météo historiques et en direct ne sont pas construites à partir d'une même source disponible avant match.

## Résumé technique

Le pipeline charge les horaires, play-by-play, blessures, effectifs et statistiques NFL de nflverse, les prix de The Odds API (secret `ODDS_API_KEY` requis), les prévisions Open-Meteo et une probabilité Polymarket utilisée comme référence passive. Il construit des variables d'Elo/SRS, d'EPA récente, de résultats ATS et H2H, de repos/voyage, de QB et d'indisponibilité pondérée, et de météo.

La tête de moneyline combine régression logistique, Random Forest, XGBoost, LightGBM et ExtraTrees dans un méta-modèle logistique entraîné sur des prédictions OOF temporelles. Une tête XGBoost distincte prévoit la marge. La ligne `market_spread` ne figure pas dans les variables d'entraînement; elle sert ensuite à calculer l'écart à la marge du marché. Un modèle logistique estime la couverture en fonction de la valeur absolue de cet écart, puis une règle de mise Kelly fractionnée recommande zéro mise si la probabilité estimée est sous le seuil de rentabilité.

Le checkout audité contient des bases SQLite suivies par Git (`data/nfl_stats.db`, environ 45,7 Mo, et `data/nfl_predictions.db`, environ 201 Ko) et un modèle sérialisé. Elles n'ont pas été copiées dans Revue. Les documents du dépôt sont incohérents : le README présente encore le « Task 0 » comme seule tâche accomplie, alors que `TASKS.md`, `MAP.md`, les bases et les prédictions décrivent un système déjà construit.

## Résultats et limites statistiques

### Holdout 2025 rapporté par l'auteur

`TASKS.md` indique un entraînement sur 2 476 matchs de 2016–2024 et un holdout de 285 matchs en 2025. L'auteur rapporte 62,46 % d'exactitude, AUC 0,696, log-loss 0,632 et Brier 0,221. L'exactitude est sous le favori du marché (65,96 %); l'erreur absolue de marge du modèle est 10,22 points contre 9,67 pour la ligne. Le dépôt conclut lui-même qu'aucune métrique n'a dépassé le marché.

La lecture du holdout n'est pas strictement aveugle : `N_SPLITS` a été comparé aux valeurs 3, 4, 5 et 6 sur ce même holdout, et 6 a été retenu après comparaison de plusieurs métriques. Cela constitue un réglage sur l'échantillon censé évaluer le modèle; ces scores restent informatifs, mais ne sont pas une estimation indépendante de performance hors échantillon.

### Suivi 2026 recalculé sur le snapshot versionné

J'ai joint en lecture seule les prédictions à la base de matchs du commit et comparé chaque horodatage de sauvegarde au coup d'envoi NFL en heure de l'Est. Sur les 65 matchs terminés de saison 2026, une prédiction (`2026_01_NE_SEA`) a été enregistrée après le coup d'envoi et a été exclue. Sur les **64 prédictions pré-match** restantes :

- **ATS : 25–37–2**, soit 40,3 % des 62 résultats décidés;
- **moneyline : 36/64** gagnés;
- **MAE de marge : 10,96 points**, contre **9,91** pour la ligne nflverse jointe;
- **Brier moneyline : 0,23672** pour le modèle contre **0,23689** pour Polymarket, sur les mêmes 64 matchs.

L'écart de Brier est minuscule (0,00017) et ne démontre pas d'avantage. Les mesures ATS et MAE vont dans le sens défavorable au modèle. Le dépôt documente qu'après le redémarrage de sa bankroll papier le 27 septembre, les 32 prédictions terminées n'ont toutes recommandé aucune mise positive; ces lignes ne démontrent donc pas de rendement réalisé. Ce recalcul vérifie les enregistrements du snapshot, pas une réexécution du modèle ni une nouvelle expérience hors échantillon. Il reste précoce et de taille limitée.

## Contrôles de validité

- **Météo — décalage train/prévision :** `scripts/build_features.py` calcule l'indicateur de météo adverse avec les températures et vents NFL réalisés après les matchs. Le chemin de prédiction remplit ces valeurs par les prévisions Open-Meteo pour les matchs à venir. `src/weather_features.py` note l'absence d'historique équivalent de prévisions. Le modèle apprend donc sur une météo effectivement réalisée, pas sur une archive de prévisions au moment de la décision; c'est un décalage de disponibilité potentiellement déterminant.
- **Blessures — horodatage :** `src/availability.py` sélectionne les statuts par saison, semaine, équipe et joueur; il ne filtre pas les rapports selon `date_modified` ou `scraped_at` avant le coup d'envoi. Dans la base fournie, un contrôle des associations match/équipe/semaine a trouvé 23 rapports avec `date_modified` postérieur au jour du match (sur environ 49 469 associations vérifiées). La fréquence est faible dans cet audit, mais le code ne garantit pas la disponibilité pré-match.
- **Prédiction tardive :** le code ajoute désormais une garde contre les matchs déjà commencés et le commentaire signale lui-même un ancien enregistrement tardif. Le snapshot contient bien un pick sauvegardé environ 13 h 47 après le coup d'envoi de `2026_01_NE_SEA`; il ne doit pas entrer dans une mesure pré-match.
- **Association au prix :** `src/spread_pricing.py` regroupe les prix récents par équipe, mais n'associe pas le prix au `odds_game_id` ni au `point` de spread dans le calcul retourné. `predict_games.py` compare ce prix d'équipe à l'écart de modèle calculé avec la ligne nflverse. La base permet de retrouver des prix de bookmakers, mais cette fonction ne prouve pas que le prix noté correspond au même match et au même spread.
- **Calibrage / sélection :** `scripts/fit_bet_sizing.py` ajuste la probabilité de couverture sur les matchs 2025 du holdout. La documentation rapporte une relation presque plate entre la valeur absolue de l'écart et la couverture (`corr=0,006`, `p=0,93`) et une pente quasi nulle; la règle d'abstention est prudente, mais le calibrage n'est pas une preuve de signal.
- **Données et reproductibilité :** les bases et leur collecte dépendent de sources tierces; les cotes The Odds API nécessitent une clé et les prix historiques réellement accessibles ne sont pas archivés comme un flux complet dans les seules tables de prédictions. Les performances publiées n'ont pas été réexécutées avec le modèle sérialisé.

## Vérifications effectuées

- 34 fichiers Python analysés statiquement par le parseur AST : aucune erreur de syntaxe.
- Aucune installation des dépendances, aucun chargement du pickle, aucune exécution des workflows et aucun appel API; le dépôt ne fournit pas de suite de tests repérée.
- Recalcul SQL en lecture seule des scores 2026 pré-match et du rapport de blessures; aucune modification du checkout source.
- Le manifeste de dépendances est non verrouillé; aucun fichier de licence explicite n'est présent.
- Aucun code, modèle, historique SQLite, secret ou autre fichier source copié dans Revue.

## Idée retenue et relation aux sources déjà cataloguées

`Stat-Seer` traite surtout les props NFL, le volume des joueurs et la distribution de marges autour des key numbers. Ce dépôt apporte une piste de **match complet** : comparer une probabilité de victoire issue d'un ensemble temporel et une marge indépendante, puis tester prospectivement une règle d'abstention ATS fondée sur le marché. C'est suffisamment distinct pour une fiche, mais pas pour reprendre le code ni faire un doublon de moteur de mise.

| Critère | Note | Preuve |
|---|---:|---|
| Utilité de l'idée (20) | NC | Architecture utile à expérimenter, avantage non établi |
| Code (20) | NC | Pipeline développé, non installé ni exécuté ici |
| Données (15) | NC | Bases versionnées, droits de redistribution non clarifiés |
| Validité statistique (20) | NC | Holdout consulté au réglage; mismatch météo et dates d'indisponibilité à corriger |
| Testabilité (15) | NC | Suivi 2026 utile, mais pas de tests repérés ni d'expérience reproduite |
| Maintenance / sécurité (10) | NC | Commit actuel, clé d'API hors dépôt via secret; licence absente |

**Score : non calculé; critères insuffisamment comparables sans exécution et protocole indépendant.**

## Fichiers source consultés

- [README](https://github.com/lmchugh17/nfl-betting-model/blob/a92149902ce96283e2a484802c5632f18bb7760d/README.md)
- [Journal des tâches et holdout](https://github.com/lmchugh17/nfl-betting-model/blob/a92149902ce96283e2a484802c5632f18bb7760d/TASKS.md)
- [Revue de calibration 2026](https://github.com/lmchugh17/nfl-betting-model/blob/a92149902ce96283e2a484802c5632f18bb7760d/CALIBRATION_REVIEW_2026.md)
- [Variables du modèle](https://github.com/lmchugh17/nfl-betting-model/blob/a92149902ce96283e2a484802c5632f18bb7760d/src/model.py)
- [Construction historique des features](https://github.com/lmchugh17/nfl-betting-model/blob/a92149902ce96283e2a484802c5632f18bb7760d/scripts/build_features.py)
- [Features météo](https://github.com/lmchugh17/nfl-betting-model/blob/a92149902ce96283e2a484802c5632f18bb7760d/src/weather_features.py)
- [Disponibilité / blessures](https://github.com/lmchugh17/nfl-betting-model/blob/a92149902ce96283e2a484802c5632f18bb7760d/src/availability.py)
- [Barrière pré-coup d'envoi et pricing](https://github.com/lmchugh17/nfl-betting-model/blob/a92149902ce96283e2a484802c5632f18bb7760d/scripts/predict_games.py)
- [Prix de spreads](https://github.com/lmchugh17/nfl-betting-model/blob/a92149902ce96283e2a484802c5632f18bb7760d/src/spread_pricing.py)
