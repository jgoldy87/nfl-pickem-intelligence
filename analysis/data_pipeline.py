from pathlib import Path
from analysis.nfl_results import fetch_week_results
from analysis.database import load_picks

import pandas as pd


def generate_weekly_pick_template(
    season,
    week,
    players,
    output_filepath=None,
):
    """
    Generate a weekly pick-entry template
    directly from the official NFL schedule.

    Creates one row per player per game.
    """

    schedule = fetch_week_results(
        season=season,
        week=week,
    )

    rows = []

    for player in players:
        for _, game in schedule.iterrows():
            rows.append(
                {
                    "season": season,
                    "week": week,
                    "player": player,
                    "game_id": game["game_id"],
                    "away_team": game["away_team"],
                    "home_team": game["home_team"],
                    "picked_team": "",
                    "confidence": "",
                }
            )

    template = pd.DataFrame(rows)

    if output_filepath is not None:
        output = Path(
            output_filepath
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        template.to_csv(
            output,
            index=False,
        )

    return template

def load_weekly_picks(filepath):
    """
    Load raw player picks for one week.
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
    ]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing pick columns: {missing}"
        )

    df = validate_unique_picks(df)

    return df

def load_pick_import(filepath):
    """
    Load a partially completed pick-entry file.

    Blank picks are ignored. Only rows containing
    an actual picked team are returned.
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
    ]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing pick columns: {missing}"
        )

    # Normalize text fields.
    for column in [
        "away_team",
        "home_team",
        "picked_team",
    ]:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
            .str.upper()
        )

    df["player"] = (
        df["player"]
        .astype("string")
        .str.strip()
    )

    # Remove rows where the pick has not
    # become available yet.
    df = df[
        df["picked_team"].notna()
        & (df["picked_team"] != "")
    ].copy()

    if df.empty:
        return df

    # Every submitted pick must be one of
    # the teams actually playing.
    valid_team = (
        (df["picked_team"] == df["away_team"])
        | (df["picked_team"] == df["home_team"])
    )

    if (~valid_team).any():
        invalid = df.loc[
            ~valid_team,
            [
                "player",
                "game_id",
                "away_team",
                "home_team",
                "picked_team",
            ],
        ]

        raise ValueError(
            "Invalid picked team found:\n"
            + invalid.to_string(index=False)
        )

    # Confidence must be numeric.
    df["confidence"] = pd.to_numeric(
        df["confidence"],
        errors="coerce",
    )

    missing_confidence = (
        df["confidence"].isna()
    )

    if missing_confidence.any():
        invalid = df.loc[
            missing_confidence,
            [
                "player",
                "game_id",
                "picked_team",
                "confidence",
            ],
        ]

        raise ValueError(
            "A submitted pick is missing a "
            "valid confidence value:\n"
            + invalid.to_string(index=False)
        )

    df["confidence"] = (
        df["confidence"].astype(int)
    )

    df = validate_unique_picks(df)

    df = validate_confidence_values(df)

    return df

def validate_unique_picks(df):
    """
    Ensure each player has only one pick per game.
    """

    key_columns = [
        "season",
        "week",
        "player",
        "game_id",
    ]

    duplicates = df[
        df.duplicated(
            subset=key_columns,
            keep=False,
        )
    ]

    if not duplicates.empty:
        duplicate_rows = duplicates[
            key_columns
        ].drop_duplicates()

        raise ValueError(
            "Duplicate player picks found:\n"
            + duplicate_rows.to_string(index=False)
        )

    return df

