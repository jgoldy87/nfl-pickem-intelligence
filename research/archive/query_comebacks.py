
import pandas as pd
import nflreadpy as nfl

SEASONS = list(range(2020, 2026))

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

print("Loading NFL schedules...")
games = nfl.load_schedules(SEASONS).to_pandas()

games = games[
    (games["game_type"] == "REG")
    & games["home_score"].notna()
    & games["away_score"].notna()
].copy()

print("Loading NFL play-by-play...")
pbp = nfl.load_pbp(SEASONS).to_pandas()

# --------------------------------------------------
# GET HALFTIME SCORES
# --------------------------------------------------

# At the beginning of the third quarter, the
# pre-play scores represent the halftime score.
# Take the first available Q3 play for each game.

q3 = pbp[
    (pbp["qtr"] == 3)
    & pbp["total_home_score"].notna()
    & pbp["total_away_score"].notna()
].copy()

q3 = q3.sort_values(
    ["game_id", "play_id"]
)

halftime = (
    q3.groupby("game_id", as_index=False)
    .first()[
        ["game_id", "total_home_score", "total_away_score"]
    ]
    .rename(columns={
        "total_home_score": "HT_Home",
        "total_away_score": "HT_Away",
    })
)

games = games.merge(
    halftime,
    on="game_id",
    how="left",
    validate="one_to_one",
)

missing = games["HT_Home"].isna().sum()

print(f"\nGames missing halftime scores: {missing}")

games = games.dropna(
    subset=["HT_Home", "HT_Away"]
).copy()

# --------------------------------------------------
# IDENTIFY HALFTIME LEADERS AND WINNERS
# --------------------------------------------------

games["HT_Difference"] = (
    games["HT_Home"] - games["HT_Away"]
)

games["Final_Difference"] = (
    games["home_score"] - games["away_score"]
)

# Positive = home team ahead
# Negative = away team ahead
# Zero = tied

games["Halftime_Tied"] = (
    games["HT_Difference"] == 0
)

games["Final_Tied"] = (
    games["Final_Difference"] == 0
)

games["Deficit"] = games["HT_Difference"].abs()

games["Comeback"] = (
    (games["HT_Difference"] * games["Final_Difference"]) < 0
)

# --------------------------------------------------
# DEFINE DEFICIT GROUPS
# --------------------------------------------------

def deficit_group(points):
    if points <= 3:
        return "01-03"
    if points <= 7:
        return "04-07"
    if points <= 10:
        return "08-10"
    if points <= 14:
        return "11-14"
    if points <= 20:
        return "15-20"
    return "21+"


trailing_games = games[
    ~games["Halftime_Tied"]
].copy()

trailing_games["Deficit_Group"] = (
    trailing_games["Deficit"].apply(deficit_group)
)

# --------------------------------------------------
# OVERALL SUMMARY
# --------------------------------------------------

print("\nHALFTIME COMEBACKS — 2020-2025")
print("=" * 75)

print(f"Total games analyzed: {len(games)}")
print(
    f"Tied at halftime: "
    f"{games['Halftime_Tied'].sum()}"
)
print(
    f"Games with halftime leader: "
    f"{len(trailing_games)}"
)
print(
    f"Halftime comebacks: "
    f"{trailing_games['Comeback'].sum()}"
)
print(
    f"Comeback rate: "
    f"{trailing_games['Comeback'].mean() * 100:.2f}%"
)
print(
    f"Final ties after halftime lead: "
    f"{trailing_games['Final_Tied'].sum()}"
)

# --------------------------------------------------
# COMEBACK RATE BY DEFICIT
# --------------------------------------------------

summary = (
    trailing_games.groupby("Deficit_Group")
    .agg(
        Games=("Comeback", "size"),
        Comebacks=("Comeback", "sum"),
        Final_Ties=("Final_Tied", "sum"),
    )
)

summary["Comeback_Rate"] = (
    summary["Comebacks"] / summary["Games"] * 100
)

print("\nCOMEBACK RATE BY HALFTIME DEFICIT")
print("=" * 75)
print(summary.round(2).to_string())

# --------------------------------------------------
# COMEBACKS BY SEASON
# --------------------------------------------------

season_summary = (
    trailing_games.groupby("season")
    .agg(
        Games=("Comeback", "size"),
        Comebacks=("Comeback", "sum"),
    )
)

season_summary["Comeback_Rate"] = (
    season_summary["Comebacks"]
    / season_summary["Games"] * 100
)

print("\nCOMEBACK RATE BY SEASON")
print("=" * 75)
print(season_summary.round(2).to_string())

# --------------------------------------------------
# BIGGEST HALFTIME COMEBACKS
# --------------------------------------------------

biggest = trailing_games[
    trailing_games["Comeback"]
].sort_values(
    ["Deficit", "season", "week"],
    ascending=[False, True, True],
)

print("\nBIGGEST HALFTIME COMEBACKS")
print("=" * 100)

columns = [
    "season",
    "week",
    "away_team",
    "home_team",
    "HT_Away",
    "HT_Home",
    "away_score",
    "home_score",
    "Deficit",
]

print(
    biggest[columns]
    .head(15)
    .to_string(index=False)
)

# --------------------------------------------------
# VALIDATION
# --------------------------------------------------

print("\nVALIDATION")
print("=" * 75)

print(
    "Unique games:",
    games["game_id"].nunique()
)
print(
    "Duplicate game IDs:",
    games["game_id"].duplicated().sum()
)
print(
    "Halftime scores above final scores:",
    (
        (games["HT_Home"] > games["home_score"])
        | (games["HT_Away"] > games["away_score"])
    ).sum()
)
