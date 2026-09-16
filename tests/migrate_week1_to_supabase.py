import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client


load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SECRET_KEY")

if not url or not key:
    raise ValueError(
        "Supabase credentials were not found."
    )

supabase = create_client(url, key)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

picks_file = (
    PROJECT_ROOT
    / "data"
    / "picks"
    / "2026_week_01.csv"
)

df = pd.read_csv(picks_file)

# Select and rename columns for Supabase
migration_df = df[
    [
        "season",
        "week",
        "player",
        "game_id",
        "picked_team",
        "confidence",
    ]
].copy()

migration_df = migration_df.rename(
    columns={
        "picked_team": "pick",
    }
)

# Convert pandas/numpy values to
# standard Python values for JSON
records = migration_df.to_dict(
    orient="records"
)

print(
    f"Preparing to migrate "
    f"{len(records)} picks..."
)

response = (
    supabase
    .table("picks")
    .upsert(
        records,
        on_conflict=(
            "season,week,player,game_id"
        ),
    )
    .execute()
)

print(
    "Migration successful!"
)

print(
    "Rows returned:",
    len(response.data),
)