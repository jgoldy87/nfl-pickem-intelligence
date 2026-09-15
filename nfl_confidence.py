import os

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ODDS_API_KEY")

if not API_KEY:
    raise ValueError("ODDS_API_KEY was not found in your .env file.")

def get_nfl_odds():
    url = (
        "https://api.the-odds-api.com/v4/"
        "sports/americanfootball_nfl/odds"
    )

    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "american",
        "commenceTimeFrom": "2026-09-09T00:00:00Z",
        "commenceTimeTo": "2026-09-15T23:59:59Z",
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    return response.json()

def implied_probability(odds):
    """
    Convert American moneyline odds to implied probability.
    """
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)

    return 100 / (odds + 100)


def no_vig_probabilities(team_a_odds, team_b_odds):
    """
    Convert both moneylines to implied probabilities
    and normalize them so they sum to 100%.
    """
    prob_a = implied_probability(team_a_odds)
    prob_b = implied_probability(team_b_odds)

    total = prob_a + prob_b

    return prob_a / total, prob_b / total


def get_consensus_probabilities(game):
    away_team = game["away_team"]
    home_team = game["home_team"]

    away_probabilities = []
    home_probabilities = []

    for bookmaker in game["bookmakers"]:
        for market in bookmaker["markets"]:

            if market["key"] != "h2h":
                continue

            odds = {
                outcome["name"]: outcome["price"]
                for outcome in market["outcomes"]
            }

            if away_team not in odds or home_team not in odds:
                continue

            away_prob, home_prob = no_vig_probabilities(
                odds[away_team],
                odds[home_team]
            )

            away_probabilities.append(away_prob)
            home_probabilities.append(home_prob)

    if not away_probabilities:
        return None, None

    away_consensus = (
        sum(away_probabilities) /
        len(away_probabilities)
    )

    home_consensus = (
        sum(home_probabilities) /
        len(home_probabilities)
    )

    return away_consensus, home_consensus

def confidence_tier(probability):
    """
    Add a descriptive label to each pick.
    """
    if probability >= 0.75:
        return "Very High"
    elif probability >= 0.65:
        return "High"
    elif probability >= 0.55:
        return "Moderate"
    elif probability >= 0.45:
        return "Toss-up"
    elif probability >= 0.35:
        return "Risky"
    else:
        return "Major Upset"


def compare_confidence(user_confidence, recommended_confidence):
    difference = user_confidence - recommended_confidence

    if difference == 0:
        return "Matches market"

    if difference > 0:
        return f"You rank this {difference} higher"

    return f"You rank this {abs(difference)} lower"

def enter_picks(api_games):
    picks = []

    print("\nEnter your predicted winner for each game.")
    print("Type A for the away team or H for the home team.\n")

    for game in api_games:
        away_team = game["away_team"]
        home_team = game["home_team"]

        print(f"{away_team} @ {home_team}")

        while True:
            choice = input(
                f"A = {away_team} | H = {home_team}: "
            ).strip().upper()

            if choice == "A":
                pick = away_team
                break

            if choice == "H":
                pick = home_team
                break

            print("Please enter A or H.")

        picks.append({
            "game": game,
            "pick": pick
        })

        print()

    return picks

def enter_confidence_order(picks):
    print("\nNow rank your picks from MOST confident to LEAST confident.")
    print("Enter the numbers separated by commas.\n")

    for index, item in enumerate(picks, start=1):
        print(f"{index}. {item['pick']}")

    number_of_picks = len(picks)

    while True:
        raw_order = input(
            f"\nEnter all {number_of_picks} numbers in order: "
        ).strip()

        try:
            order = [
                int(value.strip())
                for value in raw_order.split(",")
            ]
        except ValueError:
            print("Please enter numbers separated by commas.")
            continue

        expected = set(range(1, number_of_picks + 1))

        if len(order) != number_of_picks or set(order) != expected:
            print(
                f"Please use every number from 1 to "
                f"{number_of_picks} exactly once."
            )
            continue

        break

    # First choice gets the highest confidence value.
    confidence = number_of_picks

    for pick_number in order:
        picks[pick_number - 1]["user_confidence"] = confidence
        confidence -= 1

    return picks

