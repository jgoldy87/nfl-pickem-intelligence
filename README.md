# NFL Pick'em Intelligence Dashboard

An interactive NFL Pick'em Confidence Mode analytics dashboard built with Python and Streamlit.

The project combines sportsbook market data, weekly confidence picks, NFL game results, and historical player performance to help players make more informed weekly selections and analyze how they perform throughout the season.

## 🌐 Live App

[Launch the NFL Pick'em Intelligence Dashboard](https://nfl-pickem-intelligence-lrgrxiprqcfl3badrmhvfk.streamlit.app/)

## 🏈 Features

### Weekly Picks

Build a weekly Confidence Mode pick card and compare your selections against sportsbook market probabilities.

- Load NFL games and current sportsbook odds by week
- Select a winner for each matchup
- Drag and drop selections into confidence order
- Automatically assign confidence points based on ranking
- Calculate consensus no-vig market probabilities across sportsbooks
- Compare personal confidence rankings against market-recommended rankings
- Identify potential overconfidence and underconfidence
- Highlight strongest agreement with the betting market
- Visually flag differences between personal and market confidence

### Player Explorer

Explore an individual player's performance throughout the season.

Analyze:

- Overall record and win percentage
- Confidence points earned
- Weekly performance
- Home vs. away picks
- Performance when picking specific NFL teams
- Performance against specific opponents
- Confidence-level performance

### Standings

Track competition between players throughout the season.

Includes:

- Overall standings
- Weekly standings
- Correct and incorrect picks
- Win percentage
- Confidence points
- Confidence efficiency

### Pool Insights

Analyze how the entire pool approaches NFL games.

Includes:

- Hardest games for the pool
- Easiest games for the pool
- Lone Wolf picks and performance
- Unanimous picks
- Collective disasters
- Player-to-player agreement
- Results when players disagree
- Season and individual-week filtering

### Admin Tools

A password-protected Admin interface manages weekly pool data.

The Admin workflow supports:

1. Selecting the NFL season and week
2. Selecting a player
3. Loading the week's NFL schedule
4. Entering or editing picks and confidence values
5. Validating picks
6. Saving weekly picks
7. Refreshing NFL game results
8. Rebuilding the analytics dataset

## 📊 Data Pipeline

The application separates raw player picks from generated results and analytics.

```text
Weekly Player Picks
        ↓
NFL Schedule & Results
        ↓
Data Pipeline
        ↓
Master Picks/Results Dataset
        ↓
Analytics Engine
        ↓
Streamlit Dashboard
```

Weekly pick files serve as the permanent source data, while the master results dataset can be rebuilt as NFL results become available.

## 🛠️ Built With

- Python
- Streamlit
- pandas
- nflreadpy / nflverse
- The Odds API
- Requests
- python-dotenv
- streamlit-sortables
- Git / GitHub

## 📁 Project Structure

```text
NFL Confidence Assistant/
│
├── analysis/
│   ├── data_pipeline.py
│   ├── nfl_results.py
│   ├── pickem_analyzer.py
│   ├── player_explorer.py
│   └── weekly_picks.py
│
├── data/
│   ├── picks/
│   ├── templates/
│   └── picks_results.csv
│
├── pages/
│   ├── 1_Weekly_Picks.py
│   ├── 2_Player_Explorer.py
│   ├── 3_Standings.py
│   ├── 4_Pool_Insights.py
│   └── 5_Admin.py
│
├── app.py
├── requirements.txt
└── README.md
```

## 🎯 Project Goals

This project was created to explore how data analysis can improve decision-making in an NFL Pick'em Confidence pool.

Rather than simply tracking wins and losses, the dashboard examines **how confident players are in their decisions, where their opinions differ from the betting market, and how different picking strategies perform over time**.

The project also serves as a practical demonstration of:

- API integration
- Data ingestion and validation
- Data transformation with pandas
- Automated sports-data pipelines
- Interactive dashboard development
- Session-state management
- Analytics design
- Modular Python application architecture
- Git-based deployment workflows
