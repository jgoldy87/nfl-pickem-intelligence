
import pandas as pd

from analysis.data_pipeline import (
    build_master_results_from_supabase,
)
from analysis.market_performance import (
    get_market_performance,
)


# ============================================================
# 1. LOAD JIMMY'S COMPLETED PICKS
# ============================================================

print("Loading Jimmy's picks from Supabase...")

picks = build_master_results_from_supabase()

picks = picks[
    (picks["player"].str.strip().str.lower() == "jimmy")
    & (picks["game_completed"].eq(True))
    & (picks["pick_correct"].notna())
].copy()

if picks.empty:
    raise ValueError("No completed picks found for Jimmy.")

picks["confidence"] = pd.to_numeric(
    picks["confidence"], errors="coerce"
)

picks = picks.dropna(subset=["confidence"])

print(f"Completed picks: {len(picks)}")


# ============================================================
# 2. LOAD HISTORICAL BETTING MARKETS
# ============================================================

market_frames = []

for season in sorted(picks["season"].unique()):
    season = int(season)
    print(f"Loading {season} betting markets...")

    market = get_market_performance(season)

    if not market.empty:
        market_frames.append(market)

if not market_frames:
    raise ValueError("No historical betting markets found.")

markets = pd.concat(
    market_frames, ignore_index=True
)

markets = markets[
    (markets["game_type"] == "REG")
    & (markets["winner"] != "TIE")
].copy()


# ============================================================
# 3. MATCH PICKS WITH BETTING MARKETS
# ============================================================

join_columns = [
    "season",
    "week",
    "away_team",
    "home_team",
]

market_columns = join_columns + [
    "market_pick",
    "market_probability",
]

markets = markets[market_columns].drop_duplicates(
    subset=join_columns
)

df = picks.merge(
    markets,
    on=join_columns,
    how="left",
    validate="many_to_one",
    indicator=True,
)

unmatched = (df["_merge"] != "both").sum()

print(f"Unmatched picks: {unmatched}")

df = df[df["_merge"] == "both"].copy()

# Exclude games without a clear betting favorite.
df = df[df["market_probability"] > 50].copy()

if df.empty:
    raise ValueError("No picks matched usable betting markets.")


# ============================================================
# 4. IDENTIFY UNDERDOG SELECTIONS
# ============================================================

df["Is_Underdog"] = (
    df["picked_team"] != df["market_pick"]
)

underdogs = df[df["Is_Underdog"]].copy()

underdogs["Correct"] = (
    underdogs["pick_correct"].eq(True)
)

underdogs["Points_Earned"] = (
    underdogs["confidence"].where(
        underdogs["Correct"], 0
    )
)

underdogs["Underdog_Probability"] = (
    100 - underdogs["market_probability"]
)

underdogs["Expected_Points"] = (
    underdogs["confidence"]
    * underdogs["Underdog_Probability"]
    / 100
)


# ============================================================
# 12. ALL-FAVORITES COUNTERFACTUAL
# ============================================================

# Use Jimmy's completed picks with matched market data.
comparison = df.copy()

# Actual points from Jimmy's selections.
comparison["Actual_Points"] = comparison["confidence"].where(
    comparison["pick_correct"].eq(True),
    0,
)

# Under an all-favorites strategy, each game would be
# picked according to the betting market.
#
# For games Jimmy picked as an underdog, the counterfactual
# result is the opposite of his actual result.
# For games Jimmy picked as a favorite, nothing changes.

comparison["Favorite_Correct"] = (
    comparison["pick_correct"].eq(True)
    != comparison["Is_Underdog"]
)

comparison["All_Favorites_Points"] = (
    comparison["confidence"].where(
        comparison["Favorite_Correct"],
        0,
    )
)

# Positive values mean Jimmy gained points by selecting
# the underdog. Negative values mean he lost points.
comparison["Underdog_Impact"] = (
    comparison["Actual_Points"]
    - comparison["All_Favorites_Points"]
)


# ============================================================
# 20. CONFIDENCE ALLOCATION EXPERIMENT
# ============================================================

allocation = df.copy()

# Probability that Jimmy's selected team wins.
allocation["Pick_Probability"] = allocation[
    "market_probability"
].where(
    ~allocation["Is_Underdog"],
    100 - allocation["market_probability"],
)

allocation["Correct"] = allocation["pick_correct"].eq(True)

# Create confidence assignments within each week.
def assign_confidence(group):
    group = group.copy()

    # Original confidence values for this week.
    confidence_values = sorted(
        group["confidence"].tolist()
    )

    # Market-only ranking.
    market_order = group.sort_values(
        ["Pick_Probability", "confidence"],
        ascending=[True, True],
    ).index

    group["Market_Confidence"] = pd.Series(
        confidence_values,
        index=market_order,
    ).reindex(group.index)

    # Normalize original confidence and market probability
    # to comparable within-week percentile ranks.
    original_rank = group["confidence"].rank(
        pct=True, method="average"
    )

    market_rank = group["Pick_Probability"].rank(
        pct=True, method="average"
    )

    group["Hybrid_Score"] = (
        0.5 * original_rank
        + 0.5 * market_rank
    )

    hybrid_order = group.sort_values(
        ["Hybrid_Score", "confidence"],
        ascending=[True, True],
    ).index

    group["Hybrid_Confidence"] = pd.Series(
        confidence_values,
        index=hybrid_order,
    ).reindex(group.index)

    return group


allocation = pd.concat(
    [
        assign_confidence(group)
        for _, group in allocation.groupby(
            ["season", "week"]
        )
    ],
    ignore_index=True,
)

# ============================================================
# 21. STRATEGY SCORING
# ============================================================

