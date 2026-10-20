
import pandas as pd

from analysis.market_performance import get_market_performance


SEASON = 2026
THROUGH_WEEK = 6


def analyze_favorite_reliability():
    results = get_market_performance(season=SEASON)

    games = results[
        (results["game_type"] == "REG")
        & (results["week"].between(1, THROUGH_WEEK))
        & (results["winner"] != "TIE")
        & (
            results["away_probability"]
            != results["home_probability"]
        )
    ].copy()

    if games.empty:
        print("No completed games with market data found.")
        return

    # Each row represents a game in which a team
    # was favored by the betting market.
    games["favorite"] = games["market_pick"]

    games["favorite_won"] = (
        games["market_correct"].astype(int)
    )

    games["expected_win"] = (
        games["market_probability"] / 100
    )

    # Summarize each team's performance as favorite.
    summary = (
        games.groupby("favorite")
        .agg(
            games_favored=("favorite_won", "size"),
            wins=("favorite_won", "sum"),
            avg_probability=("market_probability", "mean"),
            expected_wins=("expected_win", "sum"),
        )
        .reset_index()
    )

    summary["losses"] = (
        summary["games_favored"] - summary["wins"]
    )

    summary["win_pct"] = (
        summary["wins"] / summary["games_favored"] * 100
    )

    summary["actual_minus_expected"] = (
        summary["wins"] - summary["expected_wins"]
    )

    # Identify each team's most surprising loss.
    losses = games[games["favorite_won"] == 0]

    biggest_losses = (
        losses.groupby("favorite")["market_probability"]
        .max()
        .rename("biggest_upset_probability")
    )

    summary = summary.merge(
        biggest_losses,
        on="favorite",
        how="left",
    )

    summary = summary.round(
        {
            "avg_probability": 1,
            "expected_wins": 2,
            "win_pct": 1,
            "actual_minus_expected": 2,
            "biggest_upset_probability": 1,
        }
    )

    columns = [
        "favorite",
        "games_favored",
        "wins",
        "losses",
        "win_pct",
        "avg_probability",
        "expected_wins",
        "actual_minus_expected",
        "biggest_upset_probability",
    ]

    print(
        f"\nNFL FAVORITE RELIABILITY — "
        f"{SEASON} THROUGH WEEK {THROUGH_WEEK}"
    )
    print("=" * 110)

    print("\nMOST UNDERPERFORMING FAVORITES")
    print("-" * 110)

    print(
        summary.sort_values(
            "actual_minus_expected"
        )[columns].to_string(index=False)
    )

    print("\nMOST RELIABLE FAVORITES")
    print("-" * 110)

    print(
        summary.sort_values(
            "actual_minus_expected",
            ascending=False,
        )[columns].head(10).to_string(index=False)
    )

    print("\nLEAGUE SUMMARY")
    print("-" * 110)

    print(f"Games analyzed: {len(games)}")
    print(f"Favorite wins: {games['favorite_won'].sum()}")
    print(f"Favorite losses: {(games['favorite_won'] == 0).sum()}")

    print(
        "Expected favorite wins: "
        f"{games['expected_win'].sum():.2f}"
    )

    print(
        "Actual minus expected: "
        f"{games['favorite_won'].sum() - games['expected_win'].sum():+.2f}"
    )


if __name__ == "__main__":
    analyze_favorite_reliability()
