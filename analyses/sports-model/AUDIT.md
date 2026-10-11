# Audit — gopalaakkrishna/sports-model

- **URL originale :** [github.com/gopalaakkrishna/sports-model](https://github.com/gopalaakkrishna/sports-model)
- **Commit audité :** [`b24872e1922af44a3c06230172f096797d2194da`](https://github.com/gopalaakkrishna/sports-model/commit/b24872e1922af44a3c06230172f096797d2194da) (`2026-10-11`, mise à jour du ledger)
- **Date d’audit :** 2026-10-11
- **Licence :** aucun fichier de licence repéré. Les données brutes et artefacts du dépôt ne sont pas copiés dans Revue.
- **Contenu :** dépôt Python multi-sports (football, MLB, NFL, WNBA, cricket) avec modèles, données Parquet/CSV, rapports, ledger papier et deux workflows GitHub Actions. 235 fichiers suivis, environ 17 Mo de données. Dépendances avec versions minimales mais non verrouillées.

## Mon avis

**Un des dépôts les plus instructifs de cette série, surtout grâce à ses analyses d’échecs.** L’auteur compare ses probabilités au marché, documente des bugs qui avaient créé de faux résultats positifs, fait des ablations et conserve un suivi de pronostics. Plusieurs conclusions négatives sont assumées au lieu d’être maquillées en succès. Je ne reprendrais toutefois pas ses chiffres de benchmark sans précaution : le dépôt a longtemps comparé aux cotes d’ouverture tout en les appelant cotes de clôture, et certaines routines de production n’ont pas été alignées sur la correction documentée.

La valeur est donc **méthodologique et exploratoire**, pas une preuve de rendement. Le modèle football de base reste inférieur au marché; le gain publié du blend LightGBM est modeste et sa validation n’est pas raccordée sans ambiguïté au poids actuellement utilisé en direct.

## Ce que le dépôt met en œuvre

- **Football :** modèle Dixon–Coles de buts avec ratings d’attaque/défense, décroissance temporelle et régularisation; dérivation des probabilités 1N2, totaux et BTTS. Les divisions d’un pays sont ajustées ensemble pour éviter le redémarrage à zéro des équipes promues.
- **Blend exploratoire :** LightGBM multiclasses construit à partir de probabilités Dixon–Coles walk-forward, Elo et formes glissantes de 5/10 matchs (buts, tirs, tirs cadrés). Le code exclut les cotes et les statistiques du match cible, et réajuste le booster par fenêtres de 90 jours. Le flux de pronostic du football appelle bien ce blend pour les cinq grands championnats.
- **Autres sports :** Poisson de courses en MLB avec lanceurs et parcs, régression de marge pour NFL/WNBA, et modèles/cricket; les rapports montrent que les gains ne se transfèrent pas automatiquement d’un sport ou marché à l’autre.
- **Mesure :** comparaison log-loss/RPS/Brier au marché, ablations appariées, calibration, contrôles de liquidité, journaux de décisions figées et règlement prudent. Les appels Kalshi de ce dépôt sont en lecture seule; je n’ai trouvé aucun code qui place des ordres.

## Résultats et limites de preuve

### Les résultats propres à chaque modèle restent modestes ou négatifs

Dans `reports/FINDINGS.md`, le Dixon–Coles football améliore nettement une fréquence de base mais ne bat pas la ligne de marché. Le rapport corrigé de septembre estime encore un écart d’environ **0,0054 RPS** au vrai prix Pinnacle de clôture sur son échantillon apparié. Le gain de calibration ou de prévision contre une fréquence de base ne constitue donc pas un gain de pari.

Le rapport attribue au blend Dixon–Coles + LightGBM un gain de **0,00053 RPS** sur Dixon–Coles seul, avec un intervalle bootstrap rapporté de **[+0,00033 ; +0,00074]** sur 14 884 matchs. C’est un signal modeste pour la qualité de prévision, pas un avantage sur le marché : le rapport garde un écart positif au marché. Cette amélioration est publiée par l’auteur et n’a pas été reproduite ici.

Le registre suivi dans ce commit contient 135 décisions principales : 128 réglées, 4 ouvertes et 3 annulées; les décisions réglées couvrent cinq sports. Le log-loss binaire recalculé à partir des probabilités figées est **0,61959 pour le modèle contre 0,61941 pour le marché**. Ce petit échantillon hétérogène est pratiquement à parité et ne démontre ni rendement ni supériorité. Le ledger séparé de totaux football n’a que 35 décisions réglées au commit; il est trop court pour conclure.

Les propres rapports signalent aussi des constats à garder : le modèle MLB non calibré est moins bon qu’une constante; une régression de runs indépendante est trop peu dispersée pour les totaux MLB; le modèle NFL était affecté par un signe de handicap inversé et l’absence d’intercept; l’ajout d’avantages domicile par équipe a empiré le résultat. Les corrections et échecs sont documentés, mais leurs nouveaux chiffres demeurent des résultats d’auteur.

### Deux incohérences importantes dans les comparaisons

1. **Ouverture appelée clôture.** Le dépôt reconnaît dans `FINDINGS.md` que `PSH/PSD/PSA` sont les cotes Pinnacle pré-clôture, tandis que les vrais prix de clôture sont `PSCH/PSCD/PSCA`. Le code d’évaluation historique (`backtest.py`, `calibrate.py`, `gbm_model.py`) continue pourtant à sélectionner `PSH`, et `eval_vs_avg.py` traite également `AvgH/AvgD/AvgA` comme une ligne moyenne de clôture. `fetch_data.py` compte encore `PSH` sous l’étiquette « Pinnacle closing ». Le rapport ultérieur compare aussi aux vraies colonnes de clôture et conclut que le marché reste devant; cela rend le verdict négatif plausible, mais ne répare pas rétroactivement les tableaux ni les scripts qui conservent le mauvais libellé.
2. **Sélection du poids du blend.** `gbm_model.py` contient une fonction `evaluate_oos()` qui choisit le poids sur les données antérieures à chaque fenêtre, puis l’applique à la fenêtre suivante. Mais le `main()` normal appelle `evaluate()`, où le meilleur poids est choisi sur les mêmes matchs qu’il score. De plus, `gbm_live.refit_weight()` règle un poids unique sur l’ensemble des prédictions walk-forward et leurs résultats, puis l’écrit dans `gbm_blend.json`. Le fichier suivi dans ce commit contient **0,25**, alors que le rapport décrit un poids OOS moyen proche de **0,17**. Le blend utilisé par le programme de pronostic lit le poids persistant. La fonction d’évaluation OOS est une bonne pièce de recherche, mais elle ne justifie pas à elle seule le poids en production; le gain et son intervalle doivent être réévalués avec le même protocole imbriqué qui choisit le poids.

Le jeu de prédictions `gbm_preds.parquet` nécessaire pour reproduire le résultat n’est pas suivi par Git; le dépôt fournit le rapport et un résumé JSON de poids, pas les sorties match par match qui étayent l’intervalle annoncé.

## Piste retenue pour Revue

Le blend causal LightGBM + Dixon–Coles est documenté dans [REV-GOPALA-01](REV-GOPALA-01_gbm-blend.md), **À étudier**. Revue n’a pas de blend de ce type dans son modèle football avancé, donc la piste est distincte. Sa force est d’expliciter des barrières contre les fuites (prévisions de base walk-forward, décalage des formes glissantes, bannissement des colonnes de cote et du résultat futur). Sa faiblesse est l’écart entre mesure OOS et pondération actuellement sauvegardée, ainsi que l’absence d’artefacts de prédiction réutilisables. Aucun code, modèle, donnée ou poids n’a été copié.

Autre enseignement à retenir sans en faire une stratégie : **un grand désaccord avec le marché peut signaler une erreur du modèle plutôt qu’une value**. Le rapport le montre dans ses tranches de désaccord, mais les premiers chiffres utilisent la ligne d’ouverture. Ne pas reprendre ses seuils sans nouvelle évaluation point-in-time contre la vraie clôture et des prix exécutables.

## Vérifications effectuées

- Clone propre de `main` au commit indiqué; inspection des modèles, routines de backtest/calibration, workflow, rapports, données et registres.
- `python -m compileall -q src tests` réussit. La suite `python -m unittest discover -s tests -v` n’a pas démarré : les imports échouent parce que `requests` n’est pas installé dans l’environnement; aucune dépendance n’a été installée pour cet audit.
- Aucun modèle n’a été réentraîné; aucun API, workflow GitHub, appel de marché, appel authentifié ou processus de règlement n’a été exécuté. Les résultats présentés sont ceux du dépôt, sauf le résumé du ledger ci-dessus calculé directement depuis son fichier JSONL.
- Aucun audit exhaustif des droits sur les jeux de données, des conditions d’utilisation, ni de la sécurité opérationnelle n’a été effectué. Aucune clé ou donnée n’a été copiée dans Revue.

## Verdict

**À conserver comme référence d’ingénierie de validation et source d’une piste GBM, pas comme source de picks.** Les analyses des hypothèses rejetées, des prix réellement disponibles et des erreurs de pipeline sont sa meilleure contribution. L’idée de blend mérite une réplication indépendante sur les données Revue, avec poids choisi dans une boucle temporelle interne et résultat mesuré sur une période externe intacte. En l’état, aucune rentabilité n’est démontrée.