strategies = {
    "Actual": "confidence",
    "Market Ranked": "Market_Confidence",
    "Hybrid 50/50": "Hybrid_Confidence",
}

summary_rows = []
weekly_rows = []

for strategy_name, confidence_column in strategies.items():

    test = allocation.copy()

    test["Points"] = test[confidence_column].where(
        test["Correct"],
        0,
    )

    weekly = (
        test.groupby(["season", "week"])
        .agg(
            Points=("Points", "sum"),
            Points_Possible=(confidence_column, "sum"),
        )
        .reset_index()
    )

    weekly["Efficiency"] = (
        weekly["Points"]
        / weekly["Points_Possible"] * 100
    )

    weekly["Strategy"] = strategy_name
    weekly_rows.append(weekly)

    summary_rows.append({
        "Strategy": strategy_name,
        "Total_Points": test["Points"].sum(),
        "Point_Efficiency": (
            test["Points"].sum()
            / test[confidence_column].sum() * 100
        ),
        "Lowest_Weekly_Efficiency": (
            weekly["Efficiency"].min()
        ),
        "Average_Weekly_Efficiency": (
            weekly["Efficiency"].mean()
        ),
    })


# ============================================================
# 22. RESULTS
# ============================================================

summary = pd.DataFrame(summary_rows)

actual_points = summary.loc[
    summary["Strategy"] == "Actual",
    "Total_Points",
].iloc[0]

summary["Points_vs_Actual"] = (
    summary["Total_Points"] - actual_points
)

print("\nCONFIDENCE ALLOCATION STRATEGY COMPARISON")
print("=" * 110)
print(summary.round(1).to_string(index=False))

weekly_results = pd.concat(weekly_rows, ignore_index=True)

weekly_points = weekly_results.pivot(
    index=["season", "week"],
    columns="Strategy",
    values="Points",
)

print("\nWEEKLY CONFIDENCE POINTS")
print("=" * 90)
print(
    weekly_points[list(strategies.keys())].to_string()
)

weekly_efficiency = weekly_results.pivot(
    index=["season", "week"],
    columns="Strategy",
    values="Efficiency",
)

print("\nWEEKLY POINT EFFICIENCY")
print("=" * 90)
print(
    weekly_efficiency[
        list(strategies.keys())
    ].round(1).to_string()
)


# ============================================================
# 23. CONFIDENCE RANKING DIAGNOSTIC
# ============================================================

diagnostic = allocation.copy()

diagnostic["Ranking_Difference"] = (
    diagnostic["confidence"]
    - diagnostic["Market_Confidence"]
)

diagnostic["Actual_Points"] = (
    diagnostic["confidence"].where(
        diagnostic["Correct"], 0
    )
)

diagnostic["Market_Points"] = (
    diagnostic["Market_Confidence"].where(
        diagnostic["Correct"], 0
    )
)

diagnostic["Point_Impact"] = (
    diagnostic["Actual_Points"]
    - diagnostic["Market_Points"]
)

diagnostic["Absolute_Difference"] = (
    diagnostic["Ranking_Difference"].abs()
)

diagnostic["Ranking_Category"] = "Aligned"

diagnostic.loc[
    diagnostic["Ranking_Difference"] >= 3,
    "Ranking_Category",
] = "More Confident"

diagnostic.loc[
    diagnostic["Ranking_Difference"] <= -3,
    "Ranking_Category",
] = "Less Confident"


# ============================================================
# 24. OVERALL RANKING DIAGNOSTIC
# ============================================================

ranking_summary = (
    diagnostic.groupby("Ranking_Category")
    .agg(
        Picks=("confidence", "count"),
        Avg_Ranking_Difference=(
            "Ranking_Difference", "mean"
        ),
        Avg_Absolute_Difference=(
            "Absolute_Difference", "mean"
        ),
        Actual_Points=("Actual_Points", "sum"),
        Market_Points=("Market_Points", "sum"),
        Net_Point_Impact=("Point_Impact", "sum"),
    )
    .reset_index()
)

print("\nCONFIDENCE RANKING DIAGNOSTIC")
print("=" * 110)

print(
    ranking_summary.round(1).to_string(index=False)
)


# ============================================================
# 25. BIGGEST RANKING DISAGREEMENTS
# ============================================================

disagreements = diagnostic[
    diagnostic["Absolute_Difference"] >= 3
].copy()

disagreement_columns = [
    "season",
    "week",
    "picked_team",
    "Is_Underdog",
    "Pick_Probability",
    "confidence",
    "Market_Confidence",
    "Ranking_Difference",
    "Correct",
    "Point_Impact",
]

disagreements = disagreements.sort_values(
    ["Absolute_Difference", "season", "week"],
    ascending=[False, True, True],
)[disagreement_columns]

print("\nBIGGEST CONFIDENCE RANKING DISAGREEMENTS")
print("=" * 130)

print(
    disagreements.round(1).to_string(index=False)
)


# ============================================================
# 26. UNDERDOG VS FAVORITE DISAGREEMENTS
# ============================================================

type_summary = (
    diagnostic.groupby("Is_Underdog")
    .agg(
        Picks=("confidence", "count"),
        Avg_Absolute_Difference=(
            "Absolute_Difference", "mean"
        ),
        Net_Point_Impact=("Point_Impact", "sum"),
    )
    .reset_index()
)

type_summary["Pick_Type"] = type_summary[
    "Is_Underdog"
].map({
    True: "Underdog",
    False: "Favorite",
})

print("\nRANKING DIFFERENCES BY PICK TYPE")
print("=" * 95)

print(
    type_summary[
        [
            "Pick_Type",
            "Picks",
            "Avg_Absolute_Difference",
            "Net_Point_Impact",
        ]
    ].round(1).to_string(index=False)
)
