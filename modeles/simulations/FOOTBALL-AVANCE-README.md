# Revue — modèle football avancé, indépendant et contrôlé

**Statut : actif en mode SHADOW, non utilisé pour les sélections ni le pari papier.**
Développement du 09/10/2026. Réécriture originale inspirée d'approches statistiques classiques (forme, Elo, buts attendus, Dixon-Coles), **pas la reproduction identique d'un logiciel tiers sans licence**.

## Ce qui fonctionne maintenant

- [Moteur Python](football_avance_independant.py), [13 tests unitaires](../../tests/test_football_avance_independant.py).
- [Derniers calculs et évaluations](../../docs/football-advanced-shadow.json), réalisés automatiquement par [GitHub Actions](../../.github/workflows/multisports-independent.yml).
- Données réellement branchées aujourd'hui : résultats ESPN, Elo chronologique, buts marqués/encaissés lissés, forme cinq rencontres, léger avantage domicile, correction de Dixon-Coles pour les petits scores, match 1N2 et Over 2,5.
- Les statistiques xG, xGA et power ratings sont optionnelles et **désactivées faute d'accès aux données dont la réutilisation est autorisée**.
- Toutes les features doivent avoir une date de publication pré-match ; aucune valeur post-match ne peut rétroagir sur une ancienne évaluation.
- Les identifiants d'équipe sont les identifiants ESPN dans le JSON des scores. Aucune comparaison floue silencieuse des noms.

## Première comparaison historique réelle (score-only, le 09/10/2026 à 20h10 CEST)

| Championnat | Matchs évalués | Brier ancien | Brier candidat | Différence candidat - ancien | Verdict |
|---|---:|---:|---:|---:|---|
| La Liga | 18 | 0,59717 | 0,59453 | -0,00264 | Petit mieux sur Brier, log loss légèrement moins bon |
| MLS | 60 | 0,64232 | 0,64416 | +0,00184 | Moins bon que l'ancien |
| PL, Serie A, Bundesliga, Ligue 1, UCL | 0 | — | — | — | Historique insuffisant pour ce protocole |

Ce test court ne valide ni une stratégie ni des gains. **La version précédente reste le moteur utilisé par Engine V2/PulseScore ; le candidat avancé ne remplace rien.**

## Connecter de futurs xG et classements de force autorisés

Préparer un fichier privé `data/football_features_authorized.json` avec les champs ci-dessous, **uniquement** lorsqu'une licence, un droit d'utilisation ou une autorisation vérifiable existe. Ne pas commettre une base Opta recopiée sans droit dans le dépôt public.

```json
{
  "version": 1,
  "authorized": true,
  "permission_reference": "Identifiant du contrat/licence ou source explicitement réutilisable",
  "snapshots": [
    {
      "league": "PL",
      "team_id": "359",
      "games": 12,
      "xg_for_per90": 1.8,
      "xg_against_per90": 1.1,
      "power_rating": 80,
      "published_at": "2026-10-09T10:00:00+00:00",
      "source": "nom de la source autorisée"
    }
  ]
}
```

**Les chiffres de l'exemple sont fictifs et n'ont pas été insérés dans le système réel.** Aucun fichier de données Opta n'est actuellement présent dans Revue.

Le module exige deux équipes avec snapshots éligibles, au moins 5 matchs source, publication avant calcul et fraîcheur <=12 jours. Sinon il revient automatiquement au modèle score-only. La provenance est marquée dans chaque prévision.

Pour lancer :
```bash
python -m unittest discover -s tests -p 'test_football_avance_independant.py' -v
python modeles/simulations/football_avance_independant.py
```

## Ce qu'il manque encore par rapport à Clairvoyance

1. Les six compétitions disposant de statistiques Opta/The Analyst dans Clairvoyance (PL, Bundesliga, Liga, Serie A, MLS, Champions League) ne sont **pas** enrichies en xG dans Revue.
2. Séquences, pressing, PPDA, blessures, formations et rotations ne sont pas encore modélisés.
3. Le calcul d'Opta Power Rankings est propriétaire ; Revue ne le possède pas et n'est pas autorisé à le recréer par simple recopie des valeurs.
4. Les modèles MLB, NBA, NHL, NFL, CFB et props joueurs plus complexes du tiers ne sont pas reproduits dans leur intégralité.
5. Étude walk-forward sur saisons complètes, calibration, historique horodaté des cotes françaises, confirmation des règles de marché et mesure prospective CLV/ROI sont nécessaires pour conclure à une amélioration.

Pour les limites du dépôt source, voir [audit Clairvoyance](../../analyses/2026-10-09_Clairvoyance_Opta_modele_ecarts.md).
