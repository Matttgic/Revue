# REV-NCSUN-03 — Marchés UFC, cote d'ouverture et « KO fade »

**Statut : À étudier — documentation uniquement; modèle non reproduit.**

- **Sport :** MMA / UFC
- **Marchés :** vainqueur du combat, victoire par décision, combat allant à la distance
- **Origine :** https://github.com/mkboggs92-cloud/ncsun/blob/main/sports/ufc.js
- **Auteur source :** mkboggs92-cloud ; licence non spécifiée
- **ANJ / France :** validation de chaque compétition, marché, opérateur et flux de prix indispensable

## Deux hypothèses à tester séparément

**Prix d'ouverture :** certaines cotes initiales pourraient intégrer moins d'information que les cotes proches du combat. Une probabilité calibrée sur performances antérieures, confrontée à une cote **horodatée**, peut identifier les divergences. Cela n'autorise pas à utiliser a posteriori le meilleur prix observé.

**KO fade :** sur les méthodes de victoire, le marché pourrait donner trop de probabilité au KO et pas assez à la décision. Tester une sélection de victoires par décision lorsque la probabilité de KO estimée est suffisamment inférieure à celle du marché dé-margé.

## Concepts techniques observés

- Rating d'opposition de type Bradley-Terry sur le réseau des combats précédents, pondéré par récence.
- Résultats professionnels au-delà de l'UFC, statistiques d'actions, durabilité, âge, avantage physique et expérience.
- Modèles probabilistes indépendants « victoire » et « méthode de victoire ».
- Calibration temporelle et blend avec le prix du marché en tenant compte de sa maturité.
- Gardes-fous contre la concentration (plusieurs picks sur un même combat ou une seule carte).

Le dépôt décrit des combinaisons d'algorithmes, mais ne fournit pas le code d'entraînement ni les données nécessaires à leur reproduction.

## Performance rapportée et réserve forte

Source `ufc_backtest.json` : **544** paris, **297** gagnés et **+171,75 unités**, soit **+31,57 % ROI** à partir des profits déclarés.

**Risque de biais significatif :** l'auteur indique calculer certains props à partir de la meilleure cote de clôture disponible entre plusieurs opérateurs alors que les moneylines utilisent des ouvertures. Sans traçabilité fine de disponibilité/horodatage et de la sélection, ce rendement élevé ne peut être considéré comme exécutable. Des filtres et seuils ont également été ajustés sur les données évaluées.

## Reproduction nécessaire

Construire un rating original; modéliser la probabilité de chaque issue par période d'entraînement strictement antérieure; réunir des historiques de cotes sourcés; enregistrer des signaux en « paper live » sans les modifier; refaire le ROI net au bookmaker réellement accessible et calculer CLV et calibration.

**Verdict :** intérêt conceptuel élevé, preuve de rentabilité insuffisante.
