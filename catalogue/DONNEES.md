# Données de Revue

<!-- Fichier généré par `python -m outils.controles.inventaire_depot` : ne pas éditer à la main. -->

## Où sont les données ?

Toutes les données publiées sont des fichiers JSON dans [`docs/`](../docs). Ce dossier est **aussi la racine du site GitHub Pages**, et les workflows y écrivent directement. Ne pas les déplacer : les pages, l'API (`api_revue/`) et les robots en dépendent.

- **Instantanés** (`*-latest.json`) : remplacés à chaque exécution.
- **Registres** (`*-ledger.json`, `*-history.json`) : historiques en ajout seul ; une prévision figée n'est jamais réécrite.
- **Rapports** (`parite-*`, `*-audit*`, `*-performance.json`) : résultats de vérification et métriques recalculés.

## Règles pour une nouvelle source de données

Documenter : propriétaire, URL, licence/CGU, autorisation d'extraction, sports et marchés, fraîcheur, quota et prix, schéma, fuseau horaire, limites, politique d'archivage. **Aucune clé API, aucun jeton ni donnée personnelle dans Git** : les secrets restent dans les secrets GitHub Actions. Les jeux de données sous licence (Opta, etc.) ne sont jamais publiés.

## Sources externes utilisées

| Source | Usage | Outils |
|---|---|---|
| API officielle NHL (api-web.nhle.com) | Calendrier, scores, statistiques | `outils/collecte/nhl_official_stats_revue.py`, `outils/collecte/scoreboard_revue.py` |
| MoneyPuck (téléchargements CSV, usage non commercial) | xG équipes et gardiens NHL | `outils/collecte/moneypuck_feed.py`, `outils/collecte/moneypuck_goalies_feed.py` |
| ESPN (API publiques site.api.espn.com) | Scores, gardiens probables, stats NBA/football | `outils/collecte/nhl_espn_goalies.py`, `outils/collecte/probe_*.py` |
| MLB Stats API | Lanceurs probables | `outils/collecte/mlb_official_pitchers.py` |
| PulseScore / The Odds API (clé en secret) | Cotes de bookmakers FR observées | `outils/collecte/pulsescore_v2.py`, `outils/suivi/revue_engine_v2.py` |
| Dépôt public Clairvoyance (lecture seule) | Comparaisons de parité, audits | `outils/clairvoyance/` |

## Inventaire (104 fichiers)

### Reproduction Clairvoyance (parité, audits)

