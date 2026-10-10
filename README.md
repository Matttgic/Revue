## Phase 2 — Notre propre historique multisports (démarré le 10 octobre 2026)

Décision : **Revue repart de zéro pour les résultats et l'Elo ; l'ancien SQL privé de Clairvoyance n'est plus requis pour notre modèle indépendant.** [Tableau mobile de l'historique](docs/historique-phase2.html) · [prévisions gelées à l'heure réelle du premier run](docs/phase2-owned-ledger.json) · [Brier/Log Loss par modèle/ligue](docs/phase2-owned-performance.json) · [moteur & Elo indépendants](outils/phase2_historique_autonome.py) · [tests anti-fuite](tests/test_phase2_historique_autonome.py) · [automatisation](.github/workflows/phase2-historique-autonome.yml).

**Première exécution réelle 2026-10-10T20:39:25Z** (22h39 Paris) : **39 rencontres verrouillées dans 8 compétitions** — NFL 13, WNBA 2, MLB 3, PL 4, LaLiga 5, Serie A 7, Bundesliga 2, Ligue 1 3. **0 résultat réglé, 0 Elo historique** à la création ; ces compteurs montent uniquement après de vrais scores officiels. Chaque pronostic est gelé avec son heure, ses probabilités et ses modèles disponibles au *même instant* : modèle de base + Elo/forme/marge + Monte-Carlo/Bayes/Elo + football avancé. Aucun ancien match n'est transformé en pick pré-match.

**Elo de Revue différent de celui de Clairvoyance** : commence à **1 500**, K **24**, actualisé **une seule fois par score final ESPN vérifié depuis la création**, même si aucun pick n'existait pour ce match. Ce classement ne reconstitue pas le SQL original. Dès que chaque équipe a au moins **3 matchs finaux observés dans notre propre historique**, un nouveau modèle Elo indépendant (logistique 2 issues, **sans bonus domicile inventé**) pourra être enregistré *uniquement sur les nouveaux matchs*, sans modifier un pronostic verrouillé.

Les 10 compétitions étudiées sont NBA/WNBA/NCAAB/NFL/MLB + PL/LaLiga/Serie A/Bundesliga/Ligue 1. **NHL**, **MLS** et **UCL** ont leurs suivis spécifiques / sont exclus de ce règlement multi-sport tant que les règles des prolongations, de l'overtime ou des phases finales ne sont pas comparables ; tennis/MMA/LIIGA restent dans leurs flux spécialisés. Les sports sans historique suffisant sont affichés comme indisponibles, pas simulés.

Les scores finals sont **ESPN observé**, rapprochés strictement par identifiant, compétition, équipe et coup d'envoi. Les résultats non vérifiés, doublons contradictoires, scores prématurés et données publiées après match sont écartés. Une fois réglé, le Brier/log loss est descriptif uniquement ; **aucun ROI, EV positif ou rentabilité démontrée**, aucun pari automatique ni coût PulseScore supplémentaire. [État de fraîcheur de 17 couches](docs/etat-donnees.html).

## Phase 1 — fidélité du modèle NHL Clairvoyance (audit de source)

**Tableau accessible : [Phase 1 NHL · calculs et différences restantes](docs/phase1-nhl.html).** Contrôle horodaté : [rapport d'acceptation](docs/phase1-nhl-fidelity.json) · [comparaison des vrais noms de gardiens publiés](docs/parite-nhl-gardiens-publics.json) · [audit de mise à jour Elo depuis les paris moneyline réglés](docs/clairvoyance-elo-source-audit.json).

**Réalisé et prouvé sur les sources publiques** :
- 44/44 formules ciblées Clairvoyance vérifiées sur mêmes entrées ; 17/17 mêmes rencontres NHL et xG MoneyPuck 5v5 publics (ne prouve pas les features SQL).
- Nouvelle comparaison **original `docs/nhl_schedule.json` vs Revue ESPN**, rapprochée par deux équipes et coup d'envoi : **15/15 rencontres, 30/30 noms de gardiens identiques**, **28/30 statuts identiques** sur des instantanés non simultanés. Deux gardiens étaient « probable » dans l'ancien relevé source, puis « confirmé » dans le relevé Revue plus récent. Cela *n'assure pas* que ces gardiens ont réellement débuté.
- Logique de classement Elo originale isolée : valeur initiale 1500, **K=32**, mises à jour seulement lors du **règlement d'un pick moneyline**, et non à chaque match NHL. Tests avec arrondis et absence de fuite temporelle. Dans le journal vérifié Revue courant, **0 pari NHL moneyline vérifié** autorise une mise à jour : aucune valeur Elo SQL n'est donc inventée.
- **4 contrôles d'acceptation sur 9** satisfaits. L'audit de parité des sorties NHL observe encore **12,71 points de pourcentage d'écart moyen sur huit moneylines** ; deux jeux de données publics identiques ne garantissent pas le même Elo, le même gardien sélectionné par SQL ou le même modèle publié.

**Pas encore reproduit exactement :** l'Elo historique *privé* de Clairvoyance et son ordre de règlements SQL, ses entrées propriétaires/point-in-time, l'identité démontrée du modèle Python backend avec celui des « Best Bets » publiés, la parité des probabilités publiées, puis au moins 100 résultats NHL prospectifs pour évaluer la qualité. La base SQL n'apparaît pas dans les exports publics inspectés. **Phase 1 non terminée à 100 %**, même si les calculs et comparaisons accessibles sans autorisation sont en place. Aucune prédiction ni mise rétrospective n'est fabriquée.

**Code et CI :** [comparaison des gardiens](outils/parite_nhl_gardiens_publics.py) · [replay Elo source](outils/clairvoyance_elo_settlement_replay.py) · [critères de validation](outils/verifier_phase1_nhl.py) · [tests Elo](tests/test_clairvoyance_elo_settlement_replay.py) · [tests noms/stats](tests/test_parite_nhl_gardiens_publics.py) · [workflow automatique](.github/workflows/phase1-nhl-fidelity.yml). Aucun coût PulseScore supplémentaire.

## Mesure prospective des modèles et contrôle des cotes (10 octobre 2026)

Deux mécanismes **sans aucun crédit sportif payant supplémentaire** sont opérationnels dans [Revue](docs/index.html) :

- **[Bilan des probabilités (Brier Score / Log Loss)](docs/bilan.html)** : [rapport calculé depuis les paris fictifs pré-match verrouillés](docs/revue-model-quality-latest.json), [moteur](outils/evaluation_prospective_papier.py), [tests anti-rétroactivité](tests/test_evaluation_prospective_papier.py). À la première exécution, **6 prévisions strictement admissibles sur 6 rencontres**, Brier modèle **0,287104** contre probabilité brute bookmaker **0,308496**, Log Loss **0,768462** contre **0,815293**. Ce sont des comparaisons descriptives sur un **tout petit échantillon**, bookmaker inclut sa marge. Ne démontre aucune calibration, EV+ ni rentabilité. Les autres entrées restent en attente ou exclues par provenance/règle de marché.
- **[Couvertures mathématiques des marchés football observés](docs/couvertures-mathematiques.html)** : [dernier audit](docs/revue-crossbook-latest.json) · [calcul avec marchés complets, même ligne et même période](outils/controle_couverture_cotes.py) · [tests de refus](tests/test_controle_couverture_cotes.py). Les deux instantanés de PulseScore sont contrôlés **séparément**, sans mélanger des prix qui n'ont jamais coexisté. **0 couverture détectée** lors du premier relevé admissible. Les cotes déjà observées ne sont pas forcément encore disponibles ; ni limites de mise, ni marge garantie, ni opportunités exécutables.
- **Radar PulseScore 6h équilibré entre sports** : la file d'attente en huit appels passe maintenant d'abord sur plusieurs sports plutôt que de consommer les huit sur les deux premiers. Un test prouve une répartition **3/3/2 sur trois sports**, même plafond de huit appels. Le scanner complet garde son classement prioritaire. [Code](outils/pulsescore_v2.py) · [tests](tests/test_pulsescore_v2.py). Cela améliore la couverture *potentielle*, sans prétendre capter chaque match de tous les sports.
- [État des 16 sources suivies](docs/etat-donnees.html) · automatisation du calcul **à chaque règlement officiel horaire** via [GitHub Actions](.github/workflows/donnees-prioritaires.yml). [Tests d'interface](tests/test_arcade_v3_site.py). La couverture fonctionnelle de la reproduction du dépôt Clairvoyance reste **estimée à 62 %** : ce ne sont pas de nouvelles preuves de parité SQL ou de justesse des picks originaux.

## PulseScore Pro — radar 6 h et cotes FR observées (10 octobre 2026)

**Fonctionnel sur GitHub :** [radar mobile rétro](docs/radar-6h.html) · [relevé authentifié et horodaté](docs/pulsescore-radar-latest.json) · [scanner 8 appels](outils/pulsescore_radar_six_heures.py) · [tests anti-surconsommation](tests/test_pulsescore_radar_six_heures.py) · [planification](.github/workflows/pulsescore-radar-6h.yml). [L'accueil À jouer → Pourquoi](docs/index.html) affiche les prix observés sur les matchs appariés, et uniquement les écarts comparables quand plusieurs bookmakers donnent **la même sélection, le même marché et la même ligne**.

- **Première exécution effective PulseScore vérifiée : 8 appels / 8, 12 matchs rapprochés, 264 lignes de marchés** (NHL et MLS). Les marchés NHL avec règle de prolongation incertaine sont **visibles comme observation**, mais exclus du calcul d'écarts comparables ; aucune prétendue EV vérifiée.
- Le scanner principal est maintenu **4 fois/jour, maximum 32 appels** ; le complément recherche les événements des **6 prochaines heures** en quatre passages supplémentaires de **8 appels maximum**. **Plafond nominal en mois de 31 jours = (4×32 + 4×8)×31 = 4 960 requêtes**, *sans compter* le premier scan déclenché manuellement, les relances, les contrôles API indépendants ou toute utilisation externe de PulseScore. Les scans abandonnent leurs appels si le modèle est périmé ou si aucune clé n'est disponible.
- Les résultats sont publiés séparément du scanner complet et **n'effacent pas son tableau**. Aucune création de pari papier/argent et aucune écriture dans le journal historique. Les prix authentifiés sont des instantanés, **pas** des disponibilités bookmaker au moment de miser. La clé PulseScore reste dans les GitHub Actions Secrets.
- Le projet reprend indépendamment les méthodes du code Clairvoyance **sans** prétendre disposer de son Elo SQL privé, de son abonnement aux flux complets ni de sa calibration finale. La couverture fonctionnelle générale reste estimée à **62 %**, pas un score de parité des picks.

## Bloc données NHL : gardiens ESPN + modèles verrouillés (10/10/2026)

**Intégrations fonctionnelles livrées :** [gardiens ESPN observés](docs/nhl-espn-goalies-latest.json) · [outil de jointure strict](outils/nhl_espn_goalies.py) · [tests hors réseau](tests/test_nhl_espn_goalies.py) · [CI](.github/workflows/nhl-espn-goalies.yml) ; [prévisions NHL pré-match verrouillées](docs/nhl-frontend-prospective-ledger.json) · [Brier/LogLoss comparés](docs/nhl-frontend-prospective-performance.json) · [code du suivi](outils/nhl_frontend_tracker.py) · [tests anti-fuite](tests/test_nhl_frontend_tracker.py) · [CI](.github/workflows/nhl-frontend-prospective.yml).

- Dernière vérification : 15 matchs NHL joints à ESPN par identités d'équipes **et horaire** ; **11 statuts de gardiens « confirmed » et 19 « projected »**, relevés ESPN à cet instant, et non garanties de titulaires ayant finalement joué.
- **15 couples de probabilités Monte-Carlo / Ensemble verrouillés avant le coup d'envoi**, 0 résultat encore réglé lors de la première publication. Les scores officiels NHL seuls règleront les entrées à mesure ; les Brier/LogLoss sont strictement nuls/absents avant résultat, jamais inventés.
- Les annonces de gardiens sont montrées séparément et **ne modifient aucune probabilité déjà verrouillée**. Aucune donnée de blessure/Edge reconstruite arbitrairement ; aucune cote de bookmaker en direct garantie, aucun pari et aucune preuve de rentabilité.
- [Tableau de fraîcheur des 16 couches de données](docs/etat-donnees.html). Les 6 sources essentielles avaient toutes passé le dernier contrôle ; ce n'est pas une preuve d'équivalence complète avec le modèle original. **Couverture fonctionnelle globale toujours estimée à 62 %**, aucune réévaluation de ce pourcentage à ce stade.

# Revue Arcade V3 — à jouer, pourquoi, bilan

**Interface par défaut : [ouvrir Revue Arcade](docs/index.html).** Trois étapes sans onglets inutiles : rencontres futures vérifiées et filtrables, explications par match de l'abstention ou des modèles disponibles, puis bilan fictif fondé uniquement sur les résultats pré-match réglés. Les pages détaillées restent accessibles depuis le bas de l'accueil et le Lab.

**Preuve de fonctionnement :** [contrôle qualité automatisé](docs/arcade-v3-qa.json) · [moteur de présentation source-gated](docs/arcade-v3-data.js) · [tests sur instantanés sportifs réels](tests/test_arcade_v3_data.js) · [tests de pages, JS et sécurité](tests/test_arcade_v3_site.py) · [workflow](.github/workflows/arcade-v3-tests.yml).

Le site bloque les sources expirées, les statuts non vérifiés, les cotes historiques présentées comme actuelles, les EV non démontrées et les recommandations fabriquées. Les simulations historiques ne sont pas des mises réelles ; seules les entrées effectivement réglées et vérifiables à la date du rapport entrent dans le ROI fictif, dont le nombre évolue automatiquement. **Aucune promesse de rentabilité, aucune parité complète avec Clairvoyance. Couverture fonctionnelle estimée inchangée à 62 %.** Le statut Vercel peut être en erreur pour limite de fréquence des builds, indépendamment de la réussite des tests GitHub.

## Control Center : ancien outil technique (accessible via Lab)

- **Page mobile** : [docs/command-center.html](docs/command-center.html). Quatre onglets : matchs à venir, cotes historiques observées, journal multisport des simulations et état des sources. Recherche, filtres par sport, CSV des simulations et actualisation des fichiers existants.
- **API** : `GET /revue/control` résume la fraîcheur des fichiers (sans prétendre au statut réel des fournisseurs). `GET /revue/ledger` relit le registre papier, classe les entrées incertaines hors P&L et calcule ROI / unités fictives **uniquement sur les résultats vérifiables**.
- GitHub Pages charge en premier les deux exports vérifiés (`docs/revue-control-ledger-latest.json` et `docs/revue-control-state-latest.json`) publiés automatiquement et **sans appel API payant**. Si ces fichiers manquent, elle tente l'API puis le journal brut sans notation ni ROI. Aucun pari réel, aucune clé API exposée, aucun nouveau coût de requête sportive.
- Vérification CI : `tests/test_revue_operational.py` + `tests/test_site_arena.py`.

# Revue — Reproduction des modèles Clairvoyance

> **Mission prioritaire : reproduire fidèlement les modèles du dépôt [Purple-Wraith/clairvoyance-backend](https://github.com/Purple-Wraith/clairvoyance-backend), et non inventer des modèles de remplacement.**


### Prévisions pré-match et contrôles de source (10 octobre 2026)

- **[Écran mobile des prévisions NHL / MLB](docs/predictions-revue.html)** · [API Vercel correspondante](https://revue-api-tawny.vercel.app/revue/predictions) · [tests HTTP](tests/test_api_revue_research_predictions.py). Le service utilise la **formule backend reproduite**, des rencontres NHL appariées à leurs vrais ID ESPN et des Elo MLB calculés à partir de l'historique officiel Revue. Il ne publie que des rencontres à venir, avec zéro cote ou pari inventé. Les entrées originales Clairvoyance et leurs prédictions publiées ne sont **pas** prouvées identiques.
- La correspondance mathématique NHL a été conservée sur **18/18 jeux d'entrées réelles** grâce à la comparaison des empreintes de l'original `app/services/predictor.py`, malgré les changements de commits de données.
- Les **44/44 fonctions ciblées** sont désormais épinglées aux empreintes SHA-256 des trois fichiers réellement testés (`predictor.py`, `docs/app.html` et `scripts/clairvoyance_update.py`). Les mises à jour de données du dépôt source ne font plus apparaître artificiellement ces tests comme périmés ; une modification du code source invalide bien la vérification. [Audit JSON](docs/reproduction-exacte-audit.json) · [workflow de reproduction](.github/workflows/parite-clairvoyance-predictor.yml).

- **Audit des entrées NHL vers Clairvoyance (source 2026-10-10)** : [interface mobile](docs/nhl-source-input-gap.html) · [écarts mesurés JSON](docs/nhl-source-input-delta.json) · [moteur d'audit](outils/nhl_source_input_gap.py) · [tests](tests/test_nhl_source_input_gap.py). Comparaison des situations xG 5v5/all et des gardiens MoneyPuck/NHL Edge sur un échantillon pré-match, en gardant les Elo Revue identiques. Rapport descriptif horodaté, distinct des prévisions gelées ; la parité avec les inputs SQL originaux reste non démontrée.

\n### Reproduction du verrouillage pré-match (Clairvoyance)\n\n- [Mécanisme indépendant et limites](recherche/produit/parite-verrouillage-clairvoyance.md) · [tests de sécurité](tests/test_clairvoyance_lock_timing.py) · [comparateur avec le code original](outils/verifier_parite_timing_clairvoyance.py) · [workflow quotidien](.github/workflows/parite-clairvoyance-timing.yml).\n- Le comparateur valide les classes `pre`, `during`, `after`, `unknown`, les calendriers en heure de Denver, les sports, exclusions parlay et indicateurs agrégés sur **1 800 cas de test synthétiques** une fois la CI réussie. Aucun ancien ROI ou pick n'est reclassé automatiquement. **CFB exclu**. Revue distingue la parité du classificateur et sa propre règle plus stricte (inconnus non prouvés pré-match). La couverture éditoriale reste **62 %** jusqu'à nouvel audit.\n\n### NHL — comparaison des entrées originales (nouvelle étape)

- [Écran mobile NHL source-style](docs/nhl-backend-source-style.html) · [moteur source-style indépendant](outils/nhl_backend_source_style.py) · [tests de provenance et horodatage](tests/test_nhl_backend_source_style.py) · [Action automatique](.github/workflows/nhl-backend-source-style.yml) · [résultat JSON après action réussie](docs/nhl-backend-source-style-latest.json).
- **Vérification avec le code backend original réussie : 30/30 sorties identiques sur 15 rencontres NHL**, pour les deux hypothèses d'échelle xG, avec entrées Revue identiques. [Preuve CI JSON](docs/parite-nhl-source-style.json) · [rejouer la comparaison](outils/verifier_parite_nhl_source_style.py) · [Action quotidienne](.github/workflows/parite-nhl-source-style.yml). Cela ne prouve ni l'égalité des Elo SQL ni celle des meilleurs paris publiés par Clairvoyance.
- Le backend original utilise MoneyPuck `situation=all` et les taux d'arrêt des gardiens issus des statistiques NHL saison/type choisies ; Revue calcule **deux hypothèses d'échelle xG** (valeurs brutes 0–1, pourcentage 0–100), avec **Elo proxy Revue inchangé** et refuse de choisir arbitrairement les gardiens à égalité. Les analyses sont uniquement pré-match, avec provenance et horodatages vérifiés ; le registre figé n'est jamais modifié.
- **Ce n'est pas la parité NHL finale** : saisons et paramètres par défaut originaux différents de la saison 2026–2027 utilisée, Elo SQL non accessible, valeurs stockées SQL non vérifiées, moteur frontend des meilleurs paris potentiellement distinct. Aucun ROI ni cote inventé. **62 % de couverture fonctionnelle estimée inchangée** tant que les critères ne sont pas prouvés.

### NHL frontend : Monte-Carlo et Ensemble sur données observées (2026-10-10)

- [Page mobile](docs/nhl-frontend-observed.html) · [rapport pré-match](docs/nhl-frontend-observed-latest.json) · [générateur indépendant](outils/nhl_frontend_observed.js) · [tests de chronologie / non-invention](tests/test_nhl_frontend_observed.js) · [workflow](.github/workflows/nhl-frontend-observed.yml).
- Première exécution GitHub Actions validée : **15 matchs calculés sur 18 rencontres examinées, 25 000 simulations par match**. Id NHL contrôlé, instantanés antérieurs au coup d'envoi, Elo et bookmaker inexistants non inventés, aucun pari réel ni fictif créé.
- Le code mathématique `nhlMC` / `nhlEns` a été reconstitué et testé séparément contre la référence originale. Le branchement utilise **NHL Stats REST**, xG/60 **MoneyPuck 5v5** et gardiens historiques MoneyPuck ; les moyennes par match sont utilisées explicitement comme *proxies* de GF60. **Ce n'est pas la parité des prévisions frontend d'origine** : NHL Edge, blessures, forme, HV, titulaire confirmé, vrais coefficients de calibration et cotes restent indisponibles ou neutres. Résultats **non calibrés**, à ne pas présenter comme des paris sélectionnés.
- La CI se réexécute quotidiennement et après la mise à jour du moteur NHL de données. Elle rejette les données périmées / postérieures au cutoff, et ne modifie jamais les pronostics historiques ni les bilans. **Couverture fonctionnelle globale toujours estimée à 62 %**, jusqu'à nouvel audit pondéré.

## Priorité absolue — identité vérifiable avec Clairvoyance

**Le but n'est plus « 50 % de fonctionnalités similaires » mais une reproduction exacte, comportement par comportement et sur la même version du code original, hors CFB.**

- **API Revue désormais disponible en production sur Vercel** : [vérification /health](https://revue-api-tawny.vercel.app/health) · [routes, tests et limitations](api_revue/README.md) · [test distant public](.github/workflows/api-vercel-smoke.yml) · [correspondance vérifiée de 18 identifiants NHL ↔ ESPN](docs/parite-nhl-espn-id-map.json). Quatorze signatures GET originales déclarées sur vingt-quatre (dont trois routes de picks simulés), mais **aucune équivalence de bout en bout complète** : les réponses `/predictions/` restent désactivées faute de mêmes données. Données absentes jamais inventées.
- [**Tableau de l'identité globale**](docs/reproduction-exacte.html) · [rapport vérifiable avec l'empreinte du code source](docs/reproduction-exacte-audit.json) · [auditeur automatisé quotidien](.github/workflows/parite-exacte-clairvoyance.yml).
- La formule ne suffit pas : chaque module doit donner le **même résultat pour les mêmes données et à la même heure**, avec des contrats API, des règles de marchés et des interactions vérifiés.
- [Catalogue 44 fonctions sur 44](docs/parite-modeles-clairvoyance.json) vérifié sur la **version source en cours** par les actions GitHub. Les 44 fonctions ne représentent pas tout le frontend ni le backend.
- Le backend original comporte **24 routes FastAPI**, dont l'équivalence complète côté Revue n'est pas encore vérifiée ; son frontend principal a **2 671 918 octets** et n'est pas reproduit à l'identique. La correspondance pixel par pixel n'a pas encore été testée.
- Les données originales des matchs, blessures, gardiens, cotes et modèles ne sont **pas** démontrées identiques. Aucun pourcentage de reproduction exacte globale n'est calculable à ce stade : `null` signifie « non établi », pas « 0 % ».
- **Licence** : le dépôt public Clairvoyance ne présente pas de licence explicite. Revue reconstruit les comportements de manière indépendante et vérifie les sorties en CI sans redistribuer le code original ou les données sous droits réservés.

Les projets de recherche annexes et le site gaming Revue sont conservés, mais **ils ne comptent jamais comme reproduction de Clairvoyance**.


- **Scores ESPN/NHL et comparaison de modèles, sans données inventées** : [Match Center complet](docs/match-center.html) · [derniers scores observés](docs/scoreboard-revue-latest.json) · [registre multisports figé avant les matchs](docs/multisport-prospective-ledger.json) · [Brier et Log Loss](docs/multisport-prospective-performance.json) · [comparateur de performances](docs/performance-comparateur.html) · [périmètre et limites du jalon fonctionnel](recherche/produit/jalon-50-couverture-fonctionnelle.md). Scores officiels horodatés, prix comparés seulement sur des règles identiques, marchés totaux réels et profils NHL historiques, sans prétendre connaître les compositions du jour.
- **Match Center Revue (interface gaming originale)** : [centre des matchs mobile](docs/match-center.html) · [rapport sur 72 h](docs/match-center-latest.json) · [workflow horaire](.github/workflows/match-center-revue.yml) · [méthode et écarts vs Clairvoyance](recherche/produit/match-center-revue-vs-clairvoyance.md). Les rencontres de plusieurs sports sont rapprochées par compétition, identifiant, adversaires et heure ; le détail rassemble plusieurs modèles et, lorsqu'elles existent, des cotes françaises réellement observées. Première exécution : **126 matchs / 14 ligues / 90 avec modèle / 9 avec cotes**, chiffres variables. **Pas de CFB, aucune cote inventée, aucun prix annoncé live, aucune EV ou sélection rentable prétendue.**
- **Parité des fonctions ciblées :** [44 sur 44, soit 100 % du catalogue vérifié](docs/parite-modeles-clairvoyance.json), **pas 98 % du dépôt complet**, ni une équivalence des prédictions sur données réelles.
- **Tests face au code original :** [5 232 comparaisons identiques](docs/parite-modeles-clairvoyance.json) pour les calculs Python et JavaScript sélectionnés, avec entrées de test communes (les formulations textuelles des props ne sont pas copiées). [Rapport frontend](docs/parite-clairvoyance-frontend.json) · [rapport NBA](docs/parite-clairvoyance-nba-source.json). La chaîne complète d’acquisition, les données Opta autorisées et les prédictions en conditions réelles ne sont pas encore identiques.
- **Méthode et statut exact des modèles :** [documentation reproduction](modeles/reproduction/README.md) · [tableau de bord gaming parité](docs/parite-clairvoyance.html) · [tests automatisés à la source](.github/workflows/parite-clairvoyance-predictor.yml).
- **NBA sur données réelles :** [30 équipes calculées avec la formule originale de forces/Elo et les statistiques ESPN avancées 2025–2026](docs/clairvoyance-nba-advanced-ratings.json) (ORTG, DRTG, rythme et marges). [460 tests de parité exacts](docs/parite-clairvoyance-espn-nba.json) des transformations ESPN. La saison 2026–2027 n'est pas encore disponible via ESPN pour ces statistiques : les équipes restent sur les données de saison régulière antérieure, sans intégrer les résultats de présaison. BBRef SRS/Opta, blessures, compositions et parité des probabilités finales restent incomplets.
- **CFB exclu** à la demande de l'utilisateur.
- **MoneyPuck NHL (usage strictement personnel, non commercial)** : [laboratoire xG + gardiens](docs/moneypuck.html) · [statistiques des équipes](docs/moneypuck-nhl-latest.json) · [GSAx des gardiens](docs/moneypuck-goalies-latest.json) · [collecteur d'équipes](outils/moneypuck_feed.py) · [collecteur de gardiens](outils/moneypuck_goalies_feed.py) · [tests](tests/test_moneypuck_feed.py) · [actualisation quotidienne](.github/workflows/moneypuck-official.yml). Le flux télécharge **uniquement les CSV de saison explicitement proposés** sur [MoneyPuck.com](https://moneypuck.com/data.htm), cite la source sur chaque écran et ne republie pas les fichiers bruts. Deux saisons restent séparées (actuelle et précédente), sans présenter des observations historiques comme des prédictions. Le `iceTime` CSV est en **secondes** : le rapport dérivé corrige la conversion `stat × 3600 / iceTime`, sans modifier le parseur de référence dont la parité est conservée. Le [moteur NHL expérimental](docs/nhl-model.html) affiche ces xG **en contexte seulement**, sans les intégrer à ses probabilités. Les rapports de gardiens contiennent le **GSAx** (= xG encaissés − buts encaissés), mais aucune donnée de titulaire confirmé : `starter_status=unknown` et `confirmed_starters=false`. Les commits automatiques de données provoquent une republication GitHub Pages par `workflow_run` après réussite du collecteur. Ni cotes ni rentabilité prouvée.

- **Comparaison NHL MoneyPuck à deux modèles (recherche)** : [protocole et formules](recherche/hockey/nhl-moneypuck-deux-modeles.md) · [stabilisation petits échantillons](outils/nhl_moneypuck_prudent.py) · [tests dédiés](tests/test_nhl_moneypuck_prudent.py) · [comparaison des Brier appariés](docs/nhl-shadow-performance.json). Formule Clairvoyance d'origine **inchangée** ; variante indépendante qui réduit le poids des xG sur 3–5 matchs et des arrêts instables grâce à des priors déclarés. Un même journal conserve les deux probabilités avant le début du match. Les anciennes prévisions verrouillées ne sont **jamais rétroactivement complétées** avec la nouvelle variante. Aucun modèle n'est encore calibré ou validé sur un nombre suffisant de rencontres.\n- **Calibration NHL prospective (recherche, non activée)** : [protocole 100 résultats d'entraînement + 40 matchs de test futurs](recherche/hockey/nhl-calibration-prospective.md) · [rapport automatique](docs/nhl-calibration-latest.json) · [tests chronologiques](tests/test_nhl_calibration_prospective.py) · [tableau mobile de progression](docs/nhl-clairvoyance.html). Les probabilités restent inchangées et aucun calibrateur n'est activé sans suffisamment de résultats réels. Les anciennes rencontres ne sont pas rétroactivement transformées en validation indépendante.
- **NHL Clairvoyance / SHADOW sur sources réelles** : [tableau interactif](docs/nhl-clairvoyance.html) · [dernier JSON](docs/nhl-clairvoyance-shadow-latest.json) · [calcul Python](outils/clairvoyance_nhl_moneypuck_shadow.py) · [tests anti-fuite](tests/test_clairvoyance_nhl_moneypuck_shadow.py) · [actualisation autonome](.github/workflows/nhl-clairvoyance-moneypuck-shadow.yml). L'algorithme applique la **formule de prédiction NHL ciblée de Clairvoyance**, vérifiée par tests de parité, aux xG% et aux statistiques de gardiens **réellement collectés** dans MoneyPuck, et à un **proxy Elo recalculé dans Revue** depuis l'historique NHL. Ce n'est **pas** une reproduction de la base Elo du dépôt tiers ni une parité de prédictions finales sur données identiques. Les données sources et leur horodatage doivent précéder le coup d'envoi. Le gardien le plus utilisé n'est **pas** un titulaire confirmé. Modèle SHADOW non calibré, sans cotes, sans recommandation de mise ni garantie de ROI. **Suivi prospectif réel :** [registre figé avant les matchs](docs/nhl-shadow-ledger.json) · [Brier et nombre de résultats](docs/nhl-shadow-performance.json) · [moteur de règlement](outils/nhl_shadow_tracker.py). Chaque prévision est verrouillée une seule fois à au moins 20 minutes du coup d'envoi, puis réglée à partir du score officiel ; aucune ancienne probabilité n'est réécrite. 18 prévisions verrouillées lors de la première exécution du 10 octobre 2026, 0 résultat encore réglé à ce stade.\n
- Les modèles exploratoires Elo, Poisson, MC et Bayes écrits précédemment dans `modeles/simulations/` sont **des expériences distinctes** et ne sont **jamais comptabilisés comme des reproductions**. Les anciennes estimations de 30–35 % mélangeaient fonctionnalités du site et innovations et ne mesuraient pas la fidélité.

## Bibliothèque expérimentale préexistante (hors périmètre de reproduction)

**Revue** est une bibliothèque de recherche **traçable, structurée et testable** : modèles statistiques, algorithmes, méthodologies, sources de données et outils inspirés de dépôts GitHub tiers.

> **Principe : une idée intéressante n'est pas une stratégie rentable démontrée.** Aucun rendement n'est garanti. La bibliothèque distingue hypothèse, code reproductible, backtest et validation hors échantillon.

**Audit Opta :** Clairvoyance intègre les xG, xGA, PPDA, statistiques d'équipes et Opta Power Rankings via The Analyst, mais **Revue n'a pas encore d'accès autorisé à ces données**, et notre modèle n'est pas la copie exacte de son moteur. [Voir l'audit et les écarts](analyses/2026-10-09_Clairvoyance_Opta_modele_ecarts.md).

## Football : mesures d'équipes et comparaison prospective

- [Statistiques ESPN dérivées](docs/football-espn-team-features.json) : tirs, tirs cadrés, possession, passes, interceptions et tacles ; ni xG ni Opta.
- [Collecteur indépendant](modeles/simulations/football_espn_statistiques.py) : historiques horodatés, identifiants d'équipe stables, plafond de requêtes et cache.
- [Registre pré-match](docs/football-shadow-ledger.json) et [score de qualité Brier/log loss](docs/football-shadow-performance.json) : modèle historique contre modèle enrichi ; aucune rentabilité supposée.
- Dernier contrôle du 9 octobre 2026 : 72 matchs avec statistiques, 23 profils d'équipes et 34 prévisions enregistrées en comparaison prospective. Les données de tirs sont actives sur 4 prévisions archivées, et les résultats ne sont pas encore disponibles.

## Football avancé — nouveau candidat testé, sans reprise de code tiers

- [Interface de comparaison football](docs/football-avance.html) et [JSON des probabilités / backtests](docs/football-advanced-shadow.json)
- [Modèle indépendant](modeles/simulations/football_avance_independant.py) et [méthodologie + performances](modeles/simulations/FOOTBALL-AVANCE-README.md)
- 13 tests passés sur GitHub ; calculs de forme, Elo, Poisson corrigé Dixon-Coles, xG/power rating **uniquement** si données autorisées et antérieures au match disponibles.
- Au premier backtest du 9/10/2026, 18 matchs en Liga (Brier un peu meilleur), 60 en MLS (Brier un peu moins bon), trop peu ailleurs. **N'est pas utilisé dans les picks papier**.
- Le fichier de snapshots statistiques licenciés est ignoré par Git, pour ne pas publier des données protégées par inadvertance.

## Engine V2 — reconstruction indépendante du fonctionnement Clairvoyance

- [Portail web Revue](docs/index.html) et [tableau « Engine V2 »](docs/engine-v2.html) : radar de cotes réelles, simulations et suivi en unités fictives.
- [Moteur original Python](outils/revue_engine_v2.py) : prix Betclic/Winamax/Unibet/PMU/NetBet via PulseScore Pro (prioritaire) ou The Odds API ; Pinnacle seulement pour comparaison lorsqu'il est réellement disponible, contrôle strict pré-match, règlement des matchs, historique.
- [Guide d'utilisation Android et configuration de clé](outils/ENGINE-V2-README.md) ; [GitHub Actions Engine V2](.github/workflows/revue-engine-v2.yml).
- [Dernier rapport moteur](docs/engine-v2-latest.json) et [registre paper](docs/engine-v2-ledger.json).

**Première validation technique : 36 tests Engine V2 + PulseScore passés sur GitHub (09/10/2026).** La collecte de cotes est **désactivée tant que PULSESCORE_API_KEY ou THE_ODDS_API_KEY n'est pas configuré** ; aucune opportunité fictive ni ROI inventé. Pas de paris en argent réel. Cette V2 ne prétend pas reproduire l'ensemble des fichiers originaux ni démontrer une stratégie rentable.

## Revue élargie — 19 flux détectés + profils NHL (prototype)

Le moteur récupère les compétitions de football, basket, football américain, baseball et NHL ainsi que les matchs ATP/WTA, UFC et Liiga. **Flux joignable ne signifie pas prédiction validée.**

- [Tableau de bord multisports](docs/multisports.html) · [JSON multisports](docs/multisports-latest.json)
- [Tennis, UFC et Liiga](modeles/simulations/SPORTS_INDIVIDUELS_README.md) · [JSON des derniers événements](docs/individual-latest.json)
- [Radar NHL buteurs / passeurs / points / tirs](docs/nhl-joueurs.html) · [224 profils NHL calculés le 09/10/2026](docs/nhl-players-latest.json)
- [Architecture de l'actualisation sur GitHub Actions](.github/workflows/multisports-independent.yml)
- [Brier / log loss par compétition](docs/qualite-modeles.html) · [résultats vérifiables](docs/backtests-multisports.json) · [méthodologie](outils/BACKTESTS_MULTISPORTS.md) (aucun ROI sans cotes).

À vérifier : les compétitions encore sans flux autorisé (SHL, National League Suisse, Extraliga Tchéquie), les compositions/titularisations, les cotes françaises et les backtests hors échantillon. **Aucune méthode de paris profitable validée.**

## Tableau de bord multisports — 14 flux connectés (prototype)

- [Moteur multisports original](modeles/simulations/multisports_independant.py) et [documentation détaillée](modeles/simulations/MULTISPORTS-README.md).
- [Tableau de bord mobile](docs/multisports.html) : football, basket, football américain, baseball et NHL ; nécessite GitHub Pages pour une adresse de site publique.
- [Prédictions réellement générées](docs/multisports-latest.json) et [workflow d'actualisation](.github/workflows/multisports-independent.yml).
- **Vérification du 09/10/2026 :** 14 flux ESPN/NHL répondent, 133 rencontres sur trois jours et 99 probabilités. D'autres compétitions restent explicitement sans source (hockey européen, tennis, MMA). Les chiffres changent à chaque exécution.
- **Aucune EV réelle ni retour prouvé** : modèles exploratoires non calibrés, pas encore de cote de bookmaker français ni de props joueurs.

## Premier modèle exécutable : NHL Independent (prototype)

- [Moteur Python original Elo + Poisson](modeles/simulations/nhl_independant.py) et [documentation](modeles/simulations/NHL-INDEPENDANT-README.md)
- [Dernières probabilités NHL](docs/nhl-model-latest.json) (fichier calculé réellement depuis l'API NHL)
- [Interface mobile](docs/nhl-model.html) (affichage comme site si GitHub Pages est activé pour /docs)
- [Tests GitHub Actions](.github/workflows/nhl-independent.yml) : 13 tests réussis, rafraîchissement automatisé

**Important :** modèle non calibré, sans données de gardien confirmé, sans prix de bookmaker français et sans stratégie de pari validée. Aucun code du dépôt Clairvoyance non licencié n'a été copié.

## Organisation

```text
Revue/
├── catalogue/                 # Index et fiches synthétiques par idée
│   └── INDEX.md
├── analyses/                  # Audits de dépôts tiers (source, licence, limites, verdict)
├── strategies/
│   ├── football/
│   ├── tennis/
│   ├── basketball/
│   ├── hockey-nhl/
│   ├── baseball/
│   ├── multisports/
│   └── transversales/         # Arbitrage, EV+, boosts, marchés, risk management
├── modeles/
│   ├── probabilites/          # Probabilités, calibration et modèles prédictifs
│   ├── machine-learning/
│   └── simulations/
├── data-sources/              # APIs, scrapers autorisés, formats, normalisation
├── outils/                    # Calculs de cotes, EV, retrait de marge, backtests
├── tests/                     # Tests unitaires, de non-régression et anti-fuite
├── templates/                 # Modèles de fiches et grilles d'évaluation
├── recherche/                 # Pistes prometteuses non validées
└── archives/                  # Approches rejetées / dépréciées et justification
```

Les dossiers sont créés lors des premières intégrations (Git n'enregistre pas les dossiers vides).

## Parcours d'un dépôt tiers

1. **Auditer** : objectif réel, sources, dépendances, licence, sécurité, maintenance et qualité du code.
2. **Extraire** : recenser les idées et sélectionner les modules réellement utiles ; éviter le copier-coller indiscriminé.
3. **Classer** : `analyses/` pour l'audit, `recherche/` pour l'hypothèse, `strategies/` ou `modeles/` pour l'implémentation exploitable, `outils/` pour les briques communes.
4. **Documenter** : auteur, URL, commit/source, licence, sport, marché, données nécessaires, hypothèses, cas d'usage et limites.
5. **Tester** : tests automatisés, absence de fuite temporelle et, si les données le permettent, backtest chronologique avec coûts réalistes.
6. **Statuer** : `À étudier`, `Prototype`, `Testé`, `Validé hors échantillon`, `Rejeté`. Une stratégie « testée » n'est pas automatiquement rentable.

## Critères d'évaluation

| Critère | Points |
|---|---:|
| Idée et utilité réelle | 20 |
| Qualité / reproductibilité du code | 20 |
| Données disponibles et légalité d'accès | 15 |
| Validité statistique, absence de biais | 20 |
| Possibilité de backtester hors échantillon | 15 |
| Maintenance, sécurité, intégration | 10 |
| **Total** | **100** |

**Score d'intérêt documentaire, jamais probabilité de gain.** Une licence incompatible, des données obtenues illicitement ou des failles critiques bloquent l'importation de code même si le score est élevé. Sans licence explicite, documenter les idées sans recopier le code.

## Mesures minimales des stratégies

Pour chaque test : nombre de paris, période, marché, bookmaker, cotes obtenables au moment du pari, mise/gestion du risque, ROI net, profit en unités, drawdown, CLV si disponible, intervalle d'incertitude, ventilation par saison et validation chronologique. Documenter les paris sans résultat et les lignes/cotes manquantes.

## Cadre français

Pour une exploitation en France, distinguer les sports, compétitions et **types de paris** autorisés par l'ANJ, la disponibilité des cotes chez les opérateurs agréés et le droit d'utilisation des données/API. Une stratégie non compatible peut rester archivée pour la recherche, **sans être présentée comme directement exploitable**.

## Ajout d'un nouveau dépôt

Transmettre l'URL GitHub. Chaque nouvelle source aura une fiche d'analyse, un verdict argumenté, une attribution, un emplacement clair et, si la copie est autorisée et pertinente, des modules isolés avec tests. Les versions sources doivent rester identifiables.

Consulter [le catalogue](catalogue/INDEX.md) et [le protocole d'évaluation](templates/PROTOCOLE.md).
