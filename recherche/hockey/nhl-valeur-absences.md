# REV-CLAIR-07 — NHL : valorisation prudente des joueurs absents

**Statut : À étudier.** Source : https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/_nhl_skaters.py

## Idée
Estimer le niveau attendu du joueur blessé en points/match avec une régularisation vers sa saison précédente, plutôt que prendre les dernières rencontres au pied de la lettre.

La source utilise un coefficient de lissage lié au nombre de matchs (exemple : `K=20`) et une valeur de remplacement par groupe de poste (attaquant/défenseur). Elle refuse les identités ambiguës et ignore les cas qu'elle ne peut résoudre.

## Réimplémentation et limites
- Formule générique de lissage : `niveau=(points_actuels + K×niveau_antérieur)/(matchs_actuels+K)`.
- Tester des valeurs de K sur jeux d'entraînement, jamais en regardant le ROI final.
- Mesurer la **valeur marginale sur la production de l'équipe**, pas assimiler points/match à valeur totale; défense, PK, faceoffs et rôle PP peuvent changer le signal.
- Vérifier état réel de l'absence / heure de publication de la blessure ; ne pas inventer de temps de jeu.
- Distinction joueur absent / promotion de son coéquipier / changement de ligne et de power play.

**Verdict :** composant de feature engineering pertinent pour modélisation NHL, mais pas un modèle de buteur autonome.
