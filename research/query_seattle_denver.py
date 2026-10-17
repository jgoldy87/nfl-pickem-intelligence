
import pandas as pd

from analysis.team_data import load_team_games
from analysis.rankings import get_team_rankings

SEASON = 2026
THROUGH_WEEK = 5
TEAMS = ["SEA", "DEN"]

team_games = load_team_games(SEASON)

rankings = get_team_rankings(
    team_games,
    season=SEASON,
    through_week=THROUGH_WEEK,
)

print("\nSEATTLE VS DENVER")
print(f"2026 NFL | Through Week {THROUGH_WEEK}")
print("=" * 65)

print("\nAVAILABLE RANKING COLUMNS")
print(rankings.columns.tolist())

print("\nTEAM RANKINGS")
print("-" * 65)

comparison = rankings[
    rankings["team"].isin(TEAMS)
].copy()

print(
    comparison
    .set_index("team")
    .T
    .to_string()
)
