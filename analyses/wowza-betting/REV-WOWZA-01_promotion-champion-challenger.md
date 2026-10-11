# REV-WOWZA-01 — Garde de promotion champion/challenger

**Statut : À étudier — replay historique publié par l'auteur; aucune réplication indépendante.**

- **Domaine :** cycle d'entraînement et déploiement de modèles prédictifs
- **Marché :** tout modèle donnant lieu à un comparatif de log-loss/calibration et à une décision de remplacement
- **Origine :** [`NevixAA/wowza-betting`, commit `87c4229`](https://github.com/NevixAA/wowza-betting/tree/87c4229dbb326306df8db7eb591bc8a857454058), `pipeline.py`, `src/promotion_gate.py`, `src/model_validation.py`
- **Licence :** aucune licence explicite repérée; aucun code repris
- **Audit :** [dossier complet](AUDIT.md)

## Hypothèse

Un candidat ne devrait pas remplacer le modèle champion simplement parce qu'il ne franchit pas une tolérance de régression très large. Comparer les deux modèles sur les mêmes fixtures réservées à l'évaluation; garder le champion si le candidat se dégrade; exiger, pour une promotion positive, une amélioration assez grande, distinguable du bruit et confirmée sur des données futures indépendantes.

Il faut séparer deux décisions qui n'ont pas la même preuve : un **coupe-circuit** contre un modèle cassé, et une **preuve d'amélioration** suffisante pour remplacer le système en place. Le rapport du dépôt souligne qu'une porte exigeant toujours une grande amélioration peut aussi bloquer de bons réentraînements; elle doit donc être comparée à ce qu'elle empêche réellement, et non à une préférence de prudence abstraite.

## Éléments observés

Le replay Wowza du 4 octobre porte sur 91 décisions historiques. L'ancienne tolérance a promu 88 candidats, dont 29 étaient moins bons sur le log-loss reporté. Le code actif ajoute une règle de non-dégradation sur le même holdout; les comparaisons avec données incompatibles sont étiquetées faibles. La porte statistique à plusieurs checks (IC bootstrap par blocs, taille minimale, calibration, canari de probabilités, régression par ligue et confirmation prospective) tourne toutefois en observation et n'est pas la porte qui décide de remplacer le modèle.

Une limite majeure est explicite : le test du modèle en production apprend la méta-couche sur les labels du bloc ensuite appelé test et l'évalue dessus. Le gate actif compare la moyenne des modèles de base, pas la sortie méta qui est réellement servie. Le replay démontre un défaut de l'ancienne règle sur ces décisions, mais ne valide pas la qualité du prédicteur déployé.

## Protocole d'usage pour Revue

- Geler un manifeste de fixtures exact (identifiants, date, marché/ligue, cible et variables) utilisé par champion et candidat; même période de scoring et même transformation.
- Réserver des blocs temporels distincts pour ajustement des modèles, calibration, éventuel empilement et évaluation finale. Ne pas réutiliser les labels du holdout dans une couche qui sera ensuite évaluée dessus.
- Rapporter les métriques du modèle réellement servi, les sous-modèles séparément, log-loss/Brier et calibration; le log-loss moyen des briques n'est pas un substitut à la qualité de la prédiction combinée.
- Bloquer une régression sur le holdout comparable; pour une promotion positive, exiger effet matériel, intervalle apparié qui exclut zéro et réplication prospective. Maintenir un shadow log jusqu'à cette réplication.
- Mesurer aussi le coût d'opportunité des candidats bloqués; ne pas supposer qu'un seuil plus strict améliore le rendement.

**Verdict :** la comparaison symétrique sur le même dataset et le replay des décisions sont des contrôles utiles. La règle source reste à adapter, car elle ne juge pas encore l'ensemble effectivement servi et son holdout est contaminé par l'apprentissage du méta-modèle.
