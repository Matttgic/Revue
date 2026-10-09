# Revue Engine V2 — reconstitution indépendante des fonctions de Clairvoyance

**État du 9 octobre 2026 : moteur de simulation technique opérationnel ; aucun secret de cotes configuré lors du dernier run.** 24 tests Engine V2 et 12 tests PulseScore passés sur GitHub (36 tests au total pour cette couche).

Revue est une réécriture **originale** des concepts repérés dans [Purple-Wraith/clairvoyance-backend](https://github.com/Purple-Wraith/clairvoyance-backend). Le dépôt source n'a pas de licence explicite : aucun code tiers n'a été recopié.

## Modules et fonctionnement

- [Modèles multisports](../modeles/simulations/multisports_independant.py), [NHL](../modeles/simulations/nhl_independant.py), [ATP/WTA/UFC/Liiga](../modeles/simulations/sports_individuels_et_liiga.py), [NHL joueurs](../modeles/simulations/nhl_joueurs_independant.py).
- [Engine V2](revue_engine_v2.py) : récupération de cotes réelles avec clé The Odds API v4, association des deux équipes et d'un horaire comparable ; événement rejeté si correspondance ambiguë.
- Cotes françaises possibles : Betclic FR, Winamax FR, PMU FR, NetBet FR, Unibet FR. Pinnacle : référence facultative du prix sans marge, PAS un opérateur de mise recommandé en France.
- Marchés : h2h et totals uniquement quand le modèle produit la bonne issue/ligne ; en football, le h2h doit comporter trois issues pour respecter les 90 minutes. Aucun faux prix synthétique.
- Hypothèses de filtrage EXPÉRIMENTALES : cotes 1,30 à 3,50, EV théorique au moins 4 %, probabilité entre 28 et 84 %. Aucun de ces seuils n'est validé rentable.
- Contrôle horodaté strict : quote et modèle avant le lock ; prix de moins de 50 minutes, modèle de moins de 6 heures et verrouillage au moins 20 minutes avant le match.
- Registre exclusivement PAPIER : une sélection d'une unité maximum par rencontre et maximum 25 nouvelles entrées par jour, sans bookmaker connecté et sans aucun pari d'argent réel.
- Règlement ESPN sur matchs achevés avec scores vérifiés ; NHL via scoreboard officiel. Totaux NHL sans but fictif de shootout lorsque type de prolongation vérifié.
- ROI en unités fictives **uniquement** sur des sélections avec horodatages pré-match revalidés, jamais sur des locks rétrospectifs ou inconnus.
- Interface [Engine V2](../docs/engine-v2.html) ; rapports [radar](../docs/engine-v2-latest.json) et [historique papier](../docs/engine-v2-ledger.json).

## Activation depuis Android (une fois)

Dans GitHub : dépôt Matttgic/Revue → Settings → Secrets and variables → Actions → New repository secret.

**Option recommandée si tu disposes déjà de PulseScore Pro :**

Name : **PULSESCORE_API_KEY**.

Value : votre clé PulseScore Pro personnelle. Le moteur interroge les cinq flux français documentés (Betclic, Winamax, Unibet FR, NetBet, PMU) avec le header X-Secret, uniquement via GitHub Actions. Autres noms reconnus : PULSESCORE_PRO_KEY ou PULSE_SCORE_API_KEY.

**Alternative si vous utilisez The Odds API v4 :**

Name : **THE_ODDS_API_KEY**.

Value : votre clé The Odds API v4. Autre nom reconnu : ODDS_API_KEY.

Lorsque les deux clés existent, PulseScore Pro est prioritaire. Les clés restent entièrement côté runner GitHub ; elles ne sont jamais sauvegardées dans un rapport public.

Ne coller aucune clé dans le dépôt, un fichier JSON public ou le chat. Si aucun de ces secrets n'est présent, le scanner n'invente aucune cote et publie un état disabled_no_key.

Puis ouvrir [Actions — Revue Engine V2](../.github/workflows/revue-engine-v2.yml) et sélectionner Run workflow. Trois traitements automatiques par jour sont programmés vers 00:00 / 08:00 / 16:00 UTC, après rafraîchissement des données. Les déclenchements par push de code ne consomment pas de crédits de l'API de cotes.

Pour consulter la page comme un site, GitHub Pages doit être activé sur main /docs. Cette mise en ligne n'est pas encore vérifiée.

## Radar PulseScore Pro — 36 heures et cinq bookmakers français

- API documentée : https://pulsescore.net/docs. Endpoints pré-match par bookmaker/sport, marchés normalisés MATCH_RESULT et OVER_UNDER, résultats paginés.
- Noms de flux confirmés : betclic, winamax, unibet-fr, netbet, pmu.
- Préfiltre sports : seuls les sports avec un match à venir sous 36 heures et une probabilité réellement calculée sont demandés.
- Première page des cinq bookmakers pour chaque sport actif ; seconde page uniquement si elle pourrait contenir un match utile.
- **32 appels maximum par exécution** (au plus environ 2 880 appels sur 30 jours à trois exécutions quotidiennes, hors déclenchements manuels).
- Si PulseScore n'expose pas l'heure exacte de mise à jour de la cote, Revue date **sa propre observation lors de l'appel** (et le signale comme telle) ; elle ne prétend pas connaître l'heure d'actualisation chez le bookmaker.
- La couverture dépend du plan et des événements disponibles ; le code et les tests fonctionnent, mais les appels avec clé PulseScore n'ont **pas encore été vérifiés en conditions réelles dans ce dépôt**.

## Quota maîtrisé

Le moteur n'interroge que les sports ayant des matchs futurs et des probabilités. Plafond : 14 sports par run, 2 marchés (h2h et totals), 3 runs/jour. Pour 30 jours, la borne nominale est environ **2 520 unités de facturation** si un groupe de bookmakers et deux marchés coûtent chacun un crédit ; vérifier toujours la formule effective du fournisseur. Si l'API indique moins de 150 crédits restants, les nouvelles requêtes cessent.

Source et codes bookmakers : https://the-odds-api.com/sports-odds-data/bookmaker-apis.html
Documentation REST : https://the-odds-api.com/liveapi/guides/v4/

## Différences avec Clairvoyance

La source tierce publie un bilan [engine_performance.json](https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/docs/engine_performance.json) dont la base inclut des picks effectués APRÈS le coup d'envoi et des picks aux heures de lock inconnues. **Ces gains ne sont pas repris**, car une performance hors chrono ne démontre pas un edge pré-match.

La reconstruction complète des 374 fichiers originaux n'est pas revendiquée. Les composantes non opérationnelles restent : cotes de props joueurs ; market handicaps/lignes alternatives ; gardiens confirmés/blessures; les calendriers SHL/Suisse/Extraliga ; calibration et adaptation prospective ; métriques CLV si les prix de clôture ne sont pas archivés.

Aucune sélection papier ne constitue une recommandation de mise. Les opérateurs, compétitions et marchés devront être vérifiés conformes aux règles ANJ au jour de leur éventuelle utilisation.

## Exécution

Tests : python -m unittest discover -s tests -p test_revue_engine_v2.py -v

Script : python outils/revue_engine_v2.py

Le script fonctionne aussi sans clé : il produit alors un rapport d'indisponibilité honnête et peut régler d'anciennes simulations à partir des résultats de matchs.
