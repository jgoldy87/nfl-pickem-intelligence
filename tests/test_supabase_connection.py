import os

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

response = (
    supabase
    .table("picks")
    .select("*")
    .execute()
)

print("Connection successful!")
print("Rows returned:", len(response.data))
print(response.data)