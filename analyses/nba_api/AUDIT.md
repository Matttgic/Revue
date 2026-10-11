# Revue ciblée — swar/nba_api

**Avis : Brique de collecte utile, sans modèle ni avantage prédictif fourni.**

- Source demandée : https://github.com/swar/nba_api
- URL résolue : https://github.com/swar/nba_api
- Version examinée : [`52c0fb0b81c4b785d6cebeb9988799e5d796dfd7`](https://github.com/swar/nba_api/tree/52c0fb0b81c4b785d6cebeb9988799e5d796dfd7) ; branche `master`.
- Consultation : 2026-10-11.
- Famille : NBA · client statistiques et live ; stack : Python.
- Priorité de recherche : **P1** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **MIT pour le client ; conditions NBA.com distinctes** ([texte à cette version](https://github.com/swar/nba_api/blob/52c0fb0b81c4b785d6cebeb9988799e5d796dfd7/LICENSE)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Sépare endpoints statistiques et données live ; documentation des paramètres et réponses.
- PlayerGameLog expose notamment minutes, points, rebonds et date du match, avec filtres DateFrom/DateTo.
- Le README souligne que NBA.com n’annonce pas systématiquement les changements d’endpoints.

## Limites et points à contrôler

- Les statistiques du match cible sont post-match ; filtrer et décaler les moyennes avant toute prédiction.
- Les dates de requête ne constituent pas un historique des révisions ni un journal pré-match des absences.
- Aucun appel NBA effectué ; disponibilité et limites de débit non vérifiées.

## Enseignement pour Revue

Conserver des tables match/joueur stables et séparer données live, résultats et variables disponibles avant match.

**Comparaison avec le catalogue :** Complète nba-betting et NBA-Machine-Learning-Sports-Betting, où la causalité des statistiques était un point sensible.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Endpoint et schéma inspectés ; pas de collecte réelle.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/swar/nba_api/blob/52c0fb0b81c4b785d6cebeb9988799e5d796dfd7/README.md)
- [src/nba_api/stats/endpoints/playergamelog.py](https://github.com/swar/nba_api/blob/52c0fb0b81c4b785d6cebeb9988799e5d796dfd7/src/nba_api/stats/endpoints/playergamelog.py)
- [LICENSE](https://github.com/swar/nba_api/blob/52c0fb0b81c4b785d6cebeb9988799e5d796dfd7/LICENSE)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
