#!/usr/bin/env python3
"""No-network freshness, health and source-coverage watchdog for Revue.

Truthful diagnostics only. No opta/injury/lineup capabilities are claimed.
"""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
import argparse,json
from pathlib import Path

MAX_AGE={
    "multisports":timedelta(hours=7),
    "pulsescore_scanner":timedelta(hours=7),
    "football_advanced":timedelta(hours=7),
    "team_advanced":timedelta(hours=7),
    "football_shots":timedelta(hours=14),
}
def parse_time(v):
    try:
        dt=datetime.fromisoformat(str(v).replace("Z","+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except (ValueError,TypeError,OverflowError):return None

def verify_component(name:str,data:dict|None,now:datetime)->dict:
    if not isinstance(data,dict):
        return {"status":"missing","age_hours":None}
    timestamp=parse_time(data.get("generated_at_utc"))
    if timestamp is None:
        return {"status":"invalid_timestamp","age_hours":None}
    age=(now-timestamp).total_seconds()/3600
    status=("future_timestamp" if age<-.05 else
            "stale" if age>MAX_AGE[name].total_seconds()/3600
            else "fresh")
    return {"status":status,"age_hours":round(age,2),
            "updated_at_utc":timestamp.isoformat()}

def build(sources:dict,now:datetime)->dict:
    pairs={
        "multisports":"multisports",
        "scanner":"pulsescore_scanner",
        "football_shadow":"football_advanced",
        "teams_shadow":"team_advanced",
        "football_boxscores":"football_shots",
    }
    checked={key:verify_component(max_age,sources.get(key),now)
             for key,max_age in pairs.items()}
    warnings=[]
    for k,v in checked.items():
        if v["status"]!="fresh":
            warnings.append(k+" "+v["status"])
    prediction=sources.get("multisports") or {}
    odds=sources.get("scanner") or {}
    soccer=sources.get("football_shadow") or {}
    teams=sources.get("teams_shadow") or {}
    espn=sources.get("football_boxscores") or {}
    pulse_status=str(odds.get("odds_status") or "unknown")
    if not pulse_status.startswith("active"):
        warnings.append("PulseScore scanner state: "+pulse_status)
    if odds.get("coverage",{}).get("api_errors"):
        warnings.append("Some bookmaker feeds returned errors; see scanner details")
    excluded=(odds.get("paper") or {}).get("excluded_unsafe_timestamps",0)
    if excluded:
        warnings.append(str(excluded)+" paper entries with uncertain chronology/rule")
    facts={
        "source_files_audited":(sources.get("code_audit") or {}).get("counts",{}).get("files"),
        "multisport_feeds_ok":(prediction.get("overview") or {}).get("feeds_ok"),
        "future_matches":(prediction.get("overview") or {}).get("fixtures"),
        "live_bookmaker_source_status":pulse_status,
        "quote_matches":(odds.get("coverage") or {}).get("requested"),
        "paper_total":(odds.get("paper") or {}).get("n_paper"),
        "paper_settled":(odds.get("paper") or {}).get("graded_pre_start"),
        "quote_close_proxy_sample":(odds.get("price_tracking") or {}).get("n_close_proxy_samples"),
        "football_espn_teams":len((espn.get("teams") or {})),
        "football_xg_licensed":(soccer.get("licensed_advanced_features") or {}).get("records",0),
        "basketball_nfl_mlb_leagues":len((teams.get("leagues") or {})),
        "opta_connected":False,
        "fully_calibrated":False,
        "real_bets_enabled":False,
    }
    return {"generated_at_utc":now.isoformat(),
        "status":"components_fresh" if not warnings else "attention_required",
        "components":checked,"facts":facts,"warnings":warnings,
        "note":"This describes operational health, not betting profitability."}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default="docs")
    ap.add_argument("--output",default="docs/health-latest.json")
    a=ap.parse_args()
    root=Path(a.root)
    files={
        "multisports":"multisports-latest.json",
        "scanner":"engine-v2-latest.json",
        "football_shadow":"football-advanced-shadow.json",
        "teams_shadow":"equipes-avance-shadow.json",
        "football_boxscores":"football-espn-team-features.json",
        "code_audit":"clairvoyance-code-audit.json",
    }
    sources={}
    for k,fname in files.items():
        try:sources[k]=json.loads((root/fname).read_text(encoding="utf-8"))
        except (OSError,ValueError):sources[k]=None
    status=build(sources,datetime.now(timezone.utc))
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("REVUE HEALTH:",status["status"],status["facts"],
          "warnings:",len(status["warnings"]))
if __name__=="__main__":main()
