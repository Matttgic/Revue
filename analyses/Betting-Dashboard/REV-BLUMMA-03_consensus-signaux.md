# REV-BLUMMA-03 — Consensus multi-signaux sans double comptage

**Statut : À étudier | source https://github.com/blummabet/Betting-Dashboard**

Sources : [sharp_signals/registry.py](https://github.com/blummabet/Betting-Dashboard/blob/main/sharp_signals/registry.py), [conviction_score.py](https://github.com/blummabet/Betting-Dashboard/blob/main/conviction_score.py), [MLS_SIGNAL_AUDIT_2026-07-25.md](https://github.com/blummabet/Betting-Dashboard/blob/main/MLS_SIGNAL_AUDIT_2026-07-25.md).

## Idée
Un pari peut recevoir des signaux de mouvement des cotes, forme, xG, effectifs, météo et classement, mais plusieurs mesures reflètent une **même cause**. Les additionner sans discernement donne une conviction artificielle.

La source classe les modules en familles, prend le plus important pleinement et réduit d'autres contributions d'une même famille; elle exige aussi un déclencheur de marché avant de produire certains verdicts. Ce procédé est un **heuristique**, pas une preuve de fiabilité.

## Reconstruction préférable
1. Définir chaque signal avec marché, données attendues, date, direction et taux de couverture.
2. Grouper les corrélations empiriques, pas seulement les noms fonctionnels.
3. Distinguer signal manquant / désactivé / neutre / réellement contradictoire.
4. Tester score brut, score plafonné par famille et variante calibrée sur dataset distinct.
5. Publier pour chaque pari : faits indépendants, signaux redondants et raisons des veto.
6. Auditer l'accessibilité des scores maximum : si une famille ne reçoit jamais de donnée, un seuil peut devenir **mathématiquement impossible à atteindre** (déjà signalé sur MLS par le projet).

## Preuves requises
Abaltions (avec/sans famille), calibrations par score, Brier/log loss, retour net, CLV, corrélations et seuils gelés. Aucun nombre minimal de signaux n'assure des gains.

**Verdict :** excellent principe d'architecture; validations nécessaires.
