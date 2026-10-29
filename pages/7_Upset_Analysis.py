
import pandas as pd
import streamlit as st

from analysis.market_performance import (
    get_market_performance,
    summarize_upset_buckets,
)


st.set_page_config(
    page_title="Upset Analysis",
    page_icon="📉",
    layout="wide",
)

st.title("NFL Upset Analysis")

st.caption(
    "Explore NFL upsets using historical market-implied "
    "win probabilities from nflverse moneylines."
)

# --------------------------------------------------
# SEASON SELECTION
# --------------------------------------------------

season = st.selectbox(
    "Select season",
    options=list(range(2026, 2020, -1)),
    index=0,
)


# --------------------------------------------------
# LOAD MARKET DATA
# --------------------------------------------------

@st.cache_data(show_spinner="Loading NFL market data...")
def load_market_data(selected_season):
    return get_market_performance(season=selected_season)


try:
    games = load_market_data(season)
except Exception as exc:
    st.error(f"Unable to load market data: {exc}")
    st.stop()


# --------------------------------------------------
# FILTER ELIGIBLE GAMES
# --------------------------------------------------

games = games[
    (games["game_type"] == "REG")
    & games["winner"].notna()
].copy()

# A valid winner must match one of the two teams.
games = games[
    games["winner"].eq(games["home_team"])
    | games["winner"].eq(games["away_team"])
].copy()

# Remove games without usable market probabilities.
games = games.dropna(
    subset=["market_probability", "market_pick"]
)

# Exactly 50/50 games have no market favorite.
games = games[
    games["market_probability"] > 50
].copy()

# Keep only probabilities within their valid range.
games = games[
    games["market_probability"].between(50, 100)
].copy()

if games.empty:
    st.info("No completed games with usable odds are available.")
    st.stop()


# --------------------------------------------------
# UPSET CALCULATIONS
# --------------------------------------------------

games["upset"] = (
    games["winner"] != games["market_pick"]
).astype(int)

games["expected_upset"] = (
    1 - games["market_probability"] / 100
)

total_games = len(games)
actual_upsets = int(games["upset"].sum())
expected_upsets = games["expected_upset"].sum()

actual_rate = actual_upsets / total_games * 100
expected_rate = expected_upsets / total_games * 100

upset_difference = actual_upsets - expected_upsets


# --------------------------------------------------
# SEASON OVERVIEW
# --------------------------------------------------

st.subheader(f"{season} Season Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Games Analyzed",
    f"{total_games:,}",
)

col2.metric(
    "Actual Upsets",
    f"{actual_upsets:,}",
    help="Games won by the market underdog.",
)

col3.metric(
    "Expected Upsets",
    f"{expected_upsets:.2f}",
    help=(
        "Sum of each favorite's implied "
        "probability of losing."
    ),
)

col4.metric(
    "Actual − Expected",
    f"{upset_difference:+.2f}",
    help=(
        "Positive means more upsets occurred "
        "than market probabilities predicted."
    ),
)

st.divider()

rate_col1, rate_col2 = st.columns(2)

rate_col1.metric(
    "Actual Upset Rate",
    f"{actual_rate:.1f}%",
)

rate_col2.metric(
    "Expected Upset Rate",
    f"{expected_rate:.1f}%",
)

st.caption(
    "Regular-season games only. Ties, incomplete games, "
    "games without usable odds, and exact 50/50 "
    "matchups are excluded."
)


# --------------------------------------------------
# UPSETS BY FAVORITE PROBABILITY
# --------------------------------------------------

st.divider()

st.subheader("Upsets by Favorite Probability")

st.write(
    "How often do favorites lose at different levels "
    "of market-implied win probability?"
)

bucket_summary = summarize_upset_buckets(games)

# --------------------------------------------------
# SUMMARY TABLE
# --------------------------------------------------

display_buckets = bucket_summary.rename(
    columns={
        "probability_bucket": "Favorite Probability",
        "games": "Games",
        "upsets": "Upsets",
        "expected_upsets": "Expected Upsets",
        "upset_rate": "Actual Upset Rate",
        "expected_upset_rate": "Expected Upset Rate",
        "upset_difference": "Actual − Expected",
    }
)

st.dataframe(
    display_buckets,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Games": st.column_config.NumberColumn(
            format="%d"
        ),
        "Upsets": st.column_config.NumberColumn(
            format="%d"
        ),
        "Expected Upsets": st.column_config.NumberColumn(
            format="%.2f"
        ),
        "Actual Upset Rate": st.column_config.NumberColumn(
            format="%.1f%%"
        ),
        "Expected Upset Rate": st.column_config.NumberColumn(
            format="%.1f%%"
        ),
        "Actual − Expected": st.column_config.NumberColumn(
            format="%+.2f"
        ),
    },
)

# --------------------------------------------------
# ACTUAL VS EXPECTED UPSET RATES
# --------------------------------------------------

st.subheader("Actual vs Expected Upset Rates")

chart_data = bucket_summary[
    [
        "probability_bucket",
        "upset_rate",
        "expected_upset_rate",
    ]
].copy()

chart_data = chart_data.rename(
    columns={
        "upset_rate": "Actual Upset Rate",
        "expected_upset_rate": "Expected Upset Rate",
    }
)

