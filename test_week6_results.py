
import nflreadpy as nfl

schedules = nfl.load_schedules([2026]).to_pandas()

week6 = schedules[
    (schedules["season"] == 2026)
    & (schedules["week"] == 6)
].copy()

print("Week 6 games found:", len(week6))
print("\nAvailable columns:")
print(week6.columns.tolist())

columns = [
    "game_id",
    "gameday",
    "away_team",
    "home_team",
    "away_score",
    "home_score",
    "result",
]

available = [col for col in columns if col in week6.columns]

print("\nWEEK 6 RESULTS")
print(week6[available].to_string(index=False))

if {"away_score", "home_score"}.issubset(week6.columns):
    completed = week6[
        week6["away_score"].notna()
        & week6["home_score"].notna()
    ]
    print("\nGames with both scores populated:", len(completed))
