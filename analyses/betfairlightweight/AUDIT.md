# Revue ciblée — betcode-org/betfair

**Avis : Bonne brique pour lire et rejouer les marchés exchange.**

- Source demandée : https://github.com/betcode-org/betfair
- URL résolue : https://github.com/betcode-org/betfair
- Version examinée : [`b00072113e9a1017d5b9cc705e9d1d3444a91036`](https://github.com/betcode-org/betfair/tree/b00072113e9a1017d5b9cc705e9d1d3444a91036) ; branche `master`.
- Consultation : 2026-10-11.
- Famille : Multi-sports · marché exchange et historique ; stack : Python.
- Priorité de recherche : **P1** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **MIT pour le code ; conditions Betfair séparées** ([texte à cette version](https://github.com/betcode-org/betfair/blob/b00072113e9a1017d5b9cc705e9d1d3444a91036/LICENSE)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Wrapper API-NG avec flux de marchés et d’ordres ; caches et générateurs pour historiques.
- L’interface historique permet de réutiliser les objets de marché du streaming pour le backtest.
- Le README précise les prérequis du live : compte, app key et certificats pour le mode non interactif.

## Limites et points à contrôler

- La bibliothèque ne fournit ni stratégie ni accès gratuit garanti à tous les historiques.
- Une cote vue ne garantit pas le volume disponible à cette cote ni l’exécution de la mise.
- Aucune connexion à un compte, souscription ou opération de pari effectuée.

## Enseignement pour Revue

Définir un format commun de snapshots et de replay pour comparer la décision et la liquidité accessible.

**Comparaison avec le catalogue :** Complète flumine et les idées de registre/CLV déjà présentes ; pas une source indépendante de signal.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

README et modules de streaming repérés ; inspection documentaire, aucun client exécuté.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/betcode-org/betfair/blob/b00072113e9a1017d5b9cc705e9d1d3444a91036/README.md)
- [betfairlightweight/streaming/stream.py](https://github.com/betcode-org/betfair/blob/b00072113e9a1017d5b9cc705e9d1d3444a91036/betfairlightweight/streaming/stream.py)
- [betfairlightweight/endpoints/streaming.py](https://github.com/betcode-org/betfair/blob/b00072113e9a1017d5b9cc705e9d1d3444a91036/betfairlightweight/endpoints/streaming.py)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
