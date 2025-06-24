"""
This script checks the last timestamp in each historical data file
and saves a JSON file so your main data fetcher knows where to resume. 
Run anytime you want new data. 
Assuming historical data is relatively up to date, this script can be run daily or weekly.
"""

import pandas as pd
from pathlib import Path
import json

# === Setup ===
project_dir = Path(__file__).resolve().parent.parent   # 👈 up from /scripts
historical_dir = project_dir / "data" / "historical"
output_file = project_dir / "data" / "last_timestamps.json"   # 👈 inside /data

print(f"📂 Checking historical data in: {historical_dir}")
print(f"💾 Will save last timestamps to: {output_file}")

# === Loop all historical CSVs ===
last_timestamps = {}

for csv_file in historical_dir.glob("*.csv"):
    try:
        # Use new naming convention: PAIR+TIMEFRAME=historical-data.csv
        name = csv_file.stem.split('=')[0]  # e.g., BTCUSD-1m
        print(f"🔍 Checking {csv_file.name}  →  ID: {name}")

        df = pd.read_csv(csv_file, index_col='datetime', parse_dates=True)

        last_ts = df.index.max()
        print(f"⏳  Last timestamp: {last_ts}")

        last_timestamps[name] = last_ts.isoformat()

    except Exception as e:
        print(f"❌ Error reading {csv_file.name}: {e}")

# === Save results ===
with open(output_file, "w") as f:
    json.dump(last_timestamps, f, indent=2)

print(f"\n✅ All last timestamps saved to: {output_file}")