def validate_confidence_values(
    df,
    max_confidence=None,
):
    """
    Validate confidence values for each player.

    Partial weekly cards are allowed, but a player
    cannot use the same confidence value more than once.

    max_confidence can be supplied based on the
    number of NFL games scheduled that week.
    """

    if df.empty:
        return df

    if max_confidence is None:
        season_values = df["season"].unique()
        week_values = df["week"].unique()

        if (
            len(season_values) != 1
            or len(week_values) != 1
        ):
            raise ValueError(
                "Confidence validation requires "
                "exactly one season and one week."
            )

        season = int(
            season_values[0]
        )

        week = int(
            week_values[0]
        )

        schedule = fetch_week_results(
            season=season,
            week=week,
        )

        max_confidence = len(schedule)

    invalid_range = (
        (df["confidence"] < 1)
        | (df["confidence"] > max_confidence)
    )

    if invalid_range.any():
        invalid = df.loc[
            invalid_range,
            [
                "player",
                "game_id",
                "confidence",
            ],
        ]

        raise ValueError(
            "Confidence values must be between "
            f"1 and {max_confidence}:\n"
            + invalid.to_string(index=False)
        )

    duplicate_confidence = df.duplicated(
        subset=[
            "season",
            "week",
            "player",
            "confidence",
        ],
        keep=False,
    )

    if duplicate_confidence.any():
        invalid = df.loc[
            duplicate_confidence,
            [
                "player",
                "game_id",
                "picked_team",
                "confidence",
            ],
        ].sort_values(
            [
                "player",
                "confidence",
            ]
        )

        raise ValueError(
            "Duplicate confidence values found:\n"
            + invalid.to_string(index=False)
        )

    return df

def append_weekly_picks(
    new_picks_filepath,
    destination_filepath,
):
    """
    Add newly available player picks to an existing
    weekly picks file.

    Existing player/game picks are not duplicated.
    """

    new_picks = load_pick_import(
        new_picks_filepath
    )

    destination = Path(
        destination_filepath
    )

    # First import for this week
    if not destination.exists():
        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        new_picks.to_csv(
            destination,
            index=False,
        )

        return new_picks

    existing_picks = load_weekly_picks(
        destination
    )

    key_columns = [
        "season",
        "week",
        "player",
        "game_id",
    ]

    combined = pd.concat(
        [
            existing_picks,
            new_picks,
        ],
        ignore_index=True,
    )

    duplicates = combined.duplicated(
        subset=key_columns,
        keep=False,
    )

    if duplicates.any():
        duplicate_rows = combined.loc[
            duplicates,
            key_columns,
        ].drop_duplicates()

        raise ValueError(
            "These picks already exist:\n"
            + duplicate_rows.to_string(
                index=False
            )
        )

    combined = validate_confidence_values(
        combined
    )

    combined = combined.sort_values(
        [
            "season",
            "week",
            "player",
            "game_id",
        ]
    )

    combined.to_csv(
        destination,
        index=False,
    )

    return combined

def append_pick_rows(
    new_picks,
    destination_filepath,
):
    destination = Path(
        destination_filepath
    )

    if new_picks.empty:
        return new_picks

    new_picks = validate_unique_picks(
        new_picks
    )

    new_picks = validate_confidence_values(
        new_picks
    )

    if not destination.exists():

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        new_picks = new_picks.sort_values(
            [
                "season",
                "week",
                "player",
                "game_id",
            ]
        )

        new_picks.to_csv(
            destination,
            index=False,
        )

        return new_picks


    existing_picks = load_weekly_picks(
        destination
    )

    combined = pd.concat(
        [
            existing_picks,
            new_picks,
        ],
        ignore_index=True,
    )

    combined = validate_unique_picks(
        combined
    )

    combined = validate_confidence_values(
        combined
    )

    combined = combined.sort_values(
        [
            "season",
            "week",
            "player",
            "game_id",
        ]
    )

    combined.to_csv(
        destination,
        index=False,
    )

    return combined

