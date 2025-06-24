'''
This script checks and merges new data files with our existing historical data.
It makes sure we only append new timestampes, deduplicates, and saves the results back to the historical files.
If there are no new timestamps, it skips the merge for that pair.
It also verifies the frequency of the timestamps and provides a final summary of merged and skipped pairs.
'''


import pandas as pd
from pathlib import Path

# === CONFIG ===
# Always resolve project root: this works even if the script is in /scripts
project_root = Path(__file__).resolve().parent.parent

append_dir = project_root / "data" / "append"
historical_dir = project_root / "data" / "historical"

# For final summary:
merged_pairs = []
skipped_pairs = []

# === Loop through all =new-data.csv files ===
for new_data_file in append_dir.glob("*=new-data.csv"):
    pair_timeframe = new_data_file.stem.split('=')[0]  # e.g., BTCUSD-1d

    # Find the corresponding historical file
    hist_file = historical_dir / f"{pair_timeframe}=historical-data.csv"

    if not hist_file.exists():
        print(f"❌ Could not find historical file for: {pair_timeframe}")
        skipped_pairs.append(pair_timeframe)
        continue

    print(f"\n=== 📁 Processing: {pair_timeframe} ===")
    print(f"📂 Historical: {hist_file.name}")
    print(f"📂 New:        {new_data_file.name}")

    # Load both
    df_hist = pd.read_csv(hist_file, index_col='datetime', parse_dates=True)
    df_new = pd.read_csv(new_data_file, index_col='datetime', parse_dates=True)

    print(f"✅ Historical rows: {len(df_hist)}")
    print(f"✅ New rows:        {len(df_new)}")

    # === Compute truly new timestamps
    only_new = df_new[~df_new.index.isin(df_hist.index)]
    num_new_unique = len(only_new)

    if num_new_unique == 0:
        print(f"⚠️  No NEW unique timestamps found — SKIPPING merge/save for this pair.")
        skipped_pairs.append(pair_timeframe)
        continue
    else:
        print(f"➕ Newly unique timestamps in new data: {num_new_unique}")

    # === Merge: only hist + truly new
    df_merged = pd.concat([df_hist, only_new])
    print(f"🔍 Combined before deduplication: {len(df_merged)} rows")

    # Drop duplicates (safe)
    df_merged = df_merged[~df_merged.index.duplicated(keep='last')]
    df_merged = df_merged.sort_index()
    print(f"✨ After deduplication: {len(df_merged)} rows")

    # Range checks
    print(f"📅 Historical: {df_hist.index.min()} → {df_hist.index.max()}")
    print(f"📅 New:        {df_new.index.min()} → {df_new.index.max()}")
    print(f"📅 Final:      {df_merged.index.min()} → {df_merged.index.max()}")

    # Verify frequency
    try:
        freq = pd.infer_freq(df_merged.index)
        if freq:
            expected = pd.date_range(df_merged.index.min(), df_merged.index.max(), freq=freq)
            missing = expected.difference(df_merged.index)
            if missing.empty:
                print(f"✅ No missing timestamps detected. Frequency: {freq}")
            else:
                print(f"⚠️  WARNING: Missing timestamps: {missing}")
        else:
            print(f"⚠️  Could not infer frequency.")
    except Exception as e:
        print(f"⚠️  Could not check frequency: {e}")

    # === Save back to historical ===
    df_merged.to_csv(hist_file)
    print(f"💾 Merged + deduped data saved to: {hist_file.name}")

    # Sanity check
    df_check = pd.read_csv(hist_file, index_col='datetime', parse_dates=True)
    assert len(df_check) == len(df_merged), "Saved file does not match merged DataFrame!"
    print(f"✅ Verified saved version: {len(df_check)} rows match in-memory merge.")

    merged_pairs.append(pair_timeframe)

# === FINAL SUMMARY ===
print("\n=== ✅ FINAL SUMMARY ===")
print(f"Pairs MERGED: {merged_pairs if merged_pairs else 'None'}")
print(f"Pairs SKIPPED (up-to-date): {skipped_pairs if skipped_pairs else 'None'}")

print("\n🎉 All done! Checked & merged only if needed, with final summary.")