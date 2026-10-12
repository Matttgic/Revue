# Revue ciblée — FinnedAI/sportsbookreview-scraper

**Avis : Seule archive gratuite trouvée de cotes d'ouverture et de clôture NHL ; la partie MLB est corrompue.**

- Source : https://github.com/FinnedAI/sportsbookreview-scraper
- Version examinée : [`1a820e50c6fbd0276cde073c22bfffae78930868`](https://github.com/FinnedAI/sportsbookreview-scraper/tree/1a820e50c6fbd0276cde073c22bfffae78930868) ; branche `main` ; dernier commit le 2024-07-12.
- Consultation : 2026-10-12.
- Famille : NHL / NBA / NFL / MLB · cotes historiques 2011-2021 ; stack : Python / JSON.
- Priorité de recherche : **P1 sous réserve** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : MIT.

## Ce que la source permet d'établir

- Archives JSON 2011-2021 : NHL 13 678 matchs (moneyline ouverture et clôture, total), NBA 13 903 et NFL 2 956 (clôture seulement, spreads ouverture/clôture), MLB 25 597.
- **NHL cohérent** : 0 % de sommes implicites < 1 à la clôture, marge médiane 3,2 %, 4 doublons ; la clôture prédit mieux que l'ouverture (log-loss 0,6689 contre 0,6711).
- **MLB corrompu** : 46 % des paires domicile/extérieur ont des cotes de même signe, 41 % des sommes implicites de clôture sont < 1. Exemple : 31/03/2011 « Brewers − Nationals 6-0 » ou « SFO −106 / Cardinals −205 ». Les lignes domicile et extérieur semblent appariées avec un décalage (cause non vérifiée dans le code).
- Retrait de marge à la clôture : NHL, aucune méthode ne bat nettement la multiplicative (−0,00009, erreur-type 0,00009) ; NBA, la multiplicative est la meilleure (puissance +0,00105, erreur-type 0,00036).
- Calibration NHL (clôture) : les gros favoris (> 0,70) gagnent plus que prévu (0,767 contre 0,733 ; n = 533).

## Limites et points à contrôler

- Bookmaker non identifié. Horaires d'ouverture et de clôture non datés.
- Données arrêtées en 2021.

## Enseignement pour Revue

Utilisable pour calibrer et étudier le CLV NHL 2011-2021 ; ne jamais utiliser la partie MLB telle quelle.

**Comparaison avec le catalogue :** Complète [OddsHarvester](../OddsHarvester/AUDIT.md) (collecte de cotes) et `REV-WOWZA-02` (CLV).

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Analyse des quatre fichiers JSON au SHA indiqué ; scripts dans [controles/](../../recherche/panorama-github-2026-10-12/controles/).

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/FinnedAI/sportsbookreview-scraper/blob/1a820e50c6fbd0276cde073c22bfffae78930868/README.md)
- [LICENSE.md](https://github.com/FinnedAI/sportsbookreview-scraper/blob/1a820e50c6fbd0276cde073c22bfffae78930868/LICENSE.md)
- [scrapers/sportsbookreview.py](https://github.com/FinnedAI/sportsbookreview-scraper/blob/1a820e50c6fbd0276cde073c22bfffae78930868/scrapers/sportsbookreview.py)
- [data/nhl_archive_10Y.json](https://github.com/FinnedAI/sportsbookreview-scraper/blob/1a820e50c6fbd0276cde073c22bfffae78930868/data/nhl_archive_10Y.json)
- [data/mlb_archive_10Y.json](https://github.com/FinnedAI/sportsbookreview-scraper/blob/1a820e50c6fbd0276cde073c22bfffae78930868/data/mlb_archive_10Y.json)
- [data/nba_archive_10Y.json](https://github.com/FinnedAI/sportsbookreview-scraper/blob/1a820e50c6fbd0276cde073c22bfffae78930868/data/nba_archive_10Y.json)
- [data/nfl_archive_10Y.json](https://github.com/FinnedAI/sportsbookreview-scraper/blob/1a820e50c6fbd0276cde073c22bfffae78930868/data/nfl_archive_10Y.json)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
