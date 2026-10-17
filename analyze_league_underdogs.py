
import pandas as pd

from analysis.market_performance import get_market_performance
from analysis.team_data import load_team_games
from analysis.rankings import get_team_rankings

SEASONS = [2023, 2024, 2025, 2026]

METRICS = {
    "point_differential_per_game": ("Point differential/game", 1),
    "yards_per_play": ("Offensive yards/play", 1),
    "yards_per_play_allowed": ("Defensive yards/play allowed", -1),
    "turnover_margin_per_game": ("Turnover margin/game", 1),
    "third_down_pct": ("Third-down conversion %", 1),
}


# --------------------------------------------------
# BUILD MULTI-SEASON HISTORICAL MATCHUP RECORDS
# --------------------------------------------------

records = []

print("\nLEAGUE-WIDE UNDERDOG ANALYSIS")
print("=" * 65)

for season in SEASONS:
    print(f"\nProcessing {season}...")

    markets = get_market_performance(season)

    games = markets[
        (markets["game_type"] == "REG")
        & markets["winner"].notna()
        & markets["winner"].ne("TIE")
        & (markets["week"] > 1)
        & markets["market_probability"].notna()
        & (markets["market_probability"] > 50)
    ].copy()

    games = games[
        games.apply(
            lambda row: row["winner"] in (
                row["away_team"],
                row["home_team"],
            ),
            axis=1,
        )
    ].copy()

    if games.duplicated(
        ["season", "week", "away_team", "home_team"]
    ).any():
        raise ValueError(
            f"Duplicate market games detected for {season}."
        )

    games["underdog"] = games.apply(
        lambda row: (
            row["home_team"]
            if row["market_pick"] == row["away_team"]
            else row["away_team"]
        ),
        axis=1,
    )

    games["underdog_probability"] = games.apply(
        lambda row: (
            row["home_probability"]
            if row["underdog"] == row["home_team"]
            else row["away_probability"]
        ),
        axis=1,
    )

    games["underdog_won"] = (
        games["winner"] == games["underdog"]
    )

    team_games = load_team_games(season)

    rankings_cache = {}

    for week in sorted(games["week"].unique()):
        rankings_cache[week] = get_team_rankings(
            team_games,
            season=season,
            through_week=int(week) - 1,
        ).set_index("team")

    for _, game in games.iterrows():
        week = int(game["week"])
        underdog = game["underdog"]
        favorite = game["market_pick"]

        rankings = rankings_cache[week]

        if (
            underdog not in rankings.index
            or favorite not in rankings.index
        ):
            raise ValueError(
                f"Missing rankings: {season} Week {week}, "
                f"{underdog} vs {favorite}"
            )

        dog_stats = rankings.loc[underdog]
        favorite_stats = rankings.loc[favorite]

        record = {
            "season": season,
            "week": week,
            "underdog": underdog,
            "favorite": favorite,
            "won": bool(game["underdog_won"]),
            "market_probability": (
                game["underdog_probability"] / 100
            ),
        }

        for metric, (_, direction) in METRICS.items():
            difference = (
                dog_stats[metric] - favorite_stats[metric]
            ) * direction

            if metric == "third_down_pct":
                difference *= 100

            record[metric] = difference

        records.append(record)

    print(f"  Completed games after Week 1: {len(games)}")
    print(f"  Matchups processed: {len(games)}")

analysis = pd.DataFrame(records)

if analysis.empty:
    raise ValueError("No completed underdog matchups found.")

if analysis["market_probability"].isna().any():
    raise ValueError("Missing underdog market probabilities.")

if not analysis["market_probability"].between(0, 1).all():
    raise ValueError("Underdog market probabilities outside 0–1.")


# --------------------------------------------------
# PERFORMANCE BY SEASON
# --------------------------------------------------

season_summary = (
    analysis.groupby("season")
    .agg(
        games=("won", "count"),
        wins=("won", "sum"),
        win_rate=("won", "mean"),
        expected_wins=("market_probability", "sum"),
    )
)

season_summary["wins_above_expected"] = (
    season_summary["wins"]
    - season_summary["expected_wins"]
)

season_summary["win_rate"] *= 100

print("\nUNDERDOG PERFORMANCE BY SEASON")
print("-" * 65)
print(season_summary.round(2).to_string())


# --------------------------------------------------
# OVERALL PERFORMANCE
# --------------------------------------------------

actual_wins = int(analysis["won"].sum())
expected_wins = analysis["market_probability"].sum()

print("\nOVERALL UNDERDOG PERFORMANCE")
print("-" * 65)

print(f"Games analyzed: {len(analysis)}")
print(f"Underdog wins: {actual_wins}")
print(f"Underdog win rate: {analysis['won'].mean():.1%}")
print(f"Expected wins: {expected_wins:.2f}")
print(f"Wins above expected: {actual_wins - expected_wins:+.2f}")

# --------------------------------------------------
# COMPARE STATISTICAL ADVANTAGES
# --------------------------------------------------

print("\nPREGAME STATISTICAL ADVANTAGES")
print("-" * 65)
print("Positive = underdog had the better statistic.\n")

