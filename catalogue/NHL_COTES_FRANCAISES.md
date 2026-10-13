# Cotes joueurs NHL — diagnostic et conditions d’intégration

État au 13 octobre 2026, branche `feat/nhl-french-player-odds`.

## Résultat vérifié

PR #59 fusionnée et main actualisée. L’intégration équipes existante est conservée.
Aucune clé PulseScore présente dans Codespaces. Le jeton GitHub renvoie HTTP 403
sur la lecture de la liste des secrets. Les secrets ne sont ni lus ni déplacés.
Le diagnostic local a donc consommé **0 appel API**. Il ne démontre ni présence
ni absence des marchés joueurs.

| Bookmaker | Buteur | Tirs cadrés | Points | Passes |
|---|---|---|---|---|
| Betclic | Non vérifié | Non vérifié | Non vérifié | Non vérifié |
| Winamax | Non vérifié | Non vérifié | Non vérifié | Non vérifié |
| Unibet FR | Non vérifié | Non vérifié | Non vérifié | Non vérifié |
| PMU | Non vérifié | Non vérifié | Non vérifié | Non vérifié |

Le diagnostic précédent du dépôt identifiait la ligue `NHL` pour ces quatre
bookmakers. Ce constat ne prouve pas la présence de marchés joueurs.

## Outil prêt

`python -m outils.collecte.diagnostic_nhl_player_odds` réutilise les identifiants
bookmakers, l’URL, le contrôle de ligue et les alias de secrets existants.
Il appelle la première page NHL de chaque bookmaker (30 événements maximum),
soit quatre requêtes maximum, sous la limite demandée de cinq. Aucun retry,
redirection ou pagination cachée. Pas d’export de prix, noms, IDs, libellés,
réponses ou exceptions brutes. Le rapport contient uniquement les statuts,
compteurs et limites de couverture. Le schéma 2 distingue quatre compteurs
`market_count` par bookmaker : `goals`, `shots`, `points`, `assists`. Ils comptent
les objets marchés, jamais les sélections ou joueurs. Sans réponse valide, les
compteurs restent `null` ; un échantillon valide sans catégorie reconnue donne
zéro et conserve le statut `unverified`, sans conclure à une absence générale.

La classification exige `period=FULL_TIME` et une clé canonique exacte :
`ANYTIME_GOALSCORER` ou `PLAYER_GOALS` pour buteur/buts joueur,
`PLAYER_SHOTS_ON_GOAL` pour tirs cadrés, `PLAYER_POINTS` pour points,
`PLAYER_ASSISTS` ou `PLAYER_TO_ASSIST` pour passes. Ces règles s’appliquent
uniquement si la réponse contient réellement ces clés ; leur prise en charge
ne prouve pas qu’un opérateur les propose. Aucun rapprochement approximatif avec
`rawName`. `PLAYER_SHOTS`, les combinés, les périodes partielles ou inconnues
restent non vérifiés. `unverified_player_markets` compte les candidats non classés.
Le statut `category_observed` signifie seulement une catégorie reconnue dans
l’échantillon NHL, jamais une cote exploitable ou un seuil validé. Les fixtures
des tests sont synthétiques, pas des observations de production.

Workflow manuel `nhl-player-odds-diagnostic.yml` : mêmes alias de secrets Actions,
même groupe de concurrence que les collectes PulseScore pour éviter un conflit
de quota, lecture seule et artefact de diagnostic sept jours. Aucun push vers main,
aucun déclenchement sur les PR ou sur un calendrier. Un nouveau workflow manuel
doit être présent dans la branche par défaut pour être sélectionnable par GitHub ;
cette PR ne le fusionne pas automatiquement. Une absence de secret reste explicite.

## Ce qui bloque l’adaptateur et les prix publics

La documentation générale décrit `markets[]`, `canonicalMarket`, `period`,
`selections[]`, `canonicalOutcome` et `odds`. Elle ne suffit pas à démontrer
le schéma réel des joueurs NHL de ces quatre opérateurs. Aucun mapping joueur,
seuil ou règle de règlement n’est supposé. Le scanner équipes demeure inchangé.

Les [conditions PulseScore](https://pulsescore.net/terms), section 5,
interdisent la redistribution des données sans consentement écrit préalable.
Un abonnement Pro ne démontre pas ce consentement. Aucun prix ne sera placé
dans les JSON publics, les artefacts ou le navigateur en son absence.

La [liste sport ANJ](https://anj.fr/index.php/les-paris-sportifs) doit être vérifiée
pour chaque compétition et type de résultat. Un bookmaker français ou un endpoint
`ice-hockey` ne suffit pas à valider tous les marchés ou leurs variantes.

## Étapes suivantes sans doublons

1. Exécuter une seule fois le diagnostic borné avec un runner autorisé disposant
   du secret existant. Distinguer erreurs d’accès, échantillon vide, marchés non
   observés et pagination non parcourue. Un nouveau diagnostic demanderait de
   comptabiliser à nouveau le budget global ; aucun automatisme de relance.
2. Si des candidats existent, examiner leur structure dans un contexte autorisé
   et privé, sans exporter les réponses. Valider joueur identifié de manière
   univoque, équipe, match et heure, marché, seuil, sens, période, prolongations,
   disponibilité et horodatage. Rejeter les homonymes et rapprochements ambigus.
3. Confirmer droits de réutilisation et support ANJ. Écrire alors un adaptateur
   indépendant du scanner équipes avec fixtures synthétiques explicites.
4. Dans la fiche NHL existante, afficher bookmaker, match, marché, seuil,
   cote et fraîcheur uniquement après validation. Garder la fréquence historique,
   la projection et la probabilité modélisée séparées. EV reste désactivée tant
   que les probabilités NHL ne sont pas calibrées et validées.

Sources techniques : [documentation officielle PulseScore](https://pulsescore.net/docs).
