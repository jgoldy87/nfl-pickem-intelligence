from analysis.pickem_analyzer import load_results
from analysis.player_explorer import display_player_explorer


DATA_FILE = "data/picks_results.csv"


def main():
    df = load_results(DATA_FILE)

    players = sorted(
        df["player"].unique()
    )

    print("\nAvailable players:")

    for number, player in enumerate(
        players,
        start=1,
    ):
        print(f"{number}. {player}")

    choice = input(
        "\nSelect a player number: "
    )

    try:
        player_number = int(choice)

        selected_player = players[
            player_number - 1
        ]

    except (
        ValueError,
        IndexError,
    ):
        print("Invalid player selection.")
        return

    display_player_explorer(
        df,
        selected_player,
    )


if __name__ == "__main__":
    main()