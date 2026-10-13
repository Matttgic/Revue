"""Private format hypotheses, aggregate counters only; never identity acceptance."""
import re
import unicodedata

from outils.collecte.diagnostic_nhl_identity_structure import NAME_FIELDS
from outils.collecte.nhl_player_matching import team_code
from outils.collecte.pulsescore_v2 import league_matches

METHODS = ("full_exact", "full_word_contained", "reversed_full", "initials_surname", "surname_only")
GENERIC = {("oui",), ("non",), ("yes",), ("no",), ("oui", "non"), ("yes", "no")}
BET_WORDS = {"buteur", "marque", "marquer", "but", "buts", "score", "scores", "scorer", "goal", "goals", "anytime"}


def words(value):
    if not isinstance(value, str):
        return ()
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return tuple(re.findall(r"[^\W_]+", value, flags=re.UNICODE))


def contains(text, name):
    return bool(name) and any(text[i:i+len(name)] == name for i in range(len(text)-len(name)+1))


def candidates(text, names):
    """Independent deterministic predicates. Row indices retain duplicate evidence.

    First token/rest and last token are explicit format hypotheses, not asserted
    given/family-name metadata. No substring inside a word or edit distance.
    """
    found = {method: [] for method in METHODS}
    if not text or text in GENERIC:
        return found
    for index, name in enumerate(names):
        if len(name) < 2:
            continue
        predicates = {
            "full_exact": text == name,
            "full_word_contained": contains(text, name),
            "reversed_full": text == name[1:]+name[:1],
            "initials_surname": text == tuple(n[0] for n in name[:-1])+name[-1:],
            "surname_only": text == name[-1:],
        }
        for method, hit in predicates.items():
            if hit:
                found[method].append(index)
    return found


def counters():
    return {"texts": 0, "missing_or_nontext": 0, "generic_yes_no": 0,
            "bet_description_marker": 0, "full_name_with_extra_text": 0,
            "full_name_with_bet_description": 0,
            "methods": {m: dict.fromkeys(("unique", "ambiguous", "impossible"), 0) for m in METHODS}}


def observe(value, names, report):
    text = words(value)
    report["texts"] += 1
    report["missing_or_nontext"] += not bool(text)
    report["generic_yes_no"] += text in GENERIC
    description = bool(set(text) & BET_WORDS)
    report["bet_description_marker"] += description
    hits = candidates(text, names)
    extra = any(text != names[i] for i in hits["full_word_contained"])
    report["full_name_with_extra_text"] += extra
    report["full_name_with_bet_description"] += extra and description
    for method, indices in hits.items():
        report["methods"][method]["unique" if len(indices) == 1 else "ambiguous" if indices else "impossible"] += 1


def analyze_formats(payload, profiles):
    """Market counters per market, selection counters per selection, never merged.

    Scope all_references tests format independent of team coverage. event_teams
    filters current observed rosters only, and is not a verified fixture match.
    Output shape/keys are fixed: arbitrary provider keys/values never exported.
    """
    result = {scope: {level: {f: counters() for f in NAME_FIELDS}
                      for level in ("market", "selection")}
              for scope in ("all_references", "event_teams")}
    players = [p for group in profiles.get("teams", {}).values() if isinstance(group, list)
               for p in group if isinstance(p, dict)]
    all_names = [words(p.get("name")) for p in players]
    events = payload.get("events") if isinstance(payload, dict) else None
    for event in events if isinstance(events, list) else []:
        if not isinstance(event, dict) or not league_matches(event.get("league", ""), "", "NHL"):
            continue
        clubs = {team_code(event.get("home")), team_code(event.get("away"))}
        clubs.discard(None)
        contextual = [words(p.get("name")) for p in players if len(clubs) == 2
                      and p.get("current_team_observed") is True and team_code(p.get("team")) in clubs]
        markets = event.get("markets")
        for market in markets if isinstance(markets, list) else []:
            if not isinstance(market, dict) or market.get("canonicalMarket") != "ANYTIME_GOALSCORER" or market.get("period") != "FULL_TIME":
                continue
            selections = market.get("selections")
            records = [("market", market)]
            if isinstance(selections, list):
                records.extend(("selection", s) for s in selections if isinstance(s, dict))
            for level, record in records:
                for scope, names in (("all_references", all_names), ("event_teams", contextual)):
                    for field in NAME_FIELDS:
                        observe(record.get(field), names, result[scope][level][field])
    return result
