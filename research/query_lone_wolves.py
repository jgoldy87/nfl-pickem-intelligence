
import pandas as pd

from analysis.data_pipeline import build_master_results_from_supabase
from analysis.market_performance import get_market_performance


# ============================================================
# CONFIGURATION
# ============================================================

PLAYERS = ["Jimmy", "John", "Jesse"]

GAME_COLUMNS = ["season", "week", "game_id"]

MARKET_JOIN_COLUMNS = [
    "season",
    "week",
    "away_team",
    "home_team",
]


# ============================================================
# 1. LOAD AND VALIDATE PLAYER PICKS
# ============================================================

df = build_master_results_from_supabase()

df = df[
    df["player"].str.strip().str.lower().isin(
        [player.lower() for player in PLAYERS]
    )
    & df["game_completed"].eq(True)
    & df["pick_correct"].notna()
].copy()

df["player"] = df["player"].str.strip().str.title()

df["confidence"] = pd.to_numeric(
    df["confidence"],
    errors="coerce",
)

df = df.dropna(subset=[
    "confidence",
    "picked_team",
])

if df.empty:
    raise ValueError("No completed player picks found.")


# ============================================================
# 2. KEEP GAMES WITH ALL THREE PLAYERS
# ============================================================

counts = df.groupby(GAME_COLUMNS)["player"].agg(
    ["count", "nunique"]
)

valid_games = counts[
    (counts["count"] == 3)
    & (counts["nunique"] == len(PLAYERS))
].index

complete = df[
    pd.MultiIndex.from_frame(
        df[GAME_COLUMNS]
    ).isin(valid_games)
].copy()

if complete.empty:
    raise ValueError(
        "No completed games with all three players found."
    )


# ============================================================
# 3. IDENTIFY LONE WOLVES AND CALCULATE POINT SWINGS
# ============================================================

lone_records = []

for game_key, group in complete.groupby(GAME_COLUMNS):

    team_counts = group["picked_team"].value_counts()

    # Exactly one player must disagree with the other two.
    if sorted(team_counts.tolist()) != [1, 2]:
        continue

    lone_team = team_counts[
        team_counts == 1
    ].index[0]

    lone_row = group[
        group["picked_team"] == lone_team
    ].iloc[0]

    opponents = group[
        group["picked_team"] != lone_team
    ].copy()

    lone_points = (
        int(lone_row["confidence"])
        if bool(lone_row["pick_correct"])
        else 0
    )

    opponent_points = [
        int(row["confidence"])
        if bool(row["pick_correct"])
        else 0
        for _, row in opponents.iterrows()
    ]

    swings = [
        lone_points - points
        for points in opponent_points
    ]

    lone_records.append({
        "season": lone_row["season"],
        "week": lone_row["week"],
        "game_id": lone_row["game_id"],
        "away_team": lone_row["away_team"],
        "home_team": lone_row["home_team"],
        "Lone Wolf": lone_row["player"],
        "Lone Wolf Pick": lone_team,
        "Confidence": int(lone_row["confidence"]),
        "Correct": bool(lone_row["pick_correct"]),
        "Points Earned": lone_points,
        "Average Opponent Points": (
            sum(opponent_points) / 2
        ),
        "Average Swing": sum(swings) / 2,
        "Combined Swing": sum(swings),
    })

lone_df = pd.DataFrame(lone_records)

if lone_df.empty:
    raise ValueError("No lone-wolf picks found.")


# ============================================================
# 4. LOAD HISTORICAL MARKET DATA
# ============================================================

market_frames = []

for season in sorted(df["season"].unique()):

    market = get_market_performance(int(season))

    if not market.empty:
        market_frames.append(market)

if not market_frames:
    raise ValueError("No historical market data found.")

markets = pd.concat(
    market_frames,
    ignore_index=True,
)

markets = markets[
    (markets["game_type"] == "REG")
    & (markets["winner"] != "TIE")
].copy()

markets = markets[
    MARKET_JOIN_COLUMNS
    + ["market_pick", "market_probability"]
].copy()

# Validate uniqueness rather than silently dropping
# conflicting market records.
duplicate_markets = markets.duplicated(
    subset=MARKET_JOIN_COLUMNS,
    keep=False,
)

if duplicate_markets.any():
    raise ValueError(
        "Duplicate market records found for one or more games."
    )


# ============================================================
# 5. MATCH LONE WOLVES TO MARKET PROBABILITIES
# ============================================================

