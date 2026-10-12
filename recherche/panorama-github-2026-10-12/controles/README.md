# Contrôles reproductibles — recherche du 12 octobre 2026

Scripts écrits pour Revue (aucun code tiers recopié). Ils lisent des fichiers téléchargés **hors du dépôt** ; aucune donnée tierce n'est versionnée ici. Résultats : [../controles-numeriques.json](../controles-numeriques.json).

| Script | Contrôle | Données attendues |
|---|---|---|
| `implied_run.R` | Exécute `implied_probabilities` du paquet R `implied` sur 11 cas (dont deux issues) | `R/implied_probabilities.R` extrait au commit `1d1c5cd5` |
| `implied_check.py` | Portage Python de la boucle Shin « js » et racine exacte, pour mesurer l'écart | aucune |
| `devig_lib.py` | Méthodes de retrait de marge vectorisées (numpy) utilisées par les deux scripts suivants | — |
| `xgabora_audit.py` | Forme recalculée, AUC des colonnes de clusters, calibration des retraits de marge 1N2 et +/-2,5, meilleure cote | `data/Matches.csv`, `data/EloRatings.csv` au commit `25882a58` |
| `xgabora_elo.py` | Date de la photo ClubElo réellement utilisée pour `HomeElo` | idem |
| `sbr_audit.py` | Cohérence des moneylines, log-loss ouverture/clôture, calibration | `data/*_archive_10Y.json` au commit `1a820e50` |

Commandes (numpy et pandas requis pour les scripts vectorisés) :

```bash
python3 -I xgabora_audit.py /chemin/Matches.csv . /chemin/EloRatings.csv
python3 -I xgabora_elo.py /chemin/Matches.csv /chemin/EloRatings.csv
python3 -I sbr_audit.py /chemin/dossier_json .
Rscript implied_run.R /chemin/implied_probabilities.R
```

La version durable, sans dépendance, de la comparaison des retraits de marge est l'outil [`outils/controles/calibration_devig.py`](../../../outils/controles/calibration_devig.py).
