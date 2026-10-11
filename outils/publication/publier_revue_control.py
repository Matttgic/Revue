"""Verified static snapshots for GitHub Pages. No paid API calls."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from api_revue.operational import ledger_data,control_status

def generate(root:Path,now:datetime)->tuple[dict,dict]:
    if now.tzinfo is None: raise ValueError("Aware clock required")
    now=now.astimezone(timezone.utc)
    ledger=ledger_data(root)
    state=control_status(root,now)
    if ledger["real_bets_enabled"] or not ledger["paper_only"] or not state["not_live_provider_health"]:
        raise ValueError("Untrusted Revue data provenance")
    ledger["generated_at_utc"]=now.isoformat()
    ledger["static_snapshot"]=True
    state["static_snapshot"]=True
    return ledger,state

def publish(root:Path,now:datetime)->tuple[Path,Path]:
    ledger,state=generate(root,now)
    files=(root/"revue-control-ledger-latest.json",root/"revue-control-state-latest.json")
    for dest,data in zip(files,(ledger,state)):
        dest.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return files

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--docs",default="docs")
    root=Path(arg.parse_args().docs)
    a,b=publish(root,datetime.now(timezone.utc))
    print("Revue Control Center snapshots:",a,b,"no odds API calls")

if __name__=="__main__":main()
