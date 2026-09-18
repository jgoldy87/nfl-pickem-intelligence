from analysis.market_performance import (
    get_market_performance,
    summarize_market_performance,
    summarize_probability_buckets,
)


SEASON = 2025


results = get_market_performance(
    season=SEASON
)


print(
    f"\n{SEASON} HISTORICAL MARKET TEST"
)
print("-" * 80)


summary = summarize_market_performance(
    results
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
        results
    )
)

print(
    bucket_summary.to_string(
        index=False
    )
)


print("\nGAMES BY WEEK")
print("-" * 80)

games_by_week = (
    results.groupby("week")
    .size()
)

print(
    games_by_week.to_string()
)