
import nflreadpy as nfl
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

SEASONS = list(range(2021, 2027))
REGULAR_SEASON_ONLY = True

PROBABILITY_BINS = [0.50, 0.55, 0.60, 0.65, 0.70,
                    0.75, 0.80, 0.85, 0.90, 1.01]


# Weekly Pick'em export
WEEKLY_ODDS_CSV = "2026-10-14T09-21_export.csv"



# ============================================================
# DATA LOADING
# ============================================================

def load_games():
    print("Loading historical NFL schedules...")

    games = nfl.load_schedules(SEASONS).to_pandas()

    if REGULAR_SEASON_ONLY:
        games = games[games["game_type"] == "REG"].copy()

    required = [
        "home_score", "away_score",
        "home_moneyline", "away_moneyline"
    ]

    for column in required:
        games[column] = pd.to_numeric(
            games[column], errors="coerce"
        )

    # Only completed games with valid moneylines
    games = games.dropna(subset=required).copy()

    # Exclude ties
    games = games[
        games["home_score"] != games["away_score"]
    ].copy()

    # American moneylines must be <= -100 or >= +100
    valid_home = (
        (games["home_moneyline"] <= -100)
        | (games["home_moneyline"] >= 100)
    )
    valid_away = (
        (games["away_moneyline"] <= -100)
        | (games["away_moneyline"] >= 100)
    )

    games = games[valid_home & valid_away].copy()

    return games


# ============================================================
# MARKET PROBABILITIES
# ============================================================

def implied_probability(odds):
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    return 100 / (odds + 100)


def prepare_upset_data(games):
    games = games.copy()

    home_raw = games["home_moneyline"].apply(
        implied_probability
    )
    away_raw = games["away_moneyline"].apply(
        implied_probability
    )

    total = home_raw + away_raw

    games["home_probability"] = home_raw / total
    games["away_probability"] = away_raw / total

    # Exclude games with no clear market favorite
    games = games[
        games["home_probability"]
        != games["away_probability"]
    ].copy()

    games["favorite"] = games.apply(
        lambda row: (
            row["home_team"]
            if row["home_probability"] > row["away_probability"]
            else row["away_team"]
        ),
        axis=1
    )

    games["favorite_probability"] = games[
        ["home_probability", "away_probability"]
    ].max(axis=1)

    games["winner"] = games.apply(
        lambda row: (
            row["home_team"]
            if row["home_score"] > row["away_score"]
            else row["away_team"]
        ),
        axis=1
    )

    games["upset"] = (
        games["winner"] != games["favorite"]
    )

    return games


# ============================================================
# ANALYSIS
# ============================================================

def season_summary(games):
    summary = (
        games.groupby("season")
        .agg(
            Games=("upset", "size"),
            Upsets=("upset", "sum"),
            Upset_Rate=("upset", "mean")
        )
        .reset_index()
    )

    summary["Upset_Rate"] = (
        summary["Upset_Rate"] * 100
    ).round(1)

    return summary


def probability_summary(games):
    games = games.copy()

    games["Probability_Band"] = pd.cut(
        games["favorite_probability"],
        bins=PROBABILITY_BINS,
        right=False,
        include_lowest=True
    )

    summary = (
        games.groupby(
            "Probability_Band",
            observed=True
        )
        .agg(
            Games=("upset", "size"),
            Upsets=("upset", "sum"),
            Upset_Rate=("upset", "mean"),
            Expected_Upset_Rate=(
                "favorite_probability",
                lambda p: (1 - p).mean()
            )
        )
        .reset_index()
    )

    for column in ["Upset_Rate", "Expected_Upset_Rate"]:
        summary[column] = (
            summary[column] * 100
        ).round(1)

    return summary


def weekly_summary(games):
    summary = (
        games.groupby(["season", "week"])
        .agg(
            Games=("upset", "size"),
            Upsets=("upset", "sum")
        )
        .reset_index()
    )

    summary["Upset_Rate"] = (
        summary["Upsets"] / summary["Games"] * 100
    ).round(1)

    return summary


def load_weekly_odds(csv_path):
    """Load a Pick'em export and identify market favorites."""

    weekly = pd.read_csv(csv_path)

    required = [
        "Game",
        "Your Pick",
        "Market Probability",
    ]

    missing = [
        col for col in required
        if col not in weekly.columns
    ]

    if missing:
        raise ValueError(
            f"Missing CSV columns: {missing}"
        )

    weekly["Market Probability"] = pd.to_numeric(
        weekly["Market Probability"]
            .astype(str)
            .str.replace("%", "", regex=False),
        errors="coerce"
    ) / 100

    if weekly["Market Probability"].isna().any():
        raise ValueError(
            "Some market probabilities are missing or invalid."
        )

    if not weekly["Market Probability"].between(0, 1).all():
        raise ValueError(
            "Market probabilities must be between 0% and 100%."
        )

    if weekly["Game"].duplicated().any():
        raise ValueError("Duplicate games found in CSV.")

    # The export contains full team names:
    # "Away Team @ Home Team"
    teams = weekly["Game"].str.split(
        " @ ", n=1, expand=True
    )

    if teams.shape[1] != 2:
        raise ValueError(
            "Expected game format: Away Team @ Home Team"
        )

    weekly["Away"] = teams[0].str.strip()
    weekly["Home"] = teams[1].str.strip()

    selected_home = weekly["Your Pick"].eq(
        weekly["Home"]
    )
    selected_away = weekly["Your Pick"].eq(
        weekly["Away"]
    )

    if not (selected_home | selected_away).all():
        raise ValueError(
            "A selected team does not match its game."
        )

    # The CSV probability belongs to Your Pick,
    # not necessarily to the favorite.
    weekly["Favorite"] = weekly["Your Pick"].where(
        weekly["Market Probability"] >= 0.5,
        weekly["Home"].where(
            selected_away,
            weekly["Away"]
        )
    )

    weekly["Underdog"] = weekly["Home"].where(
        weekly["Favorite"].eq(weekly["Away"]),
        weekly["Away"]
    )

    weekly["Favorite_Probability"] = weekly[
        "Market Probability"
    ].where(
        weekly["Market Probability"] >= 0.5,
        1 - weekly["Market Probability"]
    )

    weekly["Expected_Upsets"] = (
        1 - weekly["Favorite_Probability"]
    )

    weekly["Probability_Band"] = pd.cut(
        weekly["Favorite_Probability"],
        bins=PROBABILITY_BINS,
        right=False,
        include_lowest=True
    )

    return weekly


