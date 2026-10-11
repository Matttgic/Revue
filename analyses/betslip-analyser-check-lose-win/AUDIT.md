# Audit — kennysmithderulo-cmyk/betslip-analyser-check-lose-win

- **Projet :** https://github.com/kennysmithderulo-cmyk/betslip-analyser-check-lose-win
- **Auteur :** kennysmithderulo-cmyk
- **Commit audité :** `18050f4693952297a6487721d9c86cc4cd29f893` (`main`, 11/10/2026)
- **Licence :** aucun fichier `LICENSE`/`COPYING`; `private: true` dans `package.json` n’est pas une licence. **Aucun code tiers copié.**
- **Stack :** HTML/CSS/JavaScript statique avec Vite; une version React distincte est aussi présente dans `src/`.
- **Tests et build :** aucun script de test (`npm test` absent). `npm ci --ignore-scripts --no-audit --no-fund` puis `npm run build` réussissent; cela vérifie seulement la compilation.
- **Données et moteur :** aucun dataset, OCR, modèle, calcul statistique, serveur ou API d’analyse de paris trouvé.

## Ce que l’application fait réellement

L’entrée Vite est le `index.html` à la racine. Il affiche un formulaire et prévisualise une image avec `FileReader`, mais ne lit pas son contenu. Les champs de cote, mise, code de pari et équipes ne sont pas transmis à un moteur d’analyse. Les libellés « marge », « forme », « modèle », « Kelly » et « 11 facteurs » ne correspondent pas à des calculs implémentés.

Au clic, le code attend quelques secondes puis utilise `Math.random()` pour fabriquer le pourcentage de chances, la « valeur », le risque, la mise Kelly et le verdict gagnant/perdant. Ce résultat ne dépend ni de l’image ni des données saisies, à l’exception de l’affichage de la cote et de la mise.

`src/App.jsx` est une seconde interface React, non montée par la page racine; elle produit elle aussi des sorties aléatoires. Elle ne constitue pas un moteur de secours.

## Risques importants

1. **Résultats inventés présentés comme conseils.** La page promet qu’une IA lit un ticket SportyBet et estime s’il va gagner ou perdre; le code fourni n’effectue aucune lecture ni prédiction. Les conseils « stake »/« avoid », les pourcentages et EV sont pseudo-aléatoires et ne doivent pas guider une mise.
2. **Paiements sans vérification serveur visible.** La page charge le SDK Paystack et affiche des offres en GHS. Le callback du navigateur active Premium et augmente un solde dans `localStorage`; aucun backend n’est fourni pour vérifier côté serveur la référence, le statut et le montant réglé. L’état local est modifiable par l’utilisateur. L’audit n’a pas déclenché de paiement et ne peut pas confirmer l’état du compte marchand.
3. **Entrées utilisateur injectées dans du HTML.** Le code concatène notamment le booking code et les champs saisis dans `innerHTML` sans échappement. Une valeur HTML/JavaScript spécialement construite peut s’exécuter dans l’origine du site.
4. **Fonctions d’affiliation non établies.** Le code génère un identifiant local et affiche « Share & Earn »/un solde; aucun service de suivi ou de paiement d’affiliation n’est inclus.
5. **Licence absente.** Pas de réutilisation ou redistribution du code.

## Vérifications

| Critère | Résultat |
|---|---|
| Recherche du ticket / OCR | absent; image affichée seulement |
| Modèle ou source de données de paris | absent |
| Résultat de l’analyse | aléatoire (`Math.random()`) |
| Tests automatisés | aucun script de test |
| Build Vite | réussi, compilation seulement |
| Backend pour historique, premium, paiement ou affiliation | absent |
| Performance de paris / ROI / validation prospective | aucune |

## Verdict

**Rejeté comme analyseur ou stratégie de paris** et classé dans [les archives Revue](../../archives/REV-KENNY-01_betslip-analyser-demo.md). C’est au mieux une maquette d’interface; les conclusions et conseils affichés ne sont pas fondés sur le ticket. L’intégration se limite à documenter le dépôt dans ce dossier propre, sans ajouter une méthode inexistante à l’index des stratégies.
