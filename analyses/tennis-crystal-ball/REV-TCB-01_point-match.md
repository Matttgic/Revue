# REV-TCB-01 — Probabilités service-retour vers jeu, set et match

- Statut : **À étudier**.
- Sport : Tennis. Marché/usage : Match / sets / live.
- Source et version : [audit du dépôt](AUDIT.md).
- Preuve : lecture ciblée du code/documentation ; protocole ci-dessous non exécuté.

## Idée

Relier les probabilités de point aux règles de score et au format du match, puis comparer au modèle Elo par surface.

## Protocole proposé

Valider cas symétriques et formats best-of, tie-breaks et extrêmes. Estimer service/retour sur le passé avec régularisation ; tester calibration et gain contre Elo et marché sur blocs futurs.

## Limites

Une indépendance stationnaire des points peut être trop simple ; fatigue et changements de niveau à examiner. Données amont et convergence du normaliseur non validées.

Aucun code tiers intégré aux modèles existants.
