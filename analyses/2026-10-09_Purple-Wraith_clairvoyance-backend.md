# Audit — Purple-Wraith/clairvoyance-backend

- **Source :** https://github.com/Purple-Wraith/clairvoyance-backend
- **Auteur :** Purple-Wraith
- **Commit audité :** `baa687b11a2d59b8a25720d4d747b0671b9450ff` (main, 2026-10-09)
- **Examen :** 2026-10-09 ; analyse ciblée des scripts, des rapports publics et de l'arborescence, **non exhaustive**.
- **Licence source :** aucune licence explicite visible dans les métadonnées ou l'arborescence. **Zéro fichier tiers copié dans Revue** sans permission/licence.
- **Technologies :** Python FastAPI/SQLAlchemy, scripts de modélisation et de scraping, HTML/JS monolithique, GitHub Actions, snapshots JSON et historiques.
- **Activité :** dépôt modifié le 2026-10-09.
- **Périmètre :** surtout hockey NHL et européen (Liiga/SHL/NLA/Extraliga), NFL/CFB, NBA et football. D'autres modules (MLB, tennis, etc.) sont encore présents mais **certains ont été retirés du pipeline automatique courant** : ne pas confondre code historique et moteur actif.

## Modules importants

| Fichier source | Fonction |
|---|---|
| [backtest_hockey_models.py](https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/backtest_hockey_models.py) | Backtests NHL point-in-time, Poisson, forme, dispersion, combinaison modèle/marché |
| [backtest_goalie_starter.py](https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/backtest_goalie_starter.py) | Test walk-forward de la valeur de l'information « gardien titulaire » |
| [_nhl_goalies.py](https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/_nhl_goalies.py) | États projeté/confirmé, provenance et premier horodatage; ESPN et MoneyPuck optionnel |
| [backtest_alt_lines.py](https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/backtest_alt_lines.py) | Sensibilité des lignes de totaux et handicaps, NBA/NHL/hockey européen |
| [backtest_quanthockey_signal.py](https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/backtest_quanthockey_signal.py) | Reconstruction des données historiques depuis snapshots de commits pour tester un signal |
| [_nhl_skaters.py](https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/_nhl_skaters.py) | Régression vers une saison antérieure pour valoriser les absences NHL |
| [lock_timing.py](https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/lock_timing.py) | Audit des paris verrouillés avant / pendant / après un match et cas sans timestamp |
| [predictor.py](https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/app/services/predictor.py) | Service FastAPI plus simple, Elo MLB/NHL + xG/goalies NHL + edge |
| [settlement.py](https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/app/services/settlement.py) | Règlement des paris FastAPI; risque de double mise à jour Elo si plusieurs picks ML sur un événement |
| [auto_lock_settle.py](https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/auto_lock_settle.py) | Moteur automatique plus récent, règlement, calibration et profil de ligues |
| [adaptive_weights.json](https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/docs/adaptive_weights.json) | État de pondération Monte-Carlo / bayésien / Elo et calibrations partielles |

## Distinction obligatoire : modèles publiés ≠ performances vérifiées

[engine_performance.json](https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/docs/engine_performance.json) (généré le 2026-10-09 06:35 MT) publie pour son historique **3 816 paris**, **2 671 gagnés**, **1 141 perdus**, **+965,78 unités**. MAIS la source décrit expressément sa base comme **« all locks including picks locked after the game started »**.

La rubrique `basis_detail` indique **1 017 enregistrements réglés « pre-start »**, **181 enregistrements « known late » inclus** et **2 614 entrées dont l'heure n'est pas déterminable**. Ces catégories ne réconcilient pas exactement à elles seules l'effectif affiché (autres statuts/filtrages possibles). **Ne pas utiliser le total ou le taux de réussite agrégés comme rendement pré-match.**

[sport_performance.json](https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/docs/sport_performance.json) est plus restrictif, mais inclut également **170 known late**, **279 unknown** et **935 pre-start** parmi ses catégories. Le ratio NHL affiché (148 victoires, 34 défaites sur 182 tickets, +77,99 unités) n'est donc **pas une validation pré-match indépendante**.

