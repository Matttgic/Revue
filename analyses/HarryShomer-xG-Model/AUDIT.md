# Revue ciblée — HarryShomer/xG-Model

**Avis : Modèle xG historique (2007-2016) bien documenté ; découpage aléatoire des tirs et absence de licence.**

- Source : https://github.com/HarryShomer/xG-Model
- Version examinée : [`4477d4ef8141d55008b9122017b740097e8ade3b`](https://github.com/HarryShomer/xG-Model/tree/4477d4ef8141d55008b9122017b740097e8ade3b) ; branche `master` ; dernier commit le 2018-05-05.
- Consultation : 2026-10-12.
- Famille : Hockey NHL · expected goals ; stack : Python.
- Priorité de recherche : **P3** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : **Aucune licence** pour le code de l'auteur.

## Ce que la source permet d'établir

- Variables documentées : distance, angle, type de tir, tir du côté opposé, filet vide, supériorité, score, poste, domicile, changement de distance/angle, temps depuis l'événement précédent.
- Log-loss publiée : LR 0,213, RF 0,209, GBM 0,207.

## Limites et points à contrôler

- `train_test_split(..., test_size=.2, random_state=42)` sur les tirs : des tirs du même match et de la même saison sont dans les deux ensembles.
- Le dépôt embarque `thinkbayes2.py`/`thinkplot.py` d'un autre auteur.
- Dernier commit en mai 2018.

## Enseignement pour Revue

Liste de variables xG utile ; à ré-estimer par saisons séparées avant tout usage pré-match.

**Comparaison avec le catalogue :** Recoupe hockeyR (mêmes familles de variables) ; deux sources concordantes sur rebond et rush.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture du README et de `xg_model.py`. Non exécuté.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/HarryShomer/xG-Model/blob/4477d4ef8141d55008b9122017b740097e8ade3b/README.md)
- [xg_model.py](https://github.com/HarryShomer/xG-Model/blob/4477d4ef8141d55008b9122017b740097e8ade3b/xg_model.py)
- [clean_data.py](https://github.com/HarryShomer/xG-Model/blob/4477d4ef8141d55008b9122017b740097e8ade3b/clean_data.py)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
