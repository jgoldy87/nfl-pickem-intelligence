
from analysis.market_performance import get_market_performance

SEASON = 2026

markets = get_market_performance(SEASON)

print("\nMARKET DATA CHECK")
print("=" * 60)

print(f"Total rows: {len(markets)}")

print("\nAvailable columns:")
print(markets.columns.tolist())

print("\nGame types:")
print(markets["game_type"].value_counts(dropna=False))

print("\nMarket probabilities:")
print(
    markets["market_probability"]
    .describe()
    .round(2)
    .to_string()
)

print("\nMarket picks:")
print(markets["market_pick"].value_counts(dropna=False))

print("\nWinner values:")
print(markets["winner"].value_counts(dropna=False).head(10))

print("\nSample games:")
columns = [
    "week",
    "away_team",
    "home_team",
    "market_pick",
    "market_probability",
    "winner",
]

print(markets[columns].head(5).to_string(index=False))
