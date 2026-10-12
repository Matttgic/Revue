# Revue ciblée — helton-tech/elote

**Avis : Interface unique pour comparer Elo, Glicko, TrueSkill, Bradley-Terry, Colley, Massey, WHR… ; son évaluation gèle les forces pendant toute la période de test.**

- Source : https://github.com/helton-tech/elote
- Version examinée : [`f8904a024adeea9ec1bff3175d24f588fe7f7865`](https://github.com/helton-tech/elote/tree/f8904a024adeea9ec1bff3175d24f588fe7f7865) ; branche `master` ; dernier commit le 2026-10-11.
- Consultation : 2026-10-12.
- Famille : Multi-sports · comparaison de systèmes de classement ; stack : Python.
- Priorité de recherche : **P2** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : MIT.

## Ce que la source permet d'établir

- Plus d'une douzaine de systèmes derrière la même interface (`expected_score`, `beat`, `tied`), sérialisation et carnets d'exemple.
- `time_split` trie par date, mais place les matchs **sans date** dans l'entraînement et bascule silencieusement sur un découpage aléatoire si aucune date n'existe.
- `evaluate_arena_with_dataset` prédit tout l'ensemble de test **sans mettre à jour** les forces, et ignore les compétiteurs absents de l'entraînement (avec un avertissement).

## Limites et points à contrôler

- Gel des forces : plus la période de test est longue, plus les forces sont périmées, ce qui ne ressemble pas à l'usage réel (mise à jour après chaque match).
- Exclusion des nouveaux venus : biais de survie dans les métriques.

## Enseignement pour Revue

Bon outil pour un premier tri, à condition d'écrire sa propre boucle « prédire puis mettre à jour ».

**Comparaison avec le catalogue :** Complète kickscore et openskill ; même problème de banc d'essai qu'openskill.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture de `datasets/base.py`, `datasets/utils.py`, `benchmark.py`, README. Non exécuté.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/helton-tech/elote/blob/f8904a024adeea9ec1bff3175d24f588fe7f7865/README.md)
- [LICENSE.md](https://github.com/helton-tech/elote/blob/f8904a024adeea9ec1bff3175d24f588fe7f7865/LICENSE.md)
- [elote/datasets/base.py](https://github.com/helton-tech/elote/blob/f8904a024adeea9ec1bff3175d24f588fe7f7865/elote/datasets/base.py)
- [elote/datasets/utils.py](https://github.com/helton-tech/elote/blob/f8904a024adeea9ec1bff3175d24f588fe7f7865/elote/datasets/utils.py)
- [elote/benchmark.py](https://github.com/helton-tech/elote/blob/f8904a024adeea9ec1bff3175d24f588fe7f7865/elote/benchmark.py)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
