#!/usr/bin/env python3
"""Same NHL ESPN goalie status/merge rules as Clairvoyance _nhl_goalies.py.

Confirmed ≠ projected; old starter carry is marked via source metadata.
No third-party code copied, no MoneyPuck scraping in this module.
"""
from __future__ import annotations
from datetime import datetime,timezone
import re,unicodedata
ISO="%Y-%m-%dT%H:%MZ"
ESPN_STATUS={"confirmed":"confirmed","expected":"projected",
             "probable":"projected","likely":"projected"}

def norm_name(name:str)->str:
    raw=unicodedata.normalize("NFKD",name or "")
    normalized="".join(ch for ch in raw if not unicodedata.combining(ch)).lower()
    return re.sub(r"\s+"," ",re.sub(r"[^a-z ]"," ",normalized)).strip()

def espn_probables(competitors:list[dict],unknown:set|None=None)->dict:
    matched={}
    for comp in competitors or []:
        side=comp.get("homeAway")
        if side not in ("home","away"):continue
        for value in comp.get("probables") or []:
            if value.get("name")!="probableStartingGoalie":continue
            athlete=value.get("athlete") or {}
            name=(athlete.get("fullName") or athlete.get("displayName") or "").strip()
            stype=((value.get("status") or {}).get("type") or "").strip().lower()
            status=ESPN_STATUS.get(stype)
            if not name:continue
            if status is None:
                if unknown is not None:unknown.add(stype or "(none)")
                continue
            matched[side]={"name":name,"status":status}
            break
    return matched

def side_key(s:dict|None):
    if not s:return None
    return (norm_name(s.get("name","")),s.get("status"),s.get("src"),
            s.get("id"),s.get("by"),s.get("ts"),s.get("p"))

def clean_side(s:dict)->dict:
    return {key:value for key,value in s.items() if value not in (None,"")}

def build_goalies(sides:dict,previous:dict|None,now:datetime)->dict|None:
    previous=previous if isinstance(previous,dict) else {}
    output={}
    for side in ("home","away"):
        fresh,old=sides.get(side),previous.get(side)
        if fresh:output[side]=clean_side(fresh)
        elif isinstance(old,dict) and old.get("name"):output[side]=old
    if not output:return None
    unchanged=(all(side_key(output.get(s))==side_key(previous.get(s))
                   for s in ("home","away")) and previous.get("at"))
    output["at"]=previous["at"] if unchanged else now.astimezone(timezone.utc).strftime(ISO)
    src=sorted({(item.get("src") or "espn") for item in
                (output.get("home"),output.get("away")) if item})
    output["src"]="+".join(src) if src else "espn"
    return output

def merge_with_previous(games:list[dict],fresh:dict[str,dict],
                        previous_doc:dict|None,now:datetime)->dict:
    old={str(item.get("id")):item.get("goalies") for item in
         (previous_doc or {}).get("games",[]) if item.get("goalies")}
    counters={"games":len(games),"with_goalies":0,"confirmed_sides":0,
              "projected_sides":0,"carried_sides":0}
    for item in games:
        key=str(item.get("id"))
        previous=old.get(key)
        sides=fresh.get(key) or {}
        merged=build_goalies(sides,previous,now)
        if merged is None:
            item.pop("goalies",None)
            continue
        item["goalies"]=merged
        counters["with_goalies"]+=1
        for side in ("home","away"):
            row=merged.get(side)
            if not row:continue
            label="confirmed_sides" if row.get("status")=="confirmed" else "projected_sides"
            counters[label]+=1
            if side not in sides and previous and previous.get(side)==row:
                counters["carried_sides"]+=1
    return counters
