
import pandas as pd

from analysis.data_pipeline import build_master_results_from_supabase
from analysis.market_performance import get_market_performance
from analysis.team_data import load_team_games
from analysis.rankings import get_team_rankings

SEASON = 2026
PLAYERS = ["Jimmy", "John", "Jesse"]
GAME_KEYS = ["season", "week", "game_id"]
MARKET_KEYS = ["season", "week", "away_team", "home_team"]

# For these metrics, higher values are better.
# We reverse defensive metrics so a positive advantage
# always means the underdog was statistically better.
METRICS = {
    "point_differential_per_game": 1,
    "yards_per_play": 1,
    "yards_per_play_allowed": -1,
    "turnover_margin_per_game": 1,
    "third_down_pct": 1,
}

LABELS = {
    "point_differential_per_game": "Point differential/game",
    "yards_per_play": "Offensive yards/play",
    "yards_per_play_allowed": "Defensive yards/play allowed",
    "turnover_margin_per_game": "Turnover margin/game",
    "third_down_pct": "Third-down conversion %",
}

print("\nUNDERDOG MATCHUP RESEARCH")
print("=" * 80)

# ------------------------------------------------------------
# 1. LOAD PICKS
# ------------------------------------------------------------

picks = build_master_results_from_supabase()

picks = picks[
    (picks["season"] == SEASON)
    & picks["game_completed"].eq(True)
    & picks["pick_correct"].notna()
].copy()

picks["player"] = picks["player"].str.strip().str.title()
picks = picks[picks["player"].isin(PLAYERS)]

picks = picks.dropna(subset=["picked_team"])

# Require exactly one selection from each player.
counts = picks.groupby(GAME_KEYS)["player"].agg(
    ["count", "nunique"]
)

valid_games = counts[
    (counts["count"] == 3)
    & (counts["nunique"] == 3)
].index

complete = picks.set_index(GAME_KEYS).loc[
    lambda x: x.index.isin(valid_games)
].reset_index()

# ------------------------------------------------------------
# 2. IDENTIFY LONE WOLVES
# ------------------------------------------------------------

records = []

for _, group in complete.groupby(GAME_KEYS):
    team_counts = group["picked_team"].value_counts()

    if sorted(team_counts.tolist()) != [1, 2]:
        continue

    lone_team = team_counts[team_counts == 1].index[0]
    lone = group[group["picked_team"] == lone_team].iloc[0]

    records.append({
        "season": int(lone["season"]),
        "week": int(lone["week"]),
        "away_team": lone["away_team"],
        "home_team": lone["home_team"],
        "player": lone["player"],
        "picked_team": lone["picked_team"],
        "won": bool(lone["pick_correct"]),
    })

lone_wolves = pd.DataFrame(records)

if lone_wolves.empty:
    raise ValueError("No lone-wolf selections found.")

# ------------------------------------------------------------
# 3. MATCH MARKET DATA
# ------------------------------------------------------------

markets = get_market_performance(SEASON)

markets = markets[
    (markets["game_type"] == "REG")
    & (markets["winner"] != "TIE")
].copy()

markets = markets[
    MARKET_KEYS + ["market_pick", "market_probability"]
]

if markets.duplicated(MARKET_KEYS).any():
    raise ValueError("Duplicate market records detected.")

lone_wolves = lone_wolves.merge(
    markets,
    on=MARKET_KEYS,
    how="left",
    validate="many_to_one",
    indicator=True,
)

if (lone_wolves["_merge"] != "both").any():
    raise ValueError("Some lone wolves have no market data.")

lone_wolves = lone_wolves.drop(columns="_merge")

# Keep only underdog lone wolves.
underdogs = lone_wolves[
    lone_wolves["picked_team"] != lone_wolves["market_pick"]
].copy()

total_underdogs = len(underdogs)

# Week 1 has no current-season pregame team statistics.
week_one_count = int((underdogs["week"] == 1).sum())

underdogs = underdogs[underdogs["week"] > 1].copy()

print(f"Total underdog lone wolves: {total_underdogs}")
print(f"Week 1 excluded: {week_one_count}")
print(f"Eligible for analysis: {len(underdogs)}")

if underdogs.empty:
    raise ValueError("No eligible underdog selections.")

# ------------------------------------------------------------
# 4. LOAD TEAM DATA
# ------------------------------------------------------------

print("\nLoading historical team statistics...")

team_games = load_team_games(SEASON)

# Cache rankings for each historical week.
rankings_cache = {}

for week in sorted(underdogs["week"].unique()):
    rankings_cache[week] = get_team_rankings(
        team_games,
        season=SEASON,
        through_week=int(week) - 1,
    ).set_index("team")

# ------------------------------------------------------------
# 5. CALCULATE PREGAME STATISTICAL ADVANTAGES
# ------------------------------------------------------------

results = []

for _, game in underdogs.iterrows():
    week = int(game["week"])
    underdog = game["picked_team"]
    favorite = game["market_pick"]

    rankings = rankings_cache[week]

    if underdog not in rankings.index:
        raise ValueError(f"Missing {underdog} rankings for Week {week}")

    if favorite not in rankings.index:
        raise ValueError(f"Missing {favorite} rankings for Week {week}")

    underdog_stats = rankings.loc[underdog]
    favorite_stats = rankings.loc[favorite]

    result = {
        "Week": week,
        "Player": game["player"],
        "Underdog": underdog,
        "Favorite": favorite,
        "Won": game["won"],
        "Pregame Through Week": week - 1,
    }

    for metric, direction in METRICS.items():
        difference = (
            underdog_stats[metric]
            - favorite_stats[metric]
        ) * direction

        # Convert third-down rate to percentage points.
        if metric == "third_down_pct":
            difference *= 100

        result[metric] = difference

    results.append(result)

analysis = pd.DataFrame(results)

# ------------------------------------------------------------
# 6. DISPLAY RESULTS
# ------------------------------------------------------------

print("\nSAMPLE SUMMARY")
print("-" * 80)

print(f"Winning underdogs: {int(analysis['Won'].sum())}")
print(f"Losing underdogs: {int((~analysis['Won']).sum())}")

summary = (
    analysis.groupby("Won")[list(METRICS)]
    .mean()
    .T
    .rename(columns={False: "Losing", True: "Winning"})
)

summary = summary.rename(index=LABELS)

# Show columns even if a group has no observations.
summary = summary.reindex(columns=["Winning", "Losing"])

print("\nAVERAGE PREGAME ADVANTAGE: UNDERDOG MINUS FAVORITE")
print("-" * 80)
print("Positive = underdog had the better statistic.")
print("Third-down differences are in percentage points.\n")

print(summary.round(2).to_string())

print("\nHISTORICAL CUTOFF CHECK")
print("-" * 80)

cutoff_valid = (
    analysis["Pregame Through Week"]
    == analysis["Week"] - 1
).all()

print(f"All matchup cutoffs correct: {cutoff_valid}")
print(f"Matchups analyzed: {len(analysis)}")

print("\nAnalysis complete.")
