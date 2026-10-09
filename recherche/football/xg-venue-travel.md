# REV-BLUMMA-04 — xG, domicile/extérieur et fatigue du déplacement

**Statut : À étudier | source https://github.com/blummabet/Betting-Dashboard**

Modules : [xg_strength.py](https://github.com/blummabet/Betting-Dashboard/blob/main/sharp_signals/xg_strength.py), [venue_form.py](https://github.com/blummabet/Betting-Dashboard/blob/main/sharp_signals/venue_form.py), [mls_travel.py](https://github.com/blummabet/Betting-Dashboard/blob/main/sharp_signals/mls_travel.py).

## Hypothèse
Un modèle peut gagner en précision si sa mesure d'attaque et de défense (xG) distingue matchs à domicile et à l'extérieur, et inclut interactions entre déplacements, repos et fuseaux horaires. Une valeur agrégée peut masquer une asymétrie importante pour un match donné.

## Méthode de recherche
- Les xG, compositions, résultats et distances doivent être disponibles **avant** le match.
- Calculer forme domicile/extérieur avec lissage vers moyenne de ligue lorsque peu d'observations.
- Tester séparément : xG seul, split venue, distance seule, repos seul, distance × repos, modèle combiné.
- Exclure fuites issues de stats post-match, besoin d'une même horodatation pour toutes les features.
- Comparer performances aux consensus de bookmakers observés.

## Résultats disponibles
Dans `liga_backtest_report.json` fourni, la famille `xg_strength` affiche **1 274 paris, ROI −7,7 %**. Le fichier MLS, à l'époque reportée, mesure certains taux de réussite mais **pas de ROI** faute de cotes historiques suffisantes. Ne pas présenter le split ou les voyages comme un « edge » démontré.

**Verdict :** hypothèses testables; aucune valeur prouvée.
