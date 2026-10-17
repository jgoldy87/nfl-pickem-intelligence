
import pandas as pd

from analysis.team_data import load_team_games
from analysis.rankings import get_team_rankings, STAT_CONFIG

SEASON = 2026
THROUGH_WEEK = 5


def main():
    print("Loading team statistics...")
    team_games = load_team_games(SEASON)

    data = team_games[
        (team_games["season"] == SEASON)
        & (team_games["week"] <= THROUGH_WEEK)
    ].copy()

    print("\n" + "=" * 65)
    print("DATA COMPLETENESS")
    print("=" * 65)

    print(f"Teams: {data['team'].nunique()}")
    print(f"Team-game rows: {len(data)}")
    print(f"Unique games: {data['game_id'].nunique()}")

    print("\nTeam-game rows by week:")
    print(data.groupby("week").size().to_string())

    duplicates = data.duplicated(
        subset=["game_id", "team"]
    ).sum()

    print(f"\nDuplicate team-game rows: {duplicates}")

    rankings = get_team_rankings(
        team_games=team_games,
        season=SEASON,
        through_week=THROUGH_WEEK,
    )

    print("\n" + "=" * 65)
    print("RANKING VERIFICATION")
    print("=" * 65)

    print(f"Ranked teams: {len(rankings)}")

    issues = []

    if len(rankings) != 32:
        issues.append(
            f"Expected 32 ranked teams, found {len(rankings)}"
        )

    if duplicates:
        issues.append(
            f"Found {duplicates} duplicate team-game rows"
        )

    if data["game_id"].isna().any():
        issues.append("Missing game IDs")

    if data["team"].isna().any():
        issues.append("Missing team names")

    for metric, config in STAT_CONFIG.items():
        ascending = config["better"] == "lower"

        expected = rankings[metric].rank(
            ascending=ascending,
            method="min",
        ).astype("Int64")

        actual = rankings[f"{metric}_rank"]

        mismatches = (
            expected.fillna(-1) != actual.fillna(-1)
        ).sum()

        missing_values = rankings[metric].isna().sum()

        status = (
            "PASS"
            if mismatches == 0 and missing_values == 0
            else "CHECK"
        )

        print(
            f"{metric:<36}"
            f"{status:<8}"
            f"mismatches={mismatches}, "
            f"missing={missing_values}"
        )

        if mismatches:
            issues.append(
                f"{metric}: {mismatches} ranking mismatches"
            )

        if missing_values:
            issues.append(
                f"{metric}: {missing_values} missing values"
            )

    print("\n" + "=" * 65)
    print("FINAL RESULT")
    print("=" * 65)

    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("All automated ranking checks passed.")

    print(
        "\nNote: This verifies ranking calculations "
        "against the loaded dataset, not against "
        "an independent external source."
    )


if __name__ == "__main__":
    main()
