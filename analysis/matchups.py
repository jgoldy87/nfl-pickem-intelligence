from analysis.rankings import get_team_rankings, STAT_CONFIG

MATCHUP_PROFILE_CONFIG = {
    "Scoring": {
        "offense": "points_per_game",
        "defense": "points_allowed_per_game",
    },

    "Overall Efficiency": {
        "offense": "yards_per_play",
        "defense": "yards_per_play_allowed",
    },

    "Passing": {
        "offense": "passing_yards_per_game",
        "defense": "passing_yards_allowed_per_game",
    },

    "Rushing": {
        "offense": "rushing_yards_per_game",
        "defense": "rushing_yards_allowed_per_game",
    },

    "Third Down": {
        "offense": "third_down_pct",
        "defense": "opponent_third_down_pct",
    },

    "Red Zone": {
        "offense": "red_zone_td_pct",
        "defense": "opponent_red_zone_td_pct",
    },
}

def get_matchup_comparison(
    team_games,
    season,
    week,
    team_a,
    team_b,
):
    """
    Compare two teams using their cumulative statistics
    entering a selected week.

    Example:
        week=10 uses statistics through Week 9.
    """

    through_week = week - 1

    if through_week < 1:
        raise ValueError(
            "Pregame rankings are not available for Week 1 "
            "because no regular-season games have been played yet."
        )

    # --------------------------------------------------
    # GET PREGAME NFL RANKINGS
    # --------------------------------------------------

    rankings = get_team_rankings(
        team_games,
        season=season,
        through_week=through_week,
    )


    # --------------------------------------------------
    # GET EACH TEAM
    # --------------------------------------------------

    team_a_data = rankings[
        rankings["team"] == team_a
    ]

    team_b_data = rankings[
        rankings["team"] == team_b
    ]


    if team_a_data.empty:
        raise ValueError(
            f"No ranking data found for {team_a}."
        )

    if team_b_data.empty:
        raise ValueError(
            f"No ranking data found for {team_b}."
        )


    team_a_data = team_a_data.iloc[0]
    team_b_data = team_b_data.iloc[0]


    # --------------------------------------------------
    # BUILD COMPARISON
    # --------------------------------------------------

    comparison = []

    for metric, config in STAT_CONFIG.items():

        comparison.append(
            {
                "category": config["category"],
                "metric": metric,
                "label": config["label"],

                f"{team_a}_value":
                    team_a_data[metric],

                f"{team_a}_rank":
                    team_a_data[f"{metric}_rank"],

                f"{team_a}_percentile":
                    team_a_data[f"{metric}_percentile"],

                f"{team_b}_value":
                    team_b_data[metric],

                f"{team_b}_rank":
                    team_b_data[f"{metric}_rank"],

                f"{team_b}_percentile":
                    team_b_data[f"{metric}_percentile"],

                "league_avg":
                    team_a_data[
                        f"{metric}_league_avg"
                    ],
            }
        )


    return {
        "season": season,
        "week": week,
        "through_week": through_week,
        "team_a": team_a,
        "team_b": team_b,
        "comparison": comparison,
    }

def get_scheduled_matchup_comparison(
    team_games,
    schedule,
    season,
    week,
    game_id,
):
    """
    Build a pregame comparison for a specific
    scheduled NFL game.
    """

    game = schedule[
        (schedule["season"] == season)
        & (schedule["week"] == week)
        & (schedule["game_id"] == game_id)
    ]

    if game.empty:
        raise ValueError(
            f"Game {game_id} was not found."
        )

    game = game.iloc[0]

    comparison = get_matchup_comparison(
        team_games=team_games,
        season=season,
        week=week,
        team_a=game["away_team"],
        team_b=game["home_team"],
    )

    # Add useful schedule information
    comparison["game_id"] = game["game_id"]
    comparison["away_team"] = game["away_team"]
    comparison["home_team"] = game["home_team"]
    comparison["gameday"] = game["gameday"]
    comparison["gametime"] = game["gametime"]

    return comparison

