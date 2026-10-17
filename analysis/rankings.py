import pandas as pd

STAT_CONFIG = {
    "points_per_game": {
        "label": "Points/Game",
        "category": "Offense",
        "better": "higher",
        "format": ".1f",
    },

    "points_allowed_per_game": {
        "label": "Points Allowed/Game",
        "category": "Defense",
        "better": "lower",
        "format": ".1f",
    },

    "point_differential_per_game": {
        "label": "Point Differential/Game",
        "category": "Overall",
        "better": "higher",
        "format": "+.1f",
    },

    "yards_per_game": {
        "label": "Yards/Game",
        "category": "Offense",
        "better": "higher",
        "format": ".1f",
    },

    "yards_per_play": {
        "label": "Yards/Play",
        "category": "Offense",
        "better": "higher",
        "format": ".2f",
    },

    "passing_yards_per_game": {
        "label": "Pass Yards/Game",
        "category": "Offense",
        "better": "higher",
        "format": ".1f",
    },

    "rushing_yards_per_game": {
        "label": "Rush Yards/Game",
        "category": "Offense",
        "better": "higher",
        "format": ".1f",
    },    

    "yards_allowed_per_game": {
        "label": "Yards Allowed/Game",
        "category": "Defense",
        "better": "lower",
        "format": ".1f",
    },

    "passing_yards_allowed_per_game": {
        "label": "Pass Yards Allowed/Game",
        "category": "Defense",
        "better": "lower",
        "format": ".1f",
    },

    "rushing_yards_allowed_per_game": {
        "label": "Rush Yards Allowed/Game",
        "category": "Defense",
        "better": "lower",
        "format": ".1f",
    },

    "yards_per_play_allowed": {
        "label": "Yards Allowed/Play",
        "category": "Defense",
        "better": "lower",
        "format": ".2f",
    },

    "giveaways_per_game": {
        "label": "Giveaways/Game",
        "category": "Turnovers",
        "better": "lower",
        "format": ".2f",
    },

    "takeaways_per_game": {
        "label": "Takeaways/Game",
        "category": "Turnovers",
        "better": "higher",
        "format": ".2f",
    },

    "turnover_margin_per_game": {
        "label": "Turnover Margin/Game",
        "category": "Turnovers",
        "better": "higher",
        "format": "+.2f",
    },

    "third_down_pct": {
        "label": "3rd Down %",
        "category": "Situational",
        "better": "higher",
        "format": ".1%",
    },

    "opponent_third_down_pct": {
        "label": "Opponent 3rd Down %",
        "category": "Situational",
        "better": "lower",
        "format": ".1%",
    },

    "red_zone_td_pct": {
        "label": "Red Zone TD %",
        "category": "Situational",
        "better": "higher",
        "format": ".1%",
    },

    "opponent_red_zone_td_pct": {
        "label": "Opponent Red Zone TD %",
        "category": "Situational",
        "better": "lower",
        "format": ".1%",
    },
}

def format_stat_value(metric, value):
    """
    Format a statistical value using the display
    format defined in STAT_CONFIG.
    """

    if metric not in STAT_CONFIG:
        return str(value)

    format_string = STAT_CONFIG[
        metric
    ].get(
        "format",
        ".1f",
    )

    return format(
        value,
        format_string,
    )

