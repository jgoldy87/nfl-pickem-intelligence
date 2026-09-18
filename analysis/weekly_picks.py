import os

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

from analysis.nfl_results import (
    fetch_week_results,
)


load_dotenv()

def get_api_key():

    # Local development
    api_key = os.getenv(
        "ODDS_API_KEY"
    )

    if api_key:
        return api_key

    # Streamlit Community Cloud
    try:
        api_key = st.secrets[
            "ODDS_API_KEY"
        ]

        if api_key:
            return api_key

    except (KeyError, FileNotFoundError):
        pass

    raise ValueError(
        "ODDS_API_KEY was not found."
    )

API_KEY = get_api_key()

def get_nfl_odds(
    commence_time_from,
    commence_time_to,
):
    url = (
        "https://api.the-odds-api.com/v4/"
        "sports/americanfootball_nfl/odds"
    )

    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "american",
        "commenceTimeFrom": commence_time_from,
        "commenceTimeTo": commence_time_to,
    }

    response = requests.get(
        url,
        params=params,
        timeout=20,
    )

    response.raise_for_status()

    return response.json()

def get_week_odds_window(
    season,
    week,
):
    schedule = fetch_week_results(
        season=season,
        week=week,
    )

    if schedule.empty:
        raise ValueError(
            f"No NFL schedule found for "
            f"{season} Week {week}."
        )

    game_dates = pd.to_datetime(
        schedule["gameday"]
    )

    first_date = game_dates.min()
    last_date = game_dates.max()

    commence_time_from = (
        first_date.strftime(
            "%Y-%m-%dT00:00:00Z"
        )
    )

    commence_time_to = (
        (
            last_date
            + pd.Timedelta(days=1)
        ).strftime(
            "%Y-%m-%dT06:00:00Z"
        )
    )

    return (
        commence_time_from,
        commence_time_to,
    )

def get_week_nfl_odds(
    season,
    week,
):
    (
        commence_time_from,
        commence_time_to,
    ) = get_week_odds_window(
        season=season,
        week=week,
    )

    return get_nfl_odds(
        commence_time_from=(
            commence_time_from
        ),
        commence_time_to=(
            commence_time_to
        ),
    )

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

def summarize_pick_profile(weekly_picks):
    summary = {
        "home_picks": 0,
        "away_picks": 0,
        "favorite_picks": 0,
        "underdog_picks": 0,
        "pickem_picks": 0,
    }

    for item in weekly_picks:
        game = item["game"]
        pick = item["pick"]

        away_team = game["away_team"]
        home_team = game["home_team"]

        # Home vs. away
        if pick == home_team:
            summary["home_picks"] += 1
        elif pick == away_team:
            summary["away_picks"] += 1

        # Favorite vs. underdog
        away_probability, home_probability = (
            get_consensus_probabilities(game)
        )

        # Skip market classification if odds are unavailable.
        if (
            away_probability is None
            or home_probability is None
        ):
            continue

        if away_probability > home_probability:
            favorite = away_team
            underdog = home_team
        elif home_probability > away_probability:
            favorite = home_team
            underdog = away_team
        else:
            summary["pickem_picks"] += 1
            continue

        if pick == favorite:
            summary["favorite_picks"] += 1
        elif pick == underdog:
            summary["underdog_picks"] += 1

    return summary

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