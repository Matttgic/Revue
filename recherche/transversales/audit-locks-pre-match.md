# REV-CLAIR-05 — Audit anti-fuite : lock avant début du match

**Statut : À étudier (outil de contrôle, pas une stratégie de pari).** Source : https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/lock_timing.py

## Problème
Un historique de paris peut inclure des sélections enregistrées pendant ou après le match, quand son résultat partiel ou final est déjà connu. Ces entrées rendent les métriques pré-match trompeuses.

## Données source observées
- `docs/engine_performance.json` décrit 1 017 `pre-start`, 181 `known-late` et 2 614 `unknown` dans le périmètre documenté.
- Le même fichier affiche 3 816 picks en total et +965,78 unités, **mais précise inclure les picks known-late** : chiffre non utilisable pour prouver un rendement pré-match.
- `scripts/lock_timing.py` identifie `pre`, `during`, `after`, `unknown`, mais la politique décrite considère `unknown` comme inclus : **cela reste incompatible avec une certification stricte pré-match**.

## Politique plus sûre pour Revue

| Classe | Entrée principale de backtest pré-match |
|---|---|
| `pre` | oui, seulement si heure de prix / décision / événement vérifiées |
| `during` | non, catégorie live séparée |
| `after` | non |
| `unknown` | **non**, conserver séparément pour transparence |

Conserver aussi date de publication de l'information (compositions, cotes, stat joueur) et début officiel du marché; un lock antérieur au match ne garantit pas que toutes les features ont été capturées à temps.

**Mesures :** part classable, ROI sur seuls `pre`, n inconnu, n connu en retard, comparatifs strict/permissif et avertissement explicite.

**Verdict :** garde-fou prioritaire, transférable à tous les projets de backtest et suivi automatique.
