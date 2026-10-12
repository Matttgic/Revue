# Outils Revue

<!-- Fichier généré par `python -m outils.controles.inventaire_depot` : ne pas éditer à la main. -->

Scripts **écrits pour Revue** (aucun code tiers recopié), rangés par fonction. Chaque script se lance depuis la racine du dépôt : `python -m outils.<groupe>.<script>` ou `node outils/<groupe>/<script>.js`. Les tests sont dans [`tests/`](../tests).

| Groupe | Rôle | Scripts |
|---|---|---:|
| [`clairvoyance/`](#clairvoyance) | Reproduction et audit de Clairvoyance | 46 |
| [`collecte/`](#collecte) | Collecte de données | 16 |
| [`suivi/`](#suivi) | Suivi prospectif, règlement et évaluation | 26 |
| [`controles/`](#controles) | Contrôles qualité | 16 |
| [`publication/`](#publication) | Publication du site | 4 |

## clairvoyance

**Reproduction et audit de Clairvoyance.** Comparaisons exactes avec le code source original (checkout temporaire en lecture seule), audits de ses données, de ses sorties et de sa rentabilité affichée.

| Script | Objet |
|---|---|
| [audit_clairvoyance_complet.py](clairvoyance/audit_clairvoyance_complet.py) | Static-only codebase inventory of public Clairvoyance source. |
| [audit_entrees_clairvoyance.py](clairvoyance/audit_entrees_clairvoyance.py) | Read-only coverage audit for REPRODUCING Clairvoyance input datasets. |
| [audit_rentabilite_clairvoyance.py](clairvoyance/audit_rentabilite_clairvoyance.py) | Audit indépendant de la rentabilité affichée par Clairvoyance. |
| [audit_reproduction_exacte.py](clairvoyance/audit_reproduction_exacte.py) | Strict, reproducible audit of Clairvoyance full-stack reproduction. |
| [catalogue_parite_modeles.py](clairvoyance/catalogue_parite_modeles.py) | Source-vs-Revue reproduction catalogue, never a whole-repo completion claim. |
| [clairvoyance_elo_settlement_replay.py](clairvoyance/clairvoyance_elo_settlement_replay.py) | Audit and *independent* Elo reconstruction matching Clairvoyance settlement rules. |
| [clairvoyance_nhl_forensics.py](clairvoyance/clairvoyance_nhl_forensics.py) | NHL source-input forensics: independently explain measured Clairvoyance gaps. |
| [clairvoyance_nhl_scenarios.py](clairvoyance/clairvoyance_nhl_scenarios.py) | Independent original-backend NHL model sensitivity on real observed match inputs. |
| [clairvoyance_real_output_gap.py](clairvoyance/clairvoyance_real_output_gap.py) | Public-source-versus-Revue fixture and NHL prediction output bridge. |
| [euro_hockey_reference_feed.js](clairvoyance/euro_hockey_reference_feed.js) | Independent Revue read-only adapter from published reference hockey fixtures. |
| [inspecter_fonctions_clairvoyance.py](clairvoyance/inspecter_fonctions_clairvoyance.py) | One-off READ-ONLY local inspector for a checked-out public JS app. |
| [mlb_source_elo_gap.py](clairvoyance/mlb_source_elo_gap.py) | MLB original predictor sensitivity to unavailable original SQL Elo ratings. |
| [nba_ratings_clairvoyance_advanced.py](clairvoyance/nba_ratings_clairvoyance_advanced.py) | Source-faithful real NBA ESPN team advanced stats and Elo for Clairvoyance. |
| [nba_ratings_clairvoyance_live.py](clairvoyance/nba_ratings_clairvoyance_live.py) | Publish REAL ESPN inputs through the verified Clairvoyance NBA rating formula. |
| [nhl_backend_source_style.py](clairvoyance/nhl_backend_source_style.py) | Research-only NHL calculation with publicly observable backend-style inputs. |
| [nhl_source_input_gap.py](clairvoyance/nhl_source_input_gap.py) | Quantify NHL data-input gaps without changing historical frozen predictions. |
| [parite_calendrier_nhl_espn.py](clairvoyance/parite_calendrier_nhl_espn.py) | Reconcile factual ESPN and NHL official fixture identifiers, without copying picks. |
| [parite_nhl_gardiens_publics.py](clairvoyance/parite_nhl_gardiens_publics.py) | Read-only NHL published GOALIE observation comparison against public Clairvoyance. |
| [phase4_parite_reelle.py](clairvoyance/phase4_parite_reelle.py) | Phase 4: compare published Clairvoyance observations with Revue research. |
| [phase6_comparaison_pregame.py](clairvoyance/phase6_comparaison_pregame.py) | Phase 6 — prospective public-output comparison across four sports. |
| [pin_source_parity.py](clairvoyance/pin_source_parity.py) | Pin exact checked source files, not unrelated data-only GitHub commits. |
| [reconcile_reference_fixtures.js](clairvoyance/reconcile_reference_fixtures.js) | Reconcile NHL/NBA/MLB fixtures published by the public Clairvoyance data.json with Revue fixtures (identity, kickoff). |
| [verifier_parite_clairvoyance.py](clairvoyance/verifier_parite_clairvoyance.py) | Compare reconstructed predictors against the checked-out PUBLIC reference. |
| [verifier_parite_elo_mlb_source.py](clairvoyance/verifier_parite_elo_mlb_source.py) | Check EVERY historical Revue MLB Elo update against current original source. |
| [verifier_parite_moneypuck_source.py](clairvoyance/verifier_parite_moneypuck_source.py) | Exact row-parsing comparison against ORIGINAL Clairvoyance MoneyPuck parser. |
| [verifier_parite_nba_espn_source.py](clairvoyance/verifier_parite_nba_espn_source.py) | Direct strict source parity for ESPN byteam parsing and advanced team ratings. |
| [verifier_parite_nba_source.py](clairvoyance/verifier_parite_nba_source.py) | CI parity check against 4 real source-side NBA preprocessing functions. |
| [verifier_parite_nhl_source_style.py](clairvoyance/verifier_parite_nhl_source_style.py) | NHL source-style parity checks executed against the ORIGINAL predictor. |
| [verifier_parite_predictor_nhl_observe.py](clairvoyance/verifier_parite_predictor_nhl_observe.py) | Real NHL fixture input-output parity versus current original predictor. |
| [verifier_parite_timing_clairvoyance.py](clairvoyance/verifier_parite_timing_clairvoyance.py) | Différentiel automatique avec le classificateur du dépôt original. |
| [verifier_phase1_nhl.py](clairvoyance/verifier_phase1_nhl.py) | Acceptance gate for Phase 1 NHL fidelity, using traceable Revue evidence. |
| [verify_clairvoyance_euro_hockey.js](clairvoyance/verify_clairvoyance_euro_hockey.js) | Strict side-by-side parity of four European-hockey rate functions. |
| [verify_clairvoyance_euro_hockey_ensemble.js](clairvoyance/verify_clairvoyance_euro_hockey_ensemble.js) | Direct source-vs-reconstructed four Euro hockey log5/MC market ensembles. |
| [verify_clairvoyance_euro_hockey_matches.js](clairvoyance/verify_clairvoyance_euro_hockey_matches.js) | Source-vs-replica verification of Clairvoyance's entire 4 EU hockey MC match calculations. |
| [verify_clairvoyance_frontend.js](clairvoyance/verify_clairvoyance_frontend.js) | Source-vs-replica function equality tests on a read-only checkout. |
| [verify_clairvoyance_hockey_helpers.js](clairvoyance/verify_clairvoyance_hockey_helpers.js) | Compare six independently implemented hockey helpers against the original JS. |
| [verify_clairvoyance_hockey_market.js](clairvoyance/verify_clairvoyance_hockey_market.js) | Compare original Clairvoyance no-vig/logit market blend on the same data. |
| [verify_clairvoyance_injury_impact.js](clairvoyance/verify_clairvoyance_injury_impact.js) | Behaviour parity with original computeInjuryImpact, all supported major sports except CFB. |
| [verify_clairvoyance_nba_props.js](clairvoyance/verify_clairvoyance_nba_props.js) | Original-vs-independent props: compare numeric picks, not expressive text. |
| [verify_clairvoyance_nhl.js](clairvoyance/verify_clairvoyance_nhl.js) | Read-only, deterministic parity verifier for original NHL MC and NHL Ens. |
| [verify_clairvoyance_nhl_goalie_form.js](clairvoyance/verify_clairvoyance_nhl_goalie_form.js) | Direct outcome parity with original NHL goalie data patch and 5-game form. |
| [verify_clairvoyance_player_line.js](clairvoyance/verify_clairvoyance_player_line.js) | Source-vs-replica parity of the original _modelLineForProp NBA player-line function. |
| [verify_clairvoyance_soccer_analytic.js](clairvoyance/verify_clairvoyance_soccer_analytic.js) | Exact tests against original _poissonOverProb/_socSpreadProb family. |
| [verify_clairvoyance_soccer_fbref.js](clairvoyance/verify_clairvoyance_soccer_fbref.js) | Read-only source comparisons for _socXGFromFBref and UEFA blending. |
| [verify_clairvoyance_soccer_form.js](clairvoyance/verify_clairvoyance_soccer_form.js) | Direct source-output comparisons for two original Clairvoyance JS form functions. |
| [verify_clairvoyance_soccer_xg.js](clairvoyance/verify_clairvoyance_soccer_xg.js) | Check source vs independently derived xG formula incl FBref/Opta/CL pipeline. |

## collecte

**Collecte de données.** Acquisition des données externes : MoneyPuck, API NHL, ESPN, MLB Stats, PulseScore, cotes FR. Sondes de structure des API.

| Script | Objet |
|---|---|
| [check_pulsescore_connection.py](collecte/check_pulsescore_connection.py) | One-request PulseScore credential/entitlement smoke test. |
| [diagnostic_pulsescore.py](collecte/diagnostic_pulsescore.py) | Diagnostic PulseScore : pourquoi un bookmaker ne se rattache pas aux matchs Revue. |
| [mlb_official_pitchers.py](collecte/mlb_official_pitchers.py) | Phase 11: no-cost read-only MLB Stats API prospective probable pitchers. |
| [moneypuck_feed.py](collecte/moneypuck_feed.py) | MoneyPuck official-download NHL team metrics for Revue (personal, non-commercial). |
| [moneypuck_goalies_feed.py](collecte/moneypuck_goalies_feed.py) | Derived MoneyPuck NHL goalie metrics from official non-commercial CSV downloads. |
| [nhl_espn_goalies.py](collecte/nhl_espn_goalies.py) | Read-only ESPN NHL probable-starting-goalie observations joined to NHL game IDs. |
| [nhl_official_stats_revue.py](collecte/nhl_official_stats_revue.py) | Read-only official NHL Stats REST source snapshot for Clairvoyance field contracts. |
| [probe_espn_football_stats.py](collecte/probe_espn_football_stats.py) | Metadata-only diagnostic of ESPN soccer match statistics; NOT an Opta API. |
| [probe_espn_hockey.py](collecte/probe_espn_hockey.py) | One-time structure probe for ESPN NHL public stats. |
| [probe_nba_espn_byteam.py](collecte/probe_nba_espn_byteam.py) | Read-only diagnostic for NBA ESPN regular-season advanced stats. |
| [probe_nba_espn_standings.py](collecte/probe_nba_espn_standings.py) | Read-only diagnostic: ESPN previous NBA season team standings metadata. |
| [pulsescore_radar_six_heures.py](collecte/pulsescore_radar_six_heures.py) | Revue six-hour PulseScore radar: strictly incremental, no paper bets. |
| [pulsescore_v2.py](collecte/pulsescore_v2.py) | PulseScore Pro prematch adapter for Revue V2. |
| [scoreboard_revue.py](collecte/scoreboard_revue.py) | Observed sport scores from official NHL and ESPN scoreboard APIs. |
| [shadow_sources.py](collecte/shadow_sources.py) | Independent read-only shadow comparison: PulseScore vs community sources. |
| [tableau_cotes.py](collecte/tableau_cotes.py) | Revue: time-stamped French bookmaker odds board, independent of model EV. |

## suivi

**Suivi prospectif, règlement et évaluation.** Prévisions figées avant match, règlement sur scores officiels, journal papier, Brier / log-loss / CLV, backtests chronologiques.

Documentation : [BACKTESTS_MULTISPORTS.md](suivi/BACKTESTS_MULTISPORTS.md) · [ENGINE-V2-README.md](suivi/ENGINE-V2-README.md)

| Script | Objet |
|---|---|
| [backtest_multisports.py](suivi/backtest_multisports.py) | Chronological score-only backtests of Revue multisport probability models. |
| [banc_nhl_cloture.py](suivi/banc_nhl_cloture.py) | Banc d'essai NHL contre la cote de clôture — implémentation originale Revue. |
| [clairvoyance_nhl_moneypuck_shadow.py](suivi/clairvoyance_nhl_moneypuck_shadow.py) | Clairvoyance NHL predictor on independently acquired, timestamped inputs. |
| [couverture_bonus.py](suivi/couverture_bonus.py) | Conversion des bonus d'opérateurs français (freebets, paris remboursés) — implémentation originale Revue. |
| [evaluation_prospective_papier.py](suivi/evaluation_prospective_papier.py) | Strict prospective paper-ledger probability evaluation (not fitted models). |
| [historique_cotes_clv.py](suivi/historique_cotes_clv.py) | Prospective SAME-BOOK closing price tracking for Revue paper entries. |
| [individual_prospective_revue.py](suivi/individual_prospective_revue.py) | Immutable independent pre-match individual sports research tracker. |
| [nhl_calibration_prospective.py](suivi/nhl_calibration_prospective.py) | Prospective NHL probability calibration research; never promotes betting picks. |
| [nhl_frontend_observed.js](suivi/nhl_frontend_observed.js) | Source-aligned NHL frontend research bridge, with strictly observed features. |
| [nhl_frontend_tracker.py](suivi/nhl_frontend_tracker.py) | Prospective NHL MC / Ensemble tracker; independent model comparison, no betting. |
| [nhl_moneypuck_prudent.py](suivi/nhl_moneypuck_prudent.py) | Experimental small-sample NHL forecast, compared prospectively with Clairvoyance. |
| [nhl_point_in_time_audit.py](suivi/nhl_point_in_time_audit.py) | Point-in-time cross-source guard for MoneyPuck NHL shadow predictions. |
| [nhl_settlement_officiel.py](suivi/nhl_settlement_officiel.py) | Settle previously locked NHL SHADOW forecasts using official daily NHL scores. |
| [nhl_shadow_tracker.py](suivi/nhl_shadow_tracker.py) | Immutable prematch lock + settlement ledger for MoneyPuck-backed NHL SHADOW. |
| [phase10_modeles_multisports.py](suivi/phase10_modeles_multisports.py) | Phase 10: forward-only independent multisport research predictions. |
| [phase10_validation_prospective.py](suivi/phase10_validation_prospective.py) | Phase 10: true forward-only model-specific locks and ESPN final evaluations. |
| [phase12_audit.py](suivi/phase12_audit.py) | Phase 12 settlement audit: verify scores, never reinterpret paper returns. |
| [phase12_official_finals.py](suivi/phase12_official_finals.py) | Phase 12: recover ONLY ESPN finals for prospectively locked model fixtures. |
| [phase13_comparaison_modeles.py](suivi/phase13_comparaison_modeles.py) | Phase 13: immutable out-of-sample multisport model comparison. |
| [phase2_historique_autonome.py](suivi/phase2_historique_autonome.py) | Phase 2: Revue-owned *prospective* multi-sport forecasting & Elo history. |
| [prospectif_multisports_revue.py](suivi/prospectif_multisports_revue.py) | Immutable multisport prospective predictions and strict official-result evaluation. |
| [regle_decision.py](suivi/regle_decision.py) | Règle de décision pré-enregistrée pour le journal de paris papier de Revue. |
| [reglement_multisport_officiel.py](suivi/reglement_multisport_officiel.py) | Independent, verified ESPN final-score settlement for existing PAPER bets. |
| [revue_engine_v2.py](suivi/revue_engine_v2.py) | Revue Engine V2 — an ORIGINAL, dry-run-only multisport odds and paper ledger. |
| [suivi_ensemble.py](suivi/suivi_ensemble.py) | Prospective paired model audit: real scores vs frozen 1X2 at pregame time. |
| [suivi_football_avance.py](suivi/suivi_football_avance.py) | Prospective audit of the independent advanced-football SHADOW model. |

## controles

**Contrôles qualité.** Validation des cotes, de la chronologie, du retrait de marge, de l'intégrité des sources et portes d'acceptation.

Documentation : [CONTROLE_CHRONOLOGIE.md](controles/CONTROLE_CHRONOLOGIE.md)

| Script | Objet |
|---|---|
| [calibration_devig.py](controles/calibration_devig.py) | Calibration des méthodes de retrait de marge sur des cotes historiques — implémentation originale Revue. |
| [chronologie_pre_match.py](controles/chronologie_pre_match.py) | Contrôle chronologique original pour Revue — pré-match seulement. |
| [consensus_quotations.py](controles/consensus_quotations.py) | Independent comparison of DEVIGGED bookmaker quote snapshots. |
| [controle_couverture_cotes.py](controles/controle_couverture_cotes.py) | Read-only cross-book mathematical cover audit from existing observed FR quotes. |
| [diagnostic_revue.py](controles/diagnostic_revue.py) | No-network freshness, health and source-coverage watchdog for Revue. |
| [etat_donnees_revue.py](controles/etat_donnees_revue.py) | Audit all observable Revue data layers, without provider calls or fabricated readiness. |
| [github_actions_monitor.py](controles/github_actions_monitor.py) | Observed GitHub Actions metadata, never original Clairvoyance SQL logs. |
| [inventaire_depot.py](controles/inventaire_depot.py) | Inventaires générés du dépôt Revue : jeux de données publiés et outils. |
| [phase11_data_quality.py](controles/phase11_data_quality.py) | Phase 11: source provenance, goalie evidence and bookmaker-rule quarantine. |
| [phase14_reception.py](controles/phase14_reception.py) | Phase 14: user-facing release truth gate for the three-screen Revue Arcade. |
| [phase5_donnees_multisports.py](controles/phase5_donnees_multisports.py) | Phase 5: validate independent NBA, NHL, MLB and football observations. |
| [phase7_cotes_et_bilan.py](controles/phase7_cotes_et_bilan.py) | Phase 7: strict PulseScore price provenance and independent settled paper audit. |
| [phase9_acceptation_production.py](controles/phase9_acceptation_production.py) | Phase9: independent offline static and data-provenance release gate. |
| [sensibilite_devig.py](controles/sensibilite_devig.py) | Robustesse du retrait de marge — implémentation originale Revue. |
| [validateur_cotes.py](controles/validateur_cotes.py) | Validation élémentaire de cotations avant calcul d'EV (implémentation Revue). |
| [verifier_integrite_moneypuck.py](controles/verifier_integrite_moneypuck.py) | Check consistency of published, attributed MoneyPuck NHL snapshots. |

## publication

**Publication du site.** Construction des écrans GitHub Pages (Match Center, Picks, dossiers, export).

| Script | Objet |
|---|---|
| [match_center_revue.py](publication/match_center_revue.py) | Build an ORIGINAL read-only multisport match center from Revue's own feeds. |
| [picks_center_revue.py](publication/picks_center_revue.py) | Revue's independently implemented picks screen, driven by observed saved data. |
| [publier_revue_control.py](publication/publier_revue_control.py) | Verified static snapshots for GitHub Pages. |
| [revue_match_dossiers.py](publication/revue_match_dossiers.py) | Independent, source-audited per-game dossiers for Revue's personal Match Center. |

## Limites

Ces outils contrôlent des formats, des chronologies et des calculs. Ils ne prouvent ni l'authenticité d'une source, ni la légalité ANJ d'un marché, ni la rentabilité d'un pari.
