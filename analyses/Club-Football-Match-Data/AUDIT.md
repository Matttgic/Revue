# Revue ciblée — xgabora/Club-Football-Match-Data-2000-2025

**Avis : Plus grand jeu ouvert trouvé (238 858 matchs, 38 divisions, 2000 → 09/2026) avec cotes et Elo ; utilisable après avoir écarté les Elo postérieurs au match et les colonnes de clusters.**

- Source : https://github.com/xgabora/Club-Football-Match-Data-2000-2025
- Version examinée : [`25882a58a736daf7ece3781940eac17ae1117a66`](https://github.com/xgabora/Club-Football-Match-Data-2000-2025/tree/25882a58a736daf7ece3781940eac17ae1117a66) ; branche `main` ; dernier commit le 2026-09-06.
- Consultation : 2026-10-12.
- Famille : Football · résultats, cotes Bet365 et Elo ; stack : CSV.
- Priorité de recherche : **P1 données** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : MIT (fichier LICENSE) ; données issues de Football-Data.co.uk et ClubElo.

## Ce que la source permet d'établir

- Forme sur 3 matchs (`Form3Home`) : recalculée indépendamment, elle égale les 3 matchs **précédents** dans 99,98 % des 235 549 cas comparables. Pas de fuite.
- **Elo** : sur 149 898 matchs, `HomeElo` correspond à la photo ClubElo strictement antérieure dans 89,3 % des cas, mais à une photo **datée du jour du match ou postérieure** dans 7,9 % (médiane 0 jour, 90e centile 4 jours). L'écart entre ces deux photos suit le résultat (victoire domicile +1,67, défaite −2,78) : compatible avec l'inclusion du match.
- Les colonnes de clusters `C_*` ne prédisent rien (AUC 0,503 pour la victoire domicile, contre 0,694 pour la cote et 0,676 pour l'Elo) ; leur calcul n'est pas documenté.
- Les Elo après le 1er juin 2025 sont une « continuation provisoire » calculée par l'auteur, pas ClubElo.
- Retrait de marge (Bet365, 235 803 matchs 1N2) : toutes les méthodes battent la multiplicative ; puissance −0,00072 de log-loss (erreur-type 0,00007), additive −0,00067, Shin −0,00061. Sur les favoris à cote < 1,35 : −0,007. Sur +/-2,5 buts : gain dix fois plus faible (−0,00012).
- Meilleure cote (~17 bookmakers) contre probabilité Shin Bet365 : ROI +1,7 % au seuil EV > 5 %, IC 95 % [−0,6 ; +4,0], 32 173 paris. Non significatif et la « meilleure cote » n'est pas un prix exécutable.

## Limites et points à contrôler

- L'instant de collecte des cotes Bet365 (ouverture, veille ou clôture) n'est pas précisé.
- `MatchTime` est en « CET-1 », sans fuseau IANA.
- Le README fait la promotion d'un site payant de cotes ; non examiné.

## Enseignement pour Revue

Jeu d'essai principal pour les expériences de calibration football. Avant usage : prendre l'Elo de la photo strictement antérieure (fichier `EloRatings.csv`) et ignorer `C_*`.

**Comparaison avec le catalogue :** Complète [BeatTheBookie](../BeatTheBookie/AUDIT.md) (meilleure cote) et `REV-VCHEQUE-03` (pipeline Football-Data). Fournit la première mesure empirique Revue du choix de dé-margination.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Téléchargement des deux CSV au SHA indiqué ; scripts d'audit reproductibles dans [controles/](../../recherche/panorama-github-2026-10-12/controles/). Résultats dans `controles-numeriques.json`.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/xgabora/Club-Football-Match-Data-2000-2025/blob/25882a58a736daf7ece3781940eac17ae1117a66/README.md)
- [LICENSE](https://github.com/xgabora/Club-Football-Match-Data-2000-2025/blob/25882a58a736daf7ece3781940eac17ae1117a66/LICENSE)
- [data/Matches.csv](https://github.com/xgabora/Club-Football-Match-Data-2000-2025/blob/25882a58a736daf7ece3781940eac17ae1117a66/data/Matches.csv)
- [data/EloRatings.csv](https://github.com/xgabora/Club-Football-Match-Data-2000-2025/blob/25882a58a736daf7ece3781940eac17ae1117a66/data/EloRatings.csv)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
