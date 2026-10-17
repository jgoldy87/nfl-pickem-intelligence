import pandas as pd

from analysis.data_pipeline import (
    build_master_results_from_supabase,
)


# ============================================================
# 1. LOAD COMPLETED PICKS
# ============================================================

df = build_master_results_from_supabase()

df = df[
    (df["season"] == 2026)
    & (df["game_completed"].eq(True))
    & (df["pick_correct"].notna())
].copy()

df["Correct"] = df["pick_correct"].astype(int)

df["Confidence"] = pd.to_numeric(
    df["confidence"], errors="coerce"
)

df["Points_Earned"] = pd.to_numeric(
    df["points_earned"], errors="coerce"
)

df = df.dropna(
    subset=["Confidence", "Points_Earned"]
).copy()


# ============================================================
# 2. INCLUDE BOTH TEAMS INVOLVED IN EACH GAME
# ============================================================

away = df.copy()
away["Team"] = away["away_team"]

home = df.copy()
home["Team"] = home["home_team"]

team_picks = pd.concat(
    [away, home],
    ignore_index=True,
)


# ============================================================
# 3. PLAYER PERFORMANCE BY NFL TEAM
# ============================================================

performance = (
    team_picks.groupby(["Team", "player"])
    .agg(
        Games=("Correct", "count"),
        Correct=("Correct", "sum"),
        Avg_Confidence=("Confidence", "mean"),
        Total_Confidence=("Confidence", "sum"),
        Points_Earned=("Points_Earned", "sum"),
    )
    .reset_index()
)

performance["Incorrect"] = (
    performance["Games"] - performance["Correct"]
)

performance["Accuracy"] = (
    performance["Correct"]
    / performance["Games"]
    * 100
)

performance["Efficiency"] = (
    performance["Points_Earned"]
    / performance["Total_Confidence"]
    * 100
)

performance["Record"] = (
    performance["Correct"].astype(str)
    + "-"
    + performance["Incorrect"].astype(str)
)


# ============================================================
# 4. FIND BEST PREDICTOR OF EACH TEAM
# ============================================================

performance["Best_Accuracy"] = (
    performance.groupby("Team")["Accuracy"]
    .transform("max")
)

leaders = performance[
    performance["Accuracy"].eq(
        performance["Best_Accuracy"]
    )
].copy()

team_leaders = (
    leaders.groupby("Team")
    .agg(
        Best_Predictor=(
            "player",
            lambda x: ", ".join(sorted(x))
        ),
        Best_Accuracy=("Accuracy", "max"),
        Best_Record=("Record", "first"),
    )
    .sort_index()
)

print("\nBEST PREDICTOR OF EACH NFL TEAM — 2026")
print("=" * 95)
print(team_leaders.round(1).to_string())


# ============================================================
# 5. ACCURACY COMPARISON MATRIX
# ============================================================

accuracy_matrix = performance.pivot(
    index="Team",
    columns="player",
    values="Accuracy",
)

accuracy_matrix = accuracy_matrix.round(1)

print("\nTEAM PREDICTION ACCURACY BY PLAYER (%)")
print("=" * 95)
print(accuracy_matrix.to_string())


# ============================================================
# 6. CONFIDENCE EFFICIENCY MATRIX
# ============================================================

efficiency_matrix = performance.pivot(
    index="Team",
    columns="player",
    values="Efficiency",
)

efficiency_matrix = efficiency_matrix.round(1)

print("\nTEAM CONFIDENCE EFFICIENCY BY PLAYER (%)")
print("=" * 95)
print(efficiency_matrix.to_string())


# ============================================================
# 7. COUNT TEAM ACCURACY LEADERS
# ============================================================

# Count outright leads separately from ties.

leader_counts = (
    leaders.groupby("Team")["player"]
    .transform("count")
)

leaders["Lead_Type"] = leader_counts.map(
    lambda n: "Outright" if n == 1 else "Tied"
)

leader_summary = (
    leaders.groupby(["player", "Lead_Type"])
    .size()
    .unstack(fill_value=0)
)

for column in ["Outright", "Tied"]:
    if column not in leader_summary.columns:
        leader_summary[column] = 0

leader_summary["Total_Leads"] = (
    leader_summary["Outright"]
    + leader_summary["Tied"]
)

leader_summary = leader_summary[
    ["Outright", "Tied", "Total_Leads"]
].sort_values(
    ["Outright", "Total_Leads"],
    ascending=False,
)

print("\nNUMBER OF NFL TEAMS LED BY EACH PLAYER")
print("=" * 70)
print(leader_summary.to_string())


# ============================================================
# 8. PERFECT AND WINLESS TEAM RECORDS
# ============================================================

perfect = performance[
    performance["Accuracy"] == 100
].sort_values(["player", "Team"])

winless = performance[
    performance["Accuracy"] == 0
].sort_values(["player", "Team"])

print("\nPERFECT TEAM PREDICTION RECORDS")
print("=" * 70)

if perfect.empty:
    print("No perfect records.")
else:
    print(
        perfect[
            ["player", "Team", "Record", "Points_Earned"]
        ].to_string(index=False)
    )

print("\nWINLESS TEAM PREDICTION RECORDS")
print("=" * 70)

if winless.empty:
    print("No winless records.")
else:
    print(
        winless[
            ["player", "Team", "Record", "Total_Confidence"]
        ].to_string(index=False)
    )