
import pandas as pd

from analysis.market_performance import (
    get_market_performance,
    summarize_upset_buckets,
)

SEASON = 2023
THROUGH_WEEK = 8

games = get_market_performance(season=SEASON)

games = games[
    (games["game_type"] == "REG")
    & games["week"].between(1, THROUGH_WEEK)
].copy()

print("\n2023 MARKET DATA")
print("=" * 75)
print(f"Total games: {len(games)}")

print("\nMARKET PROBABILITY DISTRIBUTION")
print(
    games["market_probability"]
    .describe()
    .to_string()
)

print("\nGAMES WITH 50% MARKET PROBABILITY")
print("=" * 75)

even_games = games[
    games["market_probability"] == 50
]

if even_games.empty:
    print("None found.")
else:
    print(
        even_games[
            [
                "week",
                "game",
                "away_moneyline",
                "home_moneyline",
                "away_probability",
                "home_probability",
                "market_pick",
                "winner",
            ]
        ].to_string(index=False)
    )

print("\nOTHER POSSIBLE EXCLUSIONS")
print("=" * 75)

excluded = games[
    games["market_probability"].isna()
    | ~(
        games["winner"].eq(games["away_team"])
        | games["winner"].eq(games["home_team"])
    )
]

if excluded.empty:
    print("No missing probabilities or invalid winners.")
else:
    print(
        excluded[
            [
                "week",
                "game",
                "market_probability",
                "winner",
            ]
        ].to_string(index=False)
    )

summary = summarize_upset_buckets(games)

print("\nRECONCILIATION")
print("=" * 75)
print(f"Market dataset: {len(games)}")
print(f"Upset analysis: {summary['games'].sum()}")
print(
    f"Difference: "
    f"{len(games) - summary['games'].sum()}"
)
