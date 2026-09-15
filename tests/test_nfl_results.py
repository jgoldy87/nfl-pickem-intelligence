from analysis.nfl_results import (
    fetch_week_results,
)


def main():
    results = fetch_week_results(
        season=2026,
        week=1,
    )

    print(
        results.to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()