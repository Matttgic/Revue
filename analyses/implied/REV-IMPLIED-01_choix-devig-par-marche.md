# REV-IMPLIED-01 — Choisir le retrait de marge par sport et par marché

- Statut : **Testé** (calibration historique ; ce n'est pas une stratégie de pari).
- Sport : multi-sports. Marché/usage : toute probabilité « juste » tirée d'une cote (EV, CLV, benchmark marché).
- Sources : [implied](AUDIT.md) pour les formules ; [Club-Football-Match-Data](../Club-Football-Match-Data/AUDIT.md) et [sportsbookreview-scraper](../sportsbookreview-scraper/AUDIT.md) pour les données.
- Outil Revue : [`outils/controles/calibration_devig.py`](../../outils/controles/calibration_devig.py) (réécriture indépendante, testée par `tests/test_calibration_devig.py`).

## Idée

Il n'existe pas de « meilleure » méthode de retrait de marge universelle. La bonne méthode est celle dont les probabilités prédisent le mieux les résultats **pour la source de cotes, le sport et le marché utilisés**. On la choisit sur un historique, puis on la fige.

## Résultats mesurés (12 octobre 2026)

Différence de log-loss moyenne par match par rapport à la normalisation multiplicative (négatif = meilleur), erreur-type appariée entre parenthèses.

| Marché | n | Additive | Puissance | Shin | Odds ratio |
|---|---:|---:|---:|---:|---:|
| Football 1N2, Bet365, 38 divisions 2000-2026 | 235 543 | −0,00066 (0,00007) | **−0,00071** (0,00007) | −0,00060 (0,00005) | −0,00058 (0,00004) |
| Football +/-2,5 buts, Bet365 | 156 615 | −0,00011 (0,00003) | −0,00013 (0,00004) | −0,00011 (0,00003) | −0,00012 (0,00003) |
| NHL moneyline, clôture, 2011-2021 | 13 666 | −0,00007 (0,00006) | −0,00009 (0,00009) | −0,00007 (0,00006) | −0,00007 (0,00006) |
| NBA moneyline, clôture, 2011-2021 | 13 884 | +0,00044 (0,00021) | **+0,00105** (0,00036) | +0,00044 (0,00021) | +0,00052 (0,00024) |

Lecture :

- En football 1N2, toute méthode qui corrige le biais favori-outsider bat la multiplicative ; l'écart est net (≈ 10 erreurs-types) mais petit en moyenne. Il est dix fois plus grand sur les gros favoris (cote < 1,35 : −0,007).
- Sur deux issues équilibrées (+/-2,5, NHL), les méthodes sont presque équivalentes.
- En NBA, la multiplicative est la meilleure : appliquer la puissance par habitude dégraderait la calibration.
- Sur deux issues, Shin et additive donnent exactement le même résultat (identité vérifiée par test).

## Règle proposée pour Revue

1. Pour chaque couple (source de cotes, sport, marché), lancer `calibration_devig` sur un historique antérieur à la période suivie.
2. Retenir la méthode la plus basse seulement si son avantage dépasse 2 erreurs-types ; sinon garder la multiplicative (la plus simple).
3. Refaire la mesure une fois par saison, sans changer de méthode en cours de saison.

## Limites

- Instant de collecte des cotes non documenté pour les deux sources (ouverture, veille ou clôture).
- Un meilleur retrait de marge ne crée **aucun** avantage contre le bookmaker dont on retire la marge ; il améliore seulement le benchmark et la mesure de l'EV et du CLV.
- La partie MLB de l'archive sportsbookreview est corrompue : résultat MLB non retenu.