| Fichier | Généré | Ko | Publié par | Produit par |
|---|---|---:|---|---|
| [clairvoyance-code-audit.json](../docs/clairvoyance-code-audit.json) | 2026-10-09 23:59 | 106 | audit-clairvoyance.yml | `outils/clairvoyance/audit_clairvoyance_complet.py`, `outils/clairvoyance/catalogue_parite_modeles.py`, `outils/controles/diagnostic_revue.py` |
| [clairvoyance-elo-source-audit.json](../docs/clairvoyance-elo-source-audit.json) | 2026-10-11 03:15 | 2 | phase1-nhl-fidelity.yml | `outils/clairvoyance/clairvoyance_elo_settlement_replay.py`, `outils/clairvoyance/verifier_phase1_nhl.py` |
| [clairvoyance-fixture-reconciliation.json](../docs/clairvoyance-fixture-reconciliation.json) | 2026-10-11 02:10 | 4 | original-fixtures.yml | `outils/clairvoyance/reconcile_reference_fixtures.js` |
| [clairvoyance-nba-advanced-ratings.json](../docs/clairvoyance-nba-advanced-ratings.json) | 2026-10-11 14:18 | 19 | clairvoyance-nba-advanced.yml | `outils/clairvoyance/audit_entrees_clairvoyance.py`, `outils/clairvoyance/nba_ratings_clairvoyance_advanced.py`, `outils/controles/phase11_data_quality.py` |
| [clairvoyance-nba-espn-advanced-cache.json](../docs/clairvoyance-nba-espn-advanced-cache.json) | — | 14 | clairvoyance-nba-advanced.yml | `outils/clairvoyance/nba_ratings_clairvoyance_advanced.py` |
| [clairvoyance-nba-ratings.json](../docs/clairvoyance-nba-ratings.json) | 2026-10-11 03:15 | 19 | clairvoyance-nba-ratings.yml | `outils/clairvoyance/nba_ratings_clairvoyance_live.py` |
| [clairvoyance-nhl-forensics.json](../docs/clairvoyance-nhl-forensics.json) | 2026-10-11 03:15 | 3 | clairvoyance-nhl-forensics.yml | `outils/clairvoyance/clairvoyance_nhl_forensics.py`, `outils/clairvoyance/clairvoyance_nhl_scenarios.py`, `outils/clairvoyance/verifier_phase1_nhl.py` |
| [clairvoyance-nhl-scenarios.json](../docs/clairvoyance-nhl-scenarios.json) | 2026-10-11 03:15 | 2 | clairvoyance-nhl-forensics.yml | `outils/clairvoyance/clairvoyance_nhl_scenarios.py` |
| [clairvoyance-real-output-gap.json](../docs/clairvoyance-real-output-gap.json) | 2026-10-11 03:14 | 28 | clairvoyance-real-output-gap.yml | `outils/clairvoyance/clairvoyance_nhl_forensics.py`, `outils/clairvoyance/clairvoyance_real_output_gap.py`, `outils/clairvoyance/phase4_parite_reelle.py` |
| [clairvoyance-rentabilite-audit.json](../docs/clairvoyance-rentabilite-audit.json) | 2026-10-11 03:14 | 7 | audit-rentabilite-clairvoyance.yml | `outils/clairvoyance/audit_rentabilite_clairvoyance.py` |
| [parite-clairvoyance-espn-nba.json](../docs/parite-clairvoyance-espn-nba.json) | 2026-10-11 03:14 | 0 | parite-nba-espn-source.yml | `outils/clairvoyance/audit_entrees_clairvoyance.py`, `outils/clairvoyance/verifier_parite_nba_espn_source.py` |
| [parite-clairvoyance-frontend.json](../docs/parite-clairvoyance-frontend.json) | 2026-10-11 03:14 | 4 | parite-clairvoyance-predictor.yml | `outils/clairvoyance/audit_reproduction_exacte.py`, `outils/clairvoyance/catalogue_parite_modeles.py`, `outils/clairvoyance/verify_clairvoyance_frontend.js` |
| [parite-clairvoyance-moneypuck-parser.json](../docs/parite-clairvoyance-moneypuck-parser.json) | 2026-10-11 03:14 | 1 | parite-moneypuck-parser.yml | `outils/clairvoyance/audit_entrees_clairvoyance.py`, `outils/clairvoyance/verifier_parite_moneypuck_source.py` |
| [parite-clairvoyance-nba-source.json](../docs/parite-clairvoyance-nba-source.json) | 2026-10-11 03:14 | 1 | parite-clairvoyance-predictor.yml, parite-nba-source.yml | `outils/clairvoyance/catalogue_parite_modeles.py`, `outils/clairvoyance/verifier_parite_nba_source.py` |
| [parite-clairvoyance-nhl-observe.json](../docs/parite-clairvoyance-nhl-observe.json) | 2026-10-11 03:14 | 3 | parite-clairvoyance-predictor.yml, parite-exacte-clairvoyance.yml | `outils/clairvoyance/audit_reproduction_exacte.py`, `outils/clairvoyance/verifier_parite_predictor_nhl_observe.py` |
| [parite-clairvoyance-predictor.json](../docs/parite-clairvoyance-predictor.json) | 2026-10-11 03:14 | 1 | parite-clairvoyance-predictor.yml | `outils/clairvoyance/audit_reproduction_exacte.py`, `outils/clairvoyance/catalogue_parite_modeles.py`, `outils/clairvoyance/verifier_parite_clairvoyance.py` |
| [parite-clairvoyance-timing.json](../docs/parite-clairvoyance-timing.json) | 2026-10-11 03:15 | 1 | parite-clairvoyance-timing.yml | — |
| [parite-donnees-clairvoyance.json](../docs/parite-donnees-clairvoyance.json) | 2026-10-11 03:14 | 2 | audit-donnees-clairvoyance.yml | `outils/clairvoyance/audit_entrees_clairvoyance.py`, `outils/clairvoyance/audit_reproduction_exacte.py`, `outils/clairvoyance/verifier_phase1_nhl.py` |
| [parite-elo-mlb-source.json](../docs/parite-elo-mlb-source.json) | 2026-10-11 03:14 | 1 | parite-clairvoyance-predictor.yml, parite-exacte-clairvoyance.yml | `outils/clairvoyance/audit_reproduction_exacte.py`, `outils/clairvoyance/verifier_parite_elo_mlb_source.py` |
| [parite-modeles-clairvoyance.json](../docs/parite-modeles-clairvoyance.json) | 2026-10-11 03:14 | 21 | parite-clairvoyance-predictor.yml | `outils/clairvoyance/audit_reproduction_exacte.py`, `outils/clairvoyance/catalogue_parite_modeles.py`, `outils/clairvoyance/pin_source_parity.py` |
| [parite-nhl-espn-id-map.json](../docs/parite-nhl-espn-id-map.json) | 2026-10-11 03:14 | 3 | parite-clairvoyance-predictor.yml, parite-exacte-clairvoyance.yml | `api_revue/fixtures.py`, `api_revue/paper_picks.py`, `api_revue/research_predictions.py` |
| [parite-nhl-gardiens-publics.json](../docs/parite-nhl-gardiens-publics.json) | 2026-10-11 03:15 | 12 | phase1-nhl-fidelity.yml | `outils/clairvoyance/parite_nhl_gardiens_publics.py`, `outils/clairvoyance/verifier_phase1_nhl.py` |
| [parite-nhl-source-style.json](../docs/parite-nhl-source-style.json) | 2026-10-11 03:15 | 1 | parite-nhl-source-style.yml | `outils/clairvoyance/verifier_parite_nhl_source_style.py` |
| [phase1-nhl-fidelity.json](../docs/phase1-nhl-fidelity.json) | 2026-10-11 03:15 | 3 | phase1-nhl-fidelity.yml | `outils/clairvoyance/verifier_phase1_nhl.py` |
| [phase4-evidence-latest.json](../docs/phase4-evidence-latest.json) | 2026-10-11 11:34 | 2 | phase4-parite-reelle.yml | `outils/clairvoyance/phase4_parite_reelle.py` |
| [phase6-predictions-latest.json](../docs/phase6-predictions-latest.json) | 2026-10-12 01:25 | 30 | phase6-predictions.yml | `outils/clairvoyance/phase6_comparaison_pregame.py`, `outils/controles/phase9_acceptation_production.py` |
| [phase6-pregame-ledger.json](../docs/phase6-pregame-ledger.json) | — | 29 | phase6-predictions.yml | `outils/clairvoyance/phase6_comparaison_pregame.py`, `outils/controles/phase7_cotes_et_bilan.py` |
| [reproduction-exacte-audit.json](../docs/reproduction-exacte-audit.json) | 2026-10-11 03:05 | 17 | parite-exacte-clairvoyance.yml | `api_revue/app.py`, `outils/clairvoyance/audit_reproduction_exacte.py` |

