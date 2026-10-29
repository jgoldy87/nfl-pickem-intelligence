
import pandas as pd

from analysis.market_performance import (
    get_market_performance,
    summarize_upset_buckets,
)

SEASONS = range(2021, 2027)
THROUGH_WEEK = 8

season_rows = []
bucket_rows = []

for season in SEASONS:
    print(f"Loading {season}...")

    results = get_market_performance(season=season)

    # Compare the same portion of every season.
    results = results[
        (results["week"] >= 1)
        & (results["week"] <= THROUGH_WEEK)
    ].copy()

    # Restrict to regular season when this field is available.
    if "game_type" in results.columns:
        results = results[
            results["game_type"].isin(["REG", "regular"])
        ].copy()
    elif "season_type" in results.columns:
        results = results[
            results["season_type"].isin(["REG", "regular"])
        ].copy()

    summary = summarize_upset_buckets(results)
    summary.insert(0, "season", season)
    bucket_rows.append(summary)

    games = int(summary["games"].sum())
    upsets = int(summary["upsets"].sum())
    expected = float(summary["expected_upsets"].sum())

    season_rows.append({
        "season": season,
        "games": games,
        "upsets": upsets,
        "expected_upsets": expected,
        "upset_rate": (
            100 * upsets / games if games else None
        ),
        "expected_upset_rate": (
            100 * expected / games if games else None
        ),
        "upset_difference": upsets - expected,
    })

season_comparison = pd.DataFrame(season_rows)
bucket_comparison = pd.concat(
    bucket_rows,
    ignore_index=True,
)

print("\nHISTORICAL UPSET COMPARISON")
print(f"Regular season through Week {THROUGH_WEEK}")
print("=" * 90)

print(
    season_comparison.round(2).to_string(
        index=False
    )
)

print("\nUPSETS BY PROBABILITY BUCKET")
print("=" * 90)

print(
    bucket_comparison[
        [
            "season",
            "probability_bucket",
            "games",
            "upsets",
            "expected_upsets",
            "upset_rate",
            "upset_difference",
        ]
    ].to_string(index=False)
)

print("\nDATA COVERAGE")
print("=" * 90)
for row in season_rows:
    print(
        f"{row['season']}: "
        f"{row['games']} games with usable odds"
    )
