# Revue — Phase 3 : raccordement fiable (10 octobre 2026)

L'interface unique **À jouer / Pourquoi / Bilan** exploite les données
existantes : calendrier, modèles expérimentaux, PulseScore et suivi
prospectif Revue démarré en phase 2, sans importer l'historique SQL source.

## Renforcements

- Prix de recherche rattachés uniquement si ligue, identifiant, deux
  équipes et instant UTC de début concordent.
- Comparaison entre bookmakers limitée à marché, sélection, ligne
  et règle de période identiques. En football 1X2, règle « 90min » exigée.
- Les dix fiches à l'accueil donnent priorité aux rencontres disposant
  de davantage de sources vérifiables. C'est un classement de présentation,
  **pas une prédiction, un avantage de cote ou un pari recommandé**.
- Cotes relevées ≠ cotes actuellement jouables. Profit papier ≠ gain réel.

Contrôles : `tests/test_arcade_v3_phase3_guardrails.js` dans
`.github/workflows/arcade-v3-tests.yml`.

## Reste à faire pour la vraie parité Clairvoyance

Sorties mathématiques sur **les mêmes données et au même instant** ;
accès licite aux données complètes ; marchés et règles comparables ;
suivi prospectif suffisant pour calibrer les modèles ; règlements officiels.
Les 44/44 fonctions du catalogue de tests ne représentent pas
100 % de la reproduction du produit.
