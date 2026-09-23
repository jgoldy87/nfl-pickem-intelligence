import streamlit as st

from analysis.weekly_picks import (
    get_week_nfl_odds,
    rank_live_picks,
    summarize_pick_profile,
)

from streamlit_sortables import sort_items

def highlight_difference(value):

    if value > 0:
        return (
            "background-color: "
            "rgba(255, 75, 75, 0.20)"
        )

    if value < 0:
        return (
            "background-color: "
            "rgba(255, 193, 7, 0.20)"
        )

    return (
        "background-color: "
        "rgba(40, 167, 69, 0.20)"
    )

st.title("Weekly Picks")

st.write(
    "Build your weekly Pick'em card and "
    "compare your confidence rankings "
    "with sportsbook market probabilities."
)


# --------------------------------------------------
# Week selection
# --------------------------------------------------

col1, col2 = st.columns(2)

with col1:

    season = st.selectbox(
        "Season",
        options=[2026],
    )

with col2:

    week = st.selectbox(
        "Week",
        options=list(
            range(1, 19)
        ),
        index=1,
    )


# --------------------------------------------------
# Load odds
# --------------------------------------------------

if st.button(
    "Load Weekly Odds",
    type="primary",
):

    try:

        games = get_week_nfl_odds(
            season=season,
            week=week,
        )

        st.session_state[
            "weekly_odds"
        ] = games

        st.session_state[
            "weekly_odds_season"
        ] = season

        st.session_state[
            "weekly_odds_week"
        ] = week

        st.success(
            f"Loaded odds for "
            f"{len(games)} games."
        )

    except Exception as error:

        st.error(
            f"Could not load weekly odds: "
            f"{error}"
        )


# --------------------------------------------------
# Display loaded games
# --------------------------------------------------

games = st.session_state.get(
    "weekly_odds",
    []
)


