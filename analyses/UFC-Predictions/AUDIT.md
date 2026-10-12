# Revue ciblée — WarrierRajeev/UFC-Predictions

**Avis : Jeu de données UFC très utilisé (Kaggle) et variables cumulées correctement décalées ; évaluation aléatoire, sans cotes.**

- Source : https://github.com/WarrierRajeev/UFC-Predictions
- Version examinée : [`97305528e307623614133d67d1ea09583937afde`](https://github.com/WarrierRajeev/UFC-Predictions/tree/97305528e307623614133d67d1ea09583937afde) ; branche `master` ; dernier commit le 2022-03-14.
- Consultation : 2026-10-12.
- Famille : MMA UFC · classification du vainqueur ; stack : Python.
- Priorité de recherche : **P3** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : **Aucune licence**.

## Ce que la source permet d'établir

- Les statistiques de chaque combattant sont des moyennes exponentielles (span 3) calculées sur `fighter[(i + 1):]`, c'est-à-dire les combats **précédents** si le fichier brut est trié du plus récent au plus ancien (ordre non vérifié ici) ; l'âge est calculé à la date du combat.
- Taille, allonge et garde viennent de la fiche actuelle du combattant (valeur collectée aujourd'hui).
- Évaluation par `train_test_split` aléatoire (10 %) : des combats de 2021 servent à prédire des combats de 2005.
- Résultats : 0,69-0,72 d'exactitude selon les carnets ; le README cite le meilleur (0,7218).

## Limites et points à contrôler

- Le coin rouge est généralement le favori : le modèle apprend largement l'affectation des coins, non comparée au marché.
- Aucune cote, donc aucun test de rentabilité possible.

## Enseignement pour Revue

Données utiles pour l'Elo UFC de Revue (`REV-MOD-IND-02`) ; refaire une évaluation chronologique contre les cotes.

**Comparaison avec le catalogue :** Complète [ncsun](../2026-10-09_mkboggs92-cloud_ncsun.md) (`REV-NCSUN-03`, UFC).

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture de `src/createdata/preprocess.py`, `preprocess_fighter_data.py` et des carnets XGBoost avec leurs sorties enregistrées.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/WarrierRajeev/UFC-Predictions/blob/97305528e307623614133d67d1ea09583937afde/README.md)
- [src/createdata/preprocess.py](https://github.com/WarrierRajeev/UFC-Predictions/blob/97305528e307623614133d67d1ea09583937afde/src/createdata/preprocess.py)
- [src/createdata/preprocess_fighter_data.py](https://github.com/WarrierRajeev/UFC-Predictions/blob/97305528e307623614133d67d1ea09583937afde/src/createdata/preprocess_fighter_data.py)
- [notebooks/xgboost-Oversampled.ipynb](https://github.com/WarrierRajeev/UFC-Predictions/blob/97305528e307623614133d67d1ea09583937afde/notebooks/xgboost-Oversampled.ipynb)
- [notebooks/xgboost-Reshuffled.ipynb](https://github.com/WarrierRajeev/UFC-Predictions/blob/97305528e307623614133d67d1ea09583937afde/notebooks/xgboost-Reshuffled.ipynb)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
