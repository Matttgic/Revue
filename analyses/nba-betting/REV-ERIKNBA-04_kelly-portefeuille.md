# REV-ERIKNBA-04 — Dimensionner conjointement les paris d’une soirée

**Statut :** À étudier — simulation de risque, pas preuve de rendement.

## Identité

- **Sport / compétition :** NBA
- **Marché :** moneyline simultanées sur une soirée
- **Moment :** pré-match
- **Objectif :** limiter l’exposition et tenir compte de la dépendance entre mises
- **Type :** optimisation de portefeuille / Kelly fractionné
- **Origine :** [erik-droidd/nba-betting](https://github.com/erik-droidd/nba-betting), commit `d1050d325ae87487fd72ced4deddd4116db8ac2f`; `nba_betting/betting/portfolio.py`, `kelly.py`, `recommendations.py`
- **Date d’intégration :** 2026-10-11
- **Tags :** `NBA`, `bankroll`, `Kelly`, `corrélation`, `exposition`

## Hypothèse et méthode

Dimensionner chaque pari isolément peut dépasser le budget de risque total et ignorer les scénarios communs. `optimize_slate()` cherche à maximiser la croissance logarithmique espérée sur des issues simulées avec une copule gaussienne, des plafonds par pari et d’exposition globale; la fonction de recommandation l’appelle et construit une matrice de corrélation simple. Une mise de secours réduit les Kelly individuels si l’optimiseur échoue.

## Limites et évaluation

La simulation dépend directement de probabilités et de corrélations fiables; une copule gaussienne et une matrice simplifiée n’identifient pas à elles seules la dépendance sportive réelle. Les tests valident le code mais aucune comparaison publiée ne montre que cette allocation améliore le rendement net ou réduit le drawdown hors échantillon. Le document de conception historique décrit encore une réduction corrélationnelle fermée comme la voie active, alors que le code courant appelle l’optimiseur; `ARCHITECTURE.md` doit donc primer.

Tester d’abord sur un journal prospectif gelé, avec mises fictives et probabilités calibrées. Comparer Kelly simple fractionné, plafonds seuls et optimisation conjointe à exposition identique; rapporter rendement, drawdown, volatilité, perte maximale et sensibilité à la corrélation. Ne jamais traiter un montant recommandé par ce module comme une mise validée.

**Verdict :** approche de contrôle de risque intéressante à reproduire indépendamment; aucune preuve de rentabilité et aucune justification d’argent réel.