if games:

    loaded_season = st.session_state.get(
        "weekly_odds_season"
    )

    loaded_week = st.session_state.get(
        "weekly_odds_week"
    )

    st.subheader(
        f"{loaded_season} Week "
        f"{loaded_week}"
    )

    st.subheader("Make Your Picks")

    if "weekly_pick_selections" not in st.session_state:
        st.session_state[
            "weekly_pick_selections"
        ] = {}

    weekly_picks = []

    for game in games:

        away_team = game["away_team"]
        home_team = game["home_team"]
        game_id = game["id"]

        game_label = (
            f"{away_team} @ {home_team}"
        )

        saved_pick = st.session_state[
            "weekly_pick_selections"
        ].get(game_id)

        options = [
            away_team,
            home_team,
        ]

        if saved_pick in options:
            default_index = options.index(
                saved_pick
            )
        else:
            default_index = None

        pick = st.radio(
            game_label,
            options=options,
            index=default_index,
            key=f"pick_{game_id}",
            horizontal=True,
        )

        if pick is not None:
            st.session_state[
                "weekly_pick_selections"
            ][game_id] = pick

        weekly_picks.append(
            {
                "game": game,
                "pick": pick,
            }
        )

        st.divider()

    completed_picks = sum(
        1
        for item in weekly_picks
        if item["pick"] is not None
    )

    st.write(
        f"**Picks selected:** "
        f"{completed_picks} / "
        f"{len(games)}"
    )

    if completed_picks == len(games):

        # Pick profile summary
        pick_profile = summarize_pick_profile(
            weekly_picks
        )

        st.subheader("Pick Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Home Picks",
                pick_profile["home_picks"],
            )

        with col2:
            st.metric(
                "Away Picks",
                pick_profile["away_picks"],
            )

        with col3:
            st.metric(
                "Favorite Picks",
                pick_profile["favorite_picks"],
            )

        with col4:
            st.metric(
                "Underdog Picks",
                pick_profile["underdog_picks"],
            )

        if pick_profile["pickem_picks"] > 0:
            st.caption(
                f"Pick'em games selected: "
                f"{pick_profile['pickem_picks']}"
            )

        st.divider()

        st.subheader("Rank Your Picks")

        st.write(
            "Drag the teams into your preferred "
            "confidence order."
        )

        st.caption(
            "Top = lowest confidence • "
            "Bottom = highest confidence"
        )

        pick_labels = {}

        for item in weekly_picks:
            game = item["game"]
            pick = item["pick"]

            away_team = game["away_team"]
            home_team = game["home_team"]

            if pick == away_team:
                opponent = home_team
            else:
                opponent = away_team

            label = f"{pick} over {opponent}"

            pick_labels[label] = pick


        selected_teams = list(
            pick_labels.keys()
        )

        ranked_teams = sort_items(
            selected_teams,
            direction="vertical",
        )

        confidence_lookup = {
            pick_labels[label]: confidence
            for label, confidence in zip(
                ranked_teams,
                range(
                    1,
                    len(ranked_teams) + 1,
                ),
            )
        }

        ranked_picks = []

        for item in weekly_picks:

            pick = item["pick"]

            ranked_picks.append(
                {
                    "game": item["game"],
                    "pick": pick,
                    "user_confidence": (
                        confidence_lookup[pick]
                    ),
                }
            )

        st.write("Current confidence order:")

        for confidence, label in zip(
            range(
                1,
                len(ranked_teams) + 1,
            ),
            ranked_teams,
        ):

            st.write(
                f"**{confidence}.** {label}"
            )
        
        if st.button(
            "Analyze My Picks",
            type="primary",
        ):

            try:

                rankings = rank_live_picks(
                    ranked_picks
                )

                st.session_state[
                    "weekly_rankings"
                ] = rankings

            except Exception as error:

                st.error(
                    f"Could not analyze picks: "
                    f"{error}"
                )

        rankings = st.session_state.get(
            "weekly_rankings"
        )

        if rankings is not None:

            st.subheader("Confidence Insights")

            most_overconfident = rankings.loc[
                rankings["Difference"].idxmax()
            ]

            most_underconfident = rankings.loc[
                rankings["Difference"].idxmin()
            ]

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Potential Overconfidence",
                    most_overconfident["Your Pick"],
                    delta=(
                        f"{most_overconfident['Difference']:+} "
                        "vs. market"
                    ),
                    delta_color="inverse",
                )

                st.caption(
                    f"Your confidence: "
                    f"{most_overconfident['Your Confidence']} "
                    f"• Market Confidence: "
                    f"{most_overconfident['Recommended Confidence']} "
                    f"• Market: "
                    f"{most_overconfident['Market Probability']}%"
                )

            with col2:

                st.metric(
                    "Potential Underconfidence",
                    most_underconfident["Your Pick"],
                    delta=(
                        f"{most_underconfident['Difference']:+} "
                        "vs. market"
                    ),
                    delta_color="inverse",
                )

                st.caption(
                    f"Your confidence: "
                    f"{most_underconfident['Your Confidence']} "
                    f"• Market Confidence: "
                    f"{most_underconfident['Recommended Confidence']} "
                    f"• Market: "
                    f"{most_underconfident['Market Probability']}%"
                )

            # --------------------------------------------------
            # Strongest market agreement
            # --------------------------------------------------

            agreement_rankings = rankings.copy()

            agreement_rankings[
                "Absolute Difference"
            ] = (
                agreement_rankings["Difference"]
                .abs()
            )

            strongest_agreement = (
                agreement_rankings
                .sort_values(
                    [
                        "Absolute Difference",
                        "Market Probability",
                    ],
                    ascending=[
                        True,
                        False,
                    ],
                )
                .iloc[0]
            )

            st.metric(
                "Strongest Market Agreement",
                strongest_agreement["Your Pick"],
                delta=(
                    f"{strongest_agreement['Difference']:+} "
                    "vs. market"
                ),
            )

            st.caption(
                f"Your confidence: "
                f"{strongest_agreement['Your Confidence']} "
                f"• Market Confidence: "
                f"{strongest_agreement['Recommended Confidence']} "
                f"• Market: "
                f"{strongest_agreement['Market Probability']}%"
            )

            st.subheader(
                "Your Confidence Card"
            )

            display_rankings = (
                rankings
                .sort_values(
                    "Your Confidence",
                    ascending=False,
                )
                .reset_index(drop=True)
            )

            display_rankings = (
                display_rankings.rename(
                    columns={
                        "Recommended Confidence": (
                            "Market Confidence"
                        ),
                        "Difference": (
                            "Confidence Difference"
                        ),
                    }
                )
            )

            styled_rankings = (
                display_rankings.style
                .map(
                    highlight_difference,
                    subset=["Confidence Difference"],
                )
            )

            st.caption(
                "🟢 Matches market  •  "
                "🟡 Potential underconfidence  •  "
                "🔴 Potential overconfidence"
            )

            st.dataframe(
                styled_rankings,
                use_container_width=True,
                hide_index=True,
            )

else:

    st.info(
        "Select a week and load the "
        "current sportsbook odds."
    )