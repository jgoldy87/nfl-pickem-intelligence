
import sys
from pathlib import Path

# Allow imports from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis.market_performance import get_market_performance

for season in range(2023, 2027):
    print(f"\n{'=' * 50}")
    print(f"SEASON {season}")
    print("=" * 50)

    try:
        df = get_market_performance(season)

        if df is None or df.empty:
            print("No market data available.")
            continue

        print(f"Total games: {len(df)}")

        if "game_type" in df.columns:
            df = df[df["game_type"] == "REG"].copy()
            print(f"Regular-season games: {len(df)}")

        if "winner" in df.columns:
            completed = df[df["winner"].notna()]
            print(f"Completed games: {len(completed)}")

        if "market_probability" in df.columns:
            valid = df[df["market_probability"].notna()]
            print(f"Games with market probabilities: {len(valid)}")

            if not valid.empty:
                print(
                    "Market probability range: "
                    f"{valid['market_probability'].min():.1f}% - "
                    f"{valid['market_probability'].max():.1f}%"
                )

        if "week" in df.columns and not df.empty:
            print(f"Week range: {df['week'].min()} - {df['week'].max()}")

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

print("\nHistorical market-data check complete.")
