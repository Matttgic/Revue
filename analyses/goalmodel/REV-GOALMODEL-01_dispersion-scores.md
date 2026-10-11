# REV-GOALMODEL-01 — Dispersion des scores : Poisson, binomiale négative et CMP

- Statut : **À étudier**.
- Sport : Football. Marché/usage : Totaux / BTTS / scores.
- Source et version : [audit du dépôt](AUDIT.md).
- Preuve : lecture ciblée du code/documentation ; protocole ci-dessous non exécuté.

## Idée

Remplacer l’hypothèse variance = moyenne par une dispersion estimée, puis dériver les marchés depuis une distribution de scores cohérente.

## Protocole proposé

Comparer Poisson/DC, binomiale négative et CMP sur les mêmes fenêtres. Choisir les paramètres sur le passé, contrôler masse et queues, mesurer log-loss/RPS/calibration puis rendement aux cotes accessibles.

## Limites

Le paramètre supplémentaire peut surajuster ; respecter contraintes numériques, troncature et droits du code GPL-3. Pas de gain reproduit.

Aucun code tiers intégré aux modèles existants.