def get_team_rankings(team_games, season, through_week):
    """
    Calculate cumulative team statistics and NFL rankings
    through a selected week.

    Example:
        through_week=9 means Weeks 1-9 are included.
    """

    # --------------------------------------------------
    # FILTER DATA
    # --------------------------------------------------

    data = team_games[
        (team_games["season"] == season)
        & (team_games["week"] <= through_week)
    ].copy()


    # --------------------------------------------------
    # AGGREGATE TEAM TOTALS
    # --------------------------------------------------

    rankings = (
        data.groupby("team")
        .agg(
            games=("game_id", "count"),

            points=("points", "sum"),
            points_allowed=("points_allowed", "sum"),

            total_yards=("total_yards", "sum"),
            passing_yards=("net_passing_yards", "sum"),
            rushing_yards=("rushing_yards", "sum"),
            offensive_plays=("offensive_plays", "sum"),

            yards_allowed=("yards_allowed", "sum"),
            passing_yards_allowed=(
                "passing_yards_allowed",
                "sum",
            ),
            rushing_yards_allowed=(
                "rushing_yards_allowed",
                "sum",
            ),
            defensive_plays=("defensive_plays", "sum"),
            giveaways=("giveaways", "sum"),
            takeaways=("takeaways", "sum"),
            turnover_margin=("turnover_margin", "sum"),

            third_down_attempts=(
                "third_down_attempts",
                "sum",
            ),

            third_down_conversions=(
                "third_down_conversions",
                "sum",
            ),

            opponent_third_down_attempts=(
                "opponent_third_down_attempts",
                "sum",
            ),

            opponent_third_down_conversions=(
                "opponent_third_down_conversions",
                "sum",
            ),

            red_zone_attempts=(
                "red_zone_attempts",
                "sum",
            ),

            red_zone_tds=(
                "red_zone_tds",
                "sum",
            ),

            opponent_red_zone_attempts=(
                "opponent_red_zone_attempts",
                "sum",
            ),

            opponent_red_zone_tds=(
                "opponent_red_zone_tds",
                "sum",
            ),
        )
        .reset_index()
    )


    # --------------------------------------------------
    # CALCULATE PER-GAME / EFFICIENCY METRICS
    # --------------------------------------------------

    rankings["points_per_game"] = (
        rankings["points"]
        / rankings["games"]
    )

    rankings["points_allowed_per_game"] = (
        rankings["points_allowed"]
        / rankings["games"]
    )

    rankings["point_differential_per_game"] = (
        (
            rankings["points"]
            - rankings["points_allowed"]
        )
        / rankings["games"]
    )

    rankings["yards_per_game"] = (
        rankings["total_yards"]
        / rankings["games"]
    )

    rankings["passing_yards_per_game"] = (
        rankings["passing_yards"]
        / rankings["games"]
    )

    rankings["rushing_yards_per_game"] = (
        rankings["rushing_yards"]
        / rankings["games"]
    )

    rankings["yards_per_play"] = (
        rankings["total_yards"]
        / rankings["offensive_plays"]
    )

    rankings["yards_allowed_per_game"] = (
        rankings["yards_allowed"]
        / rankings["games"]
    )

    rankings["passing_yards_allowed_per_game"] = (
        rankings["passing_yards_allowed"]
        / rankings["games"]
    )

    rankings["rushing_yards_allowed_per_game"] = (
        rankings["rushing_yards_allowed"]
        / rankings["games"]
    )

    rankings["yards_per_play_allowed"] = (
        rankings["yards_allowed"]
        / rankings["defensive_plays"]
    )

    rankings["giveaways_per_game"] = (
        rankings["giveaways"]
        / rankings["games"]
    )

    rankings["takeaways_per_game"] = (
        rankings["takeaways"]
        / rankings["games"]
    )

    rankings["turnover_margin_per_game"] = (
        rankings["turnover_margin"]
        / rankings["games"]
    )

    rankings["third_down_pct"] = (
        rankings["third_down_conversions"]
        / rankings["third_down_attempts"]
    )

    rankings["opponent_third_down_pct"] = (
        rankings["opponent_third_down_conversions"]
        / rankings["opponent_third_down_attempts"]
    )

    rankings["red_zone_td_pct"] = (
        rankings["red_zone_tds"]
        / rankings["red_zone_attempts"]
    )

    rankings["opponent_red_zone_td_pct"] = (
        rankings["opponent_red_zone_tds"]
        / rankings["opponent_red_zone_attempts"]
    )

    # --------------------------------------------------
    # CALCULATE NFL RANKINGS
    # --------------------------------------------------

    # Higher is better
    higher_is_better = [
        "points_per_game",
        "point_differential_per_game",
        "yards_per_game",
        "yards_per_play",
    ]

    # Lower is better
    lower_is_better = [
        "points_allowed_per_game",
        "yards_allowed_per_game",
        "yards_per_play_allowed",
    ]


    # --------------------------------------------------
    # CALCULATE NFL RANKINGS AND CONTEXT
    # --------------------------------------------------

    for metric, config in STAT_CONFIG.items():

        # Lower values are better for defensive metrics
        # such as Points Allowed/Game.
        ascending = config["better"] == "lower"

        # NFL rank
        rankings[f"{metric}_rank"] = (
            rankings[metric]
            .rank(
                ascending=ascending,
                method="min",
            )
            .astype("Int64")
        )

        # League average
        rankings[f"{metric}_league_avg"] = (
            rankings[metric].mean()
        )

        # Percentile where a higher percentile always means
        # better performance, regardless of metric direction.
        if config["better"] == "higher":
            rankings[f"{metric}_percentile"] = (
                rankings[metric]
                .rank(pct=True)
                * 100
            )

        else:
            rankings[f"{metric}_percentile"] = (
                rankings[metric]
                .rank(
                    pct=True,
                    ascending=False,
                )
                * 100
            )


    return rankings

def format_stat_value(metric, value):
    """
    Format a statistical value using its STAT_CONFIG
    display format.
    """

    if metric not in STAT_CONFIG:
        return str(value)

    format_string = STAT_CONFIG[
        metric
    ].get(
        "format",
        ".2f",
    )

    return format(
        value,
        format_string,
    )

def format_rank(rank):
    """
    Format an NFL ranking for display.

    Returns N/A when a ranking is unavailable.
    """

    if pd.isna(rank):
        return "N/A"

    return f"#{int(rank)} in NFL"