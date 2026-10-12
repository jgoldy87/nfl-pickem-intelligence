
import pandas as pd

from analysis.data_pipeline import build_results_from_picks

# 2022 Week 1: Indianapolis 20, Houston 20
# Simulate two players picking opposite teams.
test_picks = pd.DataFrame([
    {
        "season": 2022,
        "week": 1,
        "player": "Test Player A",
        "game_id": "2022_01_IND_HOU",
        "picked_team": "IND",
        "confidence": 16,
    },
    {
        "season": 2022,
        "week": 1,
        "player": "Test Player B",
        "game_id": "2022_01_IND_HOU",
        "picked_team": "HOU",
        "confidence": 10,
    },
])

results = build_results_from_picks(test_picks)

columns = [
    "player",
    "picked_team",
    "confidence",
    "game_completed",
    "is_tie",
    "pick_correct",
    "points_earned",
]

print("\nTIE SCORING TEST")
print("=" * 75)
print(results[columns].to_string(index=False))

# Verify that both players receive zero points
# without being credited with a win or loss.
assert results["is_tie"].all()
assert results["game_completed"].all()
assert results["pick_correct"].isna().all()
assert results["points_earned"].eq(0).all()

print("\nPASS: Both tied-game picks are ungraded and earn zero points.")

from analysis.pickem_analyzer import (
    overall_standings,
    weekly_results,
    player_week_status,
    lone_wolf_picks,
    unanimous_picks,
)

print("\nANALYTICS TIE TEST")
print("=" * 75)

# Test overall standings.
overall = overall_standings(results)

assert overall["Correct"].eq(0).all()
assert overall["Incorrect"].eq(0).all()
assert overall["Picks"].eq(0).all()
assert overall["Confidence_Points"].eq(0).all()

print("PASS: Overall standings exclude ties from records.")

# Test weekly standings.
weekly = weekly_results(results)

assert weekly["Correct"].eq(0).all()
assert weekly["Incorrect"].eq(0).all()
assert weekly["Picks"].eq(0).all()
assert weekly["Confidence_Points"].eq(0).all()

print("PASS: Weekly standings exclude ties from records.")

# Test player status.
status = player_week_status(results, "Test Player A")

assert status["completed_picks"] == 1
assert status["correct"] == 0
assert status["incorrect"] == 0
assert status["confidence_points"] == 0

print("PASS: Player status handles ties correctly.")

# Test Lone Wolf and unanimous-pick analysis.
assert lone_wolf_picks(results).empty
assert unanimous_picks(results).empty

print("PASS: Pool analyses exclude tied games.")

print("\nALL TIE ANALYTICS TESTS PASSED.")