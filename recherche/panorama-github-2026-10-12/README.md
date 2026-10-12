# Recherche GitHub n° 2 — données, modèles et méthodes de paris sportifs

**22 nouvelles sources examinées le 12 octobre 2026, chacune dans son propre dossier.** Elles s'ajoutent aux 44 dépôts déjà audités (dont les [20 du 11 octobre](../panorama-github-2026-10-11/README.md)), sans doublon.

Cette deuxième vague vise ce qui manquait : **des cotes historiques réelles pour mesurer**, des **systèmes de classement dynamiques**, le **hockey** (sport central de Revue), le football international, l'UFC et le cricket. Elle va plus loin que la lecture de code : trois jeux de données ont été téléchargés et analysés, et une question restée ouverte la veille — *quelle méthode de retrait de marge choisir ?* — reçoit une première réponse mesurée.

## Ce qu'il faut retenir

1. **Le choix du retrait de marge dépend du marché, et se mesure.** Sur 235 543 matchs de football (Bet365, 1N2), la méthode puissance bat la multiplicative de 0,0007 de log-loss par match (≈ 10 erreurs-types) ; sur la NBA (13 884 matchs, clôture), c'est l'inverse : la puissance dégrade (+0,0010). Nouvel outil Revue : [`calibration_devig.py`](../../outils/controles/calibration_devig.py). Fiche : [REV-IMPLIED-01](../../analyses/implied/REV-IMPLIED-01_choix-devig-par-marche.md).
2. **Des défauts confirmés par exécution, pas seulement par lecture** : la méthode Shin par défaut du paquet R `implied` plante sur tous les marchés à deux issues ; 7,9 % des Elo du jeu Club-Football-Match-Data viennent d'une photo prise le jour du match ou après ; la partie MLB de l'archive sportsbookreview apparie les cotes de matchs différents (46 % de paires de même signe).
3. **Une archive gratuite de cotes d'ouverture et de clôture NHL 2011-2021 est exploitable** (13 678 matchs, cohérente) : c'est la matière qui manquait pour tester des modèles NHL contre la clôture.
4. **Les bancs d'essai des systèmes de classement trompent souvent** : kickscore lisse avec le futur par défaut, elote gèle les forces pendant tout le test, openskill mélange la chronologie. Pour parier, il faut toujours la boucle « prédire, puis mettre à jour ».
5. **Aucun rendement positif n'a été démontré.** Le seul ROI spectaculaire (SoccerPredictor, +33 %) est contaminé par une sélection sur le jeu de test.

## Méthode

- Recherche par connaissance des références du domaine (paquets cités dans la littérature, tutoriels Betfair, bibliothèques de classement), liens entre projets, et vérification d'existence de chaque dépôt (`git ls-remote`). Les dépôts déjà audités ont été exclus.
- Chaque dépôt est cloné sans extraction (`--filter=blob:none`) dans un répertoire temporaire hors de Revue ; seuls les fichiers cités sont lus. SHA, date du dernier commit, licence et empreinte SHA-256 de chaque fichier lu : [sources.json](sources.json).
- Code tiers jamais exécuté, sauf une fonction R pure du paquet `implied` (lue en entier avant exécution, sous R 4.3.3 isolé).
- Données téléchargées hors du dépôt et analysées par des scripts Revue : [controles/](controles/). Résultats bruts : [controles-numeriques.json](controles-numeriques.json).
- Requêtes HTTP réelles le 12/10/2026 pour vérifier que les sources de données répondent encore.

## Comparatif des 22 ajouts

P1 = à étudier en premier ; P2 = complément utile ; P3 = piste spécialisée. Priorité de recherche, pas note de qualité.