### NHL

| Fichier | Généré | Ko | Publié par | Produit par |
|---|---|---:|---|---|
| [moneypuck-goalies-latest.json](../docs/moneypuck-goalies-latest.json) | 2026-10-11 13:26 | 54 | moneypuck-official.yml, nhl-clairvoyance-moneypuck-shadow.yml | `outils/clairvoyance/nhl_source_input_gap.py`, `outils/collecte/moneypuck_goalies_feed.py`, `outils/controles/etat_donnees_revue.py` |
| [moneypuck-nhl-latest.json](../docs/moneypuck-nhl-latest.json) | 2026-10-11 13:26 | 43 | moneypuck-official.yml, nhl-clairvoyance-moneypuck-shadow.yml | `api_revue/nhl_stats.py`, `api_revue/operational.py`, `outils/clairvoyance/nhl_backend_source_style.py` |
| [moneypuck-progress.json](../docs/moneypuck-progress.json) | 2026-10-10 01:10 | 3 | — | — |
| [nhl-backend-source-style-latest.json](../docs/nhl-backend-source-style-latest.json) | 2026-10-11 11:34 | 6 | nhl-backend-source-style.yml, parite-nhl-source-style.yml | `outils/clairvoyance/nhl_backend_source_style.py`, `outils/clairvoyance/phase4_parite_reelle.py`, `outils/clairvoyance/verifier_parite_nhl_source_style.py` |
| [nhl-calibration-latest.json](../docs/nhl-calibration-latest.json) | 2026-10-11 05:39 | 3 | nhl-settlement-officiel.yml | `outils/suivi/nhl_calibration_prospective.py` |
| [nhl-clairvoyance-shadow-latest.json](../docs/nhl-clairvoyance-shadow-latest.json) | 2026-10-11 20:58 | 12 | nhl-clairvoyance-moneypuck-shadow.yml | `api_revue/research_predictions.py`, `outils/clairvoyance/clairvoyance_nhl_forensics.py`, `outils/clairvoyance/clairvoyance_nhl_scenarios.py` |
| [nhl-espn-goalies-latest.json](../docs/nhl-espn-goalies-latest.json) | 2026-10-11 22:50 | 3 | nhl-espn-goalies.yml | `outils/clairvoyance/parite_nhl_gardiens_publics.py`, `outils/collecte/nhl_espn_goalies.py`, `outils/controles/etat_donnees_revue.py` |
| [nhl-frontend-observed-latest.json](../docs/nhl-frontend-observed-latest.json) | 2026-10-11 22:27 | 8 | nhl-frontend-observed.yml | `outils/collecte/nhl_espn_goalies.py`, `outils/controles/etat_donnees_revue.py`, `outils/suivi/nhl_frontend_observed.js` |
| [nhl-frontend-prospective-ledger.json](../docs/nhl-frontend-prospective-ledger.json) | 2026-10-11 23:45 | 19 | nhl-frontend-prospective.yml | `outils/suivi/nhl_frontend_tracker.py` |
| [nhl-frontend-prospective-performance.json](../docs/nhl-frontend-prospective-performance.json) | 2026-10-11 23:45 | 1 | nhl-frontend-prospective.yml | `outils/clairvoyance/verifier_phase1_nhl.py`, `outils/controles/etat_donnees_revue.py`, `outils/suivi/nhl_frontend_tracker.py` |
| [nhl-model-latest.json](../docs/nhl-model-latest.json) | 2026-10-11 23:50 | 22 | multisports-independent.yml, nhl-independent.yml | `modeles/simulations/multisports_independant.py`, `modeles/simulations/nhl_independant.py`, `modeles/simulations/nhl_joueurs_independant.py` |
| [nhl-official-stats-latest.json](../docs/nhl-official-stats-latest.json) | 2026-10-11 23:44 | 311 | nhl-official-stats.yml | `api_revue/nhl_stats.py`, `api_revue/operational.py`, `outils/clairvoyance/nhl_backend_source_style.py` |
| [nhl-players-latest.json](../docs/nhl-players-latest.json) | 2026-10-11 23:50 | 162 | multisports-independent.yml | `modeles/simulations/nhl_joueurs_independant.py`, `outils/publication/match_center_revue.py` |
| [nhl-shadow-ledger.json](../docs/nhl-shadow-ledger.json) | 2026-10-11 20:58 | 26 | nhl-clairvoyance-moneypuck-shadow.yml, nhl-settlement-officiel.yml | `outils/publication/match_center_revue.py`, `outils/suivi/clairvoyance_nhl_moneypuck_shadow.py`, `outils/suivi/nhl_calibration_prospective.py` |
| [nhl-shadow-performance.json](../docs/nhl-shadow-performance.json) | 2026-10-11 20:58 | 1 | nhl-clairvoyance-moneypuck-shadow.yml, nhl-settlement-officiel.yml | `outils/suivi/clairvoyance_nhl_moneypuck_shadow.py`, `outils/suivi/nhl_settlement_officiel.py` |
| [nhl-source-input-delta.json](../docs/nhl-source-input-delta.json) | 2026-10-10 17:27 | 25 | nhl-source-input-gap.yml | `outils/clairvoyance/nhl_source_input_gap.py` |

