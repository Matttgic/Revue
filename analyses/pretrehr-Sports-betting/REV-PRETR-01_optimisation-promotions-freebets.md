# REV-PRETR-01 — Couverture de promotions et conversion de freebets

**Statut :** À étudier

## Identité

- **Sport / compétition :** Multi-sports
- **Marché :** Issues exhaustives d'un match, principalement 1N2
- **Moment :** Pré-match
- **Objectif :** Calculer la répartition de mises qui égalise les retours; estimer la valeur d'une promotion
- **Type :** Optimisation déterministe / couverture, pas prédiction
- **Origine :** [pretrehr/Sports-betting](https://github.com/pretrehr/Sports-betting), Raphaël Prêtre-Heckenroth, licence MIT, commit [`9f96cf4e0020249a05617ab414b800ce7c058aef`](https://github.com/pretrehr/Sports-betting/commit/9f96cf4e0020249a05617ab414b800ce7c058aef), `sportsbetting/basic_functions.py`
- **Date d'intégration :** 2026-10-11
- **Tags :** `pré-match`, `cotes`, `gestion-mise`, `freebet`, `promotion`, `couverture`

## Hypothèse

Quand toutes les issues d'un marché sont couvertes aux meilleures cotes disponibles, on peut égaliser le retour brut des issues et quantifier le coût ou la valeur théorique d'une promotion. Cela ne crée pas forcément un avantage : les marges, changements de prix, limites, acceptation des paris, règles de void/cashout et conditions d'éligibilité peuvent réduire ou annuler le résultat.

## Données nécessaires

Pour chaque issue : cote décimale réellement disponible, bookmaker, heure observée et mise acceptée. Il faut aussi enregistrer la version exacte des règles promotionnelles : seuils, limites, expiration, statut fractionnable ou non, traitement des annulations, cote minimale et valeur du remboursement.

## Algorithme

Pour un marché à `n` issues exhaustives de cotes `oᵢ`, avec budget total `B`, le retour brut égalisé est :

`R = B / Σ(1 / oᵢ)`

et la mise sur chaque issue est `sᵢ = R / oᵢ`. Le profit net théorique si une issue gagne est `R − B`. Une couverture sans perte exige `Σ(1/oᵢ) < 1`; sinon la couverture répartit le risque mais verrouille une perte théorique, avant arrondis et contraintes des bookmakers.

Pour un freebet dont la mise initiale n'est pas rendue, son rendement équivaut à une cote ajustée `oₖ − 1` sur l'issue choisie; les mises cash de couverture doivent être calculées sur les retours nets selon les règles exactes de l'offre. Le dépôt implémente ces opérations dans `gain`, `mises`, `cotes_freebet` et `mises_freebet`. Il contient aussi des coefficients fixes `0.77` et `0.8` pour certaines estimations promotionnelles : les remplacer par des conditions observées ou les marquer comme hypothèses, jamais comme taux acquis.

## Usage

La fiche décrit une méthode à réimplémenter; le paquet source n'est pas une dépendance Revue. Entrée minimale : prix horodatés de chaque issue, budget, limites de mise et paramètres contractuels de la promotion. Sortie : mises arrondies, retour net par issue et statut de faisabilité. Aucun code source tiers n'a été copié.

## Évaluation

- **Tests logiciels :** AST des 30 fichiers Python sans erreur de syntaxe; suite du dépôt non exécutée car elle appelle le web et Selenium
- **Protocole backtest :** comparer, sur prix historisés et règles conservées, les mises calculées aux règlements réels; inclure changements de cote, arrondis, mises rejetées, annulations et limites
- **Paris / mises / profit / ROI :** non testés; aucun registre réglé fourni
- **Dispersion / calibration / CLV :** non applicable à l'optimiseur en soi; surveiller l'écart entre retour théorique et règlement observé
- **Validation hors échantillon :** non réalisée
- **Limites :** la couverture n'est exacte que si les issues sont exhaustives et leurs règles de règlement compatibles. Les cotes ne sont pas figées par le dépôt; estimations 77–85 % de conversion des freebets dans le README non vérifiées.

## France / ANJ

Vérifier pour chaque offre le bookmaker agréé, le marché autorisé, les conditions de promotion et le droit d'accès automatisé aux cotes. Applicabilité actuelle : **à vérifier**.

## Verdict / prochaine étape

Intérêt documentaire réel pour la comptabilité des freebets et la simulation de promotions; aucune preuve que les retours annoncés soient obtenus en pratique. Réimplémenter en calcul pur, puis comparer chaque sortie aux règles et prix effectivement disponibles avant de cataloguer un résultat.

## Traçabilité

Voir l'[audit source](AUDIT.md) et le [README du dépôt](https://github.com/pretrehr/Sports-betting/tree/9f96cf4e0020249a05617ab414b800ce7c058aef). Cette fiche est indépendante et ne modifie aucun autre dossier source.