summary = (
    analysis.groupby("won")[list(METRICS)]
    .mean()
    .T
    .rename(columns={True: "Winning", False: "Losing"})
    .reindex(columns=["Winning", "Losing"])
)

summary.index = [
    METRICS[metric][0] for metric in summary.index
]

print(summary.round(2).to_string())

# --------------------------------------------------
# MARKET-ADJUSTED PERFORMANCE
# --------------------------------------------------

print("\nMARKET-ADJUSTED PERFORMANCE")
print("-" * 65)

for metric, (label, _) in METRICS.items():
    subset = analysis.dropna(subset=[metric]).copy()

    # Divide games into those where the underdog
    # had a statistical advantage and those where
    # the favorite had the advantage.
    subset["dog_advantage"] = subset[metric] > 0

    print(f"\n{label}")

    for advantage, group in subset.groupby("dog_advantage"):
        name = (
            "Underdog advantage"
            if advantage
            else "No underdog advantage"
        )

        actual = int(group["won"].sum())
        expected = group["market_probability"].sum()

        print(
            f"  {name}: "
            f"{len(group)} games, "
            f"{actual} wins, "
            f"{group['won'].mean():.1%} win rate, "
            f"{expected:.2f} expected wins, "
            f"{actual - expected:+.2f} wins above expected"
        )


# --------------------------------------------------
# STATISTICAL ADVANTAGES BY SEASON
# --------------------------------------------------

print("\nSTATISTICAL ADVANTAGES BY SEASON")
print("=" * 75)

for metric, (label, _) in METRICS.items():
    subset = analysis.dropna(subset=[metric]).copy()

    # Only games where the underdog had the
    # better pregame statistic.
    subset = subset[subset[metric] > 0]

    print(f"\n{label}")
    print("-" * 75)

    if subset.empty:
        print("No qualifying games.")
        continue

    summary = (
        subset.groupby("season")
        .agg(
            games=("won", "count"),
            wins=("won", "sum"),
            actual_win_rate=("won", "mean"),
            expected_win_rate=("market_probability", "mean"),
            expected_wins=("market_probability", "sum"),
        )
    )

    summary["wins_above_expected"] = (
        summary["wins"] - summary["expected_wins"]
    )

    summary["actual_win_rate"] *= 100
    summary["expected_win_rate"] *= 100

    print(
        summary[
            [
                "games",
                "wins",
                "actual_win_rate",
                "expected_win_rate",
                "wins_above_expected",
            ]
        ]
        .round(2)
        .to_string()
    )


# --------------------------------------------------
# OFFENSIVE EFFICIENCY ADVANTAGE BY MAGNITUDE
# --------------------------------------------------

print("\nOFFENSIVE EFFICIENCY ADVANTAGE BY MAGNITUDE")
print("-" * 75)

metric = "yards_per_play"

bins = [
    float("-inf"),
    -1.0,
    -0.5,
    0.0,
    0.5,
    float("inf"),
]

labels = [
    "Large disadvantage (< -1.0)",
    "Moderate disadvantage (-1.0 to -0.5)",
    "Small disadvantage (-0.5 to 0)",
    "Small advantage (0 to +0.5)",
    "Large advantage (> +0.5)",
]

analysis["efficiency_group"] = pd.cut(
    analysis[metric],
    bins=bins,
    labels=labels,
    right=True,
    include_lowest=True,
)

summary = (
    analysis.groupby(
        "efficiency_group",
        observed=False,
    )
    .agg(
        games=("won", "count"),
        wins=("won", "sum"),
        actual_win_rate=("won", "mean"),
        expected_wins=("market_probability", "sum"),
        expected_win_rate=("market_probability", "mean"),
        avg_efficiency_difference=(metric, "mean"),
    )
    .reset_index()
)

summary["wins_above_expected"] = (
    summary["wins"] - summary["expected_wins"]
)

summary["actual_win_rate"] *= 100
summary["expected_win_rate"] *= 100

print(
    summary[
        [
            "efficiency_group",
            "games",
            "wins",
            "actual_win_rate",
            "expected_win_rate",
            "wins_above_expected",
        ]
    ]
    .round(2)
    .to_string(index=False)
)

print("\nVALIDATION")
print("-" * 75)

print(f"Original games: {len(analysis)}")
print(f"Categorized games: {summary['games'].sum()}")
print(f"Uncategorized games: {analysis['efficiency_group'].isna().sum()}")


# --------------------------------------------------
# COMBINED STATISTICAL ADVANTAGES
# --------------------------------------------------

print("\nCOMBINED STATISTICAL ADVANTAGES")
print("=" * 75)

# Each metric has already been adjusted so that
# positive values favor the underdog.
metric_columns = list(METRICS.keys())

# Check for missing statistical values before counting.
if analysis[metric_columns].isna().any().any():
    raise ValueError(
        "Missing statistical values in advantage analysis."
    )

# Count how many of the five statistics favor the underdog.
analysis["advantage_count"] = (
    analysis[metric_columns] > 0
).sum(axis=1)

