# Revue ciblée — fivethirtyeight/data

**Avis : Référence historique des Elo NFL/NBA/MLB/NHL/foot ; les fichiers de données liés ne sont plus accessibles.**

- Source : https://github.com/fivethirtyeight/data
- Version examinée : [`4c1ff5e3aef1816ae04af63218015066e186c147`](https://github.com/fivethirtyeight/data/tree/4c1ff5e3aef1816ae04af63218015066e186c147) ; branche `master` ; dernier commit le 2025-02-25.
- Consultation : 2026-10-12.
- Famille : Multi-sports · Elo publiés ; stack : CSV / documentation.
- Priorité de recherche : **P3** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : Données CC BY 4.0, code MIT (README).

## Ce que la source permet d'établir

- Le README indique que les prévisions sportives ne sont plus mises à jour depuis le 13 juin 2023.
- Les README `nfl-elo`, `mlb-elo`, `nhl-forecasts`, `soccer-spi` pointent vers `projects.fivethirtyeight.com/...csv`. Le 12/10/2026, ces URL redirigent (HTTP 302) vers `abcnews.com/politics` (page HTML) : les données ne sont plus servies.
- Restent dans Git : `nba-elo/nbaallelo.csv` et `nba-raptor/*` ; les colonnes `elo_pre`/`elo_post` y séparent bien avant et après match.
- Les dictionnaires de colonnes documentent des règles réutilisables : retour à la moyenne entre saisons, ajustement quarterback (NFL), lanceur partant (MLB).

## Limites et points à contrôler

- Aucune garantie que des copies tierces des CSV disparus soient fidèles.
- Prévisions jamais comparées aux cotes dans ces fichiers.

## Enseignement pour Revue

Utiliser la documentation comme spécification d'Elo par sport ; ne pas planifier de collecte sur les URL mortes.

**Comparaison avec le catalogue :** Complète `REV-CLAIR-08` (Elo actualisé une fois par match) et les Elo de Revue avec des règles de retour à la moyenne documentées.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture des README ; requêtes HTTP sur deux URL de données (redirection constatée). CSV NBA non analysé.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/fivethirtyeight/data/blob/4c1ff5e3aef1816ae04af63218015066e186c147/README.md)
- [LICENSE](https://github.com/fivethirtyeight/data/blob/4c1ff5e3aef1816ae04af63218015066e186c147/LICENSE)
- [nfl-elo/README.md](https://github.com/fivethirtyeight/data/blob/4c1ff5e3aef1816ae04af63218015066e186c147/nfl-elo/README.md)
- [mlb-elo/README.md](https://github.com/fivethirtyeight/data/blob/4c1ff5e3aef1816ae04af63218015066e186c147/mlb-elo/README.md)
- [nhl-forecasts/README.md](https://github.com/fivethirtyeight/data/blob/4c1ff5e3aef1816ae04af63218015066e186c147/nhl-forecasts/README.md)
- [soccer-spi/README.md](https://github.com/fivethirtyeight/data/blob/4c1ff5e3aef1816ae04af63218015066e186c147/soccer-spi/README.md)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
