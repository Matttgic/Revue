# Revue ciblée — probberechts/soccerdata

**Avis : Bonne référence de connecteurs ; normalisation utile mais provenance temporelle à renforcer.**

- Source demandée : https://github.com/probberechts/soccerdata
- URL résolue : https://github.com/probberechts/soccerdata
- Version examinée : [`e120471e424a173e83e8aeeaaf4d954ab9d38ee4`](https://github.com/probberechts/soccerdata/tree/e120471e424a173e83e8aeeaaf4d954ab9d38ee4) ; branche `master`.
- Consultation : 2026-10-11.
- Famille : Football · collecte et rapprochement ; stack : Python / pandas.
- Priorité de recherche : **P1** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **Apache-2.0, crédit MIT intégré** ([texte à cette version](https://github.com/probberechts/soccerdata/blob/e120471e424a173e83e8aeeaaf4d954ab9d38ee4/LICENSE.rst)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Connecteurs Club Elo, ESPN, FBref, Football-Data, Sofascore, SoFIFA, Understat et WhoScored annoncés ; cache local et identifiants harmonisés.
- MatchHistory lit les CSV Football-Data et adapte leur encodage selon la saison.
- Quand l’heure manque, read_games remplace Time par 12:00 avant de construire la date.

## Limites et points à contrôler

- 12:00 est une valeur de remplacement, pas une preuve d’heure réelle de coup d’envoi ; ne pas l’employer aveuglément pour rapprocher les cotes.
- Un cache de données corrigées aujourd’hui ne reconstitue pas ce qui était connu hier.
- Sites et droits fournisseurs distincts ; scrapers non exécutés, disponibilité actuelle non attestée.

## Enseignement pour Revue

Conserver l’heure originale, un indicateur heure imputée, les identifiants source et le moment de collecte.

**Comparaison avec le catalogue :** Complète les besoins de snapshots et de jointure temporelle relevés dans nba-betting et sports-model.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Connecteur MatchHistory examiné ; aucune collecte sur les sites sportifs.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.rst](https://github.com/probberechts/soccerdata/blob/e120471e424a173e83e8aeeaaf4d954ab9d38ee4/README.rst)
- [soccerdata/match_history.py](https://github.com/probberechts/soccerdata/blob/e120471e424a173e83e8aeeaaf4d954ab9d38ee4/soccerdata/match_history.py)
- [LICENSE.rst](https://github.com/probberechts/soccerdata/blob/e120471e424a173e83e8aeeaaf4d954ab9d38ee4/LICENSE.rst)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
