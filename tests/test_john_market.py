
from analysis.market_performance import get_market_performance

markets = get_market_performance(
    season=2026,
    week=1,
)

print("\nMARKET DATA COLUMNS")
print("=" * 70)
print(markets.columns.tolist())

print("\nSAMPLE MARKET DATA")
print("=" * 70)
print(markets.head(5).to_string(index=False))

print(f"\nTotal games: {len(markets)}")
