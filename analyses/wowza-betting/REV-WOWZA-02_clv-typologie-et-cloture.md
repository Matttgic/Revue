# REV-WOWZA-02 — Distinguer les questions de CLV et prouver le prix proche du match

**Statut : À étudier — conception et code inspectés; pipeline non reproduit indépendamment.**

- **Sport / ligue :** football, architecture transposable à tout sport disposant de marchés multi-livres
- **Marché :** 1X2 / moneyline, totaux, BTTS et autres marchés bilatéraux cotés
- **Origine :** [`NevixAA/wowza-betting`, commit `87c4229`](https://github.com/NevixAA/wowza-betting/tree/87c4229dbb326306df8db7eb591bc8a857454058), `src/clv_types.py`, `src/book_quotes.py`, `src/market_anchor.py`
- **Licence :** aucune licence explicite repérée; aucun code repris
- **Audit :** [dossier complet](AUDIT.md)

## Hypothèse

La « CLV » doit préciser **quelle question le prix répond** :

| Comparaison | Question mesurée | Conditions |
|---|---|---|
| Même bookmaker | A-t-on pris un meilleur prix que le même livre a affiché ensuite? Mesure d'exécution | Même fixture, bookmaker, marché, côté et ligne; prix d'entrée et dernière observation admissible avant match |
| Référence sharp | Le prix de référence a-t-il convergé vers notre probabilité? Mesure d'information du marché | Référence choisie (ex. Pinnacle/Betfair), prix des deux côtés, marge retirée explicitement |
| Consensus multi-livres | La décision est-elle mieux placée que la probabilité médiane des livres observés? | Au moins trois livres, chacun avec les deux côtés cotés; dé-vig par livre avant médiane |

Ces valeurs ne sont ni identiques ni un ROI. Le comparatif au même livre garde sa marge dans les deux prix; les deux autres nécessitent une estimation sans marge. Aucun des trois ne remplace le règlement des paris.

## Garde-fous de capture observés

Le module de quotes rattache chaque observation à la fixture, au bookmaker, au marché, au côté, à la ligne et aux minutes avant coup d'envoi. Il distingue `POST` des fenêtres pré-match et définit un close admissible dans les 30 minutes précédant le début. Une observation périodique (heartbeat) aux fenêtres proches enregistre aussi un prix inchangé : sans elle, « le prix est resté identique jusqu'au coup d'envoi » et « personne n'a regardé depuis trois heures » seraient confondus. Pour éviter qu'un manque devienne un nombre inventé, la bibliothèque possède des états distincts comme `NO_CLOSE`, `POST_KICKOFF_ONLY`, `ONE_SIDED` et `INSUFFICIENT_BOOKS`.

Le rapport d'audit Wowza du 4 octobre précise cependant que les trois types de CLV avaient été ajoutés sans consommateur confirmé à cette date. Le code de calcul est inspectable, mais son usage complet n'est pas établi par les artefacts examinés.

## Application à Revue

Revue suit déjà une cote au même bookmaker et nomme explicitement son indicateur comme un proxy de clôture sur 90 minutes. Cette fiche propose d'ajouter, si l'échantillon multi-livres est suffisant, des colonnes et états séparés pour la référence sharp et le consensus dé-viggué. Conserver la fenêtre de clôture et les identifiants de ligne exacts; si l'un des deux côtés ou la récence manque, publier le statut d'indisponibilité plutôt qu'un CLV numérique.

**Verdict :** bonne taxonomie de mesure et de provenance, complémentaire au CLV d'exécution déjà suivi. Elle décrit la qualité de prix et d'observation; elle ne valide aucune stratégie de pari du dépôt.
