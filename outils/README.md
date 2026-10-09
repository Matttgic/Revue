# Outils originaux de contrôle Revue

Ces modules sont **écrits pour Revue**, sans reproduction du code des dépôts tiers. Ils servent à vérifier la qualité d'un signal; ils ne démontrent pas la rentabilité d'un pari.

| Outil | Objet | Tests |
|---|---|---|
| [validateur_cotes.py](validateur_cotes.py) | Rejeter les cotes non observées et vérifier la structure du signal EV | [Tests](../tests/test_validateur_cotes.py) |
| [sensibilite_devig.py](sensibilite_devig.py) | Comparer multiplicatif, additif et puissance pour estimer la sensibilité au retrait de marge | [Tests](../tests/test_sensibilite_devig.py) |
| [chronologie_pre_match.py](chronologie_pre_match.py) | Exclure les décisions enregistrées après le coup d'envoi ou sans preuves d'horodatage | [Tests](../tests/test_chronologie_pre_match.py) |

## Documentation spécifique

- [Chronologie et politique stricte pour les backtests](CONTROLE_CHRONOLOGIE.md)

## Tests unitaires

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## Limitations

Les contrôles valident des **formats et contraintes temporelles**, pas l'authenticité d'une source ni la légalité ANJ d'un marché. Il reste obligatoire de vérifier les licences, cotes réellement obtenables, l'origine et l'heure de chaque donnée, ainsi que la calibration du modèle.

Les tests de chronologie ont été passés sur copie locale identique des fichiers du 2026-10-09 (10/10); les suites des autres modules n'ont pas été rejouées au cours de cet audit.
