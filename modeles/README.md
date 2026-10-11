# Modèles

| Dossier | Contenu | Règle |
|---|---|---|
| [`reproduction/`](reproduction/README.md) | Réécritures indépendantes de fonctions de dépôts tiers (aujourd'hui : Clairvoyance) | Chaque fonction est comparée à l'original sur des entrées identiques ; aucun choix propre à Revue |
| [`simulations/`](simulations) | Modèles originaux Revue (Elo, Poisson, Monte-Carlo, Bayes…) | Recherche non calibrée, suivie de façon prospective |

Liste complète, statuts et fichiers de suivi : [catalogue/MODELES.md](../catalogue/MODELES.md).

Pour chaque modèle, documenter : les variables d'entrée et leur source, la fenêtre de données utilisée (jamais postérieure au match prédit), les règles d'imputation, le risque de fuite temporelle, les métriques de calibration (Brier, log-loss) et un exemple d'inférence. Un modèle doit rester indépendant des fournisseurs de cotes et des noms de ligues.
