# REV-SBT-01 — Football : baseline de-vig additif à marge fixe

**Statut : À étudier.** Source : [1canhhoa/sports-betting-toolbox](https://github.com/1canhhoa/sports-betting-toolbox), commit [`7941e20`](https://github.com/1canhhoa/sports-betting-toolbox/tree/7941e20ab089a54d4ca3bd69064133c4239c07e5). La fiche décrit la méthode en termes indépendants; aucun code ni jeu de données n’est repris.

## Hypothèse et formule observée

Le dépôt part de cotes décimales d’un même bookmaker. Pour chaque issue `i`, il calcule `qᵢ = 1 / coteᵢ`, soustrait une marge absolue `α` identique, borne les valeurs négatives à zéro et renormalise les issues complémentaires :

```text
rᵢ = max(0, qᵢ − α)
pᵢ = rᵢ / Σⱼ rⱼ
```

Une issue est ensuite signalée si `pᵢ × coteᵢ > 1`; lorsqu’elles sont mutuellement exclusives, le programme conserve celle au rendement théorique le plus élevé. La CLI fixe `α = 0,03` et emploie les cotes du bookmaker sélectionné aussi bien pour produire les probabilités que pour évaluer le pari.

Ce calcul peut servir de **baseline de dé-vig**, mais il ne constitue pas un modèle indépendant de résultat. Soustraire trois points de probabilité à chaque issue n’est pas équivalent à la marge réelle, qui varie entre opérateurs, marchés et prix. La renormalisation peut donc fabriquer ou masquer une apparente value. Cette piste est à comparer avec la fiche Revue sur la [sensibilité aux méthodes de retrait de marge](../Betting-Dashboard/REV-BLUMMA-02_devig-methode-robuste.md).

## Données et protocole

Il faut disposer des cotes décimales complètes d’un même marché, au même instant, pour toutes les issues, et des résultats officiels. Pour mesurer un pari, conserver séparément le prix réellement exécutable et l’instant de capture.

Comparer `α=0`, les valeurs fixes retenues avant test et au moins une normalisation multiplicative; si possible ajouter un consensus issu d’autres opérateurs. Mesurer la sensibilité de `Σpᵢ`, des probabilités, du nombre de sélections et de `pᵢ × coteᵢ`. Choisir les paramètres uniquement sur une fenêtre d’entraînement chronologique, puis les geler sur la fenêtre suivante.

Publier Brier/log-loss contre les résultats, nombre de paris, rendement net, ROI sur mises risquées, CLV et incertitude par période et par gamme de cote. Un résultat positif sur la même source de prix qui sert à estimer `pᵢ` ne prouve pas un signal prédictif indépendant.

## Évaluation de la source

- Aucun résultat de performance chiffré publié ou reproduit.
- Le backtest du dépôt trie les rencontres par date et utilise des fenêtres chronologiques croissantes, mais compare le modèle de-vig au même bookmaker et ne fournit ni CLV ni intervalles d’incertitude.
- Tests logiciels et dépendances non vérifiés : l’installation npm échoue actuellement faute de version accessible de `pino-ulid`; le détail est dans l’[audit](AUDIT.md).
- La comparaison complète de méthodes de-vig est déjà couverte par [REV-BLUMMA-02](../Betting-Dashboard/REV-BLUMMA-02_devig-methode-robuste.md); cette entrée conserve seulement la variante additive à marge fixe et son implémentation distinctive.

## Verdict

Garder comme **baseline de comparaison**, pas comme stratégie rentable. Ne pas publier de probabilité comme « fair » avant calibration sur des données séparées, datées et représentatives du marché considéré. Licence du code source : MIT; licence et droits sur le flux externe de cotes à vérifier.
