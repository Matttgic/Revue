# Audit — erik-droidd/nba-betting

- **Projet :** https://github.com/erik-droidd/nba-betting
- **Auteur :** erik-droidd
- **Commit audité :** `d1050d325ae87487fd72ced4deddd4116db8ac2f` (`main`, 11/10/2026, commit quotidien de snapshots)
- **Licence :** aucun fichier `LICENSE`/`COPYING` ni champ de licence dans `pyproject.toml`; **aucun code ni jeu de données copié**.
- **Stack :** Python 3.9+, pandas, scikit-learn, NumPy, SciPy, SQLAlchemy/SQLite, Typer, FastAPI.
- **Tests :** `python -m pytest -q`, 196 réussis dans un environnement isolé Python 3.12. Cela valide des tests logiciels, pas le backtest ni les performances.
- **Données consultées :** snapshots JSONL partiels d’odds et de blessures; aucune base SQLite de matchs n’est versionnée. Les historiques de résultats rapportés par l’auteur ne sont donc pas reproductibles depuis ce clone sans reconstruire la base via les fournisseurs.

## Résumé technique

Le projet produit des probabilités NBA avec un Elo ajusté (avantage du terrain, back-to-back, disponibilité) et un HistGradientBoosting calibré, puis combine les sorties. Il les réduit vers le marché en espace logit, calcule un edge et propose des mises fractionnaires de Kelly avec une optimisation de portefeuille. Les sources de données incluent NBA.com, ESPN/DraftKings et Polymarket. Le CLI sert aussi à synchroniser matchs, blessures et cotes, entraîner, évaluer et servir une API.

`ARCHITECTURE.md` est explicitement le document de référence. `NBA betting system.md` est un document de conception historique; il contient des hypothèses générales sur l’efficacité, la liquidité et le potentiel de gain qui ne constituent pas des résultats du système actuel.

## Pistes retenues pour une recherche indépendante

| ID | Thème | Fiche |
|---|---|---|
| REV-ERIKNBA-01 | Probabilités moneyline, shrinkage et clôture | [Fiche](REV-ERIKNBA-01_market-shrinkage-et-cloture.md) |
| REV-ERIKNBA-02 | Disponibilité des joueurs sans fuite temporelle | [Fiche](REV-ERIKNBA-02_disponibilite-point-in-time.md) |
| REV-ERIKNBA-03 | Capture de cotes et contrôle temporel des snapshots | [Fiche](REV-ERIKNBA-03_integrite-snapshots-cotes.md) |
| REV-ERIKNBA-04 | Kelly conjoint et exposition d’une soirée | [Fiche](REV-ERIKNBA-04_kelly-portefeuille.md) |

## Résultats rapportés et limites

Les nombres ci-dessous sont ceux documentés par l’auteur dans `ARCHITECTURE.md`; ils n’ont pas été reproduits, faute de base de matchs et de prix complète dans le dépôt.

- Dernier entraînement documenté : walk-forward à 3 949 matchs, exactitude 66,9 %, Brier 0,2117 et log-loss 0,6123; Elo OOF Brier 0,2077 (ECE 0,009), GBM OOF Brier 0,2112. Ces scores prédisent le résultat, ils ne démontrent pas un ROI.
- Après réparation des snapshots, l’évaluation contre les prix de clôture ne porte que sur **124 moneylines** : Brier du modèle 0,2046 contre 0,2081 pour le marché, test apparié `t = −0,36`, interprété par l’auteur comme une égalité statistique. Le lambda de shrinkage meilleur dans cette petite grille vaut 0,50 contre 0,60 en production; log-loss 0,5870 contre 0,5871, écart négligeable.
- Pour 108 observations spread/totaux, la MAE spread documentée est 12,59 contre 12,80 pour le marché; en totaux, 15,49 contre 14,09, à l’avantage du marché (`t = +2,3`).
- Le backtest avec cotes réelles n’avait qu’environ 3 % de couverture. Le ROI +4,7 % sur 149 paris signalé dans une passe antérieure est qualifié de non informatif par l’auteur. Le ROI du backtest Elo-proxy ne mesure pas une performance contre un bookmaker; le dépôt précise lui-même qu’il surestime l’avantage.

## Risques méthodologiques et techniques

1. **Disponibilité post-match dans les lignes d’entraînement.** `features/availability.py` calcule correctement la forme typique et le statut de « régulier » à partir des matchs précédents (`shift(1)`). Mais `present` est tiré des minutes effectivement jouées dans le match cible et `absent = regular & ~present`. La cible d’entraînement et les folds OOF connaissent donc, pour ce facteur, les participants réels du match. La prédiction live remplace cette vérité post-match par une liste d’indisponibilités ESPN; aucune série historique complète d’états ESPN pré-match n’est fournie pour démontrer l’équivalence. Les gains d’OOF attribués à ces variables ne sont pas une preuve valide de performance prospective tant que cette différence n’est pas corrigée.
2. **Contrôle du marché encore petit.** Les évaluations du même jeu de matchs sont une bonne pratique, mais n=124 est sous le seuil de 300 que le dépôt s’est fixé pour trancher. L’évaluation note aussi que les prix Polymarket ne sont pas corrigés des frais d’exécution; la disponibilité, le spread de carnet et le glissement doivent être pris en compte.
3. **Historique des snapshots.** L’auteur documente des doublons, des prix post-match, des associations au mauvais match lors des matchs tardifs et des cotes Polymarket du mauvais événement. Il rapporte les avoir réparés dans sa base locale (1 612 lignes après réparation, sans doublon ni différence à la réimportation), mais cette base n’est pas versionnée et le résultat n’a pas pu être rejoué ici.
4. **Risque et mises.** Les plafonds et l’optimisation Kelly rendent le code testable, mais ne corrigent pas une probabilité biaisée. La matrice de corrélation, la fonction de sizing et les résultats de mises ne sont pas évalués sur un journal prospectif suffisamment grand.
5. **Reproductibilité et usage.** Les dépendances ont des versions minimales, sans lockfile. Conditions d’utilisation des API, données NBA/ESPN, marchés Polymarket et compatibilité ANJ en France à vérifier avant toute exploitation.

## Vérifications et verdict

| Critère | Note | Preuve |
|---|---:|---|
| Utilité des idées | NC | Plusieurs bonnes pratiques d’évaluation, de temporalité et de sizing; avantages non démontrés |
| Code / tests | NC | 196 tests passent; revue complète du code et sécurité non effectuées |
| Données | NC | Snapshots utiles mais partiels; base d’entraînement absente |
| Validité statistique | NC | Résultats d’auteur, faible couverture réelle; fuite train/live sur disponibilité |
| Reproductibilité | NC | Entraînement et résultats non reconstruits depuis le dépôt |

**Verdict : documenter et tester indépendamment; ne pas reprendre les résultats de disponibilité ni annoncer un avantage de pari.** La piste la plus utile est le protocole d’évaluation contre des cotes réellement observées, après correction de la disponibilité post-match et collecte pré-match vérifiable. Aucun code tiers n’a été repris.

## Prochaines étapes

1. Refaire les variables de disponibilité uniquement depuis des instantanés d’information disponibles avant le coup d’envoi, ou retirer ces variables de l’évaluation.
2. Constituer au moins une saison de prix horodatés légalement accessibles, mesurer couverture, CLV, coûts d’exécution et scores appariés sur plus de 300 matchs.
3. Comparer Elo seul, modèle enrichi et marché sur exactement les mêmes folds temporels; geler la sélection de lambda avant l’échantillon de test.
