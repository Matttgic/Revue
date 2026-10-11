# REV-GDSB-01 — Variables disponibles à l'instant où le prix est coté

**Statut :** À étudier

## Identité

- **Sport / compétition :** tous sports disposant d'instantanés fiables
- **Marché :** tout marché avec une cote horodatée
- **Moment :** pré-match ou live
- **Objectif :** contrôle du backtest contre les fuites temporelles
- **Type :** méthode de préparation des données / validation
- **Origine :** Georgios Douzas, [sports-betting](https://github.com/georgedouzas/sports-betting), MIT, commit `eb4cedf376663fac68f508e50b83fd832e74dfd4`; `src/sportsbet/dataloaders/_base.py`
- **Date d'intégration :** 2026-10-11
- **Tags :** `point-in-time`, `pré-match`, `live`, `instantanés`, `fuite-temporelle`, `backtest`

## Hypothèse

Pour simuler une mise, l'ensemble de variables doit refléter l'information connue au moment où la cote testée était disponible. Les variables apprises ou publiées plus tard ne peuvent pas soutenir cette mise. Cette règle rend l'évaluation plus crédible; elle ne crée pas à elle seule un signal rentable.

## Données nécessaires

Pour chaque événement, conserver des instantanés de statistiques et de prix avec un identifiant de match, un état (`preplay`/`inplay`/`postplay`) et une heure réelle de disponibilité. Associer les résultats au moment où ils deviennent définitifs. Les fournisseurs doivent documenter les champs retardés, révisés ou rétroactivement complétés. Un simple horodatage de match ne suffit pas si l'heure de publication est différente.

## Algorithme de la source

1. Définir l'instant cible dont on prédit le résultat.
2. Trouver l'instant le plus tardif auquel le prix utilisé était effectivement offert.
3. Ne fournir au modèle que les instantanés antérieurs ou égaux à un horizon qui n'excède pas cet instant de prix.
4. Refuser explicitement une demande d'horizon postérieure au prix.
5. Extraire la cible depuis l'instant du résultat et le prix depuis le fournisseur sélectionné.

Le code source décrit une table d'instantanés contenant statistiques/cotes, puis construit `X`, `Y`, `O`. Les tests anti-fuite construisent deux matchs pré-match et live pour vérifier que le score de mi-temps est exclu face à une cote pré-match, conservé avec une cote de mi-temps, et qu'un horizon interdit déclenche une erreur. Cette fiche décrit l'approche observée; elle n'en copie pas le code.

## Évaluation

- **Tests logiciels :** cinq tests de non-fuite repérés dans le dépôt; non exécutés ici, faute de `pytest` installé.
- **Protocole backtest :** la fonction source trie les événements par date et utilise `TimeSeriesSplit`. Pour Revue, le découpage doit en plus garder ensemble tous les événements du même instant de décision; les dates sans heure réelle doivent rester regroupées ou être exclues.
- **Paris, résultats, mise, profit, ROI, drawdown :** non testés pour cette fiche.
- **Calibration, CLV, validation hors échantillon :** non testées.
- **Limites :** contrôle dépendant de la qualité des timestamps et de la provenance des champs. Une fuite subsiste si la source attribue à tort un ancien timestamp à une statistique disponible seulement après coup. Une séparation chronologique par lignes peut scinder des matchs simultanés.

## France / ANJ

Ce contrôle de recherche n'implique aucun pari. L'autorisation des marchés, les flux de données et les conditions des opérateurs restent à vérifier avant tout usage opérationnel.

## Verdict / prochaine étape

Intérêt documentaire élevé et contribution logicielle précise; aucune preuve de rentabilité. Réimplémenter le contrôle dans le protocole de données Revue, puis ajouter des tests synthétiques où des informations tardives et des matchs simultanés ne peuvent pas franchir la coupure. Ne reprendre ni l'outil de placement automatique ni les données de la source.

## Traçabilité

- [Audit du dépôt](AUDIT.md)
- [Guide source sur l'instant de pari](https://github.com/georgedouzas/sports-betting/blob/eb4cedf376663fac68f508e50b83fd832e74dfd4/docs/practice/betting_moment.md)
- [Implémentation source](https://github.com/georgedouzas/sports-betting/blob/eb4cedf376663fac68f508e50b83fd832e74dfd4/src/sportsbet/dataloaders/_base.py)
- [Tests source](https://github.com/georgedouzas/sports-betting/blob/eb4cedf376663fac68f508e50b83fd832e74dfd4/tests/dataloaders/test_leakage.py)
- [Licence](https://github.com/georgedouzas/sports-betting/blob/eb4cedf376663fac68f508e50b83fd832e74dfd4/LICENSE)
