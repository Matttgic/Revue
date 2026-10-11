# REV-BLUMMA-05 — Apprentissage des poids de signaux après règlement

**Statut : À étudier | source https://github.com/blummabet/Betting-Dashboard**

Modules : [build_signal_ledger.py](https://github.com/blummabet/Betting-Dashboard/blob/main/build_signal_ledger.py), [update_signal_weights.py](https://github.com/blummabet/Betting-Dashboard/blob/main/update_signal_weights.py), [compute_pick_calibration.py](https://github.com/blummabet/Betting-Dashboard/blob/main/compute_pick_calibration.py).

## Architecture à retenir
Une observation est inscrite au moment du pari : version du modèle, signaux présents/absents, cotes, score, date. Après règlement officiel, résultat, profit et prix de clôture sont joints **sans modifier l'enregistrement d'origine**. Les poids des signaux peuvent être recalibrés sur des exemples passés.

## Écueils identifiés
- Un signal présent sur des paris gagnants ne prouve pas qu'il est prédictif : comparer au taux de référence **au sein d'un segment comparable**, pas à 50 % arbitraire.
- Le résultat d'un seul pari est très bruité. Un verdict de qualité de jeu (« chance » / « mérite ») basé sur xG post-match est lui-même un modèle imparfait, pas une vérité; ne pas confondre avec probabilité calibrée.
- L'ajustement fréquent, les dizaines de familles testées et le choix rétrospectif des seuils créent de l'overfitting.
- Les conclusions sur un jeu de données ne doivent jamais ajuster un autre sport/compétition sans validation.

## Protocole Revue
Journal d'événements immuable, résultats et courbe de CLV, versionnement des paramètres; priors et poids recalculés uniquement sur l'historique antérieur; évaluation préquentielle (« predict then learn »); comparatif modèle gelé vs modèle qui apprend; garde-fou d'effectif minimal et intervalle d'incertitude.

**Verdict :** outil pédagogique important pour le futur « cerveau » multi-stratégies; pas de preuve autonome de rentabilité.
