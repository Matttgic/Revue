# Backtest historique multisports — Brier, log loss, pas de faux ROI

**Script original :** [backtest_multisports.py](backtest_multisports.py) ; [tests](../tests/test_backtest_multisports.py) ; [résultats réels](../docs/backtests-multisports.json) ; [tableau visuel](../docs/qualite-modeles.html).

## Protocole v0.1

- Rejouer chaque rencontre dont le score final est archivé dans [l'historique ESPN](../docs/multisports-history.json) ; masquer le score du match évalué.
- Modèle entraîné sur **les rencontres commencées au moins 8 heures avant** l'heure du match cible (tampon conservateur ; pas de temps de fin officiel disponible).
- Ne pas optimiser les poids sur les matchs évalués.
- Publier l'effectif de la ligue et les matchs refusés faute d'historique.
- Scorer le Brier et la log loss. Pour le football 1N2, Brier est une **somme des trois erreurs quadratiques** ; pour les marchés à deux issues c'est le carré d'une erreur.
- Comparer au tirage uniforme : 0,25 en Brier pour deux issues ; environ 0,66667 pour 1N2. C'est un contrôle facile, **pas un bookmaker**.

## Résultats du 9 octobre 2026 (à 15:47 UTC)

| Ligue | N | Brier du modèle | Uniforme | Log loss modèle | Uniforme |
|---|---:|---:|---:|---:|---:|
| MLB | 207 | 0,24298 | 0,25 | 0,67863 | 0,69315 |
| NFL | 65 | 0,23932 | 0,25 | 0,67135 | 0,69315 |
| MLS | 91 | 0,65920 | 0,66667 | 1,08837 | 1,09861 |
| Liga | 39 | 0,61861 | 0,66667 | 1,03093 | 1,09861 |
| Premier League | 20 | 0,65960 | 0,66667 | 1,09236 | 1,09861 |
| Serie A | 20 | 0,59915 | 0,66667 | 1,00592 | 1,09861 |
| WNBA | 13 | 0,18441 | 0,25 | 0,55976 | 0,69315 |
| CFB | 8 | 0,28133 | 0,25 | 0,75649 | 0,69315 |

Les autres ligues sont dans le JSON ; sans historique suffisant, aucune statistique n'est inventée. Les effectifs très petits (8, 13, 20) ne suffisent pas à établir une amélioration stable. Les sorties sont des observations de ce petit historique, et **ne démontrent ni un edge de cote ni la rentabilité**.

## Précautions

1. L'historique ESPN sauvegardé est **tronqué** (quelques semaines, selon les ligues). Ce rapport n'est ni un backtest sur toute la saison ni une estimation fiable du futur.
2. Les dates de match n'équivalent pas à des snapshots de cotes bookmakers ; aucun résultat ne peut servir à reconstituer un ROI crédible.
3. La calibration hors échantillon et la comparaison au marché hors marge seront indispensables. Le modèle Elo/Poisson peut être structurellement biaisé et le benchmark uniforme est faible.
4. Les scores finaux de compétition doivent correspondre aux règles du pari ciblé (90 min, prolongation, tirs au but, etc.). Ce rapport mesure des issues théoriques sur résultats ESPN uniquement.

## Commande

    python -m unittest discover -s tests -p test_backtest_multisports.py -v
    python outils/backtest_multisports.py

Déclenché après chaque actualisation via [GitHub Actions](../.github/workflows/multisports-independent.yml).
