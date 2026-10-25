
from datetime import datetime
from zoneinfo import ZoneInfo

import nflreadpy as nfl
import pandas as pd

from analysis.team_data import load_team_games
from analysis.matchups import get_matchup_comparison
from analysis.rankings import format_stat_value


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

# None = automatically use the current NFL season/week.
# Set either value manually to override it.
SEASON = None
WEEK = None

CATEGORY_ORDER = [
    "Offense",
    "Defense",
    "Overall",
    "Turnovers",
    "Situational",
]


# --------------------------------------------------
# DETERMINE CURRENT NFL SEASON AND WEEK
# --------------------------------------------------

def get_current_season():
    today = datetime.now(
        ZoneInfo("America/New_York")
    ).date()

    # January and February belong to the previous
    # NFL season. This script covers regular-season
    # matchups only.
    return today.year if today.month >= 3 else today.year - 1


def get_current_week(schedule):
    """
    Determine the current NFL regular-season week
    using the official schedule.

    The next week begins the day after the previous
    week's final scheduled game.

    For example, after Monday Night Football,
    Tuesday belongs to the upcoming NFL week.
    """

    today = pd.Timestamp(
        datetime.now(
            ZoneInfo("America/New_York")
        ).date()
    )

    regular = schedule[
        schedule["game_type"] == "REG"
    ].copy()

    if regular.empty:
        raise ValueError(
            "No regular-season schedule is available."
        )

    regular["gameday"] = pd.to_datetime(
        regular["gameday"]
    )

    week_dates = (
        regular.groupby("week")["gameday"]
        .agg(["min", "max"])
        .sort_index()
    )

    weeks = sorted(
        int(week) for week in week_dates.index
    )

    current_week = weeks[0]

    for index, week in enumerate(weeks):

        if index == 0:
            continue

        previous_week = weeks[index - 1]

        previous_final_game = week_dates.loc[
            previous_week, "max"
        ]

        if today > previous_final_game:
            current_week = week
        else:
            break

    return current_week


# --------------------------------------------------
# DISPLAY MATCHUP
# --------------------------------------------------

def display_matchup(
    team_games,
    away_team,
    home_team,
    season,
    week,
):
    result = get_matchup_comparison(
        team_games=team_games,
        season=season,
        week=week,
        team_a=away_team,
        team_b=home_team,
    )

    print("\n" + "=" * 76)
    print(f"WEEK {week}: {away_team} @ {home_team}")
    print(
        f"{season} REGULAR SEASON | "
        f"STATS THROUGH WEEK {result['through_week']}"
    )
    print("=" * 76)

    print(
        f"{'STATISTIC':<30}"
        f"{away_team:>21}"
        f"{home_team:>21}"
    )
    print("-" * 76)

    for category in CATEGORY_ORDER:

        items = [
            item
            for item in result["comparison"]
            if item["category"] == category
        ]

        if not items:
            continue

        print(f"\n{category.upper()}")

        for item in items:

            metric = item["metric"]

            away_value = format_stat_value(
                metric,
                item[f"{away_team}_value"],
            )

            home_value = format_stat_value(
                metric,
                item[f"{home_team}_value"],
            )

            away_rank = int(
                item[f"{away_team}_rank"]
            )

            home_rank = int(
                item[f"{home_team}_rank"]
            )

            away_display = (
                f"{away_value} (#{away_rank})"
            )

            home_display = (
                f"{home_value} (#{home_rank})"
            )

            print(
                f"{item['label']:<30}"
                f"{away_display:>21}"
                f"{home_display:>21}"
            )

    print("=" * 76)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    season = (
        SEASON
        if SEASON is not None
        else get_current_season()
    )

    print("Loading NFL schedule...")

    schedule = nfl.load_schedules(
        seasons=season
    ).to_pandas()

    schedule = schedule[
        schedule["season"] == season
    ].copy()

    week = (
        WEEK
        if WEEK is not None
        else get_current_week(schedule)
    )

    print(
        f"Selected NFL season: {season}"
    )
    print(
        f"Selected NFL week: {week}"
    )

    if week < 2 or week > 18:
        raise ValueError(
            "Select a regular-season week from 2 to 18. "
            "Week 1 has no prior regular-season rankings."
        )

    print("Loading team statistics...")

    team_games = load_team_games(season)

    games = schedule[
        (schedule["game_type"] == "REG")
        & (schedule["week"] == week)
    ].copy()

    if games.empty:
        print(
            f"No games found for Week {week}."
        )
        return

    games = games.sort_values(
        ["gameday", "gametime", "game_id"],
        na_position="last",
    )

    print(
        f"\n{season} WEEK {week}: "
        f"{len(games)} SCHEDULED MATCHUPS"
    )

    for _, game in games.iterrows():

        display_matchup(
            team_games=team_games,
            away_team=game["away_team"],
            home_team=game["home_team"],
            season=season,
            week=week,
        )

    print("\n" + "=" * 76)
    print(
        f"END OF WEEK {week} MATCHUP REPORT"
    )
    print(
        "Rank #1 = best in the NFL "
        "for that statistic."
    )
    print("=" * 76)


if __name__ == "__main__":
    main()
