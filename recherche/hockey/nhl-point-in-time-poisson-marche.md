# REV-CLAIR-01 — Hockey NHL : modèle Poisson chronologique et marché

**Statut : À étudier.** Source : https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/backtest_hockey_models.py ; aucune reprise de code tiers.

## Idées
- Prédire une distribution de buts par équipe à partir de résultats antérieurs à la rencontre ; lisser début de saison vers la saison précédente.
- Transformer les distributions en probabilités ML (y compris prolongation, selon règles), O/U et handicap avec traitement particulier du shootout et des pushes.
- Confronter modèle Poisson et **consensus bookmaker hors marge** ; ajuster le poids de chaque signal sur une période d'entraînement uniquement.
- Tester la dispersion (variance des buts supérieure à Poisson) et les marges de victoire avant toute décision de puck-line.
- Contraster la forme récente et le niveau de base plutôt que surpondérer une série de 3 matchs.

## Évaluation indispensable
Splits temporels train/calibration/test, disponibilité des cotes à l'heure du pick, baseline marché, log loss, Brier, CLV, ROI et incertitude. Les cotes de clôture permettent de mesurer le benchmark mais pas de reconstruire un prix jouable en amont sans snapshots.

**Verdict :** très bonne approche de test, absence de résultat indépendant reproduit.
