from analysis.market_performance import (
    get_market_performance,
    summarize_market_performance,
    summarize_probability_buckets,
)


results = get_market_performance(
    season=2026,
    week=1,
)


print("\nMARKET PERFORMANCE MODULE TEST")
print("-" * 80)

print(
    results[
        [
            "game",
            "market_pick",
            "market_probability",
            "winner",
            "market_correct",
        ]
    ].to_string(
        index=False
    )
)

summary = summarize_market_performance(
    results
)


print("\nSUMMARY")
print("-" * 80)

print(
    f"Games: {summary['games']}"
)

print(
    f"Record: "
    f"{summary['correct']}-"
    f"{summary['incorrect']}"
)

print(
    f"Accuracy: "
    f"{summary['accuracy']:.1f}%"
)


bucket_summary = (
    summarize_probability_buckets(
        results
    )
)


print("\nPROBABILITY BUCKETS")
print("-" * 80)

print(
    bucket_summary.to_string(
        index=False
    )
)