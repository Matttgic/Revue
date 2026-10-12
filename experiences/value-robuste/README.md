# Prix et rendement — stratégie prospective robuste

Objectif : détecter des cotes françaises supérieures à une référence de marché, conserver une sélection uniquement si cet écart résiste à plusieurs hypothèses de calcul, puis mesurer prospectivement le rendement. [Écran public](https://matttgic.github.io/Revue/value-robuste.html).

**Règle fixée le 12 octobre 2026 : `football_robust_sharp_v1`.** Elle crée son propre journal. Les anciens résultats et stratégies ne lui sont jamais réattribués. L'objectif est la rentabilité ; celle-ci n'est pas encore démontrée.

## Décision concrète

- Football : PL, Liga, Serie A, Bundesliga et Ligue 1, scores sur 90 minutes. MLS écartée de cette version à cause des règlements possibles de playoffs.
- 1N2 complet ou over/under à demi-ligne ; autres périodes, totaux de joueur/équipe, cartes/corners et lignes avec push/split exclus.
- Références observées : Pinnacle et PS3838, conservées sous leurs noms. Orbit est exclu de cette première stratégie football.
- Cotes de 1,30 à 3,50 ; observations datant d'au plus cinq minutes, référence et prix français distants d'au plus une minute ; coup d'envoi dans plus de vingt minutes.
- Marge de référence entre 0 et 8 %. Estimations multiplicative, additive, power et Shin ; quatre calculs ne sont pas quatre sources indépendantes, et Shin/additif coïncident à deux issues.
- Probabilité prudente = minimum de toutes les méthodes et de toutes les références complètes valides. Sélection seulement si `cote × probabilité prudente − 1 ≥ 0,03`. Cote minimale affichée = `1,03 / probabilité prudente`.
- Mise fictive constante de 1 unité ; une sélection par rencontre pour cette version de stratégie, au plus cinq nouvelles sélections par jour UTC et cinq paris simultanément en attente. Aucun recyclage de gains encore inconnus.

La robustesse aux méthodes ne valide pas la probabilité de référence. Une cote affichée peut être refusée, limitée ou déjà changée au moment d'agir. Le journal mesure une simulation au prix observé, pas une exécution de bookmaker garantie.

## Des enseignements aux composants

- [Shin](../../analyses/shin/AUDIT.md), [penaltyblog](../../analyses/penaltyblog/AUDIT.md), [Betting-Dashboard](../../analyses/Betting-Dashboard/AUDIT.md) : comparer le retrait de marge et ne pas retenir une sélection seulement parce qu'une formule la favorise.
- [OddsHarvester](../../analyses/OddsHarvester/AUDIT.md), [nba-betting](../../analyses/nba-betting/AUDIT.md) et [soccerdata](../../analyses/soccerdata/AUDIT.md) : identité de rencontre/marché/ligne, provenance et temps.
- [flumine](../../analyses/flumine/AUDIT.md), [sports-betting](../../analyses/sports-betting/AUDIT.md) : prix observé versus exécution, exposition et règlement.
- [wowza-betting](../../analyses/wowza-betting/AUDIT.md) : règles antérieures aux résultats, candidat séparé, mesurer les échecs sans recalibrer sur le test.

Implémentation originale Revue. Le calcul Shin indépendant du premier comparateur est réutilisé, sans code tiers importé. Aucun modèle sportif calibré n'est présumé.

## Pipeline et usage

`revue_engine_v2.execute` ajoute `value_scan` à son rapport à partir des cotes qu'il vient déjà de collecter ; aucun nouvel appel fournisseur. Le scanner cherche une référence marché par marché et considère toutes les références valides. Le CLI ci-dessous maintient un journal séparé et le rapport de l'écran :

```bash
python -m outils.suivi.value_robuste
python -m unittest tests.test_value_robuste
node tests/test_value_robuste_ui.js
```

Entrée : `docs/engine-v2-latest.json` et scores finaux de `docs/multisports-history.json`.
Sorties : `docs/value-robuste-ledger.json` et `docs/value-robuste-latest.json`.

Le workflow Engine V2 exécute les tests puis ce CLI après ses collectes prévues. Son calendrier existant est conservé. La publication Pages est désormais relancée après une exécution réussie de ce workflow. Le navigateur retire les candidats quand les prix dépassent cinq minutes ; il ne fait aucun appel à un bookmaker.

Au lancement local, aucun prix sharp complet récent n'est disponible dans l'ancien export : le rapport indique explicitement l'attente d'un relevé. Il ne réutilise pas rétroactivement les 13 comparaisons du premier exercice et n'invente aucun candidat.

## Évaluation

Chaque verrou conserve règle, version/empreinte, prix cible, prix et probabilités des références, horaires et mise. Les résultats ne sont réglés que lorsque le match est passé et qu'un score final existe dans l'historique déjà acquis. Un match nul perd les sélections domicile/extérieur et gagne la sélection nul.

Rapport : nombre réglé/en attente, mises et profit en unités, ROI, intervalle approximatif de moyenne des rendements et recul maximal en unités. Le proxy de clôture reprend seulement un prix du même bookmaker/marché/ligne observé après le verrou dans les 90 minutes avant match. Il n'est pas une clôture garantie.

Au moins 300 paris réglés sont prévus avant la première appréciation. Ce volume ne garantit aucune conclusion positive ; les intervalles, la dépendance entre matchs, la couverture et la qualité d'exécution doivent être examinés. Les seuils ne sont pas ajustés pour produire un ROI positif. Une modification de règle exige une nouvelle version et un nouveau journal ; l'empreinte empêche de mélanger des règles différentes par inadvertance.

## Corrections connexes

Le normaliseur Orbit exige désormais une liste back non vide, une liquidité finie au-dessus du seuil existant et une cote correspondant au niveau dont la liquidité est vérifiée. Les sondes absence/vide/NaN/prix incohérent sont ajoutées aux tests. Le seuil existant ne démontre pas la devise du fournisseur ni la faisabilité d'une mise ; cette source n'est pas utilisée par la stratégie football.
