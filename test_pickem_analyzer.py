from analysis.pickem_analyzer import (
    load_results,
    overall_standings,
    weekly_results,
    home_away_records,
    team_records,
    confidence_performance,
)


DATA_FILE = "data/picks_results.csv"


def main():
    print("\nLoading Pick'em results...")

    df = load_results(DATA_FILE)

    print(f"Successfully loaded {len(df)} picks.")
    print(f"Players: {', '.join(sorted(df['player'].unique()))}")

    print("\n" + "=" * 70)
    print("OVERALL STANDINGS")
    print("=" * 70)
    print(overall_standings(df).to_string(index=False))

    print("\n" + "=" * 70)
    print("WEEKLY RESULTS")
    print("=" * 70)
    print(weekly_results(df).to_string(index=False))

    print("\n" + "=" * 70)
    print("HOME VS AWAY RECORDS")
    print("=" * 70)
    print(home_away_records(df).to_string(index=False))

    print("\n" + "=" * 70)
    print("TEAM RECORDS")
    print("=" * 70)
    print(team_records(df).to_string(index=False))

    print("\n" + "=" * 70)
    print("CONFIDENCE PERFORMANCE")
    print("=" * 70)
    print(confidence_performance(df).to_string(index=False))


if __name__ == "__main__":
    main()