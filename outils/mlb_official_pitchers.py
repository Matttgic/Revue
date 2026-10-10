"""Phase 11: no-cost read-only MLB Stats API prospective probable pitchers.

GamePK differs from ESPN fixture id. Join only both strict nickname identities,
UTC kickoff within ten minutes, and exactly one official MLB schedule record.
Probable != confirmed starting pitcher. Never affect model probabilities.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from outils.match_center_revue import instant

URL="https://statsapi.mlb.com/api/v1/schedule"
TEAM_SUFFIXES=(
 "Diamondbacks","Braves","Orioles","Red Sox","Cubs","White Sox",
 "Reds","Guardians","Rockies","Tigers","Astros","Royals","Angels",
 "Dodgers","Marlins","Brewers","Twins","Mets","Yankees","Athletics",
 "Phillies","Pirates","Padres","Giants","Mariners","Cardinals",
 "Rays","Rangers","Blue Jays","Nationals")
NORMAL={"D-backs":"Diamondbacks","A's":"Athletics","Dbacks":"Diamondbacks"}
ALLOWED_GAME_TYPES={"R","F","D","L","W","P"}
TOLERANCE=timedelta(minutes=10)
LEAD=timedelta(minutes=20)

def team_name(source):
 if not isinstance(source,str):return None
 s=source.strip()
 if s in NORMAL:s=NORMAL[s]
 matches=[label for label in TEAM_SUFFIXES if s==label or s.endswith(" "+label)]
 return matches[0] if len(matches)==1 else None

def eligible_game(raw):
 if not isinstance(raw,dict) or raw.get("gameType") not in ALLOWED_GAME_TYPES:
  return None
 if (raw.get("status") or {}).get("abstractGameState")!="Preview":return None
 try:
  home=raw["teams"]["home"];away=raw["teams"]["away"]
  teamh=home["team"];teama=away["team"]
  home_id,away_id=teamh["id"],teama["id"]
  n1=team_name(teamh["name"]);n2=team_name(teama["name"])
  if (type(home_id) is not int or type(away_id) is not int or
      home_id<=0 or away_id<=0 or home_id==away_id or
      not n1 or not n2 or n1==n2 or
      type(raw.get("gamePk")) is not int or raw["gamePk"]<=0):
   return None
  sides={}
  for side,entry in (("home",home),("away",away)):
   obj=entry.get("probablePitcher")
   if obj is None:sides[side]=None;continue
   if not isinstance(obj,dict):
    return None
   pid=obj.get("id");name=obj.get("fullName")
   if type(pid) is not int or pid<=0 or not isinstance(name,str) or not name.strip():
    sides[side]=None;continue
   sides[side]={"name":name.strip(),"mlb_person_id":pid,
                "status":"probable_unconfirmed","source":"MLB Stats API probablePitcher"}
  return {"mlb_game_pk":raw["gamePk"],"home":n1,"away":n2,
          "start_utc":instant(raw["gameDate"]).isoformat(),
          "home_pitcher":sides["home"],"away_pitcher":sides["away"]}
 except (KeyError,ValueError,TypeError):
  return None

def collect(center,schedules,now):
 if now.tzinfo is None:raise ValueError("Must have timestamp timezone")
 now=now.astimezone(timezone.utc)
 if (center.get("status")!="experimental_revue_match_center" or
     center.get("real_bets_enabled") is not False or
     center.get("bookmaker_prices_are_live") is not False):
  raise ValueError("Untrusted match calendar")
 candidates=[];errors=Counter()
 for schedule in schedules:
  if not isinstance(schedule,dict) or not isinstance(schedule.get("dates"),list):
   errors["bad_schedule_response"]+=1;continue
  for date in schedule["dates"]:
   for game in date.get("games",[]) if isinstance(date,dict) else []:
    raw=eligible_game(game)
    if raw:candidates.append(raw)
    else:errors["excluded_non_pregame_or_incomplete_game"]+=1
 official_pks=[c["mlb_game_pk"] for c in candidates]
 if len(set(official_pks))!=len(official_pks):
  errors["duplicated_official_game_pk"]+=1
 out=[];unique_ids=set();matched=0
 for e in center.get("events") or []:
  if e.get("league")!="MLB":continue
  eid=str(e.get("event_id") or "")
  if eid in unique_ids:
   raise ValueError("Repeated ESPN MLB fixture ID")
  unique_ids.add(eid)
  try:
   kick=instant(e["start_utc"])
   if kick<now+LEAD:continue
   eligible=[x for x in candidates if x["home"]==team_name(e["home"]) and
     x["away"]==team_name(e["away"]) and
     abs(instant(x["start_utc"])-kick)<=TOLERANCE]
  except (TypeError,KeyError,ValueError):
   errors["invalid_ESPN_fixture"]+=1;continue
  if len(eligible)!=1:
   errors["no_unique_official_mlb_match"]+=1;continue
  g=eligible[0]
  if official_pks.count(g["mlb_game_pk"])!=1:
   errors["duplicated_official_game_pk"]+=1;continue
  matched+=1
  out.append({"league":"MLB","event_id":eid,
    "home":e["home"],"away":e["away"],"start_utc":kick.isoformat(),
    "mlb_game_pk":g["mlb_game_pk"],"observed_at_utc":now.isoformat(),
    "home_pitcher":g["home_pitcher"],"away_pitcher":g["away_pitcher"],
    "pitchers_are_probable_not_confirmed":True,
    "starting_pitchers_independently_confirmed":False,
    "used_in_model_probabilities":False,"sportsbook_prices_verified":False})
 return {"generated_at_utc":now.isoformat(),
  "status":"official_MLB_probable_pitchers_observed_not_confirmed",
  "source":"MLB Stats API schedule probablePitcher, matched to ESPN games by team and <=10min kickoff",
  "ESPN_fixtures_matched":matched,
  "probable_pitcher_sides":sum(g[k] is not None for g in out for k in ("home_pitcher","away_pitcher")),
  "confirmed_starting_pitchers":0,
  "model_recomputed":False,"real_bets_enabled":False,"paid_api_calls":0,
  "diagnostics":dict(errors),"rows":out,
  "note":"Only official schedule probable pitchers. No starter confirmation or certainty; does not affect forecast, Elo, bookmaker or historical picks."}

def download(start,end):
 query=urlencode({"sportId":1,"startDate":start.isoformat(),"endDate":end.isoformat(),
                  "hydrate":"probablePitcher,person"})
 url=URL+"?"+query
 req=Request(url,headers={"Accept":"application/json","User-Agent":"RevueResearch/1.0"})
 with urlopen(req,timeout=18) as reply:
  body=reply.read(3_000_001)
 if len(body)>3_000_000:raise ValueError("Oversized MLB schedule")
 return json.loads(body.decode("utf8"))

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--root",default="docs")
 parser.add_argument("--output",default="docs/mlb-official-probable-pitchers-latest.json")
 args=parser.parse_args();root=Path(args.root)
 center=json.loads((root/"match-center-latest.json").read_text(encoding="utf8"))
 now=datetime.now(timezone.utc)
 starts=[]
 for e in center.get("events") or []:
  if e.get("league")=="MLB":
   try:
    t=instant(e["start_utc"])
    if now+LEAD<=t<=now+timedelta(days=4):starts.append(t)
   except (ValueError,TypeError,KeyError):continue
 failures=[];results=[]
 if starts:
  lo=min(starts).date()-timedelta(days=1)
  hi=max(starts).date()+timedelta(days=1)
  try:results=[download(lo,hi)]
  except Exception as exc:failures.append(type(exc).__name__)
 output=collect(center,results,now)
 output["requests_attempted"]=int(bool(starts))
 output["errors"]=failures
 if failures:output["status"]="official_MLB_schedule_unavailable_no_pitcher_claims"
 dst=Path(args.output);dst.parent.mkdir(parents=True,exist_ok=True)
 dst.write_text(json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf8")
 print("MLB probable pitchers",output["probable_pitcher_sides"],"across",output["ESPN_fixtures_matched"],
       "ESPN fixtures; failures",len(failures))
if __name__=="__main__":main()
