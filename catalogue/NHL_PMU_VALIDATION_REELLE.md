# Validation réelle des correspondances PMU — lancement manuel uniquement

## État livré

Branche `feat/nhl-pmu-live-matching-validation`, depuis main après fusion de #63.
Le diagnostic réel **reste désactivé**. Aucun workflow fournisseur n’a été lancé,
aucun appel API PulseScore effectué pour ce travail. Sélections réelles analysées :
**non mesurées** ; taux de correspondance réel : **inconnu**. Le rapport désactivé
utilise `null` et non un taux nul pour exprimer cette absence d’observation.

## Lancement futur autorisé

Workflow `nhl-pmu-matching-validation.yml` : seul `workflow_dispatch` existe,
aucun calendrier, push, PR ou relance automatique. Le booléen
`authorize_one_call` est `false` par défaut. Même un lancement manuel sans cette
case ne collecte rien. Le programme exige aussi `--authorize-one-call`.
La clé n’est injectée que dans l’étape explicitement autorisée, via les trois
alias de secrets existants. Aucune valeur de secret n’est lue ou déplacée.

Un nouveau workflow manuel doit être présent sur la branche par défaut pour être
sélectionnable ; cette PR ne fusionne rien automatiquement. Un acteur disposant
des droits Actions devra sélectionner la référence voulue et autoriser un seul
lancement. Ne pas relancer/rejouer un run : cela consommerait un autre appel.
Les refus de dispatch HTTP 403 constatés précédemment ne sont pas contournés.

Le diagnostic consomme **une tentative PMU maximum**, y compris sur 403, 429,
redirection refusée, erreur réseau ou schéma invalide. Première page NHL seulement,
30 événements maximum ; pas de pagination, relance ou requête de détail.
La même réponse en mémoire alimente le diagnostic de structure existant et le moteur
`nhl_player_matching.py`. `has_next_page` signale une éventuelle couverture partielle.

## Actualisation des références sans toucher aux modèles

Avant la requête PulseScore autorisée, réutilisation des fonctions de collecte
NHL `download_season` et ESPN `_fetch_espn_stats`, ainsi que des correspondances de
codes équipes ESPN existantes. Elles font des requêtes publiques NHL/ESPN distinctes
du budget d’un appel **PulseScore**. Aucun calcul probabiliste, aucune écriture des
JSON publics, aucun modèle modifié.

Rencontres : fenêtre J-1 à J+14 de la saison courante. Profils : identités et équipes
des lignes ESPN courantes uniquement, sans top 8 ni statistiques/projections.
Les lignes multi-équipes ne prouvent pas une équipe courante et sont exclues.
Les doublons restants sont rejetés par le moteur. Une collecte ESPN incomplète,
un club sans profil, absence de rencontres, erreur source ou références de plus
d’une heure bloque la requête PMU. Il n’y a pas de repli sur un ancien fichier.
La fonction NHL existante accepte un calendrier partiel à partir de 28 clubs ;
une rencontre absente peut donc refléter la couverture de la référence. L’effectif
statistique ESPN ne confirme ni alignement ni participation du joueur au match.

## Schéma observé et mesures agrégées

Le diagnostic compte la présence et la validité des champs explicitement autorisés :
`home`, `away`, `startTime`, `eventId`, ainsi que les variantes de date `startDate`,
`start` (observation seulement). Dans les sélections : `rawName`, `team`, `playerId`,
`name`, `playerName`, `participantName` (les trois derniers ne sont pas utilisés
comme repli). Aucun nom de champ inconnu ou valeur arbitraire n’est exporté.

`structurally_observed` signifie que toutes les sélections éligibles ont un nom
complet non vide dans `rawName` et un contexte événement structuré valide ; ce
n’est pas une confirmation sémantique universelle. Les identités acceptées ont en
plus une correspondance exacte et unique avec les références. Les formes absentes
ou incompatibles restent `partial_or_incompatible` ; sans observation,
`not_observed`. Aucun alias supplémentaire, fuseau implicite, extraction de nom
ou égalité d’ID inter-fournisseurs n’est inventé.

Mesures : nombre de sélections, correspondances acceptées, ambiguës, impossibles,
taux sur toutes les sélections éligibles de l’échantillon, motifs fixes et groupes
`names`, `teams`, `dates`, `missing_data`, `identifiers`, `ambiguity`, `other`.
Les champs absents, équipes inconnues et dates invalides ont aussi leurs compteurs
structurels, même lorsqu’un autre motif provoque le premier rejet.
Les groupes indiquent où l’évidence échoue, pas une cause démontrée :
`player_not_found` peut relever d’une couverture ESPN incomplète plutôt que d’un
nom erroné ; une date sans match peut relever d’un calendrier incomplet.

## Confidentialité, droits et validation

Réponse et identités uniquement en mémoire. Le seul fichier produit est
`/tmp/nhl-pmu-matching-validation.json`, agrégé ; il est conservé comme artefact un
jour, sans commit, sans publication dans `docs`, sans cote ni identité fournisseur.
La visibilité d’un artefact dépend du dépôt GitHub : elle ne garantit pas un espace
confidentiel pour un dépôt public. Les données brutes n’y sont jamais placées.
Les exceptions sont réduites à des statuts fixes, sans corps ou URL source.

Les [conditions PulseScore](https://pulsescore.net/terms) consultées lors des travaux
précédents exigent un accord écrit avant redistribution. Aucun droit de publication
fournisseur n’est établi. Aucun prix ni identité n’est intégré au site, aucun EV,
aucune modification des modèles de probabilités.

Tests synthétiques : activation par défaut bloquée, double garde du workflow,
partage d’une seule réponse, refus 302/403/429 sans retry, références absentes,
partielles, anciennes ou futures, champs alternatifs non devinés, groupes de rejets,
homonymes, absence de fuite et rafraîchissement limité aux identités.
La prochaine étape est le lancement manuel autorisé, puis la lecture de ses seuls
compteurs et indicateurs avant toute modification du contrat fournisseur.
