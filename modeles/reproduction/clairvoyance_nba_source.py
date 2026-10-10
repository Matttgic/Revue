#!/usr/bin/env python3
"""Source-faithful NBA team preparation functions from Clairvoyance backend.

Behavior reconstructed independently from public repository:
Purple-Wraith/clairvoyance-backend/scripts/clairvoyance_update.py
No NBA standings invented or copied; all inputs are explicitly supplied.
No real sportsbook or monetary behavior.
"""
from __future__ import annotations
from datetime import date, datetime
from math import isfinite

MIN_TEAM_GAMES=15
MIN_READY_TEAMS=24
ELO_CENTRE=1550
ELO_PER_MOV=28
PREV_WEIGHT=.75
PREV_EQUIVALENT_GAMES=20
TIER_MIN_GP=15
TIER_LEVELS=((24.,"PREMIUM"),(18.,"OPTIMAL"),(12.,"GOOD"))


def prior_nba_end_year(today:date|datetime,override:str|int|None=None)->int:
    if override not in (None,""):
        try:
            year=int(str(override).strip())
            if 2000<=year<=2100:return year
        except ValueError:pass
    d=today.date() if isinstance(today,datetime) else today
    return d.year+int(d.month>=10)


def to_float(value):
    if value is None:return None
    s=str(value).strip().replace(",","")
    if s in ("","-","—"):return None
    try:return float(s)
    except ValueError:return None


def previous_strength(prior:dict|None,espn:dict|None):
    if prior:
        for label in ("srs","mov","net_rtg"):
            if prior.get(label) is not None:return float(prior[label])
    if espn and espn.get("diff") is not None:
        return float(espn["diff"])
    return None


def select_team_stats(current:dict,previous:dict,
                      current_year:int,previous_year:int,
                      min_games:int|None=None,
                      min_teams:int|None=None)->dict:
    min_games=MIN_TEAM_GAMES if min_games is None else min_games
    min_teams=MIN_READY_TEAMS if min_teams is None else min_teams
    ready={key:row for key,row in (current or {}).items()
           if (row.get("gp") or 0)>=min_games and
           row.get("ortg") is not None and row.get("drtg") is not None}
    combined={}
    if len(ready)>=min_teams:
        mode="current"
        for abbr,row in current.items():
            if abbr in ready:combined[abbr]={**row,"season":current_year}
            elif previous.get(abbr):
                combined[abbr]={**previous[abbr],"season":previous_year}
                mode="mixed"
        for abbr,row in previous.items():
            if abbr not in combined:
                combined[abbr]={**row,"season":previous_year}
                mode="mixed"
        return {"teams":combined,
                "seasonUsed":current_year if mode=="current"
                          else f"{current_year}/{previous_year}",
                "mode":mode,"curReady":len(ready),
                "reason":f"{len(ready)}/{len(current)} current-season teams have >= {min_games} GP"}
    reason=(f"current-season page has only {len(ready)} team(s) with >= {min_games} GP "
            f"(need {min_teams}); using {previous_year} as prior")
    if previous:
        combined={key:{**row,"season":previous_year} for key,row in previous.items()}
        return {"teams":combined,"seasonUsed":previous_year,"mode":"prior",
                "curReady":len(ready),"reason":reason}
    if ready:
        combined={key:{**row,"season":current_year} for key,row in ready.items()}
        return {"teams":combined,"seasonUsed":current_year,"mode":"current",
                "curReady":len(ready),
                "reason":reason+f"; prior {previous_year} UNAVAILABLE, using thin current sample"}
    return {"teams":{},"seasonUsed":None,"mode":"none","curReady":0,
            "reason":reason+f"; prior {previous_year} UNAVAILABLE -- no team stats at all"}


