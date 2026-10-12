# Revue des fusions Claude — 12 octobre 2026

État examiné : [main au commit 4e46a9b](https://github.com/Matttgic/Revue/tree/4e46a9b6db62d47e3a460d2d083194b1fd902c06), après notre publication `5299ac4`. Mise à jour locale en fast-forward, aucune modification du travail fusionné.

## Travail retrouvé

Les PR [46](https://github.com/Matttgic/Revue/pull/46), [47](https://github.com/Matttgic/Revue/pull/47), [48](https://github.com/Matttgic/Revue/pull/48), [49](https://github.com/Matttgic/Revue/pull/49), [50](https://github.com/Matttgic/Revue/pull/50) et [51](https://github.com/Matttgic/Revue/pull/51) concernent la collecte et le fonctionnement du produit : plafond d’appels du radar, diagnostic par bookmaker/sport, recherche par ligue, reprise HTTP 429, rythme de collecte, Orbit Exchange en référence NHL et rapprochement des équipes inversées.

Aucune nouvelle fiche de dépôt tiers n’apparaît dans la différence entre `5299ac4` et cet état de main. Cela ne signifie pas que Claude n’a pas effectué une recherche ailleurs ou sur une branche non identifiée. Le lien de la recherche signalée par l’utilisateur a été demandé ; il reste nécessaire pour l’examiner précisément.

**Mon avis :** les changements identifiés renforcent l’acquisition et le rapprochement des cotes. Ils peuvent alimenter le futur laboratoire. Ils ne constituent pas à eux seuls une exploitation comparative des 44 dépôts ni la preuve que la référence de prix est prédictivement meilleure.

## Vérifications exécutées

```bash
python -m unittest tests.test_pulsescore_v2 tests.test_revue_engine_v2 tests.test_pulsescore_radar_six_heures tests.test_diagnostic_pulsescore tests.test_metronome tests.test_regle_decision
```

**70 tests réussis**, hors ligne. Cela valide les cas couverts par ces tests, pas la disponibilité live des fournisseurs ni la rentabilité. Les autres suites et GitHub Actions n’ont pas été relancées dans cette revue.

## Point à corriger : contrôle de liquidité incomplet

Source : [pulsescore_v2.py, lignes 199–211](https://github.com/Matttgic/Revue/blob/4e46a9b6db62d47e3a460d2d083194b1fd902c06/outils/collecte/pulsescore_v2.py#L199).

Le contrôle de liquidité ne s’exécute que si `back` est une liste non vide. Une sélection sans `back` ou avec `back=[]` passe donc le filtre. `float('nan') < 20` étant faux, une liquidité NaN passe aussi. Enfin, la liquidité du premier niveau `back` est vérifiée, tandis que la cote conservée vient de `selection['odds']`, sans vérification de correspondance avec ce niveau.

Quatre sondes hors ligne ont confirmé que `translate_event(..., 'orbit_exchange', ...)` accepte ces cas : absence de `back`, liste vide, liquidité NaN, niveau back à 1,01 avec cote `odds` différente. Ces sondes utilisent des événements de test ; elles ne démontrent pas que les données réelles enregistrées contiennent ces erreurs. Le test existant vérifie une liquidité de 5 contre 250, mais ne couvre pas ces branches.

Correction recommandée : appliquer aux sources exchange un contrat explicite imposant prix et liquidité finis sur le même niveau, avec devise connue et seuil documenté. Garder le traitement des bookmakers traditionnels distinct. Ajouter les cas absents/vides/NaN/prix incohérents aux tests. Aucun collecteur fusionné n’a été changé dans cette revue.

## Points méthodologiques à compléter

- [Le choix de référence](https://github.com/Matttgic/Revue/blob/4e46a9b6db62d47e3a460d2d083194b1fd902c06/outils/suivi/revue_engine_v2.py#L244) prend le premier bookmaker prioritaire au niveau événement, puis filtre ses marchés. Une référence présente mais inutilisable sur la ligne visée peut masquer une autre référence exploitable. À tester marché par marché.
- Le filtre NHL écarte des libellés explicitement « 60 minutes », mais l’absence de ce libellé ne prouve pas à elle seule une règle prolongation/tirs au but identique. Le test Orbit accepte un libellé générique `Moneyline` : le contrat fournisseur doit justifier cette interprétation.
- Une référence exchange n’est pas automatiquement équivalente à une référence bookmaker : spread back/lay, liquidité et fraîcheur influencent le prix. Si une stratégie était exécutée sur l’exchange, les commissions devraient aussi entrer dans le rendement ; ici Orbit sert de référence et aucun pari exchange n’est placé.

## Contribution complémentaire réalisée

Le [comparateur de probabilités](probabilites_marche/README.md) exploite maintenant Shin, le dé-vig de Revue et les enseignements sur l’identité des marchés. Il relit les cotes issues du travail de collecte, exclut les règles non couvertes et quantifie la dépendance du diagnostic à la méthode.

Le [résultat exécuté](probabilites_marche/observation-2026-10-12/RESULTATS.md) montre 13 changements de signe sur 160 comparaisons dirigées. Il fournit une première mesure concrète, avant de construire le benchmark des modèles sportifs. Les anciens dossiers, modèles, automations et journaux sont inchangés.