# Remove empty categories from the chart.
chart_data = chart_data.loc[
    bucket_summary["games"].to_numpy() > 0
]

chart_data["probability_bucket"] = (
    chart_data["probability_bucket"].astype(str)
)

chart_data = chart_data.set_index(
    "probability_bucket"
)

st.bar_chart(
    chart_data,
    x_label="Favorite Win Probability",
    y_label="Upset Rate (%)",
    color=["#E76F51", "#457B9D"],
    stack=False,
)


# --------------------------------------------------
# RAW NUMBERS BEHIND THE CHART
# --------------------------------------------------

st.markdown("#### Numbers Behind the Chart")

chart_table = bucket_summary[
    [
        "probability_bucket",
        "games",
        "upsets",
        "expected_upsets",
        "upset_rate",
        "expected_upset_rate",
    ]
].copy()

chart_table = chart_table.rename(
    columns={
        "probability_bucket": "Favorite Probability",
        "games": "Games",
        "upsets": "Actual Upsets",
        "expected_upsets": "Expected Upsets",
        "upset_rate": "Actual Rate",
        "expected_upset_rate": "Expected Rate",
    }
)

# Match the chart by excluding categories with no games.
chart_table = chart_table[
    chart_table["Games"] > 0
]

st.dataframe(
    chart_table,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Games": st.column_config.NumberColumn(
            format="%d"
        ),
        "Actual Upsets": st.column_config.NumberColumn(
            format="%d"
        ),
        "Expected Upsets": st.column_config.NumberColumn(
            format="%.2f"
        ),
        "Actual Rate": st.column_config.NumberColumn(
            format="%.1f%%"
        ),
        "Expected Rate": st.column_config.NumberColumn(
            format="%.1f%%"
        ),
    },
)

st.caption(
    "Expected upset rates are calculated from "
    "normalized market-implied probabilities. "
    "A positive actual-minus-expected difference "
    "indicates more upsets than expected."
)


# --------------------------------------------------
# WEEKLY UPSET TRENDS
# --------------------------------------------------

st.divider()
st.subheader("Weekly Upset Trends")

st.write(
    "Compare the number of actual upsets with the "
    "number expected by the betting market each week."
)

weekly_summary = (
    games.groupby("week")
    .agg(
        games_played=("upset", "size"),
        actual_upsets=("upset", "sum"),
        expected_upsets=("expected_upset", "sum"),
    )
    .reset_index()
    .sort_values("week")
)

# --------------------------------------------------
# WEEKLY LINE CHART
# --------------------------------------------------

weekly_chart = weekly_summary[
    ["week", "actual_upsets", "expected_upsets"]
].copy()

weekly_chart = weekly_chart.rename(
    columns={
        "actual_upsets": "Actual Upsets",
        "expected_upsets": "Expected Upsets",
    }
)

# Use week numbers as categorical labels.

# Keep week numbers numeric to preserve chronological order.
weekly_chart["week"] = weekly_chart["week"].astype(int)

weekly_chart = weekly_chart.sort_values("week")

st.line_chart(
    weekly_chart,
    x="week",
    y=["Actual Upsets", "Expected Upsets"],
    x_label="NFL Week",
    y_label="Number of Upsets",
    color=["#E76F51", "#457B9D"],
)


# --------------------------------------------------
# SELECT A WEEK
# --------------------------------------------------

st.markdown("#### Weekly Upset Details")

available_weeks = sorted(
    weekly_summary["week"].astype(int).tolist(),
    reverse=True,
)

selected_week = st.selectbox(
    "Select Week",
    options=available_weeks,
    format_func=lambda week: f"Week {week}",
    key="upset_trends_week",
)

week_summary = weekly_summary[
    weekly_summary["week"] == selected_week
].iloc[0]

week_upsets = games[
    (games["week"] == selected_week)
    & (games["upset"] == 1)
].copy()

# --------------------------------------------------
# WEEKLY SUMMARY
# --------------------------------------------------

col1, col2, col3 = st.columns(3)

col1.metric(
    "Games Analyzed",
    int(week_summary["games_played"]),
)

col2.metric(
    "Actual Upsets",
    int(week_summary["actual_upsets"]),
)

col3.metric(
    "Expected Upsets",
    f"{week_summary['expected_upsets']:.2f}",
)

# --------------------------------------------------
# WEEKLY UPSET TABLE
# --------------------------------------------------

st.markdown(f"#### Week {selected_week} Upsets")

if week_upsets.empty:
    st.info("No market upsets occurred this week.")
else:
    upset_table = week_upsets[
        [
            "game",
            "winner",
            "market_pick",
            "market_probability",
        ]
    ].copy()

    upset_table = upset_table.rename(
        columns={
            "game": "Matchup",
            "winner": "Winner",
            "market_pick": "Favorite",
            "market_probability": "Favorite Win Probability",
        }
    )

    upset_table = upset_table.sort_values(
        "Favorite Win Probability",
        ascending=False,
    )

    st.dataframe(
        upset_table,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Favorite Win Probability":
                st.column_config.NumberColumn(
                    format="%.1f%%"
                ),
        },
    )

st.caption(
    "An upset occurs when the market underdog wins. "
    "Expected upsets are calculated from normalized "
    "market-implied probabilities."
)