def build_team_ratings(previous_rows:dict,current_rows:dict,
                       espn_previous:dict,espn_current:dict,
                       current_year:int,previous_year:int,
                       stats_selection:dict|None=None,
                       generated:str="")->dict:
    all_keys=sorted(set(previous_rows)|set(current_rows)|
                    set(espn_previous)|set(espn_current))
    results={}
    elos={}
    for abbr in all_keys:
        before,latest=previous_rows.get(abbr),current_rows.get(abbr)
        old_es,new_es=espn_previous.get(abbr),espn_current.get(abbr)
        wins=to_float((new_es or {}).get("w"))
        losses=to_float((new_es or {}).get("l"))
        if wins is None and latest:
            wins=float(latest["w"])
            losses=float(latest["l"])
        wins,losses=int(wins or 0),int(losses or 0)
        played=wins+losses
        margin=to_float((new_es or {}).get("diff"))
        if margin is None and latest and latest.get("mov") is not None:
            margin=latest["mov"]
        prior_margin=previous_strength(before,old_es)
        prev_w=prev_l=None
        if before:
            prev_w,prev_l=before["w"],before["l"]
        elif old_es:
            prev_w=int(to_float(old_es.get("w")) or 0)
            prev_l=int(to_float(old_es.get("l")) or 0)
        inherited=PREV_WEIGHT*prior_margin if prior_margin is not None else None
        if played>0 and margin is not None and inherited is not None:
            strength=(played*margin+PREV_EQUIVALENT_GAMES*inherited)/(
                     played+PREV_EQUIVALENT_GAMES)
            origin="prior+current"
        elif played>0 and margin is not None:
            strength=played*margin/(played+PREV_EQUIVALENT_GAMES)
            origin="current-only"
        elif inherited is not None:
            strength=inherited
            origin="prior"
        else:
            strength=None
            origin="default"
        elo=(ELO_CENTRE if strength is None else int(round(max(1300,min(
              1850,ELO_CENTRE+ELO_PER_MOV*strength)))))
        win_pct=(prev_w/(prev_w+prev_l)
                 if prev_w is not None and prev_l is not None
                 and prev_w+prev_l>0 else None)
        results[abbr]={
            "name":(before or latest or {}).get("name"),
            "prior":{
                "season":previous_year,"w":prev_w,"l":prev_l,
                "winPct":round(win_pct,3) if win_pct is not None else None,
                "mov":(before or {}).get("mov") if before
                      else to_float((old_es or {}).get("diff")),
                "srs":(before or {}).get("srs"),
                "netRtg":(before or {}).get("net_rtg"),
                "ortg":(before or {}).get("ortg"),
                "drtg":(before or {}).get("drtg"),
                "pace":(before or {}).get("pace"),
            },
            "current":{"season":current_year,"w":wins,"l":losses,
                       "gp":played,"mov":margin,
                       "netRtg":(latest or {}).get("net_rtg")},
            "priorWinPct":(round(.5+PREV_WEIGHT*(win_pct-.5),3)
                           if win_pct is not None else None),
            "strength":round(strength,2) if strength is not None else None,
            "elo":elo,"source":origin,
        }
        elos[abbr]=elo
    return {
        "teamRatings":{
            "seasonCurrent":current_year,"seasonPrior":previous_year,
            "statsSeasonUsed":(stats_selection or {}).get("seasonUsed"),
            "statsMode":(stats_selection or {}).get("mode"),
            "params":{"eloMean":ELO_CENTRE,"eloPerPoint":ELO_PER_MOV,
                      "priorCarry":PREV_WEIGHT,
                      "priorGames":PREV_EQUIVALENT_GAMES,
                      "minGamesForCurrent":MIN_TEAM_GAMES},
            "generated":generated,"teams":results,
        },
        "eloSeed":elos,
    }


def annotate_player_tiers(roster:dict,players:list[dict],
                          only_missing:bool=False)->int:
    count=0
    for player in players or []:
        entry=roster.get((player.get("name") or "").lower())
        if not entry or (player.get("gp") or 0)<TIER_MIN_GP:
            continue
        if only_missing and entry.get("rating"):
            continue
        for minimum,label in TIER_LEVELS:
            if (player.get("ppg") or 0)>=minimum:
                entry["rating"]=label
                entry["ppg"]=player["ppg"]
                count+=1
                break
    return count
