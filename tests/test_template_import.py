from analysis.data_pipeline import (
    load_pick_import,
)


def main():
    picks = load_pick_import(
        "data/templates/"
        "2026_week_01_template.csv"
    )

    print(
        "\nValid submitted picks:"
    )

    print(
        picks.to_string(
            index=False
        )
    )

    print(
        f"\nPicks ready to import: "
        f"{len(picks)}"
    )


if __name__ == "__main__":
    main()