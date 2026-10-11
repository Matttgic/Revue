# REV-BLUMMA-07 — Vérifier ROI, Brier et robustesse d'une famille de signaux

**Statut : À étudier | source https://github.com/blummabet/Betting-Dashboard**

Références : [backtest_model_health.py](https://github.com/blummabet/Betting-Dashboard/blob/main/backtest_model_health.py), [backtest_report.md](https://github.com/blummabet/Betting-Dashboard/blob/main/backtest_report.md), [liga_backtest_report.json](https://github.com/blummabet/Betting-Dashboard/blob/main/liga_backtest_report.json).

## Méthodologie à conserver
Décomposer le rendement par date, saison, bookmaker, compétition, marché, prix, niveau de confiance, famille et version de modèle. Donner nombre de paris réglés, de pushes/void, résultat en unités, ROI, CLV, calibration et drawdown. Étiqueter clairement le nombre d'observations et l'incertitude (bootstrap/Wilson).

## Conclusions des rapports (chiffres de l'auteur)
- Rapport pick-history : 619 resolved, ROI **−7,05 %**, IC bootstrap 95 % **[−14,49 % ; +0,66 %]**, Brier **0,2918**.
- Elo : 144 picks, +1,34 % ROI, IC large recouvrant zéro.
- Skellam : 512 picks, **−9,57 % ROI** dans ce rapport.
- Rapport par signaux Liga : `form_trend −8,2 %` (n=1810), `xg_strength −7,7 %` (n=1274), `league_pressure −13,9 %` (n=529), sur segments **non mutuellement exclusifs**.
- Certaines tranches annoncées positives sont minimes (ex. 4–6 pp d'edge, n=19) et ne justifient pas une sélection a posteriori.

## Vérifications supplémentaires indispensables
- Que l'échantillon n'a pas été filtré après constat des résultats.
- Que les prix étaient réellement disponibles **avant** le match chez le bookmaker indiqué.
- Que le ROI utilise les mises risquées, que annulations et demi-gains/pertes sont correctement traités.
- Que les probabilités conditionnelles sont évaluées hors échantillon et que le Brier est défini pour le marché concerné.
- Que bootstrap respecte des regroupements par date/événement en présence de dépendances.
- Que le modèle de référence (marché sans marge) est testé sur mêmes conditions.
- Que les conclusions restent après correction des comparaisons multiples et sur un suivi prospectif.

**Verdict :** conserver aussi les **échecs** : la bibliothèque ne doit jamais transformer les résultats négatifs en promesses.
