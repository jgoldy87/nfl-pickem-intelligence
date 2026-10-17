
from pathlib import Path
import sys

import pandas as pd


# ============================================================
# 1. LOAD EXPORTED PICKS
# ============================================================

if len(sys.argv) < 2:
    print("Usage: python query_jimmy_pregame.py <csv_file>")
    sys.exit(1)

csv_path = Path(sys.argv[1])

if not csv_path.is_file():
    print(f"CSV file not found: {csv_path}")
    sys.exit(1)

df = pd.read_csv(csv_path)

required_columns = [
    "Your Pick",
    "Market Probability",
    "Your Confidence",
]

missing = [col for col in required_columns if col not in df.columns]

if missing:
    print(f"Missing columns: {missing}")
    sys.exit(1)

for col in ["Market Probability", "Your Confidence"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

if df[required_columns].isna().any().any():
    print("CSV contains missing or invalid values.")
    sys.exit(1)


# ============================================================
# 2. CALCULATE OPTIMAL MARKET RANKINGS
# ============================================================

df = df.sort_values(
    "Market Probability",
    ascending=False
).reset_index(drop=True)

# Reassign the same available confidence values.
confidence_values = sorted(
    df["Your Confidence"].astype(int).tolist(),
    reverse=True
)

df["Recommended Confidence"] = confidence_values

df["Confidence Change"] = (
    df["Recommended Confidence"] - df["Your Confidence"]
)


# ============================================================
# 3. EXPECTED POINTS COMPARISON
# ============================================================

probability = df["Market Probability"] / 100

original_expected = (
    probability * df["Your Confidence"]
).sum()

recommended_expected = (
    probability * df["Recommended Confidence"]
).sum()


# ============================================================
# 4. PRINT ESPN-READY RANKINGS
# ============================================================

print("\nJIMMY'S MARKET-OPTIMIZED CONFIDENCE RANKINGS")
print("=" * 85)

print(
    df[
        [
            "Your Pick",
            "Market Probability",
            "Your Confidence",
            "Recommended Confidence",
            "Confidence Change",
        ]
    ].to_string(index=False)
)

print("\nEXPECTED CONFIDENCE POINTS")
print("=" * 85)

print(f"Original allocation:    {original_expected:.2f}")
print(f"Recommended allocation: {recommended_expected:.2f}")
print(f"Expected improvement:   {recommended_expected - original_expected:+.2f}")

print("\nFINAL ESPN CONFIDENCE ORDER")
print("=" * 85)

for _, row in df.iterrows():
    print(
        f"{int(row['Recommended Confidence']):>2}  "
        f"{row['Your Pick']}"
    )
