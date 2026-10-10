"""Public-source-versus-Revue fixture and NHL prediction output bridge.

Independently authored source diagnostic (not an import of original algorithms).
Only fetches public schedule facts and numeric outcomes, deliberately excludes
third-party odds (often US books), full descriptions, logos and betting history.

Every game join requires exact sport+event ID+kickoff. A source's past published
output may be compared with Revue's model output only when BOTH predictions
have documented pre-match timestamps. Neither model calibration nor identical
underlying features is assumed.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.request import Request,urlopen
import argparse,json,math,re

REF="https://raw.githubusercontent.com/Purple-Wraith/clairvoyance-backend/main/docs/"
SPORTS=("NHL","NBA","MLB","NFL","PL","LALIGA","BUNDESLIGA","MLS","SERIEA")
SOCCER={"pl":"PL","liga":"LALIGA","bl":"BUNDESLIGA","mls":"MLS","ita":"SERIEA"}
SOURCE_KEYS={"data":"data.json","nba":"nba_schedule.json",
             "nfl":"nfl_schedule.json","soccer":"soccer_schedule.json"}
MAX_DAYS=10
def date(s):
    if not isinstance(s,str):raise ValueError("Unparseable timestamp")
    v=s.replace("Z","+00:00")
    t=datetime.fromisoformat(v)
    if t.tzinfo is None:raise ValueError("Timestamp missing UTC offset")
    return t.astimezone(timezone.utc)
def finite(x,lo=None,hi=None):
    return type(x) in (float,int) and math.isfinite(x) and (
        lo is None or x>=lo) and (hi is None or x<=hi)
def source_event(league,row,source,observed):
    if not isinstance(row,dict):return None
    eid=str(row.get("id") or "").strip()
    if not re.fullmatch(r"[0-9]{4,16}",eid):return None
    home=str(row.get("home") or "").strip()
    away=str(row.get("away") or "").strip()
    if not home or not away or home==away or "TBD" in (home.upper(),away.upper()):
        return None
    try:kick=date(row.get("date"))
    except (ValueError,TypeError):return None
    return dict(key=f"{league}:{eid}",league=league,event_id=eid,
                kickoff_utc=kick.isoformat(),home=home,away=away,
                state=str(row.get("state") or row.get("status") or "unknown"),
                original_observed_at_utc=observed.isoformat(),
                source=source)
def calendar(ref,at_time):
    sources={}
    for k,d in ref.items():
        try:
            timestamp=date(d.get("generated") or d.get("generated_at"))
        except (ValueError,TypeError,AttributeError):
            sources[k]={"status":"invalid_timestamp","events":0}
            continue
        lag=(at_time-timestamp).total_seconds()/3600
        sources[k]={"status":"fresh" if -0.1<=lag<=MAX_DAYS*24 else
                     "future" if lag<-.1 else "stale",
                     "observed_at_utc":timestamp.isoformat(),"age_hours":round(lag,2),
                     "events":0}
    raw=[]
    d=ref.get("data") or {}
    for league in ("NHL","NBA","MLB"):
        obj=d.get(league.lower()) or {}
        for bucket in ("today","tomorrow"):
            for row in obj.get(bucket) or []:
                v=source_event(league,row,"data.json:"+bucket,
                               date(d["generated"]) if sources.get("data",{}).get("status")!="invalid_timestamp" else at_time)
                if v:raw.append(v)
    b=ref.get("nba") or {}
    for g in b.get("games") or []:
        v=source_event("NBA",g,"nba_schedule.json",
                    date(b["generated_at"]) if sources.get("nba",{}).get("status")!="invalid_timestamp" else at_time)
        if v:raw.append(v)
    nfl=ref.get("nfl") or {}
    for week,fixtures in (nfl.get("weeks") or {}).items():
        if not isinstance(fixtures,list):continue
        for g in fixtures:
            v=source_event("NFL",g,"nfl_schedule.json",
                    date(nfl["generated_at"]) if sources.get("nfl",{}).get("status")!="invalid_timestamp" else at_time)
            if v:raw.append(v)
    soc=ref.get("soccer") or {}
    for key,league in SOCCER.items():
        for g in (soc.get("leagues") or {}).get(key) or []:
            v=source_event(league,g,"soccer_schedule.json",
                    date(soc["generated_at"]) if sources.get("soccer",{}).get("status")!="invalid_timestamp" else at_time)
            if v:raw.append(v)
    # Critical: original source has duplicated NBA ids in data today + NBA
    # schedule, and may also revise kickoff/state. Do not treat duplicates
    # as independent fixtures. Fail closed if a single ID changes kickoff.
    group=defaultdict(list)
    for item in raw:group[item["key"]].append(item)
    unique={};ambiguous=[]
    for k,versions in group.items():
        stamps={x["kickoff_utc"] for x in versions}
        if len(stamps)>1 or any((x["home"],x["away"])!=(
                  versions[0]["home"],versions[0]["away"]) for x in versions):
            ambiguous.append(k);continue
        # pick newer observation without silently joining variant kickoffs
        winner=max(versions,key=lambda x:x["original_observed_at_utc"])
        unique[k]=winner
    for k,v in sources.items():
        v["events"]=sum(vv["source"].startswith(SOURCE_KEYS[k])
                        for vv in unique.values())
    return unique,sources,ambiguous

def join_events(reference,revue):
    rows={};clashes=[];ids=set()
    for r in revue.get("events") or []:
        if not isinstance(r,dict) or not r.get("league") or not r.get("event_id"):
            continue
        league=str(r["league"])
        if league not in SPORTS:continue
        key=league+":"+str(r["event_id"])
        if key in ids:clashes.append(key);continue
        ids.add(key);rows[key]=r
    joined=[];missing=defaultdict(int);rejected=Counter()
    for key,src in sorted(reference.items()):
        r=rows.get(key)
        if not r:
            missing[src["league"]]+=1;continue
        try:
            origin=date(src["kickoff_utc"])
            own=date(r["start_utc"])
            delta=(own-origin).total_seconds()
        except (KeyError,ValueError,TypeError):
            rejected["missing_valid_date"]+=1;continue
        if abs(delta)>300:
            rejected["kickoff_mismatch"]+=1;continue
        # Exact League + ESPN/NHL event id + kickoff is the identity proof.
        # Team strings are NOT claimed identical: ESPN alias differences exist.
        joined.append({
            "key":key,"league":src["league"],"event_id":src["event_id"],
            "kickoff_utc":src["kickoff_utc"],
            "original": {"home":src["home"],"away":src["away"],"source":src["source"],
                         "observed_at_utc":src["original_observed_at_utc"]},
            "revue":{"home":r["home"],"away":r["away"],
                     "models_available":len(r.get("research") or []),
                     "bookmaker_prices_verified_live":False},
            "identical_names":(
                src["home"].casefold()==str(r["home"]).casefold() and
                src["away"].casefold()==str(r["away"]).casefold()),
            "id_and_kickoff_verified":True,
            "model_output_parity_verified":False,
        })
    return joined,dict(missing),dict(rejected),clashes

def model_rows(data,shadow,nhl,observed,now):
    candidates=(data.get("bestBets") or [])
    nhl_ref={}
    for match in ((data.get("nhl") or {}).get("today") or [])+(
                    (data.get("nhl") or {}).get("tomorrow") or []):
        if not isinstance(match,dict):continue
        names=(str(match.get("away") or ""),str(match.get("home") or ""))
        if names[0] and names[1] and names[0]!=names[1]:
            nhl_ref[names]=match
    shadows={str(x.get("event_id")):x for x in shadow.get("games") or []
             if isinstance(x,dict)}
    nhls={str(x.get("event_id")):x for x in nhl.get("games") or []
          if isinstance(x,dict)}
    comparisons=[];missing=Counter();all_status=Counter()
    for raw in candidates:
        if not isinstance(raw,dict) or raw.get("sport")!="NHL":continue
        spec=re.fullmatch(r"([A-Z]{2,4}) @ ([A-Z]{2,4})",str(raw.get("game") or ""))
        if not spec:
            all_status["invalid_game_label"]+=1;continue
        game=nhl_ref.get((spec.group(1),spec.group(2)))
        if not game:
            all_status["fixture_not_found"]+=1;continue
        eid=str(game.get("id"))
        try:kick=date(game["date"])
        except (ValueError,TypeError):continue
        p=raw.get("prob")
        if not finite(p,0.001,99.999):
            all_status["bad_source_probability"]+=1;continue
        pick=str(raw.get("pick") or "").upper()
        market,side,line,ours=None,None,None,None
        explicit=re.fullmatch(r"([A-Z]{2,4}) ML [+-]?\d+(?:\.\d+)?",pick)
        ou=re.fullmatch(r"(UNDER|OVER) ([0-9]+(?:\.[0-9]+)?)",pick)
        if explicit:
            market="moneyline_including_overtime"
            side="home" if explicit.group(1)==spec.group(2) else (
                "away" if explicit.group(1)==spec.group(1) else None)
            if side is None:continue
            candidate=shadows.get(eid)
            if candidate:
                try:
                    verified=(candidate["home"]==spec.group(2) and
                        candidate["away"]==spec.group(1) and
                        abs((date(candidate["start_utc"])-kick).total_seconds())<=300 and
                        date(shadow["generated_at_utc"])<kick)
                except (ValueError,KeyError,TypeError):verified=False
                if verified:ours=candidate.get("home_win" if side=="home" else "away_win")
        elif ou:
            market="full_game_total"
            side=ou.group(1).lower()
            line=float(ou.group(2))
            candidate=nhls.get(eid)
            if candidate:
                try:
                    verified=(candidate["home"]==spec.group(2) and
                        candidate["away"]==spec.group(1) and
                        abs((date(candidate["start_utc"])-kick).total_seconds())<=300 and
                        date(nhl["generated_at_utc"])<kick)
                except (ValueError,KeyError,TypeError):verified=False
                if verified:
                    k="over_"+str(line).replace(".","_")
                    # Over/under only if the exact line exists (no interpolation).
                    pr=(candidate.get("probabilities") or {}).get(k)
                    ours=pr if side=="over" else 1-pr if finite(pr,0,1) else None
        else:
            all_status["unsupported_market_spread_or_prop"]+=1
            continue
        if observed>=kick:
            all_status["source_generated_after_kickoff"]+=1;continue
        ref_prob=p/100
        status="compared" if finite(ours,0,1) else "missing_same_market_model"
        all_status[status]+=1
        comparisons.append({
            "league":"NHL","key":"NHL:"+eid,"kickoff_utc":kick.isoformat(),
            "home":spec.group(2),"away":spec.group(1),
            "market":market,"side":side,"line":line,
            "original_probability":round(ref_prob,5),
            "revue_probability":round(ours,5) if finite(ours,0,1) else None,
            "difference_revue_minus_original_pp":round((ours-ref_prob)*100,2)
                 if finite(ours,0,1) else None,
            "status":status,
            "original_observed_at_utc":observed.isoformat(),
            "revue_observed_at_utc":(
                shadow.get("generated_at_utc") if market.startswith("moneyline")
                else nhl.get("generated_at_utc")),
            "same_scheduled_fixture_and_market":status=="compared",
            "identical_features_verified":False,
            "identical_model_configuration_verified":False,
            "source_quote_is_french_live_verified":False,
            "calibration_verified":False})
    mean=None
    compared=[abs(r["difference_revue_minus_original_pp"]) for r in comparisons
              if r["status"]=="compared"]
    if compared:mean=round(sum(compared)/len(compared),2)
    return comparisons,dict(all_status),mean

def report(data,soccer,nfl,nba,revue,shadow,nhl,now):
    originals={"data":data,"soccer":soccer,"nfl":nfl,"nba":nba}
    reference,sources,ambiguity=calendar(originals,now)
    joined,missing,rejected,clashes=join_events(reference,revue)
    comparisons,checks,mean=model_rows(data,shadow,nhl,date(data["generated"]),now)
    coverage={}
    for league in SPORTS:
        source_count=sum(r["league"]==league for r in reference.values())
        matches=sum(r["league"]==league for r in joined)
        coverage[league]={"source_fixtures":source_count,"identical_id_and_kickoff":matches,
                          "unmatched":source_count-matches,
                          "identity_match_percent":round(100*matches/source_count,1)
                             if source_count else None}
    return {
        "status":"public_original_source_fixture_and_nhl_output_diagnostic",
        "generated_at_utc":now.isoformat(),
        "reference_repository":"Purple-Wraith/clairvoyance-backend",
        "target_repository":"Matttgic/Revue",
        "real_bets_enabled":False,"live_french_odds_verified":False,
        "exact_prediction_parity_verified":False,"point_in_time_feature_parity_verified":False,
        "source_inputs":sources,
        "source_fixture_total":len(reference),"revue_fixture_total":len(revue.get("events") or []),
        "strict_event_matches":len(joined),
        "source_ambiguous_event_ids":ambiguity,
        "revue_ambiguous_event_ids":clashes,
        "identity_rejections":rejected,
        "reference_unmatched_by_league":missing,
        "by_league":coverage,
        "matched_fixtures":joined,
        "original_nhl_best_bets_reported":sum(isinstance(x,dict) and x.get("sport")=="NHL"
                                               for x in data.get("bestBets") or []),
        "nhl_same_market_model_comparisons":sum(x["status"]=="compared" for x in comparisons),
        "nhl_model_comparison_outcomes":checks,
        "nhl_mean_abs_probability_difference_pp":mean,
        "nhl_source_vs_revue":comparisons,
        "original_history_profit_report_excluded":True,
        "reason_original_profit_excluded":"Original public engine_performance basis includes late and unknown-timing settled picks. This tool neither imports nor treats original picks as verified winnings.",
        "note":"Matches prove identity of a published event ID and kickoff only. Model probabilities are independently evaluated from different datasets and times. Not live; not identical model features; no arbitrage or betting recommendations."
    }

def download(file):
    req=Request(REF+file,headers={"User-Agent":"Revue-Source-Audit/1.0","Accept":"application/json"})
    with urlopen(req,timeout=24) as response:
        body=response.read(4000001)
    if len(body)>4000000:raise ValueError("Source JSON over 4 MB")
    return json.loads(body)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--docs",default="docs")
    p.add_argument("--output",default="docs/clairvoyance-real-output-gap.json")
    a=p.parse_args();root=Path(a.docs)
    def load(name):return json.loads((root/name).read_text(encoding="utf-8"))
    originals={key:download(name) for key,name in SOURCE_KEYS.items()}
    now=datetime.now(timezone.utc)
    result=report(originals["data"],originals["soccer"],originals["nfl"],
                  originals["nba"],load("match-center-latest.json"),
                  load("nhl-clairvoyance-shadow-latest.json"),
                  load("nhl-model-latest.json"),now)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("Real output gap:",result["strict_event_matches"],"matched fixtures out of",
          result["source_fixture_total"],"reference fixtures,",
          result["nhl_same_market_model_comparisons"],"NHL model comparisons. NO wagers.")
if __name__=="__main__":main()