### Football

| Fichier | Généré | Ko | Publié par | Produit par |
|---|---|---:|---|---|
| [football-advanced-shadow.json](../docs/football-advanced-shadow.json) | 2026-10-11 23:50 | 17 | multisports-independent.yml | `modeles/simulations/football_avance_independant.py`, `outils/controles/diagnostic_revue.py`, `outils/controles/phase11_data_quality.py` |
| [football-espn-stat-cache.json](../docs/football-espn-stat-cache.json) | 2026-10-11 23:50 | 325 | multisports-independent.yml | `modeles/simulations/football_espn_statistiques.py` |
| [football-espn-team-features.json](../docs/football-espn-team-features.json) | 2026-10-11 23:50 | 72 | multisports-independent.yml | `modeles/simulations/football_avance_independant.py`, `modeles/simulations/football_espn_statistiques.py`, `outils/clairvoyance/audit_entrees_clairvoyance.py` |
| [football-shadow-ledger.json](../docs/football-shadow-ledger.json) | — | 35 | multisports-independent.yml | `outils/suivi/suivi_football_avance.py` |
| [football-shadow-performance.json](../docs/football-shadow-performance.json) | 2026-10-11 23:50 | 3 | multisports-independent.yml | `outils/suivi/suivi_football_avance.py` |

