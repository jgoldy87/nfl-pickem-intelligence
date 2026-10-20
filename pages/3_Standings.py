import streamlit as st

from analysis.pickem_analyzer import (
    overall_standings,
    weekly_results,
)

from analysis.data_pipeline import (
    build_master_results_from_supabase,
)

from analysis.nfl_standings import (
    DIVISIONS,
    load_nfl_standings,
    get_division_standings,
)

st.title("Standings")

pool_tab, nfl_tab = st.tabs([
    "Confidence Pool",
    "NFL Standings",
])

with pool_tab:
    # Your existing page content goes here.

    st.write(
        "Track overall and weekly performance "
        "across the Pick'em pool."
    )


    # --------------------------------------------------
    # Load results
    # --------------------------------------------------

    try:
        df = build_master_results_from_supabase()

    except Exception as error:
        st.error(
            f"Could not load results: {error}"
        )
        st.stop()


    # --------------------------------------------------
    # Season selector
    # --------------------------------------------------

    seasons = sorted(
        df["season"]
        .dropna()
        .unique(),
        reverse=True,
    )

    selected_season = st.selectbox(
        "Season",
        seasons,
    )


    season_df = df[
        df["season"]
        == selected_season
    ].copy()


    # --------------------------------------------------
    # Overall standings
    # --------------------------------------------------

    st.subheader("Overall Standings")


    overall = overall_standings(
        season_df
    )


    if overall.empty:

        st.info(
            "No completed games are available "
            "for the overall standings yet."
        )

    else:

        display_overall = overall.copy()

        display_overall["Record"] = (
            display_overall["Correct"].astype(str)
            + "-"
            + display_overall["Incorrect"].astype(str)
        )

        if "Win_Pct" in display_overall.columns:
            display_overall["Win_Pct"] = (
                display_overall["Win_Pct"]
                .map(
                    lambda value: (
                        f"{value:.1%}"
                        if value is not None
                        else "N/A"
                    )
                )
            )

        if "Point_Efficiency" in display_overall.columns:
            display_overall["Point_Efficiency"] = (
                display_overall["Point_Efficiency"]
                .map(
                    lambda value: (
                        f"{value:.1%}"
                        if value is not None
                        else "N/A"
                    )
                )
            )

        display_overall = display_overall.rename(
            columns={
                "player": "Player",
                "Win_Pct": "Win %",
                "Confidence_Points": "Points Earned",
                "Confidence_Risked": "Points Risked",
                "Point_Efficiency": "Point Efficiency",
            }
        )

        display_overall.insert(
            0,
            "Rank",
            range(
                1,
                len(display_overall) + 1,
            ),
        )

        column_order = [
            column
            for column in [
                "Rank",
                "Player",
                "Record",
                "Win %",
                "Points Earned",
                "Points Risked",
                "Point Efficiency",
            ]
            if column in display_overall.columns
        ]

        display_overall = display_overall[
            column_order
        ]

        st.dataframe(
            display_overall,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("Weekly Standings")


    weeks = sorted(
        season_df["week"]
        .dropna()
        .unique()
    )


    selected_week = st.selectbox(
        "Week",
        weeks,
    )


    all_weekly = weekly_results(
        season_df
    )


    week_table = all_weekly[
        all_weekly["week"]
        == selected_week
    ].copy()


    if week_table.empty:

        st.info(
            f"No completed results are available "
            f"for Week {selected_week} yet."
        )

    else:

        display_week = week_table.copy()

        display_week["Record"] = (
            display_week["Correct"].astype(str)
            + "-"
            + display_week["Incorrect"].astype(str)
        )

        if "Win_Pct" in display_week.columns:
            display_week["Win_Pct"] = (
                display_week["Win_Pct"]
                .map(
                    lambda value: (
                        f"{value:.1%}"
                        if value is not None
                        else "N/A"
                    )
                )
            )

        display_week = display_week.rename(
            columns={
                "player": "Player",
                "Win_Pct": "Win %",
                "Confidence_Points": "Points Earned",
                "Confidence_Risked": "Points Risked",
                "Weekly_Rank": "Rank",
            }
        )

        column_order = [
            column
            for column in [
                "Rank",
                "Player",
                "Record",
                "Win %",
                "Points Earned",
            ]
            if column in display_week.columns
        ]

        display_week = display_week[
            column_order
        ]

        st.dataframe(
            display_week,
            use_container_width=True,
            hide_index=True,
        )


with nfl_tab:
    st.subheader("NFL Standings")

    nfl_season = st.selectbox(
        "NFL Season",
        options=[2026, 2025, 2024],
        index=0,
        key="nfl_standings_season",
    )

    try:
        with st.spinner("Loading NFL standings..."):
            nfl_df = load_nfl_standings(nfl_season)

    except Exception as error:
        st.error(
            f"Unable to load NFL standings: {error}"
        )
        st.info(
            "The ESPN standings service may be "
            "temporarily unavailable."
        )

    else:
        st.caption(
            "Standings provided by ESPN. "
            "Updated approximately every 30 minutes."
        )

        afc_tab, nfc_tab = st.tabs([
            "AFC",
            "NFC",
        ])

        for conference, conference_tab in [
            ("AFC", afc_tab),
            ("NFC", nfc_tab),
        ]:
            with conference_tab:
                for division in DIVISIONS:
                    if not division.startswith(conference):
                        continue

                    st.markdown(f"#### {division}")

                    table = get_division_standings(
                        nfl_df,
                        division,
                    )

                    st.dataframe(
                        table,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "PCT": st.column_config.NumberColumn(
                                "PCT",
                                format="%.3f",
                            ),
                        },
                    )