lone_df = lone_df.merge(
    markets,
    on=MARKET_JOIN_COLUMNS,
    how="left",
    validate="one_to_one",
    indicator=True,
)

unmatched = lone_df["_merge"] != "both"

if unmatched.any():
    print(
        lone_df.loc[
            unmatched,
            MARKET_JOIN_COLUMNS,
        ].to_string(index=False)
    )

    raise ValueError(
        f"{unmatched.sum()} lone-wolf picks have "
        "no matching market data."
    )

lone_df = lone_df.drop(columns=["_merge"])

if (
    lone_df["market_probability"].isna().any()
    or (lone_df["market_probability"] <= 50).any()
    or (lone_df["market_probability"] > 100).any()
):
    raise ValueError(
        "Invalid or ambiguous market probabilities found."
    )

lone_df["Market Type"] = (
    lone_df["Lone Wolf Pick"]
    != lone_df["market_pick"]
).map({
    True: "Underdog",
    False: "Favorite",
})

lone_df["Pick Probability"] = (
    lone_df["market_probability"].where(
        lone_df["Market Type"] == "Favorite",
        100 - lone_df["market_probability"],
    )
)


# ============================================================
# 6. CALCULATE LONE WOLF PERFORMANCE
# ============================================================

lone_df["Expected Win"] = (
    lone_df["Pick Probability"] / 100
)

lone_df["Actual Win"] = (
    lone_df["Correct"].astype(int)
)

lone_df["Expected Points"] = (
    lone_df["Expected Win"]
    * lone_df["Confidence"]
)

lone_df["Actual Points"] = (
    lone_df["Actual Win"]
    * lone_df["Confidence"]
)


def summarize_performance(data, group_columns):

    summary = (
        data.groupby(group_columns)
        .agg(
            Picks=("Actual Win", "size"),
            Wins=("Actual Win", "sum"),
            Expected_Wins=("Expected Win", "sum"),
            Actual_Points=("Actual Points", "sum"),
            Expected_Points=("Expected Points", "sum"),
            Average_Confidence=("Confidence", "mean"),
        )
        .reset_index()
    )

    summary["Win Rate"] = (
        100 * summary["Wins"] / summary["Picks"]
    )

    summary["Expected Win Rate"] = (
        100 * summary["Expected_Wins"] / summary["Picks"]
    )

    summary["Wins Above Expected"] = (
        summary["Wins"] - summary["Expected_Wins"]
    )

    summary["Points Above Expected"] = (
        summary["Actual_Points"]
        - summary["Expected_Points"]
    )

    return summary.round(2)


overall = summarize_performance(
    lone_df.assign(Group="All Lone Wolves"),
    ["Group"],
)

by_type = summarize_performance(
    lone_df,
    ["Market Type"],
)

by_player = summarize_performance(
    lone_df,
    ["Lone Wolf"],
)


# ============================================================
# 7. CALCULATE COMPETITIVE IMPACT
# ============================================================

def summarize_swings(data, group_columns):

    return (
        data.groupby(group_columns)
        .agg(
            Picks=("Average Swing", "size"),
            Positive_Swings=(
                "Average Swing",
                lambda x: (x > 0).sum()
            ),
            Negative_Swings=(
                "Average Swing",
                lambda x: (x < 0).sum()
            ),
            Average_Swing=("Average Swing", "mean"),
            Net_Swing=("Average Swing", "sum"),
            Largest_Gain=("Average Swing", "max"),
            Largest_Loss=("Average Swing", "min"),
        )
        .reset_index()
        .round(2)
    )


by_player_swing = summarize_swings(
    lone_df,
    ["Lone Wolf"],
)

by_type_swing = summarize_swings(
    lone_df,
    ["Market Type"],
)


# ============================================================
# 8. PRINT STREAMLINED REPORT
# ============================================================

print("\nLONE WOLF ANALYSIS")
print("=" * 85)

completed_games = (
    complete[GAME_COLUMNS]
    .drop_duplicates()
    .shape[0]
)

print(f"Completed games analyzed: {completed_games}")
print(f"Total lone-wolf picks: {len(lone_df)}")


# ------------------------------------------------------------
# A. LONE WOLF PERFORMANCE
# ------------------------------------------------------------

print("\n1. LONE WOLF PERFORMANCE")
print("=" * 85)

print("\nOVERALL PERFORMANCE")
print("-" * 85)
print(overall.to_string(index=False))

