from analysis.data_pipeline import build_master_results_from_supabase
from analysis.pickem_analyzer import confidence_level_performance

df = build_master_results_from_supabase()

performance = confidence_level_performance(df)

print(performance.to_string(index=False))