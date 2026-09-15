from analysis.weekly_picks import (
    get_week_odds_window,
    get_week_nfl_odds,
)


def main():

    start_time, end_time = (
        get_week_odds_window(
            season=2026,
            week=2,
        )
    )

    print(
        "Week 2 odds window:"
    )

    print(start_time)
    print(end_time)

    games = get_week_nfl_odds(
        season=2026,
        week=2,
    )

    print(
        f"\nGames returned: {len(games)}"
    )

    for game in games:

        print(
            game["away_team"],
            "@",
            game["home_team"],
        )


if __name__ == "__main__":
    main()