# Radar NHL : historiques et qualité des données

Implémentation indépendante, sans code ni données Outlier/Props.Cash importés. Aucun modèle sportif modifié par l'amélioration de fiabilité.

## Pourquoi certains joueurs n'affichaient que quatre matchs

Le filtre initial sélectionnait uniquement 2026-27. L'instantané après fusion de la PR #58 contient treize joueurs à quatre apparitions cette saison, alors que 217 joueurs sur 224 disposent déjà d'au moins vingt apparitions sur les deux saisons collectées. Le filtre n'était pas une limite de l'API. Les petits historiques restants correspondent à des observations insuffisantes ou des saisons ESPN non accessibles ; un HTTP 404 ne prouve pas qu'un joueur n'a jamais joué.

Le choix initial est maintenant « Historique récent · saisons disponibles ». Les filtres par saison, lieu et adversaire restent explicites et communs au graphique et aux fréquences. La période réelle de L20 est affichée, y compris si elle traverse plusieurs saisons. Une recherche par nom ignore casse et accents.

## Collecte et fraîcheur

Source publique déjà utilisée par Revue : `site.web.api.espn.com/apis/common/v3/sports/hockey/nhl/athletes/{id}/gamelog?season={year}&seasontype=2`. Identifiants ESPN du radar, colonnes nommées, aucune correspondance floue. Le parseur exige la saison régulière attendue, même quand ESPN renvoie aussi des playoffs. Les événements futurs ou sans résultat sont exclus.

- À chaque passage : saison courante de tous les joueurs, avec un plafond de 256 joueurs (radar actuel : 224).
- Saison précédente : lecture initiale puis cache pendant sept jours.
- Si moins de vingt observations complètes : jusqu'à deux saisons plus anciennes, sans inclure d'autres compétitions.
- Les identifiants de rencontre dédupliquent les apparitions. Une réponse courte ou une erreur ne supprime pas les observations déjà acquises.
- `attempted_at` date la tentative ; `season_collected_at` date les lectures réussies, conservées en cas d'échec. Les archives en cache ne sont pas redatées.
- Les erreurs sont nettoyées. Un HTTP 403 ou 429 arrête les autres lectures pour ce joueur ; aucun contournement.
- Écriture atomique en JSON standard compact, un joueur par ligne. Aucun secret ni appel fournisseur depuis le navigateur.

Le workflow multisports existant s'exécute toutes les trois heures. Avant amélioration, il rafraîchissait seulement seize joueurs par passage, soit jusqu'à quatorze passages pour le radar complet. La nouvelle configuration rafraîchit le radar entier et réutilise les archives. La publication Git est limitée explicitement à main. Un déclenchement manuel sur branche archive seulement l'historique via GitHub Actions ; il ne pousse rien sur main.

Les runs automatiques [38338252482](https://github.com/Matttgic/Revue/actions/runs/38338252482) et [38338573025](https://github.com/Matttgic/Revue/actions/runs/38338573025) ont été contrôlés : étape de collecte réussie et mise à jour du fichier publiée. Les dates individuelles de seize puis seize autres joueurs confirment les rafraîchissements. Le test du workflow amélioré sur la branche est décrit dans la PR.

ESPN est une source publique sans contrat d'API : disponibilité, schéma et droits de réutilisation commerciale ne sont pas garantis.

## Indicateurs et smartphone

L5/L10/L20 prennent les N dernières apparitions après filtres et évaluent le **seuil actuel**, pas les anciennes lignes bookmaker. Une statistique absente réduit le dénominateur sans remplacement par un match plus ancien ; zéro est valide. Chaque carte affiche dépassements, nombre exploitable, taille visée, statistiques manquantes et « Échantillon incomplet » si nécessaire.

La fiabilité porte sur les **données**, jamais sur la prédiction : couverture des vingt dernières apparitions et âge des lectures sources. Seuils opérationnels : six heures pour la saison courante, trente jours pour les archives. Fraîcheur inconnue, source partielle et besoin d'actualisation restent visibles. Ces seuils ne mesurent ni calibration ni rentabilité. Un historique relu récemment peut contenir des matchs anciens : sa période est affichée.

Le graphique affiche 5/10/20 apparitions au choix, indépendamment des fenêtres L5/L10/L20. Date, adversaire, domicile/extérieur, valeurs et graduations restent lisibles avec défilement horizontal ; le tableau est accessible. Les contrôles tactiles et les cartes s'adaptent au smartphone. Le thème gaming est conservé.

Projection saisonnière et probabilité Poisson expérimentale restent séparées des fréquences et indépendantes des filtres. Aucun alignement confirmé ni EV n'est ajouté. Les cotes françaises restent « Données indisponibles » sans flux joueur PulseScore réellement vérifié.

## Bilan de la collecte réelle de développement

- 224 joueurs avec au moins une apparition ; 16 836 observations joueur-match, de 2 à 89 par joueur.
- 218/224 joueurs, soit 97,32 %, avec au moins vingt observations complètes (tirs, buts, passes, points).
- Par saison ESPN : 1 195 observations en 2027, 15 608 en 2026 et 33 en 2025.
- Gain constaté : 34 observations et un joueur supplémentaire atteignant vingt matchs ; 240 requêtes réelles, les archives déjà collectées étant réutilisées.
- Historiques inférieurs à vingt : Filip Hallander (16), William Wallinder (2), Aydar Suniev (9), Owen Michaels (5), Michael Brandsegg-Nygard (19), Trevor Connelly (6). Aucune observation manquante n'est inventée.

La proportion concerne le périmètre du radar et les saisons conservées, avant filtres ; elle ne signifie pas que tous les sous-échantillons domicile/adversaire atteignent vingt matchs.

## Tests

```sh
python -m unittest discover -s tests -p 'test_*.py'
for f in tests/*.js tests/*.cjs; do node --test "$f"; done
```

Test Chromium opt-in : servir `docs` sur `127.0.0.1:8765`, puis `RUN_NHL_BROWSER_TESTS=1 node tests/test_nhl_player_ui.cjs` avec Playwright et Chromium déjà installés (`NODE_PATH` / `CHROMIUM_PATH` si nécessaire). Le scénario vérifie le cas réel à quatre matchs, la recherche, les filtres, les graphiques 5/20 matchs, le mobile, HTTP 503 et schéma invalide. Les appels externes sont bloqués pendant ce test.
