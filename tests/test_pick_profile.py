from analysis.weekly_picks import summarize_pick_profile


def test_summarize_pick_profile():
    weekly_picks = [
        {
            "pick": "Buffalo Bills",
            "game": {
                "away_team": "Miami Dolphins",
                "home_team": "Buffalo Bills",
                "bookmakers": [
                    {
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {
                                        "name": "Miami Dolphins",
                                        "price": 200,
                                    },
                                    {
                                        "name": "Buffalo Bills",
                                        "price": -250,
                                    },
                                ],
                            }
                        ]
                    }
                ],
            },
        },
        {
            "pick": "New York Giants",
            "game": {
                "away_team": "New York Giants",
                "home_team": "Dallas Cowboys",
                "bookmakers": [
                    {
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {
                                        "name": "New York Giants",
                                        "price": 180,
                                    },
                                    {
                                        "name": "Dallas Cowboys",
                                        "price": -220,
                                    },
                                ],
                            }
                        ]
                    }
                ],
            },
        },
    ]

    summary = summarize_pick_profile(
        weekly_picks
    )

    print(summary)

    assert summary["home_picks"] == 1
    assert summary["away_picks"] == 1
    assert summary["favorite_picks"] == 1
    assert summary["underdog_picks"] == 1
    assert summary["pickem_picks"] == 0


if __name__ == "__main__":
    test_summarize_pick_profile()
    print("Pick profile test passed.")