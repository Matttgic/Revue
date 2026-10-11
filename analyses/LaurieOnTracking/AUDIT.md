# Revue ciblée — Friends-of-Tracking-Data-FoTD/LaurieOnTracking

**Avis : Très formateur pour les mécanismes du jeu ; besoin de données élevé.**

- Source demandée : https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking
- URL résolue : https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking
- Version examinée : [`7ed3ff857940d3f4611be55f3c08c79525c32171`](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking/tree/7ed3ff857940d3f4611be55f3c08c79525c32171) ; branche `master`.
- Consultation : 2026-10-11.
- Famille : Football · tracking et contrôle spatial ; stack : Python.
- Priorité de recherche : **P3** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **MIT pour le code ; données Metrica externes** ([texte à cette version](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking/blob/7ed3ff857940d3f4611be55f3c08c79525c32171/LICENSE)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Tutoriels de vitesses, contrôle du terrain et valeur attendue de possession sur données Metrica.
- Le modèle calcule un temps d’interception puis une probabilité de contrôle ; paramètres de réaction, vitesse du ballon et avantage gardien explicites.
- Les valeurs par défaut incluent un temps de réaction de 0,7 seconde et une vitesse de ballon de 15 m/s.

## Limites et points à contrôler

- Ces constantes ne sont pas une calibration garantie pour chaque championnat.
- Le tracking du match cible serait une fuite pour un modèle pré-match ; en live, disponibilité et latence des observations deviennent décisives.
- Les exemples Metrica ne constituent pas une base de tracking exhaustive pour parier.

## Enseignement pour Revue

Étudier les concepts avant d’investir dans le tracking ; commencer par les événements disponibles et tester un apport indépendant.

**Comparaison avec le catalogue :** Complète socceraction par la position des joueurs hors ballon ; priorité inférieure aux données et cotes de base.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Modèle de contrôle spatial lu ; vidéos, données Metrica et calculs non exécutés.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking/blob/7ed3ff857940d3f4611be55f3c08c79525c32171/README.md)
- [Metrica_PitchControl.py](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking/blob/7ed3ff857940d3f4611be55f3c08c79525c32171/Metrica_PitchControl.py)
- [Metrica_EPV.py](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking/blob/7ed3ff857940d3f4611be55f3c08c79525c32171/Metrica_EPV.py)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
