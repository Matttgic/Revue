# REV-STATSEER-02 — Prévoir le volume avant l’efficacité NFL

**Statut : À étudier — analyses rétrospectives publiées, avantage contre la ligne non démontré.**

- **Sport / ligue :** NFL
- **Marché :** props de courses, réceptions et yards des joueurs
- **Hypothèse :** les occasions (carries, targets et rôle) persistent davantage que l’efficacité récente; prévoir le volume, puis appliquer une efficacité régressée au lieu d’extrapoler les yards récents.
- **Origine :** [Stat-Seer, commit `1016bf6`](https://github.com/derekj987/Stat-Seer/tree/1016bf6193c8ef03de1f756202c887baa829d2f1), `analysis/persistence.py`, `analysis/props_projection.py`, `analysis/props_distribution.py`
- **Licence :** aucune licence explicite repérée; aucun code repris

## Éléments publiés

Sur 44 880 semaines-joueurs, l’auteur rapporte une corrélation temporelle de 0,678 pour les carries et 0,623 pour la part des targets, contre 0,058 pour les yards par course et 0,049 pour les yards par cible. Une projection volume × efficacité et une moyenne saison ont des MAE similaires sur les props établis; toutes deux battent la persistance de la semaine précédente d’environ 25 %. Sur les changements de rôle, l’EWMA de volume améliore les yards au sol (+1,1 %, n=503), mais détériore la réception (−2,4 %, n=1 843).

La distribution empirique de `résultat / projection`, ajustée sur les saisons précédentes, produit des couvertures 50/80/90 proches des niveaux visés dans les tests walk-forward publiés. Mais une distribution bien calibrée n’établit pas que le bookmaker est mal pricé. Le test source 2024 contre les lignes de clôture donne seulement 50,2 % de réussite au total (6 457 props) et les plus grands désaccords perdent plus souvent.

## Limites

- Les corrélations décrivent la persistance, pas un effet causal ni un rendement.
- La moyenne saison bat déjà la projection complexe en MAE pour certains marchés; les gains rapportés concernent surtout le benchmark de la dernière semaine.
- Le score n’établit ni calibration des prix réellement proposés, ni CLV positive, ni rentabilité après marge.
- La base de clôture des props est dans Supabase; elle n’est pas un fichier public reproductible avec le dépôt seul.
- L’échantillon de test et les tableaux sont rapportés par l’auteur, non reproduits indépendamment ici.

## Test à conduire

Sur des saisons postérieures laissées de côté, comparer une distribution de volume/efficacité à la moyenne saison, à la persistance et aux cotes sans marge. Verrouiller les prévisions avant match, utiliser la ligne et le prix réellement accessibles, puis rapporter Brier, log loss, calibration, CLV et ROI par marché.

**Verdict :** bonne hypothèse de décomposition pour la recherche de props; les résultats du dépôt indiquent que la prédiction de yards ne bat pas encore les lignes.
