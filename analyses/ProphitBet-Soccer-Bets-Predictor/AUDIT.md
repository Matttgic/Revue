# Audit — kochlisGit/ProphitBet-Soccer-Bets-Predictor

- **URL originale :** https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor
- **Auteur :** Vasileios Kochliaridis
- **Commit examiné :** `49fb86be553a62ed714acc1e2d99c73f6dcd27ea` (`main`), 16 avril 2026
- **Date de consultation :** 11 octobre 2026
- **Licence du code :** MIT, [LICENSE.txt](https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor/blob/49fb86be553a62ed714acc1e2d99c73f6dcd27ea/LICENSE.txt). La licence du logiciel ne règle pas les droits d'utilisation des données externes ni les conditions du site FootyStats.
- **État :** application active dans son README, dont la version décrit une release du 17 mars 2026. Aucun historique Git ne permet ici d'établir la fréquence réelle de maintenance au-delà du commit audité.
- **Langage / stack :** Python, pandas, scikit-learn, TensorFlow/Keras, PyQt6, XGBoost, Optuna et Selenium.

## Résumé technique

ProphitBet est une application de bureau pour analyser et prédire le football. Elle récupère les résultats, cotes moyennes 1N2 et statistiques de match historiques auprès de football-data.co.uk, calcule des agrégats de forme d'équipe à partir des matchs antérieurs, puis entraîne différents classifieurs. Les cibles proposées sont le résultat domicile/nul/extérieur et plus/moins de 2,5 buts. Les cotes 1N2 font partie des variables explicatives. Pour les prochains matchs, le programme peut lire les affiches de FootyStats via Selenium, rapprocher les noms d'équipes et exporter les prédictions, notamment vers Excel.

L'interface réunit aussi des outils d'analyse exploratoire et de sélection de variables (Boruta, corrélations, coefficients, importance par arbre), de tuning Optuna et d'explication des modèles. C'est un périmètre utile pour expérimenter; ce n'est pas en soi une stratégie de pari distincte.

## Idées identifiées

| Idée | Sport | Marché | Données | Intérêt | Destination envisagée |
|---|---|---|---|---|---|
| Environnement graphique pour explorer les historiques football, les variables de forme et plusieurs familles de classifieurs | Football | 1N2 et O/U 2,5 | football-data.co.uk et flux FootyStats | Utile comme outil d'analyse/benchmark après correction des validations; aucune performance indépendante établie | Audit source seulement; pas de nouvelle entrée de méthode |

## Vérifications

- **Installation et exécution :** application non lancée. La pile complète n'a pas été installée : elle est volumineuse, comprend TensorFlow 2.15.1 et PyQt6, et le README ne dit l'avoir testée que sous Python 3.10/3.11 alors que l'environnement cloud utilise Python 3.12.
- **Installateur :** échec reproduit avec `python install.py --help`. Le module ne se compile pas à cause du chemin Windows `C:\Users\...` écrit dans une chaîne de documentation sans échappement valide (`SyntaxError: unicodeescape`). Le README recommande cet installateur.
- **Tests existants :** aucun fichier de test Python ni suite de tests repéré dans le checkout.
- **Syntaxe statique :** 107 des 108 fichiers Python du dépôt se parsèment avec l'AST Python; le seul échec est `install.py`, reproduit séparément ci-dessus.
- **Données :** aucun CSV historique, fichier Excel de résultats ou base de données de matchs n'est fourni dans Git; l'application dépend de téléchargements externes.
- **Fuites de données / biais :** problème important dans le k-fold et la sélection des hyperparamètres; détails ci-dessous.
- **Licence / crédit :** le code est MIT. `CITATION.cff` est fourni, mais l'orthographe du prénom (`Vasileos`) diffère de celle de la licence (`Vasileios`).
- **Reproductibilité des performances :** aucune preuve de rendement ni de validation indépendante n'a été reproduite. Le README affirme que « Profit Balance » inférieure à l'accuracy implique la rentabilité; le calcul implémenté ne suffit pas à tirer cette conclusion.

## Validité statistique et limites

Le découpage holdout prend les premières lignes d'un tableau trié par date décroissante pour l'évaluation et les lignes plus anciennes pour l'entraînement. Lorsque le prétraitement des statistiques a bien produit cet ordre, cette séparation respecte la chronologie. Les statistiques de forme cumulées excluent aussi explicitement le match courant par décalage (`shift(1)`). Ce sont de bons choix de départ.

Ces garde-fous sont neutralisés dès que le tuning est activé : la fenêtre graphique appelle le tuner sur l'intégralité de `self._df`, puis seulement après le tuning crée le holdout final. Le résultat de ce holdout sert donc à choisir les hyperparamètres avant d'être présenté comme évaluation. L'objectif du tuner utilise en outre `Trainer.cross_validation()`, dont le `StratifiedKFold` mélange les matchs (`shuffle=True`) au lieu de respecter les dates. Les métriques de ce k-fold et le tuning qui en dépend ne sont pas des évaluations prospectives.

