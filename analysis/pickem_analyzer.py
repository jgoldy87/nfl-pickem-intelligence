import pandas as pd
from itertools import combinations

def completed_results(df):
    """
    Return only completed games.

    If game_completed does not exist, assume
    all rows are completed for backward compatibility.
    """

    if "game_completed" not in df.columns:
        return df.copy()

    return df[
        df["game_completed"] == True
    ].copy()

def load_results(filepath):
    """
    Load pick'em results and create calculated fields.
    """

    df = pd.read_csv(filepath)

    required_columns = [
        "season",
        "week",
        "player",
        "game_id",
        "away_team",
        "home_team",
        "picked_team",
        "confidence",
        "winner",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    team_columns = [
        "away_team",
        "home_team",
        "picked_team",
        "winner",
    ]

    for column in team_columns:
        df[column] = (
            df[column]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    df["picked_home"] = (
        df["picked_team"] == df["home_team"]
    )

    df["pick_location"] = df["picked_home"].map(
        {
            True: "Home",
            False: "Away",
        }
    )

    df["pick_correct"] = (
        df["picked_team"] == df["winner"]
    )

    df["points_earned"] = df["confidence"].where(
        df["pick_correct"],
        0,
    )

    return df


def overall_standings(df):
    """
    Overall performance for each player.
    """

    df = completed_results(df)

    standings = (
        df.groupby("player")
        .agg(
            Picks=("pick_correct", "count"),
            Correct=("pick_correct", "sum"),
            Confidence_Points=("points_earned", "sum"),
            Confidence_Risked=("confidence", "sum"),
        )
        .reset_index()
    )

    standings["Incorrect"] = (
        standings["Picks"] - standings["Correct"]
    )

    standings["Win_Pct"] = (
        standings["Correct"] / standings["Picks"]
    )

    standings["Point_Efficiency"] = (
        standings["Confidence_Points"]
        / standings["Confidence_Risked"]
    )

    standings = standings[
        [
            "player",
            "Correct",
            "Incorrect",
            "Picks",
            "Win_Pct",
            "Confidence_Points",
            "Confidence_Risked",
            "Point_Efficiency",
        ]
    ]

    standings = standings.sort_values(
        by=["Confidence_Points", "Win_Pct"],
        ascending=False,
    )

    return standings


def weekly_results(df):
    """
    Performance for every player by week.
    """
    df = completed_results(df)

    weekly = (
        df.groupby(["season", "week", "player"])
        .agg(
            Picks=("pick_correct", "count"),
            Correct=("pick_correct", "sum"),
            Confidence_Points=("points_earned", "sum"),
            Confidence_Risked=("confidence", "sum"),
        )
        .reset_index()
    )

    weekly["Incorrect"] = (
        weekly["Picks"] - weekly["Correct"]
    )

    weekly["Win_Pct"] = (
        weekly["Correct"] / weekly["Picks"]
    )

    weekly["Point_Efficiency"] = (
        weekly["Confidence_Points"]
        / weekly["Confidence_Risked"]
    )

    weekly["Weekly_Rank"] = (
        weekly.groupby(["season", "week"])["Confidence_Points"]
        .rank(
            method="min",
            ascending=False,
        )
        .astype(int)
    )

    weekly = weekly[
        [
            "season",
            "week",
            "player",
            "Correct",
            "Incorrect",
            "Picks",
            "Win_Pct",
            "Confidence_Points",
            "Confidence_Risked",
            "Point_Efficiency",
            "Weekly_Rank",
        ]
    ]

    return weekly.sort_values(
        ["season", "week", "Weekly_Rank"]
    )


def home_away_records(df):
    """
    Record when each player picks home vs away teams.
    """

    df = completed_results(df)

    records = (
        df.groupby(["player", "pick_location"])
        .agg(
            Picks=("pick_correct", "count"),
            Correct=("pick_correct", "sum"),
            Confidence_Points=("points_earned", "sum"),
            Avg_Confidence=("confidence", "mean"),
        )
        .reset_index()
    )

    records["Incorrect"] = (
        records["Picks"] - records["Correct"]
    )

    records["Win_Pct"] = (
        records["Correct"] / records["Picks"]
    )

    return records[
        [
            "player",
            "pick_location",
            "Correct",
            "Incorrect",
            "Picks",
            "Win_Pct",
            "Avg_Confidence",
            "Confidence_Points",
        ]
    ]


def team_records(df):
    """
    Record for each player when picking a particular NFL team.
    """

    df = completed_results(df)

    records = (
        df.groupby(["player", "picked_team"])
        .agg(
            Picks=("pick_correct", "count"),
            Correct=("pick_correct", "sum"),
            Confidence_Points=("points_earned", "sum"),
            Confidence_Risked=("confidence", "sum"),
            Avg_Confidence=("confidence", "mean"),
        )
        .reset_index()
    )

    records["Incorrect"] = (
        records["Picks"] - records["Correct"]
    )

    records["Win_Pct"] = (
        records["Correct"] / records["Picks"]
    )

    records["Point_Efficiency"] = (
        records["Confidence_Points"]
        / records["Confidence_Risked"]
    )

    return records[
        [
            "player",
            "picked_team",
            "Correct",
            "Incorrect",
            "Picks",
            "Win_Pct",
            "Avg_Confidence",
            "Confidence_Risked",
            "Confidence_Points",
            "Point_Efficiency",
        ]
    ].sort_values(
        ["player", "picked_team"]
    )

def opponent_records(df):
    """
    Record for each player when picking against a particular NFL team.
    """

    df = completed_results(df)

    working_df = df.copy()

    working_df["opponent"] = working_df.apply(
        lambda row: (
            row["away_team"]
            if row["picked_team"] == row["home_team"]
            else row["home_team"]
        ),
        axis=1,
    )

    records = (
        working_df.groupby(["player", "opponent"])
        .agg(
            Picks=("pick_correct", "count"),
            Correct=("pick_correct", "sum"),
            Confidence_Points=("points_earned", "sum"),
            Confidence_Risked=("confidence", "sum"),
            Avg_Confidence=("confidence", "mean"),
        )
        .reset_index()
    )

    records["Incorrect"] = (
        records["Picks"] - records["Correct"]
    )

    records["Win_Pct"] = (
        records["Correct"] / records["Picks"]
    )

    records["Point_Efficiency"] = (
        records["Confidence_Points"]
        / records["Confidence_Risked"]
    )

    return records[
        [
            "player",
            "opponent",
            "Correct",
            "Incorrect",
            "Picks",
            "Win_Pct",
            "Avg_Confidence",
            "Confidence_Risked",
            "Confidence_Points",
            "Point_Efficiency",
        ]
    ].sort_values(
        ["player", "opponent"]
    )

def confidence_performance(df):
    """
    Analyze performance by confidence range.
    """

    df = completed_results(df)

    bins = [0, 4, 8, 12, float("inf")]

    labels = [
        "1-4",
        "5-8",
        "9-12",
        "13+",
    ]

    working_df = df.copy()

    working_df["Confidence_Band"] = pd.cut(
        working_df["confidence"],
        bins=bins,
        labels=labels,
    )

    summary = (
        working_df.groupby(
            ["player", "Confidence_Band"],
            observed=True,
        )
        .agg(
            Picks=("pick_correct", "count"),
            Correct=("pick_correct", "sum"),
            Confidence_Points=("points_earned", "sum"),
            Avg_Confidence=("confidence", "mean"),
        )
        .reset_index()
    )

    summary["Incorrect"] = (
        summary["Picks"] - summary["Correct"]
    )

    summary["Win_Pct"] = (
        summary["Correct"] / summary["Picks"]
    )

    return summary[
        [
            "player",
            "Confidence_Band",
            "Correct",
            "Incorrect",
            "Picks",
            "Win_Pct",
            "Avg_Confidence",
            "Confidence_Points",
        ]
    ]


def player_summary(df, player):
    """
    Return all major analyses for one player.
    """

    player_df = df[
        df["player"].str.lower() == player.lower()
    ]

    if player_df.empty:
        raise ValueError(
            f"No results found for player: {player}"
        )

    return {
        "overall": overall_standings(player_df),
        "weekly": weekly_results(player_df),
        "home_away": home_away_records(player_df),
        "teams": team_records(player_df),
        "opponents": opponent_records(player_df),
        "confidence": confidence_performance(player_df),
        "status": player_week_status(
            player_df,
            player,
        ),
    }

def pool_game_results(df):
    completed = completed_results(
        df
    )

    if completed.empty:
        return pd.DataFrame(
            columns=[
                "season",
                "week",
                "game_id",
                "away_team",
                "home_team",
                "winner",
                "Correct",
                "Incorrect",
                "Picks",
                "Pool_Accuracy",
                "Avg_Confidence",
            ]
        )

    game_results = (
        completed
        .groupby(
            [
                "season",
                "week",
                "game_id",
                "away_team",
                "home_team",
                "winner",
            ],
            as_index=False,
        )
        .agg(
            Correct=(
                "pick_correct",
                "sum",
            ),
            Picks=(
                "pick_correct",
                "count",
            ),
            Avg_Confidence=(
                "confidence",
                "mean",
            ),
        )
    )

    game_results["Incorrect"] = (
        game_results["Picks"]
        - game_results["Correct"]
    )

    game_results["Pool_Accuracy"] = (
        game_results["Correct"]
        / game_results["Picks"]
    )

    return game_results

def lone_wolf_picks(df):
    completed = completed_results(
        df
    )

    if completed.empty:
        return pd.DataFrame(
            columns=[
                "season",
                "week",
                "game_id",
                "away_team",
                "home_team",
                "winner",
                "Lone_Wolf",
                "Lone_Pick",
                "Majority_Pick",
                "Confidence",
                "Correct",
            ]
        )

    lone_wolf_rows = []

    grouped_games = completed.groupby(
        [
            "season",
            "week",
            "game_id",
        ]
    )

    for (
        season,
        week,
        game_id,
    ), game_df in grouped_games:

        # Lone Wolf analysis requires
        # picks from all three players.
        if len(game_df) != 3:
            continue

        pick_counts = (
            game_df["picked_team"]
            .value_counts()
        )

        # We need a 2-1 split.
        if (
            len(pick_counts) != 2
            or sorted(
                pick_counts.tolist()
            ) != [1, 2]
        ):
            continue

        lone_pick = (
            pick_counts[
                pick_counts == 1
            ]
            .index[0]
        )

        majority_pick = (
            pick_counts[
                pick_counts == 2
            ]
            .index[0]
        )

        lone_row = game_df[
            game_df["picked_team"]
            == lone_pick
        ].iloc[0]

        lone_wolf_rows.append(
            {
                "season": season,
                "week": week,
                "game_id": game_id,
                "away_team": lone_row[
                    "away_team"
                ],
                "home_team": lone_row[
                    "home_team"
                ],
                "winner": lone_row[
                    "winner"
                ],
                "Lone_Wolf": lone_row[
                    "player"
                ],
                "Lone_Pick": lone_pick,
                "Majority_Pick": majority_pick,
                "Confidence": lone_row[
                    "confidence"
                ],
                "Correct": bool(
                    lone_row[
                        "pick_correct"
                    ]
                ),
            }
        )

    return pd.DataFrame(
        lone_wolf_rows
    )

def lone_wolf_performance(df):
    lone_wolves = lone_wolf_picks(
        df
    )

    if lone_wolves.empty:
        return pd.DataFrame(
            columns=[
                "Lone_Wolf",
                "Attempts",
                "Correct",
                "Incorrect",
                "Win_Pct",
            ]
        )

    lone_wolves["Net_Points"] = (
        lone_wolves["Confidence"].where(
            lone_wolves["Correct"] == True,
            -lone_wolves["Confidence"],
        )
    )

    performance = (
        lone_wolves
        .groupby(
            "Lone_Wolf",
            as_index=False,
        )
        .agg(
            Attempts=(
                "Correct",
                "count",
            ),
            Correct=(
                "Correct",
                "sum",
            ),
            Net_Points_Gained=(
                "Net_Points",
                "sum",
            ),
        )
    )

    performance["Incorrect"] = (
        performance["Attempts"]
        - performance["Correct"]
    )

    performance["Win_Pct"] = (
        performance["Correct"]
        / performance["Attempts"]
    )

    performance = performance.sort_values(
        by=[
            "Win_Pct",
            "Attempts",
        ],
        ascending=[
            False,
            False,
        ],
    )

    return performance.reset_index(
        drop=True
    )

def lone_wolf_standings_impact(df):
    """
    Calculate the standings impact of Lone Wolf games
    between the Lone Wolf and each opponent.

    Each cell represents the net confidence-point
    advantage gained or lost through Lone Wolf
    situations between two players.
    """

    lone_wolves = lone_wolf_picks(df)

    if lone_wolves.empty:
        return pd.DataFrame()

    completed = completed_results(df)

    players = sorted(
        completed["player"].dropna().unique()
    )

    impact = pd.DataFrame(
        0,
        index=players,
        columns=players,
        dtype=int,
    )

    for _, lone_wolf in lone_wolves.iterrows():

        game_id = lone_wolf["game_id"]
        lone_wolf_player = lone_wolf[
            "Lone_Wolf"
        ]

        game_results = completed[
            completed["game_id"] == game_id
        ]

        if game_results.empty:
            continue

        points_by_player = (
            game_results
            .set_index("player")["points_earned"]
            .to_dict()
        )

        if (
            lone_wolf_player
            not in points_by_player
        ):
            continue

        lone_wolf_points = points_by_player[
            lone_wolf_player
        ]

        for opponent in players:

            if opponent == lone_wolf_player:
                continue

            if opponent not in points_by_player:
                continue

            opponent_points = points_by_player[
                opponent
            ]

            difference = (
                lone_wolf_points
                - opponent_points
            )

            impact.loc[
                lone_wolf_player,
                opponent,
            ] += difference

            impact.loc[
                opponent,
                lone_wolf_player,
            ] -= difference

    impact.index.name = "Player"

    return impact

def lone_wolf_impact_detail(df):
    """
    Show the game-by-game calculations used to build
    the Lone Wolf Standings Impact matrix.
    """

    lone_wolves = lone_wolf_picks(df)

    if lone_wolves.empty:
        return pd.DataFrame()

    completed = completed_results(df)

    detail_rows = []

    for _, lone_wolf in lone_wolves.iterrows():

        game_id = lone_wolf["game_id"]
        lone_wolf_player = lone_wolf["Lone_Wolf"]

        game_results = completed[
            completed["game_id"] == game_id
        ]

        if game_results.empty:
            continue

        lone_wolf_result = game_results[
            game_results["player"]
            == lone_wolf_player
        ]

        if lone_wolf_result.empty:
            continue

        lone_wolf_points = (
            lone_wolf_result.iloc[0][
                "points_earned"
            ]
        )

        for _, opponent in game_results.iterrows():

            opponent_player = opponent["player"]

            if opponent_player == lone_wolf_player:
                continue

            opponent_points = opponent[
                "points_earned"
            ]

            impact = (
                lone_wolf_points
                - opponent_points
            )

            detail_rows.append(
                {
                    "Week": lone_wolf["week"],
                    "Game": game_id,
                    "Lone_Wolf": lone_wolf_player,
                    "Opponent": opponent_player,
                    "Lone_Wolf_Points": lone_wolf_points,
                    "Opponent_Points": opponent_points,
                    "Impact": impact,
                }
            )

    return pd.DataFrame(detail_rows)

def unanimous_picks(df):
    completed = completed_results(
        df
    )

    if completed.empty:
        return pd.DataFrame(
            columns=[
                "season",
                "week",
                "game_id",
                "away_team",
                "home_team",
                "winner",
                "Unanimous_Pick",
                "Total_Confidence",
                "Avg_Confidence",
                "Correct",
            ]
        )

    unanimous_rows = []

    grouped_games = completed.groupby(
        [
            "season",
            "week",
            "game_id",
        ]
    )

    for (
        season,
        week,
        game_id,
    ), game_df in grouped_games:

        # Only evaluate games where all
        # three players submitted picks.
        if len(game_df) != 3:
            continue

        unique_picks = (
            game_df["picked_team"]
            .dropna()
            .unique()
        )

        if len(unique_picks) != 1:
            continue

        unanimous_pick = (
            unique_picks[0]
        )

        first_row = game_df.iloc[0]

        unanimous_rows.append(
            {
                "season": season,
                "week": week,
                "game_id": game_id,
                "away_team": first_row[
                    "away_team"
                ],
                "home_team": first_row[
                    "home_team"
                ],
                "winner": first_row[
                    "winner"
                ],
                "Unanimous_Pick": unanimous_pick,
                "Total_Confidence": int(
                    game_df[
                        "confidence"
                    ].sum()
                ),
                "Avg_Confidence": (
                    game_df[
                        "confidence"
                    ].mean()
                ),
                "Correct": (
                    unanimous_pick
                    == first_row["winner"]
                ),
            }
        )

    return pd.DataFrame(
        unanimous_rows
    )

def collective_disasters(df):
    unanimous = unanimous_picks(
        df
    )

    if unanimous.empty:
        return pd.DataFrame(
            columns=[
                "season",
                "week",
                "game_id",
                "away_team",
                "home_team",
                "winner",
                "Unanimous_Pick",
                "Total_Confidence",
                "Avg_Confidence",
            ]
        )

    disasters = unanimous[
        unanimous["Correct"] == False
    ].copy()

    disasters = disasters.sort_values(
        by="Total_Confidence",
        ascending=False,
    )

    return disasters.reset_index(
        drop=True
    )

def collective_triumphs(df):
    unanimous = unanimous_picks(
        df
    )

    if unanimous.empty:
        return pd.DataFrame(
            columns=[
                "season",
                "week",
                "game_id",
                "away_team",
                "home_team",
                "winner",
                "Unanimous_Pick",
                "Total_Confidence",
                "Avg_Confidence",
            ]
        )

    triumphs = unanimous[
        unanimous["Correct"] == True
    ].copy()

    triumphs = triumphs.sort_values(
        by="Total_Confidence",
        ascending=False,
    )

    return triumphs.reset_index(
        drop=True
    )

def pool_burners(df):
    disasters = collective_disasters(
        df
    )

    if disasters.empty:
        return pd.DataFrame(
            columns=[
                "Team",
                "Burns",
                "Confidence_Lost",
                "Avg_Confidence_Lost",
            ]
        )

    burners = (
        disasters.groupby("winner")
        .agg(
            Burns=("game_id", "count"),
            Confidence_Lost=("Total_Confidence", "sum"),
            Avg_Confidence_Lost=("Total_Confidence", "mean"),
        )
        .reset_index()
        .rename(
            columns={
                "winner": "Team",
            }
        )
    )

    burners["Avg_Confidence_Lost"] = (
        burners["Avg_Confidence_Lost"]
        .round(1)
    )

    burners = burners.sort_values(
        by=[
            "Burns",
            "Confidence_Lost",
        ],
        ascending=[
            False,
            False,
        ],
    )

    return burners.reset_index(
        drop=True
    )

def player_agreement(df):
    completed = completed_results(
        df
    )

    if completed.empty:
        return pd.DataFrame(
            columns=[
                "Player_A",
                "Player_B",
                "Shared_Games",
                "Same_Pick",
                "Disagreements",
                "Agreement_Pct",
                "Player_A_Wins",
                "Player_B_Wins",
            ]
        )

    players = sorted(
        completed["player"]
        .dropna()
        .unique()
    )

    rows = []

    for player_a, player_b in combinations(
        players,
        2,
    ):

        a_df = completed[
            completed["player"]
            == player_a
        ][
            [
                "season",
                "week",
                "game_id",
                "picked_team",
                "pick_correct",
            ]
        ].rename(
            columns={
                "picked_team": "Pick_A",
                "pick_correct": "Correct_A",
            }
        )

        b_df = completed[
            completed["player"]
            == player_b
        ][
            [
                "season",
                "week",
                "game_id",
                "picked_team",
                "pick_correct",
            ]
        ].rename(
            columns={
                "picked_team": "Pick_B",
                "pick_correct": "Correct_B",
            }
        )

        shared = a_df.merge(
            b_df,
            on=[
                "season",
                "week",
                "game_id",
            ],
            how="inner",
        )

        if shared.empty:
            continue

        same_pick = (
            shared["Pick_A"]
            == shared["Pick_B"]
        )

        disagreement = ~same_pick

        shared_games = len(
            shared
        )

        same_count = int(
            same_pick.sum()
        )

        disagreement_count = int(
            disagreement.sum()
        )

        player_a_wins = int(
            (
                disagreement
                & (shared["Correct_A"] == True)
            ).sum()
        )

        player_b_wins = int(
            (
                disagreement
                & (shared["Correct_B"] == True)
            ).sum()
        )

        rows.append(
            {
                "Player_A": player_a,
                "Player_B": player_b,
                "Shared_Games": shared_games,
                "Same_Pick": same_count,
                "Disagreements": disagreement_count,
                "Agreement_Pct": (
                    same_count
                    / shared_games
                ),
                "Player_A_Wins": player_a_wins,
                "Player_B_Wins": player_b_wins,
            }
        )

    return pd.DataFrame(
        rows
    )

def player_week_status(df, player, season=None, week=None):
    """
    Show completed and remaining picks for one player.
    """

    player_df = df[
        df["player"].str.lower() == player.lower()
    ].copy()

    if season is not None:
        player_df = player_df[
            player_df["season"] == season
        ]

    if week is not None:
        player_df = player_df[
            player_df["week"] == week
        ]

    if player_df.empty:
        raise ValueError(
            f"No results found for player: {player}"
        )

    if "game_completed" in player_df.columns:
        completed_mask = (
            player_df["game_completed"] == True
        )
    else:
        completed_mask = pd.Series(
            True,
            index=player_df.index,
        )

    completed = player_df[
        completed_mask
    ]

    total_picks = len(player_df)
    completed_picks = len(completed)
    remaining_picks = (
        total_picks - completed_picks
    )

    correct = int(
        completed["pick_correct"].sum()
    ) if completed_picks else 0

    incorrect = (
        completed_picks - correct
    )

    confidence_points = int(
        completed["points_earned"].sum()
    ) if completed_picks else 0

    return {
        "total_picks": total_picks,
        "completed_picks": completed_picks,
        "remaining_picks": remaining_picks,
        "correct": correct,
        "incorrect": incorrect,
        "confidence_points": confidence_points,
        "week_complete": (
            remaining_picks == 0
        ),
    }