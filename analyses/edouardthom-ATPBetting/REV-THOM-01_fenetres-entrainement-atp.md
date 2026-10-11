# REV-THOM-01 — Consensus de prédictions ATP sur fenêtres d'entraînement voisines

**Statut :** À étudier

## Identité

- **Sport / compétition :** Tennis ATP
- **Marché :** Vainqueur du match
- **Moment :** Pré-match
- **Objectif :** Stabiliser le classement des paris en testant plusieurs longueurs proches de fenêtre historique
- **Type :** XGBoost probabiliste + vote de stabilité
- **Origine :** [edouardthom/ATPBetting](https://github.com/edouardthom/ATPBetting), commit [`f0c48b9b6fb1c91aef99e3fccffd2a1f012edb79`](https://github.com/edouardthom/ATPBetting/commit/f0c48b9b6fb1c91aef99e3fccffd2a1f012edb79), `Python/stategy_assessment.py`
- **Date d'intégration :** 2026-10-11
- **Tags :** `tennis`, `ATP`, `pré-match`, `Elo`, `forme`, `ensemble`, `robustesse`, `marché`

## Hypothèse

Si une sélection change fortement quand on ajoute ou retire quelques dizaines de matchs à l'historique d'entraînement, le signal peut dépendre excessivement d'une frontière arbitraire. Un vote majoritaire entre modèles entraînés sur des fenêtres voisines pourrait privilégier les décisions stables. Ces modèles restent corrélés puisqu'ils utilisent les mêmes matchs, variables et algorithme; le vote n'est donc ni une mesure d'incertitude calibrée, ni une validation indépendante.

## Variables candidates

Le dépôt combine cote Pinnacle, Elo pré-match, rang ATP, forme globale et par surface, volume/charge récents, résultat récent et indicateurs de matchs interrompus, H2H, surface et tournoi. Les statistiques de forme sont calculées à partir de matchs strictement antérieurs à la date cible. Pour une nouvelle implémentation, contrôler séparément la disponibilité à l'heure du pari, les matchs d'une même journée et la définition point-in-time du marché.

## Algorithme observé

Pour une fenêtre de test donnée, la source entraîne sept XGBoost avec des fenêtres de 10 355, 10 370, 10 390, 10 400, 10 410, 10 430 et 10 445 matchs; les 300 matchs juste avant le test servent à l'arrêt anticipé, puis le bloc de test compte jusqu'à 2 000 matchs.

Pour chaque rencontre, les modèles votent pour une issue. La majorité (au moins quatre voix sur sept) choisit le joueur; la confiance est la moyenne des ratios `p_modèle / p_implicite` des modèles qui soutiennent la décision. Pour une cote décimale `o`, ce ratio est `p_modèle × o`. La source classe ensuite les rencontres par ratio et affiche les ROI à plusieurs seuils.

Le protocole proposé pour Revue ne reprend pas les seuils ou hyperparamètres gagnants du notebook. Il doit réestimer ceux-ci uniquement sur le passé disponible à chaque date, puis verrouiller les sélections sur le bloc prospectif suivant.

## Données nécessaires

Historique de résultats ATP avec dates, joueurs, surface, tournoi et états du match; classements pré-match; cotes Pinnacle ou autre bookmaker identifiées par issue, marché, heure de capture et acceptation réelle. Garder une provenance/licence pour chaque historique.

## Évaluation

- **Tests logiciels :** syntaxe des fichiers Python vérifiée; aucun test automatisé source exécuté ou trouvé
- **Comparaisons :** modèle central seul, vote à fenêtres voisines, Elo seul, cote seule et prix de marché dé-margé; comparer aussi les désaccords et la corrélation des sorties entre membres du vote
- **Protocole :** walk-forward imbriqué. Choisir fenêtres, hyperparamètres et seuil sur entraînement/validation antérieurs, puis geler le tout avant chaque bloc de test. Aucun tri de tout l'historique test selon les résultats n'est permis.
- **Paris / ROI / CLV :** non reproduits. Le dépôt rapporte environ +70 % sur les 5 % de rencontres les mieux classées et +20 % sur 35 %, mais ces seuils et paramètres sont évalués/sélectionnés sur la même période 2013–2018.
- **Validation hors échantillon :** non démontrée; CSV de prédictions absent, saisons manquantes et chargement non reproductible
- **Limites :** vote de modèles très semblables; prix historiques sans preuve d'acceptation; marché et résultat intégrés à un protocole de seuil a posteriori.

## Verdict / prochaine étape

Tester la **stabilité des sélections** comme diagnostic distinct de la performance, dans le modèle [tennis ATP/WTA de Revue](../../modeles/simulations/SPORTS_INDIVIDUELS_README.md). Garder la fiche à `À étudier` tant qu'une comparaison walk-forward prospective, au seuil figé et aux prix observés n'a pas montré d'amélioration par rapport au modèle central et au marché.

## Traçabilité

Voir l'[audit source](AUDIT.md) et la [synthèse transversale](../../catalogue/ENSEIGNEMENTS.md). Aucun code ni jeu de données du dépôt tiers n'a été copié.
