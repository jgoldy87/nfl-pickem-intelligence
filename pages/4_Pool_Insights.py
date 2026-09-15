import streamlit as st

from analysis.pickem_analyzer import (
    load_results,
    pool_game_results,
    lone_wolf_picks,
    lone_wolf_performance,
    unanimous_picks,
    collective_disasters,
    player_agreement,
)


DATA_FILE = "data/picks_results.csv"


st.title("Pool Insights")

st.write(
    "Analyze how the entire pool performed "
    "across games and weeks."
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
    st.info(
        "No pick results are available yet."
    )
    st.stop()


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

available_weeks = sorted(
    season_df["week"]
    .dropna()
    .unique()
)

view_options = [
    "Full Season"
] + [
    f"Week {int(week)}"
    for week in available_weeks
]

selected_view = st.selectbox(
    "View",
    options=view_options,
)

if selected_view == "Full Season":

    filtered_df = season_df.copy()

else:

    selected_week = int(
        selected_view.replace(
            "Week ",
            ""
        )
    )

    filtered_df = season_df[
        season_df["week"]
        == selected_week
    ].copy()

game_results = pool_game_results(
    filtered_df
)

game_tab, behavior_tab, comparison_tab = st.tabs(
    [
        "Game Insights",
        "Pick Behavior",
        "Player Comparisons",
    ]
)

with game_tab:

    st.subheader("Hardest Games for the Pool")


    if game_results.empty:

        st.info(
            "No completed pool results are "
            "available yet."
        )

    else:

        hardest_games = (
            game_results
            .sort_values(
                by=[
                    "Pool_Accuracy",
                    "Avg_Confidence",
                ],
                ascending=[
                    True,
                    False,
                ],
            )
            .copy()
        )

        hardest_games["Matchup"] = (
            hardest_games["away_team"]
            + " @ "
            + hardest_games["home_team"]
        )

        hardest_games["Pool_Accuracy"] = (
            hardest_games["Pool_Accuracy"]
            .map(
                lambda value: f"{value:.1%}"
            )
        )

        display_hardest = hardest_games[
            [
                "week",
                "Matchup",
                "winner",
                "Correct",
                "Incorrect",
                "Picks",
                "Pool_Accuracy",
                "Avg_Confidence",
            ]
        ].rename(
            columns={
                "week": "Week",
                "winner": "Winner",
                "Pool_Accuracy": "Pool Accuracy",
                "Avg_Confidence": "Avg Confidence",
            }
        )

        st.dataframe(
            display_hardest,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("Easiest Games for the Pool")


    if game_results.empty:

        st.info(
            "No completed pool results are "
            "available yet."
        )

    else:

        easiest_games = (
            game_results
            .sort_values(
                by=[
                    "Pool_Accuracy",
                    "Avg_Confidence",
                ],
                ascending=[
                    False,
                    False,
                ],
            )
            .copy()
        )

        easiest_games["Matchup"] = (
            easiest_games["away_team"]
            + " @ "
            + easiest_games["home_team"]
        )

        easiest_games["Pool_Accuracy"] = (
            easiest_games["Pool_Accuracy"]
            .map(
                lambda value: f"{value:.1%}"
            )
        )

        display_easiest = easiest_games[
            [
                "week",
                "Matchup",
                "winner",
                "Correct",
                "Incorrect",
                "Picks",
                "Pool_Accuracy",
                "Avg_Confidence",
            ]
        ].rename(
            columns={
                "week": "Week",
                "winner": "Winner",
                "Pool_Accuracy": "Pool Accuracy",
                "Avg_Confidence": "Avg Confidence",
            }
        )

        st.dataframe(
            display_easiest,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("Collective Disasters")


    disasters = collective_disasters(
        filtered_df
    )


    if disasters.empty:

        st.info(
            "No collective disasters are available yet."
        )

    else:

        display_disasters = disasters.copy()

        display_disasters["Matchup"] = (
            display_disasters["away_team"]
            + " @ "
            + display_disasters["home_team"]
        )

        display_disasters["Avg_Confidence"] = (
            display_disasters["Avg_Confidence"]
            .round(1)
        )

        display_disasters = (
            display_disasters[
                [
                    "week",
                    "Matchup",
                    "Unanimous_Pick",
                    "winner",
                    "Total_Confidence",
                    "Avg_Confidence",
                ]
            ]
            .rename(
                columns={
                    "week": "Week",
                    "Unanimous_Pick": "Pool Pick",
                    "winner": "Winner",
                    "Total_Confidence": "Confidence Lost",
                    "Avg_Confidence": "Avg Confidence",
                }
            )
        )

        st.dataframe(
            display_disasters,
            use_container_width=True,
            hide_index=True,
        )

with behavior_tab:

    st.subheader("Lone Wolf Performance")


    lone_wolf_summary = lone_wolf_performance(
        filtered_df
    )


    if lone_wolf_summary.empty:

        st.info(
            "No Lone Wolf performance is "
            "available yet."
        )

    else:

        display_summary = (
            lone_wolf_summary.copy()
        )

        display_summary["Win_Pct"] = (
            display_summary["Win_Pct"]
            .map(
                lambda value: (
                    f"{value:.1%}"
                )
            )
        )

        display_summary = (
            display_summary.rename(
                columns={
                    "Lone_Wolf": "Player",
                    "Win_Pct": "Win %",
                }
            )
        )

        st.dataframe(
            display_summary,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("Lone Wolf Picks")


    lone_wolves = lone_wolf_picks(
        filtered_df
    )


    if lone_wolves.empty:

        st.info(
            "No Lone Wolf picks are available yet."
        )

    else:

        display_lone_wolves = lone_wolves.copy()

        display_lone_wolves["Matchup"] = (
            display_lone_wolves["away_team"]
            + " @ "
            + display_lone_wolves["home_team"]
        )

        display_lone_wolves["Result"] = (
            display_lone_wolves["Correct"]
            .map(
                {
                    True: "Correct",
                    False: "Incorrect",
                }
            )
        )

        display_lone_wolves = display_lone_wolves[
            [
                "week",
                "Matchup",
                "Lone_Wolf",
                "Lone_Pick",
                "Majority_Pick",
                "Confidence",
                "Result",
            ]
        ].rename(
            columns={
                "week": "Week",
                "Lone_Wolf": "Lone Wolf",
                "Lone_Pick": "Lone Pick",
                "Majority_Pick": "Majority Pick",
            }
        )

        st.dataframe(
            display_lone_wolves,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("Unanimous Picks")


    unanimous = unanimous_picks(
        filtered_df
    )


    if unanimous.empty:

        st.info(
            "No unanimous picks are available yet."
        )

    else:

        display_unanimous = unanimous.copy()

        display_unanimous["Matchup"] = (
            display_unanimous["away_team"]
            + " @ "
            + display_unanimous["home_team"]
        )

        display_unanimous["Result"] = (
            display_unanimous["Correct"]
            .map(
                {
                    True: "Correct",
                    False: "Incorrect",
                }
            )
        )

        display_unanimous["Avg_Confidence"] = (
            display_unanimous["Avg_Confidence"]
            .round(1)
        )

        display_unanimous = (
            display_unanimous[
                [
                    "week",
                    "Matchup",
                    "Unanimous_Pick",
                    "Total_Confidence",
                    "Avg_Confidence",
                    "Result",
                ]
            ]
            .rename(
                columns={
                    "week": "Week",
                    "Unanimous_Pick": "Unanimous Pick",
                    "Total_Confidence": "Total Confidence",
                    "Avg_Confidence": "Avg Confidence",
                }
            )
        )

        st.dataframe(
            display_unanimous,
            use_container_width=True,
            hide_index=True,
        )

with comparison_tab:

    st.subheader("Player Agreement")


    agreement = player_agreement(
        filtered_df
    )


    if agreement.empty:

        st.info(
            "No player agreement data is "
            "available yet."
        )

    else:

        display_agreement = agreement.copy()

        display_agreement["Pair"] = (
            display_agreement["Player_A"]
            + " / "
            + display_agreement["Player_B"]
        )

        display_agreement["Agreement_Pct"] = (
            display_agreement["Agreement_Pct"]
            .map(
                lambda value: f"{value:.1%}"
            )
        )

        display_agreement = (
            display_agreement[
                [
                    "Pair",
                    "Shared_Games",
                    "Same_Pick",
                    "Disagreements",
                    "Agreement_Pct",
                ]
            ]
            .rename(
                columns={
                    "Shared_Games": "Shared Games",
                    "Same_Pick": "Same Pick",
                    "Agreement_Pct": "Agreement %",
                }
            )
        )

        st.dataframe(
            display_agreement,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("When Players Disagree")


    if agreement.empty:

        st.info(
            "No disagreement data is "
            "available yet."
        )

    else:

        disagreement_rows = []

        for _, row in agreement.iterrows():

            disagreement_rows.append(
                {
                    "Pair": (
                        f"{row['Player_A']} / "
                        f"{row['Player_B']}"
                    ),
                    "Disagreements": row[
                        "Disagreements"
                    ],
                    f"{row['Player_A']} Wins": row[
                        "Player_A_Wins"
                    ],
                    f"{row['Player_B']} Wins": row[
                        "Player_B_Wins"
                    ],
                }
            )

        for row in disagreement_rows:

            st.write(
                f"**{row['Pair']}**"
            )

            pair = row["Pair"].split(
                " / "
            )

            player_a = pair[0]
            player_b = pair[1]

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Disagreements",
                row["Disagreements"],
            )

            col2.metric(
                f"{player_a} Wins",
                row[f"{player_a} Wins"],
            )

            col3.metric(
                f"{player_b} Wins",
                row[f"{player_b} Wins"],
            )