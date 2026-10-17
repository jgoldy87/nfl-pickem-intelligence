
import pandas as pd

from analysis.database import load_picks
from analysis.data_pipeline import build_results_from_picks
from analysis.pickem_analyzer import confidence_level_performance


PLAYER = "John"

# Load John's historical picks from Supabase.
picks = load_picks()

john_picks = picks[
    picks["player"].astype(str).str.strip().str.casefold()
    == PLAYER.casefold()
].copy()

# Match the column name expected by the results pipeline.
john_picks = john_picks.rename(
    columns={"pick": "picked_team"}
)

if john_picks.empty:
    raise ValueError("No picks found for John.")

print(f"\nFound {len(john_picks)} picks for John.")

# Build results one season/week at a time.
results = []

for (season, week), weekly_picks in john_picks.groupby(
    ["season", "week"]
):
    print(f"Processing {season} Week {week}...")

    weekly_results = build_results_from_picks(
        weekly_picks
    )
    results.append(weekly_results)

john_results = pd.concat(results, ignore_index=True)

# Exclude unfinished games and ties.
graded = john_results[
    john_results["game_completed"].eq(True)
    & john_results["pick_correct"].notna()
].copy()

print("\nJOHN'S CONFIDENCE PERFORMANCE")
print("=" * 80)

performance = confidence_level_performance(graded)

performance["Win_Pct"] = (
    performance["Win_Pct"] * 100
).round(1)

print(performance.to_string(index=False))

print("\nOVERALL SUMMARY")
print("=" * 80)

correct = int(graded["pick_correct"].sum())
total = len(graded)
points = int(graded["points_earned"].sum())
possible = int(graded["confidence"].sum())

print(f"Completed picks: {total}")
print(f"Correct picks: {correct}")
print(f"Incorrect picks: {total - correct}")
print(f"Win percentage: {correct / total * 100:.1f}%")
print(f"Points earned: {points}")
print(f"Points possible: {possible}")
print(f"Points captured: {points / possible * 100:.1f}%")
