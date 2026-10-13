import streamlit as st

import pandas as pd

from analysis.data_pipeline import (
    build_master_results_from_supabase,
)
from analysis.player_explorer import (
    get_division_records,
    get_opponent_division_records,
    get_player_explorer,
)


st.title("NFL Pick'em Player Explorer")

st.write(
    "Explore player performance, confidence results, "
    "team tendencies, and weekly performance."
)

try:
    df = build_master_results_from_supabase()

except Exception as error:
    st.error(
        f"Could not load results: {error}"
    )

    st.stop()

if df.empty:
    st.warning(
        "No pick results are available yet."
    )

    st.stop()

players = sorted(
    df["player"]
    .dropna()
    .unique()
)

selected_player = st.selectbox(
    "Select Player",
    players,
)

try:
    explorer = get_player_explorer(
        df,
        selected_player,
    )

except Exception as error:
    st.error(
        f"Could not build Player Explorer: {error}"
    )

    st.stop()

overview = explorer["overview"]

st.subheader("Overview")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Record",
    overview["Record"],
)

win_pct = (
    f"{overview['Win_Pct']:.1%}"
    if overview["Win_Pct"] is not None
    else "N/A"
)

col2.metric(
    "Win %",
    win_pct,
)

col3.metric(
    "Points Earned",
    overview["Confidence_Points"],
)

col4.metric(
    "Points Risked",
    overview["Confidence_Risked"],
)

point_efficiency = (
    f"{overview['Point_Efficiency']:.1%}"
    if overview["Point_Efficiency"] is not None
    else "N/A"
)

col5.metric(
    "Point Efficiency",
    point_efficiency,
)

status = explorer["status"]

st.subheader("Current Status")

status_col1, status_col2, status_col3 = st.columns(3)

status_col1.metric(
    "Picks Loaded",
    status["total_picks"],
)

status_col2.metric(
    "Completed",
    status["completed_picks"],
)

status_col3.metric(
    "Pending",
    status["remaining_picks"],
)

st.subheader("Weekly Results")

weekly = explorer["weekly"]

if weekly.empty:
    st.info(
        "No completed weekly results yet."
    )
