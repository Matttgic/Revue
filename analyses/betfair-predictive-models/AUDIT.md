# Revue ciblée — betfair-datascientists/predictive-models

**Avis : Tutoriels officiels Betfair utiles pour la structure (variables décalées, baseline marché) ; le modèle EPL publié reste derrière les cotes et contient deux erreurs.**

- Source : https://github.com/betfair-datascientists/predictive-models
- Version examinée : [`2c804f50b143ef3e9e6108171219b59ed15ebb2a`](https://github.com/betfair-datascientists/predictive-models/tree/2c804f50b143ef3e9e6108171219b59ed15ebb2a) ; branche `master` ; dernier commit le 2022-02-22.
- Consultation : 2026-10-12.
- Famille : Football / AFL / rugby · tutoriels de modèles ; stack : Python / R.
- Priorité de recherche : **P2** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : **Aucune licence** dans le dépôt.

## Ce que la source permet d'établir

- Les variables EMA/rolling sont décalées (`shift(1)`) : pas de fuite de résultat dans les moyennes glissantes AFL et EPL.
- Le tutoriel compare explicitement le modèle à la log-loss des cotes : EPL 2017/18, modèle 0,9577 contre 0,9464 pour les cotes. Le marché reste meilleur.
- **Erreur 1** : la cellule de test ajuste `test_lr` sur toutes les saisons, puis prédit avec `lr` (ajusté sans 2016/17). Le score de test publié ne correspond pas au modèle annoncé.
- **Erreur 2** : `gameId` (indice croissant dans le temps) est inclus dans la matrice de variables `['gameId'] + feature_list`.
- Les valeurs Transfermarkt par saison (`marketValues.csv`) n'ont pas de date de capture : une valeur de fin de saison utilisée en début de saison serait une fuite.

## Limites et points à contrôler

- La validation croisée `StratifiedKFold` sans ordre temporel mélange les saisons pendant le réglage.
- Pas de licence : ne rien recopier (code, données, modèles sérialisés).
- Dernier commit en février 2022.

## Enseignement pour Revue

Garder la structure pédagogique (baseline cote, variables décalées) et vérifier systématiquement que l'objet évalué est celui qui a été ajusté.

**Comparaison avec le catalogue :** Confirme le constat du catalogue : un modèle de résultats simple ne bat pas le marché ([ProphitBet](../ProphitBet-Soccer-Bets-Predictor/AUDIT.md), [nba-betting](../nba-betting/AUDIT.md)). Ajoute un contre-exemple de variable identifiant (`gameId`).

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture de `epl/data_preparation_functions.py`, `afl/afl_feature_creation_v2.py` et des cellules et sorties enregistrées des carnets EPL 03 et AFL 03. Rien n'a été ré-exécuté.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/betfair-datascientists/predictive-models/blob/2c804f50b143ef3e9e6108171219b59ed15ebb2a/README.md)
- [epl/data_preparation_functions.py](https://github.com/betfair-datascientists/predictive-models/blob/2c804f50b143ef3e9e6108171219b59ed15ebb2a/epl/data_preparation_functions.py)
- [epl/03. Model Building & Hyperparameter Tuning.ipynb](https://github.com/betfair-datascientists/predictive-models/blob/2c804f50b143ef3e9e6108171219b59ed15ebb2a/epl/03.%20Model%20Building%20&%20Hyperparameter%20Tuning.ipynb)
- [afl/afl_feature_creation_v2.py](https://github.com/betfair-datascientists/predictive-models/blob/2c804f50b143ef3e9e6108171219b59ed15ebb2a/afl/afl_feature_creation_v2.py)
- [afl/03. afl_modelling.ipynb](https://github.com/betfair-datascientists/predictive-models/blob/2c804f50b143ef3e9e6108171219b59ed15ebb2a/afl/03.%20afl_modelling.ipynb)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
