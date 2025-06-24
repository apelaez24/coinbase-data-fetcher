''''
This script is just to check when was the last time you gathered data from the coinbase API. 
It is so you can make sure you only grab missing data and not duplicate data. 

'''

# check_all_last_timestamps.py

import pandas as pd
from pathlib import Path
import json

# === Setup ===
project_dir = Path(__file__).parent
data_dir = project_dir / "data"
output_file = project_dir / "last_timestamps.json"

# === Loop all CSVs ===
last_timestamps = {}

for csv_file in data_dir.glob("*.csv"):
    try:
        # Clean identifier: remove =...wks-data.csv
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

print(f"✅ All last timestamps saved to {output_file}")
