"""NHL source-input forensics: independently explain measured Clairvoyance gaps.

Source reading (not redistribution):
  - public Clairvoyance docs/data.json (fixtures, published NHL 5v5 xG,
    numeric published pick probabilities);
  - Revue's frozen NHL shadow and verified original-output comparisons.

The *model* behind published picks may differ from original backend source
predictor.py, so we do not assert which Elo/goalie parameters caused a gap.
We never import original source code, bets, bookmaker odds, or ROI.
"""
from __future__ import annotations
import argparse,json,math,re
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.request import Request,urlopen

REF="https://raw.githubusercontent.com/Purple-Wraith/clairvoyance-backend/main/docs/data.json"
VERSION="nhl_input_gap_forensics_v1"
REQUIRED_GAP="public_original_source_fixture_and_nhl_output_diagnostic"
LIMIT=timedelta(hours=72)
TEAM=re.compile(r"^[A-Z]{2,4}$")
NOTE_XG=re.compile(r"\bxGF%:\s*([A-Z]{2,4})\s+(\d+(?:\.\d+)?)\s*/\s*([A-Z]{2,4})\s+(\d+(?:\.\d+)?)")
SKIP={"real_bet":False,"betting_recommendations_verified":False,"live_french_odds_verified":False}

def when(value):
    if not isinstance(value,str):raise ValueError("Timestamp is absent")
    t=datetime.fromisoformat(value.replace("Z","+00:00"))
    if t.tzinfo is None:raise ValueError("Missing timezone")
    return t.astimezone(timezone.utc)

def number(value,low=None,high=None):
    return type(value) in (int,float) and math.isfinite(value) and (
        low is None or value>=low) and (high is None or value<=high)

def strict_input_match(data,shadow,gap,now):
    if (gap.get("status")!=REQUIRED_GAP or
        gap.get("real_bets_enabled") is not False or
        gap.get("exact_prediction_parity_verified") is not False or
        shadow.get("status")!="experimental_not_calibrated" or
        shadow.get("bookmaker_odds_available") is not False):
        return "invalid_provenance"
    try:
        orig=when(data["generated"])
        source_gap=when(gap["source_inputs"]["data"]["observed_at_utc"])
        shadow_time=when(shadow["generated_at_utc"])
        gap_shadow={when(x["revue_observed_at_utc"])
            for x in gap.get("nhl_source_vs_revue",[])
            if x.get("status")=="compared" and x.get("market")=="moneyline_including_overtime"}
    except (KeyError,ValueError,TypeError,AttributeError):
        return "missing_timestamp"
    if any(x>now+timedelta(minutes=2) or now-x>LIMIT for x in (orig,source_gap,shadow_time)):
        return "stale_or_future_snapshot"
    if orig!=source_gap or (gap_shadow and gap_shadow!={shadow_time}):
        return "different_observation_snapshots"
    return "aligned_observation_snapshots"

def original_games(data):
    out={};duplicate=set()
    for raw in ((data.get("nhl") or {}).get("today") or [])+(
            (data.get("nhl") or {}).get("tomorrow") or []):
        if not isinstance(raw,dict):continue
        eid=str(raw.get("id") or "")
        home,away=raw.get("home"),raw.get("away")
        if not re.fullmatch(r"[0-9]{8,14}",eid) or not isinstance(home,str) or not isinstance(away,str) or not TEAM.fullmatch(home) or not TEAM.fullmatch(away) or home==away:
            continue
        if eid in out:duplicate.add(eid)
        out[eid]=raw
    for eid in duplicate:out.pop(eid,None)
    return out,duplicate

def raw_source_xg(data,team):
    raw=(((data.get("mp") or {}).get("teams") or {}).get(team) or {}).get("5on5") or {}
    x=raw.get("xgfPct")
    return round(x*100,3) if number(x,0,1) else None

def extract_xg_note(raw,home,away):
    match=NOTE_XG.search(str(raw.get("note") or ""))
    if not match:return None
    mapping={match.group(1):float(match.group(2)),match.group(3):float(match.group(4))}
    if len(mapping)!=2 or home not in mapping or away not in mapping:return None
    if any(not number(v,0,100) for v in mapping.values()):return None
    return {"home":mapping[home],"away":mapping[away]}

def group(rows):
    if not rows:return {"comparisons":0,"mean_absolute_gap_pp":None,
                        "max_absolute_gap_pp":None,"gaps_at_least_10pp":0}
    gaps=[abs(r["probability_gap_pp"]) for r in rows]
    return {"comparisons":len(rows),
            "mean_absolute_gap_pp":round(sum(gaps)/len(gaps),2),
            "max_absolute_gap_pp":round(max(gaps),2),
            "gaps_at_least_10pp":sum(x>=10 for x in gaps)}

