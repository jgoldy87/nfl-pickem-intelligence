# NFL Pick'em Intelligence Dashboard

An interactive NFL Pick'em Confidence Mode analytics dashboard built with Vibe Coding, Python, Streamlit, and Supabase.

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
4. Loading existing picks from persistent storage
5. Entering or editing picks and confidence values
6. Validating picks and confidence assignments
7. Saving picks to Supabase
8. Refreshing NFL game results
9. Rebuilding the analytics dataset

## 📊 Data Pipeline

Supabase provides persistent storage for raw player picks, allowing the deployed Streamlit application to retain data across sessions and deployments.

```text
Streamlit Admin
      ↓
Enter / Edit Picks
      ↓
Supabase
      ↓
Persistent Pick Data
      ↓
NFL Schedule & Results
      ↓
Data Pipeline
      ↓
Master Picks/Results Dataset
      ↓
Analytics Engine
      ↓
Standings / Player Explorer / Pool Insights
```

Supabase serves as the **source of truth** for raw player picks. NFL results are fetched and merged with those picks to calculate pick accuracy and confidence points.

The master analytics dataset can be rebuilt whenever updated NFL results become available.

Historical weekly CSV files are retained as backup/archive data rather than serving as the live application's primary storage.

## 🛠️ Built With

- Python
- Streamlit
- Supabase / PostgreSQL
- pandas
- nflreadpy / nflverse
- The Odds API
- Requests
- python-dotenv
- streamlit-sortables
- Git / GitHub
- Streamlit Community Cloud

## 📁 Project Structure

```text
NFL Confidence Assistant/
│
├── analysis/
│   ├── database.py
│   ├── data_pipeline.py
│   ├── nfl_results.py
│   ├── pickem_analyzer.py
│   ├── player_explorer.py
│   └── weekly_picks.py
│
├── data/
│   ├── picks/
│   ├── templates/
│   ├── archive/
│   └── picks_results.csv
│
├── pages/
│   ├── 1_Weekly_Picks.py
│   ├── 2_Player_Explorer.py
│   ├── 3_Standings.py
│   ├── 4_Pool_Insights.py
│   └── 5_Admin.py
│
├── tests/
│   ├── test_database.py
│   ├── test_supabase_results.py
│   ├── test_supabase_master.py
│   └── migrate_week1_to_supabase.py
│
├── app.py
├── requirements.txt
└── README.md
```

## 🔐 Persistent Storage

Player picks are stored in a Supabase PostgreSQL database using a unique combination of:

```text
season + week + player + game_id
```

This allows the Admin interface to safely insert new picks or update existing selections without creating duplicate player/game records.

Database credentials and API keys are managed through environment variables locally and Streamlit Secrets in production. Sensitive credentials are excluded from the Git repository.

## 🎯 Project Goals

This project was created to explore how data analysis can improve decision-making in an NFL Pick'em Confidence pool.

Rather than simply tracking wins and losses, the dashboard examines **how confident players are in their decisions, where their opinions differ from the betting market, and how different picking strategies perform over time**.

The project also serves as a practical demonstration of:

- API integration
- Persistent cloud database integration
- Data ingestion and validation
- Data transformation with pandas
- Automated sports-data pipelines
- Interactive dashboard development
- Session-state management
- Analytics design
- Secure configuration and secrets management
- Modular Python application architecture
- Database-backed application development
- Git-based deployment workflows
