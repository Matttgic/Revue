# REV-VCHEQUE-04 — Combinés : valeur nette, dépendances et calibration

**Statut : À étudier, pas une stratégie rentable validée.**

- **Source d'inspiration :** https://github.com/VCheque/Football-Betting/blob/main/sports_betting/generate_bet_combinations.py
- **Auteur source :** VCheque, licence non spécifiée.

## Méthode observée

Le générateur trie des choix de paris 1N2 selon leur EV individuelle, impose au plus une sélection par match, puis utilise le produit des probabilités et des cotes pour estimer l'EV d'un combiné. La table de paris amont repose sur un modèle de score **heuristique**, distinct du XGBoost principal.

Le produit de probabilités `∏p_i` est correct **uniquement sous hypothèse d'indépendance des événements**. La sélection d'un seul pari par match réduit une dépendance manifeste, sans démontrer l'indépendance entre rencontres.

## Amélioration proposée

1. Rejeter les cotes non observées, les marchés illégaux ou les sélections non datées.
2. Mesurer les probabilités individuelles avec un modèle calibré hors échantillon.
3. Préférer un jeu de sélection diversifié : équipes/compétitions/horaire/correlations connues.
4. Faire un test de sensibilité à l'erreur de probabilité et à une corrélation commune cachée.
5. Comparer systématiquement avec le meilleur pari simple ; documenter la variance et le pire drawdown.
6. Éviter d'optimiser le nombre de jambes sur le même backtest utilisé pour publier le ROI.

## Exemple didactique (indépendance supposée)

Deux événements estimés à `p=0,60` chacun, cotes observées `1,80` : EV simple `0,60×1,80−1=+8%` ; EV combiné théorique `(0,60²×1,80²)−1=+16,64%`. Ce résultat ne vaut **que** si les deux estimations sont fiables, les événements indépendants et le prix réellement disponible.

## Critère de rejet

Pas de cotes vérifiables, pas de calibration, ou incertitude non modélisée => **ne pas considérer un combiné comme value prouvée**.
