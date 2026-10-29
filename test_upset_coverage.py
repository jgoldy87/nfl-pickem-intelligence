
import pandas as pd
import nflreadpy as nfl

from analysis.market_performance import get_market_performance

SEASONS = range(2021, 2027)
THROUGH_WEEK = 8

MATCH_COLUMNS = [
    "season",
    "week",
    "game_type",
    "away_team",
    "home_team",
]

rows = []

for season in SEASONS:
    print(f"Checking {season}...")

    # Load completed regular-season games.
    schedule = nfl.load_schedules([season]).to_pandas()

    schedule = schedule[
        (schedule["game_type"] == "REG")
        & (schedule["week"].between(1, THROUGH_WEEK))
        & schedule["home_score"].notna()
        & schedule["away_score"].notna()
        & (schedule["home_score"] != schedule["away_score"])
    ].copy()

    # Load games with market probabilities.
    market = get_market_performance(season=season)

    market = market[
        (market["game_type"] == "REG")
        & (market["week"].between(1, THROUGH_WEEK))
    ].copy()

    # Require valid probabilities and a recognized winner.
    market = market.dropna(
        subset=[
            "away_probability",
            "home_probability",
            "market_probability",
            "market_pick",
            "winner",
        ]
    )

    market = market[
        market["winner"].eq(market["away_team"])
        | market["winner"].eq(market["home_team"])
    ].copy()

    # Match on season, week, game type, and both teams.
    schedule_games = schedule[MATCH_COLUMNS].drop_duplicates()
    market_games = market[MATCH_COLUMNS].drop_duplicates()

    coverage = schedule_games.merge(
        market_games,
        on=MATCH_COLUMNS,
        how="left",
        indicator=True,
        validate="one_to_one",
    )

    completed = len(coverage)
    covered = int((coverage["_merge"] == "both").sum())
    missing = completed - covered

    rows.append({
        "season": season,
        "completed_games": completed,
        "games_with_odds": covered,
        "missing_odds": missing,
        "coverage_pct": (
            round(100 * covered / completed, 2)
            if completed else None
        ),
    })

    missing_games = coverage[
        coverage["_merge"] == "left_only"
    ]

    if not missing_games.empty:
        print("\nGames missing usable odds:")
        print(
            missing_games[
                ["week", "away_team", "home_team"]
            ].to_string(index=False)
        )
        print()

results = pd.DataFrame(rows)

print("\nHISTORICAL ODDS COVERAGE")
print("=" * 75)
print(results.to_string(index=False))
