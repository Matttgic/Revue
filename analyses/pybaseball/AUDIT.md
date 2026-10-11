# Revue ciblée — jldbc/pybaseball

**Avis : Très bonne base de recherche MLB, particulièrement pour les variables lanceur/frappeur.**

- Source demandée : https://github.com/jldbc/pybaseball
- URL résolue : https://github.com/jldbc/pybaseball
- Version examinée : [`e588989359059ba04a510cc12aefa972f0a715d6`](https://github.com/jldbc/pybaseball/tree/e588989359059ba04a510cc12aefa972f0a715d6) ; branche `master`.
- Consultation : 2026-10-11.
- Famille : MLB · Statcast et statistiques ; stack : Python / pandas.
- Priorité de recherche : **P1** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **MIT pour le code ; droits fournisseurs séparés** ([texte à cette version](https://github.com/jldbc/pybaseball/blob/e588989359059ba04a510cc12aefa972f0a715d6/LICENSE)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Accès Statcast au niveau lancer et fonctions Baseball Reference/FanGraphs ; correspondance des identifiants joueurs.
- Les requêtes Statcast sont découpées par plage de dates, mises en cache et triées par date, match, passage au bâton et lancer.
- Le README avertit explicitement que les données Statcast peuvent être corrigées même pour les anciennes saisons.

## Limites et points à contrôler

- Ne pas employer les agrégats de fin de saison pour prédire ses matchs passés.
- Les doubles programmes exigent un ordre des matchs fiable ; une date seule ne suffit pas.
- Code MIT ne donne pas les droits des fournisseurs ; accès live et couverture non testés.

## Enseignement pour Revue

Reconstituer des fenêtres antérieures de xwOBA, K-BB% et profils de lancers, avec snapshots des versions.

**Comparaison avec le catalogue :** Complète directement les idées MLB de sports_prediction_model ; ne démontre pas leur gain prédictif.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Pipeline Statcast lu ; aucune requête MLB exécutée.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/jldbc/pybaseball/blob/e588989359059ba04a510cc12aefa972f0a715d6/README.md)
- [pybaseball/statcast.py](https://github.com/jldbc/pybaseball/blob/e588989359059ba04a510cc12aefa972f0a715d6/pybaseball/statcast.py)
- [LICENSE](https://github.com/jldbc/pybaseball/blob/e588989359059ba04a510cc12aefa972f0a715d6/LICENSE)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
