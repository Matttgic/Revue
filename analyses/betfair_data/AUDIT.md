# Revue ciblée — tarb/betfair_data

**Avis : Utile si le volume d’historiques devient le goulot d’étranglement.**

- Source demandée : https://github.com/tarb/betfair_data
- URL résolue : https://github.com/tarb/betfair_data
- Version examinée : [`5babe169ef625c193bec405580eaf04daaeb6e5e`](https://github.com/tarb/betfair_data/tree/5babe169ef625c193bec405580eaf04daaeb6e5e) ; branche `master`.
- Consultation : 2026-10-11.
- Famille : Multi-sports · parsing d’historiques exchange ; stack : Rust / Python.
- Priorité de recherche : **P2** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **MIT** ([texte à cette version](https://github.com/tarb/betfair_data/blob/5babe169ef625c193bec405580eaf04daaeb6e5e/LICENSE)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Parse les flux historiques Betfair, archives tar/zip et fichiers compressés ; modes mutable, immutable et compatibilité betfairlightweight.
- La représentation mutable réutilise des objets de marché entre mises à jour ; le code de l’itérateur est exposé via PyO3.
- Le README publie des comparaisons de vitesse sur trois mois de courses australiennes.

## Limites et points à contrôler

- Les chiffres de vitesse sont ceux de l’auteur, non reproduits sur cette machine.
- Ne pas conserver de simples références à un état mutable comme si c’était un snapshot figé ; copier les champs requis ou utiliser une représentation adaptée.
- Le parseur ne fournit ni données licenciées ni stratégie.

## Enseignement pour Revue

Stocker des snapshots immuables de champs utiles et mesurer le coût du parsing avant toute optimisation.

**Comparaison avec le catalogue :** Complète betfairlightweight/flumine, sans ajouter un signal prédictif.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Itérateur mutable lu ; compilation et benchmarks non exécutés.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/tarb/betfair_data/blob/5babe169ef625c193bec405580eaf04daaeb6e5e/README.md)
- [src/mutable/file.rs](https://github.com/tarb/betfair_data/blob/5babe169ef625c193bec405580eaf04daaeb6e5e/src/mutable/file.rs)
- [Cargo.toml](https://github.com/tarb/betfair_data/blob/5babe169ef625c193bec405580eaf04daaeb6e5e/Cargo.toml)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
