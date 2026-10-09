# Radar NHL joueurs — profils expérimentaux

**Modèle original dans Revue**, sans code tiers recopié. Référence du développement : 2026-10-09.

## Ce qui marche

- [Modèle Python](nhl_joueurs_independant.py)
- [Tests hors réseau](../../tests/test_nhl_joueurs_independant.py)
- [Fichier JSON réellement généré](../../docs/nhl-players-latest.json)
- [Page adaptée au smartphone](../../docs/nhl-joueurs.html)
- Mise à jour via [workflow multisports](../../.github/workflows/multisports-independent.yml)

Après les échecs HTTP 403 du site statistique NHL sur les runners GitHub, la source a été remplacée par le service **ESPN public statistics/byathlete**, qui fournit des nombres par joueur. Les données sont demandées avec la saison **régulière** (seasontype=2) et les saisons ESPN précédentes/courantes.

**Vérification réelle :** le 9 octobre 2026, GitHub Actions a récupéré 304 lignes de joueurs filtrées de la saison 2025-26 et 545 lignes de la saison 2026-27 pour les équipes concernées, et produit **224 profils présentés dans 32 équipes**.

## Variables et méthodes

Moyenne des buts, passes, points et tirs par match, régularisée vers le rendement de la saison précédente (équivalent à 16 matchs de priorité). Lorsque la saison précédente comporte moins de 18 rencontres dans les données, une valeur basse de référence est utilisée ; la source est alors signalée dans le nombre de matchs historiques.

Les probabilités dérivées de Poisson couvrent :

- Buteur (au moins 1 but)
- Passeur (au moins 1 passe)
- Joueur à 1+ point
- 2+ / 3+ / 4+ tirs cadrés (le modèle suppose le nombre de tirs enregistré par ESPN comparable au marché, à vérifier bookmaker par bookmaker)

L'ordre par équipe favorise les joueurs observés statistiquement cette saison et ne considère pas un transfert historique comme une preuve que le joueur est toujours dans la même équipe.

## Limites critiques

1. Aucun **alignement confirmé**, rôle de ligne, power play, suspension, blessure, ni minutes garanties : **ne pas utiliser ce radar seul pour miser**.
2. Les statistiques agrégées ne reflètent pas les derniers 5/10 matchs ni l'opposition, et le Poisson indépendant par métrique peut être mal calibré. La probabilité de point ne doit pas être combinée aveuglément aux probabilités de but/passe du même joueur.
3. Aucun EV, cote bookmaker français, ni marché opérateur vérifié.
4. Les modèles n'ont pas été calibrés prospectivement sur résultats de props ; aucun ROI démontré.
5. Une association d'équipe présente seulement la saison passée reste **historique non vérifiée**, jamais confirmée.
6. Les conditions d'utilisation et les taux limites des API doivent être respectés, tout particulièrement pour réutilisation commerciale.

## Priorités à venir

Vérification par rencontre des compositions/gardiens, saisons et stats par joueur, projection du temps de glace et du power play ; puis backtests par marché et confrontation aux cotes réellement accessibles en France.
