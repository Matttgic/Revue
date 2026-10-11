# Revue ciblée — statsbomb/open-data

**Avis : Excellente matière de recherche ; droits beaucoup plus restrictifs que le mot open ne le suggère.**

- Source demandée : https://github.com/statsbomb/open-data
- URL résolue : https://github.com/hudl/open-data
- Version examinée : [`4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`](https://github.com/hudl/open-data/tree/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb) ; branche `master`.
- Consultation : 2026-10-11.
- Famille : Football · données événementielles ; stack : JSON / PDF.
- Priorité de recherche : **P1 recherche** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **StatsBomb Public Data User Agreement, restrictions non commerciales** ([texte à cette version](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/LICENSE.pdf)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- L’URL StatsBomb redirige vers hudl/open-data à la consultation.
- Événements, compositions et données 360 pour une sélection de matchs ; liste des compétitions et saisons consultée.
- Le PDF, daté du 8 septembre 2023, interdit notamment l’exploitation commerciale des données ou analyses dérivées (§1.2.2), restreint la redistribution (§1.2.1), et demande le crédit/logo (§1.4).

## Limites et points à contrôler

- Ne pas déduire du README une licence MIT ou une autorisation commerciale.
- Échantillons de compétitions sélectionnés, pas une couverture mondiale ni une archive de cotes ; disponibilité 360 partielle.
- Les fichiers d’événements et leur intégrité n’ont pas été inspectés dans cette revue ciblée.

## Enseignement pour Revue

Étudier xT/VAEP et les schémas d’événements dans un cadre compatible avec les conditions du fournisseur.

**Comparaison avec le catalogue :** Fournit une source potentielle pour socceraction ; séparer licence du logiciel et droits des données.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

README, liste de compétitions et PDF intégral lus ; aucune donnée copiée dans Revue.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/README.md)
- [LICENSE.pdf](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/LICENSE.pdf)
- [data/competitions.json](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/data/competitions.json)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
