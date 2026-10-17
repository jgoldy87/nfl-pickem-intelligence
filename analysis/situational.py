from pathlib import Path

import nflreadpy as nfl
import pandas as pd


def load_pbp_data(season):
    """
    Load regular-season play-by-play data.

    Uses a locally cached parquet file when available.
    Otherwise downloads the data from nflverse and
    saves it locally for future use.
    """

    cache_dir = Path("data")
    cache_dir.mkdir(exist_ok=True)

    cache_file = cache_dir / f"pbp_{season}.parquet"

    # --------------------------------------------------
    # USE LOCAL CACHE IF AVAILABLE
    # --------------------------------------------------

    if cache_file.exists():

        print(
            f"Loading {season} play-by-play "
            "from local cache..."
        )

        return pd.read_parquet(
            cache_file
        )


    # --------------------------------------------------
    # DOWNLOAD FROM NFLVERSE
    # --------------------------------------------------

    print(
        f"Downloading {season} play-by-play "
        "from nflverse..."
    )

    pbp = nfl.load_pbp(
        seasons=season
    ).to_pandas()

    pbp = pbp[
        pbp["season_type"] == "REG"
    ].copy()


    # --------------------------------------------------
    # SAVE LOCAL CACHE
    # --------------------------------------------------

    pbp.to_parquet(
        cache_file,
        index=False,
    )

    print(
        f"Saved play-by-play cache: "
        f"{cache_file}"
    )

    return pbp

def refresh_pbp_data(season):
    """
    Download fresh play-by-play data for a season
    and replace the local cache.
    """

    cache_path = Path("data") / f"pbp_{season}.parquet"

    print(
        f"Refreshing {season} play-by-play from nflverse..."
    )

    pbp = nfl.load_pbp(
        seasons=season
    ).to_pandas()

    cache_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pbp.to_parquet(
        cache_path,
        index=False,
    )

    print(
        f"Updated play-by-play cache: {cache_path}"
    )

    return pbp

def load_third_down_stats(pbp):
    """
    Calculate team third-down attempts and conversions
    for each regular-season game.
    """

    # --------------------------------------------------
    # IDENTIFY OFFICIAL THIRD-DOWN ATTEMPTS
    # --------------------------------------------------

    third_downs = pbp[
        (pbp["down"] == 3)
        & (
            (pbp["third_down_converted"] == 1)
            | (pbp["third_down_failed"] == 1)
        )
    ].copy()


    # --------------------------------------------------
    # OFFENSIVE THIRD-DOWN STATS
    # --------------------------------------------------

    offense = (
        third_downs
        .groupby(
            ["game_id", "posteam"],
            as_index=False,
        )
        .agg(
            third_down_attempts=(
                "third_down_converted",
                "size",
            ),
            third_down_conversions=(
                "third_down_converted",
                "sum",
            ),
        )
        .rename(
            columns={
                "posteam": "team",
            }
        )
    )


    # --------------------------------------------------
    # DEFENSIVE THIRD-DOWN STATS
    # --------------------------------------------------

    defense = (
        third_downs
        .groupby(
            ["game_id", "defteam"],
            as_index=False,
        )
        .agg(
            opponent_third_down_attempts=(
                "third_down_converted",
                "size",
            ),
            opponent_third_down_conversions=(
                "third_down_converted",
                "sum",
            ),
        )
        .rename(
            columns={
                "defteam": "team",
            }
        )
    )


    # --------------------------------------------------
    # COMBINE OFFENSE + DEFENSE
    # --------------------------------------------------

    third_down_stats = offense.merge(
        defense,
        on=["game_id", "team"],
        how="outer",
    )


    return third_down_stats

def load_red_zone_stats(pbp):
    """
    Calculate red-zone opportunities and touchdowns
    by team and game.

    A red-zone opportunity is a drive where
    drive_inside20 == 1.
    """

    # --------------------------------------------------
    # RED-ZONE DRIVES
    # --------------------------------------------------

    red_zone = pbp[
        (pbp["drive_inside20"] == 1)
        & pbp["posteam"].notna()
        & pbp["defteam"].notna()
        & pbp["drive"].notna()
    ].copy()


    # --------------------------------------------------
    # IDENTIFY WHETHER OFFENSE SCORED A TD
    # --------------------------------------------------

    red_zone["offensive_td"] = (
        (red_zone["touchdown"] == 1)
        & (red_zone["td_team"] == red_zone["posteam"])
    ).astype(int)


    # --------------------------------------------------
    # COLLAPSE TO ONE ROW PER DRIVE
    # --------------------------------------------------

    drives = (
        red_zone
        .groupby(
            [
                "game_id",
                "drive",
                "posteam",
                "defteam",
            ],
            as_index=False,
        )
        .agg(
            red_zone_td=(
                "offensive_td",
                "max",
            )
        )
    )


    # --------------------------------------------------
    # OFFENSIVE RED-ZONE STATS
    # --------------------------------------------------

    offense = (
        drives
        .groupby(
            ["game_id", "posteam"],
            as_index=False,
        )
        .agg(
            red_zone_attempts=(
                "drive",
                "count",
            ),
            red_zone_tds=(
                "red_zone_td",
                "sum",
            ),
        )
        .rename(
            columns={
                "posteam": "team",
            }
        )
    )


    # --------------------------------------------------
    # DEFENSIVE RED-ZONE STATS
    # --------------------------------------------------

    defense = (
        drives
        .groupby(
            ["game_id", "defteam"],
            as_index=False,
        )
        .agg(
            opponent_red_zone_attempts=(
                "drive",
                "count",
            ),
            opponent_red_zone_tds=(
                "red_zone_td",
                "sum",
            ),
        )
        .rename(
            columns={
                "defteam": "team",
            }
        )
    )


    # --------------------------------------------------
    # COMBINE OFFENSE + DEFENSE
    # --------------------------------------------------

    red_zone_stats = offense.merge(
        defense,
        on=["game_id", "team"],
        how="outer",
    )


    return red_zone_stats