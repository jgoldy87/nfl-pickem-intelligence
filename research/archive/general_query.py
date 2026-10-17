
import pandas as pd
import nflreadpy as nfl

# ============================================================
# CONFIGURATION
# ============================================================

SEASON = 2026
WEEK = 6

ANALYSIS_MODE = "weekly"  # "weekly" or "single"

AWAY_TEAM = "HOU"
HOME_TEAM = "JAX"

TOP_N = 10

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", None)


# ============================================================
# DATA PREPARATION
# ============================================================

def load_data(season, week):
    schedule = nfl.load_schedules([season]).to_pandas()

    weekly_games = schedule[
        (schedule["game_type"] == "REG")
        & (schedule["week"] == week)
    ].copy()

    if weekly_games.empty:
        raise ValueError(f"No regular-season games found for Week {week}.")

    prior_games = schedule[
        (schedule["game_type"] == "REG")
        & (schedule["week"] < week)
        & schedule["home_score"].notna()
        & schedule["away_score"].notna()
    ].copy()

    if prior_games.empty:
        raise ValueError(
            "No completed games before the selected week. "
            "Week 1 requires a separate preseason baseline."
        )

    pbp = nfl.load_pbp([season]).to_pandas()

    pbp = pbp[
        (pbp["season_type"] == "REG")
        & pbp["game_id"].isin(prior_games["game_id"])
    ].copy()

    return weekly_games, prior_games, pbp


