#!/usr/bin/env bash
# Étape « Ignored Build Step » de Vercel (vercel.json → ignoreCommand).
# Code de sortie 0 = déploiement ignoré ; 1 = déploiement lancé.
# Les robots publient des centaines de commits de données par jour, alors que
# le quota gratuit Vercel est de 100 déploiements par jour : on ne redéploie
# l'API que si son code ou un fichier de données qu'elle lit a changé.
# En cas de doute (pas de commit parent, erreur git), on déploie.
set -u
API_PATHS=(
  api api_revue requirements.txt vercel.json
  docs/engine-v2-latest.json docs/engine-v2-ledger.json docs/github-workflows-latest.json
  docs/health-latest.json docs/match-center-latest.json docs/match-dossiers-latest.json
  docs/moneypuck-nhl-latest.json docs/multisports-history.json docs/multisports-latest.json
  docs/nhl-clairvoyance-shadow-latest.json docs/nhl-official-stats-latest.json
  docs/parite-nhl-espn-id-map.json docs/reproduction-exacte-audit.json
  docs/scoreboard-revue-latest.json
)
git rev-parse --verify -q HEAD^ >/dev/null || exit 1
git diff --quiet HEAD^ HEAD -- "${API_PATHS[@]}"
status=$?
if [ "$status" -eq 0 ]; then echo "Aucun changement pour l'API : déploiement ignoré"; exit 0; fi
if [ "$status" -eq 1 ]; then echo "Changement pour l'API : déploiement"; exit 1; fi
exit 1
