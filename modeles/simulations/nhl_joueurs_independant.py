#!/usr/bin/env python3
"""NHL player prop probabilities for research — not line-up-confirmed.

Separate historical stat profile from actual availability on game day.
Official NHL statistics only; no bookmaker line, no value/ROI claim.
Season rates use shrinkage toward PREVIOUS season, previous team may be stale.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime,timezone
import json
import math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

API="https://api.nhle.com/stats/rest/en/skater/summary"
SHRINK=16.0


def _display_name(row: dict) -> str:
    def part(value):
        if isinstance(value, dict):
            return value.get("default") or value.get("fr") or ""
        return value if isinstance(value, str) else ""
    name = (part(row.get("firstName"))+" "+part(row.get("lastName"))).strip()
    return name or str(row.get("skaterFullName") or row.get("playerId") or "")


def _fetch_stats(season: int, teams: set[str]) -> tuple[list[dict],dict]:
    """Get official NHL club stats from the same api-web host as the fixtures.

    The aggregate stats.nhle.com endpoint returned HTTP 403 from GitHub
    Actions on 2026-10-09. Fetch only teams that play soon; use a bounded pool.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    host="https://api-web.nhle.com/v1/club-stats"
    def one(team: str) -> tuple[str,list[dict]]:
        url=f"{host}/{team}/{season}/2"
        request=Request(url,headers={"Accept":"application/json"})
        with urlopen(request,timeout=18) as response:
            payload=json.loads(response.read().decode("utf-8"))
        data=payload.get("skaters")
        if not isinstance(data,list):
            raise ValueError(f"{team}: skaters not present")
        out=[]
        for row in data:
            if not isinstance(row,dict) or not row.get("playerId"):
                continue
            item=dict(row)
            item["skaterFullName"]=_display_name(item)
            item["teamAbbrevs"]=team
            out.append(item)
        return team,out
    all_rows=[];failed={}
    with ThreadPoolExecutor(max_workers=6) as pool:
        jobs={pool.submit(one,team):team for team in teams}
        for fut in as_completed(jobs):
            team=jobs[fut]
            try:
                _,rows=fut.result()
                all_rows.extend(rows)
            except Exception as err:
                failed[team]=f"{type(err).__name__}: {str(err)[:80]}"
    return all_rows,{"requested":len(teams),"failed":failed,
                     "successful":len(teams)-len(failed)}

def parse_rows(rows:list[dict]) -> dict[str,dict]:
    """Aggregate across traded-team rows. Never pretend unavailable stats exist."""
    found={}
    for row in rows:
        if not isinstance(row,dict) or not row.get("playerId"):
            continue
        gp=row.get("gamesPlayed")
        if not isinstance(gp,(float,int)) or gp<=0:
            continue
        pid=str(row["playerId"])
        stats=found.setdefault(pid,{
            "player_id":pid,"name":str(row.get("skaterFullName") or pid),
            "teams":set(),"games":0.,"goals":0.,"assists":0.,"shots":0.,"points":0.,
        })
        for team in str(row.get("teamAbbrevs") or "").replace(",", " ").split():
            if len(team)>=2:
                stats["teams"].add(team.upper())
        stats["games"]+=gp
        for key,out in (("goals","goals"),("assists","assists"),("shots","shots"),("points","points")):
            val=row.get(key)
            if isinstance(val,(float,int)) and val>=0:
                stats[out]+=val
    return found


def profile(previous:dict|None,current:dict|None)->dict:
    """Posterior arithmetic count rate (fixed shrinkage prior, not ML)."""
    prev=previous or {}
    cur=current or {}
    gp=float(cur.get("games") or 0)
    played_prev=float(prev.get("games") or 0)
    # Minimum prior exposure, else use conservative replacement role floor.
    default={"goals":.11,"assists":.17,"points":.28,"shots":1.6}
    out={}
    for key,prior_floor in default.items():
        if played_prev>=18:
            prior_rate=float(prev.get(key,0))/played_prev
        else:
            prior_rate=prior_floor
        count=float(cur.get(key) or 0)
        out[key]=(count+SHRINK*prior_rate)/(gp+SHRINK)
    out["n_current"]=gp
    out["n_prev"]=played_prev
    return out


def poisson_over(rate:float,line:float)->float:
    if not math.isfinite(rate) or rate<0 or abs(line%1-.5)>1e-9:
        raise ValueError("Invalid Poisson input")
    k=int(line)
    cdf=math.exp(-rate)
    mass=cdf
    for i in range(1,k+1):
        mass=mass*rate/i
        cdf+=mass
    return max(0.,min(1.,1.-cdf))


