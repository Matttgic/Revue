# Audit — kyleskom/NBA-Machine-Learning-Sports-Betting

- **Source :** https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting
- **Commit examiné :** `8e36b0b72ecc5082aa8976dff742cdf910b3aa36` (`main`), 2026-01-08
- **Date de consultation :** 2026-10-11
- **Licence :** aucun fichier de licence trouvé. Aucun code ni jeu de données n’a été copié dans Revue; obtenir une autorisation avant toute réutilisation.
- **Stack :** Python 3.11 selon le README, pandas, TensorFlow 2.14, XGBoost, scikit-learn, SQLite, Flask et `sbrscrape`.
- **Données versionnées :** trois bases SQLite; `dataset_2012-26` contient 16 969 matchs du 2012-11-04 au 2026-01-07 et 116 colonnes de statistiques, de cotes et de cibles.
- **Avis :** pipeline de recherche lisible et complet sur le plan logiciel, mais impropre à prouver une performance de pari dans son état actuel. Une fuite post-match majeure contamine les caractéristiques; aucun ROI/CLV validé n’est fourni.

## Fonctionnement

Le projet récupère les statistiques cumulées NBA par date, des cotes et résultats via SBR, puis assemble un jeu de données par match. Des scripts entraînent XGBoost, des réseaux de neurones et une régression logistique pour le moneyline et le total. Les modèles XGBoost offrent une calibration sigmoid ou isotonic. Les cotes moneyline, le spread et le total sont conservés comme variables d’entrée; la commande calcule ensuite l’EV et peut afficher un Kelly plein pour le moneyline.

Le point fort est l’effort de reproductibilité logicielle : bases SQLite versionnées, pipelines explicites, tests unitaires, validation chronologique et vérification de l’alignement des colonnes. Le README ne publie toutefois aucun résultat de pari reproduit. Les noms de fichiers de modèles contiennent des pourcentages d’exactitude, sans rapport d’évaluation associé.

## Défaut bloquant : statistiques du jour cible

`config.toml` forme une requête NBA avec un début de saison et une `DateTo` correspondant à la date de chaque table. `Get_Data` enregistre ces statistiques dans une table nommée pour cette date, et `Create_Games` joint la table au même jour de matchs. Les statistiques saisonnières comprennent donc les résultats déjà joués ce jour-là, alors que la prédiction est censée être pré-match.

Le jeu livré donne un exemple vérifiable : pour Hawks–Pelicans du 7 janvier 2026, les caractéristiques Atlanta sont `GP=39`, `W=18`; dans l’instantané du 6 janvier, elles sont `GP=38`, `W=17`. Le match du 7 janvier est lui-même étiqueté victoire d’Atlanta. Le résultat cible est ainsi déjà reflété dans une entrée du modèle. Le fait que les lignes soient triées par date puis divisées avec `TimeSeriesSplit` ne corrige pas cette contamination. Les plis sont en outre coupés par ligne et non par journée, et peuvent séparer des matchs d’une même date.

## Limites des preuves et d’exécution

- Les métriques du README sont des scores de classification prévus par le code; aucun rapport de calibration, comparaison au marché, ROI, CLV ou backtest de bankroll n’est publié.
- L’EV et le Kelly affichés concernent seulement les moneylines. Le modèle de totaux choisit une classe over/push/under, mais la sortie ne compare pas cette probabilité au prix over/under.
- Le découpage chronologique est une bonne base, mais XGBoost utilise l’échantillon de calibration aussi pour l’arrêt anticipé, puis pour ajuster le calibrateur. La recherche de paramètres réutilise également les mêmes plis de validation.
- L’application pointe en dur vers la saison 2025-26 et le calendrier `nba-2025-UTC.csv`; cette interface ne suit donc pas automatiquement les saisons ultérieures.
- Les tests existants valident surtout le traitement de données et quelques formules, pas les scripts d’entraînement, la calibration ni les performances sportives. `python -m unittest discover -s Tests -v` a réussi : **32 tests passés** dans l’environnement Python existant avec pandas. Cela ne reproduit aucun modèle ou backtest. Un avertissement `ResourceWarning` signale un fichier TOML de test non fermé.
- Les versions épinglées ciblent Python 3.11 (notamment TensorFlow 2.14); l’environnement cloud disponible est Python 3.12. L’entraînement et le démarrage Flask n’ont pas été exécutés.
- Les prix historiques ne comportent pas de capture temporelle pré-match documentée dans le schéma livré; la source exacte et les droits d’usage des statistiques et des cotes restent à établir.

## Décision et avis

**Documenter seulement; ne pas réutiliser les sorties de modèle ni les résultats implicites des noms de fichiers.** Le traitement direct des cotes comme variables et le couple statistiques d’équipe + jours de repos recoupent déjà la recherche NBA, en particulier [REV-ERIKNBA-01](../nba-betting/REV-ERIKNBA-01_market-shrinkage-et-cloture.md) et [REV-ERIKNBA-03](../nba-betting/REV-ERIKNBA-03_integrite-snapshots-cotes.md). Dans ce dossier, le point distinctif utile est le contre-exemple de fuite point-in-time; il ne justifie pas une nouvelle fiche de méthode.

Pour une réévaluation, reconstruire chaque caractéristique à partir d’un instantané effectivement disponible avant le coup d’envoi, séparer les matchs d’une même date dans les plis, comparer aux prix de marché sur les mêmes rencontres, puis mesurer calibration, CLV et rendement net hors échantillon avec intervalles d’incertitude.

## Références examinées

[README](https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting/blob/8e36b0b72ecc5082aa8976dff742cdf910b3aa36/README.md) · [configuration des données](https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting/blob/8e36b0b72ecc5082aa8976dff742cdf910b3aa36/config.toml) · [collecte des statistiques](https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting/blob/8e36b0b72ecc5082aa8976dff742cdf910b3aa36/src/Process-Data/Get_Data.py) · [assemblage des matchs](https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting/blob/8e36b0b72ecc5082aa8976dff742cdf910b3aa36/src/Process-Data/Create_Games.py) · [entraînement XGBoost](https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting/blob/8e36b0b72ecc5082aa8976dff742cdf910b3aa36/src/Train-Models/XGBoost_Model_ML.py) · [inférence et EV](https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting/blob/8e36b0b72ecc5082aa8976dff742cdf910b3aa36/src/Predict/XGBoost_Runner.py) · [calcul EV](https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting/blob/8e36b0b72ecc5082aa8976dff742cdf910b3aa36/src/Utils/Expected_Value.py) · [Kelly](https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting/blob/8e36b0b72ecc5082aa8976dff742cdf910b3aa36/src/Utils/Kelly_Criterion.py).
