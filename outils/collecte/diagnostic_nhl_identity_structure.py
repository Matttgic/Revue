"""Aggregate candidate evidence only: no provider contract or fallback inferred."""
from outils.collecte.nhl_player_matching import name_key, match_selection

# Fixed allowlist; unknown keys and all values stay in memory. Absence of a hit
# here cannot establish that a provider has no identity elsewhere in its schema.
NAME_FIELDS = ("rawName", "name", "playerName", "participantName", "label", "title")
TYPES = ("null", "string", "boolean", "number", "object", "array", "other")


def field_stats():
    return {"present": 0, "types": dict.fromkeys(TYPES, 0), "nonempty_name_key": 0,
            "candidate_selections": 0, "matched": 0, "ambiguous": 0,
            "impossible": 0, "reasons": {}}


def observe_fields(record, stats):
    for field, counter in stats.items():
        if field not in record:
            continue
        value = record[field]
        kind = ("null" if value is None else "string" if isinstance(value, str)
                else "boolean" if isinstance(value, bool) else "number" if isinstance(value, (int, float))
                else "object" if isinstance(value, dict) else "array" if isinstance(value, list) else "other")
        counter["present"] += 1
        counter["types"][kind] += 1
        counter["nonempty_name_key"] += bool(name_key(value))


def candidate_evidence(event, market, selection, players, games, stats):
    for level, record in (("market", market), ("selection", selection)):
        for field in NAME_FIELDS:
            if not name_key(record.get(field)):
                continue
            counter = stats[level][field]
            # Only change the candidate name. Keep event, selection team and ID
            # constraints; do not silently transfer market IDs/teams to selections.
            observation = {"bookmaker": "pmu_fr", "canonical_market": market["canonicalMarket"],
                "period": market["period"], "home": event.get("home"), "away": event.get("away"),
                "start_utc": event.get("startTime"), "provider_event_id": event.get("eventId"),
                "name": record[field], "team": selection.get("team"),
                "provider_player_id": selection.get("playerId")}
            match = match_selection(observation, players, games)
            counter["candidate_selections"] += 1
            counter[match.status] += 1
            counter["reasons"][match.reason] = counter["reasons"].get(match.reason, 0) + 1
