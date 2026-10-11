# Phase 10 — NBA, MLB, football et suivi prospectif

Cette étape ajoute cinq sorties expérimentales sur trois sports, tout en
conservant les modèles NHL déjà présents.

- **NBA** : modèle ESPN saison précédente, Elo de ratings ESPN issus de la
  saison précédente (saison régulière actuelle non encore observable),
  et combinaison corrélée des deux. Avantage domicile 55 points Elo
  *hypothétique*, régression neutre 42 %, combinaison 55/45.
  Une combinaison corrélée **n'est pas une preuve indépendante**.
- **MLB** : Elo reconstruit à partir des scores ESPN historiques
  observés avant le match, jamais le SQL privé ni les lanceurs confirmés.
- **Football** : combinaison géométrique 45 % modèle de score ESPN et
  55 % modèle dérivé des tirs ESPN, avec minimum trois matchs des
  deux équipes, divergence inférieure à 20 points TV. Aucun xG Opta.
- **NHL** : modèles existants intégrés au même Match Center.

Les prédictions suivent les ID ESPN, identités exactes des deux équipes,
horodatages de source et du coup d'envoi. Aucune cote jouable et aucune
EV+ ne sont déduites. Un registre séparé conserve les sorties par
match ET version de modèle avant match. ESPN scoreboard final seul
déclenche Brier et Log Loss ; aucune simulation d'argent.
MLS/UCL : modèle disponible mais settlement suspendu faute de preuve
universelle des règles de durée/stade du tournoi.
Les résultats sont pris en compte uniquement après le début effectif
du suivi : **aucun backfill**.

Workflow Match Center : tests, génération du fichier phase10, intégration
des candidats, verrouillage prospectif, résultats officiels, publication
et lien au Lab. Fréquence : environ une fois par heure.

La fidélité identique aux SQL et aux décisions de Clairvoyance demeure
non vérifiée. Minimum de 100 finales par version avant examen préliminaire
de calibration ; une bonne statistique n'est jamais une garantie de rendement.