def upsert_pick_rows(
    new_picks,
    destination_filepath,
):
    destination = Path(
        destination_filepath
    )

    if new_picks.empty:
        return new_picks

    new_picks = validate_unique_picks(
        new_picks
    )

    new_picks = validate_confidence_values(
        new_picks
    )

    if destination.exists():

        existing_picks = load_weekly_picks(
            destination
        )

        key_columns = [
            "season",
            "week",
            "player",
            "game_id",
        ]

        new_keys = new_picks[
            key_columns
        ]

        merged_keys = existing_picks.merge(
            new_keys,
            on=key_columns,
            how="left",
            indicator=True,
        )

        keep_existing = (
            merged_keys["_merge"]
            == "left_only"
        )

        existing_picks = existing_picks.loc[
            keep_existing.values
        ].copy()

        combined = pd.concat(
            [
                existing_picks,
                new_picks,
            ],
            ignore_index=True,
        )

    else:

        combined = new_picks.copy()

    combined = validate_unique_picks(
        combined
    )

    combined = validate_confidence_values(
        combined
    )

    combined = combined.sort_values(
        [
            "season",
            "week",
            "player",
            "game_id",
        ]
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    combined.to_csv(
        destination,
        index=False,
    )

    return combined

def load_game_results(filepath):
    """
    Load final game results for one week.
    """

    df = pd.read_csv(filepath)

    required_columns = [
        "season",
        "week",
        "game_id",
        "away_team",
        "home_team",
        "winner",
        "status",
    ]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing result columns: {missing}"
        )

    return df

