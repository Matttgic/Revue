#!/usr/bin/env python3
"""Independent reconstruction of ESPN byteam math from Clairvoyance.
Reference: scripts/_nba_espn.py. Verified against source in temporary CI checkout.
"""
from __future__ import annotations
TOV_PER_GAME=.75
OT_FACTOR=.995
def number(raw,default=None):
    try:x=float(raw)
    except (ValueError,TypeError):return default
    return x if x==x else default

def parse_byteam(payload:dict|None,season:int|None=None)->tuple[dict,str]:
    if not isinstance(payload,dict) or not payload.get("teams"):
        return {},"no "+chr(96)+"teams"+chr(96)+" in response"
    if season is not None:
        year=(payload.get("requestedSeason") or {}).get("year")
        if year is not None and int(year)!=int(season):
            return {},f"ESPN returned season {year}, asked for {season}"
    labels={c["name"]:c["names"] for c in payload.get("categories") or [] if c.get("names")}
    if not labels:return {},"no stat-name table ("+chr(96)+"categories[].names"+chr(96)+") in response"
    out={}
    for entity in payload["teams"]:
        tm=entity.get("team") or {}
        abbr=tm.get("abbreviation")
        if not abbr:continue
        parts={"own":{},"opp":{}}
        for cat in entity.get("categories") or []:
            label=cat.get("name")
            if label not in labels:continue
            is_other=(str(cat.get("splitId"))=="900" or
                      str(cat.get("displayName","")).lower().startswith("opponent"))
            parts["opp" if is_other else "own"].update(
                zip(labels[label],cat.get("values") or []))
        if parts["own"] and parts["opp"]:
            out[abbr]={"id":str(tm.get("id") or ""),
                       "name":tm.get("displayName") or abbr,**parts}
    if not out:return {},"teams present but none had own+opponent stat splits"
    return out,""

def possessions(team:dict,opponent:dict,games:float,tov_adj:float)->float:
    shots,made=team["fieldGoalsAttempted"],team["fieldGoalsMade"]
    off=team["offensiveRebounds"]
    other=opponent.get("defensiveRebounds")
    if other is None:other=opponent["rebounds"]-opponent["offensiveRebounds"]
    share=off/(off+other) if off+other else 0.
    return (shots+.4*team["freeThrowsAttempted"]-1.07*share*(shots-made)
            +team["turnovers"]+tov_adj*games)

def row_from_raw(raw:dict,tov_adj:float=TOV_PER_GAME,ot_factor:float=OT_FACTOR)->dict:
    team,other=raw["own"],raw["opp"]
    gp=int(number(team.get("gamesPlayed"),0) or 0)
    result={"name":raw.get("name"),"w":0,"l":0,"gp":gp,
      "mov":None,"sos":None,"srs":None,"ortg":None,"drtg":None,
      "net_rtg":None,"pace":None,"ts_pct":None,"efg_pct":None,
      "tov_pct":None,"orb_pct":None,"ft_rate":None,
      "opp_efg_pct":None,"opp_tov_pct":None,"drb_pct":None,
      "opp_ft_rate":None}
    if gp<=0:return result
    try:
        pteam=possessions(team,other,gp,tov_adj)
        popp=possessions(other,team,gp,tov_adj)
        pos=.5*(pteam+popp)
        if pos<=0:return result
        scored,allowed=team["points"],other["points"]
        result["mov"]=round((scored-allowed)/gp,2)
        result["ortg"]=round(100*scored/pos,1)
        result["drtg"]=round(100*allowed/pos,1)
        result["net_rtg"]=round(result["ortg"]-result["drtg"],1)
        result["pace"]=round(ot_factor*pos/gp,1)
        def four(a,b):
            fga,fta,tov=a["fieldGoalsAttempted"],a["freeThrowsAttempted"],a["turnovers"]+tov_adj*gp
            off=a["offensiveRebounds"]
            drb=b.get("defensiveRebounds")
            if drb is None:drb=b["rebounds"]-b["offensiveRebounds"]
            return {"efg":(a["fieldGoalsMade"]+.5*a["threePointFieldGoalsMade"])/fga,
                "ts":a["points"]/(2*(fga+.44*fta)),
                "tov":100*tov/(fga+.44*fta+tov),
                "orb":100*off/(off+drb),"ftr":a["freeThrowsMade"]/fga}
        a,b=four(team,other),four(other,team)
        result.update(
            efg_pct=round(a["efg"],3),ts_pct=round(a["ts"],3),
            tov_pct=round(a["tov"],1),orb_pct=round(a["orb"],1),
            ft_rate=round(a["ftr"],3),opp_efg_pct=round(b["efg"],3),
            opp_tov_pct=round(b["tov"],1),opp_ft_rate=round(b["ftr"],3),
            drb_pct=round(100-b["orb"],1))
    except (KeyError,TypeError,ZeroDivisionError):
        result.update(ortg=None,drtg=None,net_rtg=None,pace=None)
    return result

def rows_from_byteam(payload:dict|None,season:int|None=None)->tuple[dict,str]:
    parsed,diag=parse_byteam(payload,season)
    return ({k:row_from_raw(r) for k,r in parsed.items()},"") if parsed else ({},diag)

def attach_records(rows:dict,standings:dict|None)->dict:
    for abbr,row in rows.items():
        st=(standings or {}).get(abbr)
        if not st:continue
        w,l=number(st.get("w")),number(st.get("l"))
        if w is not None and l is not None:
            row["w"],row["l"]=int(w),int(l)
    return rows
