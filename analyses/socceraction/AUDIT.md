# Revue ciblée — ML-KULeuven/socceraction

**Avis : Une des meilleures sources de nouvelles variables pour Revue.**

- Source demandée : https://github.com/ML-KULeuven/socceraction
- URL résolue : https://github.com/ML-KULeuven/socceraction
- Version examinée : [`93a1242d46c104889205753accaabadb00c45c6d`](https://github.com/ML-KULeuven/socceraction/tree/93a1242d46c104889205753accaabadb00c45c6d) ; branche `master`.
- Consultation : 2026-10-11.
- Famille : Football · variables événementielles ; stack : Python.
- Priorité de recherche : **P1** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **MIT** ([texte à cette version](https://github.com/ML-KULeuven/socceraction/blob/93a1242d46c104889205753accaabadb00c45c6d/LICENSE.rst)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Convertit des événements de plusieurs fournisseurs vers SPADL/atomic-SPADL ; implémente xT, VAEP et Atomic-VAEP.
- xT estime les transitions spatiales et la valeur attendue des zones ; VAEP combine variation de probabilité de marquer et de concéder.
- Le README précise que le projet n’est pas activement développé et sert principalement la reproductibilité de la recherche.

## Limites et points à contrôler

- La valeur d’une action décrit une possession ; elle n’est pas une probabilité de gagner un pari.
- En pré-match, utiliser uniquement les actions de rencontres antérieures ; entraîner aussi xT/VAEP sans les périodes évaluées.
- Couverture et droits dépendent du fournisseur de données ; références académiques présentes, expériences non reproduites ici.

## Enseignement pour Revue

Construire des moyennes historiques xT/VAEP par équipe/joueur et mesurer leur apport au-delà des xG.

**Comparaison avec le catalogue :** Ajoute une famille de variables complémentaires aux Elo, buts et xG déjà catalogués.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Formules et construction xT examinées ; aucun entraînement ou appel fournisseur exécuté.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/ML-KULeuven/socceraction/blob/93a1242d46c104889205753accaabadb00c45c6d/README.md)
- [socceraction/xthreat.py](https://github.com/ML-KULeuven/socceraction/blob/93a1242d46c104889205753accaabadb00c45c6d/socceraction/xthreat.py)
- [socceraction/vaep/formula.py](https://github.com/ML-KULeuven/socceraction/blob/93a1242d46c104889205753accaabadb00c45c6d/socceraction/vaep/formula.py)
- [socceraction/vaep/labels.py](https://github.com/ML-KULeuven/socceraction/blob/93a1242d46c104889205753accaabadb00c45c6d/socceraction/vaep/labels.py)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
