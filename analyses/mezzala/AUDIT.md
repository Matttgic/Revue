# Revue ciblée — Torvaney/mezzala

**Avis : Dixon–Coles lisible et extensible (blocs, poids, regroupement des équipes rares) ; dépôt inactif depuis 2021.**

- Source : https://github.com/Torvaney/mezzala
- Version examinée : [`2c55d136ac3dae2bb86988071396063c3c79ce8c`](https://github.com/Torvaney/mezzala/tree/2c55d136ac3dae2bb86988071396063c3c79ce8c) ; branche `master` ; dernier commit le 2021-10-19.
- Consultation : 2026-10-12.
- Famille : Football · Dixon–Coles modulaire ; stack : Python.
- Priorité de recherche : **P2** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : Apache-2.0.

## Ce que la source permet d'établir

- Les « blocs » séparent force d'équipe, taux de base, avantage domicile et paramètres libres (`KeyBlock`, `ConstantBlock`) : on ajoute un avantage domicile par ligue sans réécrire la vraisemblance.
- Pondération par observation (`ExponentialWeight(epsilon, key)`, `KeyWeight`) : décroissance temporelle ou poids arbitraires (par ex. xG à la place des buts).
- `LumpedAdapter` regroupe les équipes vues moins de N fois sous un même paramètre : utile pour les promus et les petites ligues.
- Le commentaire du code reconnaît que ρ n'est pas contraint ; un ρ trop grand rend τ négatif et la log-vraisemblance indéfinie.

## Limites et points à contrôler

- Dernier commit en octobre 2021, pas de comparaison au marché ni de procédure de choix d'epsilon.
- Même auteur que [regista](../regista/AUDIT.md) : sources non indépendantes.

## Enseignement pour Revue

Reprendre l'architecture (blocs + poids + regroupement) dans le modèle football de Revue. Fiche : [REV-MEZZALA-01](REV-MEZZALA-01_ponderation-et-regroupement.md).

**Comparaison avec le catalogue :** Complète [regista](../regista/AUDIT.md), [penaltyblog](../penaltyblog/AUDIT.md) et [goalmodel](../goalmodel/AUDIT.md). Recoupe dashee87/blogScripts sur la décroissance temporelle.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture de `models.py`, `blocks.py`, `weights.py`, `adapters.py`, README. Aucun ajustement exécuté.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/Torvaney/mezzala/blob/2c55d136ac3dae2bb86988071396063c3c79ce8c/README.md)
- [LICENSE](https://github.com/Torvaney/mezzala/blob/2c55d136ac3dae2bb86988071396063c3c79ce8c/LICENSE)
- [mezzala/models.py](https://github.com/Torvaney/mezzala/blob/2c55d136ac3dae2bb86988071396063c3c79ce8c/mezzala/models.py)
- [mezzala/blocks.py](https://github.com/Torvaney/mezzala/blob/2c55d136ac3dae2bb86988071396063c3c79ce8c/mezzala/blocks.py)
- [mezzala/weights.py](https://github.com/Torvaney/mezzala/blob/2c55d136ac3dae2bb86988071396063c3c79ce8c/mezzala/weights.py)
- [mezzala/adapters.py](https://github.com/Torvaney/mezzala/blob/2c55d136ac3dae2bb86988071396063c3c79ce8c/mezzala/adapters.py)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
