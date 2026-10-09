#!/usr/bin/env python3
"""Independent early NBA season *prior* from completed previous NBA standings.

Data source: ESPN public prior-season standings; only derived team aggregates,
never historical play-by-play or protected source code. This is a SHADOW
model: preseason exposure, injuries, rotation and minute limits are NOT known.
No prospective price recommendations, never overwrite primary predictions.
"""
from __future__ import annotations
import argparse,json,math
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from modeles.simulations.multisports_independant import _read_cached_event,_logistic
from modeles.simulations.football_avance_independant import utc

BASE="https://site.api.espn.com/apis/v2/sports/basketball/nba/standings?"
PRIOR_FADE_GAMES=18.0
MAX_STANDINGS_AGE=timedelta(days=30)
STATUS="shadow_prior_not_calibrated"

def previous_season_end_year(as_of:datetime)->int:
    if as_of.tzinfo is None:raise ValueError("Timezone required")
    return as_of.year if as_of.month>=8 else as_of.year-1

def _valid(raw,lo,hi):
    if isinstance(raw,bool):return None
    try:n=float(raw)
    except (ValueError,TypeError):return None
    return n if math.isfinite(n) and lo<=n<=hi else None

def parse_standings(payload:dict,end_year:int,observed_at:datetime)->dict:
    teams={}
    def visit(root):
        for item in (root.get("standings") or {}).get("entries") or []:
            meta=item.get("team") or {}
            tid=str(meta.get("id") or "")
            vals={stat.get("name"):stat.get("value") for stat in
                  item.get("stats") or [] if isinstance(stat,dict)}
            w=_valid(vals.get("wins"),0,100)
            l=_valid(vals.get("losses"),0,100)
            home=_valid(vals.get("avgPointsFor"),40,155)
            away=_valid(vals.get("avgPointsAgainst"),40,155)
            if (not tid or not w or l is None or w+l<50 or
                home is None or away is None):continue
            teams[tid]={
                "team_id":tid,
                "label":str(meta.get("displayName") or meta.get("name") or ""),
                "abbr":str(meta.get("abbreviation") or ""),
                "wins":int(w),"losses":int(l),
                "avg_points_for":round(home,4),
                "avg_points_against":round(away,4),
                "margin":round(home-away,4),
                "win_fraction":round(w/(w+l),6),
            }
        for part in root.get("children") or []:
            if isinstance(part,dict):visit(part)
    if not isinstance(payload,dict):raise ValueError("Invalid ESPN data")
    visit(payload)
    if len(teams)<22:
        raise ValueError(f"ESPN prior-season coverage too low: {len(teams)} teams")
    if observed_at.tzinfo is None:raise ValueError("Missing observation timezone")
    return {
        "season_end_year":end_year,"observed_at_utc":observed_at.astimezone(timezone.utc).isoformat(),
        "source":"ESPN public previous-season NBA standings",
        "status":"real_previous_season_aggregate",
        "teams":teams,
        "notes":"Only final previous-season averages, not predictive xG or individual player stats.",
    }

def fetch_prior(end_year:int,now:datetime):
    query=BASE+urlencode({"season":end_year})
    with urlopen(Request(query,headers={"Accept":"application/json"}),timeout=22) as response:
        data=json.load(response)
    return parse_standings(data,end_year,now)

def _prior_team(prior:dict,team_id:str,as_of:datetime)->dict|None:
    if prior.get("status")!="real_previous_season_aggregate":return None
    observed=utc(prior.get("observed_at_utc"))
    if (not observed or observed>as_of or as_of-observed>MAX_STANDINGS_AGE or
        prior.get("season_end_year")!=previous_season_end_year(as_of)):
        return None
    return (prior.get("teams") or {}).get(str(team_id))

