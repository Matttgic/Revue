# REV-NCSUN-04 — Registre unifié pour backtests multi-sports

**Statut : À étudier — architecture conceptualisée, code tiers non repris.**

- **Origine :** https://github.com/mkboggs92-cloud/ncsun/blob/main/README.md
- **Composant analysé :** front-end `app.js`, adaptateurs par sport `sports/`, fichiers JSON de résultats
- **Licence de la source :** non indiquée; aucune copie de code ou fichier tiers dans Revue

## Intérêt

Comparer des stratégies suppose une **structure commune de chaque pari**, indépendamment du sport. Les algorithmes prédictifs doivent être séparés de la logique de stockage, de l'affichage, de la notation des résultats et du suivi des prix.

## Proposition de contrat de données original

| Colonne logique | Sens |
|---|---|
| `strategy_id`, `model_version`, `source_id` | provenance et version |
| `event_id`, `competition`, `market`, `selection` | identification non ambiguë |
| `kickoff_at_utc`, `signal_at_utc`, `quote_at_utc` | interdiction des informations futures |
| `bookmaker`, `odds_decimal`, `stake_units` | conditions d'exécution |
| `prob_model`, `prob_market_novig`, `estimated_ev` | justification du signal |
| `status`, `result`, `profit_units`, `closing_odds` | suivi et évaluation |
| `is_paper`, `is_backtest`, `is_live` | séparation obligatoire des environnements |
| `country_eligibility`, `market_eligibility` | contrôles de disponibilité légale |

Préférer une source de vérité immuable pour le prix d'entrée et l'horodatage; conserver les corrections comme événements distincts. Un pari éliminé après publication doit rester dans l'audit.

## Contrôles transversaux

1. Pas de résultat final avant le début d'un événement.
2. Pas de feature ni cote futures utilisées par une prédiction.
3. Mise fixe et mise variable analysées séparément.
4. Dénominateur du ROI explicité; push / void traités correctement.
5. Courbe cumulée, pire drawdown, ROI par sport/marché/saison/bookmaker.
6. Segments définis avant test; signaler les multiples comparaisons.
7. Suivi prospectif indépendant du choix des paramètres.

**Verdict :** très bonne architecture de recherche à reconstruire en code original. La disponibilité des datasets et des API conditionne son déploiement.
