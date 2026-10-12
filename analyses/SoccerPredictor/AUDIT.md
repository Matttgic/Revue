# Revue ciblée — jkrusina/SoccerPredictor

**Avis : « Profit 1 069 %, ROI 33,4 % » sur 32 paris : résultat contaminé par la sélection des poids sur le jeu de test. Archiver.**

- Source : https://github.com/jkrusina/SoccerPredictor
- Version examinée : [`71c66e85504d206e815e86b031dbc9a3c41e1008`](https://github.com/jkrusina/SoccerPredictor/tree/71c66e85504d206e815e86b031dbc9a3c41e1008) ; branche `master` ; dernier commit le 2019-12-09.
- Consultation : 2026-10-12.
- Famille : Football · double chance, réseaux récurrents par équipe ; stack : Python.
- Priorité de recherche : **Rejet** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : **Aucune licence**.

## Ce que la source permet d'établir

- Pour les équipes de test, `_on_epoch_end` enregistre les meilleurs paramètres quand les métriques **de test** s'améliorent (`snapshot.record_best_params`), puis les prédictions finales sont refaites avec `revert_to_best_params=True`.
- Le résultat mis en avant porte sur 32 paris en 113 jours, le meilleur de plusieurs exécutions.
- Le jeu de données n'est pas publié : impossible de reproduire.

## Limites et points à contrôler

- Échantillon minuscule et sélectionné ; aucune comparaison à la cote de clôture.

## Enseignement pour Revue

Contre-exemple pour la règle de décision Revue : le choix d'époque ou de poids doit se faire hors de l'échantillon rapporté.

**Comparaison avec le catalogue :** Même défaut que [ProphitBet](../ProphitBet-Soccer-Bets-Predictor/AUDIT.md) et [wowza-betting](../wowza-betting/AUDIT.md) (holdout utilisé pour la sélection).

**Décision :** archiver comme contre-exemple ; aucune méthode retenue ([REV-KRUSINA-01](../../archives/REV-KRUSINA-01_soccerpredictor.md)).

## Niveau de preuve

Lecture de `trainer/trainer.py` et `trainer/model.py`.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/jkrusina/SoccerPredictor/blob/71c66e85504d206e815e86b031dbc9a3c41e1008/README.md)
- [soccerpredictor/trainer/trainer.py](https://github.com/jkrusina/SoccerPredictor/blob/71c66e85504d206e815e86b031dbc9a3c41e1008/soccerpredictor/trainer/trainer.py)
- [soccerpredictor/trainer/model.py](https://github.com/jkrusina/SoccerPredictor/blob/71c66e85504d206e815e86b031dbc9a3c41e1008/soccerpredictor/trainer/model.py)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