print("\nPERFORMANCE BY MARKET TYPE")
print("-" * 85)
print(by_type.to_string(index=False))

print("\nPERFORMANCE BY PLAYER")
print("-" * 85)
print(by_player.to_string(index=False))


# ------------------------------------------------------------
# B. COMPETITIVE IMPACT
# ------------------------------------------------------------

print("\n2. COMPETITIVE IMPACT")
print("=" * 85)

positive = (lone_df["Average Swing"] > 0).sum()
negative = (lone_df["Average Swing"] < 0).sum()

print(f"Positive swings: {positive}")
print(f"Negative swings: {negative}")

print(
    f"Average swing: "
    f"{lone_df['Average Swing'].mean():+.2f}"
)

print(
    f"Net swing: "
    f"{lone_df['Average Swing'].sum():+.2f}"
)

print("\nPOINT SWINGS BY PLAYER")
print("-" * 85)
print(by_player_swing.to_string(index=False))

print("\nPOINT SWINGS BY MARKET TYPE")
print("-" * 85)
print(by_type_swing.to_string(index=False))


# ------------------------------------------------------------
# C. PERFORMANCE BY MARKET PROBABILITY
# ------------------------------------------------------------

print("\n3. PERFORMANCE BY MARKET PROBABILITY")
print("=" * 85)

# Probability ranges are expressed as percentages.
probability_bins = [
    0, 30, 40, 50, 60, 70, 100
]

probability_labels = [
    "Below 30%",
    "30-39.9%",
    "40-49.9%",
    "50-59.9%",
    "60-69.9%",
    "70%+",
]

lone_df["Probability Range"] = pd.cut(
    lone_df["Pick Probability"],
    bins=probability_bins,
    labels=probability_labels,
    right=False,
    include_lowest=True,
)

# Include exactly 100% in the final range.
lone_df.loc[
    lone_df["Pick Probability"] == 100,
    "Probability Range"
] = "70%+"

probability_summary = (
    lone_df.groupby(
        "Probability Range",
        observed=True,
    )
    .agg(
        Picks=("Actual Win", "size"),
        Wins=("Actual Win", "sum"),
        Expected_Wins=("Expected Win", "sum"),
        Average_Confidence=("Confidence", "mean"),
        Average_Swing=("Average Swing", "mean"),
        Net_Swing=("Average Swing", "sum"),
    )
    .reset_index()
)

probability_summary["Win Rate"] = (
    100
    * probability_summary["Wins"]
    / probability_summary["Picks"]
)

probability_summary["Expected Win Rate"] = (
    100
    * probability_summary["Expected_Wins"]
    / probability_summary["Picks"]
)

probability_summary["Wins Above Expected"] = (
    probability_summary["Wins"]
    - probability_summary["Expected_Wins"]
)

display_columns = [
    "Probability Range",
    "Picks",
    "Wins",
    "Win Rate",
    "Expected Win Rate",
    "Wins Above Expected",
    "Average_Confidence",
    "Average_Swing",
    "Net_Swing",
]

print(
    probability_summary[display_columns]
    .round(2)
    .to_string(index=False)
)


# ------------------------------------------------------------
# D. BIGGEST GAINS AND LOSSES
# ------------------------------------------------------------

print("\n4. BIGGEST LONE WOLF GAINS AND LOSSES")
print("=" * 85)

display_columns = [
    "week",
    "Lone Wolf",
    "away_team",
    "home_team",
    "Lone Wolf Pick",
    "Market Type",
    "Pick Probability",
    "Confidence",
    "Average Swing",
]

print("\nTOP 5 LONE WOLF GAINS")
print("-" * 85)

print(
    lone_df.nlargest(
        5,
        "Average Swing",
    )[display_columns]
    .round(2)
    .to_string(index=False)
)

print("\nTOP 5 LONE WOLF LOSSES")
print("-" * 85)

print(
    lone_df.nsmallest(
        5,
        "Average Swing",
    )[display_columns]
    .round(2)
    .to_string(index=False)
)


# ============================================================
# 9. OPPONENT PICKING TENDENCIES
# ============================================================

print("\n5. OPPONENT PICKING TENDENCIES")
print("=" * 85)

# Use all completed games with picks from all three players,
# not just games that produced a lone wolf.

opponent_picks = complete[
    complete["player"].isin(["John", "Jesse"])
].copy()

