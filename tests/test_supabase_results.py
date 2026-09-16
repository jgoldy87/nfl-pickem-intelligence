import pandas as pd

from analysis.database import load_picks
from analysis.data_pipeline import (
    build_results_from_picks,
)


# -----------------------------
# Build results from Supabase
# -----------------------------

picks = load_picks()

week_1 = picks[
    (picks["season"] == 2026)
    & (picks["week"] == 1)
].copy()

week_1 = week_1.rename(
    columns={
        "pick": "picked_team",
    }
)

week_1 = week_1[
    [
        "season",
        "week",
        "player",
        "game_id",
        "picked_team",
        "confidence",
    ]
]

supabase_results = (
    build_results_from_picks(
        week_1
    )
)


# -----------------------------
# Load existing CSV results
# -----------------------------

csv_results = pd.read_csv(
    "data/picks_results.csv"
)

csv_week_1 = csv_results[
    (csv_results["season"] == 2026)
    & (csv_results["week"] == 1)
].copy()


# -----------------------------
# Compare important fields
# -----------------------------

compare_columns = [
    "season",
    "week",
    "player",
    "game_id",
    "picked_team",
    "confidence",
    "winner",
    "pick_correct",
    "points_earned",
]

supabase_compare = (
    supabase_results[
        compare_columns
    ]
    .sort_values(
        [
            "player",
            "game_id",
        ]
    )
    .reset_index(drop=True)
)

csv_compare = (
    csv_week_1[
        compare_columns
    ]
    .sort_values(
        [
            "player",
            "game_id",
        ]
    )
    .reset_index(drop=True)
)


print(
    "Supabase rows:",
    len(supabase_compare),
)

print(
    "CSV rows:",
    len(csv_compare),
)

print()

try:

    pd.testing.assert_frame_equal(
        supabase_compare,
        csv_compare,
        check_dtype=False,
    )

    print(
        "SUCCESS: Supabase results "
        "match CSV results."
    )

except AssertionError as error:

    print(
        "MISMATCH FOUND:"
    )

    print(error)