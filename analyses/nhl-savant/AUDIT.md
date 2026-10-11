# Audit — dpk1212/nhl-savant

- **Source :** https://github.com/dpk1212/nhl-savant
- **Commit examiné :** `0dc9ca79275549c8a83e91ddc9d9b8f28c9804b1` (`main`), 2026-10-11
- **Date de consultation :** 2026-10-11
- **Licence :** aucun fichier `LICENSE`/`COPYING` suivi dans le dépôt. Le README limite le projet à un usage éducatif et personnel; ce texte ne constitue pas une licence libre permettant de reprendre le code ou les données. Aucun code ni jeu de données tiers n’a été copié dans Revue.
- **Stack :** React 19/Vite, JavaScript/TypeScript, scripts Node, Firebase; la base contient également des outils NBA, MLB, marchés prédictifs et suivi de mises.
- **But :** tableau de bord de paris NHL avec xG, indicateurs de régression, gardiens, équipes spéciales et un calcul Poisson des probabilités de victoire.
- **Verdict :** **piste de modèle documentée, rendement non démontré**. Le mélange xG récent/saisonnier et la régression vers la moyenne méritent un test indépendant. Les résultats historiques du script fourni ne sont pas temporellement valides.

## Résumé de la méthode

`src/utils/dataProcessing.js` construit des taux xG par 60 minutes, distingue le 5 contre 5 et le jeu de puissance, mélange la production offensive et la défense adverse, puis transforme des buts attendus en probabilité de victoire via des lois de Poisson indépendantes. Selon les données disponibles, le code ajoute une fenêtre récente L10, un retrait vers la moyenne de ligue fonction des matchs joués, une correction PDO, un petit ajustement de finition, un ajustement du gardien et un avantage domicile. Une composante distincte compare le taux xG du jeu de puissance au taux xG concédé en infériorité numérique.

Les commentaires et le README avancent plusieurs calibrations, mais les poids et seuils du modèle ne sont pas associés à un jeu d’entraînement pré-match et à une validation indépendante vérifiables. Le README annonce une attente de 54–58 % de victoires et 5–8 % de ROI annuel sans fournir le protocole ni un relevé de paris permettant de l’établir.

## Résultats et reproduction

Installation isolée avec `npm ci --ignore-scripts --no-audit --no-fund` : réussie. `npm run build` : réussie. Le build signale notamment deux clés dupliquées (`gotOdds`, `lockOdds`) dans un composant de prévisualisation et l’externalisation navigateur de modules Node (`fs/promises`, `path`, `url`). Les avis CSS, données Browserslist et taille de bundle sont secondaires.

`npm run test:accuracy` s’exécute et produit un rapport local : **175 matchs réglés en temps réglementaire**, du 7 octobre au 11 novembre 2025; RMSE des buts 2,139, Brier 0,2419 et exactitude directionnelle 56,6 %. Ces mesures sont descriptives du script, pas une preuve de performance de paris. Il ne fournit ni cotes horodatées, ni CLV, ni ROI.

Le test ne constitue pas un backtest pré-match valide :

1. Il calcule toutes les prédictions avec `public/nhl_data.csv`, une photo unique dont les lignes équipe indiquent seulement **5 à 7 matchs joués**, puis l’applique aux 175 matchs s’étalant jusqu’au 11 novembre. Cette photo est postérieure aux premières rencontres et déjà périmée pour les dernières; aucune statistique d’équipe n’est reconstruite « connue à la date du match ».
2. Il transmet au modèle le gardien réellement aligné dans la ligne du match cible (`Visitor Goalie` / `Home Goalie` du CSV de résultats). Cette identité n’est pas démontrée comme connue à l’heure d’une prévision pré-match. Le fichier `goalies.csv` contient également des statistiques saisonnières accumulées, sans captures datées pour chaque match évalué.
3. Le filtre ne garde que les résultats en réglementation. Il n’évalue donc pas correctement la probabilité moneyline sur l’ensemble des fins de match incluant prolongation et tirs de barrage.
4. Le script instancie `ScheduleHelper` sans le calendrier requis par son constructeur : la couche de repos/B2B n’est pas testée dans cette exécution.

