import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client


load_dotenv()


def get_supabase_credentials():
    """
    Load Supabase credentials locally from .env
    or from Streamlit Secrets when deployed.
    """

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")

    if url and key:
        return url, key

    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_SECRET_KEY"]

        if url and key:
            return url, key

    except Exception:
        pass

    raise ValueError(
        "Supabase credentials were not found."
    )


def get_supabase_client():
    """
    Create and return a Supabase client.
    """

    url, key = get_supabase_credentials()

    return create_client(url, key)


def load_picks():
    """
    Load all picks from Supabase
    into a pandas DataFrame.
    """

    supabase = get_supabase_client()

    response = (
        supabase
        .table("picks")
        .select("*")
        .execute()
    )

    return pd.DataFrame(response.data)

def upsert_picks(picks_df):
    """
    Insert new picks or update existing picks
    in Supabase.

    Expected columns:
    season, week, player, game_id,
    picked_team, confidence
    """

    if picks_df.empty:
        return []

    required_columns = [
        "season",
        "week",
        "player",
        "game_id",
        "picked_team",
        "confidence",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in picks_df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: "
            f"{missing_columns}"
        )

    db_df = picks_df[
        required_columns
    ].copy()

    db_df = db_df.rename(
        columns={
            "picked_team": "pick",
        }
    )

    # Ensure JSON-friendly native Python values.
    records = db_df.to_dict(
        orient="records"
    )

    supabase = get_supabase_client()

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

    return response.data