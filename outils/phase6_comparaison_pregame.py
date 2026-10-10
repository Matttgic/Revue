"""Phase 6 — prospective public-output comparison across four sports.

Records only the FIRST source prediction actually observed before kickoff.
GitHub history + append-only-by-event writes preserve prior model snapshots;
this does not give cryptographic immutability or prove Clairvoyance's own lock.
Public snapshots are fetched by pinned source COMMIT. No source code or odds
are redistributed, no paid feeds, no historical backfill, no wagers.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime,timedelta,timezone
import json,math,re
from pathlib import Path
from urllib.request import Request,urlopen

VERSION="revue_phase6_pregame_source_predictions_v1"
MIN_LEAD=timedelta(minutes=20)
MAX_SOURCE_AGE=timedelta(hours=6)
SPORTS=("NHL","NBA","MLB","FOOTBALL")
SOCCER={"pl":"PL","liga":"LALIGA","bl":"BUNDESLIGA",
        "ita":"SERIEA","mls":"MLS","cl":"UCL"}
FOOTBALL_LEAGUES=set(SOCCER.values())
SOURCE_REPO="Purple-Wraith/clairvoyance-backend"
BASE="https://raw.githubusercontent.com/Purple-Wraith/clairvoyance-backend/"
API="https://api.github.com/repos/Purple-Wraith/clairvoyance-backend/commits/main"


def utc(value):
    if not isinstance(value,str):raise ValueError("Missing timestamp")
    try:dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc:raise ValueError("Invalid timestamp") from exc
    if dt.tzinfo is None:raise ValueError("Naive timestamp")
    return dt.astimezone(timezone.utc)


def pvalue(v):
    if type(v) not in (int,float) or not math.isfinite(v) or not 0<v<1:
        raise ValueError("Invalid probability")
    return float(v)


def source_fixtures(data,soccer):
    """Use original event IDs and kickoff, never guess team aliases."""
    found={};ambiguous=set()
    def add(league,game,home,away,date):
        if not isinstance(game,dict):return
        game_id=str(game.get("id",""))
        if not game_id.isdecimal():return
        if not isinstance(home,str) or not isinstance(away,str) or not home or not away or home==away:return
        try:start=utc(game.get(date))
        except (ValueError,TypeError):return
        key=league+":"+game_id
        info={"key":key,"league":league,"id":game_id,
              "home":home,"away":away,"kickoff_utc":start.isoformat(),
              "state":str(game.get("state") or game.get("status") or "").lower(),
              "nba_season_type":game.get("seasonType")}
        prior=found.get(key)
        if prior is not None and any(prior[field]!=info[field] for field in
                ("home","away","kickoff_utc")):
            ambiguous.add(key)
        else:found[key]=info
    for league in ("NHL","NBA","MLB"):
        for bucket in ("today","tomorrow"):
            for g in (data.get(league.lower()) or {}).get(bucket) or []:
                if isinstance(g,dict):add(league,g,g.get("home"),g.get("away"),"date")
    for src,league in SOCCER.items():
        for g in (soccer.get("leagues") or {}).get(src) or []:
            if isinstance(g,dict):add(league,g,g.get("home"),g.get("away"),"date")
    for key in ambiguous:found.pop(key,None)
    return found,ambiguous


def side_from_pick(row,fixture):
    """Keep only explicit two-way ML or explicitly regulation-time 1X2."""
    pick=str(row.get("pick") or "").strip().upper()
    game=str(row.get("game") or "").strip().upper()
    if "[LIVE]" in pick or " LIVE" in pick:return None,"live_selection"
    match=re.fullmatch(r"([^@]+) @ ([^@]+)",game)
    if not match:return None,"unparseable_source_matchup"
    away,home=match.group(1).strip(),match.group(2).strip()
    league=fixture["league"]
    if league in ("NHL","NBA","MLB"):
        if (home!=fixture["home"].upper() or away!=fixture["away"].upper()):
            return None,"source_abbreviation_mismatch"
        spec=re.fullmatch(r"([A-Z0-9]{2,7}) ML(?: [+-]?\d+(?:\.\d+)?)?",pick)
        if not spec:return None,"unsupported_source_market"
        team=spec.group(1)
        if team not in (home,away):return None,"wrong_source_selection_team"
        return ("home" if team==home else "away"),None
    # Do NOT infer 90m vs incl OT, or 1X2 from generic football moneyline.
    if league in FOOTBALL_LEAGUES:
        spec=re.fullmatch(r"(HOME|DRAW|AWAY) 1X2 90M",pick)
        if not spec:return None,"source_soccer_period_unsupported"
        if home!=fixture["home"].upper() or away!=fixture["away"].upper():
            return None,"source_soccer_identity_mismatch"
        return spec.group(1).lower(),None
    return None,"unsupported_sport"


def classify_sport(label):
    if label in SPORTS[:3]:return label
    if label in FOOTBALL_LEAGUES:return "FOOTBALL"
    return None


def source_selection(bet,fixture):
    raw=bet.get("prob")
    if type(raw) not in (int,float) or not math.isfinite(raw) or not .01<raw<100:
        return None,"invalid_original_probability"
    side,reason=side_from_pick(bet,fixture)
    if reason:return None,reason
    return {"side":side,"original_probability":round(raw/100,5),
            "market":"1x2_90min" if fixture["league"] in FOOTBALL_LEAGUES
                     else "two_way_moneyline_unverified_period" },None


def counterpart(fixture,selection,revue_bykey,kick,now):
    own=revue_bykey.get(fixture["key"])
    if own is None:return None,None,None,"no_revue_fixture"
    if (str(own.get("home","")).casefold()!=fixture["home"].casefold() or
        str(own.get("away","")).casefold()!=fixture["away"].casefold()):
        return None,None,None,"revue_teams_differ"
    try:revt=utc(own["start_utc"])
    except (KeyError,ValueError,TypeError):
        return None,None,None,"revue_missing_kickoff"
    if abs((revt-kick).total_seconds())>300:
        return None,None,None,"revue_kickoff_differs"
    models=own.get("research") or []
    league=fixture["league"]
    prefer={
        "NHL":("clairvoyance_nhl_formula_revue_inputs",),
        "NBA":("independent_nba_prior_strength_v1",),
        "MLB":("revue_ensemble_mc_bayes_elo",),
    }
    order=prefer.get(league,("football_espn_advanced_shadow","revue_multisports_score_model"))
    for model_id in order:
        for model in models:
            if not isinstance(model,dict) or model.get("id")!=model_id:continue
            probs=model.get("probabilities") or {}
            if not isinstance(probs,dict):continue
            direction=selection["side"]
            key=direction+("_win_90" if league in FOOTBALL_LEAGUES and direction!="draw" else "")
            if direction=="draw":key="draw_90"
            elif league not in FOOTBALL_LEAGUES:key=direction+"_win"
            try:
                ts=utc(model["source_generated_utc"])
                if ts>now+timedelta(minutes=2) or ts>kick-MIN_LEAD:
                    return None,model_id,ts.isoformat(),"revue_model_observed_too_late"
                prob=pvalue(probs.get(key))
            except (KeyError,TypeError,ValueError):
                return None,model_id,None,"revue_probability_unavailable"
            return round(prob,5),model_id,ts.isoformat(),"descriptive_difference_only"
    return None,None,None,"revue_same_outcome_not_available"


def verify_ledger(ledger,now):
    if not ledger:return {"version":VERSION,"since_utc":now.isoformat(),"entries":{}}
    if ledger.get("version")!=VERSION or not isinstance(ledger.get("entries"),dict):
        raise ValueError("Refuse incompatible or corrupt existing ledger")
    utc(ledger["since_utc"])
    for key,row in ledger["entries"].items():
        if key!=row.get("id") or not isinstance(key,str):
            raise ValueError("Altered source snapshot key")
        if not re.fullmatch(r"[a-f0-9]{40}",str(row.get("source_commit",""))):
            raise ValueError("Missing pinned source commit")
        kickoff=utc(row["kickoff_utc"])
        recorded=utc(row["locked_at_utc"])
        generated=utc(row["original_document_generated_at_utc"])
        pvalue(row["original_probability"])
        if recorded>now+timedelta(minutes=2) or generated>recorded+timedelta(minutes=2):
            raise ValueError("Source report from future or altered time")
        if recorded>kickoff-MIN_LEAD:
            raise ValueError("Late source snapshot cannot be relabelled pregame")
        if row.get("revue_probability") is not None:pvalue(row["revue_probability"])
        if row.get("source_model_lock_proven") is not False or row.get("original_sql_identical") is not False:
            raise ValueError("Source lock/SQL parity cannot be certified")
    return ledger


def build(data,soccer,revue,existing,source_commit,now):
    if now.tzinfo is None:raise ValueError("Timezone-aware clock required")
    now=now.astimezone(timezone.utc)
    if not re.fullmatch(r"[0-9a-f]{40}",source_commit):
        raise ValueError("Pin a full public source commit SHA")
    if (revue.get("status")!="experimental_revue_match_center" or
        revue.get("real_bets_enabled") is not False or
        revue.get("bookmaker_prices_are_live") is not False or
        not isinstance(revue.get("events"),list)):
        raise ValueError("Revue original snapshot unsafe or unavailable")
    generated=utc(data["generated"])
    if generated>now+timedelta(minutes=2) or now-generated>MAX_SOURCE_AGE:
        raise ValueError("Original source document too old or from the future")
    own_time=utc(revue["generated_at_utc"])
    if own_time>now+timedelta(minutes=2) or now-own_time>MAX_SOURCE_AGE:
        raise ValueError("Revue match center stale or from future")
    rows=data.get("bestBets")
    if not isinstance(rows,list):raise ValueError("Missing original published output list")
    old=verify_ledger(existing,now)
    entries=dict(old["entries"])
    fixtures,ambiguous=source_fixtures(data,soccer)
    revue_bykey={}
    dup_own=set()
    for row in revue["events"]:
        if not isinstance(row,dict):continue
        key=row.get("key")
        if key in revue_bykey:dup_own.add(key)
        if isinstance(key,str):revue_bykey[key]=row
    for key in dup_own:revue_bykey.pop(key,None)
    by_sport={s:0 for s in SPORTS}
    reasons=Counter();new=[];seen=set()
    for row in rows:
        if not isinstance(row,dict):continue
        league=str(row.get("sport") or "").upper()
        sport=classify_sport(league)
        if sport is None:continue
        by_sport[sport]+=1
        if str(row.get("date"))!=generated.date().isoformat():
            # The original document contains date-scoped selections; refuse backfill.
            reasons["selection_date_not_document_day"]+=1;continue
        game_label=str(row.get("game") or "").strip().upper()
        possibles=[f for f in fixtures.values() if f["league"]==league
                   and (f["away"]+" @ "+f["home"]).upper()==game_label]
        if len(possibles)!=1:
            reasons["source_fixture_missing_or_ambiguous"]+=1;continue
        fixture=possibles[0]
        kick=utc(fixture["kickoff_utc"])
        if now>kick-MIN_LEAD or generated>kick-MIN_LEAD:
            reasons["not_observed_pre_kickoff"]+=1;continue
        if fixture["state"] not in ("pre","fut","scheduled","status_scheduled"):
            reasons["fixture_already_in_play_or_unknown"]+=1;continue
        if league=="NBA" and fixture.get("nba_season_type")!=2:
            reasons["nba_preseason_not_regular"]+=1;continue
        selection,why=source_selection(row,fixture)
        if why:reasons[why]+=1;continue
        key=fixture["key"]+":"+selection["market"]+":"+selection["side"]
        if key in seen:
            reasons["duplicate_in_original_snapshot"]+=1;continue
        seen.add(key)
        if key in entries:
            reasons["already_frozen"]+=1;continue
        ours,model,model_ts,status=counterpart(fixture,selection,revue_bykey,kick,now)
        delta=round((ours-selection["original_probability"])*100,2) if ours is not None else None
        freeze={
            "id":key,"league":league,"sport":sport,
            "event_id":fixture["id"],"home":fixture["home"],"away":fixture["away"],
            "kickoff_utc":fixture["kickoff_utc"],
            "market":selection["market"],"side":selection["side"],
            "original_probability":selection["original_probability"],
            "revue_probability":ours,
            "probability_delta_revue_minus_source_pp":delta,
            "revue_model_id":model,"revue_model_published_at_utc":model_ts,
            "status":status,"locked_at_utc":now.isoformat(),
            "original_document_generated_at_utc":generated.isoformat(),
            "source_commit":source_commit,
            "source_model_lock_proven":False,
            "original_sql_identical":False,
            "same_market_rules_verified":False,
            "calibrated":False,"real_bet":False,
        }
        entries[key]=freeze
        new.append(key)
    # Never rewrite a previously frozen comparison.
    ledger={"version":VERSION,"since_utc":old["since_utc"],
            "entries":entries}
    comparison=[r for r in entries.values() if r["revue_probability"] is not None]
    league_counts={}
    for sport in SPORTS:
        this=[r for r in entries.values() if r["sport"]==sport]
        available=sum(r["revue_probability"] is not None for r in this)
        league_counts[sport]={
            "source_selections_in_latest_document":by_sport[sport],
            "prospective_locked":len(this),
            "with_revue_comparison":available,
            "missing_same_outcome":len(this)-available,
            "mean_abs_gap_pp":round(sum(abs(r["probability_delta_revue_minus_source_pp"])
                                       for r in this if r["revue_probability"] is not None)/available,2)
                              if available else None,
            "actual_source_deployment_prediction_parity_verified":False,
        }
    snapshot=sorted(entries.values(),key=lambda r:r["locked_at_utc"],reverse=True)
    report={
        "version":VERSION,"status":"prospective_public_forecast_comparison_not_original_model_parity",
        "generated_at_utc":now.isoformat(),"source_repository":SOURCE_REPO,
        "source_commit":source_commit,
        "original_document_generated_at_utc":generated.isoformat(),
        "revue_document_generated_at_utc":own_time.isoformat(),
        "source_document_candidate_count":len(rows),
        "source_ambiguous_fixtures":len(ambiguous),"revue_duplicate_keys":len(dup_own),
        "prospective_predictions_locked":len(entries),
        "new_predictions_locked_this_run":len(new),
        "observed_output_comparisons":len(comparison),
        "excluded_in_current_scan":dict(sorted(reasons.items())),
        "by_sport":league_counts,
        "latest_locked":snapshot[:50],
        "source_output_observed_time_not_original_lock_proof":True,
        "same_inputs_and_sql_verified":False,
        "strict_original_prediction_parity_verified":False,
        "source_moneyline_period_rules_verified":False,
        "real_bets_enabled":False,"live_french_odds_verified":False,
        "paid_api_calls":0,"no_legacy_backfill":True,"CFB_excluded":True,
        "note":"First in-time public source observation per fixture/side retained without revising. Only same fixture, side, pregame data; NHL ML period rule and the original live deployment inputs are unverified. No source profit or betting picks imported.",
    }
    return ledger,report


def download(url,limit=3000000):
    request=Request(url,headers={"Accept":"application/json",
               "User-Agent":"Revue-Phase6-Public-Source-Audit/1.0"})
    with urlopen(request,timeout=28) as response:
        body=response.read(limit+1)
    if len(body)>limit:raise ValueError("Source exceeds fetch limit")
    return json.loads(body)


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--source-data")
    a.add_argument("--source-soccer")
    a.add_argument("--source-commit")
    a.add_argument("--revue",default="docs/match-center-latest.json")
    a.add_argument("--ledger",default="docs/phase6-pregame-ledger.json")
    a.add_argument("--report",default="docs/phase6-predictions-latest.json")
    options=a.parse_args()
    if options.source_data:
        if not options.source_commit:raise ValueError("Offline mode requires source commit SHA")
        sha=options.source_commit
        src=json.loads(Path(options.source_data).read_text(encoding="utf-8"))
        soc=json.loads(Path(options.source_soccer).read_text(encoding="utf-8")) if options.source_soccer else {}
    else:
        sha=download(API,1500000)["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}",sha):raise ValueError("Source commit not pinned")
        src=download(BASE+sha+"/docs/data.json")
        soc=download(BASE+sha+"/docs/soccer_schedule.json")
    oldpath=Path(options.ledger)
    old=json.loads(oldpath.read_text(encoding="utf-8")) if oldpath.is_file() else {}
    revue=json.loads(Path(options.revue).read_text(encoding="utf-8"))
    ledger,report=build(src,soc,revue,old,sha,datetime.now(timezone.utc))
    for name,obj in ((options.ledger,ledger),(options.report,report)):
        p=Path(name);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+"\n",
                     encoding="utf-8")
    print("Phase6:",report["new_predictions_locked_this_run"],"new source snapshots;",
          report["observed_output_comparisons"],"historical descriptive comparisons.",
          "No exact original deployed model parity.")


if __name__=="__main__":main()