# Reuse the historical market data loaded earlier.
opponent_picks = opponent_picks.merge(
    markets,
    on=MARKET_JOIN_COLUMNS,
    how="left",
    validate="many_to_one",
    indicator=True,
)

# Validate market coverage before calculating percentages.
if (opponent_picks["_merge"] != "both").any():
    raise ValueError(
        "Some opponent picks have no matching market data."
    )

opponent_picks["market_probability"] = pd.to_numeric(
    opponent_picks["market_probability"],
    errors="coerce",
)

if (
    opponent_picks["market_probability"].isna().any()
    or (opponent_picks["market_probability"] <= 50).any()
    or (opponent_picks["market_probability"] > 100).any()
):
    raise ValueError(
        "Invalid market probabilities in opponent analysis."
    )

opponent_picks["Picked Favorite"] = (
    opponent_picks["picked_team"]
    == opponent_picks["market_pick"]
)

# ------------------------------------------------------------
# A. FAVORITE PICKING RATE BY PLAYER
# ------------------------------------------------------------

favorite_rates = (
    opponent_picks.groupby("player")
    .agg(
        Games=("Picked Favorite", "size"),
        Favorite_Picks=("Picked Favorite", "sum"),
    )
    .reset_index()
)

favorite_rates["Underdog_Picks"] = (
    favorite_rates["Games"]
    - favorite_rates["Favorite_Picks"]
)

favorite_rates["Favorite_Pick_Rate"] = (
    100
    * favorite_rates["Favorite_Picks"]
    / favorite_rates["Games"]
)

print("\nFAVORITE PICKING RATE BY PLAYER")
print("-" * 85)

print(
    favorite_rates.round(2).to_string(index=False)
)


# ------------------------------------------------------------
# B. JOHN AND JESSE AGREEMENT
# ------------------------------------------------------------

agreement = opponent_picks.pivot(
    index=GAME_COLUMNS,
    columns="player",
    values="Picked Favorite",
).reset_index()

agreement["Both Favorite"] = (
    agreement["John"] & agreement["Jesse"]
)

agreement["Both Underdog"] = (
    ~agreement["John"] & ~agreement["Jesse"]
)

agreement["Disagree"] = (
    agreement["John"] != agreement["Jesse"]
)

total_games = len(agreement)

print("\nJOHN AND JESSE AGREEMENT")
print("-" * 85)

for label, column in [
    ("Both picked favorite", "Both Favorite"),
    ("Both picked underdog", "Both Underdog"),
    ("Disagreed", "Disagree"),
]:
    count = int(agreement[column].sum())
    rate = 100 * count / total_games

    print(f"{label:<25} {count:>3} / {total_games} ({rate:.1f}%)")


# ------------------------------------------------------------
# C. AGREEMENT BY FAVORITE PROBABILITY
# ------------------------------------------------------------

game_markets = opponent_picks[
    GAME_COLUMNS + ["market_probability"]
].drop_duplicates(subset=GAME_COLUMNS)

agreement = agreement.merge(
    game_markets,
    on=GAME_COLUMNS,
    validate="one_to_one",
)

agreement["Favorite Probability Range"] = pd.cut(
    agreement["market_probability"],
    bins=[50, 60, 70, 80, 100],
    labels=["50-59.9%", "60-69.9%", "70-79.9%", "80%+"],
    right=False,
)

agreement.loc[
    agreement["market_probability"] == 100,
    "Favorite Probability Range"
] = "80%+"

agreement_summary = (
    agreement.groupby(
        "Favorite Probability Range",
        observed=True,
    )
    .agg(
        Games=("Both Favorite", "size"),
        Both_Favorite=("Both Favorite", "sum"),
        Both_Underdog=("Both Underdog", "sum"),
        Disagreed=("Disagree", "sum"),
    )
    .reset_index()
)

agreement_summary["Both_Favorite_Rate"] = (
    100
    * agreement_summary["Both_Favorite"]
    / agreement_summary["Games"]
)

agreement_summary["Both_Underdog_Rate"] = (
    100
    * agreement_summary["Both_Underdog"]
    / agreement_summary["Games"]
)

print("\nAGREEMENT BY FAVORITE PROBABILITY")
print("-" * 85)

print(
    agreement_summary[
        [
            "Favorite Probability Range",
            "Games",
            "Both_Favorite_Rate",
            "Both_Underdog_Rate",
        ]
    ].round(1).to_string(index=False)
)