def build_team_stats(prior_games, pbp):

    home_scores = pd.DataFrame({
        "Team": prior_games["home_team"],
        "Points": prior_games["home_score"],
        "Points_Allowed": prior_games["away_score"],
    })

    away_scores = pd.DataFrame({
        "Team": prior_games["away_team"],
        "Points": prior_games["away_score"],
        "Points_Allowed": prior_games["home_score"],
    })

    team_scores = pd.concat(
        [home_scores, away_scores],
        ignore_index=True
    )

    scoring = team_scores.groupby("Team").agg(
        Games=("Points", "size"),
        Points=("Points", "sum"),
        Points_Allowed=("Points_Allowed", "sum"),
    )

    scoring["PPG"] = scoring["Points"] / scoring["Games"]
    scoring["Points_Allowed_PG"] = (
        scoring["Points_Allowed"] / scoring["Games"]
    )

    plays = pbp[
        pbp["posteam"].notna()
        & pbp["defteam"].notna()
        & pbp["yards_gained"].notna()
    ].copy()

    plays["Category"] = "Other"

    plays.loc[
        plays["play_type"] == "pass", "Category"
    ] = "Pass"

    plays.loc[
        plays["play_type"] == "run", "Category"
    ] = "Rush"

    plays.loc[
        plays["sack"] == 1, "Category"
    ] = "Pass"

    plays = plays[
        plays["Category"].isin(["Pass", "Rush"])
    ].copy()

    offense = (
        plays.groupby(["posteam", "Category"])
        .agg(
            Plays=("yards_gained", "size"),
            Yards=("yards_gained", "sum"),
        )
        .unstack("Category", fill_value=0)
    )

    offense.columns = [
        f"{category}_{stat}"
        for stat, category in offense.columns
    ]
    offense.index.name = "Team"

    defense = (
        plays.groupby(["defteam", "Category"])
        .agg(
            Plays=("yards_gained", "size"),
            Yards=("yards_gained", "sum"),
        )
        .unstack("Category", fill_value=0)
    )

    defense.columns = [
        f"{category}_{stat}_Allowed"
        for stat, category in defense.columns
    ]
    defense.index.name = "Team"

    stats = scoring.join(offense).join(defense).fillna(0)

    stats["Off_YPG"] = (
        stats["Pass_Yards"] + stats["Rush_Yards"]
    ) / stats["Games"]

    stats["Def_YPG"] = (
        stats["Pass_Yards_Allowed"]
        + stats["Rush_Yards_Allowed"]
    ) / stats["Games"]

    stats["Off_YPP"] = (
        (stats["Pass_Yards"] + stats["Rush_Yards"])
        / (stats["Pass_Plays"] + stats["Rush_Plays"])
    )

    stats["Def_YPP"] = (
        (stats["Pass_Yards_Allowed"] + stats["Rush_Yards_Allowed"])
        / (stats["Pass_Plays_Allowed"] + stats["Rush_Plays_Allowed"])
    )

    stats["Pass_YPG"] = stats["Pass_Yards"] / stats["Games"]
    stats["Rush_YPG"] = stats["Rush_Yards"] / stats["Games"]

    stats["Pass_Allowed_PG"] = (
        stats["Pass_Yards_Allowed"] / stats["Games"]
    )

    stats["Rush_Allowed_PG"] = (
        stats["Rush_Yards_Allowed"] / stats["Games"]
    )

    stats["Pass_YPP"] = (
        stats["Pass_Yards"] / stats["Pass_Plays"]
    )

    stats["Rush_YPA"] = (
        stats["Rush_Yards"] / stats["Rush_Plays"]
    )

    stats["Pass_Allowed_YPP"] = (
        stats["Pass_Yards_Allowed"]
        / stats["Pass_Plays_Allowed"]
    )

    stats["Rush_Allowed_YPA"] = (
        stats["Rush_Yards_Allowed"]
        / stats["Rush_Plays_Allowed"]
    )

    offensive_metrics = [
        "PPG", "Off_YPG", "Off_YPP",
        "Pass_YPG", "Pass_YPP",
        "Rush_YPG", "Rush_YPA",
    ]

    defensive_metrics = [
        "Points_Allowed_PG", "Def_YPG", "Def_YPP",
        "Pass_Allowed_PG", "Pass_Allowed_YPP",
        "Rush_Allowed_PG", "Rush_Allowed_YPA",
    ]

    for metric in offensive_metrics:
        stats[f"{metric}_Rank"] = (
            stats[metric]
            .rank(ascending=False, method="min")
            .astype(int)
        )

    for metric in defensive_metrics:
        stats[f"{metric}_Rank"] = (
            stats[metric]
            .rank(ascending=True, method="min")
            .astype(int)
        )

    league_averages = {
        "Passing": (
            stats["Pass_Yards"].sum()
            / stats["Pass_Plays"].sum()
        ),
        "Rushing": (
            stats["Rush_Yards"].sum()
            / stats["Rush_Plays"].sum()
        ),
        "Overall": (
            (stats["Pass_Yards"].sum() + stats["Rush_Yards"].sum())
            / (stats["Pass_Plays"].sum() + stats["Rush_Plays"].sum())
        ),
    }

    return stats, league_averages


# ============================================================
# MATCHUP ADVANTAGE CALCULATIONS
# ============================================================

METRIC_DEFINITIONS = [
    ("Passing", "Pass_YPP", "Pass_Allowed_YPP"),
    ("Rushing", "Rush_YPA", "Rush_Allowed_YPA"),
    ("Overall", "Off_YPP", "Def_YPP"),
]


def classify_advantage(value):
    if value >= 15:
        return "Strong offense advantage"
    elif value >= 5:
        return "Moderate offense advantage"
    elif value > -5:
        return "Relatively balanced"
    elif value > -15:
        return "Moderate defense advantage"
    else:
        return "Strong defense advantage"


def calculate_matchup_advantage(
    stats,
    league_averages,
    offense_team,
    defense_team,
    category,
    offense_metric,
    defense_metric,
):
    league_average = league_averages[category]

    offensive_value = stats.loc[offense_team, offense_metric]
    defensive_value = stats.loc[defense_team, defense_metric]

    offense_vs_league = (
        offensive_value / league_average - 1
    ) * 100

    defense_vs_league = (
        defensive_value / league_average - 1
    ) * 100

    advantage = offense_vs_league + defense_vs_league

    return {
        "Offense": offense_team,
        "Defense": defense_team,
        "Category": category,
        "Offense_vs_League": offense_vs_league,
        "Defense_vs_League": defense_vs_league,
        "Advantage": advantage,
        "Assessment": classify_advantage(advantage),
    }


