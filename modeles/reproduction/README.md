# Reproduction des modèles Clairvoyance — priorité du projet

**Objectif utilisateur : reproduire fidèlement les modèles de `Purple-Wraith/clairvoyance-backend`, et non inventer des méthodes de remplacement.** La comparaison avec les performances réelles vient ensuite ; la création de nouveaux algorithmes ne compte PAS dans la reproduction.

## Règles de réalisation

1. Identifier une **fonction précise de l'original**, son chemin, sa signature, ses paramètres, ses dépendances et sa version GitHub (commit SHA).
2. Reconstruire **son comportement mathématique**, sans choisir de nouveaux poids ni modifier la logique à des fins de recherche.
3. Faire tourner la fonction de référence depuis un **checkout temporaire en lecture seule**, comparer ses sorties à entrées identiques avec notre implémentation et enregistrer les cas couverts.
4. Tant que la comparaison exacte ne passe pas, afficher **« en attente de parité »** ; ne pas annoncer le module comme fini.
5. Ensuite seulement, reproduire la **chaîne d'acquisition des données**, les associations d'équipes, la fraîcheur temporelle et les règles de marché ; contrôler les résultats sur de vrais matchs.
6. Les variantes expérimentales de Revue préexistantes restent séparées. Elles ne doivent pas augmenter le pourcentage, ni remplacer automatiquement les prédictions reproduites.
7. **CFB exclu** selon la demande utilisateur.

## Modèles dont les formules sont reproduites

Le fichier [clairvoyance_predictor.py](clairvoyance_predictor.py) reproduit les fonctions de `app/services/predictor.py` :

- **MLB** : Elo à domicile avec avantage de 35 points ; conversion des probabilités / cotes américaines ; recommandation moneyline à partir d'un écart d'au moins 3 points de probabilité. Les lanceurs sont reportés en métadonnées, **mais n'affectent pas le calcul de ce prédicteur**.
- **NHL** : Elo avec avantage de 25 points ; différence de xG% MoneyPuck multipliée par 0,3 après normalisation ; différence de taux d'arrêts des gardiens multipliée par 2 ; probabilité bornée à 5–95 % ; même condition de recommandation moneyline. Le « gardien titulaire » de ce prédicteur n'est pas confirmé : la référence prend le gardien ayant joué le plus de matchs.

**Preuve :** [rapport vérifiable](../../docs/parite-clairvoyance-predictor.json) · [43 comparaisons directes dans GitHub Actions](../../.github/workflows/parite-clairvoyance-predictor.yml). Les conditions de test utilisent de faux objets de base de données, mais appellent le **véritable algorithme de référence** extrait temporairement du checkout public. Résultats identiques pour 8 scénarios MLB, 10 NHL et 25 vérifications des fonctions auxiliaires.

La reproduction des **données réelles et de leurs droits d'utilisation**, des autres modèles, de la base de données et de l'ensemble de l'application n'est pas encore vérifiée.

## Mesure de progression

[Catalogue strict des fonctions de référence](../../docs/parite-modeles-clairvoyance.json) : **43 fonctions sur 44 (98 %) reproduites et confrontées à l'original sur des entrées de test identiques**, à la date du dernier rapport (5 220 comparaisons). Cela mesure **ce catalogue restreint**, et non 98 % du dépôt entier. Les textes explicatifs du générateur NBA ne sont volontairement pas copiés et ne sont pas compris dans les comparaisons numériques. La fonction `_generateNHLPropsLive` originale est actuellement une fonction vide : sa parité ne prouve pas l'existence d'un modèle NHL props actif. La seule entrée en attente du catalogue est `injuryImplication`, fonction essentiellement textuelle.

Les modèles reconstruits sont regroupés dans `modeles/reproduction/` ; les fonctions JS proviennent de `docs/app.html`, les préparations NBA et les prédicteurs NHL/MLB du backend Python. [Rapport JavaScript](../../docs/parite-clairvoyance-frontend.json) · [parité NBA Python](../../docs/parite-clairvoyance-nba-source.json) · [parité prédicteurs](../../docs/parite-clairvoyance-predictor.json).

**Source réelle NBA :** [30 classements ESPN injectés dans les calculs originaux de force et Elo](../../docs/clairvoyance-nba-ratings.json), sans SRS Basketball-Reference. La parité sur données réelles complètes, notamment la calibration des sorties et les données de santé, **reste non démontrée**.

Le chiffre historique de « 35 % de couverture fonctionnelle Revue » comprenait le design du site, les cotes et des **modèles inventés** : il **ne mesure pas** la fidélité de reproduction et ne doit plus être présenté comme tel.

## Licence et droits

L'accès public à un dépôt GitHub permet d'en lire le code, mais ne confère pas automatiquement le droit de le redistribuer. Nous pouvons vérifier l'identité des calculs en faisant tourner le code de référence dans un job temporaire, mais **nous ne republions pas ses fichiers source** ni les éventuels jeux de données Opta protégés. Toute demande d'intégration du code original mot pour mot nécessiterait une permission ou une licence compatible.

## Reste à reproduire

Les fonctions mathématiques principales identifiées ci-dessus ont été vérifiées sur entrées synthétiques, mais la **chaîne complète** reste à reproduire : accès licite aux mêmes données, agrégation des blessures et compositions, historiques exacts, vérification des marchés et résultats identiques sur vrais matchs. La fonction textuelle `injuryImplication` reste volontairement non copiée. Il existe des fonctions de modèle supplémentaires hors du catalogue de 44, qui devront être auditées progressivement.

Ne PAS remplacer ces fonctions par un Monte-Carlo ou Bayes librement paramétré et annoncer une reproduction : chaque implémentation doit être comparée avec sa fonction homologue de Clairvoyance.
