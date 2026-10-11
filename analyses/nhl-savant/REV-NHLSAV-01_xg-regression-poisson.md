# REV-NHLSAV-01 — NHL : xG régularisé et projection de buts

**Statut : À étudier.** Source : [dpk1212/nhl-savant](https://github.com/dpk1212/nhl-savant), commit [`0dc9ca7`](https://github.com/dpk1212/nhl-savant/tree/0dc9ca79275549c8a83e91ddc9d9b8f28c9804b1). Fiche de méthode rédigée indépendamment; aucun code ni CSV source copié.

## Hypothèse

Les xG par situation peuvent fournir des taux de buts attendus en combinant la production d’une équipe et la défense de son adversaire. Une moyenne récente et une régression vers la moyenne de ligue pourraient limiter respectivement le retard de forme et le bruit des petits échantillons. Une distribution des buts peut ensuite produire une probabilité de résultat.

Cette hypothèse ressemble aux modèles NHL existants de Revue par ses entrées xG et sa couche Poisson. La piste propre à ce dépôt est la combinaison de pondération L10, shrinkage par nombre de matchs, situations 5v5/PP et correction PDO dans une estimation de buts d’équipe. Elle n’ajoute pas une preuve nouvelle de rentabilité.

## Schéma de calcul observé

Résumé conceptuel des choix codés par l’auteur, à ne pas traiter comme paramètres validés :

1. Convertir les xG offensifs et défensifs 5v5 en taux par 60 minutes.
2. Après dix matchs, mélanger le taux L10 à 60 % et le taux saisonnier à 40 %; avant cela, garder le taux saisonnier.
3. Réduire chaque taux vers la moyenne de ligue par une pondération fixe selon les matchs joués : 35 % avant 5 matchs, 30 % avant 10, 20 % avant 40, puis 10 %.
4. Construire le taux 5v5 comme 40 % du taux offensif ajusté et 60 % du taux défensif adverse. Ajouter séparément les occasions de jeu de puissance, également croisées avec la défense adverse.
5. Appliquer des ajustements PDO et de finition bornés, une pondération de temps de jeu par situation et, si leurs données sont disponibles, l’avantage domicile et la qualité du gardien adverse.
6. Convertir les buts attendus des deux clubs en probabilités par une approximation Poisson et un traitement spécifique des égalités.

Les règles de spécial teams sont une heuristique distincte dans le tableau de bord : un écart supérieur à 2 xG/60 entre PP et PK déclenche une suggestion de total d’équipe. Le seuil et le « edge » affiché ne viennent pas d’une calibration de probabilités ou de cotes.

## Données nécessaires

Snapshots horodatés d’xG d’équipe séparés au minimum par 5v5 et PP/PK; calendrier, score et statut officiel du match; qualité des gardiens disponible avant le départ; cotes moneyline et totaux observées à l’heure de décision, ainsi que prix de clôture. Pour chaque valeur, conserver le fournisseur, le moment de collecte, la saison et les corrections ultérieures.

## Évaluation

- **Tests logiciels :** aucun test ciblé du modèle repéré; le build du projet passe, mais le lint global échoue. Détails dans l’[audit](AUDIT.md).
- **Test fourni :** 175 matchs de réglementation, RMSE 2,139 buts, Brier 0,2419, exactitude directionnelle 56,6 %. Entrées temporellement contaminées; chiffres non retenus comme preuve.
- **Cotes, CLV, ROI, drawdown :** absents de ce test.
- **Validation hors échantillon :** non démontrée.
- **Limites critiques :** statistique d’équipe issue d’une seule photo (5–7 matchs) pour toutes les dates; gardien réel du match cible utilisé; historique saisonnier des gardiens sans snapshots datés; seuils et poids non justifiés hors échantillon.

## Protocole indépendant proposé

- Figer avant la saison le mélange L10/saison, les tranches de shrinkage et les paramètres de situation; si plusieurs valeurs sont comparées, les choisir sur une période d’entraînement distincte.
- À chaque date, reconstruire uniquement les statistiques issues de matchs terminés et de titulaires connus à cet instant. Conserver aussi un modèle sans gardien confirmé pour mesurer la couverture réellement disponible.
- Comparer xG seul, xG + shrinkage, xG + L10 et version complète sur les mêmes matchs, contre la moyenne de ligue, le marché sans marge et un modèle NHL de référence. Publier Brier, log-loss, calibration et intervalles.
- Ne calculer une rentabilité que pour les paris pré-match à prix horodaté réellement offert; publier CLV, ROI, coûts, limites et taille d’échantillon. Ne pas interpréter le taux de victoire seul.

## France / ANJ et traçabilité

Compatibilité des marchés NHL et droits de réutilisation des données à vérifier. Le dépôt source ne fournit pas de licence logicielle explicite; conserver cette fiche comme description de recherche et réimplémenter toute formule sans reprendre le code ni ses fichiers.

Voir l’[audit complet](AUDIT.md) et les fiches NHL déjà cataloguées pour le [Poisson point-in-time et le marché](../../recherche/hockey/nhl-point-in-time-poisson-marche.md), l’[identité du gardien titulaire](../../recherche/hockey/nhl-gardien-titulaire.md) et la [calibration prospective](../../recherche/hockey/nhl-calibration-prospective.md).
