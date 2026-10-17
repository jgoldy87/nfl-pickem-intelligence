import pandas as pd

from analysis.market_performance import get_market_performance


# ============================================================
# 1. LOAD HISTORICAL AND CURRENT MARKET RESULTS
# ============================================================

all_results = []

for season in range(2021, 2027):

    print(f"Loading {season} season...")

    season_df = get_market_performance(season)

    season_df = season_df[
        (season_df["game_type"] == "REG")
        & (season_df["winner"] != "TIE")
    ].copy()

    all_results.append(season_df)

df = pd.concat(all_results, ignore_index=True)


# ============================================================
# 2. CALCULATE BRIER SCORES
# ============================================================

df["Probability"] = df["market_probability"] / 100

df["Outcome"] = df["market_correct"].astype(int)

df["Brier"] = (
    df["Probability"] - df["Outcome"]
) ** 2

# Expected Brier score if the probabilities are correct.
df["Expected_Brier"] = (
    df["Probability"] * (1 - df["Probability"])
)


# ============================================================
# 3. SEASON-BY-SEASON COMPARISON
# ============================================================

season_summary = (
    df.groupby("season")
    .agg(
        Games=("Brier", "count"),
        Brier_Score=("Brier", "mean"),
        Expected_Brier=("Expected_Brier", "mean"),
        Favorite_Accuracy=("Outcome", "mean"),
    )
)

season_summary["Favorite_Accuracy"] *= 100

season_summary["Brier_Difference"] = (
    season_summary["Brier_Score"]
    - season_summary["Expected_Brier"]
)

print("\nNFL MARKET BRIER SCORES BY SEASON")
print("=" * 90)

print(season_summary.round(4).to_string())


# ============================================================
# 4. HISTORICAL BASELINE VS 2026
# ============================================================

historical = df[df["season"] < 2026]
current = df[df["season"] == 2026]

print("\nHISTORICAL BASELINE VS 2026")
print("=" * 70)

for label, data in [
    ("2021-2025", historical),
    ("2026", current),
]:

    print(f"\n{label}")
    print(f"Games: {len(data)}")
    print(f"Brier score: {data['Brier'].mean():.4f}")
    print(f"Expected Brier: {data['Expected_Brier'].mean():.4f}")
    print(f"50% baseline: 0.2500")


# ============================================================
# 5. 2026 WEEK-BY-WEEK BRIER SCORES
# ============================================================

weekly = (
    current.groupby("week")
    .agg(
        Games=("Brier", "count"),
        Brier_Score=("Brier", "mean"),
        Expected_Brier=("Expected_Brier", "mean"),
        Favorite_Accuracy=("Outcome", "mean"),
    )
)

weekly["Favorite_Accuracy"] *= 100

weekly["Brier_Difference"] = (
    weekly["Brier_Score"]
    - weekly["Expected_Brier"]
)

print("\n2026 WEEKLY BRIER SCORES")
print("=" * 90)

print(weekly.round(4).to_string())