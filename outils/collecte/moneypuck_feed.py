#!/usr/bin/env python3
"""MoneyPuck official-download NHL team metrics for Revue (personal, non-commercial).

Data terms: https://moneypuck.com/data.htm (attribution required).
ONLY download the CSV explicitly offered on the public data-download page.
No page scraping, no unofficial endpoints, no redistribution of source CSV.
The output is a small attributed, derived research snapshot; not a prediction.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import io
import json
import math
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from modeles.reproduction.clairvoyance_moneypuck_parser import read_team_csv, numeric

SOURCE_PAGE = "https://moneypuck.com/data.htm"
BASE = "https://moneypuck.com/moneypuck/playerData/seasonSummary"
SITUATIONS = ("5on5", "all")
USER_AGENT = "RevueResearch/1.0 (personal non-commercial; attribution MoneyPuck.com)"


@dataclass(frozen=True)
class Download:
    body: str
    last_modified: str | None = None


def season_year(now: datetime) -> int:
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return now.year if now.month >= 8 else now.year - 1


def season_label(start: int) -> str:
    return f"{start}-{start + 1}"


def source_url(start: int) -> str:
    if start < 2008 or start > 2100:
        raise ValueError("Invalid season year")
    return f"{BASE}/{start}/regular/teams.csv"


def fetch_csv(start: int) -> Download:
    request = Request(source_url(start), headers={
        "User-Agent": USER_AGENT, "Accept": "text/csv"
    })
    with urlopen(request, timeout=25) as response:
        if response.status != 200:
            raise RuntimeError(f"MoneyPuck returned HTTP {response.status}")
        content_type = response.headers.get("Content-Type", "")
        body = response.read(5_000_001)
        if len(body) > 5_000_000:
            raise ValueError("MoneyPuck file unexpectedly large")
        if content_type and "html" in content_type.lower():
            raise ValueError("Expected CSV, received HTML")
        return Download(body.decode("utf-8-sig"), response.headers.get("Last-Modified"))


def _clean_fraction(value: object) -> float | None:
    if value is None:
        return None
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(n) or n < 0:
        return None
    if n > 1:
        n /= 100  # MoneyPuck exports vary between fraction and percent.
    return round(n, 4) if n <= 1 else None


def derive_rows(content: str, year: int) -> list[dict]:
    """Keep only valid observed NHL teams and strict regular-season situations."""
    if not {"team", "situation", "xGoalsFor", "xGoalsAgainst"}.issubset(
        set(content.splitlines()[0].lstrip("\ufeff").split(",")) if content else set()
    ):
        raise ValueError("Expected MoneyPuck team CSV columns missing")
    # The source CSV iceTime is measured in SECONDS, while the reference
    # Clairvoyance normalizer mistakenly treats it as minutes. Keep that
    # normalizer unchanged for exact formula parity, and correct units HERE.
    raw_by_key: dict[tuple[str, str], dict] = {}
    for raw in csv.DictReader(io.StringIO(content)):
        team_key = str(raw.get("team") or raw.get("Team") or "").strip().upper()
        situation_key = str(raw.get("situation") or "all").strip()
        raw_by_key[(team_key, situation_key)] = raw
    output: dict[tuple[str, str], dict] = {}
    for row in read_team_csv(content):
        team = row["team"]
        situation = row["situation"]
        if situation not in SITUATIONS or not (2 <= len(team) <= 4 and team.isalpha()):
            continue
        share = _clean_fraction(row["x_goals_pct"])
        xf, xa = row["x_goals_for"], row["x_goals_against"]
        if share is None or xf is None or xa is None or not all(
            math.isfinite(x) and x >= 0 for x in (xf, xa)
        ):
            continue
        gp = row.get("games_played")
        if gp is not None and gp <= 0:
            continue
        original_row = raw_by_key.get((team, situation)) or {}
        ice_seconds = numeric(original_row.get("iceTime"))
        if ice_seconds is None or not math.isfinite(ice_seconds) or ice_seconds <= 0:
            continue

        def per_60(metric: str) -> float | None:
            count = numeric(original_row.get(metric))
            if count is None or not math.isfinite(count) or count < 0:
                return None
            return round(count * 3600 / ice_seconds, 4)

        xg_for_60 = per_60("xGoalsFor")
        xg_against_60 = per_60("xGoalsAgainst")
        shots_for_60 = per_60("shotsOnGoalFor")
        shots_against_60 = per_60("shotsOnGoalAgainst")
        # Fail closed on implausible per-60 units (column semantics changed).
        if (xg_for_60 is None or xg_against_60 is None or
            shots_for_60 is None or shots_against_60 is None or
            max(xg_for_60, xg_against_60) > 20 or
            max(shots_for_60, shots_against_60) > 120):
            continue
        output[(team, situation)] = {
            "team": team, "situation": situation, "season": season_label(year),
            "games_played": gp, "xg_share": share,
            "xg_for_60": xg_for_60,
            "xg_against_60": xg_against_60,
            "shots_for_60": shots_for_60,
            "shots_against_60": shots_against_60,
            "save_pct": _clean_fraction(row["save_pct"]),
            "pdo": row["pdo"],
        }
    return sorted(output.values(), key=lambda r: (r["situation"], -r["xg_share"], r["team"]))


def _http_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        return parsed.astimezone(timezone.utc).isoformat() if parsed.tzinfo else None
    except (ValueError, TypeError):
        return None


def create_snapshot(now: datetime, fetcher=fetch_csv) -> dict:
    """Collect current + previous season independently; NEVER relabel fallback."""
    year = season_year(now)
    seasons, status = {}, {}
    for season in (year, year - 1):
        label = season_label(season)
        try:
            result = fetcher(season)
            rows = derive_rows(result.body, season)
            if not rows:
                raise ValueError("No valid team xG rows")
            seasons[label] = rows
            status[label] = {
                "status": "available", "teams": len({r["team"] for r in rows}),
                "rows": len(rows), "source_updated_utc": _http_date(result.last_modified),
                "download_url": source_url(season),
            }
        except (HTTPError, URLError, OSError, TimeoutError, ValueError,
                UnicodeError, RuntimeError) as exc:
            seasons[label] = []
            status[label] = {"status": "unavailable", "teams": 0, "rows": 0,
                             "error_type": type(exc).__name__,
                             "source_updated_utc": None, "download_url": source_url(season)}
    if not any(seasons.values()):
        raise RuntimeError("MoneyPuck official CSVs unavailable; refusing to publish empty/stale-as-new data")
    return {
        "generated_at_utc": now.astimezone(timezone.utc).isoformat(),
        "source": "MoneyPuck.com", "source_page": SOURCE_PAGE,
        "licence_scope": "Personal non-commercial use; source attribution required",
        "data_type": "official regular-season team-level CSV; derived metrics",
        "unit_note": "MoneyPuck iceTime is seconds; per-60 rates = count * 3600 / iceTime (seconds). Reference Clairvoyance parser remains unchanged.",
        "is_live": False,
        "current_season": season_label(year),
        "status": status, "seasons": seasons,
        "disclaimer": "Observations historiques, pas de donnees temps reel, ni pronostics ou cotes.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/moneypuck-nhl-latest.json")
    args = parser.parse_args()
    result = create_snapshot(datetime.now(timezone.utc))
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")
    print("MoneyPuck derived team observations:",
          {k: v["teams"] for k, v in result["status"].items()})


if __name__ == "__main__":
    main()
