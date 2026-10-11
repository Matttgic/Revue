#!/usr/bin/env python3
"""Independent read-only shadow comparison: PulseScore vs community sources.

Never use for bets. A missing/mismatched source is UNKNOWN, not zero coverage.
One PulseScore page, up to eight Betclic match details and three Flashscore
odds details per run. Publish aggregates only, not vendor response bodies.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import re
import time
import unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PULSE_URL = "https://api.pulsescore.net/api/betclic/soccer/events?page=1&limit=30"
FLASH_URL = "http://127.0.0.1:8000"
DAY_LIMIT = 7
MAX_DETAILS = 8
MAX_FLASH_ODDS = 3


def now_utc():
    return datetime.now(timezone.utc)


def when(value):
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def norm(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(c for c in value if not unicodedata.combining(c)).casefold()
    return "".join(re.findall(r"[a-z0-9]+", value))


def teams(row):
    home = row.get("home") or row.get("home_team")
    away = row.get("away") or row.get("away_team")
    if isinstance(home, dict):
        home = home.get("name")
    if isinstance(away, dict):
        away = away.get("name")
    if not home or not away:
        name = str(row.get("name") or "")
        chunks = re.split(r"\s+(?:-|–|vs\.?|v)\s+", name, maxsplit=1, flags=re.I)
        if len(chunks) == 2:
            home, away = chunks
    return str(home or "").strip(), str(away or "").strip()


def as_dict(match):
    if isinstance(match, dict):
        return match
    value = {}
    for key in ("id", "name", "date", "start_time", "home", "away", "teams", "markets", "competition"):
        attr = getattr(match, key, None)
        if attr is not None:
            value[key] = attr
    return value


def participant_pair(row):
    h, a = teams(row)
    if not h and row.get("teams"):
        candidates = [getattr(t, "name", None) or (t.get("name") if isinstance(t, dict) else None)
                      for t in row["teams"]]
        if len(candidates) >= 2:
            h, a = candidates[:2]
    return norm(h), norm(a)


def same_fixture(a, b, max_minutes=90):
    x, y = participant_pair(a), participant_pair(b)
    if not all(x) or x != y:
        return False
    t1 = when(a.get("startTime") or a.get("start_time") or a.get("date"))
    t2 = when(b.get("startTime") or b.get("start_time") or b.get("date"))
    return bool(t1 and t2 and abs((t1 - t2).total_seconds()) <= max_minutes * 60)


def api_get(url, headers=None, timeout=15):
    req = Request(url, headers=headers or {"Accept": "application/json"})
    with urlopen(req, timeout=timeout) as response:
        obj = json.load(response)
    if not isinstance(obj, dict):
        raise ValueError("invalid JSON object")
    return obj


def source_state():
    return {"status": "not_attempted", "events": 0, "seconds": None, "reason": None}


def pulse_events(key, report, getter=api_get):
    state = report["sources"]["pulsescore"]
    if not key:
        state.update(status="missing_secret", reason="PULSESCORE_API_KEY absent")
        return []
    started = time.monotonic()
    try:
        data = getter(PULSE_URL, {"X-Secret": key, "Accept": "application/json"})
        rows = data.get("events")
        if not isinstance(rows, list):
            raise ValueError("events array unavailable")
        selected = [x for x in rows if isinstance(x, dict) and x.get("home") and x.get("away") and
                    when(x.get("startTime") or x.get("startDate")) and
                    when(x.get("startTime") or x.get("startDate")) > now_utc() + timedelta(minutes=10)]
        state.update(status="ok", events=len(selected))
        return selected
    except Exception as exc:
        state.update(status="error", reason=type(exc).__name__)
        return []
    finally:
        state["seconds"] = round(time.monotonic() - started, 3)


def pulse_h2h(event):
    result = {}
    for m in event.get("markets") or []:
        if not isinstance(m, dict) or m.get("suspended") is True or m.get("isActive") is False:
            continue
        kind = str(m.get("canonicalMarket") or "").upper()
        if kind not in {"MATCH_RESULT", "MATCH_WINNER", "MONEYLINE", "HEAD_TO_HEAD", "WINNER"}:
            continue
        raw_name = str(m.get("rawName") or "").casefold()
        if any(x in raw_name for x in ("half", "period", "quart", "mi-temps")):
            continue
        values = {}
        for choice in m.get("selections") or []:
            side = str(choice.get("canonicalOutcome") or choice.get("rawName") or "").casefold()
            if side in {"home", "1"} or norm(side) == norm(event.get("home")):
                side = "home"
            elif side in {"away", "2"} or norm(side) == norm(event.get("away")):
                side = "away"
            elif side in {"draw", "x", "n", "nul"}:
                side = "draw"
            else:
                continue
            try:
                price = float(choice["odds"])
                if not 1.0 < price < 100:
                    continue
                values[side] = price
            except (TypeError, ValueError, KeyError):
                continue
        if set(values) == {"home", "draw", "away"}:
            result = values
            break
    return result


def betclic_h2h(match):
    values = {}
    home, away = teams(match)
    for m in match.get("markets") or []:
        title = str(getattr(m, "name", None) or (m.get("name", "") if isinstance(m, dict) else "")).casefold()
        if title not in {"resultat du match", "résultat du match", "résultat du match (90 min.)",
                         "1x2", "résultat", "resultat", "résultat du match (90 minutes)"}:
            continue
        if getattr(m, "suspended", False) or (isinstance(m, dict) and m.get("suspended")):
            continue
        for s in (getattr(m, "selections", None) or (m.get("selections", []) if isinstance(m, dict) else [])):
            name = str(getattr(s, "name", None) or (s.get("name", "") if isinstance(s, dict) else ""))
            key = norm(name)
            if key in {"1", norm(home)}:
                side = "home"
            elif key in {"2", norm(away)}:
                side = "away"
            elif key in {"x", "n", "nul", "matchnul"}:
                side = "draw"
            else:
                continue
            try:
                price = float(getattr(s, "odds", None) or (s.get("odds") if isinstance(s, dict) else None))
            except (ValueError, TypeError):
                continue
            if 1.0 < price < 100:
                values[side] = price
        if set(values) == {"home", "draw", "away"}:
            return values
    return {}


def betclic_matches(report, client_factory=None):
    state = report["sources"]["betclic_community"]
    t0 = time.monotonic()
    try:
        if client_factory is None:
            from betclic_api import BetclicClient
            client_factory = BetclicClient
        client = client_factory()
        data = client.get_matches("football")
        rows = data.get("matches", []) if isinstance(data, dict) else data
        if not isinstance(rows, list):
            raise ValueError("matches array unavailable")
        state.update(status="ok", events=len(rows))
        return client, [as_dict(x) for x in rows]
    except Exception as exc:
        state.update(status="error", reason=type(exc).__name__)
        return None, []
    finally:
        state["seconds"] = round(time.monotonic() - t0, 3)


def flashscore_matches(report, getter=api_get):
    state = report["sources"]["flashscore_community"]
    started = time.monotonic()
    try:
        data = getter(FLASH_URL + "/matches?sport=football")
        matches = []
        for comp in data.get("competitions") or []:
            matches.extend(comp.get("matches") or [])
        state.update(status="ok", events=len(matches))
        return matches
    except Exception as exc:
        state.update(status="error", reason=type(exc).__name__)
        return []
    finally:
        state["seconds"] = round(time.monotonic() - started, 3)


def compare(pulse, community, client, flash_matches, report, getter=api_get):
    pairs = report["comparison"]
    compared_betclic_ids = set()
    seen_flash_ids = set()
    for raw in pulse:
        p = {"home": raw.get("home"), "away": raw.get("away"), "startTime": raw.get("startTime") or raw.get("startDate")}
        odds_pulse = pulse_h2h(raw)
        matches = [c for c in community if same_fixture(p, c)]
        fs = [c for c in flash_matches if same_fixture(p, c)]
        if fs:
            pairs["flashscore_fixture_matches"] += 1
            fid = str(fs[0].get("id") or "")
            if fid and fid not in seen_flash_ids and pairs["flashscore_odds_queries"] < MAX_FLASH_ODDS:
                seen_flash_ids.add(fid)
                pairs["flashscore_odds_queries"] += 1
                try:
                    odds = getter(FLASH_URL + "/matches/odds?" + urlencode({"match": fid}))
                    if odds and not odds.get("error"):
                        pairs["flashscore_odds_responses"] += 1
                except Exception:
                    pairs["flashscore_odds_errors"] += 1
        if not matches:
            continue
        pairs["betclic_fixture_matches"] += 1
        match = matches[0]
        mid = match.get("id")
        if not client or mid is None or mid in compared_betclic_ids or pairs["betclic_details_queried"] >= MAX_DETAILS:
            continue
        compared_betclic_ids.add(mid)
        pairs["betclic_details_queried"] += 1
        try:
            detailed = as_dict(client.get_match(mid))
            odds_community = betclic_h2h(detailed)
        except Exception:
            pairs["betclic_details_errors"] += 1
            continue
        if odds_pulse:
            pairs["pulse_complete_1x2"] += 1
        else:
            names = [str(m.get("canonicalMarket") or m.get("rawName") or "")[:48]
                     for m in (raw.get("markets") or []) if isinstance(m, dict)]
            pairs["pulse_market_examples"] = list(dict.fromkeys(
                pairs["pulse_market_examples"] + names))[:12]
        if odds_community:
            pairs["betclic_complete_1x2"] += 1
        else:
            names = [str(getattr(m, "name", None) or (m.get("name", "") if isinstance(m, dict) else ""))[:48]
                     for m in (detailed.get("markets") or [])]
            pairs["betclic_market_examples"] = list(dict.fromkeys(
                pairs["betclic_market_examples"] + names))[:12]
        if odds_pulse and odds_community:
            pairs["same_market_1x2_matches"] += 1
            differences = [abs(odds_pulse[s] - odds_community[s]) for s in ("home", "draw", "away")]
            pairs["absolute_differences"].extend(round(delta, 4) for delta in differences)
        else:
            pairs["unverified_market_matches"] += 1


def summary(reports):
    ok = [r for r in reports if r.get("version") == "open_odds_shadow_v1"]
    result = {"days": len(ok), "pulse_success_days": 0, "betclic_success_days": 0,
              "flashscore_success_days": 0, "matched_1x2_events": 0,
              "odds_difference_mean": None, "outcomes_compared": 0, "no_replacement_proven": True}
    diffs = []
    for record in ok:
        for name, key in (("pulse_success_days", "pulsescore"),
                          ("betclic_success_days", "betclic_community"),
                          ("flashscore_success_days", "flashscore_community")):
            if record.get("sources", {}).get(key, {}).get("status") == "ok":
                result[name] += 1
        comp = record.get("comparison", {})
        result["matched_1x2_events"] += comp.get("same_market_1x2_matches", 0)
        diffs += comp.get("absolute_differences", [])
    result["outcomes_compared"] = len(diffs)
    if diffs:
        result["odds_difference_mean"] = round(sum(diffs) / len(diffs), 4)
    return result


def run(out_dir, key, client_factory=None, getter=api_get):
    stamp = now_utc()
    report = {"version": "open_odds_shadow_v1", "date_utc": stamp.strftime("%Y-%m-%d"),
              "checked_at_utc": stamp.isoformat(),
              "scope": "football-prematch-Betclic-only", "live_verified": False,
              "sources": {name: source_state() for name in
                          ("pulsescore", "betclic_community", "flashscore_community")},
              "comparison": {"betclic_fixture_matches": 0, "flashscore_fixture_matches": 0,
                             "betclic_details_queried": 0, "betclic_details_errors": 0,
                             "same_market_1x2_matches": 0, "unverified_market_matches": 0,
                             "pulse_complete_1x2": 0, "betclic_complete_1x2": 0,
                             "pulse_market_examples": [], "betclic_market_examples": [],
                             "flashscore_odds_queries": 0, "flashscore_odds_responses": 0,
                             "flashscore_odds_errors": 0, "absolute_differences": []},
              "safety": "No wagering; quotes not used as recommendations"}
    pulse = pulse_events(key, report, getter)
    client, betclic = betclic_matches(report, client_factory)
    flashscore = flashscore_matches(report, getter)
    compare(pulse, betclic, client, flashscore, report, getter)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Do not overwrite a day's earlier valid sample when manually rerun.
    suffix = stamp.strftime("%H%M%S")
    path = out_dir / f"{stamp:%Y-%m-%d}_{suffix}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    reports = []
    for p in sorted(out_dir.glob("20??-??-??_??????.json")):
        try:
            reports.append(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    (out_dir / "summary.json").write_text(
        json.dumps(summary(reports), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("shadow report:", path, "pulse:", report["sources"]["pulsescore"]["status"],
          "betclic:", report["sources"]["betclic_community"]["status"],
          "flashscore:", report["sources"]["flashscore_community"]["status"],
          "same market:", report["comparison"]["same_market_1x2_matches"])
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="docs/opensource-shadow")
    args = parser.parse_args()
    run(Path(args.out_dir), next(
        (os.environ.get(k) for k in ("PULSESCORE_API_KEY", "PULSESCORE_PRO_KEY", "PULSE_SCORE_API_KEY")
         if os.environ.get(k)), ""))
