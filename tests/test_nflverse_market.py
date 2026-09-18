import nflreadpy as nfl

from nflreadpy.config import update_config

update_config(
    cache_mode="off"
)

nfl.clear_cache()

schedule = nfl.load_schedules(
    seasons=[2026]
).to_pandas()


market_columns = [
    "season",
    "week",
    "gameday",
    "away_team",
    "home_team",
    "away_score",
    "home_score",
    "away_moneyline",
    "home_moneyline",
    "spread_line",
    "away_spread_odds",
    "home_spread_odds",
    "total_line",
]


available_columns = [
    column
    for column in market_columns
    if column in schedule.columns
]


print("\nAVAILABLE MARKET COLUMNS")
print("-" * 60)

for column in available_columns:
    print(column)


print("\n2026 WEEK 1")
print("-" * 60)

week_1 = schedule[
    schedule["week"] == 2
][available_columns]

print(
    week_1.to_string(
        index=False
    )
)