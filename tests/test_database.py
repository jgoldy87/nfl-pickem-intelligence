from analysis.database import (
    load_picks,
    upsert_picks,
)


df = load_picks()

test_pick = df[
    (df["season"] == 2026)
    & (df["week"] == 1)
    & (df["player"] == "Jesse")
].head(1).copy()


# Convert database column name back to
# the format expected by upsert_picks().
test_pick = test_pick.rename(
    columns={
        "pick": "picked_team",
    }
)


result = upsert_picks(test_pick)

print("Upsert returned:")
print(result)


updated_df = load_picks()

print()
print(
    "Rows after upsert:",
    len(updated_df),
)