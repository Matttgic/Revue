# Dossier source — erik-droidd/nba-betting

Ce dossier regroupe uniquement l’audit et les quatre fiches issues de [erik-droidd/nba-betting](https://github.com/erik-droidd/nba-betting). L’audit porte sur le commit `d1050d325ae87487fd72ced4deddd4116db8ac2f` (11/10/2026). Le dépôt apporte de bonnes idées de validation contre le marché et de collecte temporelle, mais aucune preuve solide de rentabilité. Un problème de disponibilité des joueurs dans les données d’entraînement doit être résolu avant de réutiliser les performances publiées. Aucun code source tiers n’a été copié.

Voir [l’audit](AUDIT.md) et les fiches :

- [01 — Évaluer le modèle contre la clôture et réduire vers le marché](REV-ERIKNBA-01_market-shrinkage-et-cloture.md)
- [02 — Disponibilité des joueurs sans information post-match](REV-ERIKNBA-02_disponibilite-point-in-time.md)
- [03 — Snapshots et intégrité temporelle des cotes](REV-ERIKNBA-03_integrite-snapshots-cotes.md)
- [04 — Allocation Kelly conjointe au niveau de la soirée](REV-ERIKNBA-04_kelly-portefeuille.md)
