"""Read-only admin-source signatures and Revue's own observed CI history.

The original app/routers/admin.py reads SQL DailyLog. Revue never has
access to those rows or the original scheduler. /admin/* therefore exposes
the original shape with unknown SQL values (None/empty) and explicit source
warnings; /revue/workflows exposes genuine GitHub Actions execution records.
"""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
from api_revue.fixtures import SourceUnavailable,timestamp

ORIGINAL_SCRAPERS=("espn_mlb","espn_nhl","nhl_edge","moneypuck","settlement")
MAX_AGE=timedelta(hours=12)

def observed_actions(root:Path,now:datetime)->dict:
    try:
        report=json.loads((root/"github-workflows-latest.json").read_text(encoding="utf-8"))
        if not isinstance(report,dict) or report.get("status")!="verified_public_github_actions_history_not_provider_health":
            raise ValueError("Wrong report type")
        seen=timestamp(report["generated_at_utc"])
        current=now.astimezone(timezone.utc)
        if seen>current+timedelta(minutes=2) or current-seen>MAX_AGE:
            raise ValueError("Stale / future workflow evidence")
        if (report.get("not_original_clairvoyance_daily_logs") is not True or
            report.get("not_real_time_provider_status") is not True or
            report.get("real_bets_enabled") is not False or
            not isinstance(report.get("workflows"),list) or
            not isinstance(report.get("runs"),list) or not report["runs"]):
            raise ValueError("Incomplete workflow provenance")
        # The original feed producer already validates IDs, GitHub URLs and
        # timestamps. Fail closed if even a read cached file was corrupted.
        for item in report["runs"]:
            ident=item.get("id")
            if (type(ident) is not int or
                item.get("url")!="https://github.com/Matttgic/Revue/actions/runs/"+str(ident) or
                item.get("is_clairvoyance_original_run") is not False):
                raise ValueError("Corrupt GitHub run identity")
        return report
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        raise SourceUnavailable("Verified Revue GitHub Actions evidence unavailable or stale") from exc

def source_admin_status(root:Path,now:datetime)->dict:
    """No fake successful original scrapes or inferred cron next_run."""
    output={"scrapers":{k:None for k in ORIGINAL_SCRAPERS},
            "next_pipeline_run":None,
            "original_daily_log_database_available":False,
            "original_scheduler_state_available":False,
            "revue_source_notice":"Original SQL DailyLog and APScheduler unavailable; the Revue execution feed is separate."}
    try:
        source=observed_actions(root,now)
        output["revue_github_actions"]={
            "generated_at_utc":source["generated_at_utc"],
            "observed_runs":source["observed_runs"],
            "known_workflows":source["known_workflows"],
            "observed_failures":source["observed_failures"],
            "not_original_daily_logs":True}
    except SourceUnavailable:
        output["revue_github_actions"]=None
    return output

def source_admin_logs(limit:int,scraper:str|None)->list:
    """No SQL log rows exist. Do not forge source DailyLog with GitHub runs."""
    return []

def revue_workflows(root:Path,now:datetime,
                    workflow:str|None=None,limit:int=50)->dict:
    report=observed_actions(root,now)
    if workflow:
        match=[g for g in report["workflows"] if g["workflow"]==workflow]
        if not match: return {**report,"workflows":[],"runs":[],"filtered_count":0}
        rows=[r for r in report["runs"] if r["workflow"]==workflow]
        return {**report,"workflows":match,"runs":rows[:limit],
                "filtered_count":len(rows)}
    return {**report,"runs":report["runs"][:limit],
            "filtered_count":len(report["runs"])}
