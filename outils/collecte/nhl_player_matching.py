"""Conservative identity matching, independent of odds/pricing and sport models.

Inputs are normalized private observations, not an assumed provider schema.
An accepted identity does not establish lineup eligibility or settlement rules.
"""
from dataclasses import dataclass
import unicodedata

from outils.suivi.revue_engine_v2 import NHL_FULL, timestamp


def name_key(value):
    if not isinstance(value, str):
        return ""
    text = unicodedata.normalize("NFKD", value.casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    # Apostrophes/hyphens may be omitted in provider spellings; do not drop
    # initials, suffixes or arbitrary words, and never perform fuzzy matching.
    return "".join(c for c in text if c.isalnum())


def team_code(value):
    key = name_key(value)
    candidates = {code for code, full in NHL_FULL.items()
                  if key and key in (name_key(code), name_key(full))}
    return next(iter(candidates)) if len(candidates) == 1 else None


@dataclass(frozen=True)
class Match:
    status: str  # matched / ambiguous / impossible
    reason: str
    player_id: str | None = None
    event_id: str | None = None


def match_selection(observation, players, games, *, aliases=None, player_crosswalk=None,
                    event_crosswalk=None):
    """Crosswalks must be explicitly verified by the caller, namespaced by PMU.

    aliases maps ESPN IDs to curated names. Crosswalks map PMU IDs to ESPN/NHL
    IDs. Never equate identical number strings across providers implicitly.
    Exact home/away and an aware start within 15 minutes are mandatory even
    when a verified event ID exists. Conflicting supplied evidence is rejected.
    """
    reject = lambda reason: Match("impossible", reason)
    if not isinstance(observation, dict):
        return reject("invalid_observation")
    if (observation.get("bookmaker") != "pmu_fr"
            or observation.get("canonical_market") != "ANYTIME_GOALSCORER"
            or observation.get("period") != "FULL_TIME"):
        return reject("unsupported_market")
    home, away = team_code(observation.get("home")), team_code(observation.get("away"))
    start = timestamp(observation.get("start_utc"))
    if not home or not away or home == away or start is None:
        return reject("missing_event_context")
    fixtures = []
    for game in games:
        if not isinstance(game, dict):
            continue
        date = timestamp(game.get("start_utc"))
        if (team_code(game.get("home")) == home and team_code(game.get("away")) == away
                and date is not None and abs((date-start).total_seconds()) <= 15*60
                and isinstance(game.get("event_id"), str) and game["event_id"]):
            fixtures.append(game)
    if not fixtures:
        return reject("event_not_found")
    # Duplicate/conflicting fixtures are never silently collapsed.
    if len(fixtures) != 1:
        return Match("ambiguous", "multiple_events")
    game = fixtures[0]
    provider_event = observation.get("provider_event_id")
    if provider_event is not None:
        if type(provider_event) not in (str, int) or not str(provider_event).strip():
            return reject("invalid_provider_id")
        linked = (event_crosswalk or {}).get(str(provider_event))
        if linked is not None and linked != game["event_id"]:
            return reject("event_id_conflict")
    team_value = observation.get("team")
    team = team_code(team_value) if team_value is not None else None
    if team_value is not None and (not team or team not in (home, away)):
        return reject("team_conflict")
    label = name_key(observation.get("name"))
    if observation.get("name") is not None and not label:
        return reject("invalid_player_name")
    provider_player = observation.get("provider_player_id")
    if provider_player is not None and (type(provider_player) not in (str, int) or not str(provider_player).strip()):
        return reject("invalid_provider_id")
    linked_player = (player_crosswalk or {}).get(str(provider_player)) if provider_player is not None else None
    if not label and linked_player is None:
        return reject("missing_player_identity")
    candidates = []
    for player in players:
        if not isinstance(player, dict):
            continue
        pid = player.get("player_id")
        roster_team = team_code(player.get("team"))
        if (not isinstance(pid, str) or not pid or player.get("current_team_observed") is not True
                or roster_team not in (home, away) or (team and roster_team != team)):
            continue
        variants = [player.get("name"), *(aliases or {}).get(pid, [])]
        names = {name_key(n) for n in variants if name_key(n)}
        if (linked_player is None or pid == linked_player) and (not label or label in names):
            candidates.append(player)
    if len(candidates) > 1:
        return Match("ambiguous", "multiple_players")
    if not candidates:
        return reject("player_evidence_conflict" if linked_player is not None else "player_not_found")
    # If the same internal ID has multiple roster rows, reject inconsistent
    # identity/roster data even if a supplied team happened to select one row.
    pid = candidates[0]["player_id"]
    if sum(isinstance(p, dict) and p.get("player_id") == pid for p in players) != 1:
        return Match("ambiguous", "duplicate_player_id")
    return Match("matched", "unique_identity", pid, game["event_id"])