### NBA / MLB

| Fichier | Généré | Ko | Publié par | Produit par |
|---|---|---:|---|---|
| [mlb-official-probable-pitchers-latest.json](../docs/mlb-official-probable-pitchers-latest.json) | 2026-10-11 23:01 | 3 | phase11-data-quality.yml | `outils/collecte/mlb_official_pitchers.py`, `outils/controles/phase11_data_quality.py`, `outils/publication/match_center_revue.py` |
| [mlb-source-elo-gap.json](../docs/mlb-source-elo-gap.json) | 2026-10-11 17:48 | 3 | mlb-source-elo-gap.yml | `outils/clairvoyance/mlb_source_elo_gap.py`, `outils/controles/phase11_data_quality.py`, `outils/controles/phase5_donnees_multisports.py` |
| [nba-prior-shadow.json](../docs/nba-prior-shadow.json) | 2026-10-11 23:50 | 10 | multisports-independent.yml | `modeles/simulations/nba_prior_espn.py`, `outils/suivi/phase10_modeles_multisports.py` |
| [nba-prior-standings.json](../docs/nba-prior-standings.json) | — | 8 | multisports-independent.yml | `modeles/simulations/nba_prior_espn.py`, `outils/clairvoyance/nba_ratings_clairvoyance_advanced.py`, `outils/clairvoyance/nba_ratings_clairvoyance_live.py` |

### Hockey européen

| Fichier | Généré | Ko | Publié par | Produit par |
|---|---|---:|---|---|
| [euro-hockey-latest.json](../docs/euro-hockey-latest.json) | 2026-10-12 01:22 | 2 | euro-hockey-source.yml | `outils/clairvoyance/euro_hockey_reference_feed.js` |
| [euro-hockey-prospective-ledger.json](../docs/euro-hockey-prospective-ledger.json) | — | 10 | euro-hockey-source.yml | `outils/clairvoyance/euro_hockey_reference_feed.js` |
| [euro-hockey-prospective-performance.json](../docs/euro-hockey-prospective-performance.json) | 2026-10-12 01:22 | 1 | euro-hockey-source.yml | `outils/clairvoyance/euro_hockey_reference_feed.js` |

### Sports individuels

| Fichier | Généré | Ko | Publié par | Produit par |
|---|---|---:|---|---|
| [individual-history.json](../docs/individual-history.json) | — | 398 | multisports-independent.yml | `modeles/simulations/sports_individuels_et_liiga.py`, `outils/suivi/individual_prospective_revue.py` |
| [individual-latest.json](../docs/individual-latest.json) | 2026-10-11 23:50 | 4 | multisports-independent.yml | `modeles/simulations/multisports_independant.py`, `modeles/simulations/sports_individuels_et_liiga.py`, `outils/suivi/individual_prospective_revue.py` |
| [individual-prospective-ledger.json](../docs/individual-prospective-ledger.json) | — | 5 | individual-prospective.yml, multisports-independent.yml | `outils/suivi/individual_prospective_revue.py` |
| [individual-prospective-performance.json](../docs/individual-prospective-performance.json) | 2026-10-12 00:00 | 1 | individual-prospective.yml, multisports-independent.yml | `outils/suivi/individual_prospective_revue.py` |