def make(data,shadow,gap,now):
    if now.tzinfo is None:raise ValueError("Aware clock required")
    now=now.astimezone(timezone.utc)
    condition=strict_input_match(data,shadow,gap,now)
    status="nhl_forensics_verified_observation_alignment" if condition=="aligned_observation_snapshots" else "nhl_forensics_waiting_same_observation"
    output={"version":VERSION,"status":status,"generated_at_utc":now.isoformat(),
        "reference_repository":"Purple-Wraith/clairvoyance-backend",
        "source_diagnostic":"docs/clairvoyance-real-output-gap.json",
        "source_input_guard":condition,
        **SKIP,"exact_prediction_replication_verified":False,
        "same_underlying_model_features_verified":False,
        "backend_predictor_is_the_published_best_bet_model_verified":False,
        "input_summary":{},"model_summary":{},"match_diagnostics":[],
        "investigation_queue":[],"limitations":"Same public 5v5 MoneyPuck xG input ≠ same Elo, goaltender, injuries, model stage or observation-time configuration. Repeated published probabilities require investigation but are not by themselves proof of a bug."}
    if condition!="aligned_observation_snapshots":
        output["investigation_queue"]=[{"priority":1,"reason":"Source and Revue snapshots require timestamp alignment before comparing values."}]
        return output
    originals,dups=original_games(data)
    own={str(g["event_id"]):g for g in shadow.get("games",[]) if isinstance(g,dict) and g.get("event_id")}
    observed=when(data["generated"])
    xg_rows=[]
    for eid,row in originals.items():
        rival=own.get(eid)
        if not rival or row.get("home")!=rival.get("home") or row.get("away")!=rival.get("away"):
            continue
        try:fixture_at=when(row["date"]);revue_at=when(rival["start_utc"])
        except (TypeError,ValueError,KeyError):continue
        if abs((fixture_at-revue_at).total_seconds())>300 or min(fixture_at,revue_at)<=observed:
            continue
        h,a=row["home"],row["away"]
        xref={"home":raw_source_xg(data,h),"away":raw_source_xg(data,a)}
        xrev=rival.get("xg_5v5_share_pct") or {}
        if not all(number(xref[s],0,100) and number(xrev.get(s),0,100) for s in ("home","away")):
            xg_status="missing_input"
        elif all(abs(xref[s]-xrev[s])<=.15 for s in ("home","away")):
            xg_status="same_xg_both_teams"
        else:xg_status="different_xg_input"
        xg_rows.append({"event_id":eid,"key":"NHL:"+eid,
            "home":h,"away":a,"kickoff_utc":fixture_at.isoformat(),
            "reference_5v5_xg_pct":xref,"revue_5v5_xg_pct":
                {s:round(xrev[s],3) if number(xrev.get(s),0,100) else None for s in ("home","away")},
            "xg_identity":xg_status})
    byid={row["event_id"]:row for row in xg_rows}
    compare=[]
    note_samples=0;notes_equal=0
    picks=(data.get("bestBets") or [])
    for bet in picks:
        if not isinstance(bet,dict) or bet.get("sport")!="NHL":continue
        parts=re.fullmatch(r"([A-Z]{2,4}) @ ([A-Z]{2,4})",str(bet.get("game") or ""))
        if not parts:continue
        for row in xg_rows:
            if row["home"]!=parts.group(2) or row["away"]!=parts.group(1):continue
            note=extract_xg_note(bet,row["home"],row["away"])
            if note and row["xg_identity"]!="missing_input":
                note_samples+=1
                if all(abs(note[s]-row["reference_5v5_xg_pct"][s])<=.15 for s in ("home","away")):
                    notes_equal+=1
            break
    for original in gap.get("nhl_source_vs_revue",[]):
        if not isinstance(original,dict) or original.get("status")!="compared":continue
        key=original.get("key","")
        if not re.fullmatch(r"NHL:[0-9]{8,14}",key):continue
        eid=key.split(":")[1]
        matched=byid.get(eid)
        if not matched:continue
        if original.get("home")!=matched["home"] or original.get("away")!=matched["away"]:
            continue
        try:
            if when(original["kickoff_utc"])!=when(matched["kickoff_utc"]) or (
                when(original["original_observed_at_utc"])!=observed):
                continue
        except (ValueError,KeyError,TypeError):continue
        p,q=original.get("original_probability"),original.get("revue_probability")
        if not (number(p,0,1) and number(q,0,1)):continue
        market=original.get("market")
        if market not in ("moneyline_including_overtime","full_game_total"):continue
        side=original.get("side")
        if market=="moneyline_including_overtime" and (side not in ("home","away") or original.get("line") is not None):
            continue
        if market=="full_game_total" and (side not in ("over","under") or not number(original.get("line"),.5,15)):
            continue
        compared={**matched,"market":market,"side":side,"line":original.get("line"),
            "reference_probability":p,"revue_probability":q,
            "probability_gap_pp":round((q-p)*100,2),
            "absolute_gap_pp":round(abs(q-p)*100,2),
            "identical_underlying_features_verified":False}
        compare.append(compared)
    moneyline=[x for x in compare if x["market"]=="moneyline_including_overtime"]
    totals=[x for x in compare if x["market"]=="full_game_total"]
    rep={}
    for r in totals:
        k=(r["market"],r["side"],r["reference_probability"])
        rep.setdefault(k,set()).add(r["event_id"])
    clusters=[{"market":m,"side":s,"original_probability":p,
        "distinct_games":len(ids),"event_ids":sorted(ids),
        "hypothesis":"Same published numeric probability repeated across different matches; investigate placeholder, rule or model override before treating this as dynamic."}
        for (m,s,p),ids in rep.items() if len(ids)>=3]
    clusters.sort(key=lambda x:(-x["distinct_games"],x["market"],x["side"]))
    exact_pair=sum(x["xg_identity"]=="same_xg_both_teams" for x in xg_rows)
    changed_pair=sum(x["xg_identity"]=="different_xg_input" for x in xg_rows)
    unexplained=[x for x in moneyline if x["xg_identity"]=="same_xg_both_teams" and x["absolute_gap_pp"]>=5]
    unexplained.sort(key=lambda r:-r["absolute_gap_pp"])
    output["input_summary"]={"same_event_and_kickoff_nhl":len(xg_rows),
        "identical_5v5_xg_both_teams":exact_pair,
        "different_5v5_xg":changed_pair,
        "missing_5v5_xg":len(xg_rows)-exact_pair-changed_pair,
        "ambiguous_reference_event_ids":len(dups),
        "published_pick_xg_notes_usable":note_samples,
        "published_pick_xg_notes_equal_reference_input":notes_equal}
    output["model_summary"]={"all":group(compare),
        "moneyline":group(moneyline),"totals":group(totals),
        "identical_xg_but_moneyline_gap_over_5pp":len(unexplained),
        "repeated_reference_probability_clusters":clusters}
    output["match_diagnostics"]=sorted(compare,key=lambda x:(-x["absolute_gap_pp"],x["key"],x["market"],x["side"]))
    output["investigation_queue"]=[
        {"priority":1,"category":"same_xg_different_moneyline_output",
         "count":len(unexplained),
         "top_event_ids":[x["event_id"] for x in unexplained[:7]],
         "description":"Same public 5v5 xG for both sides, yet moneyline p differs by >=5 percentage points. Audit Elo, goalie proxies, model family and snapshots separately; causality not established."},
        {"priority":2,"category":"repeated_total_probability",
         "count":len(clusters),
         "top_event_ids":clusters[0]["event_ids"][:9] if clusters else [],
         "description":"Repeated totals across games; inspect original market-selection or fallback behavior, do not retroactively optimize Revue against published picks."},
        {"priority":3,"category":"temporal_and_premium_inputs",
         "count":len(compare),
         "top_event_ids":[],
         "description":"Obtain temporally aligned goalie/lineup/Elo snapshots before claiming model output equality; raw SQL/premium inputs not public."}
    ]
    return output

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--docs",default="docs")
    parser.add_argument("--output",default="docs/clairvoyance-nhl-forensics.json")
    args=parser.parse_args()
    root=Path(args.docs)
    def local(n):return json.loads((root/n).read_text(encoding="utf8"))
    req=Request(REF,headers={"User-Agent":"Revue-Noncommercial-Source-Parity/1.0","Accept":"application/json"})
    with urlopen(req,timeout=23) as response:
        raw=response.read(2500000)
        if len(raw)>=2500000:raise ValueError("Reference payload too large")
    data=json.loads(raw)
    out=make(data,local("nhl-clairvoyance-shadow-latest.json"),
             local("clairvoyance-real-output-gap.json"),datetime.now(timezone.utc))
    result=Path(args.output);result.parent.mkdir(parents=True,exist_ok=True)
    result.write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf8")
    print(out["status"],out["input_summary"],out["model_summary"].get("moneyline",{}),
          "no source code or bets copied")

if __name__=="__main__":main()
