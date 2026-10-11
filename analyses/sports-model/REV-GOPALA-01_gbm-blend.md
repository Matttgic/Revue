# REV-GOPALA-01 — Blend walk-forward LightGBM + Dixon–Coles

- **Sport / marché :** football, 1N2
- **Source :** [gopalaakkrishna/sports-model](https://github.com/gopalaakkrishna/sports-model), commit [`b24872e1922af44a3c06230172f096797d2194da`](https://github.com/gopalaakkrishna/sports-model/commit/b24872e1922af44a3c06230172f096797d2194da)
- **Statut :** À étudier
- **Licence source :** absente; aucune reprise de code ou de données.

## Idée

Combiner un modèle de buts Dixon–Coles avec un classifieur LightGBM à trois classes. Le booster reçoit les probabilités Dixon–Coles produites en walk-forward, l’Elo et les différences de formes récentes (5 et 10 matchs), dont les buts, tirs et tirs cadrés. Les formes sont décalées d’un match; les cotes, le résultat et les statistiques du match prédit sont bannis des variables. Le booster est réajusté par fenêtres de 90 jours.

Une pondération simple des deux probabilités est ensuite utilisée :

```text
p_blend = (1 − w) × p_Dixon-Coles + w × p_LightGBM
```

Pour mesurer `w` proprement, son choix doit se faire sur la période antérieure et s’appliquer seulement à la période suivante. C’est le rôle de `evaluate_oos()` dans la source; le poids sauvegardé pour la prédiction live doit suivre ce même protocole.

## Résultat rapporté et interprétation

Le rapport source donne **+0,00053 RPS** par rapport à Dixon–Coles seul, avec un IC bootstrap à 95 % `[+0,00033 ; +0,00074]` sur `n=14 884`. Le booster seul y est moins bon que Dixon–Coles; c’est le mélange de signaux partiellement complémentaires qui explique le gain rapporté. Le même rapport indique que le blend reste environ 0,0054 RPS derrière la vraie cote Pinnacle de clôture sur l’échantillon apparié.

Ces chiffres n’ont pas été reproduits indépendamment. La fonction imbriquée de choix du poids existe, mais le point d’entrée standard appelle une évaluation où le poids optimal est sélectionné sur les mêmes lignes évaluées. La configuration suivie utilise `w=0,25`, ajusté dans `gbm_live.refit_weight()` sur l’ensemble du fichier walk-forward, tandis que la validation OOS du rapport décrit un poids moyen proche de `0,17`. Les sorties match par match de l’expérience ne sont pas dans Git. Il faut donc considérer le gain comme une hypothèse prometteuse, pas comme un effet établi.

## Test proposé dans Revue

1. Construire des sorties Dixon–Coles strictement walk-forward et les conserver par identifiant de match et heure de décision.
2. Former LightGBM uniquement sur les variables alors disponibles; garder bannis les prix si la question est l’information indépendante du marché, et toute statistique du match cible.
3. À chaque origine de test, choisir `w` et les réglages du booster sur une fenêtre antérieure distincte, les figer, puis évaluer le blend sur la fenêtre suivante jamais consultée.
4. Comparer DC seul, LightGBM seul, blend et probabilités du vrai marché dé-viggué sur les mêmes événements; rapporter RPS, log-loss, calibration et intervalles groupés par période/ligue.
5. N’évaluer la rentabilité qu’ensuite, avec des cotes accessibles à l’heure de la prédiction, frais, règlements et règle de mise définie à l’avance.

**Décision :** candidate de recherche pour l’architecture causale et le stacking; pas de copie du code et aucune intégration au modèle opérationnel Revue avant réplication du choix de poids et de la comparaison au marché.
