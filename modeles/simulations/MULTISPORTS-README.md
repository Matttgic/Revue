# Revue — Multisports Independent v0.1

**Statut : prototype exécuté avec succès ; prédictions non calibrées et rentabilité non prouvée.**

## Couverture

| Sport | Compétitions | Méthode | Situation |
|---|---|---|---|
| Football | Premier League, La Liga, Serie A, Bundesliga, Ligue 1, MLS, Ligue des champions | Elo + Poisson, 1N2 90 min et Over 2,5 | Feed ESPN confirmé |
| Basketball | NBA, WNBA, NCAA Basketball | Elo, victoire et score moyen indicatif | Feed ESPN confirmé ; NBA présaison parfois sans historique |
| Football américain | NFL, NCAA Football | Elo, victoire et score moyen indicatif | Feed ESPN confirmé |
| Baseball | MLB | Elo, victoire et score moyen indicatif | Feed ESPN confirmé |
| Hockey | NHL | Modèle original Elo + Poisson, victoire et totaux | NHL API confirmée |
| Hockey européen | SHL, Liiga, National League, Extraliga | À développer | Flux NON connecté |
| Tennis | ATP, WTA | À développer | Flux NON connecté |
| MMA | UFC | À développer | Flux NON connecté |

**Preuve d'exécution :** le workflow du 9 octobre 2026 a effectivement publié 133 rencontres et 99 probabilités issues de 14 flux sportifs répondant aux requêtes. Ces nombres sont spécifiques à la fenêtre de 3 jours et varient ensuite.

## Fichiers

- [Moteur multisports](multisports_independant.py)
- [Moteur NHL](nhl_independant.py)
- [Dashboard mobile](../../docs/multisports.html)
- [Prédictions publiées](../../docs/multisports-latest.json)
- [Tests](../../tests/test_multisports_independant.py)
- [Workflow GitHub](../../.github/workflows/multisports-independent.yml)

## Exécution

Sur GitHub Android : ouvrir Actions, puis Revue - Multisports Independent, sélectionner Run workflow ; les sorties sont publiées dans docs/multisports-latest.json. Les actualisations sont aussi programmées trois fois par jour.

Sur Python 3.12 :

    python -m unittest discover -s tests -p 'test_multisports_independant.py' -v
    python modeles/simulations/nhl_independant.py --days 3
    python modeles/simulations/multisports_independant.py --days 3

Pour 4 ligues seulement :

    python modeles/simulations/multisports_independant.py --leagues NFL,NBA,PL,NHL --days 3

## Méthodologie et transparence

- Aucune copie de code de Clairvoyance, dépôt sans licence explicite.
- Football : probabilités 1N2 et Over 2,5 sous Poisson; autres sports : Elo de victoire uniquement, sans cote du marché.
- Le pipeline ESPN a été corrigé : les requêtes multi-jours produisaient HTTP 400; les requêtes mono-date passent. Pour réduire les appels récurrents, les résultats historiques sont stockés dans un cache compact versionné ; les deux derniers jours et le futur sont actualisés.
- Aucune recommandation de mise, de combiné ou d'EV sans cotes françaises observées et validées.
- Les probabilités sont NON calibrées ; pas de ROI backtesté hors échantillon, ni validation prospective.
- En cas d'historique insuffisant, la rencontre est affichée avec probabilités absentes plutôt qu'un faux score.
- Le moteur NHL précédent n'intègre pas encore gardiens confirmés, blessures, xG; pas de props buteurs ni de données de joueurs. Idem pour les modèles des autres sports.
- L'API du fournisseur et ses conditions d'usage peuvent évoluer. Tous les paris hypothétiques doivent respecter les règles ANJ françaises.
- Le cache historique de résultats ne constitue pas une archive de cotes/éléments observables avant chaque ancien match.

## Ordre des développements après v0.1

1. Backtests point-in-time par ligue avec Brier / log loss et baseline de marché.
2. Cotes réellement disponibles chez les opérateurs agréés en France et calcul EV.
3. Variables joueur, titularisations et gardiens avec provenance et timestamps.
4. Flux autorisés pour hockey européen, ATP/WTA/UFC et modèles spécifiques à leurs marchés.