Le chiffre de 56,6 % n’annule pas ces biais. Un Brier de 0,2419, sur ce petit échantillon sélectionné, ne prouve pas davantage une calibration ni un avantage contre le marché.

## Limites du code et des données

- Les mélanges 60 % L10 / 40 % saison, l’attaque/défense 40/60, les coefficients de régression par tranches de matchs, la correction PDO, l’avantage domicile et la conversion des matchs nuls en victoire de prolongation sont codés comme règles. Leur sélection hors échantillon n’est pas établie.
- Le score de régression et la fonction d’opportunité traduisent des écarts PDO/xG et de spécial teams en « confiance » et « edge » par multiplication fixe. Ces valeurs ne sont pas des probabilités calibrées ni des prix EV.
- Les données d’équipes et de joueurs publiées sont des instantanés CSV sans horodatage de collecte ni protocole point-in-time attaché. Le dépôt mentionne MoneyPuck pour les gardiens titulaires et OddsTrader pour les cotes dans `scripts/fetchData.js`; la provenance, les conditions d’usage et les droits sur chaque CSV historique restent à vérifier.
- Aucun test dédié à `dataProcessing.js`, au modèle Poisson ou aux calculs d’équipe n’a été repéré dans `tests/`. `npm run lint` échoue sur **1 685 erreurs et 25 avertissements** dans le dépôt; ce constat couvre l’ensemble du projet, pas seulement le module NHL.
- La fonction Poisson énumère les scores jusqu’à 10 buts et partage les égalités avec une règle heuristique de prolongation. Les conséquences de la masse de probabilité tronquée et de cette approximation ne sont pas publiées.

## Pistes cataloguées et décision

Une seule fiche retient la combinaison de xG 5v5/jeu de puissance, de forme récente et de shrinkage dépendant du nombre de matchs. Elle est marquée **À étudier**, avec une réimplémentation indépendante et des entrées gelées dans le temps comme condition préalable. Les idées générales de PDO et de gardien recoupent déjà les fiches NHL existantes; elles ne sont pas dupliquées en lignes de catalogue.

Avant tout nouvel essai : constituer des snapshots xG et gardiens antérieurs à chaque match, séparer saisons d’entraînement et de test, garder toutes les issues moneyline, comparer au marché sans marge sur les mêmes matchs et publier Brier/log-loss, CLV, ROI aux prix réellement accessibles et incertitude. Aucun argument n’établit une rentabilité à ce stade.

## Références examinées

- [README source](https://github.com/dpk1212/nhl-savant/blob/0dc9ca79275549c8a83e91ddc9d9b8f28c9804b1/README.md)
- [Calculs xG et probabilités](https://github.com/dpk1212/nhl-savant/blob/0dc9ca79275549c8a83e91ddc9d9b8f28c9804b1/src/utils/dataProcessing.js)
- [Processeur de gardiens](https://github.com/dpk1212/nhl-savant/blob/0dc9ca79275549c8a83e91ddc9d9b8f28c9804b1/src/utils/goalieProcessor.js)
- [Test de précision 2025–26](https://github.com/dpk1212/nhl-savant/blob/0dc9ca79275549c8a83e91ddc9d9b8f28c9804b1/scripts/test2025Accuracy.js)
- [CSV équipe utilisé par le test](https://github.com/dpk1212/nhl-savant/blob/0dc9ca79275549c8a83e91ddc9d9b8f28c9804b1/public/nhl_data.csv)
- [Résultats et gardiens utilisés](https://github.com/dpk1212/nhl-savant/blob/0dc9ca79275549c8a83e91ddc9d9b8f28c9804b1/public/nhl-202526-asplayed.csv)
