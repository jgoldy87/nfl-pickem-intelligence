import pandas as pd
import nflreadpy as nfl

from nflreadpy.config import update_config


def implied_probability(moneyline):
    """
    Convert an American moneyline to implied probability.
    """

    if moneyline < 0:
        return abs(moneyline) / (
            abs(moneyline) + 100
        )

    return 100 / (
        moneyline + 100
    )


def calculate_no_vig_probabilities(
    away_moneyline,
    home_moneyline,
):
    """
    Convert two opposing moneylines into no-vig
    win probabilities.
    """

    away_implied = implied_probability(
        away_moneyline
    )

    home_implied = implied_probability(
        home_moneyline
    )

    total_probability = (
        away_implied + home_implied
    )

    away_probability = (
        away_implied / total_probability
    )

    home_probability = (
        home_implied / total_probability
    )

    return (
        away_probability,
        home_probability,
    )


def get_market_performance(
    season,
    week=None,
):
    """
    Build market-performance results from nflverse
    recorded moneylines.

    If week is supplied, only that week is returned.
    Otherwise, all available games for the season
    are returned.
    """

    # Disable caching so market-line investigations
    # use the latest available nflverse data.
    update_config(
        cache_mode="off"
    )

    nfl.clear_cache()

    schedule = nfl.load_schedules(
        seasons=[season]
    ).to_pandas()

    if week is not None:
        schedule = schedule[
            schedule["week"] == week
        ].copy()

    results = []

    for _, game in schedule.iterrows():

        away_moneyline = game[
            "away_moneyline"
        ]

        home_moneyline = game[
            "home_moneyline"
        ]

        away_score = game[
            "away_score"
        ]

        home_score = game[
            "home_score"
        ]

        # Skip games without usable market data.
        if (
            pd.isna(away_moneyline)
            or pd.isna(home_moneyline)
        ):
            continue

        # Skip games that have not been completed.
        if (
            pd.isna(away_score)
            or pd.isna(home_score)
        ):
            continue

        away_team = game[
            "away_team"
        ]

        home_team = game[
            "home_team"
        ]

        (
            away_probability,
            home_probability,
        ) = calculate_no_vig_probabilities(
            away_moneyline,
            home_moneyline,
        )

        if (
            away_probability
            > home_probability
        ):
            market_pick = away_team
            market_probability = (
                away_probability
            )
        else:
            market_pick = home_team
            market_probability = (
                home_probability
            )

        if away_score > home_score:
            winner = away_team
        elif home_score > away_score:
            winner = home_team
        else:
            winner = "TIE"

        market_correct = (
            market_pick == winner
        )

        results.append(
            {
                "season": int(
                    game["season"]
                ),
                "week": int(
                    game["week"]
                ),
                "game_type": game[
                    "game_type"
                ],
                "game": (
                    f"{away_team} @ "
                    f"{home_team}"
                ),
                "away_team": away_team,
                "home_team": home_team,
                "away_moneyline": (
                    away_moneyline
                ),
                "home_moneyline": (
                    home_moneyline
                ),
                "away_probability": round(
                    away_probability * 100,
                    1,
                ),
                "home_probability": round(
                    home_probability * 100,
                    1,
                ),
                "market_pick": market_pick,
                "market_probability": round(
                    market_probability * 100,
                    1,
                ),
                "winner": winner,
                "market_correct": (
                    market_correct
                ),
            }
        )

    return pd.DataFrame(results)

def summarize_market_performance(results_df):
    """
    Summarize overall market performance.
    """

    total_games = len(results_df)

    if total_games == 0:
        return {
            "games": 0,
            "correct": 0,
            "incorrect": 0,
            "accuracy": 0.0,
        }

    correct = int(
        results_df["market_correct"].sum()
    )

    incorrect = (
        total_games - correct
    )

    accuracy = (
        correct / total_games * 100
    )

    return {
        "games": total_games,
        "correct": correct,
        "incorrect": incorrect,
        "accuracy": round(
            accuracy,
            1,
        ),
    }

def summarize_probability_buckets(
    results_df,
):
    """
    Summarize market performance by predicted
    probability range.
    """

    if results_df.empty:
        return pd.DataFrame()

    bucket_df = results_df.copy()

    bucket_df["probability_bucket"] = pd.cut(
        bucket_df["market_probability"],
        bins=[
            50,
            60,
            70,
            80,
            100,
        ],
        labels=[
            "50-59.9%",
            "60-69.9%",
            "70-79.9%",
            "80%+",
        ],
        right=False,
        include_lowest=True,
    )

    summary = (
        bucket_df.groupby(
            "probability_bucket",
            observed=False,
        )
        .agg(
            games=(
                "market_correct",
                "size",
            ),
            correct=(
                "market_correct",
                "sum",
            ),
            average_probability=(
                "market_probability",
                "mean",
            ),
        )
        .reset_index()
    )

    summary["incorrect"] = (
        summary["games"]
        - summary["correct"]
    )

    summary["accuracy"] = (
        summary["correct"]
        / summary["games"]
        * 100
    )

    summary["average_probability"] = (
        summary[
            "average_probability"
        ].round(1)
    )

    summary["accuracy"] = (
        summary["accuracy"].round(1)
    )

    return summary