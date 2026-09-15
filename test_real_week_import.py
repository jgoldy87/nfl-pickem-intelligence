from analysis.data_pipeline import (
    append_weekly_picks,
)


def main():
    updated = append_weekly_picks(
        new_picks_filepath=(
            "data/templates/"
            "2026_week_01_template.csv"
        ),
        destination_filepath=(
            "data/picks/"
            "2026_week_01.csv"
        ),
    )

    print(
        "\nReal Week 1 picks imported."
    )

    print(
        f"Rows: {len(updated)}"
    )

    print(
        updated.to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()