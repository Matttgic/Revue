# Phase 6 — Comparer les prédictions finales **observables**, pas inventer le modèle déployé

## Nouvelle chaîne

- Vérifier les sorties publiques de Clairvoyance à un commit GitHub précis
  (SHA stable), sans distribuer son code ni son historique de paris.
- Couvrir NHL / NBA / MLB et les compétitions de football sans CFB.
  Correspondance stricte des IDs, équipes, coup d'envoi et sélection.
- Verrouiller la **première observation Revue** 20 minutes minimum avant
  match dans `docs/phase6-pregame-ledger.json`. Les entrées figées ne
  sont pas réécrites par le script après un rafraîchissement de source.
- Enregistrer séparément l'horodatage du fichier original et l'instant
  où Revue l'a réellement récupéré. L'horodatage interne original
  de verrouillage du modèle ne peut pas être démontré.
- Les paris « LIVE », formats de marché non reconnus, données périmées,
  dates non concordantes et matchs NBA de présaison sont exclus.
- Si aucun modèle Revue portant sur le même résultat n'est disponible,
  conserver la source sans inventer une probabilité comparable.
- Les labels `ML` de la source ne suffisent pas à démontrer les mêmes
  règles de prolongation que Revue : les écarts restent **descriptifs**.
- Aucun historique ancien importé, aucun bilan ROI importé, aucune
  mise réelle ni appel API PulseScore payant.

## Dernière couverture publique constatée lors du développement

`docs/data.json` de la référence contenait 20 `bestBets` NHL et
aucun `bestBets` NBA/MLB/football. L'absence d'une sélection originale
publique **n'est pas** une erreur de notre modèle, mais empêche d'établir
une parité de sortie pour le sport concerné à cet instant.

## Exécution

`python -m outils.phase6_comparaison_pregame` (GitHub Actions suit le
dernier commit public original et archive localement les seuls paramètres
nécessaires à la comparaison). Chaque heure, sans appel API payant.
`python -m unittest discover -s tests -p 'test_phase6_comparaison_pregame.py' -v`.

**Reste à démontrer :** parité des paramètres SQL, des entrées originalement
déployées, des règles de marché, et des prévisions finales sur entrées
identiques. Git/GitHub conserve l'historique des commits : ce mécanisme
n'empêche pas un administrateur de réécrire l'historique Git.
