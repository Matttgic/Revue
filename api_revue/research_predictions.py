"""Transparent independent research forecasts from verified Revue input snapshots.

Unlike /predictions/ in the original Clairvoyance app, this route does NOT
pretend to use the original SQL Elo, MoneyPuck snapshots or confirmed goalies.
It reuses the mathematically tested independent predictor and publishes the
same formula fields plus an explicit first-party provenance envelope.
Never retroactively forecasts fixtures already under way.
"""
from __future__ import annotations

from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import json, math

from api_revue.fixtures import SourceUnavailable,snapshot,timestamp
from api_revue.mlb_elo import mlb_elo_from_file
from modeles.reproduction.clairvoyance_predictor import Game,mlb,nhl

MIN_LEAD=timedelta(minutes=20)
NHL_REPORT_MAX_AGE=timedelta(hours=24)


def _nhl_schedule_mapping(doc:dict) -> dict:
    if doc.get("status") != "verified_fixture_identity_pairs":
        raise SourceUnavailable("No verified NHL-to-ESPN fixture identity evidence")
    lookup={}
    for row in doc.get("mappings") or []:
        key=str(row.get("nhl_game_id"))
        if key in lookup:
            raise SourceUnavailable("Ambiguous official NHL ID in ESPN map")
        lookup[key]=row
    return lookup


def _nhl_model_rows(root:Path,now:datetime,day:date) -> list[dict]:
    try:
        report=snapshot(root/"nhl-clairvoyance-shadow-latest.json",now,max_age_hours=24)
        mapping=snapshot(root/"parite-nhl-espn-id-map.json",now,max_age_hours=72)
    except SourceUnavailable:
        return []
    audit=report.get("point_in_time_audit") or {}
    if (report.get("status")!="experimental_not_calibrated" or
        report.get("bookmaker_odds_available") is not False or
        audit.get("status")!="verified_temporal_bounds" or
        audit.get("as_of_utc")!=report.get("generated_at_utc")):
        raise SourceUnavailable("NHL source has not passed pregame temporal audit")
    match_by_id=_nhl_schedule_mapping(mapping)
    output=[]
    seen=set()
    for row in report.get("games") or []:
        try:
            start=timestamp(row["start_utc"])
            nhl_id=str(row["event_id"])
            if not (start.date()==day and now+MIN_LEAD<=start):
                continue
            if nhl_id in seen:
                raise SourceUnavailable("Duplicate NHL event in immutable prediction report")
            seen.add(nhl_id)
            source_time=timestamp(report["generated_at_utc"])
            if not source_time+MIN_LEAD<=start:
                raise SourceUnavailable("NHL source forecast was not recorded pre-game")
            p=match_by_id.get(nhl_id)
            if (not p or p.get("home")!=row.get("home") or
                p.get("away")!=row.get("away") or
                timestamp(p["start_utc"])!=start or
                not str(p.get("original_espn_id","")).isdecimal()):
                # No fallback to made-up ESPN identifiers
                continue
            xg=row.get("xg_5v5_share_pct") or {}
            eh,ea=row.get("home_elo_proxy"),row.get("away_elo_proxy")
            if any(type(v) not in (int,float) or not math.isfinite(v) for v in
                   (eh,ea,xg.get("home"),xg.get("away"))):
                raise SourceUnavailable("NHL research feature is not a finite number")
            if not 0<=xg["home"]<=100 or not 0<=xg["away"]<=100:
                raise SourceUnavailable("NHL xG share outside realistic bounds")
            historic=row.get("historical_goalie_proxy") or {}
            def goalie(side):
                value=(historic.get(side) or {}).get("save_pct")
                if value is None:
                    return None
                if type(value) not in (float,int) or not math.isfinite(value) or not 0<value<=1:
                    raise SourceUnavailable("Invalid goalie percentage")
                return float(value)
            g=Game(
                str(p["original_espn_id"]),row["home"],row["away"],
                game_date=start.date().isoformat(),game_time_utc=start.isoformat(),
            )
            result=nhl(g,float(eh),float(ea),float(xg["home"]),float(xg["away"]),
                       goalie("home"),goalie("away"))
            # A genuine pre-match snapshot already contains this rounded
            # probability. This prevents silently serving new/unmatched
            # forecasts under a historically locked event.
            if (result["model_home_win_prob"]!=row.get("home_win") or
                result["model_away_win_prob"]!=row.get("away_win")):
                raise SourceUnavailable("Computed NHL formula differs from pregame source prediction")
            output.append({
                "sport":"nhl","official_event_id":nhl_id,"espn_game_id":g.espn_id,
                "formula_result":result,
                "input_snapshot_utc":source_time.isoformat(),
                "match_start_utc":start.isoformat(),
                "features":{"home_elo_proxy":eh,"away_elo_proxy":ea,
                            "xg_5v5_share_pct":xg,
                            "goalies_are_confirmed_starters":False},
                "source_input_parity_with_original":False,
                "real_bets_enabled":False,
                "pick_recommendation_verified":False,
            })
        except (KeyError,ValueError,TypeError) as exc:
            raise SourceUnavailable("Inconsistent source NHL forecast features") from exc
    return output


