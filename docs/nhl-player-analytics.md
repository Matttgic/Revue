# Analyse NHL joueurs — implémentation indépendante

Branche : `feat/nhl-player-analytics`. Aucune logique ni donnée Outlier/Props.Cash importée.

## Parcours

`nhl-joueurs.html` conserve le radar et le thème existants. Une fiche commune propose tirs cadrés, buts, passes et points, un seuil Over demi-entier, une saison et les filtres lieu/adversaire. Le graphique et le tableau montrent les 20 dernières apparitions sélectionnées. Les fréquences L5/L10/L20 utilisent le seuil actuel, pas les lignes bookmaker historiques. Après filtres, on prend N apparitions : toute statistique manquante réduit le dénominateur, sans chercher un match plus ancien. Zéro est une observation valide. Aucun match d'équipe manqué n'est ajouté comme zéro.

Les saisons sont séparées par défaut ; le choix « Deux saisons » est explicite. Les valeurs de lieu ou d'adversaire inconnues ne satisfont pas un filtre spécifique. L'identité du joueur est l'identifiant ESPN déjà présent dans le radar, jamais une correspondance floue par nom.

## Sources réellement vérifiées

Lecture réseau du 13 octobre 2026 : endpoint public ESPN `site.web.api.espn.com/apis/common/v3/sports/hockey/nhl/athletes/{id}/gamelog?season={year}&seasontype=2`. Les noms de colonnes, et non leur position supposée, permettent de lire `goals`, `assists`, `points`, `shotsTotal`. La réponse de Cutter Gauthier (5080145), saison 2026, a fourni 76 apparitions de saison régulière. Elle contenait aussi des playoffs : le paramètre `seasontype=2` ne suffit pas. Le parseur exige le groupe annuel `Regular Season` et exclut les événements futurs ou sans résultat.

Pages publiques de contrôle : https://www.espn.com/nhl/player/gamelog/_/id/5080145/cutter-gauthier et https://www.espn.com/nhl/player/gamelog/_/id/3101/alex-ovechkin . ESPN n'est pas une API contractuelle : schéma, disponibilité et droits de réutilisation commerciale ne sont pas garantis. Pas de contournement en cas de restriction ; erreur nettoyée et données indisponibles. Le champ de tirs doit toujours être rapproché des règles du marché français avant toute comparaison aux cotes.

Le collecteur publie uniquement des observations, dates de collecte et diagnostics par saison. Deux saisons régulières sont demandées. Le workflow existant actualise les 16 joueurs les moins récemment tentés, avec deux requêtes séquentielles maximum par joueur, sans nouveau service ni dépendance Python. Les historiques non retentés restent horodatés ; une collecte échouée ne se fait pas passer pour actuelle ou complète.

## Séparation des indicateurs

- Fréquence historique : dépassements observés / valeurs connues dans l'échantillon.
- Projection : moyenne saisonnière régularisée du modèle Revue existant, indépendante des filtres historiques.
- Probabilité : Poisson expérimental existant, recalculé pour le seuil choisi, clairement non calibré.
- EV : désactivée. Ni hit rate ni projection ne sont utilisés comme probabilité validée.

Aucune clé PulseScore disponible dans l'environnement de développement ; aucun payload authentifié NHL joueurs vérifié. L'adaptateur existant `pulsescore_v2.py` refuse les props joueurs : il reste inchangé. Les cotes françaises affichent **Données indisponibles**. Il faudra vérifier un vrai payload et les identifiants, seuils, côtés, règles de règlement et horodatages avant d'ajouter un adaptateur et l'affichage. Aucun appel fournisseur depuis le navigateur, aucune clé dans les fichiers publiés. Le champ `odds` reste vide et ne constitue pas un adaptateur fonctionnel.

## Validation

```sh
python -m unittest discover -s tests -p 'test_nhl_player_history.py' -v
python -m unittest discover -s tests -p 'test_nhl_joueurs_independant.py' -v
node tests/test_nhl_player_analytics.js
```

Test Chromium facultatif avec Playwright déjà installé, sans nouvelle dépendance du site : servir `docs` sur `127.0.0.1:8765`, puis lancer `node tests/test_nhl_player_ui.cjs` avec `NODE_PATH` et `CHROMIUM_PATH` adaptés à l'installation. Il vérifie des données réelles collectées, les quatre métriques, les filtres, les seuils invalides, le mobile et une indisponibilité HTTP simulée. Tous les appels externes sont bloqués pendant ce test.

Le site utilise du JavaScript et SVG natifs, sans nouvelle bibliothèque graphique. Aucun calcul EV, conseil de mise ou disponibilité d'un joueur confirmé n'est ajouté.

## Bilan de la collecte initiale et des tests

224 joueurs sur 224 avec au moins une observation ; 16 802 lignes joueur-match, dont 1 194 pour la saison ESPN 2027 et 15 608 pour 2026. 221 collectes de deux saisons réussies et 3 partielles (HTTPError sur la saison précédente). Aucun champ métrique, lieu ou adversaire manquant dans les lignes publiées. Ce total compte les observations par joueur, pas les rencontres uniques. Il ne garantit pas une couverture exhaustive de tous les joueurs NHL : le périmètre est celui du radar existant.

Validation : 59 tests de calcul/collecte et de non-régression NHL/PulseScore réussis, plus un scénario Chromium réel (quatre métriques, filtres, seuil invalide, mobile 390 px, HTTP 503, schéma invalide et absence d'erreur JavaScript). Aucun déploiement ni fusion effectué.
