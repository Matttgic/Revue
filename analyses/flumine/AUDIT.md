# Revue ciblée — betcode-org/flumine

**Avis : Candidat prioritaire pour comprendre un backtest avec contraintes d’exécution.**

- Source demandée : https://github.com/betcode-org/flumine
- URL résolue : https://github.com/betcode-org/flumine
- Version examinée : [`bdd4df145179996dd88067b90b3e118c60e4796f`](https://github.com/betcode-org/flumine/tree/bdd4df145179996dd88067b90b3e118c60e4796f) ; branche `master`.
- Consultation : 2026-10-11.
- Famille : Multi-sports · simulation et exécution ; stack : Python.
- Priorité de recherche : **P1** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **MIT** ([texte à cette version](https://github.com/betcode-org/flumine/blob/bdd4df145179996dd88067b90b3e118c60e4796f/LICENSE)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Framework événementiel, paper trading, simulation, ordres et contrôles d’exposition.
- Le simulateur prend en compte des latences de placement/annulation/remplacement et une position estimée dans la file.
- La documentation précise que simulation_available_prices peut compter deux fois la liquidité.

## Limites et points à contrôler

- La simulation estime la file et l’exécution ; elle ne reproduit pas parfaitement l’impact de ses propres ordres.
- Auditer liquidité, commissions, suspensions, non-partants et options de matching avant de lire un profit simulé.
- Les exemples de stratégie sont des démonstrations d’API ; aucun ROI n’est validé ici.

## Enseignement pour Revue

Tester une même stratégie sous plusieurs latences et hypothèses de remplissage, puis comparer au paper trading.

**Comparaison avec le catalogue :** Ajoute une dimension d’exécution au backtest financier et aux méthodes de CLV déjà cataloguées.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Code de simulation et limites documentées examinés ; aucune simulation historique ni connexion live exécutée.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/betcode-org/flumine/blob/bdd4df145179996dd88067b90b3e118c60e4796f/README.md)
- [docs/quickstart.md](https://github.com/betcode-org/flumine/blob/bdd4df145179996dd88067b90b3e118c60e4796f/docs/quickstart.md)
- [docs/advanced.md](https://github.com/betcode-org/flumine/blob/bdd4df145179996dd88067b90b3e118c60e4796f/docs/advanced.md)
- [flumine/simulation/simulatedorder.py](https://github.com/betcode-org/flumine/blob/bdd4df145179996dd88067b90b3e118c60e4796f/flumine/simulation/simulatedorder.py)
- [flumine/execution/simulatedexecution.py](https://github.com/betcode-org/flumine/blob/bdd4df145179996dd88067b90b3e118c60e4796f/flumine/execution/simulatedexecution.py)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
