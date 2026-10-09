# Revue — Tennis ATP/WTA, UFC et Liiga

**Date : 2026-10-09.** Modules originaux sans recopie de code du tiers.

## Code et exécution
- [Flux et modèles tennis, UFC, Liiga](sports_individuels_et_liiga.py)
- [Tests sans réseau](../../tests/test_sports_individuels_et_liiga.py)
- [Dernières rencontres et pronostics conditionnels](../../docs/individual-latest.json)
- [Cache historique des rencontres / résultats](../../docs/individual-history.json)
- [GitHub Actions](../../.github/workflows/multisports-independent.yml)

## Ce qui a été testé
Le workflow GitHub Actions du 9 octobre 2026 a interrogé avec succès les flux ESPN ATP, WTA, UFC et TENNIS (non identifié) et l'API publique Liiga. Lors du calcul de 15:33 UTC, les flux ont retourné 24 futurs matchs WTA, 12 combats UFC et 6 matchs Liiga. Seule la **Liiga avait un modèle pouvant afficher six probabilités** avec l'historique reçu. Il ne s'agit **pas** d'une preuve de fiabilité.

**Tennis :** conservation des matches dont le vainqueur est réellement présent dans la source ESPN, apprentissage Elo chronologique entre joueurs, mais absence de probabilité si historique insuffisant. Le circuit non identifié est conservé sans ATP/WTA inventé et les doublons connus sont écartés. La méthode **RUTS SAFE** (rang + UTR) ne change pas, ce module n'utilise ni UTR ni rang vérifiés.

**UFC :** historique officiel de combats ESPN ; Elo chronologique si suffisamment de résultats. Une baseline alternative fondée sur des bilans de carrière peut être calculée uniquement si le fournisseur fournit effectivement et clairement les bilans des deux combattants (>=6 combats chacun), sans la présenter comme fiable. Au premier run, ESPN n'a pas fourni de bilans utilisables sur les combats futurs, donc **zéro probabilité UFC**, même si le calendrier est affiché.

**Liiga :** API publique `www.liiga.fi/api/v2/games?tournament=runkosarja&season=YYYY`, 544 rencontres pour 2026-27 au run examiné. On estime Elo + moyenne attaque/défense lissée et probabilités de buts sous Poisson. Règles de shootout/sans tirs au but pour les totaux. Les matchs démarrés sont exclus.

## Limites
- Aucun classement UTR, aucune donnée de blessures, surface tennis ou style d'adversaire : ne pas utiliser le modèle comme prédiction de niveau professionnel fiable.
- Les résultats d'une saison sportive passée ne doivent pas être mis à disposition comme s'ils étaient pré-match : les historiques d'évolution des cotes exigent des snapshots horodatés.
- Les paris disponibles en France doivent être contrôlés séparément via la réglementation ANJ ; ne pas utiliser les marchés/compétitions d'autres juridictions par défaut.
- Pas de bookmaker, cote, EV ni mise recommandée. Aucune rentabilité démontrée.
- Conditions et droits des sources ESPN/Liiga à contrôler avant toute utilisation commerciale et redistribution. L'accès HTTP public ne garantit pas un droit de réutilisation.

## Étapes suivantes
Tests walk-forward par sport et surface/marché ; validation hors échantillon des probabilités ; données UTR + rang quand elles sont légalement disponibles ; sources de gardiens/compositions confirmées ; cotations françaises comparables, suivies de Brier, log loss, CLV et ROI réel.