def _mlb_model_rows(root:Path,now:datetime,day:date) -> list[dict]:
    fixture_doc=snapshot(root/"multisports-latest.json",now,max_age_hours=8)
    if fixture_doc.get("status")!="prototype_non_calibre":
        raise SourceUnavailable("Unverified fixture source state")
    elo=mlb_elo_from_file(root,now)
    ratings={x["team"]:x["rating"] for x in elo["rows"]}
    data=(fixture_doc.get("competitions") or {}).get("MLB")
    if not isinstance(data,dict):
        raise SourceUnavailable("MLB fixture league absent")
    output=[]
    seen=set()
    for row in data.get("games") or []:
        try:
            start=timestamp(row["start_utc"])
            if not (start.date()==day and now+MIN_LEAD<=start):
                continue
            ident=str(row["event_id"])
            if not ident.isdecimal() or ident in seen:
                raise SourceUnavailable("Duplicate or invalid source MLB ESPN identifier")
            seen.add(ident)
            home,away=row["home"],row["away"]
            if not home or not away or home==away:
                raise SourceUnavailable("Invalid source MLB teams")
            # The original predictor itself uses default Elo 1500 on missing
            # teams. Treat missing first-party training data as unavailable:
            # a 1500 fallback could obscure a coverage failure.
            if home not in ratings or away not in ratings:
                continue
            g=Game(ident,home,away,game_date=start.date().isoformat(),
                   game_time_utc=start.isoformat())
            output.append({
                "sport":"mlb","official_event_id":ident,"espn_game_id":ident,
                "formula_result":mlb(g,ratings[home],ratings[away]),
                "input_snapshot_utc":fixture_doc["generated_at_utc"],
                "match_start_utc":start.isoformat(),
                "features":{"home_elo_revue":ratings[home],
                            "away_elo_revue":ratings[away],
                            "historical_mlb_final_games":elo["completed_espn_games"],
                            "same_original_sql_ratings":False},
                "source_input_parity_with_original":False,
                "real_bets_enabled":False,
                "pick_recommendation_verified":False,
            })
        except (KeyError,ValueError,TypeError) as exc:
            raise SourceUnavailable("Inconsistent source MLB forecast fixture") from exc
    return output


def predictions_from_files(root:Path,day:date,now:datetime) -> dict:
    if now.tzinfo is None:
        raise ValueError("Aware observation time mandatory")
    now=now.astimezone(timezone.utc)
    if day < now.date() or day > (now+timedelta(days=3)).date():
        raise ValueError("Only prospective games within the next three UTC days")
    errors={}
    rows=[]
    for name,build in (("nhl",_nhl_model_rows),("mlb",_mlb_model_rows)):
        try:
            rows.extend(build(root,now,day))
        except SourceUnavailable as exc:
            errors[name]=str(exc)
    rows.sort(key=lambda v:(v["match_start_utc"],v["sport"],v["espn_game_id"]))
    if not rows:
        raise SourceUnavailable(
            "No authentic pregame research predictions available for this date; "
            +json.dumps(errors,ensure_ascii=False)
        )
    return {
        "generated_at_utc":now.isoformat(),
        "game_date_utc":day.isoformat(),
        "status":"revue_research_same_formula_not_original_source_inputs",
        "source_input_parity_with_original":False,
        "identical_original_clairvoyance_predictions_proven":False,
        "not_original_predictions_endpoint":True,
        "not_live_odds":True,
        "real_bets_enabled":False,
        "count":len(rows),"predictions":rows,
        "unavailable_sports":errors,
        "note":"Original MLB/NHL formula, original 401 ESPN IDs when verified, Revue's observed inputs. No original SQL Elo, no confirmed goalie starters, no source bookmaker market odds and no warranted profitability.",
    }
