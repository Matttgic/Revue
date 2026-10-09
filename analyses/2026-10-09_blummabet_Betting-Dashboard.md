# Audit — blummabet/Betting-Dashboard

- **Projet :** https://github.com/blummabet/Betting-Dashboard
- **Auteur :** blummabet
- **Commit source audité :** `4d9d08f76ce1b0f39b2e2890c9781f5862b3553c` (branche main, 09/10/2026)
- **Licence :** AUCUNE licence explicite visible dans les métadonnées et l'arborescence inspectées. Code, datasets, historiques, interface : **pas de copie ni de redistribution**.
- **Stack :** Python, JavaScript, HTML, GitHub Actions, multiples API sport/cotes.
- **Statut Revue :** recherche documentée ; pas d'intégration de code tiers ; pas de stratégie prouvée rentable.
- **Étendue :** dépôt très volumineux (GitHub annonce plusieurs millions de Ko) : revue ciblée des sources, documents, signaux et rapports ; **pas d'audit exhaustif**, tests du moteur source non exécutés.

## Architecture trouvée

- [ARCHITECTURE.md](https://github.com/blummabet/Betting-Dashboard/blob/main/ARCHITECTURE.md) : un moteur central mutualisé entre jeux de données (WM, Liga et adaptations MLS), profils, registres.
- [steam_engine.py](https://github.com/blummabet/Betting-Dashboard/blob/main/steam_engine.py) : suivi des mouvements Pinnacle (« steam »), sélection de marchés.
- [sharp_signals/](https://github.com/blummabet/Betting-Dashboard/tree/main/sharp_signals) : famille de modules sur forme, xG, blessures, marchés, cotes, momentum, contexte, etc.
- [conviction_score.py](https://github.com/blummabet/Betting-Dashboard/blob/main/conviction_score.py) : score composite, familles, règles de décision.
- [devig.py](https://github.com/blummabet/Betting-Dashboard/blob/main/devig.py) : extraction de probabilités hors marge, sensibilité des méthodes.
- [build_signal_ledger.py](https://github.com/blummabet/Betting-Dashboard/blob/main/build_signal_ledger.py) et [update_signal_weights.py](https://github.com/blummabet/Betting-Dashboard/blob/main/update_signal_weights.py) : suivi et ajustement des poids.
- [betfair_coherence.py](https://github.com/blummabet/Betting-Dashboard/blob/main/sharp_signals/betfair_coherence.py) : cohérence d'une échelle de totaux et diagnostic de mauvaise spécification.
- [backtest_model_health.py](https://github.com/blummabet/Betting-Dashboard/blob/main/backtest_model_health.py) : simulations/buckets de ROI, CLV, Brier, intervalles d'incertitude.

## Pistes acceptées pour recherches indépendantes

| ID | Thème | Fiche |
|---|---|---|
| REV-BLUMMA-01 | Steam Pinnacle + retard de bookmakers | [steam](../recherche/football/steam-sharp-softbooks.md) |
| REV-BLUMMA-02 | Dé-margement et sensibilité des longshots | [devig](../recherche/transversales/devig-methode-robuste.md) |
| REV-BLUMMA-03 | Consensus, anti-double comptage et gating | [signaux](../recherche/transversales/consensus-signaux-independants.md) |
| REV-BLUMMA-04 | xG, effet domicile/extérieur, déplacement MLS | [forme](../recherche/football/xg-venue-travel.md) |
| REV-BLUMMA-05 | Journal de signaux et apprentissage prudent | [apprentissage](../recherche/transversales/learning-loop.md) |
| REV-BLUMMA-06 | Cohérence des lignes de totaux entre marchés | [cohérence](../recherche/football/coherence-marche-totaux.md) |
| REV-BLUMMA-07 | Audit de backtest, ROI et incertitude | [validation](../recherche/transversales/audit-signal-backtests.md) |

## Évidence des rendements — prudence indispensable

**Rapport historique fourni par l'auteur** [backtest_report.md](https://github.com/blummabet/Betting-Dashboard/blob/main/backtest_report.md) et [backtest_results.json](https://github.com/blummabet/Betting-Dashboard/blob/main/backtest_results.json) :
- 656 picks inclus ; 619 réglés sans annulation (327 gagnés, 292 perdus) et 37 void.
- ROI reporté **−7,05 %** ; bootstrap à 95 % **[−14,49 % ; +0,66 %]** ; Brier binaire **0,2918**.
- Segment Elo 144 picks, ROI +1,34 % [−15,31 % ; +20,37 %] : preuve insuffisante d'avantage.
- Segment « Skellam » 512 picks, ROI −9,57 % [−17,45 % ; −1,44 %].
- ATTENTION : rapport établi à partir d'un historique publié, non audit d'exécution indépendante ni mesure nécessairement comparable au moteur actif en octobre.

**Rapport liga 2025** [liga_backtest_report.json](https://github.com/blummabet/Betting-Dashboard/blob/main/liga_backtest_report.json) :
- `form_trend` : 1 810 paris, ROI −8,2 %.
- `xg_strength` : 1 274 paris, ROI −7,7 %.
- `league_pressure` : 529 paris, ROI −13,9 %.
- Les segments se recouvrent potentiellement : **ne jamais additionner leurs nombres de paris** pour créer un « total ».
- Filtre « value ≥2 pp » : 1 307 cas, **ROI −9,4 %**.
- Aucun des constats ne prouve une rentabilité d'ensemble.

Les documents mentionnent quelques segments gagnants, souvent échantillons faibles et explorés a posteriori. De nombreuses fiches « sharp » restent des **hypothèses**.

## Risques techniques majeurs

1. **De-vig confus selon module :** [README](https://github.com/blummabet/Betting-Dashboard/blob/main/README.md) donne un `(1/cote)*1.03` qualifié à tort de correction de marge ; ce n'est pas un retrait de vig. [PICK_ENGINE_REVIEW_2026-07-25](https://github.com/blummabet/Betting-Dashboard/blob/main/PICK_ENGINE_REVIEW_2026-07-25.md) relève également cet écart dans une partie du pipeline. `devig.py` (septembre) traite plus sérieusement la question ; pas de preuve que tous les parcours l'utilisent.
2. **Signaux actifs sans marché réel :** l'audit source a signalé l'absence de cotes BTTS, de totaux alternatifs et de certains marchés dans des fetchers. Il faut vérifier le code du commit actuel avant de déclarer ces bugs encore présents.
3. **Signal ≠ rentabilité :** mouvement de cote, consensus de marché, volume de pari et taux de réussite doivent être validés sur le **prix accessible lors du signal**.
4. **Déficits de couverture :** API muette, cotes absentes, lineup manquante peuvent laisser des familles de signaux à zéro et empêcher les seuils d'être atteints.
5. **Apprentissage adaptatif :** poids modifiés sur les mêmes sélections, changements de modèles et sélection répétée des meilleurs segments => validation prospective, gel des règles, protection contre overfit nécessaires.
6. **Dé-margement :** méthodes Shin/power/additive/multiplicative divergentes pour certains 1N2 longshots, et les formules ne doivent pas masquer une fausse EV.
7. **Conformité France :** Polymarket, échange Betfair, marchés et API évoqués dans le dépôt ne doivent **pas** être supposés légalement accessibles aux parieurs français ; usage documentaire seulement tant que cadre ANJ vérifié.
8. **Données et sécurité :** repository contenant de nombreux JSON/logs/états ; ne pas importer de données ni configurations ni identifiants. Vérifier licences des fournisseurs.

## Verdict

**Intérêt de recherche : très élevé** (nombreuses méthodes et retours d'échec utiles).
**Preuve de rentabilité : absente sur les rapports principaux disponibles.**
**Score officiel /100 : NC** — examen ciblé, pas de tests ni validation source complète.
**Décision : 7 fiches de recherche, zéro fichier de code tiers copié.** Une implémentation originale et testée de contrôle de sensibilité à la marge peut être créée séparément dans `outils/`.

## Priorités futures

1. Simuler en paper sur **cotes réellement collectées chez opérateurs légaux France** les hypothèses « steam + soft lag ».
2. Vérifier CLV vs prix réellement obtenable et timings de cotation.
3. Tester dé-margement sur 1N2 longshots, sensibilité de la décision aux méthodes, comparer au modèle.
4. Backtester ablations et familles indépendantes, sans optimisation rétrospective.
5. Conserver simultanément les résultats perdants et les filtres de données manquantes.
