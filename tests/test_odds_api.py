import os
import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("ODDS_API_KEY")

if not API_KEY:
    raise ValueError("ODDS_API_KEY was not found in your .env file.")


url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"

params = {
    "apiKey": API_KEY,
    "regions": "us",
    "markets": "h2h",
    "oddsFormat": "american",
    "commenceTimeFrom": "2026-09-09T00:00:00Z",
    "commenceTimeTo": "2026-09-15T23:59:59Z",
}


response = requests.get(url, params=params, timeout=20)

response.raise_for_status()

games = response.json()

def implied_probability(odds):
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)

    return 100 / (odds + 100)


def no_vig_probabilities(odds_a, odds_b):
    prob_a = implied_probability(odds_a)
    prob_b = implied_probability(odds_b)

    total = prob_a + prob_b

    return prob_a / total, prob_b / total


for game in games:
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

    if away_probabilities and home_probabilities:
        away_consensus = (
            sum(away_probabilities) / len(away_probabilities)
        )

        home_consensus = (
            sum(home_probabilities) / len(home_probabilities)
        )

        print()
        print(f"{away_team} @ {home_team}")
        print(
            f"  {away_team}: {away_consensus:.1%}"
        )
        print(
            f"  {home_team}: {home_consensus:.1%}"
        )
        print(
            f"  Sportsbooks used: {len(away_probabilities)}"
        )