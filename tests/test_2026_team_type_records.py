from analysis.market_performance import (
    get_market_performance,
    summarize_team_type_records,
)


def test_2026_team_type_records():
    results = get_market_performance(2026)

    records = summarize_team_type_records(
        results
    )

    print("\nCOMPLETED GAMES:")
    print(len(results))

    print("\nTEAM TYPE RECORDS:")

    for category, record in records.items():
        print(
            f"{category}: "
            f"{record['wins']}-"
            f"{record['losses']} "
            f"({record['win_percentage']}%)"
        )

    # Home and away records must mirror each other.
    assert (
        records["home_teams"]["wins"]
        == records["away_teams"]["losses"]
    )
    assert (
        records["away_teams"]["wins"]
        == records["home_teams"]["losses"]
    )

    # Favorite and underdog records must mirror each other.
    assert (
        records["favorites"]["wins"]
        == records["underdogs"]["losses"]
    )
    assert (
        records["underdogs"]["wins"]
        == records["favorites"]["losses"]
    )

    print(
        "\nAll record validation checks passed."
    )


if __name__ == "__main__":
    test_2026_team_type_records()