def weekly_upset_allocation(historical, weekly):
    """Compare weekly games with historical upset rates."""

    history = probability_summary(historical)

    allocation = (
        weekly.groupby(
            "Probability_Band",
            observed=True
        )
        .agg(
            Games=("Game", "size"),
            Market_Expected_Upsets=(
                "Expected_Upsets", "sum"
            )
        )
        .reset_index()
    )

    allocation = allocation.merge(
        history[
            ["Probability_Band", "Games", "Upset_Rate"]
        ].rename(
            columns={"Games": "Historical_Games"}
        ),
        on="Probability_Band",
        how="left"
    )

    allocation["Historical_Expected_Upsets"] = (
        allocation["Games"]
        * allocation["Upset_Rate"] / 100
    )

    return allocation


def print_weekly_allocation(historical):
    weekly = load_weekly_odds(WEEKLY_ODDS_CSV)

    allocation = weekly_upset_allocation(
        historical, weekly
    )

    print("\n" + "=" * 80)
    print("WEEKLY UPSET ALLOCATION REPORT")
    print("=" * 80)

    display = allocation.copy()

    for column in [
        "Market_Expected_Upsets",
        "Historical_Expected_Upsets",
    ]:
        display[column] = display[column].round(2)

    print("\nEXPECTED UPSETS BY PROBABILITY BAND")
    print("-" * 80)
    print(display.to_string(index=False))

    print("\nWEEKLY GAMES BY PROBABILITY BAND")
    print("-" * 80)

    weekly = weekly.sort_values(
        "Favorite_Probability"
    )

    for band, group in weekly.groupby(
        "Probability_Band",
        observed=True
    ):
        print(f"\n{band}")

        for _, row in group.iterrows():
            print(
                f"  {row['Game']}\n"
                f"    Favorite: {row['Favorite']} "
                f"({row['Favorite_Probability']:.1%})\n"
                f"    Underdog: {row['Underdog']}"
            )

    print("\n" + "-" * 80)
    print(
        "Total games:",
        len(weekly)
    )
    print(
        "Expected upsets (market):",
        round(weekly["Expected_Upsets"].sum(), 2)
    )
    print(
        "Expected upsets (historical bands):",
        round(
            allocation[
                "Historical_Expected_Upsets"
            ].sum(), 2
        )
    )

    print(
        "\nNote: Expected upsets are not "
        "recommended underdog pick counts."
    )


def main():
    games = load_games()
    games = prepare_upset_data(games)

    if games.empty:
        raise ValueError(
            "No completed games with valid odds were found."
        )

    print("\n" + "=" * 65)
    print("NFL UPSET ANALYSIS")
    print("=" * 65)

    print(f"Seasons: {SEASONS[0]}–{SEASONS[-1]}")
    print(f"Games analyzed: {len(games)}")
    print(f"Total upsets: {games['upset'].sum()}")
    print(
        f"Overall upset rate: "
        f"{games['upset'].mean() * 100:.1f}%"
    )

    print("\nUPSET RATE BY SEASON")
    print("-" * 65)
    print(season_summary(games).to_string(index=False))

    print("\nUPSET RATE BY FAVORITE PROBABILITY")
    print("-" * 65)
    print(
        probability_summary(games).to_string(index=False)
    )

    weekly = weekly_summary(games)

    print("\nWEEKLY UPSET FREQUENCY")
    print("-" * 65)

    print(
        weekly["Upsets"]
        .value_counts()
        .sort_index()
        .rename_axis("Upsets_Per_Week")
        .reset_index(name="Number_Of_Weeks")
        .to_string(index=False)
    )

    print(
        f"\nAverage upsets per week: "
        f"{weekly['Upsets'].mean():.2f}"
    )

    print(
        f"Median upsets per week: "
        f"{weekly['Upsets'].median():.1f}"
    )

    # Save results for future analysis
    games.to_csv(
        "upset_game_data.csv",
        index=False
    )

    print("\nSaved: upset_game_data.csv")

    print_weekly_allocation(games)


if __name__ == "__main__":
    main()
