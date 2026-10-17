from analysis.data_pipeline import (
    build_master_results_from_supabase,
)

from analysis.pickem_analyzer import (
    confidence_ranking_efficiency,
)

df = build_master_results_from_supabase()

results = confidence_ranking_efficiency(df)

print("\nCONFIDENCE RANKING EFFICIENCY")
print("=" * 85)

print(results.to_string(index=False))