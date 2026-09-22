import streamlit as st
import pandas as pd

from analysis.pickem_analyzer import (
    pool_game_results,
    lone_wolf_picks,
    lone_wolf_performance,
    lone_wolf_standings_impact,
    lone_wolf_impact_detail,
    unanimous_picks,
    collective_disasters,
    collective_triumphs,
    pool_burners,
    player_agreement,
)

from analysis.data_pipeline import (
    build_master_results_from_supabase,
)

from analysis.market_performance import (
    get_market_performance,
    summarize_team_type_records,
)


st.title("Pool Insights")

left_col, image_col, right_col = st.columns(
    [2, 2, 2]
)

with image_col:
    st.image(
        "assets/pool_insights.png",
        use_container_width=True,
    )

st.write(
    "Analyze how the entire pool performed "
    "across games and weeks."
)


try:
    df = build_master_results_from_supabase()

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

(
    game_tab,
    behavior_tab,
    comparison_tab,
    nfl_trends_tab,
) = st.tabs(
    [
        "Game Insights",
        "Pick Behavior",
        "Player Comparisons",
        "NFL Trends",
    ]
)

with game_tab:

    st.divider()

    st.subheader("Collective Triumphs")


    triumphs = collective_triumphs(
        filtered_df
    )


    if triumphs.empty:

        st.info(
            "No collective triumphs are available yet."
        )

    else:

        display_triumphs = triumphs.copy()

        display_triumphs["Matchup"] = (
            display_triumphs["away_team"]
            + " @ "
            + display_triumphs["home_team"]
        )

        display_triumphs["Avg_Confidence"] = (
            display_triumphs["Avg_Confidence"]
            .round(1)
        )

        display_triumphs = (
            display_triumphs[
                [
                    "week",
                    "Matchup",
                    "Unanimous_Pick",
                    "Total_Confidence",
                    "Avg_Confidence",
                ]
            ]
            .rename(
                columns={
                    "week": "Week",
                    "Unanimous_Pick": "Pool Pick",
                    "Total_Confidence": "Confidence Earned",
                    "Avg_Confidence": "Avg Confidence",
                }
            )
        )

        st.dataframe(
            display_triumphs,
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

    left_col, image_col, right_col = st.columns(
        [2, 2, 2]
    )

    with image_col:
        st.image(
            "assets/pool_burners.png",
            use_container_width=True,
        )

    st.subheader("Pool Burners")

    st.caption(
        "A Pool Burner occurs when all three players pick against a team and that team wins."
    )

    burners = pool_burners(
        filtered_df
    )

    if burners.empty:

        st.info(
            "No teams have burned the pool yet."
        )

    else:

        display_burners = burners.copy()

        display_burners = (
            display_burners[
                [
                    "Team",
                    "Burns",
                    "Confidence_Lost",
                    "Avg_Confidence_Lost",
                ]
            ]
            .rename(
                columns={
                    "Confidence_Lost": "Confidence Lost",
                    "Avg_Confidence_Lost": "Avg Confidence Lost",
                }
            )
        )

        st.dataframe(
            display_burners,
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

        # Combine wins and losses into one record
        display_summary["Lone Wolf Record"] = (
            display_summary["Correct"].astype(str)
            + "-"
            + display_summary["Incorrect"].astype(str)
        )

        # Format winning percentage
        display_summary["Win_Pct"] = (
            display_summary["Win_Pct"]
            .map(
                lambda value: (
                    f"{value:.1%}"
                )
            )
        )

        display_summary = (
            display_summary[
                [
                    "Lone_Wolf",
                    "Lone Wolf Record",
                    "Win_Pct",
                ]
            ]
            .rename(
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

    st.subheader("Lone Wolf Point Swing")

    st.caption(
        "Net confidence-point swing between each pair of "
        "players across all Lone Wolf games. Positive values "
        "mean the player has gained ground; negative values "
        "mean the player has lost ground."
    )

    impact = lone_wolf_standings_impact(
        filtered_df
    )

    if impact.empty:

        st.info(
            "No Lone Wolf standings impact is "
            "available yet."
        )

    else:

        display_impact = impact.copy()

        for player in display_impact.columns:

            display_impact[player] = (
                display_impact[player]
                .map(
                    lambda value: (
                        f"{value:+g}"
                    )
                )
            )

        for player in display_impact.index:

            if player in display_impact.columns:
                display_impact.loc[
                    player,
                    player,
                ] = "—"

        st.dataframe(
            display_impact,
            use_container_width=True,
        )

    with st.expander(
        "View Point Swing Calculations"
    ):

        impact_detail = lone_wolf_impact_detail(
            filtered_df
        )

        if impact_detail.empty:

            st.info(
                "No Lone Wolf Point Swing calculations "
                "are available yet."
            )

        else:

            players = sorted(
                filtered_df["player"]
                .dropna()
                .unique()
            )

            matchups = []

            for i, player_a in enumerate(players):
                for player_b in players[i + 1:]:
                    matchups.append(
                        (player_a, player_b)
                    )

            matchup_labels = {
                f"{player_a} vs {player_b}": (
                    player_a,
                    player_b,
                )
                for player_a, player_b in matchups
            }

            selected_matchup = st.selectbox(
                "Select player matchup",
                options=list(
                    matchup_labels.keys()
                ),
                key="lone_wolf_swing_matchup",
            )

            player_a, player_b = (
                matchup_labels[selected_matchup]
            )

            matchup_detail = impact_detail[
                (
                    (
                        impact_detail["Lone_Wolf"]
                        == player_a
                    )
                    & (
                        impact_detail["Opponent"]
                        == player_b
                    )
                )
                |
                (
                    (
                        impact_detail["Lone_Wolf"]
                        == player_b
                    )
                    & (
                        impact_detail["Opponent"]
                        == player_a
                    )
                )
            ].copy()

            if matchup_detail.empty:

                st.info(
                    "No Lone Wolf games are available "
                    "for this matchup."
                )

            else:

                # Calculate every swing from player A's
                # perspective.
                matchup_detail["Swing"] = (
                    matchup_detail.apply(
                        lambda row: (
                            row["Impact"]
                            if row["Lone_Wolf"]
                            == player_a
                            else -row["Impact"]
                        ),
                        axis=1,
                    )
                )

                # Get each player's actual points.
                matchup_detail[
                    f"{player_a} Points"
                ] = matchup_detail.apply(
                    lambda row: (
                        row["Lone_Wolf_Points"]
                        if row["Lone_Wolf"]
                        == player_a
                        else row["Opponent_Points"]
                    ),
                    axis=1,
                )

                matchup_detail[
                    f"{player_b} Points"
                ] = matchup_detail.apply(
                    lambda row: (
                        row["Lone_Wolf_Points"]
                        if row["Lone_Wolf"]
                        == player_b
                        else row["Opponent_Points"]
                    ),
                    axis=1,
                )

                total_swing = (
                    matchup_detail["Swing"].sum()
                )

                if total_swing > 0:
                    swing_summary = (
                        f"+{total_swing:g} "
                        f"{player_a}"
                    )
                elif total_swing < 0:
                    swing_summary = (
                        f"+{abs(total_swing):g} "
                        f"{player_b}"
                    )
                else:
                    swing_summary = "Even"

                st.metric(
                    "Total Point Swing",
                    swing_summary,
                )

                display_detail = (
                    matchup_detail[
                        [
                            "Week",
                            "Game",
                            "Lone_Wolf",
                            f"{player_a} Points",
                            f"{player_b} Points",
                            "Swing",
                        ]
                    ]
                    .copy()
                )

                display_detail["Game"] = (
                    display_detail["Game"]
                    .map(
                        lambda game_id: (
                            f"{game_id.split('_')[2]} "
                            f"@ {game_id.split('_')[3]}"
                        )
                    )
                )

                display_detail = (
                    display_detail.rename(
                        columns={
                            "Lone_Wolf": "Lone Wolf",
                        }
                    )
                )

                display_detail["Swing"] = (
                    display_detail["Swing"]
                    .map(
                        lambda value: f"{value:+g}"
                    )
                )

                st.caption(
                    f"Swing is shown from "
                    f"{player_a}'s perspective."
                )

                st.dataframe(
                    display_detail,
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

        display_lone_wolves = display_lone_wolves.sort_values(
            by=[
                "Week",
                "Confidence",
                "Matchup",
            ],
            ascending=[
                False,
                False,
                True,
            ],
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

        unanimous_win_pct = (
            unanimous["Correct"].mean()
            * 100
        )

        st.write(
            "Unanimous picks:",
            len(unanimous),
        )

        st.write(
            "Correct unanimous picks:",
            unanimous["Correct"].sum(),
        )

        if selected_view == "Full Season":
            unanimous_message = (
                "When all players agree, we are right "
                f"{unanimous_win_pct:.1f}% of the time this season."
            )

        else:
            unanimous_message = (
                "When all players agree, we are right "
                f"{unanimous_win_pct:.1f}% of the time "
                f"in {selected_view}."
            )

        st.info(unanimous_message)

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

        display_unanimous = display_unanimous.sort_values(
            by=[
                "Week",
                "Total Confidence",
                "Matchup",
            ],
            ascending=[
                False,
                False,
                True,
            ],
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

with nfl_trends_tab:

    st.subheader("NFL Team Type Records")

    st.caption(
        "Regular-season results for the "
        f"{selected_season} NFL season."
    )

    try:
        market_results = get_market_performance(
            selected_season
        )

        regular_season_results = (
            market_results[
                market_results["game_type"]
                == "REG"
            ].copy()
        )

        team_type_records = (
            summarize_team_type_records(
                regular_season_results
            )
        )

        completed_games = len(
            regular_season_results
        )

        st.caption(
            f"{completed_games} completed games included."
        )

        home = team_type_records[
            "home_teams"
        ]

        away = team_type_records[
            "away_teams"
        ]

        favorites = team_type_records[
            "favorites"
        ]

        underdogs = team_type_records[
            "underdogs"
        ]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Home Teams",
            f"{home['wins']}-{home['losses']}",
            f"{home['win_percentage']:.1f}%",
        )

        col2.metric(
            "Away Teams",
            f"{away['wins']}-{away['losses']}",
            f"{away['win_percentage']:.1f}%",
        )

        col3.metric(
            "Favorites",
            f"{favorites['wins']}-{favorites['losses']}",
            f"{favorites['win_percentage']:.1f}%",
        )

        col4.metric(
            "Underdogs",
            f"{underdogs['wins']}-{underdogs['losses']}",
            f"{underdogs['win_percentage']:.1f}%",
        )

        st.markdown("#### Home / Away Breakdown")

        home_favorites = team_type_records[
            "home_favorites"
        ]

        away_favorites = team_type_records[
            "away_favorites"
        ]

        home_underdogs = team_type_records[
            "home_underdogs"
        ]

        away_underdogs = team_type_records[
            "away_underdogs"
        ]

        breakdown = pd.DataFrame(
            {
                "Type": [
                    "Favorites",
                    "Underdogs",
                ],
                "Home": [
                    (
                        f"{home_favorites['wins']}-"
                        f"{home_favorites['losses']} "
                        f"({home_favorites['win_percentage']:.1f}%)"
                    ),
                    (
                        f"{home_underdogs['wins']}-"
                        f"{home_underdogs['losses']} "
                        f"({home_underdogs['win_percentage']:.1f}%)"
                    ),
                ],
                "Away": [
                    (
                        f"{away_favorites['wins']}-"
                        f"{away_favorites['losses']} "
                        f"({away_favorites['win_percentage']:.1f}%)"
                    ),
                    (
                        f"{away_underdogs['wins']}-"
                        f"{away_underdogs['losses']} "
                        f"({away_underdogs['win_percentage']:.1f}%)"
                    ),
                ],
            }
        )

        st.dataframe(
            breakdown,
            use_container_width=True,
            hide_index=True,
        )

    except Exception as error:
        st.error(
            f"Could not load NFL Trends: {error}"
        )