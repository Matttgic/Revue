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

## Investigation après #64 — run 38345350425

Artefact agrégé du run du 13 octobre 2026 : 661 joueurs de référence,
101 rencontres, 16 événements PMU éligibles, 575 marchés ANYTIME_GOALSCORER
FULL_TIME, chacun avec une sélection. Les 575 `selection.rawName` sont présents
et normalisables, mais les 575 observations échouent avec `player_not_found`.
Les contrôles de rencontre sont donc franchis ; aucune équipe ni aucun playerId
n'est fourni dans ces sélections. La présence d'un texte normalisable n'établit
pas qu'il s'agit d'un nom de joueur. Le statut historique `structurally_observed`
ne prouve pas le contrat sémantique. Les champs de nom des marchés n'avaient pas
été observés : le run ne permet pas de confirmer où se trouve l'identité.

Le diagnostic supplémentaire `schema.identity_candidates` sépare `market` et
`selection`, avec une liste fixe de champs à observer : rawName, name, playerName,
participantName, label, title. Ce sont des candidats, pas un schéma présumé.
Pour chacun : présence, types, texte normalisable, nombre de sélections candidates,
correspondances exactes normalisées par le moteur existant, ambiguïtés et motifs
de rejet. Présence/type marché compte une fois par marché ; résultats candidats
comptent par sélection. `market_objects` et `market_selection_cardinality`
explicitent cette différence, y compris marchés vides ou malformés.
Aucun champ inconnu, nom, identifiant, cote, réponse ou extrait n'est exporté.
Les objets imbriqués ne sont pas parcourus ; une absence de résultat sur cette
liste ne permet pas de conclure à l'absence d'identité dans tout le schéma.

Chaque essai change seulement le nom candidat, en conservant les contraintes
événement et les éventuels équipe/ID de la sélection. Aucun nom n'est extrait
d'un libellé composé, aucun rapprochement approximatif ni alias n'est ajouté.
Les résultats candidats ne sont jamais utilisés comme repli du moteur actif.
Même une correspondance exacte de libellé marché reste une preuve à examiner,
particulièrement pour un marché portant plusieurs sélections ou des issues
oui/non : l'identité du joueur ne prouve pas la sémantique de chaque issue.

Prochain test : lancer manuellement `nhl-pmu-matching-validation.yml` sur la
branche de la PR avec `authorize_one_call=true`, uniquement après autorisation
explicite pour cette nouvelle tentative. La réponse unique déjà bornée alimente
les nouveaux compteurs en mémoire ; aucun second appel fournisseur n'est ajouté.
Le budget est une tentative PulseScore PMU, hors rafraîchissement public NHL/ESPN
inchangé. Ne pas rejouer le run. Examiner les agrégats, les rejets et la cardinalité
avant d'adapter le champ d'identité du moteur. Les probabilités et EV restent inchangés.

### Correction des tests CI après le run 38403506153

Les échecs `test_real_docs_if_available` et
`test_real_repo_observations_do_not_invent_covers` se reproduisent sur `main`
(e9fa742). Le radar publié à 12:18 UTC sur la base du run, puis à 13:18 UTC
sur main, porte `model_stale_or_invalid` : modèle trop ancien, zéro requête,
zéro observation. Ce statut est produit volontairement par le collecteur ;
il ne constitue pas une collecte observée. Les consommateurs refusent correctement
cette provenance. Les tests d'intégration supposaient à tort que le dernier
fichier avait toujours le statut `observed`.

Les tests vérifient désormais explicitement le rejet du radar non observé,
l'absence de contribution aux couvertures et le maintien des assertions sur les
radars observés. Deux tests synthétiques supplémentaires exigent le rejet des
statuts `model_stale_or_invalid`, `no_api_key` et inconnu, même avec des cotes
synthétiques présentes. Aucun contrôle de production ni fichier de cotes n'est
modifié pour rendre un radar invalide acceptable. La branche est synchronisée
avec main pour exécuter ces contrôles sur les données actuelles. Aucun appel
PulseScore supplémentaire n'est réalisé.
