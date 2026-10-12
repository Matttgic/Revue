# REV-MEZZALA-01 — Dixon–Coles : pondération temporelle et regroupement des équipes rares

- Statut : **À étudier**.
- Sport : football. Marché/usage : 1N2, totaux, scores exacts.
- Sources : [mezzala](AUDIT.md) ; recoupé par [dashee87/blogScripts](../dashee87-blogScripts/AUDIT.md).
- Preuve : lecture ciblée du code ; protocole ci-dessous non exécuté.

## Idée

Trois réglages simples qui manquent souvent aux Dixon–Coles « de tutoriel » :

1. **Décroissance temporelle** : poids exp(−ξ·jours) dans la vraisemblance (mezzala `ExponentialWeight`, dashee87 `xi`).
2. **Regroupement** : les équipes vues moins de N fois (promus, petites ligues) partagent un paramètre (`LumpedAdapter`), au lieu d'une force estimée sur trois matchs.
3. **Blocs** : avantage domicile par ligue ou covariables (`KeyBlock`) ajoutés sans réécrire la vraisemblance.

## Protocole proposé

Sur les championnats du jeu [Club-Football-Match-Data](../Club-Football-Match-Data/AUDIT.md) : choisir ξ et N sur 2010-2018, figer, évaluer 2019-2026 contre la cote Bet365 dé-margée (méthode choisie selon REV-IMPLIED-01). Contraindre ρ pour garder τ positif.

## Limites

dashee87 choisit ξ sur les saisons qu'il rapporte : ne pas reprendre ses valeurs telles quelles. mezzala n'est plus maintenu depuis 2021.