advantage_summary = (
    analysis.groupby("advantage_count")
    .agg(
        games=("won", "count"),
        wins=("won", "sum"),
        actual_win_rate=("won", "mean"),
        expected_win_rate=("market_probability", "mean"),
        expected_wins=("market_probability", "sum"),
    )
)

advantage_summary["wins_above_expected"] = (
    advantage_summary["wins"]
    - advantage_summary["expected_wins"]
)

advantage_summary["actual_win_rate"] *= 100
advantage_summary["expected_win_rate"] *= 100

print("\nALL SEASONS COMBINED")
print("-" * 75)

print(
    advantage_summary[
        [
            "games",
            "wins",
            "actual_win_rate",
            "expected_win_rate",
            "wins_above_expected",
        ]
    ]
    .round(2)
    .to_string()
)

# --------------------------------------------------
# COMBINED ADVANTAGES BY SEASON
# --------------------------------------------------

print("\nCOMBINED ADVANTAGES BY SEASON")
print("-" * 75)

season_advantages = (
    analysis.groupby(["season", "advantage_count"])
    .agg(
        games=("won", "count"),
        wins=("won", "sum"),
        actual_win_rate=("won", "mean"),
        expected_win_rate=("market_probability", "mean"),
        expected_wins=("market_probability", "sum"),
    )
)

season_advantages["wins_above_expected"] = (
    season_advantages["wins"]
    - season_advantages["expected_wins"]
)

season_advantages["actual_win_rate"] *= 100
season_advantages["expected_win_rate"] *= 100

print(
    season_advantages[
        [
            "games",
            "wins",
            "actual_win_rate",
            "expected_win_rate",
            "wins_above_expected",
        ]
    ]
    .round(2)
    .to_string()
)

# --------------------------------------------------
# VALIDATION
# --------------------------------------------------

print("\nADVANTAGE COUNT VALIDATION")
print("-" * 75)

print(f"Original games: {len(analysis)}")
print(f"Categorized games: {advantage_summary['games'].sum()}")
print(f"Minimum advantages: {analysis['advantage_count'].min()}")
print(f"Maximum advantages: {analysis['advantage_count'].max()}")

assert advantage_summary["games"].sum() == len(analysis)
assert analysis["advantage_count"].between(0, 5).all()


# --------------------------------------------------
# MARKET PROBABILITY CALIBRATION
# --------------------------------------------------

print("\nMARKET PROBABILITY CALIBRATION")
print("=" * 75)

# Underdog probabilities are stored as decimals (0 to 1).
bins = [0, 0.20, 0.30, 0.40, 0.50, 1.0]

labels = [
    "Below 20%",
    "20% to 30%",
    "30% to 40%",
    "40% to 50%",
    "50% or higher",
]

analysis["probability_group"] = pd.cut(
    analysis["market_probability"],
    bins=bins,
    labels=labels,
    include_lowest=True,
    right=False,
)

calibration = (
    analysis.groupby("probability_group", observed=False)
    .agg(
        games=("won", "count"),
        wins=("won", "sum"),
        actual_win_rate=("won", "mean"),
        expected_win_rate=("market_probability", "mean"),
        expected_wins=("market_probability", "sum"),
    )
)

calibration["wins_above_expected"] = (
    calibration["wins"] - calibration["expected_wins"]
)

calibration["actual_win_rate"] *= 100
calibration["expected_win_rate"] *= 100

print("\nALL SEASONS COMBINED")
print("-" * 75)

print(
    calibration[
        [
            "games",
            "wins",
            "actual_win_rate",
            "expected_win_rate",
            "wins_above_expected",
        ]
    ]
    .round(2)
    .to_string()
)

# --------------------------------------------------
# CALIBRATION BY SEASON
# --------------------------------------------------

print("\nCALIBRATION BY SEASON")
print("-" * 75)

season_calibration = (
    analysis.groupby(
        ["season", "probability_group"],
        observed=False,
    )
    .agg(
        games=("won", "count"),
        wins=("won", "sum"),
        actual_win_rate=("won", "mean"),
        expected_win_rate=("market_probability", "mean"),
        expected_wins=("market_probability", "sum"),
    )
)

season_calibration["wins_above_expected"] = (
    season_calibration["wins"]
    - season_calibration["expected_wins"]
)

season_calibration["actual_win_rate"] *= 100
season_calibration["expected_win_rate"] *= 100

# Hide empty probability groups.
season_calibration = season_calibration[
    season_calibration["games"] > 0
]

print(
    season_calibration[
        [
            "games",
            "wins",
            "actual_win_rate",
            "expected_win_rate",
            "wins_above_expected",
        ]
    ]
    .round(2)
    .to_string()
)

print("\nCALIBRATION VALIDATION")
print("-" * 75)
print(f"Original games: {len(analysis)}")
print(f"Categorized games: {calibration['games'].sum()}")
print(
    "Uncategorized games: "
    f"{analysis['probability_group'].isna().sum()}"
)


print("\nAnalysis complete.")