def build_matchup_advantages(
    games,
    stats,
    league_averages,
    include_overall=True,
):
    results = []

    definitions = [
        definition
        for definition in METRIC_DEFINITIONS
        if include_overall or definition[0] != "Overall"
    ]

    for _, game in games.iterrows():
        away = game["away_team"]
        home = game["home_team"]

        for offense_team, defense_team in [
            (away, home),
            (home, away),
        ]:
            for category, off_metric, def_metric in definitions:
                result = calculate_matchup_advantage(
                    stats,
                    league_averages,
                    offense_team,
                    defense_team,
                    category,
                    off_metric,
                    def_metric,
                )

                result["Game"] = f"{away} @ {home}"
                results.append(result)

    advantages = pd.DataFrame(results)
    advantages["Magnitude"] = advantages["Advantage"].abs()

    return advantages


# ============================================================
# OUTPUT HELPERS
# ============================================================

def print_advantage_table(title, dataframe):
    print(f"\n{title}")
    print("=" * 115)

    if dataframe.empty:
        print("No results.")
        return

    columns = [
        "Game",
        "Offense",
        "Defense",
        "Category",
        "Offense_vs_League",
        "Defense_vs_League",
        "Advantage",
        "Assessment",
    ]

    display = dataframe[columns].copy()

    for column in [
        "Offense_vs_League",
        "Defense_vs_League",
        "Advantage",
    ]:
        display[column] = display[column].map(
            lambda value: f"{value:+.1f}%"
        )

    print(display.to_string(index=False))


def print_league_averages(league_averages):
    print("\nLEAGUE-AVERAGE EFFICIENCY")
    print("=" * 70)

    for category, value in league_averages.items():
        print(f"{category:<12}: {value:.2f}")


def print_comparison(stats, offense_team, defense_team):
    rows = [
        ("Points/Game", "PPG", "Points_Allowed_PG"),
        ("Total Yards/Game", "Off_YPG", "Def_YPG"),
        ("Yards/Play", "Off_YPP", "Def_YPP"),
        ("Pass Yards/Game", "Pass_YPG", "Pass_Allowed_PG"),
        ("Net Pass Yards/Play", "Pass_YPP", "Pass_Allowed_YPP"),
        ("Rush Yards/Game", "Rush_YPG", "Rush_Allowed_PG"),
        ("Rush Yards/Attempt", "Rush_YPA", "Rush_Allowed_YPA"),
    ]

    print(f"\n{offense_team} OFFENSE vs {defense_team} DEFENSE")
    print("=" * 90)

    print(
        f"{'METRIC':<27}"
        f"{offense_team + ' OFFENSE':>27}"
        f"{defense_team + ' DEFENSE':>27}"
    )
    print("-" * 90)

    for label, off_metric, def_metric in rows:
        off_value = stats.loc[offense_team, off_metric]
        def_value = stats.loc[defense_team, def_metric]

        off_rank = stats.loc[
            offense_team, f"{off_metric}_Rank"
        ]
        def_rank = stats.loc[
            defense_team, f"{def_metric}_Rank"
        ]

        print(
            f"{label:<27}"
            f"{off_value:>17.2f} (#{off_rank:<2})"
            f"{def_value:>17.2f} (#{def_rank:<2})"
        )


# ============================================================
# SINGLE-GAME ANALYSIS
# ============================================================

