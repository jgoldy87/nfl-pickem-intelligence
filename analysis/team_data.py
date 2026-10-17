import nflreadpy as nfl
import pandas as pd

from analysis.situational import (
    load_pbp_data,
    load_third_down_stats,
    load_red_zone_stats,
)


def load_team_games(season):
    """
    Load NFL team statistics and schedules, then create
    one row per team per regular-season game.
    """

    # --------------------------------------------------
    # LOAD WEEKLY TEAM STATS
    # --------------------------------------------------

    team_stats = nfl.load_team_stats(
        seasons=season,
        summary_level="week",
    ).to_pandas()

    team_stats = team_stats[
        team_stats["season_type"] == "REG"
    ].copy()


    # --------------------------------------------------
    # CALCULATE BASIC OFFENSIVE METRICS
    # --------------------------------------------------

    team_stats["net_passing_yards"] = (
        team_stats["passing_yards"]
        + team_stats["sack_yards_lost"]
    )

    team_stats["total_yards"] = (
        team_stats["net_passing_yards"]
        + team_stats["rushing_yards"]
    )

    team_stats["offensive_plays"] = (
        team_stats["attempts"]
        + team_stats["carries"]
        + team_stats["sacks_suffered"]
    )

    team_stats["yards_per_play"] = (
        team_stats["total_yards"]
        / team_stats["offensive_plays"]
    )

    # --------------------------------------------------
    # TURNOVERS
    # --------------------------------------------------

    team_stats["giveaways"] = (
        team_stats["passing_interceptions"]
        + team_stats["fumbles_lost_total"]
    )

    # --------------------------------------------------
    # CREATE DEFENSIVE / OPPONENT STATS
    # --------------------------------------------------

    opponent_stats = team_stats[
        [
            "game_id",
            "team",
            "net_passing_yards",
            "rushing_yards",
            "total_yards",
            "offensive_plays",
            "yards_per_play",
            "giveaways",
        ]
    ].copy()

    opponent_stats = opponent_stats.rename(
        columns={
            "team": "opponent_team_check",
            "net_passing_yards": "passing_yards_allowed",
            "rushing_yards": "rushing_yards_allowed",
            "total_yards": "yards_allowed",
            "offensive_plays": "defensive_plays",
            "yards_per_play": "yards_per_play_allowed",
            "giveaways": "takeaways",
        }
    )

    team_games = team_stats.merge(
        opponent_stats,
        on="game_id",
        how="left",
    )

    team_games = team_games[
        team_games["team"]
        != team_games["opponent_team_check"]
    ].copy()

    team_games["turnover_margin"] = (
        team_games["takeaways"]
        - team_games["giveaways"]
    )

    # --------------------------------------------------
    # LOAD SCHEDULE / SCORES
    # --------------------------------------------------

    schedule = nfl.load_schedules(
        seasons=season
    ).to_pandas()

    schedule = schedule[
        schedule["game_type"] == "REG"
    ].copy()


    # --------------------------------------------------
    # CONVERT SCHEDULE TO ONE ROW PER TEAM
    # --------------------------------------------------

    away_scores = schedule[
        [
            "game_id",
            "away_team",
            "home_team",
            "away_score",
            "home_score",
        ]
    ].copy()

    away_scores = away_scores.rename(
        columns={
            "away_team": "team",
            "home_team": "schedule_opponent",
            "away_score": "points",
            "home_score": "points_allowed",
        }
    )

    away_scores["home_away"] = "Away"


    home_scores = schedule[
        [
            "game_id",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
        ]
    ].copy()

    home_scores = home_scores.rename(
        columns={
            "home_team": "team",
            "away_team": "schedule_opponent",
            "home_score": "points",
            "away_score": "points_allowed",
        }
    )

    home_scores["home_away"] = "Home"


    scores = pd.concat(
        [away_scores, home_scores],
        ignore_index=True,
    )


    # --------------------------------------------------
    # MERGE SCORES INTO TEAM-GAME DATA
    # --------------------------------------------------

    team_games = team_games.merge(
        scores,
        on=["game_id", "team"],
        how="left",
    )

    team_games["point_differential"] = (
        team_games["points"]
        - team_games["points_allowed"]
    )

    # --------------------------------------------------
    # LOAD PLAY-BY-PLAY ONCE
    # --------------------------------------------------

    pbp = load_pbp_data(
        season
    )

    # --------------------------------------------------
    # THIRD-DOWN STATS
    # --------------------------------------------------

    third_down_stats = load_third_down_stats(
        pbp
    )

    team_games = team_games.merge(
        third_down_stats,
        on=["game_id", "team"],
        how="left",
    )

    # --------------------------------------------------
    # RED-ZONE STATS
    # --------------------------------------------------

    red_zone_stats = load_red_zone_stats(
        pbp
    )

    team_games = team_games.merge(
        red_zone_stats,
        on=["game_id", "team"],
        how="left",
    )

    # --------------------------------------------------
    # RETURN CLEAN DATASET
    # --------------------------------------------------

    return team_games