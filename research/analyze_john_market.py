"""Compare PLAYER's NFL confidence picks with historical market lines."""

import numpy as np
import pandas as pd

from analysis.database import load_picks
from analysis.market_performance import get_market_performance

PLAYER = "John"


def section(title, width=80):
    print(f"\n{title}\n" + "=" * width)


def main():
    picks = load_picks()
    player_picks = picks.loc[
        picks["player"].astype(str).str.strip().str.casefold() == PLAYER.casefold()
    ].copy()
    if player_picks.empty:
        print(f"No picks found for {PLAYER}.")
        return

    # A game ID such as 2026_01_ARI_LAC encodes the away and home teams.
    parts = player_picks["game_id"].astype(str).str.split("_", expand=True)
    if parts.shape[1] != 4:
        raise ValueError("Unexpected game_id format; expected season_week_away_home")
    player_picks["away_team"] = parts[2].values
    player_picks["home_team"] = parts[3].values
    player_picks["season"] = pd.to_numeric(player_picks["season"]).astype(int)
    player_picks["week"] = pd.to_numeric(player_picks["week"]).astype(int)
    player_picks["confidence"] = pd.to_numeric(player_picks["confidence"]).astype(int)

    markets = pd.concat(
        [get_market_performance(int(s)) for s in sorted(player_picks["season"].unique())],
        ignore_index=True,
    )
    markets["season"] = pd.to_numeric(markets["season"]).astype(int)
    markets["week"] = pd.to_numeric(markets["week"]).astype(int)
    merged = player_picks.merge(
        markets,
        on=["season", "week", "away_team", "home_team"],
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    unmatched = int(merged["_merge"].ne("both").sum())
    print(f"\n{PLAYER}'s picks: {len(player_picks)}")
    print(f"Unmatched games: {unmatched}")
    if unmatched:
        print("Unmatched game IDs:", merged.loc[merged["_merge"].ne("both"), "game_id"].tolist())
    merged = merged.loc[merged["_merge"].eq("both")].copy()
    if merged.empty:
        print("No market-matched picks to analyze.")
        return

    valid = merged["pick"].eq(merged["away_team"]) | merged["pick"].eq(merged["home_team"])
    if not valid.all():
        raise ValueError(f"Invalid team selections: {merged.loc[~valid, 'game_id'].tolist()}")
    if merged[["away_probability", "home_probability", "market_pick"]].isna().any().any():
        raise ValueError("Matched games contain missing market probabilities or market picks.")

    merged["selected_team_probability"] = np.where(
        merged["pick"].eq(merged["away_team"]),
        merged["away_probability"],
        merged["home_probability"],
    ).astype(float)
    merged["picked_favorite"] = merged["pick"].eq(merged["market_pick"])
    merged["is_tie"] = merged["winner"].eq("TIE")
    merged["pick_won"] = merged["pick"].eq(merged["winner"])

    # A true 50/50 market should not be classified as favorite or underdog.
    merged["is_tossup"] = np.isclose(merged["selected_team_probability"], 50.0, atol=0.05)
    merged["picked_underdog"] = (~merged["picked_favorite"]) & (~merged["is_tossup"])
    total = len(merged)
    favorites = int(merged["picked_favorite"].sum())
    underdogs = int(merged["picked_underdog"].sum())
    tossups = int(merged["is_tossup"].sum())

    section(f"{PLAYER.upper()} VS. THE MARKET")
    print(f"Games analyzed: {total}")
    print(f"Favorites picked: {favorites} ({favorites / total:.1%})")
    print(f"Underdogs picked: {underdogs} ({underdogs / total:.1%})")
    print(f"Toss-ups: {tossups}")

    section(f"{PLAYER.upper()}'S UNDERDOG PICKS")
    underdog_picks = merged.loc[merged["picked_underdog"]].copy()
    display_cols = ["season", "week", "game", "pick", "confidence", "selected_team_probability", "winner"]
    print(underdog_picks.sort_values(["season", "week", "confidence"])[display_cols].to_string(index=False))

    # Reallocate only the confidence slots actually used in each week.
    def rank_week(group):
        group = group.copy()
        slots = sorted(group["confidence"].tolist(), reverse=True)
        group = group.sort_values(["selected_team_probability", "game_id"], ascending=[False, True])
        group["market_confidence"] = slots
        return group

    ranked = pd.concat(
        [rank_week(group) for _, group in merged.groupby(["season", "week"])],
        ignore_index=True,
    )
    ranked["confidence_difference"] = ranked["confidence"] - ranked["market_confidence"]
    ranked["expected_points_actual"] = ranked["selected_team_probability"] / 100 * ranked["confidence"]
    ranked["expected_points_market"] = ranked["selected_team_probability"] / 100 * ranked["market_confidence"]
    ranked["expected_points_gap"] = ranked["expected_points_market"] - ranked["expected_points_actual"]

    weekly = ranked.groupby(["season", "week"]).agg(
        picks=("pick", "size"),
        total_adjustment=("confidence_difference", lambda s: s.abs().sum()),
        biggest_adjustment=("confidence_difference", lambda s: s.abs().max()),
        expected_actual=("expected_points_actual", "sum"),
        expected_market=("expected_points_market", "sum"),
    ).reset_index()
    weekly["expected_gap"] = weekly["expected_market"] - weekly["expected_actual"]
    section(f"{PLAYER.upper()}'S WEEKLY MARKET ALIGNMENT")
    print(weekly.round(2).to_string(index=False))
    section("OVERALL MARKET ALIGNMENT")
    print(f"Average absolute confidence adjustment: {ranked['confidence_difference'].abs().mean():.2f}")
    print(f"Exact market-ranking matches: {int(ranked['confidence_difference'].eq(0).sum())} of {len(ranked)}")
    print(f"Total expected points sacrificed: {ranked['expected_points_gap'].sum():.2f}")

    section(f"{PLAYER.upper()}'S BIGGEST MARKET DISAGREEMENTS", 105)
    columns = ["week", "game", "pick", "selected_team_probability", "confidence", "market_confidence", "confidence_difference", "winner"]
    biggest = ranked.assign(adjustment_size=ranked["confidence_difference"].abs()).sort_values(
        ["adjustment_size", "week"], ascending=[False, True]
    )
    print(biggest[columns].head(20).to_string(index=False))

    # No scoring assumptions for tied or unplayed games.
    completed = ranked.loc[ranked["winner"].notna() & ~ranked["is_tie"]].copy()
    completed["actual_points"] = completed["confidence"] * completed["pick_won"].astype(int)
    completed["market_ranked_points"] = completed["market_confidence"] * completed["pick_won"].astype(int)
    completed["points_difference"] = completed["actual_points"] - completed["market_ranked_points"]
    section(f"{PLAYER.upper()} VS. MARKET RANKINGS — ACTUAL RESULTS")
    if completed.empty:
        print("No completed non-tied games to score.")
    else:
        weekly_results = completed.groupby(["season", "week"]).agg(
            actual_points=("actual_points", "sum"),
            market_ranked_points=("market_ranked_points", "sum"),
            points_difference=("points_difference", "sum"),
        ).reset_index()
        print(weekly_results.to_string(index=False))
        section("OVERALL COMPARISON")
        actual_total = int(completed["actual_points"].sum())
        market_total = int(completed["market_ranked_points"].sum())
        print(f"{PLAYER}'s actual points: {actual_total}")
        print(f"Market-ranked points: {market_total}")
        print(f"{PLAYER}'s ranking advantage: {actual_total - market_total:+d}")
        columns = ["week", "game", "pick", "confidence", "market_confidence", "winner", "actual_points", "market_ranked_points", "points_difference"]
        section("MOST BENEFICIAL CONFIDENCE ADJUSTMENTS", 100)
        print(completed.sort_values("points_difference", ascending=False)[columns].head(10).to_string(index=False))
        section("MOST COSTLY CONFIDENCE ADJUSTMENTS", 100)
        print(completed.sort_values("points_difference")[columns].head(10).to_string(index=False))

    # Poisson-binomial distribution: each underdog has its own win probability.
    underdog_results = completed.loc[completed["picked_underdog"]].copy()
    probabilities = underdog_results["selected_team_probability"].to_numpy(dtype=float) / 100
    wins = int(underdog_results["pick_won"].sum())
    expected_wins = float(probabilities.sum())
    distribution = np.array([1.0])
    for p in probabilities:
        distribution = np.convolve(distribution, [1 - p, p])
    tail_probability = float(distribution[wins:].sum())
    std = float(np.sqrt(np.sum(probabilities * (1 - probabilities))))
    section(f"{PLAYER.upper()}'S UNDERDOG LUCK ANALYSIS")
    print(f"Underdog games evaluated: {len(underdog_results)}")
    print(f"Actual underdog wins: {wins}")
    print(f"Expected underdog wins: {expected_wins:.2f}")
    print(f"Wins above expectation: {wins - expected_wins:+.2f}")
    print(f"Standard deviation: {std:.2f}")
    if std:
        print(f"Standardized result: {(wins - expected_wins) / std:+.2f}")
    print(f"Probability of at least this many wins: {tail_probability:.2%}")
    actual_underdog_points = float((underdog_results["confidence"] * underdog_results["pick_won"]).sum())
    expected_underdog_points = float((underdog_results["confidence"] * underdog_results["selected_team_probability"] / 100).sum())
    section("UNDERDOG CONFIDENCE POINTS")
    print(f"Actual points: {actual_underdog_points:.2f}")
    print(f"Expected points: {expected_underdog_points:.2f}")
    print(f"Points above expectation: {actual_underdog_points - expected_underdog_points:+.2f}")
    print("Note: Tied and unplayed games excluded; probabilities are historical market estimates.")


if __name__ == "__main__":
    main()
