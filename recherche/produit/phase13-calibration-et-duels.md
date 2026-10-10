# Phase 13 — comparaison honnête et calibration prospective

**Objectif** : évaluer, sans créer de paris, les modèles NBA, MLB et
football sur leurs propres matchs prospectivement figés. NHL utilise
ses scores officiels et sa calibration antérieure indépendante.

## Règles de validité

- Les résultats doivent venir de la phase 12 et des registres pré-match
  immuables. Vérifier les probabilités, heures de génération, coup
  d'envoi, observations ESPN finales, équipes, version et marché.
- Seuls les modèles d'une **même ligue**, sur **exactement le même
  événement, les mêmes équipes, le même horaire et la même période**
  peuvent être comparés directement. Un duel de modèles NBA liés ne
  constitue pas trois observations indépendantes.
- Brier **multiclasse non normalisé**, Log Loss, référence uniforme
  (0,5/0,5 ou 1/3), fiabilité par issue et cinq bacs de probabilité.
- Delta candidat moins référence. Une valeur négative est meilleure
  uniquement sur l'échantillon observé. Intervalles de différence
  *bootstrap apparié* (graine fixée) seulement après **30 rencontres
  communes**, exploratoires, non significativité garantie.
- Calibration : les **100 premiers résultats officiels** d'un modèle
  suivant l'heure de règlement constituent le groupe d'entraînement.
  La température `softmax(log(p)/T)` est choisie parmi une grille
  annoncée en avance. Les **40 prochains matchs** de validation doivent
  commencer **strictement après** la dernière résolution de cet
  entraînement. Cela bloque les fuites chronologiques.
- Même après un holdout favorable : classement et déploiement restent
  sujets à une revue humaine et à davantage de données. **Aucun
  champion automatique, aucune EV+, aucun ROI ni rendement validé.**
- NHL : calcul officiel indépendant, Brier **binaire scalaire** natif
  séparé du Brier 2 classes (qui est 2 fois ce dernier).

## Exécution

`python -m unittest discover -s tests -p 'test_phase13_comparaison_modeles.py' -v`

`python -m outils.phase13_comparaison_modeles`

Le workflow `Revue - Match Center unifié` génère automatiquement
`docs/phase13-modeles-evaluation-latest.json` après le score/audit
officiel, sans aucun appel à une API de bookmakers payante.

Le Lab propose la page `phase13-modeles.html`, en mode gaming
mobile Android, avec les comparaisons sur cohortes alignées.
