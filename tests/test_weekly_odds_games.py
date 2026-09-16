from analysis.nfl_results import fetch_week_results
from analysis.weekly_picks import get_week_nfl_odds


SEASON = 2026
WEEK = 2


schedule = fetch_week_results(
    season=SEASON,
    week=WEEK,
)

odds_games = get_week_nfl_odds(
    season=SEASON,
    week=WEEK,
)


print("\nNFL SCHEDULE")
print("-" * 50)

schedule_matchups = set()

for _, game in schedule.iterrows():
    matchup = (
        game["away_team"],
        game["home_team"],
    )

    schedule_matchups.add(matchup)

    print(
        f"{game['away_team']} @ "
        f"{game['home_team']}"
    )


print(
    f"\nNFL schedule games: "
    f"{len(schedule_matchups)}"
)


print("\nODDS API")
print("-" * 50)

odds_matchups = set()

for game in odds_games:
    matchup = (
        game["away_team"],
        game["home_team"],
    )

    odds_matchups.add(matchup)

    print(
        f"{game['away_team']} @ "
        f"{game['home_team']} "
        f"({len(game['bookmakers'])} sportsbooks)"
    )


print(
    f"\nOdds API games: "
    f"{len(odds_matchups)}"
)


missing_games = (
    schedule_matchups - odds_matchups
)

extra_games = (
    odds_matchups - schedule_matchups
)


print("\nMISSING FROM ODDS API")
print("-" * 50)

if missing_games:
    for away_team, home_team in missing_games:
        print(
            f"{away_team} @ {home_team}"
        )
else:
    print("None")


print("\nEXTRA IN ODDS API")
print("-" * 50)

if extra_games:
    for away_team, home_team in extra_games:
        print(
            f"{away_team} @ {home_team}"
        )
else:
    print("None")