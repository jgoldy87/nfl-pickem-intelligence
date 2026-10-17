
import nflreadpy as nfl

from analysis.team_data import load_team_games
from analysis.matchups import get_matchup_comparison
from analysis.rankings import format_stat_value

SEASON = 2026
WEEK = 6

CATEGORY_ORDER = [
    "Offense",
    "Defense",
    "Overall",
    "Turnovers",
    "Situational",
]


def display_matchup(team_games, away_team, home_team):
    result = get_matchup_comparison(
        team_games=team_games,
        season=SEASON,
        week=WEEK,
        team_a=away_team,
        team_b=home_team,
    )

    print("\n" + "=" * 76)
    print(f"WEEK {WEEK}: {away_team} @ {home_team}")
    print(
        f"{SEASON} REGULAR SEASON | "
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

            away_display = f"{away_value} (#{away_rank})"
            home_display = f"{home_value} (#{home_rank})"

            print(
                f"{item['label']:<30}"
                f"{away_display:>21}"
                f"{home_display:>21}"
            )

    print("=" * 76)


def main():
    if WEEK < 2 or WEEK > 18:
        raise ValueError(
            "Select a regular-season week from 2 to 18. "
            "Week 1 has no prior regular-season rankings."
        )

    print("Loading team statistics...")
    team_games = load_team_games(SEASON)

    print("Loading NFL schedule...")
    schedule = nfl.load_schedules(
        seasons=SEASON
    ).to_pandas()

    games = schedule[
        (schedule["season"] == SEASON)
        & (schedule["game_type"] == "REG")
        & (schedule["week"] == WEEK)
    ].copy()

    if games.empty:
        print(f"No games found for Week {WEEK}.")
        return

    games = games.sort_values(
        ["gameday", "gametime", "game_id"],
        na_position="last",
    )

    print(
        f"\n{SEASON} WEEK {WEEK}: "
        f"{len(games)} SCHEDULED MATCHUPS"
    )

    for _, game in games.iterrows():
        display_matchup(
            team_games,
            away_team=game["away_team"],
            home_team=game["home_team"],
        )

    print("\n" + "=" * 76)
    print(f"END OF WEEK {WEEK} MATCHUP REPORT")
    print("Rank #1 = best in the NFL for that statistic.")
    print("=" * 76)


if __name__ == "__main__":
    main()
