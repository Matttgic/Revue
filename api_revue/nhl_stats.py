"""Source-backed NHL season statistics adapters for Clairvoyance route signatures.

All numbers originate from official NHL Stats REST or MoneyPuck Revue snapshots.
Revue's own NHL/player ID is NOT Clairvoyance's private SQL row primary key.
Where source columns are unavailable they remain None; no phantom stats.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import math

from api_revue.fixtures import SourceUnavailable,snapshot


def official(root:Path,now:datetime)->dict:
    doc=snapshot(root/"nhl-official-stats-latest.json",now,max_age_hours=24)
    if (doc.get("status")!="verified_nhl_official_stats_snapshot" or
        doc.get("source")!="api.nhle.com/stats/rest/en" or
        doc.get("game_type_id")!=2 or
        not isinstance(doc.get("teams"),list) or len(doc["teams"])<25):
        raise SourceUnavailable("Verified regular-season official NHL statistics unavailable")
    return doc


def _fraction(x):
    return type(x) in (int,float) and math.isfinite(x) and 0<=x<=1


def teams(root:Path,now:datetime)->list[dict]:
    doc=official(root,now)
    rows=doc["teams"]
    if not rows or not all(
        type(x.get("team_id")) is int and
        isinstance(x.get("team_abbrev"),str) and
        len(x["team_abbrev"])==3 and
        x.get("season")==doc["season"] and
        x.get("game_type_id")==2
        for x in rows
    ):
        raise SourceUnavailable("Official NHL team row integrity failed")
    return sorted(rows,key=lambda x:(-(x.get("wins") or 0),x["team_abbrev"]))


def goalies(root:Path,now:datetime,min_games:int)->list[dict]:
    doc=official(root,now)
    if (doc.get("reports",{}).get("goalie_summary",{}).get("status")!="available" or
        not isinstance(doc.get("goalies"),list) or not doc["goalies"]):
        raise SourceUnavailable("Official NHL goalie summary unavailable")
    rows=[]
    for r in doc["goalies"]:
        if (r.get("season")!=doc["season"] or
            r.get("game_type_id")!=2 or
            type(r.get("player_id")) is not int or
            type(r.get("games_played")) is not int):
            continue
        if r["games_played"]<min_games:
            continue
        pct=r.get("overall_save_pct")
        if pct is not None and not _fraction(pct):
            continue
        rows.append(r)
    return sorted(rows,key=lambda x:(-float(x.get("overall_save_pct") or 0),x["player_id"]))


def skaters(root:Path,now:datetime,team:str|None)->list[dict]:
    doc=official(root,now)
    if (doc.get("reports",{}).get("skater_summary",{}).get("status")!="available" or
        not isinstance(doc.get("skaters"),list) or not doc["skaters"]):
        raise SourceUnavailable("Official NHL skater report unavailable")
    if team is not None:
        team=team.upper().strip()
        if not len(team)==3 or not team.isalpha():
            raise ValueError("Invalid NHL team code")
    rows=[]
    for r in doc["skaters"]:
        if (r.get("season")!=doc["season"] or r.get("game_type_id")!=2 or
            type(r.get("player_id")) is not int or
            not isinstance(r.get("team_abbrev"),str) or
            len(r["team_abbrev"])!=3):
            continue
        if team is None or r["team_abbrev"]==team:
            rows.append(r)
    return rows


def moneypuck(root:Path,now:datetime,situation:str)->list[dict]:
    if situation not in ("all","5on5"):
        raise ValueError("Only independently collected MoneyPuck 'all' and '5on5' situations supported")
    doc=snapshot(root/"moneypuck-nhl-latest.json",now,max_age_hours=48)
    season=doc.get("current_season")
    if (doc.get("source")!="MoneyPuck.com" or doc.get("is_live") is not False or
        not isinstance(season,str) or not isinstance(doc.get("seasons"),dict) or
        doc.get("status",{}).get(season,{}).get("status")!="available"):
        raise SourceUnavailable("Verified MoneyPuck team season summary unavailable")
    rows=doc["seasons"].get(season) or []
    out=[]
    seen=set()
    for r in rows:
        if r.get("situation")!=situation or r.get("season")!=season:
            continue
        team=r.get("team")
        share=r.get("xg_share")
        if (not isinstance(team,str) or len(team)!=3 or team in seen or
            not _fraction(share) or type(r.get("games_played")) is not int or
            r["games_played"]<0):
            raise SourceUnavailable("Malformed MoneyPuck team and season entry")
        seen.add(team)
        def val(field):
            x=r.get(field)
            return x if type(x) in (int,float) and math.isfinite(x) and x>=0 else None
        out.append({
            "team":team,"season":season.replace("-",""),"situation":situation,
            "games_played":r["games_played"],
            "shots_for_60":val("shots_for_60"),"shots_against_60":val("shots_against_60"),
            "goals_for_60":None,"goals_against_60":None,
            "x_goals_for_60":val("xg_for_60"),
            "x_goals_against_60":val("xg_against_60"),
            "x_goals_pct":share,
            "corsi_for_pct":None,"fenwick_for_pct":None,
            "shooting_pct":None,
            "save_pct":val("save_pct"),"pdo":val("pdo"),
            "goals_for":None,"goals_against":None,
            "x_goals_for":None,"x_goals_against":None,
            "high_danger_goals_for":None,"high_danger_goals_against":None,
            "medium_danger_goals_for":None,"medium_danger_goals_against":None,
            "low_danger_goals_for":None,"low_danger_goals_against":None,
        })
    if len(out)<25:
        raise SourceUnavailable("Insufficient verified MoneyPuck teams for season")
    return sorted(out,key=lambda x:(-x["x_goals_pct"],x["team"]))


def live_moneypuck_snapshot(now:datetime, *, fetcher=None)->dict:
    """Fetch authoritative current MoneyPuck regular-season CSVs on demand.

    Independent parser, not a copy of Clairvoyance source. No silent stale
    snapshot fallback; 'live' describes fresh HTTP fetch, not in-game odds.
    The original route's playoff-team filter and full raw field set differ.
    """
    import csv
    import io
    from urllib.request import Request,urlopen
    year=now.year if now.month>=8 else now.year-1
    base=f"https://moneypuck.com/moneypuck/playerData/seasonSummary/{year}/regular"
    if fetcher is None:
        def fetcher(url):
            request=Request(url,headers={"User-Agent":"Revue-Data-Research/1.0","Accept":"text/csv"})
            with urlopen(request,timeout=15) as response:
                if response.status!=200:
                    raise SourceUnavailable("MoneyPuck upstream unavailable")
                return response.read().decode("utf-8-sig")
    try:
        team_csv=fetcher(base+"/teams.csv")
        goalie_csv=fetcher(base+"/goalies.csv")
        teams_rows=list(csv.DictReader(io.StringIO(team_csv)))
        goalie_rows=list(csv.DictReader(io.StringIO(goalie_csv)))
    except (OSError,UnicodeError,ValueError,TimeoutError) as exc:
        raise SourceUnavailable("Fresh MoneyPuck team/goalie CSV fetch failed") from exc
    if not teams_rows or not goalie_rows:
        raise SourceUnavailable("MoneyPuck supplied no current team/goalie records")
    def num(row,field):
        value=row.get(field)
        if value is None or value=="":
            return None
        try:
            x=float(value)
            return x if math.isfinite(x) else None
        except (TypeError,ValueError):
            return None
    teams={}
    for row in teams_rows:
        team=row.get("team")
        situation=row.get("situation")
        if not (isinstance(team,str) and len(team)==3 and team.isalpha() and
                situation in ("all","5on5")):
            continue
        dest=teams.setdefault(team,{})
        gp=num(row,"games_played")
        if situation=="all":
            dest.update({
                "games_played":int(gp) if gp is not None and gp>=0 else None,
                "goals_for_pg":round(num(row,"goalsFor")/gp,2)
                    if gp and num(row,"goalsFor") is not None else None,
                "goals_against_pg":round(num(row,"goalsAgainst")/gp,2)
                    if gp and num(row,"goalsAgainst") is not None else None,
                "sog_pg":None,"opp_sog_pg":None,
            })
        else:
            share=num(row,"xGoalsPercentage")
            if share is None:
                share=num(row,"xGoalsForPercentage")
            dest.update({
                "xgf_pct":round(share*100,1) if share is not None and 0<=share<=1 else None,
                "corsi_pct":None,"fenwick_pct":None,
            })
    goalies=[]
    for row in goalie_rows:
        if row.get("situation")!="all":
            continue
        team=row.get("team")
        name=row.get("name")
        if not (team in teams and isinstance(name,str) and name.strip()):
            continue
        xg=num(row,"xGoals")
        conceded=num(row,"goals")
        seconds=num(row,"icetime")
        games=num(row,"games_played")
        goalies.append({
            "name":name,"team":team,
            "games_played":int(games) if games is not None and games>=0 else None,
            "ice_hours":round(seconds/3600,1) if seconds is not None and seconds>=0 else None,
            "x_goals_against":xg,
            "goals_against":conceded,
            "gsax":round(xg-conceded,2) if xg is not None and conceded is not None else None,
        })
    if len(teams)<20 or len(goalies)<20:
        raise SourceUnavailable("Current MoneyPuck CSV coverage is insufficient; no fake live values")
    goalies.sort(key=lambda x:-(x["ice_hours"] or 0))
    return {
        "teams":teams,"goalies":goalies,"source":"moneypuck.com",
        "revue_observed_at_utc":now.isoformat(),
        "revue_reproduction_status":"partial_original_live_route_semantics_not_verified",
        "revue_season":f"{year}-{year+1}",
        "confirmed_starting_goalies":False,
    }
