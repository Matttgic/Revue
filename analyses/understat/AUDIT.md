# Revue ciblée — amosbastian/understat

**Avis : Client minimal et à jour des points d'accès JSON d'Understat ; utile pour des xG de match, sans garantie sur les révisions.**

- Source : https://github.com/amosbastian/understat
- Version examinée : [`a86debe518690f37fb296778a6bd382b90bed6c0`](https://github.com/amosbastian/understat/tree/a86debe518690f37fb296778a6bd382b90bed6c0) ; branche `master` ; dernier commit le 2025-12-16.
- Consultation : 2026-10-12.
- Famille : Football · xG Understat ; stack : Python (asyncio).
- Priorité de recherche : **P2** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : MIT.

## Ce que la source permet d'établir

- Version 0.1.14 (décembre 2025) : les appels passent par `getLeagueData`, `getTeamData`, `getMatchData`, `getPlayerData` avec l'en-tête `X-Requested-With`.
- Le 12/10/2026, `getLeagueData/EPL/2025` répond en HTTP 200 (corps compressé).
- Six championnats couverts (EPL, Liga, Bundesliga, Serie A, Ligue 1, RFPL).

## Limites et points à contrôler

- Understat peut recalculer ses xG ; une valeur collectée aujourd'hui pour un match ancien n'est pas forcément celle disponible avant le match suivant. Archiver chaque collecte avec sa date.
- Conditions d'utilisation d'Understat non examinées.

## Enseignement pour Revue

Source xG candidate pour le modèle football avancé de Revue, avec instantanés datés.

**Comparaison avec le catalogue :** Complète `REV-BLUMMA-04` (xG) et [soccerdata](../soccerdata/AUDIT.md).

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture de `constants.py`, `utils.py`, README ; une requête HTTP réelle.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/amosbastian/understat/blob/a86debe518690f37fb296778a6bd382b90bed6c0/README.md)
- [LICENSE](https://github.com/amosbastian/understat/blob/a86debe518690f37fb296778a6bd382b90bed6c0/LICENSE)
- [understat/constants.py](https://github.com/amosbastian/understat/blob/a86debe518690f37fb296778a6bd382b90bed6c0/understat/constants.py)
- [understat/utils.py](https://github.com/amosbastian/understat/blob/a86debe518690f37fb296778a6bd382b90bed6c0/understat/utils.py)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
