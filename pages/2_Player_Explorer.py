import streamlit as st

from analysis.pickem_analyzer import (
    load_results,
)
from analysis.player_explorer import (
    get_player_explorer,
)


DATA_FILE = "data/picks_results.csv"


st.title("NFL Pick'em Player Explorer")

st.write(
    "Explore player performance, confidence results, "
    "team tendencies, and weekly performance."
)

try:
    df = load_results(
        DATA_FILE
    )

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
    "Win Percentage",
    win_pct,
)

col3.metric(
    "Confidence Points",
    overview["Confidence_Points"],
)

col4.metric(
    "Confidence Risked",
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

st.subheader("Key Insights")

highest_correct = explorer[
    "highest_confidence_correct"
]

highest_miss = explorer[
    "highest_confidence_miss"
]

insight_col1, insight_col2 = st.columns(2)

with insight_col1:
    st.markdown(
        "#### Highest-Confidence Correct Pick"
    )

    if highest_correct is None:
        st.write(
            "No completed correct picks yet."
        )
    else:
        st.write(
            f"{highest_correct['team']} vs "
            f"{highest_correct['opponent']}"
        )

        st.write(
            f"Confidence: "
            f"{highest_correct['confidence']}"
        )

        st.write(
            f"Week: "
            f"{highest_correct['week']}"
        )

with insight_col2:
    st.markdown(
        "#### Highest-Confidence Miss"
    )

    if highest_miss is None:
        st.write(
            "No completed missed picks yet."
        )
    else:
        st.write(
            f"{highest_miss['team']} vs "
            f"{highest_miss['opponent']}"
        )

        st.write(
            f"Confidence: "
            f"{highest_miss['confidence']}"
        )

        st.write(
            f"Week: "
            f"{highest_miss['week']}"
        )

st.subheader("Weekly Results")

weekly = explorer["weekly"]

if weekly.empty:
    st.info(
        "No completed weekly results yet."
    )
else:
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
    st.dataframe(
        home_away,
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Team Records")

teams = explorer["teams"]

if teams.empty:
    st.info(
        "No completed team results yet."
    )
else:
    st.dataframe(
        teams,
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
    st.dataframe(
        opponents,
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
    st.dataframe(
        confidence,
        use_container_width=True,
        hide_index=True,
    )