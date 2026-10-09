# REV-CLAIR-08 — Séparer règlement des paris et actualisation des ratings Elo

**Statut : À étudier — vérification de fiabilité.** Source : https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/app/services/settlement.py

## Problème observé
Dans le service FastAPI source, `settle_pending_picks` boucle sur les paris et appelle `_update_elo` pour chaque `pick.bet_type == "moneyline"`. Si plusieurs picks ML renvoient au **même événement**, Elo serait actualisé plusieurs fois, ce qui déformerait les ratings.

Le code ne suffit pas à prouver que des doublons ont existé ou que ce service historique est toujours utilisé par le moteur de production. C'est une **vulnérabilité conditionnelle** à tester.

## Règle de conception Revue
- **Un match final = une seule mise à jour Elo** même s'il a généré plusieurs tickets.
- Enregistrer `sport, event_id, finished_at, settlement_version` dans un journal unique.
- Rendre le règlement de pari idempotent ; chaque pari peut être réglé individuellement, mais la statistique sportive sous-jacente n'est actualisée qu'une fois.
- Ne jamais faire dépendre un rating du nombre de paris que l'utilisateur a pris sur ce match.
- Tester : 0, 1 et 3 picks pour le même match doivent mener au **même Elo final**; les règlements ne doivent pas se dupliquer lors d'un retry.

**Verdict :** excellent garde-fou technique transversal; aucune stratégie de gains en soi.
