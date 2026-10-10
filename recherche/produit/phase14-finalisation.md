# Phase 14 — Produit Revue prêt à être utilisé en mode recherche

Revue conserve **trois entrées publiques** : À JOUER, POURQUOI et BILAN ;
tous les outils historiques restent au Lab. Un encart gaming commun rappelle
le statut des sources et distingue **matchs à analyser**, **simulations papier**
et **prévisions prospectives de modèles**. Les détails techniques encombrants
de l'accueil sont repliés par défaut, sans suppression des données.

`outils/phase14_reception.py` produit
`docs/phase14-readiness-latest.json` en contrôlant hors ligne :
- HTML primaire : navigation identique, mobile, assets relatifs présents ;
- inventaire des matchs : aucun pari certifié / aucune cote jouable ;
- portefeuille fictif : gagnés/perdus/remboursés/en attente/exclus et ROI
  recalculés depuis **les seules entrées réglées** ;
- prévisions de modèles : compte aligné sur les règlements ESPN/NHL réels ;
- marchés NHL sans règle vérifiée : toujours exclus ;
- absence de calibration démontrée, d'accès aux SQL privés Clairvoyance,
  d'EV réelle et de paris réels ;
- fraîcheur des snapshots : avis si une source devient périmée, sans
  fabriquer une recommandation.

Le navigateur bloque l'affichage d'un statut opérationnel positif si le
rapport est trop vieux, si les comptes ou règles sont incompatibles ou si
les données ne sont pas vérifiées.

Les tests statiques et adversariaux tournent dans le workflow
`Revue - Phase 14 Finalisation Produit` ; GitHub Pages effectue **à part**
un smoke test HTTP des pages et ressources publiées.

**Important** : projet utilisable en mode exploration et statistiques,
mais modèle non calibré indépendamment sur un échantillon suffisant.
Ce n'est pas une reproduction exacte 100 % Clairvoyance et aucun rendement
financier n'est démontré. Le produit peut être livré techniquement sans
mentir sur ces limites ni changer les prévisions déjà verrouillées.
