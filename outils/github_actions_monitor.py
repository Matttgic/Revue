#!/usr/bin/env python3
"""Observed GitHub Actions metadata, never original Clairvoyance SQL logs."""
from __future__ import annotations
import argparse,json,os
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.request import Request,urlopen

SOURCE="https://api.github.com/repos/Matttgic/Revue/actions/runs?branch=main&per_page=100"
PREFIX="https://github.com/Matttgic/Revue/actions/runs/"
STATES={"queued","in_progress","waiting","requested","pending","completed"}
CONCLUSIONS={"success","failure","cancelled","skipped","timed_out","neutral","action_required","startup_failure",None}

def aware(v):
    if not isinstance(v,str):raise ValueError("Invalid timestamp")
    t=datetime.fromisoformat(v.replace("Z","+00:00"))
    if t.tzinfo is None:raise ValueError("Naive timestamp")
    return t.astimezone(timezone.utc)

def compile_runs(raw,now):
    if now.tzinfo is None:raise ValueError("Naive current time")
    now=now.astimezone(timezone.utc)
    if not isinstance(raw,dict) or not isinstance(raw.get("workflow_runs"),list):
        raise ValueError("Malformed GitHub Actions JSON")
    rows=[];seen=set()
    for x in raw["workflow_runs"]:
        if not isinstance(x,dict):continue
        name,ident=x.get("name"),x.get("id")
        status,conclusion=x.get("status"),x.get("conclusion")
        sha=x.get("head_sha")
        if (not isinstance(name,str) or not name.startswith("Revue - ") or
            type(ident) is not int or ident<=0 or ident in seen or
            status not in STATES or conclusion not in CONCLUSIONS or
            x.get("head_branch")!="main" or x.get("html_url")!=PREFIX+str(ident) or
            not isinstance(sha,str) or len(sha)!=40 or
            not all(ch in "0123456789abcdef" for ch in sha.lower())):
            continue
        try:
            created=aware(x["created_at"]);updated=aware(x["updated_at"])
        except (ValueError,KeyError,TypeError):continue
        if created>now+timedelta(minutes=3) or updated>now+timedelta(minutes=3) or updated<created:
            continue
        seen.add(ident)
        rows.append({
            "id":ident,"workflow":name,"status":status,
            "conclusion":conclusion if status=="completed" else None,
            "created_at_utc":created.isoformat(),
            "updated_at_utc":updated.isoformat(),
            "commit_sha":sha,"url":PREFIX+str(ident),
            "event":str(x.get("event") or "unknown"),
            "is_clairvoyance_original_run":False,
            "is_proof_of_source_ingestion":False
        })
    rows.sort(key=lambda x:(x["created_at_utc"],x["id"]),reverse=True)
    rows=rows[:80]
    if not rows:raise ValueError("No verified Revue public workflow runs")
    groups={}
    for r in rows:
        g=groups.setdefault(r["workflow"],{
            "workflow":r["workflow"],"latest":None,"last_success":None,
            "last_failure":None,"observed_count":0})
        g["observed_count"]+=1
        if g["latest"] is None:g["latest"]=r
        if g["last_success"] is None and r["conclusion"]=="success":
            g["last_success"]=r
        if g["last_failure"] is None and r["conclusion"] in {"failure","timed_out","startup_failure"}:
            g["last_failure"]=r
    return {
        "generated_at_utc":now.isoformat(),
        "status":"verified_public_github_actions_history_not_provider_health",
        "source":"GitHub REST Actions list runs: Matttgic/Revue, main",
        "source_url":SOURCE,
        "pagination":"Recent 100 runs on main; max 80 Revue runs, not complete lifetime history",
        "known_workflows":len(groups),"observed_runs":len(rows),
        "observed_failures":sum(x["conclusion"] in {"failure","timed_out","startup_failure"} for x in rows),
        "observed_cancelled":sum(x["conclusion"]=="cancelled" for x in rows),
        "not_original_clairvoyance_daily_logs":True,
        "not_real_time_provider_status":True,"real_bets_enabled":False,
        "workflows":sorted(groups.values(),key=lambda x:x["workflow"]),"runs":rows
    }

def fetch(token=None):
    headers={"User-Agent":"RevuePersonalMonitor/1.0",
             "Accept":"application/vnd.github+json",
             "X-GitHub-Api-Version":"2022-11-28"}
    if token:headers["Authorization"]="Bearer "+token
    with urlopen(Request(SOURCE,headers=headers),timeout=18) as resp:
        return json.load(resp)

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--output",default="docs/github-workflows-latest.json")
    cli.add_argument("--input",help="Use offline GitHub response")
    args=cli.parse_args()
    raw=json.loads(Path(args.input).read_text()) if args.input else fetch(os.getenv("GITHUB_TOKEN"))
    d=compile_runs(raw,datetime.now(timezone.utc))
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(d,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print("GitHub Actions history:",d["observed_runs"],"runs",d["known_workflows"],"workflows")

if __name__=="__main__":main()
