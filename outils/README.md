# Validateur de cotes observées (outil original Revue)

Ce module démontre un **contrat minimal** : une probabilité de modèle ne peut être comparée qu'à une cotation **observée**, externe, horodatée, associée à un bookmaker, un marché, une sélection et un identifiant de source.

- `outils/validateur_cotes.py` : structure `Cotation`, validation et calcul unitaire d'EV.
- `tests/test_validateur_cotes.py` : contrôles de provenance, de temps et des bornes.
- Aucune copie de code de VCheque ; outil original inspiré d'un défaut repéré pendant son audit.

## Commande

```bash
python -m unittest discover -s tests -p "test_validateur_cotes.py" -v
```

## Limitations

La validation des champs **ne prouve pas** que les informations ont été authentifiées, que la cote était obtenable, ni qu'un marché est autorisé par l'ANJ. Connecteurs et vérifications de provenance/réglementation restent nécessaires.
