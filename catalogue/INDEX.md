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
| REV-BLUMMA-01 | Football | Cotes / steam | Mouvement Pinnacle et réaction retardée | [Betting-Dashboard](https://github.com/blummabet/Betting-Dashboard) | À étudier | NC | Code et rapports source examinés ; non reproduit | [Fiche](../recherche/football/steam-sharp-softbooks.md) |
| REV-BLUMMA-02 | Multi-sports | Probabilités | Robustesse du de-vig (1N2 et deux issues) | [Betting-Dashboard](https://github.com/blummabet/Betting-Dashboard) | À étudier | NC | Code et rapports source examinés ; non reproduit | [Fiche](../recherche/transversales/devig-methode-robuste.md) |
| REV-BLUMMA-03 | Multi-sports | Sélection | Consensus de signaux anti-corrélés | [Betting-Dashboard](https://github.com/blummabet/Betting-Dashboard) | À étudier | NC | Code et rapports source examinés ; non reproduit | [Fiche](../recherche/transversales/consensus-signaux-independants.md) |
| REV-BLUMMA-04 | Football | 1N2 / totaux | xG, forme domicile/extérieur et voyages | [Betting-Dashboard](https://github.com/blummabet/Betting-Dashboard) | À étudier | NC | Code et rapports source examinés ; non reproduit | [Fiche](../recherche/football/xg-venue-travel.md) |
| REV-BLUMMA-05 | Multi-sports | Calibration / suivi | Apprentissage prospectif des signaux | [Betting-Dashboard](https://github.com/blummabet/Betting-Dashboard) | À étudier | NC | Code et rapports source examinés ; non reproduit | [Fiche](../recherche/transversales/learning-loop.md) |
| REV-BLUMMA-06 | Football | Totaux | Cohérence des marchés et détection d'incohérences | [Betting-Dashboard](https://github.com/blummabet/Betting-Dashboard) | À étudier | NC | Code et rapports source examinés ; non reproduit | [Fiche](../recherche/football/coherence-marche-totaux.md) |
| REV-BLUMMA-07 | Multi-sports | Backtests | Évaluation honnête ROI, Brier, CLV | [Betting-Dashboard](https://github.com/blummabet/Betting-Dashboard) | À étudier | NC | Code et rapports source examinés ; non reproduit | [Fiche](../recherche/transversales/audit-signal-backtests.md) |
| REV-CLAIR-01 | Hockey NHL | Moneyline / totals / puck line | Poisson point-in-time et poids du marché | [Clairvoyance](https://github.com/Purple-Wraith/clairvoyance-backend) | À étudier | NC | Sources ciblées inspectées ; aucun backtest reproduit | [Fiche](../recherche/hockey/nhl-point-in-time-poisson-marche.md) |
| REV-CLAIR-02 | Hockey NHL | Gagnant / total | Gardien confirmé versus gardien principal | [Clairvoyance](https://github.com/Purple-Wraith/clairvoyance-backend) | À étudier | NC | Sources ciblées inspectées ; aucun backtest reproduit | [Fiche](../recherche/hockey/nhl-gardien-titulaire.md) |
| REV-CLAIR-03 | Hockey / NBA | Handicap / O-U | Lignes alternatives : taux de couverture et prix | [Clairvoyance](https://github.com/Purple-Wraith/clairvoyance-backend) | À étudier | NC | Sources ciblées inspectées ; aucun backtest reproduit | [Fiche](../recherche/hockey/lignes-alternatives-ecart.md) |
| REV-CLAIR-04 | Hockey Europe | ML / spreads / O-U | Snapshots QuantHockey et absence de signal validé | [Clairvoyance](https://github.com/Purple-Wraith/clairvoyance-backend) | À étudier | NC | Sources ciblées inspectées ; aucun backtest reproduit | [Fiche](../recherche/hockey/quanthockey-snapshots.md) |
| REV-CLAIR-05 | Tous sports | Contrôle | Séparation pré-match / tardif / inconnu | [Clairvoyance](https://github.com/Purple-Wraith/clairvoyance-backend) | À étudier | NC | Sources ciblées inspectées ; aucun backtest reproduit | [Fiche](../recherche/transversales/audit-locks-pre-match.md) |
| REV-CLAIR-06 | Multi-sports | Modèles / calibration | Ensemble Monte-Carlo / Bayésien / Elo | [Clairvoyance](https://github.com/Purple-Wraith/clairvoyance-backend) | À étudier | NC | Sources ciblées inspectées ; aucun backtest reproduit | [Fiche](../recherche/transversales/ensemble-adaptatif-modeles.md) |
| REV-CLAIR-07 | Hockey NHL | Effectifs | Lissage du niveau des joueurs indisponibles | [Clairvoyance](https://github.com/Purple-Wraith/clairvoyance-backend) | À étudier | NC | Sources ciblées inspectées ; aucun backtest reproduit | [Fiche](../recherche/hockey/nhl-valeur-absences.md) |
| REV-CLAIR-08 | Multi-sports | Architecture | Elo actualisé une fois par match, pas par pick | [Clairvoyance](https://github.com/Purple-Wraith/clairvoyance-backend) | À étudier | NC | Sources ciblées inspectées ; aucun backtest reproduit | [Fiche](../recherche/transversales/elo-actualisation-unique.md) |

## Analyses par source

- [2026-10-09 — Purple-Wraith/clairvoyance-backend](../analyses/2026-10-09_Purple-Wraith_clairvoyance-backend.md) : 8 pistes NHL/hockey/validation et un outil de contrôle original, métriques historiques contaminées par des locks tardifs/inconnus ; aucune copie de source sans licence.

- [2026-10-09 — blummabet/Betting-Dashboard](../analyses/2026-10-09_blummabet_Betting-Dashboard.md) : 7 méthodes documentées. Rapports historiques à ROI négatif, pas de copie de code source (licence non spécifiée).

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