### Cotes et journal papier

| Fichier | Généré | Ko | Publié par | Produit par |
|---|---|---:|---|---|
| [engine-v2-latest.json](../docs/engine-v2-latest.json) | 2026-10-12 01:29 | 83 | revue-engine-v2.yml | `api_revue/operational.py`, `outils/clairvoyance/audit_entrees_clairvoyance.py`, `outils/controles/controle_couverture_cotes.py` |
| [engine-v2-ledger.json](../docs/engine-v2-ledger.json) | — | 92 | donnees-prioritaires.yml, revue-engine-v2.yml | `api_revue/operational.py`, `api_revue/paper_picks.py`, `outils/clairvoyance/clairvoyance_elo_settlement_replay.py` |
| [paper-score-settlement-latest.json](../docs/paper-score-settlement-latest.json) | 2026-10-12 01:03 | 1 | donnees-prioritaires.yml | `outils/controles/etat_donnees_revue.py`, `outils/suivi/reglement_multisport_officiel.py` |
| [phase7-prices-performance-latest.json](../docs/phase7-prices-performance-latest.json) | 2026-10-11 22:28 | 18 | phase7-cotes-et-bilan.yml | `outils/controles/phase7_cotes_et_bilan.py`, `outils/controles/phase9_acceptation_production.py` |
| [picks-center-latest.json](../docs/picks-center-latest.json) | 2026-10-12 01:30 | 39 | donnees-prioritaires.yml, picks-center-revue.yml | `outils/controles/etat_donnees_revue.py`, `outils/controles/phase11_data_quality.py`, `outils/controles/phase14_reception.py` |
| [pulsescore-connection-status.json](../docs/pulsescore-connection-status.json) | — | 0 | check-pulsescore.yml | `outils/collecte/check_pulsescore_connection.py` |
| [pulsescore-diagnostic-latest.json](../docs/pulsescore-diagnostic-latest.json) | 2026-10-12 01:07 | 78 | diagnostic-pulsescore.yml | `outils/collecte/diagnostic_pulsescore.py` |
| [pulsescore-radar-latest.json](../docs/pulsescore-radar-latest.json) | 2026-10-12 01:15 | 1 | pulsescore-radar-6h.yml | `outils/collecte/pulsescore_radar_six_heures.py`, `outils/controles/controle_couverture_cotes.py`, `outils/controles/etat_donnees_revue.py` |
| [revue-control-ledger-latest.json](../docs/revue-control-ledger-latest.json) | 2026-10-12 01:30 | 39 | donnees-prioritaires.yml, revue-control-export.yml | `outils/controles/etat_donnees_revue.py`, `outils/publication/picks_center_revue.py`, `outils/publication/publier_revue_control.py` |
| [revue-control-state-latest.json](../docs/revue-control-state-latest.json) | 2026-10-12 01:30 | 2 | donnees-prioritaires.yml, revue-control-export.yml | `outils/publication/publier_revue_control.py` |
| [revue-crossbook-latest.json](../docs/revue-crossbook-latest.json) | 2026-10-12 01:03 | 1 | donnees-prioritaires.yml | `outils/controles/controle_couverture_cotes.py`, `outils/controles/etat_donnees_revue.py` |

### Modèles multisports et évaluation

