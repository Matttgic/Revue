# Audit — sedemmler/WagerBrain

- **URL originale :** [github.com/sedemmler/WagerBrain](https://github.com/sedemmler/WagerBrain)
- **Commit audité :** [`b1cc33f5eb7a6130106bf8251b554718e2d22172`](https://github.com/sedemmler/WagerBrain/commit/b1cc33f5eb7a6130106bf8251b554718e2d22172) (`2020-05-02`)
- **Date d'audit :** 2026-10-11
- **Licence :** aucun fichier de licence n'est présent dans le checkout. Ne pas reprendre son code ou ses données sans clarifier les droits.
- **Maintenance :** dernier commit consulté en 2020; dépôt très ancien au moment de l'audit.
- **Stack :** Python, NumPy et pandas; scraping avec Requests et Beautiful Soup; tests écrits pour pytest.

## Résumé technique

Petit ensemble de fonctions pour convertir les cotes américaines, décimales et fractionnaires, calculer profits, paiements, probabilités implicites, marge bookmaker, EV et répartitions de mise. Le dépôt propose aussi un calculateur d'arbitrage binaire, quelques règles de bankroll (Kelly, Fibonacci et Labouchère), deux fonctions de filtrage rétrospectif de spreads NBA, des scrapers et des fichiers de données historiques.

Le checkout ne contient pas de README, de manifeste de dépendances ni de métadonnées de paquet. La provenance, la méthode de collecte et les conditions d'utilisation des fichiers de données ne sont pas documentées.

## Idées et comparaison avec Revue

| Idée | Apport observé | Comparaison / destination |
|---|---|---|
| Calculer un arbitrage à deux issues en inversant les cotes décimales et en égalisant les retours | Aide arithmétique simple; le résultat présuppose deux issues exhaustives et des prix exécutables simultanément | Même famille de dutching que [REV-PRETR-01](../pretrehr-Sports-betting/REV-PRETR-01_optimisation-promotions-freebets.md); pas de fiche méthode en doublon |
| Convertir plusieurs formats de cote et calculer le seuil de rentabilité | Rappelle de séparer prix, probabilité implicite et profit; quelques cas limites sont incorrects | Intérêt documentaire seulement; vérifier les équations et les frontières avant toute réutilisation |
| Utiliser les historiques d'odds MLB/NBA/NFL et des statistiques d'équipe par saison | CSV NBA (17 801 matchs, 2006–2020), MLB (27 710, 2009–2020), NFL (3 118, 2009–2020); bases d'équipe agrégées sur les saisons indiquées par leur nom | À conserver comme piste de provenance à rechercher, pas comme données propres à un backtest : bookmaker, source, horodatage et licence manquent |

## Vérifications et défauts constatés

- `basic_kelly_criterion` calcule `(b × q − p) / b`, alors que la formule Kelly binaire standard est `(b × p − q) / b`, avec `b = cote décimale − 1`, `p` la probabilité de gain et `q = 1 − p`. À cote décimale 2,00, le code recommande −20 % du capital pour `p = 60 %` et +20 % pour `p = 40 %` : le sens est inversé.
- `decimal_odds(-100)` retombe sur la branche de repli et renvoie `-100.0`, au lieu de la cote décimale 2,00 équivalente à +100. Ce cas limite n'est pas couvert par les tests.
- `arb_percentage` utilise `decimal_implied_win_prob`, qui arrondit chaque probabilité à trois décimales avant de décider si la somme est sous 1. Une opportunité proche du seuil peut donc être mal classée.
- `strats/value.py` sélectionne les lignes selon le spread de clôture et le score final; il n'établit pas le mouvement « outsider vers favori » annoncé, ne compare pas à un prix de pari réellement offert et ne mesure pas le rendement d'une règle pré-match.
- Les trois CSV d'odds ont des Game ID uniques et des dates renseignées, mais aucun identifiant de bookmaker ni heure de capture. Leurs résultats finaux ne permettent pas à eux seuls de reconstruire les prix effectivement accessibles avant chaque match. Les bases SQLite ne contiennent que des agrégats par équipe et saison, sans instant de disponibilité par match.
- Les scrapers de `data/scraper.py` ciblent des pages fixes, sans délai réseau ni contrôle explicite du statut HTTP; ils n'ont pas été exécutés.
- `tests/test_probs.py` contient une assertion inconditionnellement fausse (`assert False`); deux tests de parlay sont vides (`pass`). L'essai `python -m pytest -q` n'a pas pu collecter la suite, car pytest n'est pas installé dans l'environnement. Aucune dépendance n'est déclarée par le dépôt.

## Vérifications

- **Exécution / installation :** non réalisées; manifeste absent
- **Test logiciel :** suite non exécutée (pytest absent); examen statique des tests effectué
- **Contrôle arithmétique :** défaut Kelly et cas `-100` reproduits par appel direct aux fonctions
- **Backtest / rendement :** aucun backtest reproduit; aucune preuve de rentabilité
- **Fuite temporelle :** les fonctions de `strats/value.py` utilisent les scores finaux et le spread de clôture pour décrire un filtre historique; aucun test pré-match valide n'est fourni
- **Sécurité / données / licence :** aucun appel aux scrapers n'a été fait; provenance et licence des données non établies
- **Compatibilité France / ANJ :** à vérifier; les exemples et marchés décrits ne démontrent pas l'exploitabilité chez un opérateur agréé

## Avis

**Documenter seulement; ne pas réutiliser les fonctions de mise telles quelles.** Mon avis : c'est un aide-mémoire de calculs, pas un moteur de paris ni un modèle prédictif. Son petit calculateur de dutching est redondant avec une idée déjà cataloguée, et le défaut de Kelly suffit à écarter les fonctions de bankroll avant correction et tests indépendants. L'intérêt pour Revue est surtout de rappeler que des formules courtes exigent des tests de référence aux frontières et que des fichiers historiques sans provenance ni heure de capture ne prouvent pas qu'un prix était jouable.

## Fichiers consultés

- [Calcul Kelly](https://github.com/sedemmler/WagerBrain/blob/b1cc33f5eb7a6130106bf8251b554718e2d22172/bankroll.py)
- [Conversions de cotes](https://github.com/sedemmler/WagerBrain/blob/b1cc33f5eb7a6130106bf8251b554718e2d22172/odds.py)
- [Calcul d'arbitrage](https://github.com/sedemmler/WagerBrain/blob/b1cc33f5eb7a6130106bf8251b554718e2d22172/strats/arb.py)
- [Filtre de valeur NBA](https://github.com/sedemmler/WagerBrain/blob/b1cc33f5eb7a6130106bf8251b554718e2d22172/strats/value.py)
- [Tests de probabilités](https://github.com/sedemmler/WagerBrain/blob/b1cc33f5eb7a6130106bf8251b554718e2d22172/tests/test_probs.py)
