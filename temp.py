
import nflreadpy as nfl
import numpy as np
import pandas as pd

SEASON = 2026
THROUGH_WEEK = 6

# Controls how strongly ratings are pulled toward zero.
# Higher values produce more conservative ratings.
RIDGE_STRENGTH = 4.0

schedule = nfl.load_schedules(
    seasons=[SEASON]
).to_pandas()

games = schedule[
    (schedule["game_type"] == "REG")
    & (schedule["week"] <= THROUGH_WEEK)
    & schedule["home_score"].notna()
    & schedule["away_score"].notna()
].copy()

games["margin"] = (
    games["home_score"] - games["away_score"]
).astype(float)

teams = sorted(
    set(games["home_team"]) | set(games["away_team"])
)

team_to_idx = {
    team: i for i, team in enumerate(teams)
}

n_games = len(games)
n_teams = len(teams)

# Each row describes a matchup:
# +1 for home team, -1 for away team.
X = np.zeros((n_games, n_teams))
y = games["margin"].to_numpy()

for row_idx, (_, game) in enumerate(games.iterrows()):
    X[row_idx, team_to_idx[game["home_team"]]] = 1.0
    X[row_idx, team_to_idx[game["away_team"]]] = -1.0

# Solve ridge-regularized least squares:
# min ||Xr - y||^2 + lambda * ||r||^2
#
# With a positive penalty, the system has a unique solution.
regularizer = RIDGE_STRENGTH * np.eye(n_teams)

ratings = np.linalg.solve(
    X.T @ X + regularizer,
    X.T @ y,
)

rating_lookup = dict(zip(teams, ratings))

# Build team-level scoring summaries.
home = games[
    ["home_team", "away_team", "home_score", "away_score"]
].copy()

home.columns = [
    "team", "opponent", "points_for", "points_against"
]

away = games[
    ["away_team", "home_team", "away_score", "home_score"]
].copy()

away.columns = [
    "team", "opponent", "points_for", "points_against"
]

team_games = pd.concat(
    [home, away],
    ignore_index=True,
)

team_games["margin"] = (
    team_games["points_for"] - team_games["points_against"]
)

team_games["win"] = (team_games["margin"] > 0).astype(int)
team_games["loss"] = (team_games["margin"] < 0).astype(int)
team_games["tie"] = (team_games["margin"] == 0).astype(int)

summary = (
    team_games.groupby("team")
    .agg(
        games=("margin", "size"),
        wins=("win", "sum"),
        losses=("loss", "sum"),
        ties=("tie", "sum"),
        point_diff=("margin", "sum"),
        raw_margin_pg=("margin", "mean"),
    )
    .reset_index()
)

summary["record"] = (
    summary["wins"].astype(str)
    + "-"
    + summary["losses"].astype(str)
    + "-"
    + summary["ties"].astype(str)
)

summary["adjusted_rating"] = (
    summary["team"].map(rating_lookup)
)

# Descriptive schedule-strength measure based on
# opponents' fitted adjusted ratings.
opponent_ratings = (
    team_games.assign(
        opponent_rating=team_games["opponent"].map(
            rating_lookup
        )
    )
    .groupby("team")["opponent_rating"]
    .mean()
)

summary["opponent_rating_avg"] = (
    summary["team"].map(opponent_ratings)
)

# Difference between adjusted rating and raw margin.
# This combines schedule correction and ridge shrinkage.
summary["rating_change"] = (
    summary["adjusted_rating"]
    - summary["raw_margin_pg"]
)

summary = summary.sort_values(
    "adjusted_rating",
    ascending=False,
).reset_index(drop=True)

summary.index += 1
summary.index.name = "Rank"

display_columns = [
    "team",
    "record",
    "games",
    "point_diff",
    "raw_margin_pg",
    "opponent_rating_avg",
    "adjusted_rating",
    "rating_change",
]

display = summary[display_columns].copy()

numeric_columns = [
    "raw_margin_pg",
    "opponent_rating_avg",
    "adjusted_rating",
    "rating_change",
]

display[numeric_columns] = (
    display[numeric_columns].round(2)
)

print("\nNFL OPPONENT-ADJUSTED TEAM RATINGS")
print(f"Season: {SEASON} | Through Week: {THROUGH_WEEK}")
print(f"Ridge strength: {RIDGE_STRENGTH}")
print("Ratings are relative to league average, in points/game")
print("=" * 115)
print(display.to_string())

# Identify how rankings differ from raw point differential.
raw_ranks = summary["raw_margin_pg"].rank(
    ascending=False,
    method="min",
).astype(int)

summary["raw_rank"] = raw_ranks
summary["adjusted_rank"] = np.arange(1, len(summary) + 1)

# Positive means the team ranks higher after adjustment.
summary["rank_improvement"] = (
    summary["raw_rank"] - summary["adjusted_rank"]
)

movement = summary[
    [
        "team",
        "record",
        "raw_rank",
        "adjusted_rank",
        "rank_improvement",
    ]
].copy()

print("\nBIGGEST RANKING IMPROVEMENTS")
print("=" * 80)
print(
    movement.sort_values(
        "rank_improvement",
        ascending=False,
    ).head(10).to_string(index=False)
)

print("\nBIGGEST RANKING DECLINES")
print("=" * 80)
print(
    movement.sort_values(
        "rank_improvement",
        ascending=True,
    ).head(10).to_string(index=False)
)

focus_teams = [
    "DEN", "CLE", "SF", "HOU",
    "NYG", "MIN", "GB", "ATL",
    "KC", "SEA",
]

print("\nFOCUS TEAMS")
print("=" * 115)

print(
    display[
        display["team"].isin(focus_teams)
    ].to_string(index=False)
)

# Verify that the fitted ratings are centered at zero.
print("\nMODEL CHECKS")
print("=" * 80)
print(f"Games included: {n_games}")
print(f"Teams included: {n_teams}")
print(f"Mean adjusted rating: {ratings.mean():+.8f}")
