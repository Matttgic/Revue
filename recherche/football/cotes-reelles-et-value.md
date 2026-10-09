# REV-VCHEQUE-02 — Séparer probabilité prédite et cote réellement offerte

**Statut : À étudier; garde-fou de qualité des données.**

- **Origine :** https://github.com/VCheque/Football-Betting/blob/main/app.py
- **Auteur source :** VCheque, licence non spécifiée.
- **Périmètre :** tous les sports, notamment le 1N2 et les totaux.

## Pourquoi cette fiche existe

Dans le constructeur de tickets du dépôt audité, la « cote » est calculée à partir de la **même probabilité** servant à estimer la value. Avec une marge `m=5 %` appliquée de façon multiplicative :

```text
cote_synthetique = (1 - m) / probabilite_estimee
EV = probabilite_estimee * cote_synthetique - 1 = -m
```

Cette EV est **par construction** autour de -5 %, pas une opportunité décelée sur un bookmaker. Aucune comparaison de marché n'est réalisée. Il faut éviter cette confusion dans les futurs projets de Revue.

## Contrat pour un vrai signal de value

- `event_id`, `market`, `selection`, `line` identifiés.
- `p_model` issu d'un modèle préalablement calibré et évalué.
- `decimal_odds` **observée** chez un bookmaker précis, avec horodatage pré-match et droit d'utilisation.
- `p_market_novig` calculée sur les **deux/trois issues du même marché et de la même source**; noter la méthode de dé-marge.
- `EV = p_model * decimal_odds - 1`, prix réellement obtenable, pas cote théorique issue du modèle.
- Rejeter tout pari sans cotation observable; conserver les échecs API et la latence.

## Tests d'acceptation

1. La provenance d'une cote est obligatoire.
2. L'horodatage de publication précède le début du match.
3. Une cote construite à partir du modèle est explicitement rejetée comme base de EV.
4. Le modèle produit une probabilité valide entre 0 et 1.
5. Le même calcul s'applique aux paris perdants, gagnants et non retenus, pour éviter le biais de sélection.

## Suite

**Outil original créé et testé :** [validateur_cotes.py](../../outils/validateur_cotes.py) et [8 tests unitaires](../../tests/test_validateur_cotes.py). Le contrôle exige une provenance externe déclarée, un identifiant, un bookmaker et une cotation antérieure au début de l'événement. Cette vérification est **structurelle** : elle ne certifie pas l'authenticité de la source ni la conformité ANJ.

Comparer ensuite sur flux autorisés auprès d'opérateurs accessibles en France, avec précautions ANJ. Ne pas confondre probabilité d'issue et rapport espéré.
