# REV-CFB-01 — Lier modèle et contrat ordonné des variables

- Statut : **À étudier**.
- Sport : Multi-sports. Marché/usage : Fiabilité des modèles.
- Source et version : [audit du dépôt](AUDIT.md).
- Preuve : lecture ciblée du code/documentation ; protocole ci-dessous non exécuté.

## Idée

Conserver avec l’artefact les noms et l’ordre exacts des variables, encodages d’ère, transformations et période d’entraînement.

## Protocole proposé

Sauvegarder les empreintes conjointes modèle/fiche. Refuser variables manquantes, ordre incorrect ou transformateur incompatible. Vérifier les changements de schéma avant de comparer les performances.

## Limites

Un contrat valide prévient certains écarts d’inférence mais ne prouve ni causalité de l’entraînement ni rentabilité. La source utilise un garde de cache par date du booster ; couplage par empreinte proposé ici.

Aucun code tiers intégré aux modèles existants.
