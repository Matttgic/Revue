# Première expérience — sensibilité des probabilités de marché

Snapshot : 2026-10-12T01:37:09.445589+00:00. Lecture historique, pas de prix live.

**51 marchés retenus**, 160 comparaisons dirigées entre bookmakers et issues ; **13 changements de signe** de l’écart théorique selon la méthode.

Les comparaisons sont dépendantes et ne sont pas un nombre de paris indépendants.

Empreinte SHA256 de l’entrée : `9321d83af18e681d68b5bf0f2f0e9ef89456da12c54037ff628565278efa2d37`.

## Dix marchés les plus sensibles

| Rencontre | Bookmaker | Marché / ligne | Écart maximal entre méthodes (points de %) |
|---|---|---|---:|
| Atalanta – Venezia | pmu_fr | totals / 5.5 | 9.332 |
| Torino – Udinese | pmu_fr | totals / 4.5 | 8.674 |
| Levante – Sevilla | pmu_fr | totals / 4.5 | 8.674 |
| Torino – Udinese | betclic_fr | totals / 4.5 | 7.204 |
| Torino – Udinese | winamax_fr | totals / 4.5 | 7.131 |
| Coventry – Newcastle | pmu_fr | totals / 4.5 | 7.001 |
| Atalanta – Venezia | pmu_fr | totals / 1.5 | 6.966 |
| Torino – Udinese | winamax_fr | totals / 0.5 | 6.686 |
| Coventry – Newcastle | betclic_fr | totals / 4.5 | 5.884 |
| Coventry – Newcastle | pmu_fr | totals / 1.5 | 5.884 |

## Exclusions

- outside_football_90min_scope : 69
- invalid_or_unsupported_market : 5
- duplicate_market_rows : 0

## Interprétation

Un changement de signe signifie que la même cote paraît supérieure ou inférieure à une référence selon la formule choisie. Cela ne prouve pas quelle formule est correcte. Les autres bookmakers peuvent partager des informations ; leurs probabilités ne sont pas une vérité indépendante.

La comparaison porte sur des marchés complets du même match, de la même période et de la même ligne ; une référence ne se compare pas à elle-même. Les lignes entières et les quarts sont exclus. Les règles NHL non vérifiées restent exclues. Additif et Shin sont équivalents pour deux issues : quatre noms ne représentent alors pas quatre avis indépendants.

Les observations sont rapprochées à 60 secondes au plus. Un horodatage de collecte ne prouve pas la fraîcheur interne de chaque bookmaker. Aucun résultat de match, aucune commission ni simulation de remplissage ne sont évalués ici ; aucun ROI calculé.

Sensibilité mathématique seulement : ni probabilités calibrées, ni rentabilité vérifiée.
