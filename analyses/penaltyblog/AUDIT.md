# Revue ciblée — martineastwood/penaltyblog

**Avis : Premier choix pour un banc comparatif football ; backtest financier à encadrer.**

- Source demandée : https://github.com/martineastwood/penaltyblog
- URL résolue : https://github.com/martineastwood/penaltyblog
- Version examinée : [`6a51173454cba172f2e7b2d8374c1770f257b86a`](https://github.com/martineastwood/penaltyblog/tree/6a51173454cba172f2e7b2d8374c1770f257b86a) ; branche `master`.
- Consultation : 2026-10-11.
- Famille : Football · modèles et probabilités ; stack : Python / Cython.
- Priorité de recherche : **P1** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **MIT** ([texte à cette version](https://github.com/martineastwood/penaltyblog/blob/6a51173454cba172f2e7b2d8374c1770f257b86a/LICENCE)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Bibliothèque de Poisson, Dixon–Coles, Poisson bivarié et variantes bayésiennes ; plusieurs méthodes de retrait de marge dans une API commune.
- Le backtest sélectionne les matchs antérieurs à la date courante pour le trainer, puis traite les rencontres du jour une par une.
- Account.place_bet reçoit le résultat et met immédiatement à jour la bankroll. Un contrôle isolé confirme : 100 unités, mise 10 à cote 2 gagnante → 110 immédiatement.

## Limites et points à contrôler

- Le filtrage journalier du trainer ne garantit pas la causalité des variables déjà calculées ni celle des mises. Si la stratégie utilise la bankroll courante, un résultat du jour peut financer un autre pari avant son règlement réel.
- Les annonces de maturité du README ne remplacent pas une validation indépendante ; modèles bayésiens et compilation Cython non exécutés.

## Enseignement pour Revue

Comparer les familles sur les mêmes fenêtres chronologiques et les mêmes cotes ; distinguer benchmark probabiliste et compte de règlement.

**Comparaison avec le catalogue :** Complète sports-model et wowza-betting par une bibliothèque commune ; confirme le besoin de règlement différé déjà relevé dans sports-betting.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Contrôle isolé de Account exécuté ; aucun entraînement, aucune suite complète ni rentabilité reproduite.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/martineastwood/penaltyblog/blob/6a51173454cba172f2e7b2d8374c1770f257b86a/README.md)
- [penaltyblog/implied/implied.py](https://github.com/martineastwood/penaltyblog/blob/6a51173454cba172f2e7b2d8374c1770f257b86a/penaltyblog/implied/implied.py)
- [penaltyblog/backtest/backtest.py](https://github.com/martineastwood/penaltyblog/blob/6a51173454cba172f2e7b2d8374c1770f257b86a/penaltyblog/backtest/backtest.py)
- [penaltyblog/backtest/account.py](https://github.com/martineastwood/penaltyblog/blob/6a51173454cba172f2e7b2d8374c1770f257b86a/penaltyblog/backtest/account.py)
- [penaltyblog/models/dixon_coles.py](https://github.com/martineastwood/penaltyblog/blob/6a51173454cba172f2e7b2d8374c1770f257b86a/penaltyblog/models/dixon_coles.py)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
