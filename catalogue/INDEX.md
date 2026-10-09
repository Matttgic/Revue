# Catalogue Revue

Ce catalogue contient **uniquement** les méthodes effectivement examinées. Aucun score ni performance n'est inventé.

| ID | Sport | Marché | Stratégie / composant | Source | Statut | Score intérêt /100 | Preuves | Fiche |
|---|---|---|---|---|---|---|---|---|
| REV-NCSUN-01 | Basketball NCAA | Handicaps / totaux | Luck fade + rating drift + ensemble | [ncsun](https://github.com/mkboggs92-cloud/ncsun) | À étudier | NC | JSON backtest d'auteur ; non reproduit | [Fiche](../recherche/basketball/ncaab-luck-fade.md) |
| REV-NCSUN-02 | NFL | Réceptions / yards / TD | Sous + composition active + blend marché | [ncsun](https://github.com/mkboggs92-cloud/ncsun) | À étudier | NC | JSON backtest d'auteur ; non reproduit | [Fiche](../recherche/football-americain/nfl-receiving-props.md) |
| REV-NCSUN-03 | UFC | Moneyline / décision / distance | Cotes d'ouverture et KO fade | [ncsun](https://github.com/mkboggs92-cloud/ncsun) | À étudier | NC | JSON backtest d'auteur ; non reproduit | [Fiche](../recherche/mma/ufc-ko-fade.md) |
| REV-NCSUN-04 | Multi-sports | Infrastructure | Registre commun de paris / CLV / ROI | [ncsun](https://github.com/mkboggs92-cloud/ncsun) | À étudier | NC | Architecture observée ; non implémentée | [Fiche](../recherche/transversales/registre-paris.md) |
| REV-VCHEQUE-01 | Football | 1N2 | Elo, forme et XGBoost multiclasses | [Football-Betting](https://github.com/VCheque/Football-Betting) | À étudier | NC | Code inspecté ; calibration/hors-échantillon non démontrés | [Fiche](../recherche/football/xgboost-elo-1n2.md) |
| REV-VCHEQUE-02 | Football / multisports | EV+ et cotes | Contrôle prix observé vs cote synthétique | [Football-Betting](https://github.com/VCheque/Football-Betting) | À étudier | NC | Bug de cote synthétique démontré algébriquement | [Fiche](../recherche/football/cotes-reelles-et-value.md) |
| REV-VCHEQUE-03 | Football | Données | Pipeline de rafraîchissement et fraîcheur | [Football-Betting](https://github.com/VCheque/Football-Betting) | À étudier | NC | Workflows inspectés et métadonnées datées | [Fiche](../recherche/transversales/pipeline-football-data.md) |
| REV-VCHEQUE-04 | Football | Combinés 1N2 | Probabilités conjointes et corrélations | [Football-Betting](https://github.com/VCheque/Football-Betting) | À étudier | NC | Code statique inspecté ; EV non backtestée | [Fiche](../recherche/football/combine-correlations.md) |

## Analyses par source

- [2026-10-09 — mkboggs92-cloud/ncsun](../analyses/2026-10-09_mkboggs92-cloud_ncsun.md) : 3 historiques disponibles (NCAA, NFL, UFC), méthodes décrites, pipelines non publiés, **licence source non spécifiée : aucune copie de code tiers**.
- [2026-10-09 — VCheque/Football-Betting](../analyses/2026-10-09_VCheque_Football-Betting.md) : 20 features 1N2, Elo, scripts de collecte, audit critique des cotes synthétiques, absence de calibration visible et licence manquante.

## Statuts
- **À étudier** : proposition ou méthode documentée, non implémentée et non auditée indépendamment.
- **Prototype** : idée et implémentation partielle, non vérifiées.
- **Testé** : code/test(s) ou backtest exécuté(s), résultats et limites documentés.
- **Validé hors échantillon** : résultats reproductibles sur données temporellement séparées, sans promesse de performances futures.
- **Rejeté** : code non sûr/inexploitable, stratégie non convaincante, licence bloquante ou résultats non fiables.
- **Déprécié** : composant auparavant retenu mais obsolète.

## Recherche
Classement prioritaire par : sport → marché → stratégie → modèle / méthode → version source. Utiliser les tags `pré-match`, `live`, `cotes`, `EV`, `ML`, `simulation`, `scraping`, `gestion-mise`, `calibration`, `backtest`.

## Évidence attendue
Préciser toujours : **non testé**, **test logiciel réussi**, **backtest historique externe**, **backtest reproduit**, **hors échantillon** ou **suivi en conditions réelles**. Ne pas confondre ces niveaux.