else:

    weekly = explorer["weekly"].copy()

    weekly["Record"] = (
        weekly["Correct"].astype(str)
        + "-"
        + weekly["Incorrect"].astype(str)
    )

    weekly["Win %"] = (
        weekly["Win_Pct"]
        .map(lambda value: f"{value:.1%}")
    )

    weekly["Point Efficiency"] = (
        weekly["Point_Efficiency"]
        .map(lambda value: f"{value:.1%}")
    )

    weekly = weekly[
        [
            "week",
            "Record",
            "Win %",
            "Confidence_Points",
            "Confidence_Risked",
            "Point Efficiency",
        ]
    ].rename(
        columns={
            "week": "Week",
            "Confidence_Points": "Points Earned",
            "Confidence_Risked": "Points Risked",
        }
    )

    st.dataframe(
        weekly,
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Home vs Away")

home_away = explorer["home_away"]

if home_away.empty:
    st.info(
        "No completed home/away results yet."
    )

else:
    display_home_away = home_away.copy()

    display_home_away["Record"] = (
        display_home_away["Correct"].astype(str)
        + "-"
        + display_home_away["Incorrect"].astype(str)
    )

    display_home_away["Win_Pct"] = (
        display_home_away["Win_Pct"]
        .map(
            lambda value: f"{value:.1%}"
        )
    )

    display_home_away = (
        display_home_away[
            [
                "pick_location",
                "Record",
                "Win_Pct",
                "Avg_Confidence",
                "Confidence_Points",
            ]
        ]
        .rename(
            columns={
                "pick_location": "Location",
                "Win_Pct": "Win %",
                "Avg_Confidence": "Avg Confidence Risked",
                "Confidence_Points": "Points Earned",
            }
        )
    )

    st.dataframe(
        display_home_away,
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Record When Picking Team")

teams = explorer["teams"]

if teams.empty:
    st.info(
        "No completed team results yet."
    )
else:
    division_records = get_division_records(
        teams
    )

    for division in division_records:

        division_name = division["Division"]
        wins = division["Correct"]
        losses = division["Incorrect"]
        win_pct = division["Win_Pct"]

        expander_label = (
            f"{division_name} — "
            f"{wins}-{losses} "
            f"({win_pct:.1%})"
        )

        with st.expander(expander_label):

            division_teams = (
                division["Teams"].copy()
            )

            display_teams = division_teams[
                [
                    "picked_team",
                    "Correct",
                    "Incorrect",
                    "Avg_Confidence",
                    "Point_Efficiency",
                ]
            ].copy()

            display_teams["Record"] = (
                display_teams["Correct"]
                .astype(str)
                + "-"
                + display_teams["Incorrect"]
                .astype(str)
            )

            display_teams["Avg Confidence Risked"] = (
                display_teams["Avg_Confidence"]
                .map(
                    lambda value:
                    f"{value:.1f}"
                )
            )

            display_teams["Point Efficiency"] = (
                display_teams["Point_Efficiency"]
                .map(
                    lambda value:
                    f"{value:.1%}"
                )
            )

            display_teams = (
                display_teams[
                    [
                        "picked_team",
                        "Record",
                        "Avg Confidence Risked",
                        "Point Efficiency",
                    ]
                ]
                .rename(
                    columns={
                        "picked_team": "Team",
                    }
                )
            )

            st.dataframe(
                display_teams,
                use_container_width=True,
                hide_index=True,
            )

st.subheader(
    "Record When Picking Against Team"
)

opponents = explorer["opponents"]

if opponents.empty:
    st.info(
        "No completed opponent results yet."
    )
else:
    opponent_division_records = (
        get_opponent_division_records(
            opponents
        )
    )

    for division in opponent_division_records:

        division_name = division["Division"]
        wins = division["Correct"]
        losses = division["Incorrect"]
        win_pct = division["Win_Pct"]

        expander_label = (
            f"{division_name} — "
            f"{wins}-{losses} "
            f"({win_pct:.1%})"
        )

        with st.expander(expander_label):

            division_teams = (
                division["Teams"].copy()
            )

            display_teams = division_teams[
                [
                    "opponent",
                    "Correct",
                    "Incorrect",
                    "Avg_Confidence",
                    "Point_Efficiency",
                ]
            ].copy()

            display_teams["Record"] = (
                display_teams["Correct"]
                .astype(str)
                + "-"
                + display_teams["Incorrect"]
                .astype(str)
            )

            display_teams["Avg Confidence Risked"] = (
                display_teams["Avg_Confidence"]
                .map(
                    lambda value:
                    f"{value:.1f}"
                )
            )

            display_teams["Point Efficiency"] = (
                display_teams["Point_Efficiency"]
                .map(
                    lambda value:
                    f"{value:.1%}"
                )
            )

            display_teams = (
                display_teams[
                    [
                        "opponent",
                        "Record",
                        "Avg Confidence Risked",
                        "Point Efficiency",
                    ]
                ]
                .rename(
                    columns={
                        "opponent": "Team",
                    }
                )
            )

            st.dataframe(
                display_teams,
                use_container_width=True,
                hide_index=True,
            )

st.subheader("Confidence Performance")

confidence = explorer["confidence"]

if confidence.empty:
    st.info(
        "No completed confidence results yet."
    )

else:
    display_confidence = confidence.copy()

    display_confidence["Record"] = (
        display_confidence["Correct"].astype(str)
        + "-"
        + display_confidence["Incorrect"].astype(str)
    )

    display_confidence["Win_Pct"] = (
        display_confidence["Win_Pct"]
        .map(
            lambda value: f"{value:.1%}"
        )
    )

    display_confidence = (
        display_confidence[
            [
                "Confidence_Band",
                "Record",
                "Win_Pct",
                "Avg_Confidence",
                "Confidence_Points",
            ]
        ]
        .rename(
            columns={
                "Confidence_Band": "Confidence Band",
                "Win_Pct": "Win %",
                "Avg_Confidence": "Avg Confidence Risked",
                "Confidence_Points": "Points Earned",
            }
        )
    )

    st.dataframe(
        display_confidence,
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Confidence Level Performance")

confidence_levels = explorer["confidence_levels"]

if confidence_levels.empty:
    st.info("No completed confidence level results yet.")

else:
    # Sort from highest to lowest confidence.
    confidence_levels = confidence_levels.sort_values(
        "confidence",
        ascending=False,
    ).copy()

    st.write(
        "Win percentage at each individual confidence "
        "level, from highest to lowest."
    )

    chart_data = confidence_levels[
        ["confidence", "Win_Pct"]
    ].copy()

    chart_data["Confidence Level"] = pd.Categorical(
        chart_data["confidence"].astype(str),
        categories=[str(i) for i in range(1, 17)],
        ordered=True,
    )

    chart_data = chart_data.sort_values("Confidence Level")

    chart_data["Win %"] = (
        chart_data["Win_Pct"] * 100
    )

    chart_data = chart_data.set_index(
        "Confidence Level"
    )

    st.line_chart(
        chart_data["Win %"],
        x_label="Confidence Level",
        y_label="Win Percentage (%)",
    )

    st.markdown("#### Weekly Confidence Results")

    player_picks = df[
        df["player"].str.lower() == selected_player.lower()
    ].copy()

    def pick_result_symbol(row):
        if not row["game_completed"]:
            return " "

        if row["is_tie"]:
            return "➖"

        if row["pick_correct"] == True:
            return "✅"

        if row["pick_correct"] == False:
            return "❌"

        return " "

    player_picks["Result"] = player_picks.apply(
        pick_result_symbol,
        axis=1,
    )

    confidence_matrix = player_picks.pivot_table(
        index="confidence",
        columns="week",
        values="Result",
        aggfunc="first",
    )

    confidence_matrix = confidence_matrix.reindex(
        range(1, 17)
    )

    confidence_matrix = confidence_matrix.reindex(
        sorted(df["week"].dropna().unique()),
        axis=1,
    )

    confidence_matrix.columns = [
        f"Week {int(week)}"
        for week in confidence_matrix.columns
    ]

    st.dataframe(
        confidence_matrix.fillna(""),
        use_container_width=True,
        hide_index=False,
    )