def predict_nba(prior:dict,cache:dict,now:datetime,days:int=3)->dict:
    if now.tzinfo is None or not 1<=days<=7:raise ValueError("Invalid date/time")
    raw=(cache.get("leagues") or {}).get("NBA",{}).get("events") or []
    games=[e for row in raw if (e:=_read_cached_event(row)) is not None and e.league=="NBA"]
    future=sorted((e for e in games if not e.complete and now<e.start<
                   now+timedelta(days=days)),key=lambda x:(x.start,x.id))
    out=[]
    for match in future:
        h=_prior_team(prior,match.home_id,now)
        a=_prior_team(prior,match.away_id,now)
        record={
            "event_id":match.id,"league":"NBA","home":match.home,"away":match.away,
            "start_utc":match.start.isoformat(),
            "model":"independent_nba_prior_strength_v1",
            "status":"no_authorized_prior",
            "probabilities":None,
        }
        if not h or not a:
            out.append(record);continue
        current=[g for g in games if g.scored and
                 g.start<=now-timedelta(hours=8) and
                 (g.home_id in (match.home_id,match.away_id) or
                  g.away_id in (match.home_id,match.away_id))]
        sums={}
        for tid,base in ((match.home_id,h),(match.away_id,a)):
            sample=[]
            for e in current:
                if e.home_id==tid:sample.append(e.home_score-e.away_score)
                if e.away_id==tid:sample.append(e.away_score-e.home_score)
            n=len(sample)
            # 18 equivalent prior-games, 65% carryover for roster turnover;
            # current scores can adapt, but preseason samples may be noisy.
            strength=(PRIOR_FADE_GAMES*.65*base["margin"]+sum(sample)) /(
                PRIOR_FADE_GAMES+n)
            sums[tid]=(strength,n)
        sh,nh=sums[match.home_id]
        sa,na=sums[match.away_id]
        elo_home=max(1330.,min(1740.,1500.+sh*22.))
        elo_away=max(1330.,min(1740.,1500.+sa*22.))
        p_elo=_logistic(elo_home,elo_away,35)
        margin=(sh-sa)/2+1.4
        p_margin=.5*(1+math.erf(margin/(12.*math.sqrt(2))))
        p_win=.5+.65*(h["win_fraction"]-a["win_fraction"])*.55+.02
        p=min(.99,max(.01,.45*p_elo+.40*p_margin+.15*p_win))
        record.update({
            "status":STATUS,
            "probabilities":{"home_win":round(p,5),"away_win":round(1-p,5)},
            "components":{"elo":round(p_elo,5),"margin":round(p_margin,5),
                          "prior_wins":round(p_win,5)},
            "strength":{"home":round(sh,3),"away":round(sa,3)},
            "current_games":{"home":nh,"away":na},
            "previous_season":prior["season_end_year"],
            "data_observed_at":prior["observed_at_utc"],
            "warning":"Prior is pre-2026-27 regular season stats. Preseason lineup effects not modeled."
        })
        out.append(record)
    return {
        "generated_at_utc":now.astimezone(timezone.utc).isoformat(),
        "status":"shadow_nba_prior_only",
        "source":prior.get("source","not_connected"),
        "previous_season_end_year":prior.get("season_end_year"),
        "previous_season_team_count":len(prior.get("teams") or {}),
        "matches":out,
        "ready":sum(x["probabilities"] is not None for x in out),
        "disclaimer":"Prior-season standings are NOT the current lineups. No historical look-ahead backtest from a newly collected snapshot."
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cache",default="docs/multisports-history.json")
    ap.add_argument("--prior",default="docs/nba-prior-standings.json")
    ap.add_argument("--output",default="docs/nba-prior-shadow.json")
    ap.add_argument("--offline",action="store_true")
    args=ap.parse_args()
    now=datetime.now(timezone.utc)
    file=Path(args.prior)
    prior={}
    if file.is_file():
        prior=json.loads(file.read_text(encoding="utf-8"))
    observed=utc(prior.get("observed_at_utc"))
    correct_season=prior.get("season_end_year")==previous_season_end_year(now)
    fresh=bool(observed and timedelta(0)<=now-observed<=MAX_STANDINGS_AGE)
    if (not args.offline) and (not correct_season or not fresh):
        prior=fetch_prior(previous_season_end_year(now),now)
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_text(json.dumps(prior,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    history=json.loads(Path(args.cache).read_text(encoding="utf-8"))
    output=predict_nba(prior,history,datetime.now(timezone.utc))
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("NBA prior:",output["previous_season_team_count"],
          "teams; ready",output["ready"],"from",len(output["matches"]),"upcoming")

if __name__=="__main__":main()
