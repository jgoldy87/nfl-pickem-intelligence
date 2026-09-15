from analysis.data_pipeline import (
    generate_weekly_pick_template,
)


def main():
    players = [
        "James",
        "Mike",
        "Sarah",
    ]

    template = generate_weekly_pick_template(
        season=2026,
        week=1,
        players=players,
        output_filepath=(
            "data/templates/"
            "2026_week_01_template.csv"
        ),
    )

    print(
        "\nWeekly pick template created."
    )

    print(
        f"Rows: {len(template)}"
    )

    print(
        "\nPlayers:"
    )

    print(
        sorted(
            template["player"].unique()
        )
    )

    print(
        "\nPreview:"
    )

    print(
        template.head(
            10
        ).to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()