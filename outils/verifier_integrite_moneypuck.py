"""Check consistency of published, attributed MoneyPuck NHL snapshots."""
import json
import math
from pathlib import Path


def validate(teams, goalies):
    problems = []
    if teams.get("source") != "MoneyPuck.com" or goalies.get("source") != "MoneyPuck.com":
        problems.append("Missing MoneyPuck attribution")
    if teams.get("is_live") is not False or goalies.get("is_live") is not False:
        problems.append("Historical data incorrectly marked live")
    if goalies.get("confirmed_starters") is not False:
        problems.append("Unverified goalie starters")
    if teams.get("current_season") != goalies.get("current_season"):
        problems.append("Season disagreement")
    for kind, doc, status_key, count_key in (
        ("teams", teams, "status", "rows"),
        ("goalies", goalies, "statuses", "goalies"),
    ):
        records = doc.get("seasons", {})
        statuses = doc.get(status_key, {})
        if set(records) != set(statuses):
            problems.append(f"{kind}: inconsistent season keys")
        for season, rows in records.items():
            state = statuses.get(season, {})
            if state.get(count_key) != len(rows):
                problems.append(f"{kind}/{season}: reported row count differs")
            if (state.get("status") == "available") != bool(rows):
                problems.append(f"{kind}/{season}: availability differs")
            seen = set()
            for row in rows:
                if row.get("season") != season:
                    problems.append(f"{kind}/{season}: season mismatch")
                key = (row.get("team"), row.get("situation") if kind == "teams" else row.get("name"))
                if key in seen:
                    problems.append(f"{kind}/{season}: duplicate record")
                seen.add(key)
                if kind == "teams":
                    if row.get("situation") not in ("all", "5on5"):
                        problems.append(f"{kind}/{season}: unexpected situation")
                    for field in ("xg_share", "save_pct"):
                        value = row.get(field)
                        if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1):
                            problems.append(f"{kind}/{season}: invalid {field}")
                else:
                    if row.get("starter_status") != "unknown":
                        problems.append(f"{kind}/{season}: misleading starter status")
                    x, g, s = (row.get(k) for k in ("xg_against", "goals_against", "gsax"))
                    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (x, g, s)) or abs(x - g - s) > 0.011:
                        problems.append(f"{kind}/{season}: GSAx arithmetic failure")
    return problems


def main():
    t = json.loads(Path("docs/moneypuck-nhl-latest.json").read_text())
    g = json.loads(Path("docs/moneypuck-goalies-latest.json").read_text())
    problems = validate(t, g)
    print(json.dumps({"status": "PASS" if not problems else "FAIL", "issues": problems}, indent=2))
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
