# Revue — jalon de couverture fonctionnelle et limites réelles

## Périmètre de la livraison du 10 octobre 2026

L'évolution vise les **fonctions utilisables du site** plutôt que la simple
copie de la présentation de Clairvoyance. Notre UI, nos classements et nos
connecteurs sont du code indépendant ; la disponibilité publique du dépôt
Clairvoyance ne remplace pas la vérification de ses licences.

### 1. Scores multisports réellement observés

`outils/scoreboard_revue.py` lit des tableaux de résultats publics NHL et
ESPN. La première exécution a reçu **26 réponses sur 26** et identifié
**20 événements terminés et un en cours**. Elle conserve la date de lecture
et refuse d'appeler cela un flux continu ou une validation rétroactive de
probabilités. Les rencontres sont associées à leur identifiant, date et clubs.

### 2. Plus de marchés réellement observés

Le Match Center exploite maintenant les **marchés totaux over/under** déjà
collectés auprès des bookmakers français (prix des deux côtés et mêmes lignes).
Les prix restent horodatés. Les règles NHL relatives aux prolongations sont
signalées non vérifiées. Le comparateur de H2H/1X2 ne rapproche que des
cotes aux règles identiques et validées, avec la meilleure cote observée
pour chaque sélection et la marge brute arithmétique du bookmaker.
Ce n'est ni une détection certaine d'arbitrage ni une EV positive.

Au premier rapport enrichi : **25 matchs avec cotes**, comparés aux 9
rencontres identifiées sur le premier tableau unifié précédent.
La couverture dépend entièrement de l'arrivée des API et des calendriers.

### 3. Projections de joueurs NHL sur les matchs à venir

Revue affiche pour chaque match NHL les profils individuels observés
de joueurs des deux équipes : chances expérimentales de but, passe, point,
deux tirs ou trois tirs. Il reprend `docs/nhl-players-latest.json`,
dérivé de statistiques historiques de joueurs. **Une observation de club
n'établit pas la présence d'un joueur dans la composition officielle**
et la probabilité de marquer ne constitue pas une proposition de mise.

### 4. Scores et verrouillage multisports

`outils/prospectif_multisports_revue.py` verrouille les probabilités des
modèles Revue **20 minutes au minimum avant le coup d'envoi**. Le premier
registre a **36 événements prospectifs** : 18 NHL, 13 NFL, 3 MLB, 2 WNBA ;
**aucun n'était encore réglé** lors de sa création. Le score de Brier
et la Log Loss sont calculés après les résultats officiels,
sans jamais réécrire les estimations initiales.

Les ligues de football ne sont pas réglées par cette chaîne binaire
(elles disposent de leur propre système 1X2/90 minutes) ; une égalité NFL
est laissée non réglée par un modèle à deux issues.

Le tableau `docs/performance-comparateur.html` réunit les
analyses indépendantes des modèles football, Monte-Carlo/Bayes, Clairvoyance
NHL et multisports. Il n'additionne pas les bilans de populations
différentes et ne présente pas de rendement observé non vérifié.

Les journaux football et ensemble ont aussi été durcis : pour régler un
pari papier, **identifiant + heure + équipes** doivent tous correspondre
aux résultats d'origine ESPN.

### 5. Ce qui reste nécessaire

- Améliorer profondément la couverture des **cotes françaises** : 25 matchs
  couverts ne représentent pas tous les événements et marchés de France
  et les mises à jour ne sont pas vraiment temps réel.
- Vérifier les **compositions et blessures** ; en particulier les gardiens NHL
  annoncés titulaires et la disponibilité des buteurs/tireurs.
- Fournir des **statistiques football xG/xGA sous licence adaptée**, des
  données joueur avancées NBA/NFL/MLB et plusieurs saisons fiables.
- Atteindre au moins **100 observations réelles de calibration** NHL et
  un échantillon prospectif indépendant d'au moins **40 rencontres suivantes**.
- Garantir l'équivalence des prédictions finales de Clairvoyance sur des
  entrées de données parfaitement identiques ; les 44 fonctions ciblées
  vérifiées ne prouvent pas cette égalité globale.
- Valider juridiquement les règles spécifiques aux marchés et ne présenter
  comme paris éligibles que ceux qui sont autorisés en France.

## Calcul de la progression

`docs/progression-revue.json` contient une **estimation éditoriale**
à pondérations constantes. Ce pourcentage n'est **ni la proportion du code
Clairvoyance recopié**, ni un score de prédiction, ni une précision de
reproduction pixel par pixel. Il est possible d'avoir un dashboard fonctionnel
avec des modèles de recherche non calibrés.
