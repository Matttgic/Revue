# Revue ciblée — lucasmaystre/kickscore

**Avis : Généralisation solide d'Elo/TrueSkill à des forces qui évoluent dans le temps ; à n'utiliser en backtest qu'en mode filtrage, jamais avec le lissage par défaut.**

- Source : https://github.com/lucasmaystre/kickscore
- Version examinée : [`d8e6c1a58b71d950bc41e7cb672b93b85a02e7a2`](https://github.com/lucasmaystre/kickscore/tree/d8e6c1a58b71d950bc41e7cb672b93b85a02e7a2) ; branche `master` ; dernier commit le 2025-09-05.
- Consultation : 2026-10-12.
- Famille : Multi-sports · classements dynamiques ; stack : Python.
- Priorité de recherche : **P1** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : MIT.

## Ce que la source permet d'établir

- Modèles d'observation binaire, ternaire (nul avec marge), différence de score (gaussien), comptage Poisson et différence Skellam : un même cadre couvre victoire, 1N2 et scores.
- Noyaux temporels combinables (constant, Wiener, Matérn 3/2 et 5/2, exponentiel, périodique, affine) : la vitesse de variation de la force est un hyperparamètre estimable, pas un K d'Elo fixé à la main.
- `RecursiveFitter` fait un passage avant (filtre de Kalman) **puis un passage arrière (lissage RTS)**. Après `model.fit()` sur tout l'historique, la force estimée à une date passée utilise les matchs postérieurs.
- Publication KDD 2019 (Maystre, Kristof, Grossglauser) et tests unitaires dans le dépôt ; version 0.2.0, Python ≥ 3,10.

## Limites et points à contrôler

- Un backtest naïf (ajuster une fois, puis interroger `probabilities(..., t)` pour chaque match passé) est contaminé par le futur. Il faut réajuster avec les seules observations antérieures à chaque date, ce qui coûte cher.
- Le carnet NBA illustre l'histoire des forces, pas une performance de pari.
- Pas de comparaison au marché fournie.

## Enseignement pour Revue

Tester kickscore comme alternative à l'Elo Revue sur NHL et football, en ré-ajustement glissant strictement antérieur. Fiche : [REV-KICKSCORE-01](REV-KICKSCORE-01_filtrage-vs-lissage.md).

**Comparaison avec le catalogue :** Complète l'Elo de Clairvoyance et de Revue (`REV-CLAIR-08`, `REV-MOD-NHL-01`) : la dynamique est apprise. Recoupe [tennis-crystal-ball](../tennis-crystal-ball/AUDIT.md) pour les forces variables dans le temps.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture ciblée de `model.py`, `fitter/recursive.py`, `observation/*`. Aucun ajustement exécuté.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/lucasmaystre/kickscore/blob/d8e6c1a58b71d950bc41e7cb672b93b85a02e7a2/README.md)
- [LICENSE](https://github.com/lucasmaystre/kickscore/blob/d8e6c1a58b71d950bc41e7cb672b93b85a02e7a2/LICENSE)
- [kickscore/model.py](https://github.com/lucasmaystre/kickscore/blob/d8e6c1a58b71d950bc41e7cb672b93b85a02e7a2/kickscore/model.py)
- [kickscore/fitter/recursive.py](https://github.com/lucasmaystre/kickscore/blob/d8e6c1a58b71d950bc41e7cb672b93b85a02e7a2/kickscore/fitter/recursive.py)
- [kickscore/observation/poisson.py](https://github.com/lucasmaystre/kickscore/blob/d8e6c1a58b71d950bc41e7cb672b93b85a02e7a2/kickscore/observation/poisson.py)
- [pyproject.toml](https://github.com/lucasmaystre/kickscore/blob/d8e6c1a58b71d950bc41e7cb672b93b85a02e7a2/pyproject.toml)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