[lock_timing.py](https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/lock_timing.py) documente explicitement le problème : l'auteur note une victoire ~93 % après départ contre ~66 % avant départ et construit une classification pour exclure les known-late des chiffres publics. **Incohérence à examiner** : les deux fichiers de performance consultés se décrivent encore comme incluant les known-late (ne pas affirmer sans preuve que leur publication est filtrée).

[adaptive_weights.json](https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/docs/adaptive_weights.json) signale une sélection de **1 298 entrées sur 1 488 réglées** pour calibration, 190 exclues ; des temps inconnus restent conservés. Ces chiffres sont des **déclarations d'état** et non une validation du modèle en conditions réelles.

## Intérêt retenu

- **Hockey point-in-time :** prévisions sur résultats antérieurs au match, Poisson xG et comparaison à clôture bookmaker ; les cotes de clôture ne représentent pas forcément le prix atteignable au moment du pari.
- **Gardiens NHL :** qualité de gardien en fonction de la saison précédente et du temps joué, comparaison primary vs vrai starter ; le vrai starter issu d'un box score final est un **oracle de recherche**, pas une information disponible avant le match. Pour déployer, exiger `confirmed` horodaté et antérieur.
- **Hockey européen :** réutilisation de distributions propres aux ligues, lignes alternatives et stratégie de validation du signal QuantHockey; le projet note **89 paris exploitables mais aucun signal QuantHockey utilisable** à l'audit référencé 2026-10-03.
- **Montée en qualité de données :** snapshots Git horodatés, absences à valeurs lissées et identités des joueurs résolues conservativement, journal de règlement.
- **Vigilance Elo :** `settlement.py` appelle `_update_elo` pour **chaque** pick `moneyline` réglé. Si plusieurs tickets ML sur le **même événement** sont réglés, le score Elo serait mis à jour plusieurs fois ; vérifier contrainte métier avant utilisation.
- **Retraits / limites :** `auto_lock_settle.py` explique qu'une famille de props NFL TD avait annoncé **79,5 %** de probabilité moyenne mais obtenu **49,1 %** de réussite sur 57 paris et **−21,7 unités**, conduisant à sa désactivation automatique. Preuve utile du besoin de calibration par marché.

## Fiches originales conservées

| ID | Fiche |
|---|---|
| REV-CLAIR-01 | [NHL Poisson et consensus du marché](../recherche/hockey/nhl-point-in-time-poisson-marche.md) |
| REV-CLAIR-02 | [Gardien titulaire, confirmation et GSAx](../recherche/hockey/nhl-gardien-titulaire.md) |
| REV-CLAIR-03 | [Lignes alternatives NHL/NBA/hockey EU](../recherche/hockey/lignes-alternatives-ecart.md) |
| REV-CLAIR-04 | [Hockey européen, QuantHockey et snapshots](../recherche/hockey/quanthockey-snapshots.md) |
| REV-CLAIR-05 | [Qualité des locks avant match](../recherche/transversales/audit-locks-pre-match.md) |
| REV-CLAIR-06 | [Pondération / calibration adaptative](../recherche/transversales/ensemble-adaptatif-modeles.md) |
| REV-CLAIR-07 | [Impact des absences et shrinkage](../recherche/hockey/nhl-valeur-absences.md) |
| REV-CLAIR-08 | [Un seul règlement de jeu pour Elo](../recherche/transversales/elo-actualisation-unique.md) |

## Licence, données, conformité France

- Pas de code, CSV, JSON, composants graphiques ni actifs du tiers repris.
- Vérifier les droits MoneyPuck, ESPN, Flashscore, QuantHockey et d'éventuelles API avant toute collecte automatisée ou redistribution.
- Les opérateurs US, cotes américaines et marchés Polymarket/Betfair ne sont pas présumés accessibles/légaux en France. Appliquer les vérifications ANJ par sport, compétition et marché.
- Les scripts source n'ont pas été exécutés ; aucune calibration répliquée, ni résultat futur garanti.

**Verdict : très fort intérêt de recherche sur NHL, données temporelles et qualité des backtests ; rentabilité NON VALIDÉE.**