def get_matchup_profiles(
    team_games,
    season,
    week,
    away_team,
    home_team,
):
    """
    Build offense-vs-defense matchup profiles using
    statistics entering the selected week.
    """

    # The matchup should never use data from the matchup week
    # or later.
    requested_through_week = week - 1

    # Find the latest completed week actually available
    # in our team-game dataset for this season.
    season_games = team_games[
        team_games["season"] == season
    ]

    latest_available_week = int(
        season_games["week"].max()
    )

    # Use whichever cutoff comes first:
    # the week before the matchup or the latest available data.
    through_week = min(
        requested_through_week,
        latest_available_week,
    )

    if through_week < 1:
        raise ValueError(
            "Pregame matchup profiles are not available "
            "for Week 1."
        )

    rankings = get_team_rankings(
        team_games,
        season=season,
        through_week=through_week,
    )

    away_data = rankings[
        rankings["team"] == away_team
    ]

    home_data = rankings[
        rankings["team"] == home_team
    ]

    if away_data.empty:
        raise ValueError(
            f"No ranking data found for {away_team}."
        )

    if home_data.empty:
        raise ValueError(
            f"No ranking data found for {home_team}."
        )

    away_data = away_data.iloc[0]
    home_data = home_data.iloc[0]


    # --------------------------------------------------
    # HELPER: BUILD ONE OFFENSE VS DEFENSE PROFILE
    # --------------------------------------------------

    def build_profile(
        offense_team,
        offense_data,
        defense_team,
        defense_data,
    ):

        profile = []

        for section, metrics in MATCHUP_PROFILE_CONFIG.items():

            offense_metric = metrics["offense"]
            defense_metric = metrics["defense"]

            profile.append(
                {
                    "section": section,

                    "offense_team": offense_team,
                    "offense_metric": offense_metric,
                    "offense_label":
                        STAT_CONFIG[offense_metric]["label"],
                    "offense_value":
                        offense_data[offense_metric],
                    "offense_rank":
                        offense_data[
                            f"{offense_metric}_rank"
                        ],
                    "offense_percentile":
                        offense_data[
                            f"{offense_metric}_percentile"
                        ],

                    "defense_team": defense_team,
                    "defense_metric": defense_metric,
                    "defense_label":
                        STAT_CONFIG[defense_metric]["label"],
                    "defense_value":
                        defense_data[defense_metric],
                    "defense_rank":
                        defense_data[
                            f"{defense_metric}_rank"
                        ],
                    "defense_percentile":
                        defense_data[
                            f"{defense_metric}_percentile"
                        ],
                    "league_average":
                        offense_data[
                            f"{offense_metric}_league_avg"
                        ],
                }
            )

        return profile


    # --------------------------------------------------
    # AWAY OFFENSE VS HOME DEFENSE
    # --------------------------------------------------

    away_offense = build_profile(
        offense_team=away_team,
        offense_data=away_data,
        defense_team=home_team,
        defense_data=home_data,
    )


    # --------------------------------------------------
    # HOME OFFENSE VS AWAY DEFENSE
    # --------------------------------------------------

    home_offense = build_profile(
        offense_team=home_team,
        offense_data=home_data,
        defense_team=away_team,
        defense_data=away_data,
    )


    # --------------------------------------------------
    # TURNOVER PROFILE
    # --------------------------------------------------

    turnover_profile = {
        away_team: {
            "giveaways_per_game":
                away_data["giveaways_per_game"],

            "giveaways_rank":
                away_data["giveaways_per_game_rank"],

            "takeaways_per_game":
                away_data["takeaways_per_game"],

            "takeaways_rank":
                away_data["takeaways_per_game_rank"],

            "turnover_margin_per_game":
                away_data["turnover_margin_per_game"],

            "turnover_margin_rank":
                away_data[
                    "turnover_margin_per_game_rank"
                ],
        },

        home_team: {
            "giveaways_per_game":
                home_data["giveaways_per_game"],

            "giveaways_rank":
                home_data["giveaways_per_game_rank"],

            "takeaways_per_game":
                home_data["takeaways_per_game"],

            "takeaways_rank":
                home_data["takeaways_per_game_rank"],

            "turnover_margin_per_game":
                home_data["turnover_margin_per_game"],

            "turnover_margin_rank":
                home_data[
                    "turnover_margin_per_game_rank"
                ],
        },
    }


    return {
        "season": season,
        "week": week,
        "through_week": through_week,

        "away_team": away_team,
        "home_team": home_team,

        "away_offense": away_offense,
        "home_offense": home_offense,

        "turnovers": turnover_profile,
        "through_week": through_week,
    }