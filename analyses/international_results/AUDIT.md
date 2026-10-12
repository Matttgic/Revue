# Revue ciblée — martj42/international_results

**Avis : Base de référence pour les Elo de sélections (49 945 matchs, mise à jour au 06/10/2026) ; le score inclut la prolongation, donc il ne règle pas un pari 1N2.**

- Source : https://github.com/martj42/international_results
- Version examinée : [`d5bd6de012c87e2f325de602ae77fe2f9ab61ef3`](https://github.com/martj42/international_results/tree/d5bd6de012c87e2f325de602ae77fe2f9ab61ef3) ; branche `master` ; dernier commit le 2026-10-10.
- Consultation : 2026-10-12.
- Famille : Football international · résultats 1872-2026 ; stack : CSV.
- Priorité de recherche : **P2** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : CC0 1.0.

## Ce que la source permet d'établir

- `results.csv` : 49 945 matchs du 30/11/1872 au 06/10/2026, aucun score manquant ; `shootouts.csv`, `goalscorers.csv`, `former_names.csv`.
- Le score est « full-time including extra time, not including penalty-shootouts » : un match à élimination directe 1-1 après 90 minutes puis 2-1 après prolongation est enregistré 2-1. Un pari 1N2 se règle à 90 minutes.
- Le champ `neutral` et le pays du match permettent de modéliser l'avantage du terrain correctement.
- Les équipes portent leur nom **actuel** (ex. Irlande 1882 → Irlande du Nord) : la continuité est voulue, mais il faut l'avoir en tête pour les successions d'États.

## Limites et points à contrôler

- Le README annonce 49 459 matchs « jusqu'à 2024 » : la documentation est en retard sur les données.
- Pas d'indication de la durée (90 min ou prolongation) par match.

## Enseignement pour Revue

Utiliser pour les Elo de sélections, en marquant les matchs à élimination directe et en excluant du règlement 1N2 les scores avec prolongation possible.

**Comparaison avec le catalogue :** Ajoute la couverture football international absente du catalogue.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture du README et analyse du CSV au SHA indiqué.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/martj42/international_results/blob/d5bd6de012c87e2f325de602ae77fe2f9ab61ef3/README.md)
- [LICENSE](https://github.com/martj42/international_results/blob/d5bd6de012c87e2f325de602ae77fe2f9ab61ef3/LICENSE)
- [results.csv](https://github.com/martj42/international_results/blob/d5bd6de012c87e2f325de602ae77fe2f9ab61ef3/results.csv)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
