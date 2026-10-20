
import pandas as pd
import streamlit as st

from analysis.team_data import load_team_games
from analysis.situational import refresh_pbp_data
from analysis.rankings import (
    STAT_CONFIG,
    get_team_rankings,
    format_stat_value,
)

st.set_page_config(
    page_title="Team Rankings",
    layout="wide",
)

st.title("Team Rankings")
st.write(
    "Explore individual NFL team statistics and league rankings."
)

CATEGORY_ORDER = [
    "Offense",
    "Defense",
    "Overall",
    "Turnovers",
    "Situational",
]


def style_nfl_rank(value):
    """Apply subtle colors to NFL rankings."""

    if not isinstance(value, str) or not value.startswith("#"):
        return ""

    try:
        rank = int(value.replace("#", ""))
    except ValueError:
        return ""

    if rank <= 10:
        return "color: #2E8B57; font-weight: 600;"

    if rank >= 23:
        return "color: #C65D5D; font-weight: 600;"

    return ""


@st.cache_data(ttl=3600, show_spinner=False)
def get_team_data(season):
    return load_team_games(season)


# --------------------------------------------------
# SEASON AND DATA
# --------------------------------------------------

season = st.selectbox(
    "Season",
    [2026, 2025, 2024],
)


# --------------------------------------------------
# REFRESH TEAM STATISTICS
# --------------------------------------------------

if st.button(
    "🔄 Refresh Team Statistics",
    help="Download updated NFL play-by-play data and recalculate rankings.",
):
    try:
        with st.spinner("Refreshing NFL statistics..."):
            refresh_pbp_data(season)

            # Clear cached team-game statistics so the
            # next load uses the refreshed play-by-play data.
            get_team_data.clear()

        st.success(
            f"{season} team statistics refreshed successfully!"
        )

    except Exception as error:
        st.error(f"Unable to refresh statistics: {error}")


try:
    with st.spinner("Loading NFL team statistics..."):
        team_games = get_team_data(season)
except Exception as error:
    st.error(f"Unable to load team statistics: {error}")
    st.stop()

if team_games.empty:
    st.info("No team statistics are available for this season.")
    st.stop()

available_weeks = sorted(
    int(week)
    for week in team_games["week"].dropna().unique()
)

if not available_weeks:
    st.info("No completed weeks are available.")
    st.stop()

# --------------------------------------------------
# WEEK AND TEAM SELECTION
# --------------------------------------------------

col1, col2 = st.columns(2)

with col1:
    through_week = st.selectbox(
        "Statistics Through Week",
        available_weeks,
        index=len(available_weeks) - 1,
    )

with st.spinner("Calculating NFL rankings..."):
    rankings = get_team_rankings(
        team_games=team_games,
        season=season,
        through_week=through_week,
    )

teams = sorted(rankings["team"].dropna().unique())

with col2:
    selected_team = st.selectbox(
        "Team",
        teams,
    )

team_rows = rankings.loc[
    rankings["team"] == selected_team
]

if team_rows.empty:
    st.warning("No rankings are available for this team.")
    st.stop()

team = team_rows.iloc[0]

st.divider()

st.subheader(f"{selected_team} — Team Rankings")
st.caption(
    f"{season} Regular Season | "
    f"Statistics through Week {through_week}"
)

# --------------------------------------------------
# STATISTICAL CATEGORIES
# --------------------------------------------------

for category in CATEGORY_ORDER:

    rows = []

    for metric, config in STAT_CONFIG.items():

        if config["category"] != category:
            continue

        value = team.get(metric)
        rank = team.get(f"{metric}_rank")
        league_avg = team.get(f"{metric}_league_avg")

        rows.append(
            {
                "Statistic": config["label"],
                "Value": (
                    format_stat_value(metric, value)
                    if pd.notna(value)
                    else "N/A"
                ),
                "NFL Rank": (
                    f"#{int(rank)}"
                    if pd.notna(rank)
                    else "N/A"
                ),
                "League Average": (
                    format_stat_value(metric, league_avg)
                    if pd.notna(league_avg)
                    else "N/A"
                ),
            }
        )

    
    if rows:
        st.subheader(category)

        display_df = pd.DataFrame(rows)

        styled_df = display_df.style.map(
            style_nfl_rank,
            subset=["NFL Rank"],
        )

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
        )


st.caption(
    "Rank #1 represents the best performance in the NFL "
    "for each statistic. Rankings are based on cumulative "
    "regular-season results through the selected week."
)
