"""Revue's independent REST backend, with Clairvoyance-compatible GET signatures.

The reference runs FastAPI + SQLAlchemy with proprietary state. Our first
adapter exposes only verified available NHL/MLB fixtures from Revue. SQL IDs,
snapshots, markets and predictions are NOT claimed to be original values.
No wagering/write endpoints and no CFB.
"""
from __future__ import annotations
from datetime import date,datetime,timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api_revue.fixtures import SourceUnavailable,fixtures_from_files,fixture_rows
from api_revue.nhl_stats import teams as official_teams, goalies as official_goalies, skaters as official_skaters, moneypuck as season_moneypuck


class NHLGameOut(BaseModel):
    id: int
    espn_id: str
    game_date: date | None
    game_time_utc: datetime | None
    status: str
    home_team: str
    away_team: str
    home_score: int | None
    away_score: int | None
    home_moneyline: int | None
    away_moneyline: int | None
    over_under: float | None


class MLBGameOut(NHLGameOut):
    home_pitcher: str | None
    away_pitcher: str | None
    venue: str | None


class NHLTeamStatOut(BaseModel):
    id: int
    team_id: int
    team_abbrev: str
    team_name: str | None
    season: str
    game_type_id: int
    games_played: int | None
    wins: int | None
    losses: int | None
    ot_losses: int | None
    goals_for: int | None
    goals_against: int | None
    goals_for_per_game: float | None
    goals_against_per_game: float | None
    pp_pct: float | None
    pk_pct: float | None
    shots_for_per_game: float | None
    shots_against_per_game: float | None
    offensive_zone_time_pct: float | None
    defensive_zone_time_pct: float | None
    neutral_zone_time_pct: float | None


class NHLGoalieStatOut(BaseModel):
    id: int
    player_id: int
    player_name: str | None
    team_abbrev: str | None
    games_played: int | None
    saves_even_strength: int | None
    save_pct_even_strength: float | None
    saves_power_play: int | None
    save_pct_power_play: float | None
    saves_short_handed: int | None
    save_pct_short_handed: float | None
    overall_save_pct: float | None
    goals_against_avg: float | None


class NHLSkaterStatOut(BaseModel):
    id: int
    player_id: int
    player_name: str | None
    team_abbrev: str | None
    shots_wrist: int | None
    shots_snap: int | None
    shots_slap: int | None
    shots_backhand: int | None
    shots_tip: int | None
    shots_deflected: int | None
    shots_wrap_around: int | None
    avg_speed: float | None
    top_speed: float | None


