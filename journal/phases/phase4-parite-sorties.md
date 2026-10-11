# Phase 4 — Fidélité des sorties observées (2026-10-10)

## Réalisé
- Nouveau moteur `outils/clairvoyance/phase4_parite_reelle.py`, testable hors ligne, qui joint
  les comparaisons publiques Clairvoyance/Revue et les scénarios NHL Revue.
- Chaque rapprochement impose la même rencontre, le même marché et deux
  instantanés observés **au moins 20 min avant le match**.
- Pour le marché vainqueur uniquement, un scénario en fraction xG (0..1)
  est opposé à un scénario en points de pourcentage (0..100) afin de voir
  la sensibilité des résultats aux unités, **sans prétendre trouver
  les paramètres déployés par Clairvoyance**.
- Les comparaisons impossible ou tardives restent visibles mais n'ont pas
  de différence de probabilité revendiquée.
- Page `docs/phase4-parite.html` accessible depuis le Lab, avec bilan
  des preuves et cas exclus. Tests de régression et GitHub Actions.
- Aucun nouvel appel API payant ; aucune modification de prévisions figées
  ni du journal des paris fictifs.

## Ce que cela ne prouve PAS
L'instant d'observation de `docs/data.json` n'est pas le verrouillage
historique de chaque prévision originale ; le modèle exposant les
`bestBets` n'est pas prouvé être `app/services/predictor.py` ;
la base SQL/Elo source et les droits sur les données ne sont pas disponibles.
Par conséquent, **parité des probabilités originales non démontrée**,
pas de rentabilité prouvée, aucun pourcentage global de clone majoré.

Sources du rapport : `docs/clairvoyance-real-output-gap.json` et
`docs/nhl-backend-source-style-latest.json`. Pour une analyse reproductible,
exécuter `python -m outils.clairvoyance.phase4_parite_reelle`.