def build_results_from_picks(picks):
    """
    Join a DataFrame of player picks to
    automatically fetched NFL results.
    """

    if picks.empty:
        return picks.copy()

    picks = picks.copy()

    season_values = picks["season"].unique()
    week_values = picks["week"].unique()

    if len(season_values) != 1:
        raise ValueError(
            "Picks must contain exactly "
            "one season."
        )

    if len(week_values) != 1:
        raise ValueError(
            "Picks must contain exactly "
            "one week."
        )

    season = int(
        season_values[0]
    )

    week = int(
        week_values[0]
    )

    results = fetch_week_results(
        season=season,
        week=week,
    )

    # Add schedule information to database
    # picks because Supabase stores only the
    # essential pick fields.
    schedule_columns = [
        "season",
        "week",
        "game_id",
        "away_team",
        "home_team",
        "winner",
        "status",
        "game_completed",
    ]

    merged = picks.merge(
        results[schedule_columns],
        on=[
            "season",
            "week",
            "game_id",
        ],
        how="left",
        validate="many_to_one",
    )

    unmatched_games = (
        merged["status"].isna()
    )

    if unmatched_games.any():
        missing = (
            merged.loc[
                unmatched_games,
                "game_id",
            ]
            .unique()
            .tolist()
        )

        raise ValueError(
            "Could not match these pick games "
            "to NFL schedule data:\n"
            f"{missing}"
        )

    team_columns = [
        "away_team",
        "home_team",
        "picked_team",
    ]

    for column in team_columns:
        merged[column] = (
            merged[column]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    merged["winner"] = (
        merged["winner"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    merged["pick_correct"] = pd.Series(
        pd.NA,
        index=merged.index,
        dtype="boolean",
    )

    completed = (
        merged["game_completed"] == True
    )

    merged.loc[
        completed,
        "pick_correct",
    ] = (
        merged.loc[
            completed,
            "picked_team",
        ]
        == merged.loc[
            completed,
            "winner",
        ]
    )

    merged["points_earned"] = pd.Series(
        pd.NA,
        index=merged.index,
        dtype="Int64",
    )

    merged.loc[
        completed,
        "points_earned",
    ] = merged.loc[
        completed,
        "confidence",
    ].where(
        merged.loc[
            completed,
            "pick_correct",
        ],
        0,
    )

    return merged

def build_week_results(
    picks_filepath,
):
    """
    Join player picks to automatically fetched NFL results.
    """

    picks = load_weekly_picks(
        picks_filepath
    )

    season_values = picks["season"].unique()
    week_values = picks["week"].unique()

    if len(season_values) != 1:
        raise ValueError(
            "A weekly picks file must contain "
            "exactly one season."
        )

    if len(week_values) != 1:
        raise ValueError(
            "A weekly picks file must contain "
            "exactly one week."
        )

    season = int(
        season_values[0]
    )

    week = int(
        week_values[0]
    )

    results = fetch_week_results(
        season=season,
        week=week,
    )

    result_columns = [
        "season",
        "week",
        "game_id",
        "winner",
        "status",
        "game_completed",
    ]

    merged = picks.merge(
        results[result_columns],
        on=[
            "season",
            "week",
            "game_id",
        ],
        how="left",
        validate="many_to_one",
    )

    unmatched_games = (
        merged["status"].isna()
    )

    if unmatched_games.any():
        missing = (
            merged.loc[
                unmatched_games,
                "game_id",
            ]
            .unique()
            .tolist()
        )

        raise ValueError(
            "Could not match these pick games "
            "to NFL schedule data:\n"
            f"{missing}"
        )

    team_columns = [
        "away_team",
        "home_team",
        "picked_team",
    ]

    for column in team_columns:
        merged[column] = (
            merged[column]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    merged["winner"] = (
        merged["winner"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    merged["pick_correct"] = pd.Series(
        pd.NA,
        index=merged.index,
        dtype="boolean",
    )

    completed = (
        merged["game_completed"] == True
    )

    merged.loc[
        completed,
        "pick_correct",
    ] = (
        merged.loc[
            completed,
            "picked_team",
        ]
        == merged.loc[
            completed,
            "winner",
        ]
    )

    merged["points_earned"] = pd.Series(
        pd.NA,
        index=merged.index,
        dtype="Int64",
    )

    merged.loc[
        completed,
        "points_earned",
    ] = merged.loc[
        completed,
        "confidence",
    ].where(
        merged.loc[
            completed,
            "pick_correct",
        ],
        0,
    )

    return merged


def build_master_results(
    picks_directory="data/picks",
):
    """
    Build the complete master results table
    from all available weekly pick files.
    """

    picks_directory = Path(
        picks_directory
    )

    weekly_results = []

    for picks_file in sorted(
        picks_directory.glob("*.csv")
    ):
        week_df = build_week_results(
            picks_file
        )

        weekly_results.append(
            week_df
        )

    if not weekly_results:
        raise ValueError(
            "No weekly pick files were found."
        )

    master = pd.concat(
        weekly_results,
        ignore_index=True,
    )

    master = master.sort_values(
        [
            "season",
            "week",
            "player",
            "game_id",
        ]
    )

    return master

def build_master_results_from_supabase():
    """
    Build the complete master results table
    from picks stored in Supabase.
    """

    picks = load_picks()

    if picks.empty:
        raise ValueError(
            "No picks were found in Supabase."
        )

    # Translate database naming into the
    # naming expected by the analytics code.
    picks = picks.rename(
        columns={
            "pick": "picked_team",
        }
    )

    pick_columns = [
        "season",
        "week",
        "player",
        "game_id",
        "picked_team",
        "confidence",
    ]

    picks = picks[
        pick_columns
    ].copy()

    weekly_results = []

    week_groups = picks.groupby(
        [
            "season",
            "week",
        ],
        sort=True,
    )

    for (
        season,
        week,
    ), week_picks in week_groups:

        week_results = (
            build_results_from_picks(
                week_picks
            )
        )

        weekly_results.append(
            week_results
        )

    master = pd.concat(
        weekly_results,
        ignore_index=True,
    )

    master = master.sort_values(
        [
            "season",
            "week",
            "player",
            "game_id",
        ]
    )

    return master

def save_master_results(
    output_filepath="data/picks_results.csv",
):
    """
    Rebuild and save the master results CSV.
    """

    master = build_master_results()

    master.to_csv(
        output_filepath,
        index=False,
    )

    return master

def save_master_results_from_supabase(
    output_filepath="data/picks_results.csv",
):
    """
    Rebuild and save the master results CSV
    using Supabase as the picks source.
    """

    master = (
        build_master_results_from_supabase()
    )

    master.to_csv(
        output_filepath,
        index=False,
    )

    return master