def run_single_analysis(
    weekly_games,
    stats,
    league_averages,
):
    selected = weekly_games[
        (weekly_games["away_team"] == AWAY_TEAM)
        & (weekly_games["home_team"] == HOME_TEAM)
    ].copy()

    if len(selected) != 1:
        raise ValueError(
            f"Expected one {AWAY_TEAM} @ {HOME_TEAM} "
            f"game in Week {WEEK}; found {len(selected)}."
        )

    print(f"\n{SEASON} WEEK {WEEK}: {AWAY_TEAM} @ {HOME_TEAM}")
    print("=" * 90)

    print_comparison(stats, AWAY_TEAM, HOME_TEAM)
    print_comparison(stats, HOME_TEAM, AWAY_TEAM)

    print_league_averages(league_averages)

    advantages = build_matchup_advantages(
        selected,
        stats,
        league_averages,
        include_overall=True,
    )

    print_advantage_table(
        "MATCHUP ADVANTAGES",
        advantages,
    )

    print_advantage_table(
        "LARGEST MATCHUP MISMATCHES",
        advantages.sort_values(
            "Magnitude",
            ascending=False,
        ),
    )


# ============================================================
# WEEKLY ANALYSIS
# ============================================================

def run_weekly_analysis(
    weekly_games,
    stats,
    league_averages,
):
    print(f"\n{SEASON} WEEK {WEEK} MATCHUP EXPLORER")
    print("=" * 100)

    weekly_games = weekly_games.sort_values(
        ["gameday", "gametime"]
    )

    print("\nWEEKLY SCHEDULE")
    print("-" * 100)

    print(
        weekly_games[
            ["away_team", "home_team", "gameday", "gametime"]
        ].to_string(index=False)
    )

    print_league_averages(league_averages)

    advantages = build_matchup_advantages(
        weekly_games,
        stats,
        league_averages,
        include_overall=False,
    )

    offensive = advantages[
        advantages["Advantage"] > 0
    ].sort_values("Advantage", ascending=False)

    defensive = advantages[
        advantages["Advantage"] < 0
    ].sort_values("Advantage", ascending=True)

    print_advantage_table(
        f"TOP {TOP_N} OFFENSIVE ADVANTAGES",
        offensive.head(TOP_N),
    )

    print_advantage_table(
        f"TOP {TOP_N} DEFENSIVE ADVANTAGES",
        defensive.head(TOP_N),
    )

    print_advantage_table(
        "ALL WEEKLY MATCHUPS — LARGEST FIRST",
        advantages.sort_values(
            "Magnitude",
            ascending=False,
        ),
    )

    expected = len(weekly_games) * 4

    print("\nWEEKLY VALIDATION")
    print("=" * 70)
    print("Scheduled games:", len(weekly_games))
    print("Expected comparisons:", expected)
    print("Actual comparisons:", len(advantages))
    print("Comparison count matches:", len(advantages) == expected)


# ============================================================
# MAIN
# ============================================================

def main():
    if ANALYSIS_MODE not in ("weekly", "single"):
        raise ValueError(
            "ANALYSIS_MODE must be 'weekly' or 'single'."
        )

    weekly_games, prior_games, pbp = load_data(
        SEASON,
        WEEK,
    )

    stats, league_averages = build_team_stats(
        prior_games,
        pbp,
    )

    print("\nDATA VALIDATION")
    print("=" * 70)
    print("Completed prior games:", len(prior_games))
    print("Teams ranked:", len(stats))
    print("Latest completed week:", prior_games["week"].max())

    off_yards = (
        stats["Pass_Yards"].sum()
        + stats["Rush_Yards"].sum()
    )
    def_yards = (
        stats["Pass_Yards_Allowed"].sum()
        + stats["Rush_Yards_Allowed"].sum()
    )

    print(
        "Offensive/defensive yards match:",
        off_yards == def_yards,
    )

    if ANALYSIS_MODE == "single":
        run_single_analysis(
            weekly_games,
            stats,
            league_averages,
        )
    else:
        run_weekly_analysis(
            weekly_games,
            stats,
            league_averages,
        )


if __name__ == "__main__":
    main()
