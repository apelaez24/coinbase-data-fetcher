'''
This script fetches data based on last timestamps. It first reads the last timestamps from a JSON file,
then fetches new data from Coinbase for each pair and timeframe, then saves it to a "new-data.csv",
which is saved to the following directory:
"SAVE_DIR = project_root / "data" / "append""

'''

import pandas as pd
import datetime
import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
import requests
import math

# === CONFIG ===
TEST_MODE = False  # <--- we want production mode
MAX_LOOKBACK = datetime.timedelta(days=7)

# === PATHS ===
project_root = Path(__file__).resolve().parent
env_path = project_root / ".env"

LAST_TS_FILE = project_root / ("last_timestamps_TEST.json" if TEST_MODE else "last_timestamps.json")

if TEST_MODE:
    SAVE_DIR = project_root / "test_data"
else:
    SAVE_DIR = project_root / "data" / "append"

print(f"Resolved LAST_TS_FILE: {LAST_TS_FILE}")
print(f"Resolved SAVE_DIR: {SAVE_DIR}")
os.makedirs(SAVE_DIR, exist_ok=True)

load_dotenv(env_path)

api_key = os.getenv('COINBASE_API_KEY')
api_secret = os.getenv('COINBASE_API_SECRET')
assert api_key and api_secret, "❌ API credentials missing!"

def timeframe_to_granularity(timeframe):
    if "m" in timeframe:
        return int(''.join(c for c in timeframe if c.isdigit())) * 60
    elif "h" in timeframe:
        return int(''.join(c for c in timeframe if c.isdigit())) * 3600
    elif "d" in timeframe:
        return int(''.join(c for c in timeframe if c.isdigit())) * 86400

# === Load last timestamps ===
if LAST_TS_FILE.exists():
    with open(LAST_TS_FILE, "r") as f:
        json_data = json.load(f)
else:
    json_data = {}

# === PROCESS ===
for id in json_data.keys():
    pair, timeframe = id.split("-")
    symbol = f"{pair[:3]}-{pair[3:].strip()}"  # fix accidental space

    # === New clean save target ===
    save_file = SAVE_DIR / f"{id.strip()}=new-data.csv"

    print(f"\n🚀 Processing {symbol} [{timeframe.strip()}]")
    print(f"💾 Target save: {save_file}")

    # === Figure out starting timestamp ===
    json_last = json_data.get(id).strip()
    best_last = pd.to_datetime(json_last)

    print(f"✅ Using last timestamp: {best_last}")

    granularity = timeframe_to_granularity(timeframe)
    start_time = best_last + datetime.timedelta(seconds=granularity)

    now_ts = math.floor(datetime.datetime.utcnow().timestamp() / granularity) * granularity
    end_time = datetime.datetime.utcfromtimestamp(now_ts)

    if end_time - start_time > MAX_LOOKBACK:
        end_time = start_time + MAX_LOOKBACK
        print(f"⏳ Limiting to max lookback: {start_time} → {end_time}")

    if start_time >= end_time:
        print(f"⏸️  Up-to-date — skipping.")
        continue

    print(f"⏰ Start: {start_time} | End: {end_time} | Granularity: {granularity}s")

    # === Fetch ===
    base_url = "https://api.exchange.coinbase.com"
    path = f"/products/{symbol}/candles"
    max_candles = 300
    chunk_seconds = max_candles * granularity

    all_candles = []
    current_ts = math.floor(start_time.timestamp() // granularity) * granularity
    end_ts = end_time.timestamp()

    while current_ts < end_ts:
        chunk_end_ts = min(current_ts + chunk_seconds, end_ts)
        s_dt = datetime.datetime.utcfromtimestamp(current_ts)
        e_dt = datetime.datetime.utcfromtimestamp(chunk_end_ts)
        print(f"📊 Chunk: {s_dt} → {e_dt}")

        params = {
            "start": s_dt.isoformat(),
            "end": e_dt.isoformat(),
            "granularity": str(granularity)
        }

        for attempt in range(5):
            resp = requests.get(base_url + path, params=params)
            if resp.status_code == 200:
                all_candles.extend(resp.json())
                break
            elif resp.status_code in [500, 502, 503]:
                wait = 2 ** attempt
                print(f"⚠️  {resp.status_code} → retry in {wait}s")
                time.sleep(wait)
            else:
                print(f"❌ {resp.status_code}: {resp.text}")
                raise Exception("API error")

        current_ts = chunk_end_ts
        time.sleep(0.5)

    print(f"✨ New candles fetched: {len(all_candles)}")

    # === Save only new chunk ===
    if all_candles:
        new_df = pd.DataFrame(all_candles)
        new_df.columns = ["datetime", "open", "high", "low", "close", "volume"]
        new_df["datetime"] = pd.to_datetime(new_df["datetime"], unit="s")
        new_df = new_df.set_index("datetime").sort_index()
        new_df.to_csv(save_file)
        print(f"✅ NEW chunk saved: {save_file}")
    else:
        print(f"⏸️  No new candles to save.")

    # === Update JSON ===
    new_latest = new_df.index.max().isoformat() if not new_df.empty else best_last.isoformat()
    json_data[id] = new_latest
    print(f"✅ Updated state: {new_latest}")

# === Write updated JSON ===
with open(LAST_TS_FILE, "w") as f:
    json.dump(json_data, f, indent=2)

print(f"\n🎉 ALL DONE. TEST_MODE = {TEST_MODE} → new chunks in: {SAVE_DIR}")
