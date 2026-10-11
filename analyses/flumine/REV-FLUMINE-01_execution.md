# REV-FLUMINE-01 — Rejouer latence, file, volume et règlements

- Statut : **À étudier**.
- Sport : Multi-sports. Marché/usage : Exchange / backtest.
- Source et version : [audit du dépôt](AUDIT.md).
- Preuve : lecture ciblée du code/documentation ; protocole ci-dessous non exécuté.

## Idée

Séparer le signal de décision de l’acceptation réelle d’un ordre, de son remplissage partiel et de son règlement.

## Protocole proposé

Comparer latences et hypothèses de file ; intégrer commissions, liquidité consommée, annulations et exposition. Éviter les options qui doublent les volumes. Confronter ensuite au paper trading prospectif.

## Limites

Le replay ne connaît pas précisément l’impact de ses propres ordres ni leur place réelle. Le mode simulation ne valide pas la stratégie. Aucun ordre envoyé.

Aucun code tiers intégré aux modèles existants.
