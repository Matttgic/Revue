# Audit de dépôt tiers — edouardthom/ATPBetting

- **URL originale :** https://github.com/edouardthom/ATPBetting
- **Auteur / organisation :** edouardthom
- **Commit audité :** [`f0c48b9b6fb1c91aef99e3fccffd2a1f012edb79`](https://github.com/edouardthom/ATPBetting/commit/f0c48b9b6fb1c91aef99e3fccffd2a1f012edb79), branche `master`, 2018-03-13
- **Date de consultation :** 2026-10-11
- **Licence :** aucune licence repérée; aucun code ni fichier de données n'a été repris dans Revue
- **État de maintenance :** dernier commit en 2018, aucune suite de tests ou configuration de dépendances repérée
- **Langage / stack :** Python, pandas, scikit-learn, XGBoost, notebooks Jupyter, classeurs tennis-data.co.uk

## Résumé technique

Le projet assemble des résultats ATP et des cotes dans 18 classeurs annuels, de 2000 à 2018. La dernière saison livrée s'arrête au 4 mars 2018; 2014 n'est pas présent. `Python/main.py` fabrique des variables de forme joueur (globales et par surface), H2H, activité/résultats récents, rang ATP, Elo, tournoi/surface et cotes Pinnacle. Un XGBoost binaire classe les deux issues d'un match.

Le test décrit dans le notebook utilise des blocs successifs : environ 10 400 matchs d'entraînement, 300 matchs de validation et 2 000 matchs de test. Pour réduire la sensibilité à la taille de l'historique, le code entraîne sept variantes avec des fenêtres de 10 355, 10 370, 10 390, 10 400, 10 410, 10 430 et 10 445 matchs. Il vote sur l'issue majoritaire et moyenne les ratios de confiance des modèles qui soutiennent cette issue. Le ratio est `p_modèle / p_implicite` (soit `p_modèle × cote`).

## Idées identifiées et comparaison

| Idée | Ce que contient le dépôt | Comparaison / décision |
|---|---|---|
| Variables de forme tennis par surface, joueur, H2H et récence, avec cote et Elo | Statistiques dérivées des matchs antérieurs, puis modèle XGBoost de gagnant | Complète la piste Elo ATP/WTA de [REV-MOD-IND-01](../../modeles/simulations/SPORTS_INDIVIDUELS_README.md); fiche de recherche ci-dessous. Les variables sont une piste, pas une preuve d'edge. |
| Tester la stabilité d'un modèle en variant légèrement la longueur de sa fenêtre d'entraînement | Sept fenêtres proches, vote majoritaire et moyenne de confiance | Variante plus précise que l'ensemble de modèles hétérogènes de [REV-CLAIR-06](../2026-10-09_Purple-Wraith_clairvoyance-backend.md) : ici, les modèles partagent données, variables et algorithme. À évaluer comme diagnostic de sensibilité; les votes ne sont pas indépendants. |
| Sélectionner les matchs par ratio de probabilité du modèle à probabilité implicite | Les sorties de tous les blocs 2013–2018 sont regroupées et classées par ratio | Le tri utilise les sorties et résultats de toute la période présentée comme test; le seuil gagnant est donc sélectionné sur cette même période. Les ROI ne sont pas conservés comme preuve hors échantillon. |

## Vérifications et limites

- **Données :** 18 classeurs sont fournis; aucune archive de prévisions figées ni de transactions réellement acceptées. Il y a une saison manquante (2014) et 2018 ne couvre que janvier au 4 mars. La lecture statique repère aussi une ligne de match dupliquée dans `Data/2001.xls`.
- **Ordre des fichiers :** le script utilise `glob.glob()` sans tri, puis concatène `[l[0]] + l[2:]`, ce qui écarte arbitrairement l'élément d'index 1. Dans l'ordre renvoyé par le système lors de cet audit, cela exclurait `2017.xlsx`; l'année écartée peut changer selon l'ordre du système de fichiers.
- **Reproductibilité :** le dossier `Generated Data` attendu par le script et le CSV de confiance `confidence_data.csv` ne sont pas dans le dépôt. Le notebook contient des sorties et commentaires d'auteur, mais le résultat dérivé n'est pas rejouable directement à partir des fichiers livrés.
- **Résultats annoncés :** le notebook rapporte environ +70 % de ROI sur les 5 % de matchs les mieux classés et environ +20 % sur 35 %. Il indique que les paramètres ont été choisis pour maximiser le ROI. Le score est ensuite tracé pour plusieurs seuils sur l'ensemble de la période test; choisir le seuil sur ce même historique surestime le résultat.
- **Chronologie des variables :** `past_features.py` ne prend que les matchs dont la date est strictement antérieure à celle de la rencontre, ce qui évite d'utiliser les résultats du même jour dans ces variables. En revanche, l'Elo parcourt les lignes chronologiquement et actualise les ratings un résultat à la fois; les classeurs ne fournissent que des dates, pas les heures permettant de contrôler l'ordre des matchs d'une même journée.
- **Probabilités / marché :** le ratio au prix Pinnacle peut classer les opportunités, mais aucun test de calibration, dé-vig indépendant, CLV ou prix accepté n'est publié.
- **Code / tests :** les sept fichiers Python passent une analyse de syntaxe. Aucun test automatisé, fichier de dépendances ou environnement reproductible n'a été trouvé; compatibilité avec les versions actuelles de pandas, NumPy et XGBoost non vérifiée. Le code contient notamment des usages anciens comme `np.float` et l'argument `encoding` à `read_excel`.
- **Licence / droits des données :** licence du code absente; vérifier également les conditions de réutilisation des données tennis-data.co.uk avant tout autre usage.

## Verdict

**À étudier comme piste de robustesse, pas comme stratégie rentable.** Le point le plus utile est de mesurer si les sélections restent stables lorsque l'historique d'entraînement varie légèrement. Pour Revue, comparer cet ensemble de fenêtres au modèle ATP Elo seul et au marché, avec les hyperparamètres et le seuil définis sur une période antérieure puis gelés sur une période ultérieure. Les chiffres de ROI publiés ne doivent pas être repris : la sélection du seuil et le réglage des paramètres réutilisent la période présentée comme test, et les fichiers de sortie ne sont pas livrés.

## Références examinées

Liens épinglés au commit : [notebook et résultats d'auteur](https://github.com/edouardthom/ATPBetting/blob/f0c48b9b6fb1c91aef99e3fccffd2a1f012edb79/Beating%20the%20bookmakers%20on%20tennis%20matches.ipynb), [construction des variables et fenêtres de test](https://github.com/edouardthom/ATPBetting/blob/f0c48b9b6fb1c91aef99e3fccffd2a1f012edb79/Python/main.py), [vote des fenêtres et ROI](https://github.com/edouardthom/ATPBetting/blob/f0c48b9b6fb1c91aef99e3fccffd2a1f012edb79/Python/stategy_assessment.py), [Elo](https://github.com/edouardthom/ATPBetting/blob/f0c48b9b6fb1c91aef99e3fccffd2a1f012edb79/Python/elo_features.py), [variables historiques](https://github.com/edouardthom/ATPBetting/blob/f0c48b9b6fb1c91aef99e3fccffd2a1f012edb79/Python/past_features.py) et [données livrées](https://github.com/edouardthom/ATPBetting/tree/f0c48b9b6fb1c91aef99e3fccffd2a1f012edb79/Data).

Aucun modèle n'a été entraîné et aucune cote live n'a été interrogée. L'analyse a porté sur le code, les classeurs et les sorties déjà enregistrées dans le notebook.
