# REV-ERIKNBA-03 — Collecter et contrôler les snapshots de cotes

**Statut :** À étudier — procédure utile; couverture prospective insuffisante.

## Identité

- **Sport / compétition :** NBA
- **Marché :** moneyline, spread, total; lignes d’indisponibilité
- **Moment :** pré-match
- **Objectif :** conserver les prix et nouvelles disponibles au moment de la prévision
- **Type :** infrastructure de données point-in-time
- **Origine :** [erik-droidd/nba-betting](https://github.com/erik-droidd/nba-betting), commit `d1050d325ae87487fd72ced4deddd4116db8ac2f`; `nba_betting/data/snapshot_jsonl.py`, `injury_jsonl.py`, `snapshot_loop.py`
- **Date d’intégration :** 2026-10-11
- **Tags :** `NBA`, `données`, `horodatage`, `cotes`, `qualité`

## Hypothèse et méthode

Conserver des lignes JSONL quotidiennes plutôt que seulement la dernière cote en base permet d’auditer les prix et de reconstruire le prix le plus proche du début du match. Le système audité utilise une boucle de capture rapprochée du tip-off, sépare les sources, associe les lignes par match et date de jeu en heure de l’Est, puis réimporte les fichiers de façon idempotente. Les snapshots de blessures sont gelés au tip-off pour ne pas introduire les mises à jour post-match dans le même jour.

Les corrections documentées sont instructives : captures post-match, cotes attachées au prochain match d’une même paire lors des matchs tardifs, doublons, snapshots associés au mauvais événement Polymarket et données blessures écrasées après le tip-off. L’auteur rapporte une réparation locale de 1 612 lignes sans doublon et une réimportation identique; la base nécessaire à la reproduction n’est pas incluse.

## Données, contrôles et limites

À chaque capture, conserver l’identifiant et les équipes du match, l’heure UTC, le jour de match ET, le bookmaker/source, les prix bruts et le statut du marché. Refuser les prix postérieurs au tip-off, déjà réglés, extrêmes ou associés sans certitude au match. Vérifier la fraîcheur de la dernière ligne et la couverture par source avant tout calcul de CLV.

Les snapshots versionnés sont partiels et ne constituent pas encore une saison complète de prix. Le dépôt décrit des retards importants du cron initial puis une boucle auto-relancée; quelques nuits vérifiées ne suffisent pas à démontrer une couverture stable. Les fournisseurs et leurs conditions de réutilisation doivent être contrôlés.

**Verdict :** bonnes pratiques d’audit des événements et des horodatages à reprendre dans une implémentation originale; ne pas utiliser les séries de cotes avant d’avoir validé couverture et rattachement.
