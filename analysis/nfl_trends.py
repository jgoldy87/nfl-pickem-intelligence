
import pandas as pd
import nflreadpy as nfl


def get_close_game_results(season):
    """
    Load completed NFL regular-season games.

    Includes games even when sportsbook odds
    are unavailable.
    """
    schedule = nfl.load_schedules(
        seasons=[season]
    ).to_pandas()

    games = schedule[
        schedule["game_type"] == "REG"
    ].copy()

    games = games.dropna(
        subset=["home_score", "away_score"]
    )

    games["margin"] = (
        games["home_score"] - games["away_score"]
    ).abs()

    return games


def summarize_close_games(games):
    """
    Calculate league-wide competitiveness metrics.
    """
    total_games = len(games)

    if total_games == 0:
        return {
            "total_games": 0,
            "one_score_pct": 0.0,
            "field_goal_pct": 0.0,
            "average_margin": 0.0,
        }

    return {
        "total_games": total_games,
        "one_score_pct": round(
            (games["margin"] <= 8).mean() * 100, 1
        ),
        "field_goal_pct": round(
            (games["margin"] <= 3).mean() * 100, 1
        ),
        "average_margin": round(
            games["margin"].mean(), 1
        ),
    }


def get_margin_distribution(games):
    """
    Group games by final scoring margin.
    """
    labels = [
        "1–3",
        "4–7",
        "8–10",
        "11–14",
        "15+",
    ]

    if games.empty:
        return pd.DataFrame({
            "Margin": labels,
            "Games": [0] * len(labels),
        })

    margins = games.loc[
        games["margin"] > 0, "margin"
    ]

    buckets = pd.cut(
        margins,
        bins=[0, 3, 7, 10, 14, float("inf")],
        labels=labels,
        include_lowest=True,
    )

    counts = buckets.value_counts(
        sort=False
    )

    return pd.DataFrame({
        "Margin": labels,
        "Games": counts.reindex(
            labels, fill_value=0
        ).to_numpy(),
    })