def create_app(*, root: Path | None = None, clock=None) -> FastAPI:
    directory=root if root is not None else Path(__file__).resolve().parents[1]/"docs"
    now=clock if clock is not None else lambda:datetime.now(timezone.utc)
    app=FastAPI(
        title="Revue — Clairvoyance source-contract lab",
        version="0.1.0",
        description="Original read-only API adapter, incomplete source equivalence. No real bets, no secret database.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://matttgic.github.io","https://revue-api-tawny.vercel.app"],
        allow_credentials=False,allow_methods=["GET"],allow_headers=["Content-Type"],
    )

    @app.get("/health")
    def health():
        # Service liveness != freshness of every data provider.
        return {"status":"ok"}

    def read_schedule(league:str,day:date):
        try:
            return fixtures_from_files(directory,league,day,now())
        except SourceUnavailable as e:
            # No stale or fabricated fallback. Users see actual API outage.
            raise HTTPException(status_code=503, detail=str(e)) from e

    @app.get("/nhl/schedule",response_model=list[NHLGameOut])
    def nhl_schedule(game_date:date=Query(default_factory=date.today)):
        return read_schedule("NHL",game_date)

    def read_nhl_data(func,*args):
        try:
            return func(directory,now(),*args)
        except SourceUnavailable as exc:
            raise HTTPException(status_code=503,detail=str(exc)) from exc

    @app.get("/nhl/teams",response_model=list[NHLTeamStatOut])
    def nhl_teams(response:Response):
        response.headers["X-Revue-Parity"]="partial: independent NHL IDs; not Clairvoyance SQL row IDs"
        return read_nhl_data(official_teams)

    @app.get("/nhl/goalies",response_model=list[NHLGoalieStatOut])
    def nhl_goalies(response:Response,min_games:int=Query(default=1,ge=1)):
        response.headers["X-Revue-Parity"]="partial: NHL season stats, no confirmed starters"
        return read_nhl_data(official_goalies,min_games)

    @app.get("/nhl/skaters",response_model=list[NHLSkaterStatOut])
    def nhl_skaters(response:Response,team:str|None=Query(default=None)):
        response.headers["X-Revue-Parity"]="partial: unknown NHL Edge stats are null"
        try:
            return read_nhl_data(official_skaters,team)
        except ValueError as exc:
            raise HTTPException(status_code=422,detail=str(exc)) from exc

    @app.get("/nhl/moneypuck")
    def nhl_moneypuck(response:Response,situation:str=Query(default="all")):
        response.headers["X-Revue-Parity"]="partial: MoneyPuck last observed snapshot; NOT live"
        try:
            return read_nhl_data(season_moneypuck,situation.lower())
        except ValueError as exc:
            raise HTTPException(status_code=422,detail=str(exc)) from exc

    @app.get("/mlb/schedule",response_model=list[MLBGameOut])
    def mlb_schedule(game_date:date=Query(default_factory=date.today)):
        return read_schedule("MLB",game_date)

    @app.get("/mlb/games/{espn_id}",response_model=MLBGameOut)
    def mlb_game(espn_id:str):
        if not espn_id.isdecimal():
            raise HTTPException(status_code=404,detail="Game not found")
        now_value=now()
        # Current snapshot is at most a few days of fixtures, not original
        # database history. Search only dates explicitly present in the feed.
        from api_revue.fixtures import snapshot
        try:
            doc=snapshot(directory/"multisports-latest.json",now_value)
            raw=doc.get("competitions",{}).get("MLB",{}).get("games",[])
            exact=[x for x in raw if str(x.get("event_id"))==espn_id]
            if not exact:
                raise HTTPException(status_code=404,detail="Game not found")
            start=datetime.fromisoformat(exact[0]["start_utc"].replace("Z","+00:00"))
            entries=read_schedule("MLB",start.date())
        except SourceUnavailable as e:
            raise HTTPException(status_code=503,detail=str(e)) from e
        except (KeyError,ValueError,TypeError):
            raise HTTPException(status_code=503,detail="Malformed fixture source")
        match=next((g for g in entries if g["espn_id"]==espn_id),None)
        if not match:
            raise HTTPException(status_code=404,detail="Game not found")
        return match

    @app.get("/predictions/")
    def predictions(game_date:date=Query(default_factory=date.today)):
        # The reference's MLB + NHL outcome dict relies on original Elo
        # database and goalie/xG provider state. NEVER substitute Revue priors
        # and claim identical predictions on source inputs.
        raise HTTPException(
            status_code=503,
            detail="Source-parity prediction unavailable: original Elo, goalie, market and time-stamped data inputs are not proven identical.",
        )

    @app.get("/revue/parity")
    def source_parity():
        import json
        p=directory/"reproduction-exacte-audit.json"
        try:
            data=json.loads(p.read_text(encoding="utf-8"))
            return {
                "reference_commit":data["source_commit"],
                "exact_end_to_end_parity":data["exact_end_to_end_parity"],
                "exact_reproduction_percent":data["exact_reproduction_percent"],
                "source_routes":data["backend"]["source_route_count"],
                "full_original_route_parity_verified":data["backend"]["end_to_end_verified_equivalent_routes"],
                "read_only":True,
                "not_original_backend":True,
            }
        except (OSError,KeyError,ValueError,TypeError):
            raise HTTPException(status_code=503,detail="Parity evidence unavailable")

    return app


app=create_app()
