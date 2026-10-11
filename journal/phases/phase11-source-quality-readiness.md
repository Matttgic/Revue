# Phase 11 — Qualité des entrées sportives et règlements

**Réalisé** : audit prospectif séparant les données réellement obtenues des
informations non confirmées, sur les quatre sports. Les données nécessaires
aux modèles sont visibles dans le Lab, et l'analyse est rafraîchie dans
GitHub Actions. Les cotes ou résultats non fiables ne deviennent jamais des
paris gagnés/perdus.

- **NHL** : correspondance ESPN ↔ NHL (identifiant officiel + équipes +
  coup d'envoi exact) ; séparation entre statut *confirmé ESPN* et
  *pressenti ESPN*. Le statut du fournisseur ne prouve pas que le gardien
  ait joué, et n'ajuste aucun modèle. Contrôle d'horodatage et de doublons.
- **MLB** : une requête du calendrier officiel MLB Stats API
  (`schedule?sportId=1&hydrate=probablePitcher,person`). Association aux ID
  ESPN uniquement si deux noms d'équipes et horaire UTC (10 minutes de
  tolérance) correspondent de manière unique ; les lanceurs *probables*
  ne sont **pas des titulaires vérifiés** et ne modifient pas l'Elo.
- **NBA** : ne pas confondre statistiques avancées 2025–26 et saison
  régulière 2026–27 ; mode `prior_only` tant que les 30 équipes
  en cours ne sont pas observées et valides.
- **Football** : données de tirs ESPN utilisables comme telles ;
  pas d'xG/xGA Opta sans droits ni ingestion vérifiable. Aucun renommage
  de tirs en xG.
- **10 marchés NHL** : exclusions prouvées cohérentes avec l'historique
  papier originel, statut `market_rule_unverified`. Vérifier les périodes
  règlementaires/prolongations/tirs au but du bookmaker **avant les futurs
  paris**, et **ne pas réparer rétroactivement les 10 entrées** ni les
  compter au ROI.

**Limitations** : l'API de calendrier MLB peut ne pas publier les
lanceurs probables. Les sources actuelles ne fournissent pas les SQL
privés d'origine ni les éventuelles licences Opta. Aucun signal EV+
validé, pari réel ou promesse de rentabilité.

Tests : `python -m unittest discover -s tests -p 'test_phase11*.py' -v`
et `python -m unittest discover -s tests -p 'test_mlb_official_pitchers.py' -v`.

Actions : `Revue - Phase 11 Data Integrity` toutes les six heures et à
la suite du Match Center ou des observations NHL, sans appel à
PulseScore/Odds API. La page de données reste dans le Lab.

Documentation de l'endpoint public MLB :
https://github.com/pseudo-r/Public-MLB-API/blob/main/docs/schedule.md
