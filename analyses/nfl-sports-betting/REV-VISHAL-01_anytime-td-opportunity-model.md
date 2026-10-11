# REV-VISHAL-01 — Modèle anytime-TD par occasions et parts hiérarchiques

- **Sport / marché :** NFL, props joueur anytime-touchdown
- **Source :** [vishalkiritnaik-a11y/nfl-sports-betting](https://github.com/vishalkiritnaik-a11y/nfl-sports-betting), commit [`382d9d4fc9b8c8432889cde424e7103520ad8c0d`](https://github.com/vishalkiritnaik-a11y/nfl-sports-betting/commit/382d9d4fc9b8c8432889cde424e7103520ad8c0d)
- **Statut :** À étudier
- **Licence source :** absente; aucune reprise de code ou de données

## Idée

Décomposer la probabilité d'un touchdown joueur en trois facteurs séparés :

1. **Volume d'occasions de l'équipe :** régression des occasions attendues de chaque zone sur les points et la marge prévus pour l'équipe. Zones au sol : courses dans les 5, 6–10, 11–20 et hors des 20 verges. Zones en réception : cibles de end zone, autres cibles red zone et reste du terrain.
2. **Part du joueur :** répartir les occasions projetées avec les parts d'usage récentes du joueur par zone, en donnant plus de poids aux matchs récents (décroissance `0,85`) et en limitant l'historique à 12 matchs / 450 jours. Des priors imbriqués régularisent les parts rares : part globale de courses/cibles, puis red zone, 10 verges et end zone. Les parts des joueurs indisponibles sont redistribuées aux joueurs disponibles.
3. **Taux de conversion :** multiplier les occasions prévues par les taux historiques de TD par occasion, corrigés par une mesure de finition du joueur et par un facteur de défense adverse. Ces multiplicateurs sont rétrécis vers `1` par ajout d'un prior d'environ 4 TD attendus pour le joueur et 8 pour l'adversaire.

Les intensités course et réception sont additionnées (`λ = λ_course + λ_réception`). Une probabilité brute Poisson `1 − exp(−λ)` est ensuite recalibrée par une régression logistique sur `log(λ)`, `log(λ)²`, poste, part course, profondeur d'historique et participation récente aux snaps. Le backtest rapporte cette calibration sur des saisons ultérieures, avec modèles d'occasions et taux ajustés seulement sur les saisons précédentes.

## Résultat rapporté et limite principale

Le dépôt publie un log-loss walk-forward de `0,395` contre `0,446` pour une probabilité constante au taux de base, un Brier de `0,122` et une AUC de `0,74` sur environ 29 000 lignes joueur-match (2022–2026). La population d'évaluation se limite aux QB/RB/WR/TE ayant pris au moins un snap offensif.

Cette comparaison ne mesure pas l'avantage contre un bookmaker. Le dépôt n'a pas de cotes anytime-TD historiques; l'API facultative demande un plan payant pour collecter les props. Au commit audité, le ledger contient des prévisions pré-match, mais aucun résultat prospectif encore réglé. Le score probabiliste reste donc une preuve d'auteur sur historique, non une preuve de value ou de rentabilité.

## Test proposé dans Revue

1. Construire par kickoff les occasions, parts de rôle et taux de TD uniquement avec les observations disponibles avant ce kickoff; conserver la version exacte de roster et les statuts blessures.
2. Comparer des baselines emboîtées : taux de base par poste, modèle de volume sans finition, modèle volume × finition, puis ajout du multiplicateur défensif et de la calibration.
3. Utiliser des plis walk-forward par semaine ou saison; sélectionner les paramètres de shrinkage et la calibration sans revoir les événements de test.
4. Définir la population des props et les règles bookmaker pour joueurs absents, actifs mais sans snap, forfaits et voids; rapporter aussi ces cas séparément.
5. Après validation des probabilités, comparer aux cotes anytime-TD observées au même instant de décision, après dé-vig; évaluer CLV puis ROI prospectif avec mise gelée et incertitude.

**Décision :** piste de modélisation intéressante pour les touchdown props, notamment par la séparation « occasions d'équipe → rôle joueur → finition ». Garder `À étudier` tant qu'il n'existe ni réplication ni prix historiques/prospectifs permettant de mesurer le marché.
