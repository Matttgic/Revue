# Revue — mécanisme de verrouillage pré-match (Clairvoyance)

**État : implémentation indépendante ajoutée le 10 octobre 2026.**
Ce jalon vise la correspondance d'un **comportement de moteur**, pas la
copie du dépôt ni une validation des probabilités ou des performances.

## Ce que reproduit cette étape

Le script public `scripts/lock_timing.py` de Clairvoyance distingue quatre
situations en fonction des horodatages de verrouillage et de début :

| Situation | Comportement source |
| --- | --- |
| `pre` | verrouillage strictement avant le coup d'envoi |
| `during` | à partir du début, jusqu'au seuil de durée par sport |
| `after` | à partir du seuil dépassé |
| `unknown` | début ou verrouillage impossibles à déterminer |

- Le début intégré au pick a priorité sur l'appariement au calendrier.
- L'appariement utilise date locale **America/Denver**, clubs dans les deux
  sens, et heure UTC d'une fixture réellement observée.
- Les seuils documentés pour les sports couverts restent spécifiques :
  NHL/NBA/hockey européen 150 minutes, NFL 195 minutes,
  football de club 120 minutes. Ce sont des **seuils techniques source**,
  pas la preuve d'une fin de rencontre.
- Les parlay et les ligues retirées des statistiques source restent distincts.
  **CFB exclu intégralement** du périmètre Revue.

L'original compte les **verrouillages de durée inconnue** avec les pré-start
dans certains indicateurs publiés : son `settled_unknown_timing_included`
l'indique explicitement. **Revue applique en plus un garde-fou** :
seul `pre` avec un sport autorisé par son périmètre peut être certifié
pré-match. Ce garde-fou est **une différence volontaire**, jamais un
résultat de parité complète.

## Fichiers et vérification

- Moteur reconstruit : [clairvoyance_lock_timing.py](../../modeles/reproduction/clairvoyance_lock_timing.py).
- Tests unitaires : [test_clairvoyance_lock_timing.py](../../tests/test_clairvoyance_lock_timing.py).
- Vérification sur le code réel de référence : [verifier_parite_timing_clairvoyance.py](../../outils/verifier_parite_timing_clairvoyance.py).
- Action CI quotidienne / sur changement :
  [parite-clairvoyance-timing.yml](../../.github/workflows/parite-clairvoyance-timing.yml).
- À la **première action GitHub réussie** :
  [parite-clairvoyance-timing.json](../../docs/parite-clairvoyance-timing.json)
  présentera l'empreinte SHA-256 source et le nombre d'opérations comparées.

La CI exécute **1 800 cas synthétiques déterministes** (dates, normes de
ligues, verrouillages de part et d'autre du coup d'envoi, statuts inconnus,
rencontres reconnues, changements d'heure, cumul des décisions). Le code source
tiers est lu seulement sur le runner de test, sans être commité dans Revue.

Un workflow rouge signifie que la vérification **n'est pas démontrée**.
Aucun chiffre de parité, ROI ou pourcentage ne doit être annoncé sur la
seule base de l'existence de ces fichiers.

## Limites importantes

- Pas de copie de la base SQL, de l'historique de picks ou de leurs cotes.
- Aucune prétention de rentabilité ou de reprise des résultats originaux.
- Aucune opération sur un pari réel et aucune modification rétroactive des
  journaux prospectifs existants.
- L'interface Arcade et le registre de suivi actuel restent inchangés.
- Le dépôt original public n'expose pas de licence autorisant la
  redistribution de ses fichiers : Revue utilise une implémentation
  indépendante et des tests d'équivalence sur données de test.

**Priorité suivante :** comparer sur la même fenêtre les **Elo SQL
originaux, les unités xG MoneyPuck et la sélection des gardiens NHL**, puis
les probabilités réellement publiées ; à défaut d'accès source autorisé,
laisser explicitement la parité finale non démontrée.
