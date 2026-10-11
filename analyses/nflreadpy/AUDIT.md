# Revue ciblée — nflverse/nflreadpy

**Avis : Point d’entrée Python intéressant pour uniformiser les données NFL.**

- Source demandée : https://github.com/nflverse/nflreadpy
- URL résolue : https://github.com/nflverse/nflreadpy
- Version examinée : [`e7e87b2ef626b8672279db25432b1554ee13348a`](https://github.com/nflverse/nflreadpy/tree/e7e87b2ef626b8672279db25432b1554ee13348a) ; branche `main`.
- Consultation : 2026-10-11.
- Famille : NFL · client de données ; stack : Python / Polars.
- Priorité de recherche : **P1** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **MIT pour le code ; données généralement CC-BY-4.0, FTN CC-BY-SA-4.0 selon README** ([texte à cette version](https://github.com/nflverse/nflreadpy/blob/e7e87b2ef626b8672279db25432b1554ee13348a/LICENSE.md)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Chargement de play-by-play, effectifs, snaps, statistiques, blessures et données avancées ; cache mémoire ou disque.
- load_pbp construit les chemins annuels des releases nflverse-data et autorise les saisons depuis 1999.
- Le README marque le projet expérimental ; la présence de load_injuries n’atteste pas la disponibilité de chaque année.

## Limites et points à contrôler

- La concaténation souple facilite les changements de schéma mais exige de vérifier types et valeurs manquantes.
- Snapshots de blessures, depth charts et disponibilité doivent être datés ; les résultats/snap counts ne sont connus qu’après le match.
- Aucun téléchargement annuel ni état de fraîcheur des flux n’a été validé.

## Enseignement pour Revue

Centraliser identifiants et versions des données NFL avant de comparer les différents modèles déjà accumulés.

**Comparaison avec le catalogue :** Complète Stat-Seer, nfl-betting-model et nfl-sports-betting ; ces trois analyses ne doivent pas être fusionnées.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Loaders et accès au downloader lus ; clients externes non exécutés.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/nflverse/nflreadpy/blob/e7e87b2ef626b8672279db25432b1554ee13348a/README.md)
- [src/nflreadpy/load_pbp.py](https://github.com/nflverse/nflreadpy/blob/e7e87b2ef626b8672279db25432b1554ee13348a/src/nflreadpy/load_pbp.py)
- [src/nflreadpy/load_injuries.py](https://github.com/nflverse/nflreadpy/blob/e7e87b2ef626b8672279db25432b1554ee13348a/src/nflreadpy/load_injuries.py)
- [src/nflreadpy/downloader.py](https://github.com/nflverse/nflreadpy/blob/e7e87b2ef626b8672279db25432b1554ee13348a/src/nflreadpy/downloader.py)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
