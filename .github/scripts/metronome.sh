#!/usr/bin/env bash
# Usage : metronome.sh <durée en minutes>
# Minute 0 puis toutes les 60 min : radar ; toutes les 120 min : relevé complet ;
# minute 30 puis toutes les 180 min : prédictions multisports (radar et relevé
# refusent des prédictions de plus de 6 h).
set -u
duration=${1:?durée en minutes}
for ((minute = 0; minute < duration; minute++)); do
  if (( minute % 60 == 0 )); then
    gh workflow run pulsescore-radar-6h.yml --ref main || echo "radar : relance refusée"
  fi
  if (( minute % 120 == 0 )); then
    gh workflow run revue-engine-v2.yml --ref main || echo "relevé complet : relance refusée"
  fi
  if (( minute % 180 == 30 )); then
    gh workflow run multisports-independent.yml --ref main || echo "prédictions : relance refusée"
  fi
  sleep "${METRONOME_SLEEP_SECONDS:-60}"
done
