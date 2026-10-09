# REV-NCSUN-01 — Écarter la réussite aux tirs temporairement atypique

**Statut : À étudier — documentation uniquement; modèle non reproduit.**

- **Sport :** basketball universitaire américain (NCAAB)
- **Marchés :** handicaps (spreads), totaux
- **Origine :** https://github.com/mkboggs92-cloud/ncsun/blob/main/sports/ncaab.js
- **Auteur source :** mkboggs92-cloud ; licence non spécifiée; pas de code copié
- **ANJ / France :** autorisation exacte de la compétition et des marchés à vérifier

## Hypothèse

Les lignes de handicaps peuvent accorder trop d'importance aux résultats récents d'équipes ayant bénéficié d'un pourcentage de tirs anormalement élevé, parfois dû à un bruit statistique. Estimer l'écart entre réussite observée et attendue, puis recouper avec des modèles de performance plus globaux.

## Données nécessaires

Tirs et tentatives par zone (près du cercle / mi-distance / trois points), résultats successifs, niveaux d'attaque et de défense, ratings pré-saison datés, historique de cotes à l'heure retenue, fermeture des marchés, terrain neutre, nombre de matchs joués.

## Schéma d'une reconstruction originale

1. Préparer, pour chaque date, des statistiques d'équipe qui excluent le match à prévoir.
2. Estimer une réussite attendue par zone, avec lissage vers un taux de référence historique.
3. Calculer l'écart observé/attendu séparément pour attaque et défense.
4. Mesurer les variations de force selon les ratings pré-saison et courants, enregistrés avant le match.
5. Construire plusieurs prédicteurs (régression régularisée et modèles non linéaires), puis normaliser leurs sorties sur périodes d'apprentissage passées.
6. N'envisager un pari que si le sens du signal de régression et celui du prédicteur sont compatibles. Seuls les prix existant réellement à l'heure retenue sont éligibles.
7. Garder hors apprentissage les saisons d'évaluation et limiter les paris corrélés sur un même match.

**Précision :** le dépôt décrit des ensembles LightGBM/ridge et des filtres de sélection, sans publier le moteur qui calcule réellement les prédictions. Les paramètres visibles ne suffisent pas à reproduire les performances.

## Performance rapportée

Source `ncaab_backtest.json` : **2 476** paris, **1 420** gagnés, **+228,92 unités**, soit **+9,25 % ROI** recalculé sur les profits publiés. Il s'agit uniquement de l'historique annoncé. L'auteur indique avoir ajusté des seuils et limites de sélection sur ces mêmes saisons, ce qui favorise le backtest.

## Conditions pour être promue dans Revue

Jeu de données obtenu légalement, preuve que toutes les features précèdent le pari, entraînement walk-forward, contrôle du choix des seuils sur validation distincte, cotes d'opérateurs français disponibles, coûts/limites/ROI/CLV et variance observés en suivi prospectif.

**Verdict :** concept pertinent à tester; pas de preuve transférable de rentabilité.
