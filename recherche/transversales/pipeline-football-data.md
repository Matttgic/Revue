# REV-VCHEQUE-03 — Pipeline football et fraîcheur des données

**Statut : À étudier / architecture identifiée, code tiers non repris.**

- **Projet source :** https://github.com/VCheque/Football-Betting
- **Parties analysées :** `.github/workflows/refresh-matches.yml`, `refresh-players.yml`, `sports_betting/fetch_top6_data.py`, `fetch_player_stats.py`.
- **Licence :** aucune licence au dépôt; noter séparément les droits des données tierces.

## Schéma architectural utile

Planificateur → connecteurs de données autorisées → normalisation par équipe / ligue → horodatage de source → vérification des résultats et des doublons → features au temps T → prédiction et journal immuable → suivi du règlement des paris.

## Sources repérées

- **football-data.co.uk** : résultats et cotes historiques de six ligues, CSV; qualité et droits d'usage à vérifier. La source distingue des colonnes de cotes de périodes différentes, mais cela ne fournit pas un carnet d'ordres temps réel.
- **Understat** : données joueurs xG/xA sur Big Five via récupération dédiée; Primeira Liga non couverte en secours Understat.
- **API-Football** : possibilité d'enrichissement avec clé, lorsqu'elle est fournie au script.

La métadonnée du projet indiquait au 2026-10-09 : matchs actualisés (10 750 lignes), joueurs datés du 2026-03-23 (2 660 lignes). Prévoir une alerte de fraîcheur qui porte sur la date **réellement observée**, pas simplement sur le cron configuré.

## Contrôles à intégrer dans un pipeline autonome

- Journaliser heure de capture en UTC, période des cotes (opening / closing / snapshot), source et droits.
- Écarter les blessures, compositions ou statistiques qui n'étaient pas publiées avant l'heure de la prévision.
- Ne jamais substituer `0` à une donnée manquante sans conserver un indicateur de manquant.
- Valider saison, ligue, équipe normalisée, doublons, statut terminé, données manquantes et anomalies de cotation.
- Séparer `refresh`, `train`, `predict`, `evaluate`, `settle`.
- Préférer des snapshots horodatés à des CSV qui écrasent silencieusement l'état historique.
- Vérifier la conformité avec les licences des API et la réglementation ANJ pour toute exploitation.

## Restriction majeure

Le fournisseur football-data.co.uk présente ses données gratuites comme destinées à une utilisation privée avec restrictions pour produits commerciaux et certains usages automatisés/IA : https://www.football-data.co.uk/data.php. **Ne pas intégrer les CSV tiers dans Revue.**

**Verdict :** architecture intéressante à réimplémenter avec des flux autorisés, mais pas une stratégie de gain autonome.