| Fichier | Généré | Ko | Publié par | Produit par |
|---|---|---:|---|---|
| [backtests-multisports.json](../docs/backtests-multisports.json) | 2026-10-11 23:50 | 6 | multisports-independent.yml | `outils/clairvoyance/audit_clairvoyance_complet.py`, `outils/suivi/backtest_multisports.py` |
| [ensemble-mc-bayes-latest.json](../docs/ensemble-mc-bayes-latest.json) | 2026-10-11 23:50 | 17 | multisports-independent.yml | `modeles/simulations/ensemble_montecarlo_bayes.py`, `outils/publication/match_center_revue.py`, `outils/suivi/phase2_historique_autonome.py` |
| [ensemble-mc-bayes-ledger.json](../docs/ensemble-mc-bayes-ledger.json) | — | 18 | multisports-independent.yml | `outils/suivi/suivi_ensemble.py` |
| [ensemble-mc-bayes-performance.json](../docs/ensemble-mc-bayes-performance.json) | 2026-10-11 23:50 | 2 | multisports-independent.yml | `outils/suivi/suivi_ensemble.py` |
| [equipes-avance-shadow.json](../docs/equipes-avance-shadow.json) | 2026-10-11 23:50 | 13 | multisports-independent.yml | `modeles/simulations/equipes_avance_multisports.py`, `outils/controles/diagnostic_revue.py`, `outils/suivi/phase2_historique_autonome.py` |
| [multisport-prospective-ledger.json](../docs/multisport-prospective-ledger.json) | — | 55 | match-center-revue.yml | `outils/publication/revue_match_dossiers.py`, `outils/suivi/prospectif_multisports_revue.py` |
| [multisport-prospective-performance.json](../docs/multisport-prospective-performance.json) | 2026-10-12 01:30 | 1 | match-center-revue.yml | `outils/suivi/prospectif_multisports_revue.py` |
| [multisports-history.json](../docs/multisports-history.json) | — | 200 | multisports-independent.yml, revue-engine-v2.yml | `api_revue/mlb_elo.py`, `modeles/simulations/ensemble_montecarlo_bayes.py`, `modeles/simulations/equipes_avance_multisports.py` |
| [multisports-latest.json](../docs/multisports-latest.json) | 2026-10-11 23:50 | 40 | multisports-independent.yml, revue-engine-v2.yml | `api_revue/app.py`, `api_revue/fixtures.py`, `api_revue/operational.py` |
| [phase10-modeles-multisports-latest.json](../docs/phase10-modeles-multisports-latest.json) | 2026-10-12 01:30 | 27 | match-center-revue.yml | `outils/publication/match_center_revue.py`, `outils/suivi/phase10_modeles_multisports.py`, `outils/suivi/phase10_validation_prospective.py` |
| [phase10-modeles-performance.json](../docs/phase10-modeles-performance.json) | 2026-10-12 01:30 | 3 | match-center-revue.yml | `outils/controles/phase11_data_quality.py`, `outils/controles/phase14_reception.py`, `outils/suivi/phase10_validation_prospective.py` |
| [phase10-modeles-prospectif-ledger.json](../docs/phase10-modeles-prospectif-ledger.json) | — | 91 | match-center-revue.yml | `outils/suivi/phase10_validation_prospective.py`, `outils/suivi/phase12_audit.py`, `outils/suivi/phase12_official_finals.py` |
| [phase12-official-finals-latest.json](../docs/phase12-official-finals-latest.json) | 2026-10-12 01:30 | 1 | match-center-revue.yml | `outils/suivi/phase10_validation_prospective.py`, `outils/suivi/phase12_official_finals.py` |
| [phase12-reconciliation-latest.json](../docs/phase12-reconciliation-latest.json) | 2026-10-12 01:30 | 1 | match-center-revue.yml | `outils/suivi/phase10_validation_prospective.py`, `outils/suivi/phase12_audit.py` |
| [phase12-result-integrity-latest.json](../docs/phase12-result-integrity-latest.json) | 2026-10-12 01:30 | 3 | match-center-revue.yml | `outils/controles/phase14_reception.py`, `outils/suivi/phase12_audit.py`, `outils/suivi/phase13_comparaison_modeles.py` |
| [phase13-modeles-evaluation-latest.json](../docs/phase13-modeles-evaluation-latest.json) | 2026-10-12 01:30 | 33 | match-center-revue.yml | `outils/controles/phase14_reception.py`, `outils/suivi/phase13_comparaison_modeles.py` |
| [phase2-owned-ledger.json](../docs/phase2-owned-ledger.json) | 2026-10-12 01:03 | 85 | phase2-historique-autonome.yml | `outils/suivi/phase2_historique_autonome.py` |
| [phase2-owned-performance.json](../docs/phase2-owned-performance.json) | 2026-10-12 01:03 | 11 | phase2-historique-autonome.yml | `outils/controles/etat_donnees_revue.py`, `outils/controles/phase9_acceptation_production.py`, `outils/suivi/phase2_historique_autonome.py` |
| [revue-model-quality-latest.json](../docs/revue-model-quality-latest.json) | 2026-10-12 01:03 | 4 | donnees-prioritaires.yml | `outils/controles/etat_donnees_revue.py`, `outils/suivi/evaluation_prospective_papier.py` |
| [scoreboard-revue-latest.json](../docs/scoreboard-revue-latest.json) | 2026-10-12 01:30 | 20 | donnees-prioritaires.yml, match-center-revue.yml | `api_revue/fixtures.py`, `outils/collecte/scoreboard_revue.py`, `outils/controles/etat_donnees_revue.py` |

