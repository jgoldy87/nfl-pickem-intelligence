from analysis.data_pipeline import (
    save_master_results,
)


def main():
    master = save_master_results()

    print("\nMaster results rebuilt successfully.")
    print(f"Rows: {len(master)}")

    print("\nPlayers:")
    print(
        sorted(
            master["player"].unique()
        )
    )

    print("\nPreview:")
    print(
        master.head().to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()