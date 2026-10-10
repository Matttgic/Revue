"""Reimplementation indépendante du classificateur temporel de Clairvoyance.

Parité visée : catégories de verrouillage et compteurs sur entrées identiques.
Pas de copie du fichier tiers, pas d'import de données ou de mises réelles.
Les inconnus sont comptés, mais non considérés comme pré-match confirmés.
CFB volontairement hors de Revue.
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

DENVER = ZoneInfo("America/Denver")
CUTOFF_MS = 946684800000
LENGTHS = {
    "NHL": 150, "SHL": 150, "LIIGA": 150, "NLA": 150,
    "EXTRALIGA": 150, "NBA": 150, "NFL": 195,
    "PL": 120, "LIGA": 120, "CL": 120, "SERIEA": 120,
    "BUND": 120, "MLS": 120,
}
ALIASES = {
    "MLB": "MLB", "BASEBALL": "MLB", "NHL": "NHL",
    "HOCKEY": "NHL", "ICE HOCKEY": "NHL", "WNBA": "WNBA",
    "NBA": "NBA", "BASKETBALL": "NBA", "CBB": "CBB",
    "NCAAB": "CBB", "COLLEGE BASKETBALL": "CBB",
    "NFL": "NFL", "FOOTBALL": "NFL",
    "KHL": "KHL", "SHL": "SHL", "LIIGA": "LIIGA",
    "NLA": "NLA", "EXTRALIGA": "EXTRALIGA",
    "NCAAH": "NCAAH", "COLLEGE HOCKEY": "NCAAH",
    "WC": "WC", "WORLDCUP": "WC", "WORLD_CUP": "WC",
    "WORLD CUP": "WC", "SOC": "WC",
    "PL": "PL", "PREMIER LEAGUE": "PL",
    "LIGA": "LIGA", "LA LIGA": "LIGA",
    "BUND": "BUND", "BL": "BUND", "BUNDESLIGA": "BUND",
    "MLS": "MLS", "SERIEA": "SERIEA", "SERIE A": "SERIEA",
    "CL": "CL", "CH": "CL", "CHAMPIONS LEAGUE": "CL",
}
AMBIGUOUS = {"FOOTBALL", "BASKETBALL", "HOCKEY", "SOCCER", "BASEBALL"}
RETIRED = {"MLS", "BUND"}
IN_SCOPE = {"NBA", "NFL", "NHL", "KHL", "SHL", "LIIGA",
            "NLA", "EXTRALIGA", "NCAAH", "PL", "LIGA", "SERIEA", "CL"}
BASIS = "pre-start locks (known-late manual locks excluded)"


def sport_code(pick: dict) -> str:
    given = str(pick.get("sport") or "").strip().upper()
    if given in AMBIGUOUS and pick.get("league"):
        raw = pick["league"]
    else:
        raw = pick.get("sport") or pick.get("league") or ""
    code = str(raw).strip().upper()
    return ALIASES.get(code, code)


def excluded_sport(pick: dict) -> bool:
    """CFB never enters the Revue reproduction or statistical totals."""
    a = str(pick.get("sport") or "").strip().upper()
    b = str(pick.get("league") or "").strip().upper()
    return any(x in {"CFB", "COLLEGE FOOTBALL", "NCAAF"} for x in (a, b))


def is_parlay(pick: dict) -> bool:
    typ = str(pick.get("betType") or "").upper()
    return typ in {"PARLAY", "PL_PARLAY"} or pick.get("hA") in {"PARLAY", "NBA-PARLAY"}


def source_scope(pick: dict) -> bool:
    return not excluded_sport(pick) and not is_parlay(pick) and sport_code(pick) in IN_SCOPE


def number(value):
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return None if result != result else result


def iso_millis(value):
    if not isinstance(value, str) or len(value) < 11:
        return None
    try:
        stamp = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        milliseconds = stamp.timestamp() * 1000
    except (ValueError, OverflowError, OSError):
        return None
    return milliseconds if milliseconds > CUTOFF_MS else None


def match_key(day, home, away):
    return str(day) + "|" + "|".join(sorted((str(home), str(away))))


def schedule_index(fixtures):
    """Pure helper: fixtures must come from independent, dated snapshots."""
    index = {}
    for fixture in fixtures:
        value = iso_millis(fixture.get("date"))
        home = fixture.get("home")
        away = fixture.get("away")
        if value is None or not home or not away:
            continue
        day = datetime.fromtimestamp(value / 1000, DENVER).date().isoformat()
        index[match_key(day, home, away)] = value
    return index


def game_start(pick: dict, index: dict | None = None):
    direct = number(pick.get("startMs"))
    if direct is not None and direct > CUTOFF_MS:
        return direct
    if index and pick.get("date") and pick.get("hA") and pick.get("awA"):
        found = index.get(match_key(pick["date"], pick["hA"], pick["awA"]))
        return float(found) if found is not None else None
    return None


def classify(pick: dict, index: dict | None = None) -> str:
    start = game_start(pick, index)
    locked = number(pick.get("lockedAt"))
    if start is None or not locked:
        return "during" if pick.get("lockTiming") == "late-manual" else "unknown"
    gap_minutes = (start - locked) / 60000
    if gap_minutes > 0:
        return "pre"
    return "during" if gap_minutes > -LENGTHS.get(sport_code(pick), 150) else "after"


def is_known_late(pick, index=None):
    return classify(pick, index) in {"during", "after"}


def summarize(picks, index=None) -> dict:
    categories = {name: 0 for name in ("pre", "during", "after", "unknown")}
    unknown_by_league = {}
    for pick in picks:
        if pick.get("outcome") not in ("win", "loss"):
            continue
        result = classify(pick, index)
        categories[result] += 1
        if result == "unknown":
            code = sport_code(pick) or "?"
            unknown_by_league[code] = unknown_by_league.get(code, 0) + 1
    return {
        "basis": BASIS,
        "settled_pre_start": categories["pre"],
        "settled_excluded_late": categories["during"] + categories["after"],
        "settled_excluded_in_progress": categories["during"],
        "settled_excluded_after_end": categories["after"],
        "settled_unknown_timing_included": categories["unknown"],
        "unknown_timing_by_league": dict(sorted(unknown_by_league.items(), key=lambda v: -v[1])),
    }


def revue_public_eligibility(pick: dict, index=None) -> bool:
    """Règle Revue stricte, distincte de Clairvoyance : jamais de 'unknown' en ROI vérifié."""
    return source_scope(pick) and classify(pick, index) == "pre"


def revue_timing_report(picks, index=None) -> dict:
    """Rapport indépendant ; ne modifie aucune entrée ni aucun journal gelé."""
    kept = [p for p in picks if source_scope(p)]
    verified = sum(revue_public_eligibility(p, index) for p in kept)
    return {
        "status": "diagnostic_only_not_live_bets",
        "source_behavior_basis": BASIS,
        "source_compatible_timing": summarize(kept, index),
        "revue_verified_pre_start_count": verified,
        "revue_unknown_not_verified": sum(classify(p, index) == "unknown" for p in kept),
        "cfb_excluded": True,
        "original_picks_data_copied": False,
        "real_bets_enabled": False,
        "original_sql_parity_verified": False,
    }
