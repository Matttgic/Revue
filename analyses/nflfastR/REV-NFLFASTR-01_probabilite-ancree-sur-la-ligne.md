# REV-NFLFASTR-01 — Variables ancrées sur la ligne du marché

- Statut : **À étudier** (règle de contrôle, pas une stratégie).
- Sport : NFL (et toute variable dérivée d'un modèle utilisant la cote). Marché/usage : contrôle des variables pré-match.
- Source et version : [audit du dépôt](AUDIT.md).

## Idée

Certaines variables « sportives » contiennent déjà le marché. Dans nflfastR, `vegas_wp` et `vegas_home_wp` sont calculées avec `spread_line` ; les EP/WP sont produites par des modèles entraînés sur toutes les saisons (`full_train`).

## Règle proposée

Avant d'ajouter une variable à un modèle Revue, noter :

1. si elle dépend d'une cote ou d'une ligne, et de laquelle (ouverture, clôture, instant inconnu) ;
2. sur quelles saisons le modèle qui la produit a été entraîné.

Une variable qui dépend de la clôture ne peut pas servir à parier avant la clôture. Une variable produite par un modèle entraîné sur la période testée doit être recalculée avec un modèle entraîné sur le passé.

## Limites

L'instant de capture de `spread_line` dans nflverse n'a pas été vérifié dans cette revue. Si la ligne manque, nflfastR impose 1,5 point au domicile : filtrer ces matchs.
