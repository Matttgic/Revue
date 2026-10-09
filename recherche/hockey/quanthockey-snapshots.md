# REV-CLAIR-04 — QuantHockey et données réellement antérieures au pari

**Statut : À étudier — signal externe écarté pour l'instant par l'auteur.** Source : https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/backtest_quanthockey_signal.py

## Intérêt technique
Une statistique « bilan saison en cours » contient après coup les matchs futurs par rapport à un ancien pari. La source cherche à reconstruire l'état historique en retrouvant **le dernier commit Git antérieur à l'heure exacte du lock** d'un fichier de stats. Cela évite une fuite temporelle, à condition que le temps de disponibilité du fournisseur et le commit soient fiables.

Deux familles analysées séparément : écarts équipes (ML/spread) et attaque/défense combinée pour totals.

## Résultat documenté
Le commentaire du script référence **89 paris réglés et aucun signal QuantHockey robuste**. Dans de petites séries Liiga et SHL, certaines corrélations étaient de signe contre-intuitif ou variaient d'un snapshot à l'autre. L'auteur conserve les fichiers en affichage uniquement et attend plus d'historique.

## À tester plus tard
Collecter légalement des snapshots pré-match horodatés, dédupliquer, comparer un modèle hockey de base seul vs +statistiques de saison, faire walk-forward, vérifier signe d'effet et intervalles d'incertitude par ligue et marché. Une corrélation instable n'est pas une preuve de value.

**Verdict :** excellente méthode de qualité des données, signal **non retenu** tant qu'une validation indépendante n'est pas disponible.
