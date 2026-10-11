# Revue ciblée — pnxenopoulos/awpy

**Avis : Bonne porte d’entrée vers CS2 ; tout le modèle de pari reste à construire.**

- Source demandée : https://github.com/pnxenopoulos/awpy
- URL résolue : https://github.com/pnxenopoulos/awpy
- Version examinée : [`94f3571367012b763d3730d92bb4502b50a89bd8`](https://github.com/pnxenopoulos/awpy/tree/94f3571367012b763d3730d92bb4502b50a89bd8) ; branche `main`.
- Consultation : 2026-10-11.
- Famille : Esport CS2 · demos et variables ; stack : Python / Polars / demoparser2.
- Priorité de recherche : **P3** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **MIT pour le code ; droits des demos séparés** ([texte à cette version](https://github.com/pnxenopoulos/awpy/blob/94f3571367012b763d3730d92bb4502b50a89bd8/LICENSE)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Parse les demos Counter-Strike 2 : ticks, kills, dégâts, grenades, rounds et positions.
- Calcule notamment ADR, KAST et rating ; rating.py utilise des coefficients explicites pour l’impact, avec ventilations par côté.
- Le README avertit de possibles erreurs de parsing, notamment pour les demos POV.

## Limites et points à contrôler

- Rating de performance et probabilité de victoire sont deux objets différents.
- Pour des prévisions futures, agréger seulement les demos passées et tenir compte des changements de roster, carte et version du jeu.
- Aucun corpus de cotes, benchmark de pari ni disponibilité des demos n’a été validé.

## Enseignement pour Revue

Construire des variables par carte et côté, puis comparer à Elo et au marché sur des séries futures.

**Comparaison avec le catalogue :** Ouvre une nouvelle piste esport ; pas de fusion avec les modèles sportifs existants.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Formule d’impact lue ; aucune demo parsée ni performance reproduite.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/pnxenopoulos/awpy/blob/94f3571367012b763d3730d92bb4502b50a89bd8/README.md)
- [awpy/stats/rating.py](https://github.com/pnxenopoulos/awpy/blob/94f3571367012b763d3730d92bb4502b50a89bd8/awpy/stats/rating.py)
- [pyproject.toml](https://github.com/pnxenopoulos/awpy/blob/94f3571367012b763d3730d92bb4502b50a89bd8/pyproject.toml)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
