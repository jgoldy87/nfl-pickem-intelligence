
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis.team_data import load_team_games

for season in range(2023, 2027):
    print(f"\n{'=' * 50}")
    print(f"SEASON {season}")
    print("=" * 50)

    try:
        df = load_team_games(season)

        if df is None or df.empty:
            print("No team data available.")
            continue

        print(f"Total rows: {len(df)}")
        print(f"Teams: {df['team'].nunique()}")
        print(f"Weeks: {sorted(df['week'].unique())}")

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

print("\nHistorical team-data check complete.")
