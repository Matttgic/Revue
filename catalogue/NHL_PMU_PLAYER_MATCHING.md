# Correspondance des buteurs PMU avec la base NHL

## Périmètre livré

Moteur indépendant `outils.collecte.nhl_player_matching`, sans accès réseau,
clé, prix ou modèle sportif. Seuls PMU, `ANYTIME_GOALSCORER` et `FULL_TIME` sont
admis. Il réutilise la table d’équipes NHL et le parseur de dates existants,
les profils ESPN `nhl-players-latest.json` et les rencontres `nhl-model-latest.json`.
Les profils ne prouvent pas l’alignement d’un joueur pour un match.

Le moteur compare le domicile et l’extérieur exactement après normalisation des
noms officiels/codes équipes. Il exige une date avec fuseau et un horaire dans
une tolérance explicite de 15 minutes. Aucun rapprochement sur le seul jour ou
le seul nom ; aucune inversion domicile/extérieur. Plusieurs rencontres candidates,
même dupliquées, sont rejetées comme ambiguës.

Les accents, la casse, espaces, apostrophes et tirets sont normalisés. Le nom complet
ou un alias validé doit correspondre exactement. Aucune distance floue, correction
orthographique, suppression de suffixe ou interprétation automatique d’initiales.
Les variantes non triviales sont des alias explicitement fournis par ID ESPN ;
aucun dictionnaire d’alias réel n’a été inventé. Le joueur doit appartenir à l’une
des équipes du match et avoir `current_team_observed=true`. Une équipe fournisseur
explicite doit également correspondre. Son absence n’autorise une association
que si le nom est unique dans les deux effectifs.

Les tables de correspondance PMU→ESPN (joueurs) et PMU→NHL (matchs) sont des entrées
facultatives **à valider indépendamment**. Les égalités numériques entre espaces
d’identifiants ne sont jamais utilisées. Un lien joueur validé peut lever un
homonyme mais ne peut contredire un nom, une équipe ou le contexte du match.
Un lien match contradictoire entraîne un rejet. Un identifiant PMU inconnu n’est
pas un lien vérifié ; seul le contexte exact peut alors permettre l’association.
Les doublons d’ID ESPN dans la base entraînent un rejet, sans fusion silencieuse.

## Diagnostic privé prêt, sans nouvel appel API

`outils.collecte.diagnostic_nhl_player_matching.summarize` accepte une réponse
PMU autorisée déjà en mémoire et produit uniquement nombres de sélections,
correspondances réussies, ambiguës et impossibles, motifs fixes, marchés exclus
et taux de correspondance. Aucun nom, ID, prix, seuil ou réponse brute en sortie.
Le moteur retourne des IDs uniquement en mémoire au diagnostic, qui ne les exporte
pas. Il n’enregistre aucun lien réel ou donnée fournisseur dans le dépôt.

Un point d’entrée hors ligne accepte le JSON sur stdin pour un futur runner privé
avec les références locales ; il ne comporte aucune requête HTTP ni accès aux
secrets et n’est branché à aucune collecte automatique. Ne pas conserver le flux
brut dans les logs ou artefacts. Le contrat initial lit `event.home`, `away`,
`startTime`, `eventId` et les sélections `rawName`, `team`, `playerId`, sans
extraction depuis des libellés composites. Ces champs doivent être confirmés sur
une vraie réponse : le statut exporté indique que ce contrat n’est pas validé.
Les champs manquants produisent des rejets, jamais des correspondances supposées.

## Validation et limites

Batterie principale de **23 scénarios synthétiques** : **7 réussis, 4 ambiguës,
12 impossibles**. Tous les résultats attendus sont testés, y compris les rejets.
Des tests complémentaires couvrent les conflits et homonymes avec correspondance
ID vérifiée, fuseaux et tolérance horaire, entrées malformées, absence de références,
exclusion des autres marchés et non-divulgation dans le rapport agrégé.
Ces nombres ne sont pas un taux de réussite sur les sélections PMU réelles.
**Aucun appel API supplémentaire effectué.**

Pour valider sur données réelles, il manque : une réponse autorisée analysée en
mémoire dans un runner privé, confirmation du schéma exact du nom/équipe/ID joueur,
référentiels de matchs et effectifs à jour pour les dates observées, validation
manuelle des correspondances et des alias nécessaires, vérification des tables
d’IDs si utilisées. La disponibilité/alignement et les règles de règlement du
marché restent distincts de l’identité. Les plafonds d’appel précédents ne sont
pas réinitialisés par ce travail : aucune collecte supplémentaire n’est lancée.

Les [conditions PulseScore](https://pulsescore.net/terms), vérifiées dans le travail
précédent, demandent un consentement écrit avant redistribution. Aucun droit de
publication fournisseur n’est établi ici. Aucun prix intégré au site, aucun EV,
aucun changement de modèle sportif.