def score_player(prev:dict|None,cur:dict|None,team:str)->dict|None:
    """Player must have a declared team relation; roster NEVER assumed confirmed."""
    item=cur or prev
    if not item or team.upper() not in item.get("teams",set()):
        return None
    stats=profile(prev,cur)
    current_known=bool(cur and team.upper() in cur.get("teams",set()) and cur.get("games",0)>0)
    return {
        "player_id":item["player_id"],"name":item["name"],
        "team":team,"current_team_observed":current_known,
        "availability":"NON_VERIFIEE",
        "season_games_current":int(stats["n_current"]),
        "season_games_previous":int(stats["n_prev"]),
        "metrics":{
            "but":round(poisson_over(stats["goals"],.5),4),
            "point":round(poisson_over(stats["points"],.5),4),
            "passe":round(poisson_over(stats["assists"],.5),4),
            "tir_cadre_2_plus":round(poisson_over(stats["shots"],1.5),4),
            "tir_cadre_3_plus":round(poisson_over(stats["shots"],2.5),4),
            "tir_cadre_4_plus":round(poisson_over(stats["shots"],3.5),4),
        },
        "projected_rates":{k:round(stats[k],3) for k in ("goals","assists","points","shots")},
        "note":"Profil historique expérimental. Alignement, adversaire, temps de glace et PP non vérifiés.",
    }


def season_id(now:datetime)->int:
    year=now.year if now.month>=8 else now.year-1
    return int(str(year)+str(year+1))


def run(source:dict,prior_rows:list[dict],current_rows:list[dict],generated:datetime,
        max_per_team=8)->dict:
    prior,current=parse_rows(prior_rows),parse_rows(current_rows)
    fixtures=source.get("games")
    if not isinstance(fixtures,list):
        raise ValueError("NHL fixtures missing")
    unique_teams=set()
    for g in fixtures:
        if not isinstance(g,dict):
            continue
        start=datetime.fromisoformat(g["start_utc"].replace("Z","+00:00"))
        if start>generated:
            unique_teams.update((g["home"],g["away"]))
    per_team={}
    for team in sorted(unique_teams):
        candidates=[]
        for pid,item in {**prior,**current}.items():
            row=score_player(prior.get(pid),current.get(pid),team)
            if row:
                candidates.append(row)
        # Put current-season team observed players first so transfers cannot
        # masquerade as current-team props. Other profiles are research-only.
        candidates.sort(key=lambda r:(not r["current_team_observed"],
                   -r["projected_rates"]["goals"],-r["projected_rates"]["shots"]))
        per_team[team]=candidates[:max_per_team]
    return {
        "generated_at_utc":generated.isoformat(),
        "status":"profils_experimentaux_non_calibres",
        "source":"NHL Stats REST / skater summary, seasons previous+current",
        "season":season_id(generated),
        "note":"No lineup verification, no bookmaker prices. Do not bet directly from these estimates.",
        "teams":per_team,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--nhl-file",default="docs/nhl-model-latest.json")
    parser.add_argument("--output",default="docs/nhl-players-latest.json")
    args=parser.parse_args()
    as_of=datetime.now(timezone.utc)
    fixtures=json.loads(Path(args.nhl_file).read_text(encoding="utf-8"))
    season=season_id(as_of)
    upcoming=fixtures.get("games") or []
    clubs=set()
    for game in upcoming:
        try:
            if datetime.fromisoformat(game["start_utc"].replace("Z","+00:00"))>as_of:
                clubs.update((game["home"],game["away"]))
        except (KeyError,TypeError,ValueError):
            pass
    previous, prevdiag=_fetch_stats(season-10001,clubs)
    current, curdiag=_fetch_stats(season,clubs)
    report=run(fixtures,previous,current,as_of)
    report["source"]="NHL Web API / club-stats/{team}/{season}/2"
    report["diagnostics"]={"previous":prevdiag,"current":curdiag}
    if not previous:
        report["status"]="source_indisponible"
        report["teams"]={}
        report["note"]="Statistiques saison passée indisponibles ; pas de profils publiés"
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"NHL: {len(report['teams'])} équipes, "
          f"{sum(len(x) for x in report['teams'].values())} profils de joueurs ; non confirmés.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
