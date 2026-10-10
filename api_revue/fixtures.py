"""Independent read-only NHL/MLB fixture adapter for the Clairvoyance API project.

NOT a wholesale port of Clairvoyance. Uses Revue observations and publishes
a compatible *field set* where possible, while documenting where actual
source database rows / time of observation / status are not equivalent.
Reject stale snapshots, malformed dates, mixed team identity and phantom odds.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any


class SourceUnavailable(Exception):
    pass


def timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Date missing")
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid date") from exc
    if t.tzinfo is None:
        raise ValueError("Timezone required")
    return t.astimezone(timezone.utc)


def snapshot(path: Path, now: datetime, *, max_age_hours: int = 8) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        instant = timestamp(data["generated_at_utc"])
        if (not isinstance(data, dict) or instant > now or
                now - instant > timedelta(hours=max_age_hours)):
            raise SourceUnavailable("No recent verified source snapshot")
        return data
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise SourceUnavailable(f"Source file missing / malformed: {path.name}") from exc


def _correct_score(row: dict, score: dict) -> bool:
    try:
        return (
            row["league"] == score["league"] and
            str(row["event_id"]) == str(score["event_id"]) and
            row["home"] == score["home"] and
            row["away"] == score["away"] and
            timestamp(row["start_utc"]) == timestamp(score["kickoff_utc"]) and
            score["state"] in ("final", "in_progress") and
            timestamp(score["observed_at_utc"]) >= timestamp(row["start_utc"]) and
            type(score["home_score"]) is int and
            type(score["away_score"]) is int and
            0 <= score["home_score"] <= 500 and
            0 <= score["away_score"] <= 500
        )
    except (KeyError, ValueError, TypeError):
        return False


def fixture_rows(doc: dict, scores: dict | None, league: str,
                 day: date, now: datetime, *,
                 reference_ids: dict | None = None,
                 require_original_espn_id: bool = False) -> list[dict]:
    """One event is sourced from a dated ESPN/NHL fixture, not from an invented pick."""
    if league not in ("MLB", "NHL"):
        raise ValueError("Only source-backed NHL and MLB adapters")
    if not isinstance(day, date) or now.tzinfo is None:
        raise ValueError("Aware now / date required")
    comp = (doc.get("competitions") or {}).get(league)
    if not isinstance(comp, dict):
        raise SourceUnavailable("Requested league's fixture source is unavailable")
    candidates = list(comp.get("games") or [])
    if not isinstance(scores, dict):
        scores = {}
    # Final score snapshots are at most two hours old; they cannot be
    # silently transformed into a live service when the provider is stale.
    try:
        scores_at = timestamp(scores["generated_at_utc"])
        usable_scores = (scores.get("status") == "observed_scoreboard_not_streaming"
                         and now - timedelta(hours=2) <= scores_at <= now)
    except (ValueError, KeyError, TypeError):
        usable_scores = False
    observed = {
        (event.get("league"), str(event.get("event_id"))): event
        for event in scores.get("events") or [] if usable_scores and
        isinstance(event, dict)
    }
    matches = {}
    if league == "NHL" and isinstance(reference_ids, dict):
        if reference_ids.get("status") == "verified_fixture_identity_pairs":
            for pair in reference_ids.get("mappings") or []:
                key = str(pair.get("nhl_game_id"))
                if key in matches:
                    raise SourceUnavailable("Ambiguous cross-provider ESPN identifiers")
                matches[key] = pair
    if league == "NHL" and require_original_espn_id and not matches:
        raise SourceUnavailable("Verified original ESPN identifiers unavailable")
    results = []
    ids: set[str] = set()
    for raw in candidates:
        try:
            game_id = str(raw["event_id"])
            kickoff = timestamp(raw["start_utc"])
            home, away = raw["home"], raw["away"]
            if (not isinstance(home, str) or not home or
                not isinstance(away, str) or not away or home == away or
                not game_id.isdecimal() or int(game_id) > 2**63 - 1 or
                kickoff.date() != day):
                continue
            if game_id in ids:
                raise SourceUnavailable(f"Repeated event ID {league}/{game_id}")
            ids.add(game_id)
            reference_espn = game_id
            if league == "NHL":
                pair = matches.get(game_id)
                if pair is not None:
                    if (pair.get("home") != home or pair.get("away") != away or
                        timestamp(pair.get("start_utc")) != kickoff or
                        not str(pair.get("original_espn_id", "")).isdecimal()):
                        raise SourceUnavailable("Inconsistent original ESPN / NHL fixture identity")
                    reference_espn = str(pair["original_espn_id"])
                elif require_original_espn_id:
                    raise SourceUnavailable("No exact source ESPN identity for NHL game")
            score = observed.get((league, game_id))
            status = "STATUS_SCHEDULED"
            home_score = away_score = None
            if score and _correct_score({**raw, "league": league}, score):
                status = {
                    "final": "STATUS_FINAL", "in_progress": "STATUS_IN_PROGRESS",
                }[score["state"]]
                home_score = score["home_score"]
                away_score = score["away_score"]
            # Source internal SQL primary keys do not exist here. Revue owns an
            # explicitly DIFFERENT numeric identifier derived from ESPN ID.
            # This is field-compatible, not DB-identity compatible.
            results.append({
                "id": int(reference_espn),
                "espn_id": reference_espn,
                "game_date": kickoff.date().isoformat(),
                "game_time_utc": kickoff.isoformat(),
                "status": status,
                "home_team": home,
                "away_team": away,
                "home_score": home_score,
                "away_score": away_score,
                "home_moneyline": None,
                "away_moneyline": None,
                "over_under": None,
                **({
                    "home_pitcher": None, "away_pitcher": None, "venue": None,
                } if league == "MLB" else {}),
            })
        except (ValueError, TypeError, KeyError):
            continue
    return sorted(results, key=lambda x: (x["game_time_utc"], x["espn_id"]))


def fixtures_from_files(root: Path, league: str, day: date,
                        now: datetime) -> list[dict]:
    doc = snapshot(root / "multisports-latest.json", now)
    if doc.get("status") not in ("prototype_non_calibre", "experimental_not_calibrated"):
        # Revue's own feed currently uses a research status, which has no
        # effect on the independently observed match schedule.
        raise SourceUnavailable("Unsupported Revue fixture feed status")
    try:
        scores = snapshot(root / "scoreboard-revue-latest.json", now, max_age_hours=2)
    except SourceUnavailable:
        scores = None
    reference = None
    if league == "NHL":
        reference = snapshot(root / "parite-nhl-espn-id-map.json", now, max_age_hours=72)
    return fixture_rows(doc, scores, league, day, now,
                        reference_ids=reference,
                        require_original_espn_id=(league == "NHL"))