### Écrans et dossiers de match

| Fichier | Généré | Ko | Publié par | Produit par |
|---|---|---:|---|---|
| [arcade-v3-qa.json](../docs/arcade-v3-qa.json) | 2026-10-12 01:03 | 1 | arcade-v3-tests.yml | — |
| [match-center-latest.json](../docs/match-center-latest.json) | 2026-10-12 01:30 | 220 | donnees-prioritaires.yml, match-center-revue.yml | `api_revue/operational.py`, `outils/clairvoyance/clairvoyance_real_output_gap.py`, `outils/clairvoyance/phase6_comparaison_pregame.py` |
| [match-dossiers-latest.json](../docs/match-dossiers-latest.json) | 2026-10-12 01:30 | 365 | donnees-prioritaires.yml, match-center-revue.yml | `api_revue/game_dossiers.py`, `outils/publication/revue_match_dossiers.py` |

### État du dépôt et recette

| Fichier | Généré | Ko | Publié par | Produit par |
|---|---|---:|---|---|
| [banc-nhl-cloture.json](../docs/banc-nhl-cloture.json) | — | 20 | — | `outils/suivi/banc_nhl_cloture.py` |
| [etat-donnees-latest.json](../docs/etat-donnees-latest.json) | 2026-10-12 01:03 | 6 | donnees-prioritaires.yml | `outils/controles/etat_donnees_revue.py` |
| [github-workflows-latest.json](../docs/github-workflows-latest.json) | 2026-10-11 13:11 | 53 | github-actions-monitor.yml | `api_revue/admin_readonly.py`, `outils/controles/github_actions_monitor.py` |
| [health-latest.json](../docs/health-latest.json) | 2026-10-11 20:22 | 2 | health-revue.yml | `api_revue/operational.py`, `outils/controles/diagnostic_revue.py`, `outils/controles/phase9_acceptation_production.py` |
| [phase11-source-quality-latest.json](../docs/phase11-source-quality-latest.json) | 2026-10-11 23:01 | 10 | phase11-data-quality.yml | `outils/controles/phase11_data_quality.py`, `outils/controles/phase14_reception.py` |
| [phase14-readiness-latest.json](../docs/phase14-readiness-latest.json) | 2026-10-12 01:30 | 2 | phase14-finalisation.yml | `outils/controles/phase14_reception.py` |
| [phase5-sources-latest.json](../docs/phase5-sources-latest.json) | 2026-10-11 11:34 | 4 | phase5-donnees-multisports.yml | `outils/controles/phase11_data_quality.py`, `outils/controles/phase5_donnees_multisports.py` |
| [phase9-readiness-latest.json](../docs/phase9-readiness-latest.json) | 2026-10-11 11:34 | 1 | phase9-acceptation-production.yml | `outils/controles/phase14_reception.py`, `outils/controles/phase9_acceptation_production.py` |
| [progression-revue.json](../docs/progression-revue.json) | 2026-10-10 17:16 | 28 | — | — |
| [regle-decision-latest.json](../docs/regle-decision-latest.json) | 2026-10-12 01:29 | 2 | regle-decision.yml | `outils/suivi/regle_decision.py` |
