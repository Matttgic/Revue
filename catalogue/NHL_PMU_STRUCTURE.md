# Diagnostic PMU NHL — structure privée, un seul appel supplémentaire

Branche issue de main après fusion de la PR #61. Les 575 marchés buteurs et
666 marchés joueurs non classés sur 16 événements sont le résultat précédent
communiqué par l’utilisateur, pas une nouvelle mesure de ce diagnostic.

## Exécution

Le workflow existant `nhl-player-odds-diagnostic.yml` propose le mode explicite
`pmu-private`, sélectionné par défaut sur cette branche. Ce mode exclut le diagnostic général à quatre appels. Il exécute
`outils.collecte.diagnostic_nhl_pmu_structure` avec les alias de secrets existants.
Une seule tentative HTTP PMU, première page de 30 événements NHL maximum,
sans redirection, pagination ou retry, y compris sur HTTP 429/403. Ne pas relancer
le workflow : un second lancement consommerait un nouvel appel non autorisé.

Les données API restent en mémoire. Aucun fichier brut, aucune sortie d’exception,
aucune cote, nom, ID ou valeur de seuil/horodatage n’est exporté. L’artefact ne
contient que `/tmp/nhl-pmu-structure.json`, agrégé, avec rétention d’un jour.
Il n’est pas publié au site ou commité. Sa visibilité dépend des permissions du
dépôt GitHub ; un artefact d’un dépôt public ne doit pas être considéré confidentiel.

## Classification et lecture

Les clés canoniques reconnues sont comparées exactement. Buteurs :
`ANYTIME_GOALSCORER`, `PLAYER_GOALS`, `PLAYER_TO_SCORE_2_PLUS`, `PLAYER_HATTRICK`,
`FIRST_GOALSCORER`, `LAST_GOALSCORER`. Tirs cadrés : `PLAYER_SHOTS_ON_GOAL`.
Points : `PLAYER_POINTS`. Passes : `PLAYER_ASSISTS`, `PLAYER_TO_ASSIST`.
Les règles ne signifient pas que ces marchés sont présents ; seuls les compteurs
issus d’une réponse réelle le montreront. Les fixtures de tests sont synthétiques.
`PLAYER_SHOTS`, `PLAYER_TO_SCORE_OR_ASSIST`, les marchés équipes et les autres
catégories vont dans `other`, sans déduction depuis un nom ou un libellé brut.
Pour éviter toute fuite d’un nom/ID placé dans une clé inattendue, seules les clés
d’une liste fixe sont exportées ; les inconnues sont regroupées `UNRECOGNIZED`.
Les périodes non FULL_TIME sont comptabilisées séparément, pas assimilées à un
marché match entier. Un objet marché est compté une fois par occurrence dans
la réponse ; il ne représente pas forcément un marché unique ou un joueur unique.

Chaque catégorie et clé reconnue a des compteurs de marchés et sélections valides,
prix décimaux finis > 1, seuils numériques finis (`line`), identifiants explicitement
nommés `playerId`, dates de mise à jour ISO avec fuseau (`updatedAt`, `lastUpdate`).
Les champs marché, sélection et événement sont mesurés séparément. Le compteur
complet exige les quatre champs dans la même sélection ; aucune fusion implicite,
aucun seuil buteur de 0,5 inventé, aucune extraction d’ID depuis les noms.
Les champs absents ou encodés autrement restent non vérifiés. Un ID explicite
n’est pas une association validée avec ESPN ; une date lisible ne prouve ni la
fraîcheur ni la provenance de la cote. Le coup d’envoi n’est jamais une mise à jour.
Une erreur/clé absente donne des compteurs inconnus (`null`), pas des zéros.

## Droits et périmètre

[Conditions PulseScore](https://pulsescore.net/terms), vérifiées le 13 octobre 2026,
section 5 : redistribution/sous-licence interdites sans consentement écrit préalable.
L’abonnement Pro ne démontre pas cette autorisation. Aucun prix n’est intégré au
site, aucun EV calculé, aucun modèle sportif modifié. L’accès technique et les
droits de publication restent deux validations distinctes.

## Résultat d’exécution sur cette branche

Tests complets : 940 tests Python réussis, dont sept tests dédiés à ce diagnostic.
La tentative unique de lancement via Actions a été refusée avec HTTP 403
`Resource not accessible by integration` sur l’endpoint de dispatch.
Aucun appel API PulseScore supplémentaire n’a été effectué. Les décompositions
réelles des 666 marchés restent donc inconnues ; aucun résultat synthétique
ne leur est substitué. Le workflow est prêt pour un lancement unique par un
acteur GitHub autorisé, avec le mode `pmu-private` et la référence de cette branche.
