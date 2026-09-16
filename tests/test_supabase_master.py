import pandas as pd

from analysis.data_pipeline import (
    build_master_results_from_supabase,
)


supabase_master = (
    build_master_results_from_supabase()
)

csv_master = pd.read_csv(
    "data/picks_results.csv"
)


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
    supabase_master[
        compare_columns
    ]
    .sort_values(
        [
            "season",
            "week",
            "player",
            "game_id",
        ]
    )
    .reset_index(drop=True)
)


csv_compare = (
    csv_master[
        compare_columns
    ]
    .sort_values(
        [
            "season",
            "week",
            "player",
            "game_id",
        ]
    )
    .reset_index(drop=True)
)


print(
    "Supabase master rows:",
    len(supabase_compare),
)

print(
    "CSV master rows:",
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
        "SUCCESS: Supabase master "
        "matches CSV master."
    )

except AssertionError as error:

    print(
        "MISMATCH FOUND:"
    )

    print(error)