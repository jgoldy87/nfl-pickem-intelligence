from analysis.pickem_analyzer import (
    load_results,
    pool_game_results,
    lone_wolf_picks,
    lone_wolf_performance,
    unanimous_picks,
    collective_disasters,
    player_agreement,
)


def main():

    df = load_results(
        "data/picks_results.csv"
    )

    game_results = pool_game_results(
        df
    )

    print(
        game_results.to_string(
            index=False
        )
    )

    lone_wolves = lone_wolf_picks(
        df
    )

    print("\nLONE WOLF PICKS")

    if lone_wolves.empty:
        print(
            "No Lone Wolf picks found."
        )
    else:
        print(
            lone_wolves.to_string(
                index=False
            )
        )
    performance = lone_wolf_performance(
        df
    )

    print("\nLONE WOLF PERFORMANCE")

    if performance.empty:
        print(
            "No Lone Wolf performance available."
        )
    else:
        print(
            performance.to_string(
                index=False
            )
        )

    unanimous = unanimous_picks(
        df
    )

    print("\nUNANIMOUS PICKS")

    if unanimous.empty:
        print(
            "No unanimous picks found."
        )
    else:
        print(
            unanimous.to_string(
                index=False
            )
        )

    disasters = collective_disasters(
        df
    )

    print("\nCOLLECTIVE DISASTERS")

    if disasters.empty:
        print(
            "No collective disasters found."
        )
    else:
        print(
            disasters.to_string(
                index=False
            )
        )

    agreement = player_agreement(
        df
    )

    print("\nPLAYER AGREEMENT")

    if agreement.empty:
        print(
            "No player agreement data available."
        )
    else:
        print(
            agreement.to_string(
                index=False
            )
        )


if __name__ == "__main__":
    main()