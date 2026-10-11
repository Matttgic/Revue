# REV-BLUMMA-06 — Cohérence intra-marché des totaux de buts

**Statut : À étudier | source https://github.com/blummabet/Betting-Dashboard**

Source : [betfair_coherence.py](https://github.com/blummabet/Betting-Dashboard/blob/main/sharp_signals/betfair_coherence.py).

## Hypothèse
Comparer simultanément les lignes Over/Under 1,5/2,5/3,5/4,5 d'un même match permet de détecter des violations monotones (P(Over 3,5) ne peut pas dépasser P(Over 2,5)) et des incohérences avec un modèle de buts. Les lignes à marge différente doivent être traitées avant comparaison.

## Limite cruciale démontrée par la source
Le développeur constate que des « écarts » signalés contre un modèle Poisson simple provenaient **très largement du manque d'ajustement de son propre modèle** à la courbe réelle. Quand l'ajustement était correct, les supposées opportunités disparaissaient. Un **résidu de modèle n'est pas automatiquement une inefficience du bookmaker**.

## Validation
- Exiger ≥3 lignes de même rencontre et côté, cotées simultanément, comparer à probabilités sans marge.
- Vérifier monotonicité et incohérences arithmétiques en premier, avant modèles.
- Modéliser plusieurs distributions plausibles, puis mesurer les résidus hors échantillon.
- Détecter les problèmes de liquidité, latence, lignes asynchrones, frais et impossibilité d'exécution.
- N'utiliser en France que des marchés/quotes d'opérateurs autorisés.

**Verdict :** garde-fou et idée de recherche intéressants, mais pas un arbitrage démontré.
