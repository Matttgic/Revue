# REV-ANDREW-01 — Variables MLB xFIP, K-BB% et xwOBA

- **Sport / marché :** MLB, moneyline; variables de prévision pré-match, pas une stratégie de mise
- **Source :** [andrewkemmer/sports_prediction_model](https://github.com/andrewkemmer/sports_prediction_model), commit [`3febd52512234730070b0788f003a84f9cae5c48`](https://github.com/andrewkemmer/sports_prediction_model/commit/3febd52512234730070b0788f003a84f9cae5c48)
- **Statut :** À étudier
- **Licence source :** absente; aucune reprise de code ou de données

## Idée

Tester, comme familles séparées dans un modèle pré-match MLB :

1. **xFIP des lanceurs et de la relève**, `xFIP = (13 × HR_estimés + 3 × BB − 2 × K) / IP + 3,10`, avec `HR_estimés = FB × taux HR/FB de ligue` disponible avant le match; le code du dépôt décale les historiques et applique des fenêtres/staleness gates.
2. **K-BB% de la relève**, `(strikeouts − buts sur balles) / batteurs affrontés`, régularisé vers le taux de ligue point-in-time selon l'exposition observée (le dépôt indique `k = 93,3` lancers, soit environ 20 % d'une saison moyenne de releveur).
3. **xwOBA de frappeurs par pool de position et catégorie de lancer** (fastball, breaking, offspeed), croisée avec les catégories de lancers utilisées par le lanceur adverse.

Chaque famille doit être jointe uniquement avec les événements antérieurs à l'heure de décision. Les identifiants de lanceur, saisons, équipes et apparitions doivent borner explicitement les fenêtres; un simple tri global par date ne suffit pas, surtout lors de doubleheaders.

## Ce que la source étaye

L'audit de livraison vérifie la présence et la couverture des colonnes, les égalités `diff = home − away`, l'absence de valeurs infinies et la cohérence des fenêtres. Les familles xFIP/K-BB% passent aussi par des tests de décalage et de prior de ligue. C'est une preuve de construction et d'intégrité dans les artefacts examinés, pas une preuve d'amélioration des prévisions.

La comparaison xFIP contre ERA sur trois seeds ne franchit pas le gate annoncé : le log-loss est meilleur de `0,000100` et `0,000053` sur deux seeds, mais pire de `0,000206` sur la troisième; le gain moyen échoue au seuil de bruit préétabli. Le verdict du rapport est `KEEP ERA`. Le scénario xFIP + K-BB% rapporte un log-loss de `0,682343` contre `0,681995` pour ERA sur un seul seed, puis est adopté par décision du propriétaire. Une livraison suivante ne montre pas de changement mesurable.

## Test proposé dans Revue

1. Partir du modèle MLB Revue comme référence inchangée et ajouter une seule famille à la fois : xFIP, K-BB%, puis interaction xwOBA.
2. Apparier les événements et conserver le même découpage temporel, les mêmes seeds et les mêmes hyperparamètres dans chaque bras; calculer des intervalles appariés par blocs de dates.
3. Vérifier les valeurs sources et leur disponibilité exacte avant le premier lancer; exclure les résultats du jour des états Elo et des statistiques historiques tant que leur heure de règlement n'est pas établie.
4. Fixer avant exécution les seuils de log-loss/Brier/calibration exigés pour l'ajout. Une amélioration d'une seed ou d'une fenêtre ne suffit pas.
5. Garder les meilleures cotes et clôtures réelles hors des variables de modèle, mais les recueillir pour un test de calibration, de CLV et de ROI distinct.

**Décision :** bonne piste de variables spécialisées pour la MLB; gain prédictif non établi et aucune preuve de rentabilité. Ne pas adopter directement la combinaison xFIP/K-BB% de la source, dont le comparatif disponible est négatif ou sous-puissant.
