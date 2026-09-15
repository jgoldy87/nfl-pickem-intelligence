import pandas as pd
import nflreadpy as nfl


def fetch_week_results(
    season,
    week,
):
    """
    Fetch NFL schedule/results for a specific
    regular-season week using nflverse.
    """

    schedule = nfl.load_schedules(
        seasons=season
    )

    # nflreadpy returns a Polars DataFrame
    schedule = schedule.to_pandas()

    week_df = schedule[
        (schedule["season"] == season)
        & (schedule["week"] == week)
        & (schedule["game_type"] == "REG")
    ].copy()

    if week_df.empty:
        raise ValueError(
            f"No NFL games found for "
            f"{season} Week {week}."
        )

    # Determine whether each game is completed.
    week_df["game_completed"] = (
        week_df["home_score"].notna()
        & week_df["away_score"].notna()
    )

    # Default status
    week_df["status"] = "scheduled"

    week_df.loc[
        week_df["game_completed"],
        "status",
    ] = "final"

    # Winner stays blank until the game is final.
    week_df["winner"] = pd.NA

    home_wins = (
        week_df["game_completed"]
        & (
            week_df["home_score"]
            > week_df["away_score"]
        )
    )

    away_wins = (
        week_df["game_completed"]
        & (
            week_df["away_score"]
            > week_df["home_score"]
        )
    )

    week_df.loc[
        home_wins,
        "winner",
    ] = week_df.loc[
        home_wins,
        "home_team",
    ]

    week_df.loc[
        away_wins,
        "winner",
    ] = week_df.loc[
        away_wins,
        "away_team",
    ]

    result_columns = [
        "season",
        "week",
        "game_id",
        "gameday",
        "away_team",
        "home_team",
        "away_score",
        "home_score",
        "winner",
        "status",
        "game_completed",
    ]

    return week_df[
        result_columns
    ].reset_index(
        drop=True
    )