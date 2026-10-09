# REV-CLAIR-06 — Mélange Monte-Carlo / Bayésien / Elo et calibration

**Statut : À étudier.** Référence : https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/docs/adaptive_weights.json, https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/backtest_hockey_models.py

## Idée
Plusieurs estimateurs peuvent apporter une information différente : probabilité Poisson/Monte-Carlo, rating Elo, modèle bayésien et consensus du marché. La combinaison doit être calibrée sur exemples passés et **évaluée après gel des poids**.

## Particularités intéressantes de la source
- État courant de pondération stocké par sport (`nhl_ens`, `ens`, `nba_ens`, etc.).
- Ajustements par bandes de probabilités et sport.
- Un compteur d'échantillons `used/excluded` lors du recalibrage.
- Une étude NHL propose de régler le poids du marché en minimisant la log loss historique.

## Conditions pour Revue
1. Remplacer les cotes de marché par des prix réellement disponibles au temps T, retirer correctement la marge.
2. Découper chronologiquement, éviter que l'évaluation serve aussi à régler les poids.
3. Séparer le poids par ligue et marché, sous réserve d'un effectif suffisant; shrinkage en l'absence d'information.
4. Comparer chaque composant isolé, ensemble égalitaire, ensemble appris et marché seul.
5. Une fois la série évaluée, figer paramètres et conserver chaque décision; pas de réécriture de l'historique.

**Alerte :** le `docs/adaptive_weights.json` examiné montre 1 298 observations retenues sur 1 488 ; une partie des timestamps reste inconnue. Ne pas assimiler ce fichier à une validation indépendante.

**Verdict :** architecture réutilisable conceptuellement, pas de preuve de surperformance sans ablation hors échantillon.
