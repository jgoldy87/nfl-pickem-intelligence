from analysis.data_pipeline import (
    append_weekly_picks,
)


NEW_PICKS = (
    "data/imports/week_01_more_picks.csv"
)

WEEK_FILE = (
    "data/picks/2026_week_01.csv"
)


def main():
    updated = append_weekly_picks(
        NEW_PICKS,
        WEEK_FILE,
    )

    print(
        "\nWeekly picks updated successfully."
    )

    print(
        f"Total rows: {len(updated)}"
    )

    print("\nPlayers:")

    print(
        sorted(
            updated["player"].unique()
        )
    )


if __name__ == "__main__":
    main()