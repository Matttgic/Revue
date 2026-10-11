# REV-SOCCERACTION-01 — xT et VAEP historiques comme variables pré-match

- Statut : **À étudier**.
- Sport : Football. Marché/usage : Variables équipe / joueur.
- Source et version : [audit du dépôt](AUDIT.md).
- Preuve : lecture ciblée du code/documentation ; protocole ci-dessous non exécuté.

## Idée

Quantifier progression et valeur des actions, puis agréger ces valeurs uniquement sur les rencontres antérieures au match prédit.

## Protocole proposé

Figer la transformation xT/VAEP avant chaque bloc test ; comparer baseline Elo/DC/xG puis ajout des variables. Tester les mêmes matchs, couverture, stabilité par compétition et gain au-delà du marché.

## Limites

VAEP/xT décrivent les actions, pas directement le pari ; données événementielles parfois partielles et restrictions fournisseur. Aucun modèle implémenté dans Revue.

Aucun code tiers intégré aux modèles existants.
