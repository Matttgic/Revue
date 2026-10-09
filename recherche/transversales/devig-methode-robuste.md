# REV-BLUMMA-02 — Robustesse aux méthodes de retrait de marge

**Statut : À étudier | source https://github.com/blummabet/Betting-Dashboard/blob/main/devig.py**

## Problème
Sur un marché 1N2, retirer la marge du bookmaker par simple normalisation peut répartir trop uniformément celle-ci et créer une valeur apparente sur de longues cotes. L'approche du dépôt compare notamment méthodes multiplicative, additive, puissance, odds-ratio et Shin.

## Ce qu'il faut distinguer
- **Break-even réel :** `1/cote_offerte` (la marge du bookmaker n'est pas à ajouter une seconde fois).
- **Consensus « fair » :** dé-marge des cotes des **issues du même marché, même bookmaker, même heure** ; c'est une estimation, pas une vérité.
- **EV du modèle :** `P_modèle * cote_offerte - 1` si P_modèle est calibrée et la cote effectivement obtenable.
- **Sensibilité :** comparer plusieurs estimations de référence et signaler les conclusions qui changent de signe.

## Protocole
Comparer multiplicative, additive (qui peut être invalide pour longshots), puissance et Shin/odds-ratio via bibliothèques et références autorisées. Tester sur gammes de cotes extrêmes, marché 1N2 et deux issues. Vérifier `∑p = 1`, bornes, dates, méthode et disponibilité de prix.

**Pas de preuve :** diverger entre méthodes prouve une incertitude de retrait de marge, pas l'existence d'une value exploitable.

**Outil Revue original :** [outils/sensibilite_devig.py](../../outils/sensibilite_devig.py), si disponible, pour comparaison limitée (multiplicative/additive/puissance) ; jamais recopier la source.
