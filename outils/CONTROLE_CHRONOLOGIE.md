# Contrôle chronologique pré-match — module original Revue

Une statistique historique ne prouve pas une performance **avant match** si l'instant de la décision, celui du début de la rencontre, celui de la cote et celui des features ne sont pas comparables et authentifiés.

- [`chronologie_pre_match.py`](chronologie_pre_match.py) : modèle de décision et classification stricte.
- [`test_chronologie_pre_match.py`](../tests/test_chronologie_pre_match.py) : jeux de tests unitaires.
- [Analyse de la source ayant inspiré ce contrôle](../analyses/2026-10-09_Purple-Wraith_clairvoyance-backend.md).

## Règle stricte
Le backtest pré-match conserve **uniquement** `pre_valide`. Les cas `tardif`, `indetermine`, `cote_non_verifiable` et `feature_non_verifiable` sont exclus du rendement mais gardés dans le bilan de couverture.

## Exécution
```bash
python -m unittest discover -s tests -p test_chronologie_pre_match.py -v
```

## Limites
Une date déclarée par le fournisseur peut être falsifiée, tardive ou trompeuse. Ce validateur contrôle les relations chronologiques mais ne certifie pas l'authenticité des horodatages, la disponibilité du prix ni la légalité ANJ. Il faut une provenance contrôlable et les journaux de capture originaux.
