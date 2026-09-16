import streamlit as st
import pandas as pd

from analysis.data_pipeline import (
    save_master_results_from_supabase,
)

from analysis.database import (
    load_picks,
    upsert_picks,
)

from analysis.nfl_results import (
    fetch_week_results,
)


if not st.session_state.get(
    "admin_authenticated",
    False,
):
    st.error(
        "Admin access required."
    )
    st.stop()


st.title("Admin")

st.write(
    "Enter and manage player picks, then refresh NFL results."
)

st.subheader("NFL Results")

st.write(
    "Fetch the latest NFL results and rebuild "
    "the master analytics dataset."
)

if st.button(
    "Refresh NFL Results",
    type="primary",
):
    try:
        refreshed = save_master_results_from_supabase()

        st.success(
            "NFL results refreshed successfully."
        )

        st.write(
            f"{len(refreshed)} pick records "
            f"are now in the master dataset."
        )

    except Exception as error:
        st.error(
            f"Could not refresh NFL results: "
            f"{error}"
        )

st.divider()


st.subheader("Pick Entry Setup")


season = st.selectbox(
    "Season",
    options=[2026],
)


week = st.selectbox(
    "Week",
    options=list(range(1, 19)),
)


PLAYERS = [
    "Jimmy",
    "John",
    "Jesse",
]


player = st.selectbox(
    "Player",
    options=PLAYERS,
)


st.divider()


st.subheader(
    f"{player} — {season} Week {week}"
)

try:
    schedule = fetch_week_results(
        season=season,
        week=week,
    )

except Exception as error:
    st.error(
        f"Could not load NFL schedule: {error}"
    )
    st.stop()


st.write(
    f"{len(schedule)} games found."
)

existing_player_picks = {}

try:

    existing_df = load_picks()

    player_existing = existing_df[
        (existing_df["season"] == season)
        & (existing_df["week"] == week)
        & (existing_df["player"] == player)
    ].copy()

    for _, row in player_existing.iterrows():

        existing_player_picks[
            row["game_id"]
        ] = {
            "picked_team": row["pick"],
            "confidence": int(
                row["confidence"]
            ),
        }

except Exception as error:

    st.error(
        f"Could not load existing picks: "
        f"{error}"
    )

    st.stop()

submitted_picks = []


with st.form("pick_entry_form"):

    for index, game in schedule.iterrows():

        away_team = game["away_team"]
        home_team = game["home_team"]

        # Look for an existing pick for this game
        existing_pick = (
            existing_player_picks.get(
                game["game_id"],
                {},
            )
        )

        existing_team = existing_pick.get(
            "picked_team",
            "",
        )

        existing_confidence = (
            existing_pick.get(
                "confidence",
                "",
            )
        )

        st.markdown(
            f"### {away_team} @ {home_team}"
        )

        col1, col2 = st.columns(2)

        # -----------------------------
        # Pick
        # -----------------------------

        with col1:

            pick_options = [
                "",
                away_team,
                home_team,
            ]

            pick_index = (
                pick_options.index(
                    existing_team
                )
                if existing_team
                in pick_options
                else 0
            )

            picked_team = st.selectbox(
                "Pick",
                options=pick_options,
                index=pick_index,
                key=(
                    f"pick_"
                    f"{season}_"
                    f"{week}_"
                    f"{player}_"
                    f"{game['game_id']}"
                ),
            )

        # -----------------------------
        # Confidence
        # -----------------------------

        with col2:

            confidence_options = [
                ""
            ] + list(
                range(
                    1,
                    len(schedule) + 1,
                )
            )

            confidence_index = (
                confidence_options.index(
                    existing_confidence
                )
                if existing_confidence
                in confidence_options
                else 0
            )

            confidence = st.selectbox(
                "Confidence",
                options=confidence_options,
                index=confidence_index,
                key=(
                    f"confidence_"
                    f"{season}_"
                    f"{week}_"
                    f"{player}_"
                    f"{game['game_id']}"
                ),
            )

        # Store the values currently
        # shown in the form
        submitted_picks.append(
            {
                "season": season,
                "week": week,
                "player": player,
                "game_id": game["game_id"],
                "away_team": away_team,
                "home_team": home_team,
                "picked_team": picked_team,
                "confidence": confidence,
            }
        )

        st.divider()


    submitted = st.form_submit_button(
        "Validate Picks"
    )

if submitted:

    entered_picks = [
        pick
        for pick in submitted_picks
        if (
            pick["picked_team"] != ""
            or pick["confidence"] != ""
        )
    ]

    errors = []


    for pick in entered_picks:

        if (
            pick["picked_team"] == ""
            and pick["confidence"] != ""
        ):
            errors.append(
                f"{pick['away_team']} @ "
                f"{pick['home_team']}: "
                f"confidence entered without a pick."
            )

        if (
            pick["picked_team"] != ""
            and pick["confidence"] == ""
        ):
            errors.append(
                f"{pick['away_team']} @ "
                f"{pick['home_team']}: "
                f"pick entered without confidence."
            )


    confidence_values = [
        pick["confidence"]
        for pick in entered_picks
        if pick["confidence"] != ""
    ]

    duplicate_confidence = {
        value
        for value in confidence_values
        if confidence_values.count(value) > 1
    }

    if duplicate_confidence:
        errors.append(
            "Duplicate confidence values found: "
            + ", ".join(
                str(value)
                for value in sorted(
                    duplicate_confidence
                )
            )
        )


    if errors:

        st.error(
            "Please fix the following:"
        )

        for error in errors:
            st.write(
                f"- {error}"
            )

    elif not entered_picks:

        st.warning(
            "No picks were entered."
        )

    else:

        st.success(
            f"{len(entered_picks)} picks "
            f"validated successfully."
        )

        entered_df = pd.DataFrame(
            entered_picks
        )

        st.dataframe(
            entered_df,
            use_container_width=True,
            hide_index=True,
        )

        destination_file = (
            f"data/picks/"
            f"{season}_week_{week:02d}.csv"
        )

        try:

            saved_picks = upsert_picks(
                entered_df
            )

            st.success(
                "Picks saved successfully "
                "to Supabase."
            )

            st.write(
                f"{len(saved_picks)} picks "
                f"were saved."
            )

        except Exception as error:

            st.error(
                f"Could not save picks: {error}"
            )