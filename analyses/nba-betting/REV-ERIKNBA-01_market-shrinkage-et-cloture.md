# REV-ERIKNBA-01 — Réduire les probabilités vers le marché et tester contre la clôture

**Statut :** À étudier — preuve de supériorité du modèle absente.

## Identité

- **Sport / marché :** NBA moneyline
- **Moment :** pré-match
- **Objectif :** calibration et filtrage d’écarts modèle-marché
- **Type :** combinaison probabiliste et protocole d’évaluation
- **Origine :** [erik-droidd/nba-betting](https://github.com/erik-droidd/nba-betting), commit `d1050d325ae87487fd72ced4deddd4116db8ac2f`; `nba_betting/betting/shrinkage.py`, `edge.py`, `market_eval.py`
- **Date d’intégration :** 2026-10-11
- **Tags :** `NBA`, `pré-match`, `cotes`, `calibration`, `marché`, `walk-forward`

## Hypothèse et méthode

Traiter le prix de marché comme une référence forte réduit les écarts dus au bruit du modèle. En log-odds : `logit(p_final) = (1 − λ) × logit(p_modèle) + λ × logit(p_marché)`. L’auteur utilise `λ = 0,60`; le calcul d’edge compare ensuite la probabilité réduite au prix du contrat.

L’idée méthodologique la plus solide est de comparer modèle et prix de clôture sur **les mêmes matchs hors échantillon**. Ajuster λ seulement sur les folds de calibration, puis le figer avant d’évaluer le fold suivant. Garder séparés le score probabiliste (Brier/log-loss), la performance contre la clôture (CLV) et le ROI aux prix réellement accessibles.

## Données et évaluation

Il faut des probabilités pré-match horodatées, le prix pris au pari et le prix de clôture du même marché, le résultat et les frais. Les documents du dépôt signalent que le prix Polymarket utilisé n’est pas corrigé des frais d’exécution.

Après réparation des données, le rapport d’auteur porte sur 124 moneylines : Brier modèle 0,2046 contre 0,2081 pour le marché, `t = −0,36`; le dépôt conclut que le modèle ne bat pas le marché. La grille de λ donne 0,50, mais log-loss 0,5870 contre 0,5871 au λ de production 0,60. L’auteur refuse à juste titre un verdict sous 300 matchs. Ces chiffres n’ont pas été reproduits depuis le dépôt, qui ne contient pas sa base SQLite.

## Limites et prochaine étape

Un meilleur score sur 124 matchs peut relever du bruit et ne garantit aucun rendement après coûts. Polymarket et les prix US cités ne doivent pas être supposés accessibles légalement en France. Refaire l’évaluation sur prix disponibles chez opérateurs agréés, avec CLV et frais, en séparant strictement l’ajustement de λ du test final.

**Verdict :** bon protocole à adapter indépendamment; aucune stratégie rentable démontrée.
