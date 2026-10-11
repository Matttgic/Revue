# Audit — andrewkemmer/sports_prediction_model

- **URL originale :** [github.com/andrewkemmer/sports_prediction_model](https://github.com/andrewkemmer/sports_prediction_model)
- **Commit audité :** [`3febd52512234730070b0788f003a84f9cae5c48`](https://github.com/andrewkemmer/sports_prediction_model/commit/3febd52512234730070b0788f003a84f9cae5c48) (`2026-10-11`)
- **Date d'audit :** 2026-10-11
- **Licence :** aucun fichier de licence repéré. Seuls les constats et idées sont catalogués; aucun code ou jeu de données n'est repris.
- **Périmètre :** dépôt Python/Streamlit avec backends MLB, NBA, NFL et NHL, rapports d'audit, journaux et artefacts de livraison. Chaque sport a son README, mais aucun README général à la racine.

## Mon avis

**Très bon dépôt pour apprendre à auditer un pipeline sportif; nettement moins convaincant comme preuve d'un modèle de pari.** Il publie des rapports de corrections, des tests ciblés et des analyses qui distinguent les défauts d'entrée, les métriques causales et les résultats de prédiction. Plusieurs documents disent clairement quand une expérience ne justifie pas de promouvoir un changement.

Sa meilleure contribution à Revue est une famille de variables MLB fondées sur Statcast — xFIP, K-BB% de relève et xwOBA par type de lancer ou pool de frappeurs — et le détail de leur construction point-in-time. Mais les comparaisons disponibles ne démontrent pas que ces variables améliorent le modèle. Le rapport global de fuite reste lui-même au statut **`requires_review` / `partial_evidence_with_confirmed_repairs`**.

## Ce que le dépôt contient

- **MLB :** pipeline de prévision du vainqueur, variables d'équipes, lanceurs, frappeurs, météo et arbitres; constructions de totaux et run line; interface de suivi Streamlit.
- **NBA :** modèles moneyline et totaux/spreads, ratings de joueurs de type RAPM proxy et enrichissements de disponibilité.
- **NFL :** moneyline et distributions conjointes de marge/total; les lignes produites sont des estimations du modèle, pas des prix de bookmaker observés.
- **NHL :** moneyline, distributions de scores et composantes joueurs/gardiens, avec corrections de données et de filtres temporels.
- **Méthodes de validation :** découpages walk-forward, calibrage préquentiel, checks de couverture/identité des variables, tests d'empoisonnement temporel, analyses par seed/fold et journaux de changements.

## Éléments utiles et résultats

### Piste MLB à tester séparément

La fiche [REV-ANDREW-01](REV-ANDREW-01_mlb-pitch-hitter-features.md) résume les estimateurs xFIP et K-BB% ainsi que les mesures xwOBA découpées par type de lancer et pool de frappeurs. Les transformations sont construites avec des décalages temporels, des priors de ligue disponibles à la date cible et des contrôles de couverture. L'audit de la famille xFIP/K-BB% / xwOBA vérifie des identités de différences et la cohérence des valeurs livrées; cela valide la mécanique des données, **pas** l'utilité prédictive.

Le comparatif xFIP vs ERA indique un gain de log-loss très petit sur deux seeds et une légère dégradation sur la troisième. La règle de sélection annoncée échoue au seuil sur l'ensemble des plis (`KEEP ERA`); la queue de quatre plis est favorable mais ne suffit pas à franchir cette porte. Le scénario ajoutant K-BB% obtient, sur un seul seed, un log-loss légèrement plus mauvais. Le projet adopte néanmoins ce scénario à la demande de son propriétaire. Le premier run publié après le changement reste essentiellement inchangé et ne prouve aucun gain.

Le document de politique de tuning propose un contrôle en deux étages : une amélioration du membre sur les mêmes plis/seeds et un contrôle de non-dégradation de l'ensemble, avec calibration suivie explicitement. C'est une bonne règle à reprendre comme protocole. Son application au changement xFIP/K-BB% a toutefois été contournée par la décision propriétaire; il faut rendre visible toute exception au gate plutôt que présenter l'adoption comme résultat expérimental.

### Fuites réparées, mais pas toutes réévaluées en production

Le rapport `LEAKAGE_REPORT.json` confirme notamment que l'ordre des lignes d'un doubleheader MLB pouvait laisser le résultat d'un match commencer à mettre à jour Elo et les bilans avant le calcul des variables d'une autre rencontre le même jour. Le rapport marque la correction dans le code, mais précise qu'il faut synchroniser une reconstruction des données, du walk-forward, du calibrage et des modèles : les artefacts de production du commit n'avaient pas été remplacés par cette reconstruction.

Le même rapport consigne aussi un état NHL qui avançait avec des matchs programmés mais non joués, un test NHL qui utilisait involontairement des boxscores post-match et un score Brier de monitoring NBA défini comme erreur d'un choix dur toujours à domicile. Ces problèmes sont indiqués comme réparés dans le code ou les tests; l'ancien artefact NBA n'a pas été réécrit.

Les incertitudes restantes sont importantes : les archives ne conservent pas toujours l'heure où les faits historiques sont réellement devenus disponibles; aucun jeu complet d'odds bookmaker au cutoff n'est présent pour mesurer la performance contre le marché; les données OOF et paramètres ont déjà servi à des choix de modèle. Les rapports disent explicitement qu'aucune population finale entièrement intacte n'est certifiée. Le dépôt ne démontre donc ni ROI ni avantage de prix.

## Décision pour Revue

Conserver **une piste de recherche MLB** sur les estimateurs xFIP / K-BB% et les interactions xwOBA par type de lancer; ne pas importer les variables ou reconfigurer les modèles Revue. Commencer par une ablation ciblée, même population appariée, variables point-in-time et plis/semences gelés à l'avance. Rejeter la famille si elle ne passe pas un seuil de gain défini avant l'expérience, puis attendre un test temporel intact et des cotes réellement observées avant de parler d'avantage de pari.

Pour le reste, le dépôt confirme plusieurs principes déjà présents dans Revue : une prédiction walk-forward peut différer du mélange final recalculé sur ses propres labels; toute correction de données doit être appliquée de la reconstruction des features jusqu'au modèle livré; et l'absence d'un prix de bookmaker interdit de conclure sur le rendement. Aucun modèle n'a été exécuté ou réentraîné pour cet audit.

## Vérifications de cet audit

- Clone propre du commit `3febd525`; lecture des quatre README de sport, du rapport global de fuite, des audits MLB et des documents de validation causale.
- Les suites et réanalyses citées sont celles que le dépôt consigne; elles n'ont pas été relancées dans cet audit. Les reconstructions complètes, APIs, workflows et intégrations de livraison n'ont pas été exécutés.
- Aucun code, dépendance ou jeu de données n'a été copié dans Revue. Les différences entre correction logicielle, artefact présent et résultat mesuré sont conservées dans le dossier.
