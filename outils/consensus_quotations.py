#!/usr/bin/env python3
"""Independent comparison of DEVIGGED bookmaker quote snapshots.

Not a calibrated fair price, not 'confirmed value', not an official
Pinnacle feed. Strict outcome + line identity and prestart timestamps.
"""
from __future__ import annotations
from datetime import datetime
from statistics import median
import math
from outils.revue_engine_v2 import (
    same_team,quote_book_valid,FR_BOOKS,
)

def outcome_key(outcome:dict,market:str,game:dict)->str|None:
    name=str(outcome.get("name") or "")
    if market=="h2h":
        if name.lower()=="draw":return "draw"
        if same_team(name,str(game.get("home") or ""),game.get("_league","")):
            return "home"
        if same_team(name,str(game.get("away") or ""),game.get("_league","")):
            return "away"
    if market=="totals" and name in ("Over","Under"):
        try:line=float(outcome["point"])
        except (KeyError,ValueError,TypeError):return None
        if not math.isfinite(line):return None
        return name.lower()+"@"+str(line)
    return None


def market_probs(book:dict,market:dict,game:dict,now:datetime)->dict[str,float]|None:
    """De-vig matching 2-way/3-way result or exact single total line."""
    key=market.get("key")
    if key not in ("h2h","totals") or not quote_book_valid(book,market,now):
        return None
    outcomes=market.get("outcomes") or []
    expected_h2h=3 if "draw_90" in game.get("probabilities",{}) else 2
    buckets={}
    for item in outcomes:
        name=outcome_key(item,key,game)
        if not name:return None
        try:price=float(item["price"])
        except (KeyError,ValueError,TypeError):return None
        if not math.isfinite(price) or price<=1.:return None
        if name in buckets:return None
        buckets[name]=1./price
    if key=="h2h" and set(buckets)!=(
            {"home","away","draw"} if expected_h2h==3 else {"home","away"}):
        return None
    if key=="totals":
        lines={k.split("@",1)[1] for k in buckets}
        if len(lines)!=1 or len(buckets)!=2 or {x.split("@")[0] for x in buckets}!={"over","under"}:
            return None
    margin=sum(buckets.values())
    if not .75<=margin<=1.4:return None # reject malformed massive devig
    return {k:v/margin for k,v in buckets.items()}


def peer_consensus(event:dict,game:dict,market:str,outcome:dict,
                   exclude_book:str,now:datetime,min_peers:int=2)->dict:
    """Median vig-free probability of OTHER named FR books; no own-price leakage."""
    label=outcome_key(outcome,market,game)
    if label is None:return {"peer_count":0,"p_no_vig":None}
    peers=[]
    for book in event.get("bookmakers") or []:
        ident=book.get("key")
        if ident not in FR_BOOKS or ident==exclude_book:continue
        matching=[]
        for m in book.get("markets") or []:
            if m.get("key")!=market:continue
            # Each row must include a coherent full market with both sides.
            p=market_probs(book,m,game,now)
            if p and label in p:matching.append(p[label])
        if len(matching)==1:
            peers.append((ident,matching[0]))
    if len(peers)<min_peers:
        return {"peer_count":len(peers),"p_no_vig":None}
    return {"peer_count":len(peers),
            "p_no_vig":round(median(x for _,x in peers),5),
            "bookmakers":sorted(name for name,_ in peers),
            "method":"median of other FR sportsbook odds, de-vigged",
            "warning":"Bookmakers can share feeds; this is NOT an independent fair price."}
