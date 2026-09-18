import streamlit as st

from analysis.pickem_analyzer import (
    overall_standings,
    weekly_results,
)

from analysis.data_pipeline import (
    build_master_results_from_supabase,
)



st.title("Standings")

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
            "Correct": "Correct",
            "Incorrect": "Incorrect",
            "Picks": "Picks",
            "Win_Pct": "Win %",
            "Confidence_Points": "Confidence Points",
            "Confidence_Risked": "Confidence Risked",
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
            "Correct": "Correct",
            "Incorrect": "Incorrect",
            "Picks": "Picks",
            "Win_Pct": "Win %",
            "Confidence_Points": "Confidence Points",
            "Weekly_Rank": "Rank",
        }
    )

    column_order = [
        column
        for column in [
            "Rank",
            "Player",
            "Correct",
            "Incorrect",
            "Picks",
            "Win %",
            "Confidence Points",
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