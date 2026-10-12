# Revue ciblée — JeffSackmann/tennis_MatchChartingProject

**Avis : Seule source publique de tennis coup par coup ; échantillon très biaisé vers les vedettes et les fins de tournoi.**

- Source : https://github.com/JeffSackmann/tennis_MatchChartingProject
- Version examinée : [`1813a1309b7ed7ebf1c7e884b32bf675d00e4edf`](https://github.com/JeffSackmann/tennis_MatchChartingProject/tree/1813a1309b7ed7ebf1c7e884b32bf675d00e4edf) ; branche `master` ; dernier commit le 2026-09-18.
- Consultation : 2026-10-12.
- Famille : Tennis · données coup par coup ; stack : CSV.
- Priorité de recherche : **P2 recherche** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : CC BY-NC-SA 4.0 (README) — usage non commercial.

## Ce que la source permet d'établir

- 7 566 matchs masculins chartés (plus les féminins), 1 003 joueurs ; mises à jour régulières (dernier commit 18/09/2026).
- 42 % des matchs masculins impliquent l'un des 10 joueurs les plus chartés (Federer 723, Djokovic 553, Nadal 425) ; les finales représentent 16 % des matchs.
- Les autres dépôts JeffSackmann (`tennis_atp`, `tennis_wta`, `tennis_slam_pointbypoint`) ne sont pas accessibles depuis cette session (authentification demandée), comme lors de la recherche précédente.

## Limites et points à contrôler

- Les matchs sont choisis par des bénévoles : toute statistique de joueur hors vedettes repose sur peu de matchs, et un modèle entraîné dessus extrapole mal aux premiers tours.
- Licence non commerciale et partage à l'identique.

## Enseignement pour Revue

Utile pour étudier les mécanismes service/retour des meilleurs joueurs, pas comme base de modèle général de pari tennis.

**Comparaison avec le catalogue :** Complète [tennis-crystal-ball](../tennis-crystal-ball/AUDIT.md) et `REV-TCB-01` avec des données de points.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture du README et analyse de `charting-m-matches.csv` au SHA indiqué.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/JeffSackmann/tennis_MatchChartingProject/blob/1813a1309b7ed7ebf1c7e884b32bf675d00e4edf/README.md)
- [charting-m-matches.csv](https://github.com/JeffSackmann/tennis_MatchChartingProject/blob/1813a1309b7ed7ebf1c7e884b32bf675d00e4edf/charting-m-matches.csv)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
