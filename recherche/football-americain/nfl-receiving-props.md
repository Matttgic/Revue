# REV-NCSUN-02 — Sous sur réceptions et yards, effectif actif et prix du marché

**Statut : À étudier — documentation uniquement; modèle non reproduit.**

- **Sport :** NFL
- **Marchés :** under sur réceptions et yards à la réception; touchdown à tout moment comme segment séparé
- **Origine :** https://github.com/mkboggs92-cloud/ncsun/blob/main/sports/nfl.js
- **Auteur source :** mkboggs92-cloud ; licence non spécifiée
- **ANJ / France :** vérifier la disponibilité légale de chaque marché et bookmaker; historique américain non transposable directement

## Hypothèse

Les joueurs les plus populaires peuvent être surachetés sur les marchés « over ». Un écart n'est intéressant que lorsque le volume de jeu prévisible, le rôle et les absences donnent une estimation indépendante plus faible que celle de la ligne proposée.

## Éléments à modéliser

- Volume de snaps, participation, routes, cibles, réceptions, efficacité, interceptions de rôle.
- Joueurs réellement actifs, impact des absences et remontées dans la hiérarchie des receveurs.
- Adversaire, météo, nombre de tentatives aériennes et total implicite de l'équipe.
- Distribution des événements discrets (réceptions) distincte de celle des yards.
- Probabilités de touchdown par course/réception, calibrées indépendamment.
- Probabilités dé-margées sur les deux côtés d'une même ligne chez plusieurs bookmakers.

## Procédure de recherche

1. Fixer une heure de prévision et utiliser uniquement les informations et cotes antérieures.
2. Quantifier l'effet de l'absence d'un coéquipier sur l'usage des joueurs restants.
3. Prédire distribution de réceptions et probabilité d'être sous la ligne; traiter les yards séparément.
4. Mélanger prudemment probabilité du modèle et consensus de marché, en calibrant les poids sur une période d'entraînement.
5. Calculer l'espérance de gain nette au prix **réellement proposé**, pas seulement un écart de pourcentage avec la probabilité sans marge.
6. Retenir des choix diversifiés; enregistrer les lignes perdues, picks proposés, prix disponibles, blessures tardives et résultats.

## Performance rapportée

Source `nfl_backtest.json` : **864** paris, **472** gagnés, **+140,80 unités** pour un ROI recalculé de **+16,30 %**. Cette cohérence arithmétique n'établit pas l'indépendance du pipeline ou la disponibilité des prix.

L'auteur mentionne une pondération du consensus de marché dans la probabilité finale et une validation chronologique. Cependant, ni le code d'entraînement ni la base de cotes ne sont publiés.

## Test à conduire

Comparer modèle brut, marché sans marge et blend sur saisons complètement séparées. Mesurer calibration, log loss, Brier, CLV et ROI, avec intervalles d'incertitude, disponibilité des lignes et timing effectif. Les touchdown yes doivent faire l'objet d'un protocole distinct des under.

**Verdict :** méthodologie intéressante pour développer des marchés joueurs; non déployable en l'état.
