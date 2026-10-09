#!/usr/bin/env python3
"""Revue: time-stamped French bookmaker odds board, independent of model EV.

Only REAL quotes already fetched during the Engine V2 PulseScore/The Odds API
scan. No extra paid calls. No credentials in public output. Keep canonical
league + ESPN event ID, exact market structure and observation time.
Hockey OT semantics are not independently verified: display explicit warning.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime
import math
from outils.revue_engine_v2 import (
    FR_BOOKS, KICKOFF_BUFFER, match_fixture, quote_book_valid,
    same_team, timestamp,
)

def _price(obj) -> float|None:
    try:
        x=float(obj)
    except (ValueError,TypeError):return None
    return round(x,3) if math.isfinite(x) and 1.001<=x<=1000 else None


def selections(market:dict,game:dict,league:str) -> list[dict]:
    """Accept only 2/3-way 1X2 or coherent paired O/U with identical line."""
    mk=market.get("key")
    out=market.get("outcomes") or []
    if mk=="h2h":
        expected=3 if "draw_90" in (game.get("probabilities") or {}) else 2
        if len(out)!=expected:return []
        found={}
        for item in out:
            name=str(item.get("name") or "")
            if name.casefold()=="draw":side="draw"
            elif same_team(name,game["home"],league):side="home"
            elif same_team(name,game["away"],league):side="away"
            else:return []
            if side in found:return []
            price=_price(item.get("price"))
            if price is None:return []
            found[side]={"selection":side,"price":price}
        if set(found)!=({"home","draw","away"} if expected==3 else {"home","away"}):
            return []
        return [found[k] for k in (("home","draw","away") if expected==3 else ("home","away"))]
    if mk=="totals":
        pairs=defaultdict(dict)
        for item in out:
            side=str(item.get("name") or "").strip().casefold()
            if side not in ("over","under"):return []
            try:line=float(item.get("point"))
            except (TypeError,ValueError):return []
            if not math.isfinite(line) or not 0<=line<=500:return []
            price=_price(item.get("price"))
            if price is None or side in pairs[line]:return []
            pairs[line][side]=price
        values=[]
        for line,v in sorted(pairs.items()):
            if set(v)=={"over","under"}:
                values.extend([{"selection":k,"line":line,"price":v[k]}
                               for k in ("over","under")])
        return values[:16]
    return []


def _nhl_rule(market:dict)->str:
    period=str(market.get("period") or "").upper()
    name=str(market.get("raw_market_name") or "").casefold()
    incl=period in ("GAME_INCLUDING_OVERTIME","INCLUDING_OVERTIME") or any(
        x in name for x in ("incl ot","including ot","including overtime",
         "overtime included","prolongation incl","prolongations incl",
         "incluant prolongation","incl. prolongation","avec prolongation"))
    return "including_ot_confirmed" if incl else "overtime_rule_unverified"


def build_board(models:dict,odds:dict,now:datetime)->dict:
    if now.tzinfo is None:raise ValueError("Timestamp without timezone")
    board=[]
    for league,events in odds.items():
        if league=="CFB":continue
        games=[{**g,"_league":league} for g in
            (models.get("competitions") or {}).get(league,{}).get("games",[])
            if timestamp(g.get("start_utc")) and
               timestamp(g["start_utc"])>now+KICKOFF_BUFFER]
        for e in events:
            game=match_fixture(e,games,league)
            if not game:continue
            start=timestamp(game["start_utc"])
            if start is None or start<=now+KICKOFF_BUFFER:continue
            books=[]
            for book in e.get("bookmakers") or []:
                bk=book.get("key")
                if bk not in FR_BOOKS:continue
                markets=[]
                for market in book.get("markets") or []:
                    if market.get("key") not in ("h2h","totals"):continue
                    observed=quote_book_valid(book,market,now)
                    if not observed or observed>=start:continue
                    values=selections(market,game,league)
                    if not values:continue
                    markets.append({
                        "market":market["key"],
                        "period_rule":_nhl_rule(market) if league=="NHL"
                                      else "90min" if "draw_90" in (game.get("probabilities") or {})
                                      else "game_result",
                        "quote_at":observed.isoformat(),
                        "quote_time_source":market.get("observed_origin") or "last_update",
                        "outcomes":values,
                    })
                if markets:
                    books.append({"bookmaker":bk,"markets":markets})
            if books:
                board.append({
                    "league":league,"event_id":str(game["event_id"]),
                    "home":game["home"],"away":game["away"],
                    "start_utc":game["start_utc"],
                    "bookmakers":books,
                })
    board.sort(key=lambda e:(e["start_utc"],e["league"],e["event_id"]))
    return {"generated_at_utc":now.isoformat(),
            "source":"PulseScore or The Odds API: authenticated previously fetched prices",
            "status":"available" if board else "no_matching_valid_prices",
            "events":board[:250],
            "events_count":len(board),
            "bookmaker_market_rows":sum(len(book["markets"]) for e in board
                                        for book in e["bookmakers"]),
            "warning":"Snapshot only, NOT live. Prices may move; NHL market overtime conditions may be unverified. No claim of value."}