Il existe un autre problème dans ce k-fold : `Trainer.cross_validation()` réutilise le même objet modèle à travers les folds. `ClassificationModel.fit()` remplace le type de normaliseur par le scaler ajusté au premier fold; les folds suivants transforment leurs variables avec ce scaler existant au lieu d'en ajuster un nouveau uniquement sur leur propre entraînement. Les résultats peuvent alors dépendre de la distribution d'un autre fold et le prétraitement n'est pas isolé par fold.

La métrique nommée **Profit Balance** simplifie algébriquement à la moyenne des probabilités implicites des cotes sélectionnées, `mean(1 / cote)`. La comparer au taux global de bons pronostics ne donne pas le ROI si les cotes et la performance varient d'un pari à l'autre. Par exemple, sur deux cotes 1,50 et 20,00, un succès seulement sur la cote 1,50 donne 50 % d'accuracy contre environ 35,8 % de « Profit Balance », mais une mise fixe d'une unité sur chaque sélection perd 0,50 unité au total. Le programme n'enregistre pas dans cette métrique les gains/pertes réels par sélection; il ne calcule ni ROI par mise fixe/Kelly, ni CLV, ni incertitude. Les cotes historiques moyennes du fichier ne prouvent pas non plus qu'un prix donné était disponible chez un bookmaker précis au moment de la décision.

Les filtres de cotes et de probabilités permettent d'examiner des sous-groupes, mais choisir les seuils après observation du même holdout crée une sélection a posteriori. Le tableau de métriques porte surtout sur accuracy, F1, précision et rappel; le dépôt ne démontre donc pas que les probabilités sont calibrées ni qu'elles surpassent une baseline de marché hors échantillon.

## Notes d'audit

| Critère | Note | Preuve |
|---|---:|---|
| Utilité de l'idée | NC | Interface d'analyse complète, sans contribution de modélisation distincte mesurée |
| Code | NC | Architecture substantielle inspectée, mais aucune suite automatisée et installateur invalide |
| Données | NC | Sources publiques distantes; aucun jeu de données ou droits de redistribution inclus |
| Validité statistique | NC | Tuning sur le holdout, k-fold aléatoire et normaliseur réutilisé entre folds |
| Testabilité | NC | Aucun test automatisé; le jeu source manque pour reproduire les sorties |
| Maintenance / sécurité | NC | Commit d'avril 2026; installation lourde, scraping Selenium et compatibilité non vérifiés ici |

**Score global : non calculé.** L'application n'a pas été exécutée et son protocole d'évaluation ne justifie pas un score de performance.

## Verdict

**Documenter seulement pour l'instant.** L'application peut servir de tableau de travail exploratoire et ses agrégats de forme antérieurs sont une base raisonnable à étudier. Je ne retiens pas une nouvelle stratégie ni un modèle de pari : les classifieurs proposés sont standards, aucun rendement n'est démontré, et le protocole doit être corrigé avant d'utiliser ses métriques. Pour une évaluation, séparer d'abord tuning et test chronologique, créer un scaler par fold, employer une validation walk-forward non chevauchante, et calculer le rendement réalisé à partir d'une règle de mise et de cotes horodatées disponibles.

## Références examinées

Toutes les références ci-dessous sont épinglées au commit `49fb86be553a62ed714acc1e2d99c73f6dcd27ea` : [README et installation](https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor/blob/49fb86be553a62ed714acc1e2d99c73f6dcd27ea/README.md), [split k-fold et sliding](https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor/blob/49fb86be553a62ed714acc1e2d99c73f6dcd27ea/src/models/trainer.py), [tuning sur le jeu complet](https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor/blob/49fb86be553a62ed714acc1e2d99c73f6dcd27ea/src/gui/windows/models/trainer.py), [objectif du tuner](https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor/blob/49fb86be553a62ed714acc1e2d99c73f6dcd27ea/src/models/tuner.py), [prétraitement du modèle et normalisation](https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor/blob/49fb86be553a62ed714acc1e2d99c73f6dcd27ea/src/models/model.py), [calcul de Profit Balance](https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor/blob/49fb86be553a62ed714acc1e2d99c73f6dcd27ea/src/metrics/balance.py), [affichage et calcul des métriques d'évaluation](https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor/blob/49fb86be553a62ed714acc1e2d99c73f6dcd27ea/src/gui/windows/models/evaluator.py), [préparation des variables](https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor/blob/49fb86be553a62ed714acc1e2d99c73f6dcd27ea/src/preprocessing/dataset.py), [statistiques passées](https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor/blob/49fb86be553a62ed714acc1e2d99c73f6dcd27ea/src/preprocessing/statistics.py), [téléchargement des résultats et cotes](https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor/blob/49fb86be553a62ed714acc1e2d99c73f6dcd27ea/src/network/leagues/downloaders/main.py) et [installateur](https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor/blob/49fb86be553a62ed714acc1e2d99c73f6dcd27ea/install.py).

## Provenance et modifications

Checkout source consulté en lecture seule, sans changement de fichier. Aucun code, jeu de données, modèle entraîné ou secret n'a été importé dans Revue. Seuls ce dossier source et ses liens d'indexation sont ajoutés; les autres dossiers de dépôts restent inchangés.
