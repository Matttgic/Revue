# Audit — elonbiz/sports-betting-sportsbook

- **Source :** https://github.com/elonbiz/sports-betting-sportsbook
- **Commit examiné :** `a749704d78011d8a1c50e6d018c0e3a76195abfa` (`main`), 2026-08-21, message `feat: updated links`.
- **Date de consultation :** 2026-10-11
- **Licence :** fichiers Apache-2.0 présents dans `backend/`, `frontend/` et `admin/`; pas de licence à la racine. La portée sur les vidéos, captures et autres ressources promotionnelles n’est pas établie.
- **Stack :** React 17 / Create React App, TypeScript 4.7, Node/Express, MongoDB, Socket.IO, intégrations Solana/EVM.
- **But :** vitrine et code partiel de sportsbook avec paris sportifs, portefeuille/paiements et composants casino/Web3.
- **Mon avis :** **je ne le considère pas comme un produit prêt à déployer ni comme une source de méthode de paris.** La présentation commerciale promet trois plateformes « complètes » et « battle-tested », mais le dépôt public ne livre pas le code complet des trois versions, son backend est incomplet, et des risques de sécurité touchent les sessions et l’accès RPC.

## Ce que le dépôt contient

Le README décrit trois offres : un sportsbook crypto BoiBook, une plateforme BetFrenzy avec casino et paiements mobiles, puis un sportsbook décentralisé Azuro. Pourtant, `version-1/`, `version-2/` et `version-3/` contiennent seulement des captures et vidéos. Le code applicatif livré se trouve plutôt sous `frontend/`, `admin/` et un `backend/` incomplet; aucune référence Azuro n’a été trouvée dans le code.

Il s’agit d’un produit d’exploitation et de paiement, pas d’un dépôt de recherche analytique : aucun modèle, algorithme de prévision, backtest, résultat hors échantillon, ROI ou CLV n’est présenté. Je ne retiens donc aucune stratégie pour le catalogue des méthodes Revue.

## Blocages d’exécution visibles dans le dépôt

- `backend/src/index.ts` importe `routes1`, `routes2`, `routes3`, `socket` et `middlewares`, absents du checkout public. Plusieurs contrôleurs importent aussi `src/models`, qui n’est pas livré. Les scripts backend `build`/`start` ne peuvent pas constituer une livraison reproductible avec ces fichiers manquants.
- `admin/src` référence des modules locaux `@core`, `redux` et `assets` absents. Le frontend principal a ses imports internes, mais aucune installation ou compilation des applications n’a été lancée.
- Aucun lockfile npm/yarn/pnpm ni workflow CI n’est versionné. Le dépôt ne contient qu’un test `App.test.js` pour l’admin; il n’y a pas de suite testant les paris, les paiements, les règlements, les sessions ou le backend.
- Un script backend de mise à jour de configuration relève `betLimit` à un milliard pour toutes les devises s’il est exécuté; ne pas le lancer sans décision explicite sur les plafonds financiers.

## Risques de sécurité à traiter avant toute utilisation

- Des clés d’accès de fournisseurs RPC sont codées en dur dans les sources frontend et backend. Le dépôt étant public, les traiter comme exposées : révoquer/renouveler toute clé encore active et les remplacer par des secrets configurés côté serveur avec restrictions d’origine, d’usage et de quota. Les valeurs ne sont pas reproduites ici.
- `backend/.env.example` contient aussi des valeurs non vides ressemblant à des secrets pour les paramètres de session, d’administration et de chiffrement. Si l’une a servi dans un environnement, elle doit être remplacée; un fichier d’exemple ne doit pas fournir d’identifiants utilisables.
- `signAccessToken()` fabrique les jetons d’accès et de renouvellement comme le même MD5 de l’identifiant utilisateur et de l’expiration, sans secret de signature. Ce n’est pas un mécanisme de session robuste; le code d’authentification complet n’étant pas présent, la vérification serveur ne peut pas être auditée de bout en bout.
- La configuration désactive la politique CSP de Helmet, les limites d’API Express sont commentées et Socket.IO accepte toute origine. Pour un service qui gère des soldes et des mises, cela exige une revue de sécurité complète avant exposition.

## Exécution, données et droits

- **Tests/build/démarrage :** non exécutés. L’absence de modules backend et de lockfile rendrait un résultat de build non représentatif du produit annoncé; le dépôt n’a pas été installé ni lancé.
- **Données et prix :** les fournisseurs, l’horodatage exploitable des cotes, leur source historique, le règlement des marchés et la vérification de l’équité des soldes ne sont pas documentés de façon suffisante pour les reproduire.
- **Licence :** Apache-2.0 est explicite dans les trois sous-projets nommés, mais ne couvre pas automatiquement le contenu média ou les ressources sans licence claire. Aucun code ou média n’a été copié dans Revue.
- **Conformité :** une plateforme réelle de jeu d’argent nécessite des autorisations adaptées au pays, aux sports et aux marchés, ainsi que des contrôles de paiement, identité, lutte contre la fraude et jeu responsable; ce dépôt ne démontre pas cette conformité.

## Verdict

**Documenter seulement; ne pas déployer avec de l’argent réel et ne pas utiliser comme preuve d’avantage sportif.** Le dépôt ressemble davantage à une vitrine commerciale assortie de morceaux de frontend/backend qu’à trois plateformes publiques complètes. Avant toute évaluation technique ou achat, exiger la livraison vérifiable de chaque version, ses dépendances verrouillées, des tests de règlement et de paiements, une revue de sécurité indépendante et des preuves de licence/conformité. Aucun élément ne justifie de reprendre du code ou une stratégie de paris dans Revue.

Références : [README](https://github.com/elonbiz/sports-betting-sportsbook/blob/a749704d78011d8a1c50e6d018c0e3a76195abfa/README.md), [entrée backend](https://github.com/elonbiz/sports-betting-sportsbook/blob/a749704d78011d8a1c50e6d018c0e3a76195abfa/backend/src/index.ts), [sessions et jetons](https://github.com/elonbiz/sports-betting-sportsbook/blob/a749704d78011d8a1c50e6d018c0e3a76195abfa/backend/src/controllers/base.ts), [paiements RPC](https://github.com/elonbiz/sports-betting-sportsbook/blob/a749704d78011d8a1c50e6d018c0e3a76195abfa/backend/src/utils/payments.ts), [limite de mises](https://github.com/elonbiz/sports-betting-sportsbook/blob/a749704d78011d8a1c50e6d018c0e3a76195abfa/backend/src/set-bet-limit.ts), [variables d’environnement](https://github.com/elonbiz/sports-betting-sportsbook/blob/a749704d78011d8a1c50e6d018c0e3a76195abfa/backend/.env.example).
