# Revue ciblée — nflverse/nflverse-data

**Avis : Source structurante ; il faut versionner les fichiers téléchargés en plus du code.**

- Source demandée : https://github.com/nflverse/nflverse-data
- URL résolue : https://github.com/nflverse/nflverse-data
- Version examinée : [`a78da18ca93f167bd0a2af274df48f539fa4153c`](https://github.com/nflverse/nflverse-data/tree/a78da18ca93f167bd0a2af274df48f539fa4153c) ; branche `main`.
- Consultation : 2026-10-11.
- Famille : NFL · publications de données ; stack : R / releases GitHub.
- Priorité de recherche : **P1** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **CC-BY-4.0 à la racine ; exceptions à vérifier par jeu** ([texte à cette version](https://github.com/nflverse/nflverse-data/blob/a78da18ca93f167bd0a2af274df48f539fa4153c/LICENSE.md)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Le dépôt héberge surtout les données dans les releases, organisées par famille de chargement.
- nflverse_upload joint timestamp.txt et timestamp.json et utilise overwrite=TRUE par défaut.
- nflverse_save publie notamment CSV, RDS et Parquet avec métadonnées de type et de date.

## Limites et points à contrôler

- Un SHA du dépôt ne fige pas les fichiers de release qui peuvent être remplacés.
- L’heure de publication d’un export n’est pas l’heure de disponibilité initiale de chaque observation.
- Les jeux eux-mêmes et leur fraîcheur n’ont pas été contrôlés ; ne pas étendre la licence racine aux exceptions FTN.

## Enseignement pour Revue

Archiver URL, date de récupération, taille et SHA256 de chaque asset pour rendre un backtest rejouable.

**Comparaison avec le catalogue :** Complète nflreadpy ; source de données et client sont deux responsabilités distinctes.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Mécanisme de publication lu ; aucune release de données ingérée.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/nflverse/nflverse-data/blob/a78da18ca93f167bd0a2af274df48f539fa4153c/README.md)
- [R/upload.R](https://github.com/nflverse/nflverse-data/blob/a78da18ca93f167bd0a2af274df48f539fa4153c/R/upload.R)
- [LICENSE.md](https://github.com/nflverse/nflverse-data/blob/a78da18ca93f167bd0a2af274df48f539fa4153c/LICENSE.md)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
