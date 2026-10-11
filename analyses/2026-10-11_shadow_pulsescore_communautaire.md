# Audit 7 jours : PulseScore vs alternatives communautaires

Périmètre : football pré-match, Betclic France, marché 1X2. Ne couvre pas Pinnacle/PS3838, Winamax, Unibet FR, ni les marchés joueurs. Ce protocole ne remplace pas le radar actuel.

## Sources

- PulseScore Pro : maximum 30 événements (une page) et un seul appel authentifié par relevé.
- [TapsHTS/betclic-api](https://github.com/TapsHTS/betclic-api), révision 5989c0936e17c98fff392dc20f5d2e8e4048c04e : client Betclic non officiel, sujet aux changements et aux conditions d'utilisation.
- [omkarcloud/flashscore-scraper](https://github.com/omkarcloud/flashscore-scraper), révision b1c54af09d893a5a56a52398f76845a111b4235e : serveur local REST, cotes et événements selon disponibilité réelle.

Une licence libre du code ne garantit pas le droit de redistribuer les données sportives. Ne pas contourner les mesures de restriction d'accès ; stopper la collecte si le fournisseur ne la permet pas.

## Exécution

Workflow : .github/workflows/community-odds-shadow.yml
- Test hors ligne à chaque PR.
- Relevé quotidien programmé du 12 au 18 octobre 2026 inclus à 09:27 UTC, une fois le workflow présent dans main.
- Lancement manuel possible depuis GitHub Actions.
- Jusqu'à 8 appels pour le détail de rencontres Betclic et 3 lectures du détail Flashscore.
- Résultats dans docs/opensource-shadow/ et artefacts GitHub Actions ; aucun secret ni corps de réponse brute dans le rapport.
- Les autres workflows, prédictions, mises fictives et pipelines existants restent inchangés.
- Après le 18 octobre, le workflow ne collecte plus rien, mais la planification GitHub déclenche encore un contrôle minimal. Il faudra supprimer le cron pour éviter les exécutions vides.

## Interprétation

Chaque relevé mesure les codes d'état, le nombre de rencontres, les fixtures appariées (équipes et heures de début ±90 minutes), les marchés 1X2 complets identiques et l'écart absolu des cotes. Flashscore est évalué sur les rencontres communes et la réussite des requêtes d'odds, pas sur une prétendue équivalence des cotes Betclic.

Une erreur ne prouve pas l'absence de couverture. Une réponse JSON valide ne prouve pas non plus que les prix sont commercialement exploitables. Les prix relevés à des instants différents ne prouvent pas l'équivalence temps réel.

## Décision

Sept relevés sont insuffisants pour justifier un changement d'API. Avant résiliation PulseScore : tester au moins 100 rencontres sur plusieurs sports et bookmakers, comparer les horaires de mise à jour, les marchés joueurs et les résultats, vérifier la légitimité de la collecte et calculer les frais d'hébergement. Les rapports portent systématiquement la mention no_replacement_proven = true.
