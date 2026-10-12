import pandas as pd

from analysis.data_pipeline import build_master_results_from_supabase


# Build current results from Supabase picks + NFL results
df = build_master_results_from_supabase()

# 2026 season, completed games only
df = df[
    (df["season"] == 2026)
    & (df["game_completed"] == True)
].copy()


# ---------------------------------------------------------
# POINTS LOST
# ---------------------------------------------------------

df["points_lost"] = df["confidence"].where(
    df["pick_correct"] == False,
    0
)


# ---------------------------------------------------------
# TEAM LOYALTY
# ---------------------------------------------------------

loyalty = (
    df.groupby(["player", "picked_team"])
    .agg(
        Times_Picked=("game_id", "count"),
        Wins=("pick_correct", "sum"),
        Points_Earned=("points_earned", "sum"),
        Points_Lost=("points_lost", "sum"),
        Avg_Confidence=("confidence", "mean"),
    )
    .reset_index()
)

# Record
loyalty["Wins"] = loyalty["Wins"].astype(int)
loyalty["Losses"] = loyalty["Times_Picked"] - loyalty["Wins"]

loyalty["Record"] = (
    loyalty["Wins"].astype(str)
    + "-"
    + loyalty["Losses"].astype(str)
)

# Win %
loyalty["Win_Pct"] = (
    loyalty["Wins"] / loyalty["Times_Picked"] * 100
).round(1)

# Round average confidence
loyalty["Avg_Confidence"] = loyalty["Avg_Confidence"].round(2)


# ---------------------------------------------------------
# CLEAN COLUMN NAMES
# ---------------------------------------------------------

loyalty = loyalty.rename(
    columns={
        "player": "Player",
        "picked_team": "Team",
        "Times_Picked": "Times Picked",
        "Win_Pct": "Win %",
        "Points_Earned": "Points Earned",
        "Points_Lost": "Points Lost",
        "Avg_Confidence": "Avg Confidence",
    }
)


# ---------------------------------------------------------
# SORT
# ---------------------------------------------------------

loyalty = loyalty.sort_values(
    by=[
        "Player",
        "Times Picked",
        "Avg Confidence",
    ],
    ascending=[
        True,
        False,
        False,
    ],
)


# ---------------------------------------------------------
# FINAL DISPLAY
# ---------------------------------------------------------

loyalty = loyalty[
    [
        "Player",
        "Team",
        "Times Picked",
        "Record",
        "Win %",
        "Avg Confidence",
        "Points Earned",
        "Points Lost",
    ]
]


print("\nTEAM LOYALTY")
print("=" * 95)

for player in loyalty["Player"].unique():

    print(f"\n{player.upper()}")
    print("-" * 95)

    player_results = loyalty[
        loyalty["Player"] == player
    ].drop(columns="Player")

    print(player_results.to_string(index=False))