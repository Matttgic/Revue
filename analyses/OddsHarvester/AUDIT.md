# Revue ciblée — jordantete/OddsHarvester

**Avis : Très pertinent pour étudier la collecte de cotes ; qualité temporelle à vérifier avant backtest.**

- Source demandée : https://github.com/jordantete/OddsHarvester
- URL résolue : https://github.com/jordantete/OddsHarvester
- Version examinée : [`eefcaddac2aa6462ad2e03a1bd361ea4404b364e`](https://github.com/jordantete/OddsHarvester/tree/eefcaddac2aa6462ad2e03a1bd361ea4404b364e) ; branche `master`.
- Consultation : 2026-10-11.
- Famille : Multi-sports · collecte de cotes ; stack : Python 3.12+ / Playwright.
- Priorité de recherche : **P1 sous réserve** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **MIT pour le code ; conditions OddsPortal distinctes** ([texte à cette version](https://github.com/jordantete/OddsHarvester/blob/eefcaddac2aa6462ad2e03a1bd361ea4404b364e/LICENSE.txt)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Annonce cotes historiques/prochaines, instantanés live et données communautaires ; registre explicite des sports/marchés.
- Le README signale des ambiguïtés sets/games au tennis et documente le refus de certaines lignes.
- Les timestamps d’historique restent sans offset UTC et dépendent du fuseau du navigateur. ScrapeResult distingue erreurs de navigation, de parsing, de marchés et de pages de listing.

## Limites et points à contrôler

- Un historique collecté après le match ne prouve pas que le prix était accessible au moment simulé.
- Le mode preview ne donne pas le même détail bookmaker que le mode complet ; ne pas traiter un meilleur prix agrégé comme une offre de compte.
- Archive dépassant le plafond de téléchargement retenu de 45 Mo : revue de fichiers ciblés au SHA, pas du dépôt intégral. Scraper non lancé.

## Enseignement pour Revue

Valider les triplets marché/période/ligne, conserver les erreurs et convertir explicitement les heures en UTC.

**Comparaison avec le catalogue :** Complète les audits nba-betting et sports-model sur l’intégrité des cotes ; apporte des cas concrets de marchés ambigus.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

README et trois fichiers de code ciblés lus ; aucune collecte OddsPortal effectuée.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/jordantete/OddsHarvester/blob/eefcaddac2aa6462ad2e03a1bd361ea4404b364e/README.md)
- [pyproject.toml](https://github.com/jordantete/OddsHarvester/blob/eefcaddac2aa6462ad2e03a1bd361ea4404b364e/pyproject.toml)
- [src/oddsharvester/core/scrape_result.py](https://github.com/jordantete/OddsHarvester/blob/eefcaddac2aa6462ad2e03a1bd361ea4404b364e/src/oddsharvester/core/scrape_result.py)
- [src/oddsharvester/core/sport_market_registry.py](https://github.com/jordantete/OddsHarvester/blob/eefcaddac2aa6462ad2e03a1bd361ea4404b364e/src/oddsharvester/core/sport_market_registry.py)
- [src/oddsharvester/core/match_details.py](https://github.com/jordantete/OddsHarvester/blob/eefcaddac2aa6462ad2e03a1bd361ea4404b364e/src/oddsharvester/core/match_details.py)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
