# Recherche GitHub — données, modèles et méthodes de paris sportifs

**20 nouvelles sources examinées le 11 octobre 2026, chacune ajoutée dans son propre dossier.** Elles complètent les 24 dépôts déjà audités. Les analyses existantes et les modèles de Revue restent indépendants.

Mon choix prioritaire est **penaltyblog + goalmodel** pour les modèles football, **socceraction** pour de nouvelles variables, **nflverse** pour les données NFL et **flumine** pour les contraintes d’exécution. **OddsHarvester** mérite un examen de collecte, mais ses heures et marchés doivent être validés avant de construire un historique de paris. Aucun de ces choix ne repose sur une rentabilité démontrée ici.

## Périmètre et méthode

Recherche à partir de quatre pages GitHub thématiques : [sports-betting](https://github.com/topics/sports-betting), [sports-analytics](https://github.com/topics/sports-analytics), [betfair](https://github.com/topics/betfair), [tennis](https://github.com/topics/tennis), complétées par [une recherche football/prediction/Dixon–Coles](https://github.com/search?q=football+prediction+dixon+coles&type=repositories), des bibliothèques de référence et les liens entre projets. Pages consultées sans connexion de compte. Les pages de topics et de recherche sont variables et ne constituent pas un inventaire exhaustif de GitHub.

Sélection sur l’apport au catalogue : données, probabilités, mécanismes sportifs, simulation, traçabilité. Les étoiles et les promesses de ROI ne servent pas de preuve. Les outils de données sont conservés même s’ils ne prédisent aucun pari : une donnée vérifiable peut apporter plus qu’un modèle supplémentaire utilisant les mêmes variables.

Les 20 dépôts sont accessibles à la consultation et épinglés par SHA. Les revues portent sur les README, licences et fichiers ciblés indiqués dans chaque audit. Betfairlightweight fait surtout l’objet d’un examen documentaire ; StatsBomb d’un examen de documentation, licence et liste des compétitions. Il ne s’agit pas de 20 audits exhaustifs ni de 20 installations validées. Les scripts de collecte sportive, entraînements et suites complètes n’ont pas été lancés.

Les sources ont été consultées dans un répertoire temporaire. Revue reçoit seulement des fiches rédigées, les références et les résultats de contrôles. [sources.json](sources.json) conserve les versions, URL et empreintes des fichiers référencés. Pour les datasets publiés en releases, le SHA du code ne fige pas les données.

## Comparatif des 20 ajouts

P1 = à étudier en premier ; P2 = complément utile ; P3 = piste spécialisée avec prérequis plus lourds. Ce sont des priorités de recherche, pas des notes de qualité absolues.

| Dépôt | Domaine / rôle | Priorité | Mon avis | Analyse indépendante |
|---|---|---|---|---|
| [martineastwood/penaltyblog](https://github.com/martineastwood/penaltyblog) | Football · modèles et probabilités | P1 | Premier choix pour un banc comparatif football ; backtest financier à encadrer. | [Dossier](../../analyses/penaltyblog/AUDIT.md) |
| [mberk/shin](https://github.com/mberk/shin) | Multi-sports · retrait de marge | P1 | Petite référence utile pour comparer les probabilités implicites. | [Dossier](../../analyses/shin/AUDIT.md) |
| [gotoConversion/goto_conversion](https://github.com/gotoConversion/goto_conversion) | Multi-sports · retrait de marge | P2 | Formule à comparer ; paquet actuel trop hétérogène pour une adoption directe. | [Dossier](../../analyses/goto_conversion/AUDIT.md) |
| [opisthokonta/goalmodel](https://github.com/opisthokonta/goalmodel) | Football · distributions de scores | P1 | Très bonne référence méthodologique pour dépasser le Poisson simple. | [Dossier](../../analyses/goalmodel/AUDIT.md) |
| [Torvaney/regista](https://github.com/Torvaney/regista) | Football · Dixon–Coles extensible | P2 | Référence pédagogique claire ; intérêt surtout pour comprendre et étendre les formules. | [Dossier](../../analyses/regista/AUDIT.md) |
| [ML-KULeuven/socceraction](https://github.com/ML-KULeuven/socceraction) | Football · variables événementielles | P1 | Une des meilleures sources de nouvelles variables pour Revue. | [Dossier](../../analyses/socceraction/AUDIT.md) |
| [statsbomb/open-data](https://github.com/statsbomb/open-data) | Football · données événementielles | P1 recherche | Excellente matière de recherche ; droits beaucoup plus restrictifs que le mot open ne le suggère. | [Dossier](../../analyses/statsbomb-open-data/AUDIT.md) |
| [probberechts/soccerdata](https://github.com/probberechts/soccerdata) | Football · collecte et rapprochement | P1 | Bonne référence de connecteurs ; normalisation utile mais provenance temporelle à renforcer. | [Dossier](../../analyses/soccerdata/AUDIT.md) |
| [nflverse/nflreadpy](https://github.com/nflverse/nflreadpy) | NFL · client de données | P1 | Point d’entrée Python intéressant pour uniformiser les données NFL. | [Dossier](../../analyses/nflreadpy/AUDIT.md) |
| [nflverse/nflverse-data](https://github.com/nflverse/nflverse-data) | NFL · publications de données | P1 | Source structurante ; il faut versionner les fichiers téléchargés en plus du code. | [Dossier](../../analyses/nflverse-data/AUDIT.md) |
| [jldbc/pybaseball](https://github.com/jldbc/pybaseball) | MLB · Statcast et statistiques | P1 | Très bonne base de recherche MLB, particulièrement pour les variables lanceur/frappeur. | [Dossier](../../analyses/pybaseball/AUDIT.md) |
| [swar/nba_api](https://github.com/swar/nba_api) | NBA · client statistiques et live | P1 | Brique de collecte utile, sans modèle ni avantage prédictif fourni. | [Dossier](../../analyses/nba_api/AUDIT.md) |
| [sportsdataverse/cfbfastR](https://github.com/sportsdataverse/cfbfastR) | Football américain NCAA · données et modèles EP/WP | P2 | Intéressant pour les modèles de situation et les contrats de variables. | [Dossier](../../analyses/cfbfastR/AUDIT.md) |
| [mcekovic/tennis-crystal-ball](https://github.com/mcekovic/tennis-crystal-ball) | Tennis · Elo, matchs et tournois | P2 | Très riche pour étudier le tennis ; adoption complète coûteuse. | [Dossier](../../analyses/tennis-crystal-ball/AUDIT.md) |
| [betcode-org/betfair](https://github.com/betcode-org/betfair) | Multi-sports · marché exchange et historique | P1 | Bonne brique pour lire et rejouer les marchés exchange. | [Dossier](../../analyses/betfairlightweight/AUDIT.md) |
| [betcode-org/flumine](https://github.com/betcode-org/flumine) | Multi-sports · simulation et exécution | P1 | Candidat prioritaire pour comprendre un backtest avec contraintes d’exécution. | [Dossier](../../analyses/flumine/AUDIT.md) |
| [tarb/betfair_data](https://github.com/tarb/betfair_data) | Multi-sports · parsing d’historiques exchange | P2 | Utile si le volume d’historiques devient le goulot d’étranglement. | [Dossier](../../analyses/betfair_data/AUDIT.md) |
| [jordantete/OddsHarvester](https://github.com/jordantete/OddsHarvester) | Multi-sports · collecte de cotes | P1 sous réserve | Très pertinent pour étudier la collecte de cotes ; qualité temporelle à vérifier avant backtest. | [Dossier](../../analyses/OddsHarvester/AUDIT.md) |
| [Friends-of-Tracking-Data-FoTD/LaurieOnTracking](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking) | Football · tracking et contrôle spatial | P3 | Très formateur pour les mécanismes du jeu ; besoin de données élevé. | [Dossier](../../analyses/LaurieOnTracking/AUDIT.md) |
| [pnxenopoulos/awpy](https://github.com/pnxenopoulos/awpy) | Esport CS2 · demos et variables | P3 | Bonne porte d’entrée vers CS2 ; tout le modèle de pari reste à construire. | [Dossier](../../analyses/awpy/AUDIT.md) |

## Enseignements concrets

1. **Comparer les distributions, pas seulement les algorithmes ML.** Goalmodel permet d’examiner dispersion et queues de distribution ; penaltyblog offre plusieurs modèles et transformations de cotes. Tester leur apport sur les totaux, BTTS et 1N2 avec les mêmes matchs et les mêmes fenêtres. Un meilleur ajustement historique ne suffit pas.
2. **Enrichir les variables sans introduire le futur.** Socceraction apporte xT/VAEP, LaurieOnTracking le contrôle spatial, pybaseball les événements Statcast, awpy les événements CS2. Pour le pré-match, ces mesures doivent être calculées exclusivement sur le passé. Même le modèle qui transforme les événements en scores doit avoir été entraîné avant la période évaluée.
3. **Une archive publique n’est pas forcément une archive des informations disponibles à l’époque.** nflverse peut remplacer ses fichiers de release ; Statcast peut réviser des saisons anciennes ; soccerdata peut remplacer une heure manquante par midi. Sauvegarder séparément date de l’événement, disponibilité, collecte, révision et empreinte du fichier.
4. **Les cotes exigent une identité complète.** Sport, rencontre, joueur/équipe, bookmaker, marché, ligne, période, règles de règlement et fuseau doivent correspondre. OddsHarvester documente des ambiguïtés tennis et des heures sans offset. Une moyenne ou un meilleur prix n’est pas nécessairement une mise exécutable.
5. **Le compte et l’exécution peuvent changer le résultat du backtest.** Penaltyblog crédite immédiatement le gain dans son compte ; une stratégie qui réutilise ce solde doit gérer les règlements différés. Flumine modélise des délais et files, mais une option de matching peut compter deux fois la liquidité. Aucun moteur ne dispense d’examiner les hypothèses.
6. **Les noms et la popularité ne valident pas les calculs.** L’exemple Shin a été reproduit avec l’optimiseur Python isolé. Sur les mêmes cotes, efficient_shin_conversion diffère de Shin itératif d’environ 0,002877 au maximum. Les prix Kaggle affichés par goto_conversion ne constituent pas des gains de paris.
7. **Licence du client et droits des données sont séparés.** NBA API et pybaseball sont MIT pour leur code, pas pour tous les contenus récupérés. Le PDF StatsBomb interdit explicitement l’exploitation commerciale des données ou analyses dérivées. nflreadpy distingue notamment les données FTN sous CC-BY-SA du socle généralement CC-BY.

## Ce que je testerais en premier

| Expérience future | Comparaison | Condition pour retenir l’idée |
|---|---|---|
| Retrait de marge | Multiplicatif, Shin, power et goto sur les mêmes cotes | Calibration/log-loss et stabilité par marché sur période future gelée ; seuils choisis auparavant |
| Scores football | Poisson, Dixon–Coles, binomiale négative/CMP | Gain probabiliste stable hors échantillon ; masse de probabilité correcte ; benchmark marché au même instant |
| Variables football | Baseline Elo/DC/xG puis ajout xT/VAEP | Gain incrémental sur matchs communs, sans entraîner les transformations sur le test |
| NFL et MLB | Pipeline de données commun avant nouveaux modèles | Identifiants stables, absence de variables post-match et snapshots reproductibles |
| Exchange | Hypothèse d’exécution immédiate puis délais, liquidité et commissions | Résultat qui résiste à des hypothèses prudentes et concorde ensuite avec un suivi simulé prospectif |
| Tennis | Elo par surface puis modèle point/jeu/set/match | Probabilités calibrées par format et politique explicite sur abandons/forfaits |

Ces expériences sont proposées, **pas exécutées**. Elles doivent commencer par un benchmark de marché avec marge retirée et une baseline simple. Réserver une période finale jamais utilisée pour sélectionner modèle, seuil d’EV ou fraction de Kelly. Reporter le nombre de matchs et de paris, les données manquantes, le ROI net, l’exposition, le drawdown et l’incertitude ; le taux de réussite seul est insuffisant.

## Contrôles effectués

- Accès aux 20 dépôts, SHA des versions, textes de licence et chemins ciblés vérifiés.
- Compte penaltyblog : exécution directe du module Account, 100 unités + pari gagnant de 10 à cote 2 = solde immédiat 110. Confirme son comportement ; ne valide pas le moteur complet.
- Shin : extraction AST de l’optimiseur Python, restitution de l’exemple [2,6 ; 2,4 ; 4,3], 425 itérations internes et delta d’environ 9,67e−13. La convention de comptage de l’API complète n’est pas testée ; extension Rust non exécutée.
- goto_conversion : extraction AST de quatre fonctions mathématiques, uniquement chemin listes Python. Somme des probabilités goto = 1 sur l’exemple, et comparaison à Shin. Les fonctions annexes et le paquet complet ne sont pas exécutés.
- Résultats bruts de ces contrôles : [controles-numeriques.json](controles-numeriques.json). Aucun backtest économique reproduit.

## Limites de couverture et accès

Cette recherche couvre football, NFL, NCAA football, NBA, MLB, tennis, CS2 et infrastructures exchange utilisables notamment en hippisme. Elle ne couvre pas exhaustivement les modèles UFC, cricket, rugby, sports féminins ou NHL supplémentaires ; des pistes NHL/UFC figurent déjà dans Revue. Les dépôts non retenus dans les pages de découverte n’ont pas tous été examinés et ne sont pas implicitement rejetés.

Les URL JeffSackmann/tennis_atp, JeffSackmann/tennis_wta et JeffSackmann/tennis_pointbypoint ont renvoyé HTTP 404 dans la session : pas d’ajout comme sources accessibles, ni conclusion sur une disparition définitive. La piste open-source-sports/awesome-sports-analytics a également renvoyé 404. StatsBomb/open-data redirige vers hudl/open-data ; l’alias et la destination sont conservés.

L’archive OddsHarvester dépassait le plafond local de 45 Mo retenu pour cette recherche ; README, licence et fichiers pertinents ont été lus individuellement au même SHA. Les dépôts et services externes n’ont pas été modifiés. Aucun compte de pari ni API sportive payante n’a été connecté.

## Fiches de méthode ajoutées

- [Dispersion des scores](../../analyses/goalmodel/REV-GOALMODEL-01_dispersion-scores.md)
- [Variables xT/VAEP](../../analyses/socceraction/REV-SOCCERACTION-01_variables-actions.md)
- [Simulation de l’exécution](../../analyses/flumine/REV-FLUMINE-01_execution.md)
- [Tennis : du point au match](../../analyses/tennis-crystal-ball/REV-TCB-01_point-match.md)
- [Contrat modèle/variables](../../analyses/cfbfastR/REV-CFB-01_contrat-modele.md)

Les autres sources complètent les méthodes existantes ou fournissent des données/outils. Elles restent cataloguées sans créer artificiellement une stratégie par dépôt.
