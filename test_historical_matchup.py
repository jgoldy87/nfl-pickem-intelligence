
from analysis.team_data import load_team_games
from analysis.matchups import get_matchup_comparison

SEASON = 2026
WEEK = 5
AWAY_TEAM = "DET"
HOME_TEAM = "ARI"

print("Loading team data...")
team_games = load_team_games(SEASON)

print(f"Loaded {len(team_games)} team-game records.")

# Confirm that both teams have records from before Week 5.
prior_games = team_games[
    (team_games["season"] == SEASON)
    & (team_games["week"] < WEEK)
    & (team_games["team"].isin([AWAY_TEAM, HOME_TEAM]))
]

print("\nPRE-MATCHUP DATA CHECK")
print("-" * 60)
print(
    prior_games.groupby("team")["week"]
    .agg(["count", "min", "max"])
    .to_string()
)

print("\nHISTORICAL MATCHUP COMPARISON")
print("-" * 60)

comparison = get_matchup_comparison(
    team_games=team_games,
    season=SEASON,
    week=WEEK,
    team_a=AWAY_TEAM,
    team_b=HOME_TEAM,
)

print(comparison)
