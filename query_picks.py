import pandas as pd

from analysis.database import load_picks

def main():

    df = load_picks()

    # Limit analysis to Weeks 1-3.
    df = df[
        (df["season"] == 2026)
        & (df["week"].between(1, 3))
    ].copy()

    # --------------------------------------------------
    # Determine which team each player picked against
    # --------------------------------------------------

    def get_opponent(row):

        parts = row["game_id"].split("_")

        away_team = parts[2]
        home_team = parts[3]

        if row["pick"] == away_team:
            return home_team

        if row["pick"] == home_team:
            return away_team

        return None

    df["opponent"] = df.apply(
        get_opponent,
        axis=1,
    )

    # --------------------------------------------------
    # Count times each team was picked
    # --------------------------------------------------

    picked = (
        df.groupby("pick")
        .size()
        .reset_index(
            name="Picked"
        )
        .rename(
            columns={
                "pick": "Team",
            }
        )
    )

    # --------------------------------------------------
    # Count times each team was picked against
    # --------------------------------------------------

    picked_against = (
        df.groupby("opponent")
        .size()
        .reset_index(
            name="Picked Against"
        )
        .rename(
            columns={
                "opponent": "Team",
            }
        )
    )

    # --------------------------------------------------
    # All 32 NFL teams
    # --------------------------------------------------

    nfl_teams = [
        "ARI", "ATL", "BAL", "BUF",
        "CAR", "CHI", "CIN", "CLE",
        "DAL", "DEN", "DET", "GB",
        "HOU", "IND", "JAX", "KC",
        "LV", "LAC", "LA", "MIA",
        "MIN", "NE", "NO", "NYG",
        "NYJ", "PHI", "PIT", "SEA",
        "SF", "TB", "TEN", "WAS",
    ]

    result = pd.DataFrame(
        {
            "Team": nfl_teams
        }
    )

    # --------------------------------------------------
    # Combine results
    # --------------------------------------------------

    result = result.merge(
        picked,
        on="Team",
        how="left",
    )

    result = result.merge(
        picked_against,
        on="Team",
        how="left",
    )

    result["Picked"] = (
        result["Picked"]
        .fillna(0)
        .astype(int)
    )

    result["Picked Against"] = (
        result["Picked Against"]
        .fillna(0)
        .astype(int)
    )

    # --------------------------------------------------
    # Calculate trust and fade rates
    # --------------------------------------------------

    result["Total Decisions"] = (
        result["Picked"]
        + result["Picked Against"]
    )

    result["Trust Rate"] = (
        result["Picked"]
        / result["Total Decisions"]
    )

    result["Fade Rate"] = (
        result["Picked Against"]
        / result["Total Decisions"]
    )

    # Format percentages.
    result["Trust Rate"] = (
        result["Trust Rate"]
        .map(
            lambda value: (
                f"{value:.1%}"
                if pd.notna(value)
                else "—"
            )
        )
    )

    result["Fade Rate"] = (
        result["Fade Rate"]
        .map(
            lambda value: (
                f"{value:.1%}"
                if pd.notna(value)
                else "—"
            )
        )
    )

    # We don't need Total Decisions in the final table.
    result = result.drop(
        columns="Total Decisions"
    )

    # Sort by teams picked against most often.
    result = result.sort_values(
        by=[
            "Picked Against",
            "Picked",
        ],
        ascending=[
            False,
            True,
        ],
    )

    print(
        "\nTEAM TRUST — WEEKS 1-3"
    )
    print("=" * 70)

    print(
        result.to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()