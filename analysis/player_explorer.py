from analysis.pickem_analyzer import player_summary

NFL_DIVISIONS = {
    "AFC East": ["BUF", "MIA", "NE", "NYJ"],
    "AFC North": ["BAL", "CIN", "CLE", "PIT"],
    "AFC South": ["HOU", "IND", "JAX", "TEN"],
    "AFC West": ["DEN", "KC", "LV", "LAC"],
    "NFC East": ["DAL", "NYG", "PHI", "WAS"],
    "NFC North": ["CHI", "DET", "GB", "MIN"],
    "NFC South": ["ATL", "CAR", "NO", "TB"],
    "NFC West": ["ARI", "LA", "SF", "SEA"],
}

def get_player_explorer(df, player):
    """
    Build Player Explorer data for one player.
    """

    summary = player_summary(df, player)

    status = summary["status"]

    player_df = df[
        df["player"].str.lower() == player.lower()
    ].copy()

    completed_player_df = player_df[
        player_df["game_completed"] == True
    ].copy()

    overall_table = summary["overall"]

    if overall_table.empty:
        overall = None
    else:
        overall = overall_table.iloc[0]

    player_df = df[
        df["player"].str.lower()
        == player.lower()
    ].copy()

    if overall is None:
        player_overview = {
            "Player": player,
            "Record": "0-0",
            "Correct": 0,
            "Incorrect": 0,
            "Picks": 0,
            "Win_Pct": None,
            "Confidence_Points": 0,
            "Confidence_Risked": 0,
            "Point_Efficiency": None,
        }

    else:
        correct = int(
            overall["Correct"]
        )

        incorrect = int(
            overall["Incorrect"]
        )

        player_overview = {
            "Player": player,
            "Record": (
                f"{correct}-{incorrect}"
            ),
            "Correct": correct,
            "Incorrect": incorrect,
            "Picks": int(
                overall["Picks"]
            ),
            "Win_Pct": (
                overall["Win_Pct"]
            ),
            "Confidence_Points": int(
                overall[
                    "Confidence_Points"
                ]
            ),
            "Confidence_Risked": int(
                overall[
                    "Confidence_Risked"
                ]
            ),
            "Point_Efficiency": (
                overall[
                    "Point_Efficiency"
                ]
            ),
        }

    # Highest-confidence correct pick
    correct_picks = completed_player_df[
        completed_player_df["pick_correct"] == True
    ]

    if not correct_picks.empty:
        highest_correct = correct_picks.loc[
            correct_picks["confidence"].idxmax()
        ]

        highest_confidence_correct = {
            "team": highest_correct["picked_team"],
            "opponent": (
                highest_correct["away_team"]
                if highest_correct["picked_team"]
                == highest_correct["home_team"]
                else highest_correct["home_team"]
            ),
            "confidence": int(
                highest_correct["confidence"]
            ),
            "week": int(
                highest_correct["week"]
            ),
        }

    else:
        highest_confidence_correct = None

    # Highest-confidence incorrect pick
    incorrect_picks = completed_player_df[
        completed_player_df["pick_correct"] == False
    ]

    if not incorrect_picks.empty:
        highest_miss = incorrect_picks.loc[
            incorrect_picks["confidence"].idxmax()
        ]

        highest_confidence_miss = {
            "team": highest_miss["picked_team"],
            "opponent": (
                highest_miss["away_team"]
                if highest_miss["picked_team"]
                == highest_miss["home_team"]
                else highest_miss["home_team"]
            ),
            "confidence": int(
                highest_miss["confidence"]
            ),
            "week": int(
                highest_miss["week"]
            ),
        }

    else:
        highest_confidence_miss = None

    # Best and worst teams
    team_table = summary["teams"].copy()

    best_teams = team_table.sort_values(
        by=[
            "Win_Pct",
            "Picks",
            "Avg_Confidence",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    )

    worst_teams = team_table.sort_values(
        by=[
            "Win_Pct",
            "Picks",
            "Avg_Confidence",
        ],
        ascending=[
            True,
            False,
            False,
        ],
    )

        # Best and worst week
    weekly_table = summary["weekly"].copy()

    if weekly_table.empty:
        best_week_summary = None
        worst_week_summary = None
    else:
        best_week = weekly_table.sort_values(
            by=[
                "Confidence_Points",
                "Win_Pct",
            ],
            ascending=[
                False,
                False,
            ],
        ).iloc[0]

        worst_week = weekly_table.sort_values(
            by=[
                "Confidence_Points",
                "Win_Pct",
            ],
            ascending=[
                True,
                True,
            ],
        ).iloc[0]

        best_week_summary = {
            "week": int(
                best_week["week"]
            ),
            "record": (
                f"{int(best_week['Correct'])}-"
                f"{int(best_week['Incorrect'])}"
            ),
            "win_pct": (
                best_week["Win_Pct"]
            ),
            "confidence_points": int(
                best_week[
                    "Confidence_Points"
                ]
            ),
            "weekly_rank": int(
                best_week[
                    "Weekly_Rank"
                ]
            ),
        }

        worst_week_summary = {
            "week": int(
                worst_week["week"]
            ),
            "record": (
                f"{int(worst_week['Correct'])}-"
                f"{int(worst_week['Incorrect'])}"
            ),
            "win_pct": (
                worst_week["Win_Pct"]
            ),
            "confidence_points": int(
                worst_week[
                    "Confidence_Points"
                ]
            ),
            "weekly_rank": int(
                worst_week[
                    "Weekly_Rank"
                ]
            ),
        }

    # Best and worst confidence band
    confidence_table = summary["confidence"].copy()

    if confidence_table.empty:
        best_confidence_band_summary = None
        worst_confidence_band_summary = None

    else:
        best_confidence_band = confidence_table.sort_values(
            by=[
                "Win_Pct",
                "Picks",
                "Avg_Confidence",
            ],
            ascending=[
                False,
                False,
                False,
            ],
        ).iloc[0]

        worst_confidence_band = confidence_table.sort_values(
            by=[
                "Win_Pct",
                "Picks",
                "Avg_Confidence",
            ],
            ascending=[
                True,
                False,
                False,
            ],
        ).iloc[0]

        best_confidence_band_summary = {
            "band": str(
                best_confidence_band[
                    "Confidence_Band"
                ]
            ),
            "record": (
                f"{int(best_confidence_band['Correct'])}-"
                f"{int(best_confidence_band['Incorrect'])}"
            ),
            "picks": int(
                best_confidence_band["Picks"]
            ),
            "win_pct": (
                best_confidence_band["Win_Pct"]
            ),
            "avg_confidence": (
                best_confidence_band[
                    "Avg_Confidence"
                ]
            ),
        }

        worst_confidence_band_summary = {
            "band": str(
                worst_confidence_band[
                    "Confidence_Band"
                ]
            ),
            "record": (
                f"{int(worst_confidence_band['Correct'])}-"
                f"{int(worst_confidence_band['Incorrect'])}"
            ),
            "picks": int(
                worst_confidence_band["Picks"]
            ),
            "win_pct": (
                worst_confidence_band["Win_Pct"]
            ),
            "avg_confidence": (
                worst_confidence_band[
                    "Avg_Confidence"
                ]
            ),
        }

    return {
        "overview": player_overview,
        "status": status,
        "weekly": summary["weekly"],
        "home_away": summary["home_away"],
        "teams": summary["teams"],
        "opponents": summary["opponents"],
        "confidence": summary["confidence"],
        "highest_confidence_correct": (
            highest_confidence_correct
        ),
        "highest_confidence_miss": (
            highest_confidence_miss
        ),
        "best_teams": best_teams,
        "worst_teams": worst_teams,
        "best_week": best_week_summary,
        "worst_week": worst_week_summary,
        "best_confidence_band": best_confidence_band_summary,
        "worst_confidence_band": worst_confidence_band_summary,
    }

def get_division_records(team_records_df):

    if team_records_df.empty:
        return []

    division_records = []

    for division, teams in NFL_DIVISIONS.items():

        division_teams = team_records_df[
            team_records_df["picked_team"].isin(teams)
        ].copy()

        wins = int(
            division_teams["Correct"].sum()
        )

        losses = int(
            division_teams["Incorrect"].sum()
        )

        total_picks = wins + losses

        if total_picks > 0:
            win_pct = wins / total_picks
        else:
            win_pct = 0.0

        division_records.append(
            {
                "Division": division,
                "Correct": wins,
                "Incorrect": losses,
                "Picks": total_picks,
                "Win_Pct": win_pct,
                "Teams": division_teams,
            }
        )

    return division_records

def get_opponent_division_records(opponent_records_df):

    if opponent_records_df.empty:
        return []

    division_records = []

    for division, teams in NFL_DIVISIONS.items():

        division_teams = opponent_records_df[
            opponent_records_df["opponent"].isin(teams)
        ].copy()

        wins = int(
            division_teams["Correct"].sum()
        )

        losses = int(
            division_teams["Incorrect"].sum()
        )

        total_picks = wins + losses

        if total_picks > 0:
            win_pct = wins / total_picks
        else:
            win_pct = 0.0

        division_records.append(
            {
                "Division": division,
                "Correct": wins,
                "Incorrect": losses,
                "Picks": total_picks,
                "Win_Pct": win_pct,
                "Teams": division_teams,
            }
        )

    return division_records

def display_player_explorer(df, player):
    """
    Display Player Explorer v2 in the terminal.
    """

    explorer = get_player_explorer(
        df,
        player,
    )

    overview = explorer["overview"]

    win_pct = (
        f"{overview['Win_Pct']:.1%}"
        if overview["Win_Pct"] is not None
        else "N/A"
    )

    point_efficiency = (
        f"{overview['Point_Efficiency']:.1%}"
        if overview["Point_Efficiency"] is not None
        else "N/A"
    )

    print("\nOVERVIEW")
    print("-" * 50)

    print(
        f"Record: {overview['Record']}"
    )

    print(
        f"Win Percentage: {win_pct}"
    )

    print(
        f"Confidence Points: "
        f"{overview['Confidence_Points']}"
    )

    print(
        f"Confidence Risked: "
        f"{overview['Confidence_Risked']}"
    )

    print(
        f"Point Efficiency: "
        f"{point_efficiency}"
    )

    print("\n" + "-" * 70)
    print("KEY INSIGHTS")
    print("-" * 70)

    correct = explorer[
        "highest_confidence_correct"
    ]

    if correct:
        print(
            "Highest-Confidence Correct Pick: "
            f"{correct['team']} over "
            f"{correct['opponent']} "
            f"({correct['confidence']} points, "
            f"Week {correct['week']})"
        )
    else:
        print(
            "Highest-Confidence Correct Pick: "
            "None"
        )

    miss = explorer[
        "highest_confidence_miss"
    ]

    if miss:
        print(
            "Highest-Confidence Miss: "
            f"{miss['team']} vs "
            f"{miss['opponent']} "
            f"({miss['confidence']} points, "
            f"Week {miss['week']})"
        )
    else:
        print(
            "Highest-Confidence Miss: None"
        )

    best_week = explorer["best_week"]
    worst_week = explorer["worst_week"]

    print("\nWEEKLY HIGHLIGHTS")
    print("-" * 50)

    if best_week is None:
        print(
            "No completed weekly results yet."
        )

    else:
        print(
            "Best Week: "
            f"Week {best_week['week']} — "
            f"{best_week['record']} — "
            f"{best_week['confidence_points']} points"
        )

        print(
            "Worst Week: "
            f"Week {worst_week['week']} — "
            f"{worst_week['record']} — "
            f"{worst_week['confidence_points']} points"
        )

    best_band = explorer["best_confidence_band"]
    worst_band = explorer["worst_confidence_band"]

    print("\nCONFIDENCE HIGHLIGHTS")
    print("-" * 50)

    if best_band is None:
        print(
            "No completed confidence results yet."
        )

    else:
        print(
            "Best Confidence Band: "
            f"{best_band['band']} — "
            f"{best_band['record']} — "
            f"{best_band['win_pct']:.1%}"
        )

        print(
            "Worst Confidence Band: "
            f"{worst_band['band']} — "
            f"{worst_band['record']} — "
            f"{worst_band['win_pct']:.1%}"
        )

    print("\nBest Team Results:")

    best_teams = (
        explorer["best_teams"]
        .head(3)
        .copy()
    )

    best_teams["Win_Pct"] = (
        best_teams["Win_Pct"]
        .map(
            lambda value: f"{value:.1%}"
        )
    )

    print(
        best_teams[
            [
                "picked_team",
                "Correct",
                "Incorrect",
                "Win_Pct",
                "Avg_Confidence",
            ]
        ].to_string(
            index=False
        )
    )

    print("\nWorst Team Results:")

    worst_teams = (
        explorer["worst_teams"]
        .head(3)
        .copy()
    )

    worst_teams["Win_Pct"] = (
        worst_teams["Win_Pct"]
        .map(
            lambda value: f"{value:.1%}"
        )
    )

    print(
        worst_teams[
            [
                "picked_team",
                "Correct",
                "Incorrect",
                "Win_Pct",
                "Avg_Confidence",
            ]
        ].to_string(
            index=False
        )
    )

    print("\n" + "-" * 70)
    print("WEEKLY RESULTS")
    print("-" * 70)

    weekly = explorer["weekly"].copy()

    weekly["Win_Pct"] = (
        weekly["Win_Pct"]
        .map(
            lambda value: f"{value:.1%}"
        )
    )

    print(
        weekly.to_string(
            index=False
        )
    )

    print("\n" + "-" * 70)
    print("HOME VS AWAY")
    print("-" * 70)

    home_away = (
        explorer["home_away"].copy()
    )

    home_away["Win_Pct"] = (
        home_away["Win_Pct"]
        .map(
            lambda value: f"{value:.1%}"
        )
    )

    print(
        home_away.to_string(
            index=False
        )
    )

    print("\n" + "-" * 70)
    print("TEAM RECORDS")
    print("-" * 70)

    teams = explorer["teams"].copy()

    teams["Win_Pct"] = (
        teams["Win_Pct"]
        .map(
            lambda value: f"{value:.1%}"
        )
    )

    print(
        teams.to_string(
            index=False
        )
    )

    print("\n" + "-" * 70)
    print("RECORD WHEN PICKING AGAINST TEAM")
    print("-" * 70)

    opponents = (
        explorer["opponents"].copy()
    )

    opponents["Win_Pct"] = (
        opponents["Win_Pct"]
        .map(
            lambda value: f"{value:.1%}"
        )
    )

    print(
        opponents.to_string(
            index=False
        )
    )

    print("\n" + "-" * 70)
    print("CONFIDENCE PERFORMANCE")
    print("-" * 70)

    confidence = (
        explorer["confidence"].copy()
    )

    confidence["Win_Pct"] = (
        confidence["Win_Pct"]
        .map(
            lambda value: f"{value:.1%}"
        )
    )

    print(
        confidence.to_string(
            index=False
        )
    )