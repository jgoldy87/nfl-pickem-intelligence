import pandas as pd

START_SEASON = 1999
END_SEASON = 2025

url = (
    "https://raw.githubusercontent.com/"
    "nflverse/nfldata/master/data/games.csv"
)

print("Loading NFL game data...")

games = pd.read_csv(url)

# ---------------------------------------------------------
# REGULAR-SEASON COMPLETED GAMES
# ---------------------------------------------------------

games = games[
    (games["season"] >= START_SEASON)
    & (games["season"] <= END_SEASON)
    & (games["game_type"] == "REG")
    & games["home_score"].notna()
    & games["away_score"].notna()
].copy()

# Neutral-site games are not true home/road games.
games = games[
    games["location"] == "Home"
].copy()

print(f"Games loaded: {len(games):,}")


# ---------------------------------------------------------
# CREATE HOME-TEAM RECORDS
# ---------------------------------------------------------

home = games[
    [
        "season",
        "game_id",
        "home_team",
        "home_score",
        "away_score",
    ]
].copy()

home = home.rename(
    columns={
        "home_team": "Team",
        "home_score": "Points For",
        "away_score": "Points Against",
    }
)

home["Location"] = "Home"


# ---------------------------------------------------------
# CREATE ROAD-TEAM RECORDS
# ---------------------------------------------------------

road = games[
    [
        "season",
        "game_id",
        "away_team",
        "away_score",
        "home_score",
    ]
].copy()

road = road.rename(
    columns={
        "away_team": "Team",
        "away_score": "Points For",
        "home_score": "Points Against",
    }
)

road["Location"] = "Road"


# ---------------------------------------------------------
# COMBINE TEAM-GAME RECORDS
# ---------------------------------------------------------

team_games = pd.concat(
    [home, road],
    ignore_index=True,
)

team_games["Win"] = (
    team_games["Points For"]
    > team_games["Points Against"]
).astype(int)

team_games["Loss"] = (
    team_games["Points For"]
    < team_games["Points Against"]
).astype(int)

team_games["Tie"] = (
    team_games["Points For"]
    == team_games["Points Against"]
).astype(int)

# Treat ties as half a win for Win %
team_games["Win Value"] = (
    team_games["Win"]
    + 0.5 * team_games["Tie"]
)

team_games["Point Differential"] = (
    team_games["Points For"]
    - team_games["Points Against"]
)


# ---------------------------------------------------------
# SUMMARIZE EACH TEAM-SEASON BY LOCATION
# ---------------------------------------------------------

summary = (
    team_games.groupby(
        ["season", "Team", "Location"]
    )
    .agg(
        Games=("game_id", "count"),
        Wins=("Win", "sum"),
        Losses=("Loss", "sum"),
        Ties=("Tie", "sum"),
        Win_Value=("Win Value", "sum"),
        Point_Differential=("Point Differential", "sum"),
    )
    .reset_index()
)

summary["Win %"] = (
    summary["Win_Value"]
    / summary["Games"]
    * 100
)

summary["PD/G"] = (
    summary["Point_Differential"]
    / summary["Games"]
)


# ---------------------------------------------------------
# SPLIT HOME AND ROAD
# ---------------------------------------------------------

home_summary = summary[
    summary["Location"] == "Home"
].copy()

road_summary = summary[
    summary["Location"] == "Road"
].copy()


home_summary = home_summary.rename(
    columns={
        "Games": "Home Games",
        "Wins": "Home Wins",
        "Losses": "Home Losses",
        "Ties": "Home Ties",
        "Win %": "Home Win %",
        "PD/G": "Home PD/G",
    }
)

road_summary = road_summary.rename(
    columns={
        "Games": "Road Games",
        "Wins": "Road Wins",
        "Losses": "Road Losses",
        "Ties": "Road Ties",
        "Win %": "Road Win %",
        "PD/G": "Road PD/G",
    }
)


# ---------------------------------------------------------
# MERGE HOME + ROAD
# ---------------------------------------------------------

team_seasons = home_summary[
    [
        "season",
        "Team",
        "Home Games",
        "Home Wins",
        "Home Losses",
        "Home Ties",
        "Home Win %",
        "Home PD/G",
    ]
].merge(
    road_summary[
        [
            "season",
            "Team",
            "Road Games",
            "Road Wins",
            "Road Losses",
            "Road Ties",
            "Road Win %",
            "Road PD/G",
        ]
    ],
    on=["season", "Team"],
    how="inner",
)


# ---------------------------------------------------------
# ROAD WARRIOR METRICS
# ---------------------------------------------------------

team_seasons["Road-Home Win % Gap"] = (
    team_seasons["Road Win %"]
    - team_seasons["Home Win %"]
)

team_seasons["Road-Home PD/G Gap"] = (
    team_seasons["Road PD/G"]
    - team_seasons["Home PD/G"]
)


# ---------------------------------------------------------
# RECORD DISPLAY
# ---------------------------------------------------------

def make_record(wins, losses, ties):

    if ties > 0:
        return f"{wins}-{losses}-{ties}"

    return f"{wins}-{losses}"


team_seasons["Home Record"] = team_seasons.apply(
    lambda row: make_record(
        row["Home Wins"],
        row["Home Losses"],
        row["Home Ties"],
    ),
    axis=1,
)

team_seasons["Road Record"] = team_seasons.apply(
    lambda row: make_record(
        row["Road Wins"],
        row["Road Losses"],
        row["Road Ties"],
    ),
    axis=1,
)


# ---------------------------------------------------------
# RANK ROAD WARRIORS
# ---------------------------------------------------------

road_warriors = team_seasons.sort_values(
    [
        "Road-Home Win % Gap",
        "Road-Home PD/G Gap",
    ],
    ascending=False,
).copy()

road_warriors["Rank"] = range(
    1,
    len(road_warriors) + 1,
)


# Round only for display
display = road_warriors.copy()

for column in [
    "Home Win %",
    "Road Win %",
    "Road-Home Win % Gap",
    "Home PD/G",
    "Road PD/G",
    "Road-Home PD/G Gap",
]:
    display[column] = display[column].round(1)


# ---------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------

print("\nGREATEST NFL ROAD WARRIORS")
print(f"Regular Seasons {START_SEASON}-{END_SEASON}")
print("=" * 125)

print(
    display[
        [
            "Rank",
            "season",
            "Team",
            "Home Record",
            "Road Record",
            "Home Win %",
            "Road Win %",
            "Road-Home Win % Gap",
            "Home PD/G",
            "Road PD/G",
            "Road-Home PD/G Gap",
        ]
    ]
    .head(25)
    .to_string(index=False)
)