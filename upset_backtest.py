
import numpy as np
import pandas as pd


DATA_FILE = "upset_game_data.csv"

TRAIN_SEASONS = [2021, 2022, 2023, 2024]
TEST_SEASONS = [2025, 2026]

BINS = [0.50, 0.55, 0.60, 0.65, 0.70,
        0.75, 0.80, 0.85, 0.90, 1.01]


def load_data():
    games = pd.read_csv(DATA_FILE)

    required = [
        "season", "week", "favorite_probability",
        "favorite", "winner", "upset"
    ]

    missing = [c for c in required if c not in games.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    games["upset"] = (
        games["upset"].astype(str).str.lower() == "true"
    )

    games["band"] = pd.cut(
        games["favorite_probability"],
        bins=BINS,
        right=False,
        include_lowest=True
    )

    return games


def calculate_training_rates(training):
    rates = (
        training.groupby("band", observed=True)["upset"]
        .agg(["mean", "size"])
        .rename(columns={"mean": "upset_rate",
                         "size": "training_games"})
        .reset_index()
    )

    return rates


def allocate_picks(games, rates, conservative=False):
    """
    Choose underdogs by historical band allocation.

    Quotas are rounded to the nearest integer.
    Weakest favorites within each band are flipped first.
    """
    picks = games.copy()
    picks["pick_underdog"] = False

    rate_map = rates.set_index("band")["upset_rate"]

    for (season, week, band), group in picks.groupby(
        ["season", "week", "band"],
        observed=True
    ):
        if conservative and band.left >= 0.60:
            continue

        historical_rate = rate_map.get(band, np.nan)

        if pd.isna(historical_rate):
            continue

        # Round half up rather than Python's banker's rounding
        quota = int(np.floor(len(group) * historical_rate + 0.5))
        quota = min(quota, len(group))

        # Lower favorite probability = higher upset probability
        selected = (
            group.sort_values("favorite_probability")
            .head(quota)
            .index
        )

        picks.loc[selected, "pick_underdog"] = True

    return picks


def evaluate_strategy(games, name):
    games = games.copy()

    games["correct"] = (
        games["pick_underdog"] == games["upset"]
    )

    return {
        "Strategy": name,
        "Games": len(games),
        "Correct": int(games["correct"].sum()),
        "Accuracy": round(games["correct"].mean() * 100, 2),
        "Underdog_Picks": int(games["pick_underdog"].sum()),
        "Underdog_Pick_Rate": round(
            games["pick_underdog"].mean() * 100, 2
        ),
    }


def score_confidence_picks(games):
    """
    Assign confidence points independently for each
    season/week, then score the selected picks.

    Highest estimated win probability receives the
    highest available confidence value.
    """
    scored = games.copy()

    scored["pick_probability"] = np.where(
        scored["pick_underdog"],
        1 - scored["favorite_probability"],
        scored["favorite_probability"]
    )

    scored["correct"] = (
        scored["pick_underdog"] == scored["upset"]
    )

    # Rank picks from least to most likely to win.
    # Confidence values are 1 through the number
    # of games in that week.
    scored["confidence"] = (
        scored.groupby(["season", "week"])["pick_probability"]
        .rank(method="first", ascending=True)
        .astype(int)
    )

    scored["points"] = np.where(
        scored["correct"],
        scored["confidence"],
        0
    )

    return scored


def summarize_confidence(scored, name):
    weekly = (
        scored.groupby(["season", "week"])
        .agg(
            Games=("correct", "size"),
            Correct=("correct", "sum"),
            Points=("points", "sum")
        )
        .reset_index()
    )

    weekly["Max_Points"] = (
        weekly["Games"] * (weekly["Games"] + 1) / 2
    )

    weekly["Points_Pct"] = (
        weekly["Points"] / weekly["Max_Points"] * 100
    )

    return {
        "Strategy": name,
        "Total_Points": int(weekly["Points"].sum()),
        "Avg_Points_Per_Week": round(
            weekly["Points"].mean(), 2
        ),
        "Points_Pct": round(
            weekly["Points"].sum()
            / weekly["Max_Points"].sum() * 100, 2
        ),
        "Median_Weekly_Pct": round(
            weekly["Points_Pct"].median(), 2
        ),
        "P25_Weekly_Pct": round(
            weekly["Points_Pct"].quantile(0.25), 2
        ),
        "Worst_Weekly_Pct": round(
            weekly["Points_Pct"].min(), 2
        ),
    }


def main():
    games = load_data()

    training = games[
        games["season"].isin(TRAIN_SEASONS)
    ].copy()

    testing = games[
        games["season"].isin(TEST_SEASONS)
    ].copy()

    if training.empty or testing.empty:
        raise ValueError("Training or testing data is empty.")

    rates = calculate_training_rates(training)

    print("=" * 70)
    print("NFL UPSET ALLOCATION BACKTEST")
    print("=" * 70)

    print(f"Training seasons: {TRAIN_SEASONS}")
    print(f"Testing seasons: {TEST_SEASONS}")
    print(f"Training games: {len(training)}")
    print(f"Testing games: {len(testing)}")

    print("\nTRAINING UPSET RATES")
    print("-" * 70)
    print(rates.to_string(index=False))

    # Strategy A: all favorites
    favorites = testing.copy()
    favorites["pick_underdog"] = False

    # Strategy B: allocate across every band
    allocated = allocate_picks(
        testing, rates, conservative=False
    )

    # Strategy C: only allocate below 60%
    conservative = allocate_picks(
        testing, rates, conservative=True
    )

    results = pd.DataFrame([
        evaluate_strategy(favorites, "All Favorites"),
        evaluate_strategy(allocated, "Historical Allocation"),
        evaluate_strategy(conservative, "Conservative Allocation"),
    ])

    print("\nBACKTEST RESULTS")
    print("-" * 70)
    print(results.to_string(index=False))

    print("\nRESULTS BY SEASON")
    print("-" * 70)

    for season in TEST_SEASONS:
        print(f"\n{season}")

        season_results = pd.DataFrame([
            evaluate_strategy(
                strategy[strategy["season"] == season],
                name
            )
            for name, strategy in [
                ("All Favorites", favorites),
                ("Historical Allocation", allocated),
                ("Conservative Allocation", conservative),
            ]
        ])

        print(season_results.to_string(index=False))


    # ========================================================
    # CONFIDENCE POINT BACKTEST
    # ========================================================

    strategies = {
        "All Favorites": favorites,
        "Historical Allocation": allocated,
        "Conservative Allocation": conservative,
    }

    confidence_results = []
    scored_strategies = {}

    for name, strategy in strategies.items():
        scored = score_confidence_picks(strategy)
        scored_strategies[name] = scored

        confidence_results.append(
            summarize_confidence(scored, name)
        )

    confidence_table = pd.DataFrame(
        confidence_results
    )

    print("\nCONFIDENCE POINT BACKTEST")
    print("-" * 90)
    print(confidence_table.to_string(index=False))

    print("\nCONFIDENCE POINTS BY SEASON")
    print("-" * 90)

    for season in TEST_SEASONS:
        season_results = []

        for name, scored in scored_strategies.items():
            season_games = scored[
                scored["season"] == season
            ]

            season_results.append(
                summarize_confidence(
                    season_games, name
                )
            )

        print(f"\n{season}")
        print(
            pd.DataFrame(
                season_results
            ).to_string(index=False)
        )

    print("\n" + "=" * 70)
    print("BACKTEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
