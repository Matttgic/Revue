# REV-STATSEER-01 — Part de snaps NFL et changement de rôle

**Statut : À étudier — résultat de prévision publié par l’auteur, non reproduit indépendamment.**

- **Sport / ligue :** football américain, NFL
- **Marché visé :** props de joueurs, indirectement; la sortie testée est la part des snaps offensifs, pas une sélection over/under
- **Type :** régression à gradient boosting, caractéristiques de rôle et historique
- **Origine :** [Stat-Seer, commit `1016bf6`](https://github.com/derekj987/Stat-Seer/tree/1016bf6193c8ef03de1f756202c887baa829d2f1)
- **Licence :** aucune licence explicite repérée; aucune reprise de code

## Hypothèse

La part de snaps récente est persistante, mais une variation de rôle peut être plus prévisible lorsque des informations de disponibilité ou de profondeur d’effectif changent. Le modèle combine notamment des EWMAs retardées, le niveau de la saison précédente, le rang dans le groupe de poste, les snaps vacants signalés comme Out/Doubtful, un retour après absence et le rapport de blessure de la semaine. La cible est la part de snaps observée cette semaine, conditionnelle au fait que le joueur soit actif.

## Résultat source

Sur des saisons de test 2022–2024, l’auteur rapporte 17 404 prédictions : MAE 0,1047 contre 0,1112 pour la persistance de la semaine précédente (+5,9 %). Sur les semaines où un signal de changement pré-match est déclenché, il annonce 0,1123 contre 0,1223 (+8,2 %, n=9 345). Sans signal, le gain rapporté est de 2,6 % (n=8 059). Les intervalles conformes publiés ont une couverture proche de leur niveau nominal.

Cette mesure est une MAE de part de snaps. Elle ne mesure pas la justesse des props ni un profit de pari. Dans le rapport source, la validation contre les lignes de clôture en 2024 donne 50,2 % de réussite sur 6 457 props, sous le seuil approximatif de 52,4 % à −110; l’auteur dit que le modèle ne bat pas le marché.

## Limites et risques de fuite

- La population de test comprend des joueurs qui ont effectivement joué. Il manque un modèle pré-match de disponibilité; les inactifs tardifs ne sont pas tous présents dans le rapport médical final.
- Plusieurs variables de groupe (`grp_prior_sum`, `grp_n_active`, `depth_rank`) sont calculées dans le panel de snaps de la semaine prédite. Leur disponibilité à l’heure de décision doit être vérifiée à partir d’effectifs connus avant match.
- La part de snaps ne détermine pas les carries ou targets. Les transformer en distributions de props et évaluer leur prix est une étape distincte.
- Les performances, données et comparaisons ci-dessus sont déclarées dans le dépôt source; elles n’ont pas été reproduites dans Revue.

## Protocole Revue

1. Fixer un instant de prévision (par exemple après le rapport officiel du vendredi) et reconstruire à cet instant l’effectif ainsi que chaque feature.
2. Garder des saisons postérieures intactes; comparer au dernier match, à une moyenne saison et au marché.
3. Séparer l’évaluation de `E[share | active]` du modèle de probabilité qu’un joueur soit actif.
4. Convertir les prévisions en volume seulement après une validation des touches et des snaps, puis tester contre des lignes de props horodatées accessibles au même instant.
5. Publier couverture, calibration, nombre de prédictions, CLV et rendement net avec incertitude; ne pas assimiler le gain de MAE à un edge.

**Verdict :** piste utile pour comprendre les changements d’utilisation; aucune preuve qu’elle produise des paris gagnants.
