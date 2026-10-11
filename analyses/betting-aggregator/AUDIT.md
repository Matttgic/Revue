# Audit — ixbogotaix-ops/betting-aggregator

- **URL originale :** [github.com/ixbogotaix-ops/betting-aggregator](https://github.com/ixbogotaix-ops/betting-aggregator)
- **Commit audité :** [`a528bdc3b78914561904b2e2d9872a4bb9e8131f`](https://github.com/ixbogotaix-ops/betting-aggregator/commit/a528bdc3b78914561904b2e2d9872a4bb9e8131f) (`2026-10-11`, correction annoncée des marchés mi-temps/temps plein et des dates de Moscou)
- **Date d’audit :** 2026-10-11
- **Licence :** aucun fichier de licence repéré. Ne pas reprendre le code ni les données sans autorisation.
- **Maintenance et contenu :** commit récent; application FastAPI/SQLAlchemy asynchrone et React/Vite, scrapers web et Telegram, intégration The Odds API/OpenRouter, SQLite et Docker. Aucun README ni test automatisé repéré dans les fichiers suivis. La base SQLite commitée est vide (0 octet); les dépendances Python ne sont pas épinglées.

## Mon avis

**Bonne idée d’architecture à regarder, mais faible valeur prédictive en l’état.** Le projet réunit dans une même interface des pronostics de sites et de canaux Telegram, des matchs et des cotes bookmaker, puis tente de rapprocher les équipes et de présenter un consensus. C’est une piste de collecte et de suivi. Les scores affichés comme confiance ne sont pas mesurés : les performances des sources sont saisies à la main, les prédictions ne sont pas réglées contre les résultats, et le consensus récompense des avis qui ne sont ni indépendants ni vérifiés. Les justifications présentent des statistiques et un avantage (+EV) qui ne proviennent d’aucune donnée du pipeline.

## Ce que le code fait

- `api_client.py` interroge The Odds API pour plusieurs sports et enregistre une sélection d’issues du marché `h2h` comme avis bookmaker. Le bookmaker et le marché sont pris par leur position dans la réponse, et non choisis ou comparés selon une règle vérifiable.
- `telegram_scraper.py` récupère les publications publiques récentes de nombreux canaux, extrait une cote par expression régulière et cherche des équipes par correspondance floue. Une mention très proche d’une seule équipe suffit à retenir un match; le parseur ne couvre que quelques formats d’issues et de cotes.
- `consensus.py` normalise le texte des pronostics, additionne les poids des sources, puis applique des bonus heuristiques selon le nombre de pronostics et les poids élevés. Le résultat est divisé par une constante choisie dans le code et affiché sur 100 : il ne s’agit ni d’une probabilité calibrée ni d’une mesure de performance.
- `capper_scraper.py` attribue des poids à partir de ROI, taux de réussite et volume prédéfinis dans la liste des canaux; ce ne sont pas des bilans recalculés depuis un historique de pronostics réglés. Il attribue aussi une confiance de 100 aux pronostics Telegram enregistrés.

## Problèmes qui changent le verdict

1. **Le consensus peut compter deux fois le même signal.** Pour chaque favori extrait des cotes, le code ajoute également un pronostic de « StatArea AI » qui reprend exactement le même favori et le même prix, mais le présente comme une source statistique distincte. Il n’y a pas de modèle de tendances visible derrière cette seconde ligne. Le nombre de sources augmente donc sans nouvelle preuve.
2. **Les pondérations de pronostiqueurs sont non sourcées.** `TARGET_CHANNELS` contient des ROI, taux de réussite et volumes statiques, puis `calculate_capper_weight()` les convertit en score. Aucune date, liste de paris, règle de règlement, cote obtenue ou taille d’échantillon reproductible ne les étaye dans le dépôt.
3. **L’habillage analytique invente des faits.** `analytics_engine.py` génère des séries récentes, pourcentages d’arrêts, statistiques de tirs/points, confrontations directes et arguments de blessures sans recevoir ces données. Il affirme aussi une convergence indépendante et un EV positif. Le module OpenRouter ne reçoit que noms, issues, cotes et scores; son prompt lui demande malgré tout de sélectionner des paris « sûrs » et de rédiger un texte persuasif. Ces champs doivent être traités comme du texte généré, jamais comme de l’analyse factuelle.
4. **Le checkout semble incomplet pour l’exécution.** `main.py`, `schemas.py`, les scrapers et le planificateur importent `app.models`, mais aucun `backend/app/models.py` ni équivalent n’est suivi dans le commit. La compilation syntaxique des fichiers Python passe, ce qui ne valide pas les imports; l’application n’a pas été lancée. La base vide ne fournit pas de remplacement.
5. **L’absence de clé API peut injecter un faux match.** Si The Odds API ne renvoie aucun match, `capper_scraper.py` crée un événement de démonstration Manchester United–Arsenal avec un identifiant `mock_api_1`, puis poursuit le flux de collecte. Sans séparation stricte entre démonstration et production, ce match peut se mélanger aux données affichées.
6. **Résultats et prix ne sont pas validés.** Je n’ai trouvé ni mécanisme exploitable de règlement, ni mesure de ROI/CLV/calibration, ni suite de tests. L’API de cotes stocke une sélection favorite, pas un historique de prix horodatés et comparables. L’accord de plusieurs pronostics ne démontre donc aucun avantage face au marché.

## Idées et relation au catalogue Revue

L’idée générale d’agréger des avis indépendants recoupe déjà [REV-BLUMMA-03](../Betting-Dashboard/REV-BLUMMA-03_consensus-signaux.md), qui insiste sur la redondance et le double comptage, et [REV-THOM-01](../edouardthom-ATPBetting/REV-THOM-01_fenetres-entrainement-atp.md), qui montre pourquoi des variantes corrélées ne sont pas des confirmations indépendantes. Ce dépôt ne propose pas une méthode distincte à ajouter au catalogue : sa formule ne corrige précisément pas ces problèmes. Il renforce plutôt la nécessité de prouver l’identité de chaque signal et de suivre séparément les résultats de chaque source, par marché, prix et instant de décision.

Pour rendre un tel agrégateur utile à Revue, il faudrait conserver chaque pronostic daté et non modifiable, identifier exactement l’événement/le marché/la ligne, enregistrer le prix disponible chez un bookmaker à cet instant, régler les résultats, mesurer chaque source hors échantillon, puis dédupliquer ou regrouper les sources dépendantes avant tout consensus. Le score combiné devrait être calibré contre une baseline marché; jusque-là, l’interface devrait afficher un décompte d’avis, pas un pourcentage de confiance.

## Vérifications et limites de l’audit

- Checkout propre de `main` au commit indiqué; inventaire des fichiers, lecture statique des chemins de consensus, d’acquisition, d’analyse générée, de l’API et de la configuration.
- `python -m compileall -q backend/app` réussit, mais ne vérifie pas les imports manquants ou le démarrage. Aucun paquet n’a été installé et l’application, les scrapers, les appels API/LLM, les notifications et les tâches planifiées n’ont pas été exécutés.
- Aucun audit exhaustif de sécurité ni vérification des conditions d’utilisation de chaque source n’a été effectué. Les endpoints d’écriture et de synchronisation inspectés ne montrent pas de contrôle d’authentification; vérifier ce point avant toute exposition publique.
- Aucun code, modèle, base de données, donnée ou identifiant API n’a été copié dans Revue.

## Verdict

**À conserver comme exemple d’agrégateur de pronostics et de pièges de consensus, sans reprendre son moteur ni ses scores.** L’interface et le principe de rapprochement multi-source sont les aspects intéressants. Les poids arbitraires, la source bookmaker recomptée comme IA, les motifs inventés et l’absence d’un module central rendent ses recommandations non fiables; le commit audité ne fournit pas de preuve de rentabilité.
