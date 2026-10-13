"""Manually authorized PMU probe, one attempt, aggregated private validation.

Disabled by default. Fresh public NHL/ESPN references before any PulseScore call.
No odds, IDs, names, arbitrary field names or provider responses are persisted.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path

from outils.collecte.check_pulsescore_connection import KEYS
from outils.collecte.diagnostic_nhl_player_matching import summarize
from outils.collecte.diagnostic_nhl_pmu_structure import diagnose as probe, identifier
from outils.collecte.nhl_player_matching import name_key, team_code
from outils.collecte.diagnostic_nhl_identity_structure import (
    NAME_FIELDS, field_stats, observe_fields, candidate_evidence)
from outils.collecte.pulsescore_v2 import league_matches
from outils.suivi.revue_engine_v2 import timestamp

EVENT_FIELDS = ("home", "away", "startTime", "eventId", "startDate", "start")
SELECTION_FIELDS = ("rawName", "team", "playerId", "name", "playerName", "participantName")
GROUPS = ("names", "teams", "dates", "missing_data", "identifiers", "ambiguity", "other")


def rejection_groups(report):
    """Fixed groups from explicit failure reasons, not speculative corrections."""
    result = dict.fromkeys(GROUPS, 0)
    for reason, count in report["reasons"].items():
        if reason == "unique_identity":
            continue
        if reason in ("multiple_events", "multiple_players", "duplicate_player_id"):
            group = "ambiguity"
        elif reason in ("team_conflict", "event_team_conflict"):
            group = "teams"
        elif reason in ("invalid_event_date", "event_date_mismatch"):
            group = "dates"
        elif reason in ("missing_player_identity", "invalid_observation", "missing_event_context", "event_not_found"):
            group = "missing_data"
        elif reason in ("event_id_conflict", "invalid_provider_id", "player_evidence_conflict"):
            group = "identifiers"
        elif reason in ("player_not_found", "invalid_player_name"):
            group = "names"
        else:
            group = "other"
        result[group] += count
    return result


def analyze_payload(payload, profiles, fixtures):
    from outils.collecte.diagnostic_nhl_label_formats import analyze_formats
    matching = summarize(payload, profiles, fixtures)
    players = [p for group in profiles.get("teams", {}).values() if isinstance(group, list)
               for p in group if isinstance(p, dict)]
    identity = {"market": {f: field_stats() for f in NAME_FIELDS},
                "selection": {f: field_stats() for f in NAME_FIELDS}}
    audit = {"eligible_events": 0, "selection_objects": 0, "market_objects": 0,
             "market_selection_cardinality": {"zero": 0, "one": 0, "many": 0, "invalid": 0},
             "identity_candidates": identity,
             "label_formats": analyze_formats(payload, profiles),
             "event_fields_present": dict.fromkeys(EVENT_FIELDS, 0),
             "event_fields_valid": dict.fromkeys(EVENT_FIELDS, 0),
             "selection_fields_present": dict.fromkeys(SELECTION_FIELDS, 0),
             "selection_fields_valid": dict.fromkeys(SELECTION_FIELDS, 0),
             "selections_missing_name": 0, "selections_missing_team": 0,
             "selections_unknown_team": 0, "events_missing_date": 0,
             "events_invalid_date": 0, "events_unknown_teams": 0,
             "contract_status": "not_observed"}
    if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
        return {"counts": matching, "schema": audit}
    for event in payload["events"]:
        if not isinstance(event, dict) or not isinstance(event.get("league"), str) or not league_matches(event["league"], "", "NHL"):
            continue
        markets = event.get("markets")
        if not isinstance(markets, list):
            continue
        eligible = [m for m in markets if isinstance(m, dict)
                    and m.get("canonicalMarket") == "ANYTIME_GOALSCORER" and m.get("period") == "FULL_TIME"]
        if not eligible:
            continue
        audit["eligible_events"] += 1
        for field in EVENT_FIELDS:
            audit["event_fields_present"][field] += field in event
            valid = (timestamp(event.get(field)) is not None if field in ("startTime", "startDate", "start") else
                     identifier(event.get(field)) if field == "eventId" else bool(team_code(event.get(field))))
            audit["event_fields_valid"][field] += valid
        audit["events_missing_date"] += event.get("startTime") is None
        audit["events_invalid_date"] += event.get("startTime") is not None and timestamp(event.get("startTime")) is None
        audit["events_unknown_teams"] += not team_code(event.get("home")) or not team_code(event.get("away"))
        for market in eligible:
            audit["market_objects"] += 1
            observe_fields(market, identity["market"])
            selections = market.get("selections")
            cardinality = ("invalid" if not isinstance(selections, list) else
                           "zero" if not selections else "one" if len(selections) == 1 else "many")
            audit["market_selection_cardinality"][cardinality] += 1
            if not isinstance(selections, list):
                continue
            for selection in selections:
                if not isinstance(selection, dict):
                    continue
                audit["selection_objects"] += 1
                observe_fields(selection, identity["selection"])
                candidate_evidence(event, market, selection, players, fixtures.get("games", []), identity)
                for field in SELECTION_FIELDS:
                    audit["selection_fields_present"][field] += field in selection
                    valid = identifier(selection.get(field)) if field == "playerId" else bool(name_key(selection.get(field)))
                    audit["selection_fields_valid"][field] += valid
                audit["selections_missing_name"] += not bool(name_key(selection.get("rawName")))
                audit["selections_missing_team"] += selection.get("team") is None
                audit["selections_unknown_team"] += selection.get("team") is not None and not team_code(selection.get("team"))
    n = audit["selection_objects"]
    if n:
        valid_events = all(audit["event_fields_valid"][f] == audit["eligible_events"] for f in ("home", "away", "startTime"))
        audit["contract_status"] = ("structurally_observed" if valid_events
            and audit["selection_fields_valid"]["rawName"] == matching["selections"] else "partial_or_incompatible")
    matching["rejection_groups"] = rejection_groups(matching)
    if matching["status"] == "analyzed_unvalidated_provider_contract":
        matching["status"] = ("analyzed_observed_contract" if audit["contract_status"] == "structurally_observed"
                              else "analyzed_partial_contract")
    # Explicitly structural: alternative name fields are counted but never used
    # as fallback without validation. Successful exact reference matches supply
    # identity evidence; merely having a rawName field does not.
    return {"counts": matching, "schema": audit}


def refresh_references(now):
    # Reuse collection functions only. No probabilities recalculated or written.
    from modeles.simulations.nhl_independant import download_season, season_code
    from modeles.simulations.nhl_joueurs_independant import _fetch_espn_stats
    from outils.collecte.nhl_espn_goalies import CODES
    season = season_code(now.date())
    schedule = download_season(season)
    games = [{"event_id": g.id, "home": g.home, "away": g.away, "start_utc": g.start_utc.isoformat()}
             for g in schedule if now-timedelta(days=1) <= g.start_utc <= now+timedelta(days=14)]
    clubs = {g[side] for g in games for side in ("home", "away")}
    if not clubs:
        raise ValueError("no_fixtures")
    espn_clubs = clubs | {alias for alias, code in CODES.items() if code in clubs}
    rows, metadata = _fetch_espn_stats(int(season), espn_clubs)
    if metadata.get("errors") or not metadata.get("teams_mapped") or metadata.get("pages_attempted", 0) > 12:
        raise ValueError("partial_profiles")
    teams = {club: [] for club in clubs}
    for row in rows:
        codes = sorted({CODES.get(c, c) for c in row.get("teamAbbrevs", "").split()})
        # Multi-team seasonal rows are not evidence of a current roster team.
        if len(codes) != 1 or codes[0] not in clubs:
            continue
        if not name_key(row.get("skaterFullName")) or not identifier(row.get("playerId")):
            continue
        teams[codes[0]].append({"player_id": str(row["playerId"]), "name": row["skaterFullName"],
                               "team": codes[0], "current_team_observed": True})
    if any(not players for players in teams.values()):
        raise ValueError("incomplete_clubs")
    stamp = now.isoformat()
    return ({"generated_at_utc": stamp, "teams": teams}, {"generated_at_utc": stamp, "games": games})


def run(*, authorized=False, key=None, fetch=None, reference_loader=refresh_references, now=None):
    result = {"status": "disabled", "calls": 0, "max_calls": 1,
              "selections_analyzed": None, "real_match_rate": None}
    if not authorized:
        return result
    if not key:
        return {**result, "status": "missing_secret"}
    now = now or datetime.now(timezone.utc)
    try:
        profiles, fixtures = reference_loader(now)
        for source in (profiles, fixtures):
            stamp = timestamp(source.get("generated_at_utc"))
            if stamp is None or not 0 <= (now-stamp).total_seconds() <= 3600:
                raise ValueError("stale_reference")
        teams, games = profiles.get("teams"), fixtures.get("games")
        if (not isinstance(teams, dict) or not teams or not isinstance(games, list) or not games
                or any(not isinstance(v, list) or not v for v in teams.values())):
            raise ValueError("empty_reference")
    except Exception:
        # No source exception bodies or URLs in logs/artifacts.
        return {**result, "status": "reference_refresh_failed"}
    report = probe(key, fetch, references=(profiles, fixtures))
    result.update(status=report["status"], calls=report["calls"], diagnostic=report,
                  reference_players=sum(len(v) for v in profiles["teams"].values()),
                  reference_games=len(fixtures["games"]))
    if "matching" in report:
        counts = report["matching"]["counts"]
        result.update(selections_analyzed=counts["selections"], real_match_rate=counts["match_rate"])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorize-one-call", action="store_true")
    args = parser.parse_args()
    key = next((os.getenv(k) for k in KEYS if os.getenv(k)), None)
    report = run(authorized=args.authorize_one_call, key=key)
    Path("/tmp/nhl-pmu-matching-validation.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(f"PMU matching validation status={report['status']}; calls={report['calls']}/1")


if __name__ == "__main__":
    main()
