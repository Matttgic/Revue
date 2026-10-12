# REV-KRUSINA-01 — SoccerPredictor (double chance par réseaux récurrents)

- Date : 2026-10-12.
- Motif : **résultats non fiables** (sélection sur le jeu de test) et données non publiées.
- Source : [jkrusina/SoccerPredictor](https://github.com/jkrusina/SoccerPredictor) — [dossier d'audit](../analyses/SoccerPredictor/AUDIT.md).

## Preuves

- `soccerpredictor/trainer/trainer.py` enregistre les meilleurs paramètres des équipes de test quand leurs métriques **de test** s'améliorent, puis refait les prédictions finales avec ces paramètres (`revert_to_best_params=True`).
- Le « profit 1 069 %, ROI 33,4 % » affiché porte sur 32 paris en 113 jours, meilleure de plusieurs exécutions.
- Jeu de données absent : impossible à reproduire.

## Remplacement

Aucun : l'idée (un réseau par équipe) n'a pas de résultat valide à comparer. Pour le football, voir [REV-MEZZALA-01](../analyses/mezzala/REV-MEZZALA-01_ponderation-et-regroupement.md) et [REV-GOPALA-01](../analyses/sports-model/AUDIT.md).
