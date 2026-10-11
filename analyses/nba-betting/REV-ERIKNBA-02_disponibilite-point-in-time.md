# REV-ERIKNBA-02 — Disponibilité des joueurs calculée avant le match

**Statut :** À étudier — l’implémentation source ne doit pas être reproduite telle quelle.

## Identité

- **Sport / compétition :** NBA
- **Marché :** moneyline, spread et total
- **Moment :** pré-match
- **Objectif :** mesurer l’effet des absences de rotation sur la probabilité d’équipe
- **Type :** variables temporelles et modèle Elo/GBM
- **Origine :** [erik-droidd/nba-betting](https://github.com/erik-droidd/nba-betting), commit `d1050d325ae87487fd72ced4deddd4116db8ac2f`; `nba_betting/features/availability.py`
- **Date d’intégration :** 2026-10-11
- **Tags :** `NBA`, `pré-match`, `joueurs`, `disponibilité`, `fuite temporelle`

## Hypothèse et méthode

Au lieu de compter seulement les noms blessés, estimer la rotation d’une équipe à partir des dix derniers matchs antérieurs : un joueur est « régulier » s’il a joué dans au moins 60 % des cinq derniers matchs et cumulé typiquement au moins 12 minutes. Les variables proposées sont la part de minutes de rotation indisponibles, la présence d’un joueur à 30 minutes ou plus, et la part de talent/minutes habituelle disponible.

L’idée à tester est la pondération des absences par le rôle réellement observé, à condition de construire chaque ligne exclusivement avec des informations datées avant le match cible. Le dépôt rapporte une amélioration de Brier OOF pour Elo de 0,2096 à 0,2077 et une exactitude walk-forward de 66,2 % à 67,1 %; ce sont des résultats de l’auteur, non reproduits.

## Problème temporel bloquant

Dans la version auditée, `typical minutes`, la forme et le statut de régulier sont décalés d’un match, mais l’indicateur `present` provient des minutes jouées **dans le match cible**. La variable « absent » est donc connue après le match pour les lignes historiques et OOF. En direct, elle est remplacée par les blessures ESPN et leurs statuts probables. Les données publiées ne fournissent pas l’historique complet de ce qui était effectivement connu avant chaque tip-off. Cette différence peut gonfler les performances rapportées et rend les gains associés à cette variable non fiables pour le déploiement.

## Données et protocole à refaire

Il faut des snapshots d’indisponibilités et de lineups horodatés avant le début de chaque rencontre, les rôles calculés uniquement sur les matchs antérieurs, et un gel de la variable à l’heure de décision. Comparer sur les mêmes folds : Elo sans disponibilité, Elo avec informations pré-match, puis GBM. Consigner séparément les changements de statut tardifs et joueurs actifs mais non utilisés.

**Verdict :** l’idée d’un poids d’absence fondé sur la rotation est pertinente; l’implémentation d’entraînement utilise de l’information post-match et ses gains ne doivent pas être repris avant réévaluation.
