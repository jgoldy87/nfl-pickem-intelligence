
import pandas as pd
import requests
import streamlit as st


ESPN_URL = (
    "https://site.api.espn.com/apis/v2/"
    "sports/football/nfl/standings"
)

DIVISIONS = {
    "AFC East": ["BUF", "MIA", "NE", "NYJ"],
    "AFC North": ["BAL", "CIN", "CLE", "PIT"],
    "AFC South": ["HOU", "IND", "JAX", "TEN"],
    "AFC West": ["DEN", "KC", "LAC", "LV"],
    "NFC East": ["DAL", "NYG", "PHI", "WAS"],
    "NFC North": ["CHI", "DET", "GB", "MIN"],
    "NFC South": ["ATL", "CAR", "NO", "TB"],
    "NFC West": ["ARI", "LA", "SF", "SEA"],
}

TEAM_DIVISIONS = {
    team: division
    for division, teams in DIVISIONS.items()
    for team in teams
}

# ESPN sometimes uses different team abbreviations.
TEAM_ALIASES = {
    "WSH": "WAS",
    "LAR": "LA",
    "JAC": "JAX",
}


def get_stat(stats, *names, default=None):
    for name in names:
        if name in stats:
            item = stats[name]
            value = item.get("value")
            if value is not None:
                return value
    return default


@st.cache_data(ttl=1800, show_spinner=False)
def load_nfl_standings(season):
    response = requests.get(
        ESPN_URL,
        params={
            "season": int(season),
            "seasontype": 2,
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()

    rows = []

    def collect_entries(group):
        if not isinstance(group, dict):
            return

        standings = group.get("standings", {})
        entries = standings.get("entries", [])

        for entry in entries:
            team = entry.get("team", {})
            abbreviation = team.get("abbreviation", "")
            abbreviation = TEAM_ALIASES.get(
                abbreviation, abbreviation
            )

            if abbreviation not in TEAM_DIVISIONS:
                continue

            stats = {
                item["name"]: item
                for item in entry.get("stats", [])
                if "name" in item
            }

            wins = get_stat(stats, "wins", default=0)
            losses = get_stat(stats, "losses", default=0)
            ties = get_stat(stats, "ties", default=0)

            pf = get_stat(stats, "pointsFor", default=0)
            pa = get_stat(stats, "pointsAgainst", default=0)

            games = wins + losses + ties
            pct = (
                (wins + ties / 2) / games
                if games
                else 0.0
            )

            rows.append({
                "Division": TEAM_DIVISIONS[abbreviation],
                "Team": team.get(
                    "displayName", abbreviation
                ),
                "Abbreviation": abbreviation,
                "W": int(wins),
                "L": int(losses),
                "T": int(ties),
                "PCT": pct,
                "PF": int(pf),
                "PA": int(pa),
                "DIFF": int(pf - pa),
                "Division Rank": get_stat(
                    stats,
                    "divisionRank",
                    "divisionStanding",
                ),
                "ESPN Order": len(rows),
            })

        for child in group.get("children", []):
            collect_entries(child)

    collect_entries(data)

    if not rows:
        raise ValueError(
            "ESPN returned no usable NFL standings."
        )

    df = pd.DataFrame(rows)

    # Protect against duplicate team entries.
    df = df.drop_duplicates(
        subset=["Abbreviation"],
        keep="first",
    )

    if len(df) != 32:
        raise ValueError(
            f"Expected 32 NFL teams, received {len(df)}."
        )

    return df


def get_division_standings(df, division):
    division_df = df[
        df["Division"] == division
    ].copy()

    if division_df["Division Rank"].notna().all():
        division_df = division_df.sort_values(
            ["Division Rank", "ESPN Order"],
            ascending=[True, True],
            kind="stable",
        )
    else:
        # Preserve ESPN's original ordering.
        # This is not a substitute for official
        # division tiebreaking.
        division_df = division_df.sort_values(
            "ESPN Order",
            kind="stable",
        )

    return division_df[
        ["Team", "W", "L", "T", "PCT", "PF", "PA", "DIFF"]
    ]
