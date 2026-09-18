import pandas as pd

from analysis.market_performance import (
    get_market_performance,
    summarize_market_performance,
    summarize_probability_buckets,
)


SEASONS = [
    2021,
    2022,
    2023,
    2024,
    2025,
]


season_results = []


for season in SEASONS:

    print(
        f"Loading {season}..."
    )

    results = get_market_performance(
        season=season
    )

    season_results.append(
        results
    )


all_results = pd.concat(
    season_results,
    ignore_index=True,
)


print("\nMULTI-SEASON MARKET TEST")
print("-" * 80)


summary = summarize_market_performance(
    all_results
)


print(
    f"Seasons: "
    f"{SEASONS[0]}-"
    f"{SEASONS[-1]}"
)

print(
    f"Games with usable market data: "
    f"{summary['games']}"
)

print(
    f"Market record: "
    f"{summary['correct']}-"
    f"{summary['incorrect']}"
)

print(
    f"Market accuracy: "
    f"{summary['accuracy']:.1f}%"
)


print("\nPROBABILITY BUCKETS")
print("-" * 80)

bucket_summary = (
    summarize_probability_buckets(
        all_results
    )
)

print(
    bucket_summary.to_string(
        index=False
    )
)


print("\nPERFORMANCE BY SEASON")
print("-" * 80)

season_summary = (
    all_results.groupby("season")
    .agg(
        games=(
            "market_correct",
            "size",
        ),
        correct=(
            "market_correct",
            "sum",
        ),
    )
    .reset_index()
)

season_summary["incorrect"] = (
    season_summary["games"]
    - season_summary["correct"]
)

season_summary["accuracy"] = (
    season_summary["correct"]
    / season_summary["games"]
    * 100
)

season_summary["accuracy"] = (
    season_summary["accuracy"]
    .round(1)
)

print(
    season_summary.to_string(
        index=False
    )
)