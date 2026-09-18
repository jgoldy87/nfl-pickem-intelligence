import nflreadpy as nfl
import pandas as pd


SEASON = 2026
WEEK = 1


def implied_probability(moneyline):
    """Convert American moneyline to implied probability."""

    if moneyline < 0:
        return abs(moneyline) / (
            abs(moneyline) + 100
        )

    return 100 / (moneyline + 100)


def calculate_no_vig_probabilities(
    away_moneyline,
    home_moneyline,
):
    """Calculate no-vig probabilities for both teams."""

    away_implied = implied_probability(
        away_moneyline
    )

    home_implied = implied_probability(
        home_moneyline
    )

    total = away_implied + home_implied

    away_probability = away_implied / total
    home_probability = home_implied / total

    return (
        away_probability,
        home_probability,
    )


schedule = nfl.load_schedules(
    seasons=[SEASON]
).to_pandas()


week_games = schedule[
    schedule["week"] == WEEK
].copy()


results = []

for _, game in week_games.iterrows():

    away_team = game["away_team"]
    home_team = game["home_team"]

    away_score = game["away_score"]
    home_score = game["home_score"]

    away_moneyline = game["away_moneyline"]
    home_moneyline = game["home_moneyline"]

    if pd.isna(away_moneyline) or pd.isna(
        home_moneyline
    ):
        continue

    (
        away_probability,
        home_probability,
    ) = calculate_no_vig_probabilities(
        away_moneyline,
        home_moneyline,
    )

    if away_probability > home_probability:
        market_pick = away_team
        market_probability = away_probability
    else:
        market_pick = home_team
        market_probability = home_probability

    if away_score > home_score:
        winner = away_team
    elif home_score > away_score:
        winner = home_team
    else:
        winner = "TIE"

    market_correct = market_pick == winner

    results.append(
        {
            "Game": (
                f"{away_team} @ {home_team}"
            ),
            "Away ML": away_moneyline,
            "Home ML": home_moneyline,
            "Market Pick": market_pick,
            "Market Probability": round(
                market_probability * 100,
                1,
            ),
            "Winner": winner,
            "Correct": market_correct,
        }
    )


results_df = pd.DataFrame(results)


print("\nMARKET PERFORMANCE")
print("-" * 80)

print(
    results_df.to_string(
        index=False
    )
)


correct_picks = (
    results_df["Correct"].sum()
)

total_games = len(results_df)

accuracy = (
    correct_picks / total_games * 100
)


print("\nMARKET SUMMARY")
print("-" * 80)

print(
    f"Record: "
    f"{correct_picks}-"
    f"{total_games - correct_picks}"
)

print(
    f"Accuracy: {accuracy:.1f}%"
)