| Dépôt | Domaine / rôle | Priorité | Avis | Dossier |
|---|---|---|---|---|
| [opisthokonta/implied](https://github.com/opisthokonta/implied) | Multi-sports · retrait de marge (R) | P1 | Meilleure référence de formules ; Shin par défaut cassé sur deux issues. | [Audit](../../analyses/implied/AUDIT.md) |
| [xgabora/Club-Football-Match-Data-2000-2025](https://github.com/xgabora/Club-Football-Match-Data-2000-2025) | Football · 238 858 matchs, cotes, Elo | P1 données | Plus grand jeu ouvert trouvé ; écarter Elo postérieurs et clusters. | [Audit](../../analyses/Club-Football-Match-Data/AUDIT.md) |
| [FinnedAI/sportsbookreview-scraper](https://github.com/FinnedAI/sportsbookreview-scraper) | NHL/NBA/NFL/MLB · cotes 2011-2021 | P1 sous réserve | NHL exploitable (ouverture + clôture) ; MLB corrompu. | [Audit](../../analyses/sportsbookreview-scraper/AUDIT.md) |
| [lucasmaystre/kickscore](https://github.com/lucasmaystre/kickscore) | Multi-sports · forces dynamiques | P1 | Généralise Elo/TrueSkill ; filtrer, ne pas lisser, en backtest. | [Audit](../../analyses/kickscore/AUDIT.md) |
| [Torvaney/mezzala](https://github.com/Torvaney/mezzala) | Football · Dixon–Coles modulaire | P2 | Blocs, poids, regroupement des équipes rares ; inactif depuis 2021. | [Audit](../../analyses/mezzala/AUDIT.md) |
| [helton-tech/elote](https://github.com/helton-tech/elote) | Multi-sports · comparateur de classements | P2 | Pratique pour trier ; son évaluation gèle les forces. | [Audit](../../analyses/elote/AUDIT.md) |
| [OpenDebates/openskill.py](https://github.com/OpenDebates/openskill.py) | Multi-joueurs · TrueSkill ouvert | P3 | Pour courses et équipes variables ; banc d'essai non chronologique. | [Audit](../../analyses/openskill/AUDIT.md) |
| [danmorse314/hockeyR](https://github.com/danmorse314/hockeyR) | NHL · PBP et xG (R) | P2 | xG ouvert documenté ; à ré-entraîner saison par saison. | [Audit](../../analyses/hockeyR/AUDIT.md) |
| [HarryShomer/Hockey-Scraper](https://github.com/HarryShomer/Hockey-Scraper) | NHL · PBP et présences | P2 | Non maintenu, mais ses points d'accès répondent (4/4). | [Audit](../../analyses/Hockey-Scraper/AUDIT.md) |
| [HarryShomer/xG-Model](https://github.com/HarryShomer/xG-Model) | NHL · xG | P3 | Liste de variables utile ; découpage aléatoire, pas de licence. | [Audit](../../analyses/HarryShomer-xG-Model/AUDIT.md) |
| [betfair-datascientists/predictive-models](https://github.com/betfair-datascientists/predictive-models) | Foot/AFL/rugby · tutoriels | P2 | Bonne pédagogie ; modèle EPL derrière les cotes et deux erreurs. | [Audit](../../analyses/betfair-predictive-models/AUDIT.md) |
| [dashee87/blogScripts](https://github.com/dashee87/blogScripts) | Football · tutoriel Dixon–Coles | P3 | Protocole correct, ξ choisi sur la période rapportée. | [Audit](../../analyses/dashee87-blogScripts/AUDIT.md) |
| [fivethirtyeight/data](https://github.com/fivethirtyeight/data) | Multi-sports · Elo publiés | P3 | Spécifications utiles ; URL de données mortes (→ abcnews.com). | [Audit](../../analyses/fivethirtyeight-data/AUDIT.md) |
| [amosbastian/understat](https://github.com/amosbastian/understat) | Football · xG | P2 | Client à jour, point d'accès actif ; archiver les valeurs datées. | [Audit](../../analyses/understat/AUDIT.md) |
| [JaseZiv/worldfootballR](https://github.com/JaseZiv/worldfootballR) | Football · FBref/Transfermarkt | P2 | Valeurs marchandes et suspensions datées ; archivé. | [Audit](../../analyses/worldfootballR/AUDIT.md) |
| [martj42/international_results](https://github.com/martj42/international_results) | Football international · 1872-2026 | P2 | Excellente base Elo ; score avec prolongation ≠ règlement 1N2. | [Audit](../../analyses/international_results/AUDIT.md) |
| [JeffSackmann/tennis_MatchChartingProject](https://github.com/JeffSackmann/tennis_MatchChartingProject) | Tennis · coup par coup | P2 recherche | Unique, mais 42 % des matchs concernent 10 joueurs. | [Audit](../../analyses/tennis_MatchChartingProject/AUDIT.md) |
| [sportsdataverse/hoopR](https://github.com/sportsdataverse/hoopR) | NBA/NCAAB · données | P2 | Très actif ; blessures sans historique. | [Audit](../../analyses/hoopR/AUDIT.md) |
| [nflverse/nflfastR](https://github.com/nflverse/nflfastR) | NFL · EP/WP | P2 | `vegas_wp` contient la ligne ; modèles ajustés sur tout l'historique. | [Audit](../../analyses/nflfastR/AUDIT.md) |
| [WarrierRajeev/UFC-Predictions](https://github.com/WarrierRajeev/UFC-Predictions) | UFC · classification | P3 | Données utiles ; test aléatoire, pas de cotes. | [Audit](../../analyses/UFC-Predictions/AUDIT.md) |
| [robjhyndman/cricketdata](https://github.com/robjhyndman/cricketdata) | Cricket · données | P3 | Porte d'entrée vers un sport absent de Revue. | [Audit](../../analyses/cricketdata/AUDIT.md) |
| [jkrusina/SoccerPredictor](https://github.com/jkrusina/SoccerPredictor) | Football · double chance | Rejet | ROI 33 % sur 32 paris, poids choisis sur le test. | [Audit](../../analyses/SoccerPredictor/AUDIT.md) |

## Résultats mesurés

### 1. Retrait de marge : la réponse dépend du marché

Différence de log-loss par match par rapport à la multiplicative (négatif = mieux ; erreur-type appariée entre parenthèses). Calcul : outil Revue `calibration_devig.py`, recoupé par une version numpy indépendante.

| Marché | n | Additive | Puissance | Shin | Odds ratio |
|---|---:|---:|---:|---:|---:|
| Football 1N2 (Bet365) | 235 543 | −0,00066 (0,00007) | **−0,00071** (0,00007) | −0,00060 (0,00005) | −0,00058 (0,00004) |
| Football +/-2,5 buts (Bet365) | 156 615 | −0,00011 (0,00003) | −0,00013 (0,00004) | −0,00011 (0,00003) | −0,00012 (0,00003) |
| NHL moneyline clôture | 13 666 | −0,00007 (0,00006) | −0,00009 (0,00009) | −0,00007 (0,00006) | −0,00007 (0,00006) |
| NBA moneyline clôture | 13 884 | +0,00044 (0,00021) | **+0,00105** (0,00036) | +0,00044 (0,00021) | +0,00052 (0,00024) |

Le gain football se concentre sur les gros favoris (cote < 1,35 : −0,007 par match). L'effet garde le même signe sur 2000-2009 (puissance −0,0012), 2010-2018 (−0,0005) et 2019-2026 (−0,0006). Sur deux issues, Shin = additive (identité vérifiée par test).

### 2. Qualité des données

| Contrôle | Résultat |
|---|---|
| Forme 3 matchs (Club-Football-Match-Data) | 99,98 % identique aux 3 matchs précédents : pas de fuite |
| Elo (Club-Football-Match-Data) | 7,9 % des lignes utilisent une photo datée du jour du match ou après ; l'écart suit le résultat (+1,67 victoire / −2,78 défaite) |
| Colonnes de clusters `C_*` | AUC 0,503 : aucun signal, calcul non documenté |
| NHL sportsbookreview | 0 somme implicite < 1 à la clôture, marge médiane 3,2 %, clôture plus juste que l'ouverture (0,6689 contre 0,6711) |
| MLB sportsbookreview | 46 % de paires de même signe, 41 % de sommes < 1 : appariement décalé, inutilisable |
| Football international | Scores avec prolongation : ne règlent pas un 1N2 à 90 minutes |
| Tennis MCP | 42 % des matchs impliquent 10 joueurs ; 16 % sont des finales |

### 3. Meilleure cote du marché

Parier quand la meilleure cote (~17 bookmakers) dépasse la probabilité Shin de Bet365 de plus de 5 % : ROI +1,7 %, IC 95 % [−0,6 ; +4,0] sur 32 173 paris. Pas significatif, et une « meilleure cote » agrégée n'est pas un prix qu'on peut réellement prendre. Cela confirme la prudence déjà notée sur [BeatTheBookie](../../analyses/BeatTheBookie/AUDIT.md).

## Enseignements nouveaux

1. **Mesurer la conversion des cotes avant de mesurer l'avantage.** L'EV et le CLV dépendent de la probabilité « juste ». Un mauvais choix (puissance en NBA) introduit un biais systématique dans tout le suivi.
2. **Le lissage est une fuite.** Tout modèle d'état (Kalman, processus gaussien, kickscore) qui exploite la séquence entière doit être réajusté avec le seul passé avant chaque prédiction.
3. **Une photo de rating doit être strictement antérieure au match.** Une égalité de date suffit à contaminer un Elo.
4. **Un score n'est pas un règlement.** Prolongation (football international), tirs au but, temps réglementaire en hockey, push : le résultat utilisé doit être celui de la règle du pari.
5. **Une variable sportive peut contenir le marché.** `vegas_wp` (NFL) ou des cotes moyennes dans les variables : noter l'instant de la cote utilisée.
6. **Échantillon de données ≠ population.** Les matchs chartés au tennis, les combattants UFC sans historique, les nouveaux venus exclus par elote : toujours vérifier qui manque.
7. **Les tutoriels officiels se trompent aussi.** Le tutoriel Betfair évalue un autre modèle que celui annoncé et utilise un identifiant de match comme variable.

## Ce que je testerais ensuite

| Expérience | Données disponibles | Condition pour retenir |
|---|---|---|
| Choisir la méthode de retrait de marge des cotes FR suivies par Revue | Journal papier et cotes observées Revue | Gain > 2 erreurs-types sur une période antérieure, puis figé |
| Elo Revue contre kickscore (filtrage) sur la NHL | sportsbookreview NHL 2011-2021 (clôture) | Log-loss plus basse que la clôture dé-margée, hyperparamètres choisis sur le passé |
| Dixon–Coles pondéré + regroupement | Club-Football-Match-Data | Calibré 2019-2026 avec ξ et N choisis sur 2010-2018 |
| CLV NHL : l'ouverture → clôture est-elle prévisible ? | sportsbookreview NHL | Effet hors échantillon et après marge, sinon abandon |

Ces expériences ne sont pas exécutées. Elles doivent suivre la [règle de décision](../../outils/suivi/regle_decision.py) et le [protocole](../../templates/PROTOCOLE.md).

## Limites et accès

- Revues ciblées : pas d'audit exhaustif ni de sécurité ; aucune suite de tests tierce exécutée ; aucun modèle tiers réentraîné.
- Les cotes Bet365 (Football-Data) et sportsbookreview n'ont pas d'horodatage précis : ouverture/clôture selon la source, instant inconnu.
- Inaccessibles dans cette session (authentification demandée par GitHub) : `JeffSackmann/tennis_atp`, `tennis_wta`, `tennis_slam_pointbypoint`, `joenano/rpscrape`, `greerreNFL/nfeloapp`, `mcbarlowe/nhlscraper`. Pas de conclusion sur leur disparition.
- Hippisme, rugby, golf et esport restent peu couverts.
- Cadre français : vérifier pour chaque marché qu'il est proposé par un opérateur agréé ANJ ; les sources non commerciales (MCP, StatsBomb) restent limitées à la recherche.

## Fiches de méthode ajoutées

- [REV-IMPLIED-01 — Choisir le retrait de marge par sport et par marché](../../analyses/implied/REV-IMPLIED-01_choix-devig-par-marche.md)
- [REV-KICKSCORE-01 — Forces dynamiques : filtrer pour prédire, lisser pour décrire](../../analyses/kickscore/REV-KICKSCORE-01_filtrage-vs-lissage.md)
- [REV-MEZZALA-01 — Dixon–Coles : pondération temporelle et regroupement](../../analyses/mezzala/REV-MEZZALA-01_ponderation-et-regroupement.md)
- [REV-NFLFASTR-01 — Variables ancrées sur la ligne du marché](../../analyses/nflfastR/REV-NFLFASTR-01_probabilite-ancree-sur-la-ligne.md)
