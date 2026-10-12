# Revue ciblée — OpenDebates/openskill.py

**Avis : Alternative ouverte à TrueSkill pour équipes et compétitions à plusieurs participants ; son banc d'essai mélange le temps.**

- Source : https://github.com/OpenDebates/openskill.py
- Version examinée : [`65a675d21d9a0d5405731385e83be9aa781537ec`](https://github.com/OpenDebates/openskill.py/tree/65a675d21d9a0d5405731385e83be9aa781537ec) ; branche `main` ; dernier commit le 2026-02-12.
- Consultation : 2026-10-12.
- Famille : Multi-sports · classements multijoueurs ; stack : Python.
- Priorité de recherche : **P3** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : MIT.

## Ce que la source permet d'établir

- Cinq modèles Weng-Lin (Plackett-Luce, Bradley-Terry et Thurstone-Mosteller complets/partiels), équipes asymétriques, nuls, marges de score, poids.
- Article JOSS (doi 10.21105/joss.05901), couverture de tests annoncée à 100 %.
- Le banc `benchmark/benchmark.py` utilise `KFold(shuffle=True)` : les matchs de test sont tirés au hasard dans toute la chronologie et la mesure est l'exactitude.

## Limites et points à contrôler

- Banc d'essai non chronologique et sans probabilité calibrée : ne dit rien de la valeur prédictive en pari.
- Les joueurs absents de l'entraînement sont ignorés au test, ce qui flatte le score.

## Enseignement pour Revue

Piste pour les courses (hippisme, F1, golf) et les sports à composition d'équipe changeante ; à évaluer en walk-forward.

**Comparaison avec le catalogue :** Complète kickscore et elote ; même famille que TrueSkill.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture du README et du banc d'essai. Non exécuté.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/OpenDebates/openskill.py/blob/65a675d21d9a0d5405731385e83be9aa781537ec/README.md)
- [LICENSE](https://github.com/OpenDebates/openskill.py/blob/65a675d21d9a0d5405731385e83be9aa781537ec/LICENSE)
- [benchmark/benchmark.py](https://github.com/OpenDebates/openskill.py/blob/65a675d21d9a0d5405731385e83be9aa781537ec/benchmark/benchmark.py)
- [openskill/models/weng_lin/plackett_luce.py](https://github.com/OpenDebates/openskill.py/blob/65a675d21d9a0d5405731385e83be9aa781537ec/openskill/models/weng_lin/plackett_luce.py)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
