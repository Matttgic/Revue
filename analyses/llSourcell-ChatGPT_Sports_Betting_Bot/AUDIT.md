# Audit de dépôt tiers — llSourcell/ChatGPT_Sports_Betting_Bot

- **URL originale :** https://github.com/llSourcell/ChatGPT_Sports_Betting_Bot
- **Auteur / organisation :** compte `llSourcell`; le README présente le code comme starter associé à une vidéo de Siraj Raval
- **Commit audité :** [`9a907d1ca6ba8f0d50b22e4d60e4815f48b9b4a1`](https://github.com/llSourcell/ChatGPT_Sports_Betting_Bot/commit/9a907d1ca6ba8f0d50b22e4d60e4815f48b9b4a1), branche `master`, 2023-01-24
- **Date de consultation :** 2026-10-11
- **Licence :** aucune licence repérée dans le dépôt; aucune reprise de code
- **État de maintenance :** dernier commit ancien; dépendances de l'application basées sur Expo SDK 40
- **Langage / stack :** Python/Jupyter, modèle NBA externe, OpenAI API, Twitter API, The Odds API, React Native/Expo et Firebase

## Résumé technique

Le dépôt rassemble deux notebooks et un squelette d'application mobile. `Arbitrage.ipynb` interroge The Odds API pour des cotes moneyline américaines, sélectionne le prix maximum par position de résultat, détecte `Σ(1/cote) < 1`, répartit une mise pour égaliser le retour, puis exporte les résultats vers Excel.

`Sports_Bettor.ipynb` supprime les fichiers du répertoire courant avec `rm -rf *`, clone ensuite [kyleskom/NBA-Machine-Learning-Sports-Betting](https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting), installe ses dépendances et lance son modèle. Ce dépôt ne contient donc pas le code ni les données du modèle NBA. Une autre cellule compte le sentiment de tweets des Warriors, sans intégrer cette mesure aux prédictions. Une cellule OpenAI envoie à `text-davinci-002` un bloc de texte de résultats déjà rédigé et lui demande de le résumer : GPT sert de commentaire, pas de moteur prédictif ni de vérificateur des calculs.

L'application Expo/Firebase est principalement un gabarit d'authentification. Son écran d'accueil contient un iframe web et un commentaire indiquant qu'il faudrait connecter le modèle; le README confirme que l'affichage des prédictions était manuel et que les paris ne sont pas passés par programme.

## Idées identifiées et comparaison

| Élément | Apport du dépôt | Comparaison / décision |
|---|---|---|
| Calcul de surebet à partir des meilleurs prix par issue | Formule d'inversion des cotes et mises à retours égaux | Même famille mathématique que le dutching/freebet de [REV-PRETR-01](../pretrehr-Sports-betting/REV-PRETR-01_optimisation-promotions-freebets.md); la couverture multi-bookmaker y est également déjà présente dans le dépôt pretrehr. Aucun doublon méthode ajouté. |
| Enchaînement données → modèle externe → résumé textuel | Illustration d'une architecture de prototype | Aucun composant nouveau vérifiable : les poids/données et le code de prédiction sont clonés depuis un autre projet; GPT résume des sorties inscrites en dur et n'évalue ni la calibration ni le ROI. |
| Comparaison de prix par index de tableau | La cellule d'arbitrage n'apparie pas explicitement les issues selon leur nom ni la ligne de marché | Garde-fou de qualité à conserver : apparier équipe/issue, marché, période et événement avant de comparer les prix. Dans la réponse API enregistrée du notebook, les 115 comparaisons entre bookmakers gardent le même ordre; une anomalie n'est donc pas démontrée dans cet exemple, mais le code dépend de cet ordre. |

## Vérifications et limites

- **Exécution :** aucun notebook, script, appel API ou installateur n'a été lancé.
- **Tests :** aucun test automatisé trouvé; `package.json` ne définit que les commandes Expo de démarrage.
- **Évaluation sportive :** aucun backtest, comparaison de probabilité, journal de prix acceptés, règlement de pari, ROI ou CLV vérifiable.
- **Fraîcheur / disponibilité :** les résultats API enregistrés sont des sorties notebook anciennes, pas un instantané immuable d'une évaluation prospective. Le code n'archive pas les réponses et leurs règles de marché pour reproduction.
- **Robustesse du calcul :** la condition de surebet est algébriquement correcte pour des issues mutuellement exclusives et exhaustives, des cotes décimales valides, une même ligne et des règlements compatibles. Le notebook ne documente pas les arrondis, limites, refus de mises, changements de cote, annulations ni frais. La sélection des meilleurs prix par index suppose en outre que l'ordre des issues est identique chez tous les bookmakers.
- **Risque d'exécution :** la première cellule de `Sports_Bettor.ipynb` efface `*` dans le répertoire courant avant de cloner le modèle; elle peut supprimer des fichiers de travail si on l'exécute ailleurs que dans un environnement jetable.
- **Sécurité :** des cellules contiennent des valeurs qui ressemblent à des clés OpenAI, Twitter et The Odds API directement inscrites dans le notebook. Leur validité actuelle n'a pas été testée et leurs valeurs ne sont pas recopiées ici. Les traiter comme exposées et révoquer/remplacer toute clé encore active. Le notebook ne doit pas être exécuté avec elles.
- **Licence / données :** aucune licence du dépôt n'a été repérée. Les licences, conditions d'utilisation et droits des API externes, ainsi que ceux du modèle cloné, restent séparés et à vérifier.
- **État du front-end :** aucun flux de prédictions vers l'écran d'accueil n'est implémenté; le README décrit cette intégration comme manuelle. La cellule d'analyse Twitter emploie une ancienne interface de recherche et reste un TODO.

## Verdict

**Documenter seulement.** Mon avis : le dépôt est une preuve de concept fragmentaire, pas un bot opérationnel ni un modèle ChatGPT de paris. Son calcul d'arbitrage reprend une méthode déjà cataloguée et n'apporte aucune nouvelle preuve de performance. Sa valeur pour Revue est surtout comparative : il confirme la récurrence du dutching et met en évidence deux contrôles indispensables aux calculateurs de surebets — ne pas laisser les données d'identifiants d'issues dépendre d'un ordre implicite, et ne présenter un arbitrage théorique qu'avec prix compatibles et effectivement disponibles.

## Références et provenance

Références examinées au commit épinglé : [README](https://github.com/llSourcell/ChatGPT_Sports_Betting_Bot/blob/9a907d1ca6ba8f0d50b22e4d60e4815f48b9b4a1/README.md), [notebook d'arbitrage](https://github.com/llSourcell/ChatGPT_Sports_Betting_Bot/blob/9a907d1ca6ba8f0d50b22e4d60e4815f48b9b4a1/Arbitrage.ipynb), [notebook NBA/ChatGPT](https://github.com/llSourcell/ChatGPT_Sports_Betting_Bot/blob/9a907d1ca6ba8f0d50b22e4d60e4815f48b9b4a1/Sports_Bettor.ipynb), [dépendances Expo](https://github.com/llSourcell/ChatGPT_Sports_Betting_Bot/blob/9a907d1ca6ba8f0d50b22e4d60e4815f48b9b4a1/package.json), [écran d'accueil](https://github.com/llSourcell/ChatGPT_Sports_Betting_Bot/blob/9a907d1ca6ba8f0d50b22e4d60e4815f48b9b4a1/src/screens/HomeScreen.js) et [configuration Firebase](https://github.com/llSourcell/ChatGPT_Sports_Betting_Bot/blob/9a907d1ca6ba8f0d50b22e4d60e4815f48b9b4a1/src/core/config.js).

Dépôt consulté en lecture seule. Aucun code, jeu de données ou identifiant n'a été copié dans Revue; aucun appel bookmaker/API ni pari n'a été effectué.