def rank_picks(games):
    """
    Rank the user's picks according to no-vig
    market-implied win probability.
    """
    results = []

    for game in games:

        team_a_prob, team_b_prob = no_vig_probabilities(
            game["team_a_odds"],
            game["team_b_odds"]
        )

        if game["pick"] == game["team_a"]:
            pick_probability = team_a_prob
        elif game["pick"] == game["team_b"]:
            pick_probability = team_b_prob
        else:
            raise ValueError(
                f'{game["pick"]} is not part of '
                f'{game["team_a"]} vs {game["team_b"]}'
            )

        results.append({
            "Game": f'{game["team_a"]} vs {game["team_b"]}',
            "Your Pick": game["pick"],
            "Market Probability": pick_probability,
            "Tier": confidence_tier(pick_probability),
            "Your Confidence": game["user_confidence"]
        })

    df = pd.DataFrame(results)

    df = df.sort_values(
        "Market Probability",
        ascending=False
    ).reset_index(drop=True)

    number_of_games = len(df)

    df["Recommended Confidence"] = range(
        number_of_games,
        0,
        -1
    )

    df["Difference"] = (
        df["Your Confidence"] - df["Recommended Confidence"]
    )

    df["Comparison"] = df.apply(
        lambda row: compare_confidence(
            row["Your Confidence"],
            row["Recommended Confidence"]
        ),
        axis=1
    )

    df["Market Probability"] = (
        df["Market Probability"] * 100
    ).round(1)

    return df

def rank_live_picks(picks):
    results = []

    for item in picks:
        game = item["game"]
        pick = item["pick"]

        away_team = game["away_team"]
        home_team = game["home_team"]

        away_prob, home_prob = get_consensus_probabilities(game)

        if away_prob is None:
            continue

        if pick == away_team:
            pick_probability = away_prob
        else:
            pick_probability = home_prob

        results.append({
            "Game": f"{away_team} @ {home_team}",
            "Your Pick": pick,
            "Market Probability": pick_probability,
            "Tier": confidence_tier(pick_probability),
            "Sportsbooks": len(game["bookmakers"]),
            "Your Confidence": item["user_confidence"]
        })

    df = pd.DataFrame(results)

    df = df.sort_values(
        "Market Probability",
        ascending=False
    ).reset_index(drop=True)

    number_of_games = len(df)

    df["Recommended Confidence"] = range(
        number_of_games,
        0,
        -1
    )

    df["Difference"] = (
        df["Your Confidence"] -
        df["Recommended Confidence"]
    )

    df["Comparison"] = df.apply(
        lambda row: compare_confidence(
            row["Your Confidence"],
            row["Recommended Confidence"]
        ),
        axis=1
    )


    df["Market Probability"] = (
        df["Market Probability"] * 100
    ).round(1)

    return df

api_games = get_nfl_odds()

picks = enter_picks(api_games)
picks = enter_confidence_order(picks)

rankings = rank_live_picks(picks)

print("\nMARKET-BASED CONFIDENCE RANKINGS\n")

print(rankings.to_string(index=False))


# games = [
#     {
#         "team_a": "BUF",
#         "team_b": "NYJ",
#         "team_a_odds": -300,
#         "team_b_odds": 250,
#         "pick": "BUF",
#         "user_confidence": 4
#     },
#     {
#         "team_a": "KC",
#         "team_b": "LV",
#         "team_a_odds": -220,
#         "team_b_odds": 185,
#         "pick": "KC",
#         "user_confidence": 2
#     },
#     {
#         "team_a": "DAL",
#         "team_b": "PHI",
#         "team_a_odds": 110,
#         "team_b_odds": -130,
#         "pick": "DAL",
#         "user_confidence": 1
#     },
#     {
#         "team_a": "CLE",
#         "team_b": "PIT",
#         "team_a_odds": 180,
#         "team_b_odds": -215,
#         "pick": "CLE",
#         "user_confidence": 3
#     }
# ]


# rankings = rank_picks(games)

# print(rankings.to_string(index=False))