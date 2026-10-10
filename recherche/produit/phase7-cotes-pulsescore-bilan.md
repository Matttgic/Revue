# Phase 7 — Cotes PulseScore et bilan papier

**But** : séparer strictement les marchés observés via les bookmakers français,
les rapprochements avec les prévisions Clairvoyance observées en phase 6 et les
performances de la simulation de Revue. Aucun ancien pari Clairvoyance n'est
utilisé pour gonfler le rendement.

## Contrôles

- Lecture des *snapshots PulseScore préexistants* : bookmaker français connu,
  événement, équipes, identifiant, début exact, prix décimal fini,
  horodatage de la cote et origine de l'horodatage.
- Rapprochement Phase 6 **même ID + domicile/extérieur + coup d'envoi
  à 5 minutes + marché, côté et ligne**. Les cotations doivent avoir été
  observées dans les 30 minutes précédant le verrouillage pour prétendre
  être pertinentes à ce moment ; une cote plus ancienne reste historique.
- NHL : les périodes incluant les prolongations sont non démontrées dans
  le radar actuel. L'indicateur \`90min\` dérivé du modèle football n'est
  pas à lui seul une preuve des règles du bookmaker.
- **Aucune cote actuelle jouable ou EV+ garantie** : une archive PulseScore
  n'est pas une offre en cours, les modèles ne sont pas calibrés et les
  règles source ne sont pas prouvées.
- Bilan papier *recalculé depuis chaque pari individuel* : vérification
  des cotes figées et dates pré-match, des statuts, des mises unitaires,
  des montants gagnés/perdus et cohérence avec le total du hub.
  Les exclusions et les matchs en attente sont distincts du ROI.
- Aucun appel API payant, aucune mutation des registres existants,
  aucun véritable pari ou autre opération sur un compte bookmaker.
  Le CFB est exclu.

**Exécuter** : \`python -m outils.phase7_cotes_et_bilan\`

**Tester** : \`python -m unittest discover -s tests -p test_phase7_cotes_et_bilan.py -v\`

Automatisation : workflow \`phase7-cotes-et-bilan.yml\`, quatre fois par jour
plus déclenchement à chaque changement de code, validation sans API externe.

## Limites restantes

Le radar est un observateur horodaté, pas un moteur de réservation de prix
chez les bookmakers. Pour une vérification authentique d'un marché précis,
il faudrait des métadonnées de période vérifiées directement chez le
fournisseur, une observation suffisamment proche d'une décision figée
avant match et des probabilités préalablement calibrées. La phase 7 ne
peut donc revendiquer ni rentabilité, ni EV+ exploitable.
