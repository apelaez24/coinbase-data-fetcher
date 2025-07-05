'''
STEPS TO USE
1. create a .env file that looks like this:
    COINBASE_API_KEY="organizations/{org_id}/apiKeys/{key_id}"
    COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----\nYOUR PRIVATE KEY\n------END EC PRIVATE KEY-----\n"
2. select the symbol you want to fetch data for
3. select the timeframe you want to fetch data for
4. select the number of weeks of data to fetch
5. run the script. THIS IS ONLY FOR POSTGRES, NOT FOR CSVs
'''


# ===== Imports =====
import pandas as pd
import datetime
import os
from dotenv import load_dotenv
from math import ceil
from pathlib import Path
import requests
import time
import hmac
import hashlib
import base64
import json
from urllib.parse import urlencode
import psycopg2
from psycopg2.extras import execute_values

# === Get project root ===
project_root = Path(__file__).resolve().parent.parent  # 👈 from /scripts up to root
env_path = project_root / ".env"

# === Directory for saving raw data ===
SAVE_DIR = project_root / "data" / "raw"  # 👈 place raw fetches in /data/raw
os.makedirs(SAVE_DIR, exist_ok=True)
print(f"📁 Save directory ready: {SAVE_DIR}")
print(f"🔍 Looking for .env file in: {env_path}")

# === Load env ===
load_dotenv(env_path)

api_key = os.getenv('COINBASE_API_KEY')
api_secret = os.getenv('COINBASE_API_SECRET')
SAVE_TO_POSTGRES = os.getenv("SAVE_TO_POSTGRES", "False").lower() == "true"

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

print("🔑 API Key loaded:", "✅" if api_key else "❌")
print("🔒 API Secret loaded:", "✅" if api_secret else "❌")
print(f"📦 Save to Postgres? {SAVE_TO_POSTGRES}")

if SAVE_TO_POSTGRES:
    # Connect to Postgres database
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = True
    cur = conn.cursor()
    print(f"✅ Connected to DB: {DB_NAME}")

if not api_key or not api_secret:
    print("❌ Error: API credentials not found in .env file")
    raise ValueError("Missing API credentials")

print("🌙 Coinbase Data Fetcher Initialized! 🚀")

def sign_request(method, path, body='', timestamp=None):
    timestamp = timestamp or str(int(time.time()))
    if path.startswith('/api/v3/brokerage'):
        path = path[len('/api/v3/brokerage'):]
    message = f"{timestamp}{method}{path}{body}"

    try:
        print(f"✍️ Signing request for: {method} {path}")
        headers = {
            'CB-ACCESS-KEY': api_key,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'accept': 'application/json',
            'content-type': 'application/json',
        }
        return headers
    except Exception as e:
        print(f"❌ Error generating signature: {str(e)}")
        raise

def timeframe_to_granularity(timeframe):
    if 'm' in timeframe:
        return int(''.join([char for char in timeframe if char.isnumeric()])) * 60
    elif 'h' in timeframe:
        return int(''.join([char for char in timeframe if char.isnumeric()])) * 60 * 60
    elif 'd' in timeframe:
        return int(''.join([char for char in timeframe if char.isnumeric()])) * 24 * 60 * 60

def get_historical_data(symbol, timeframe, weeks):
    print(f"🔍 Script is fetching {weeks} weeks of {timeframe} data for {symbol}")

    output_file = SAVE_DIR / f"{symbol.replace('-', '')}-{timeframe}=raw-data.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if output_file.exists() and not SAVE_TO_POSTGRES:
        print(f"📁 Found existing data file!")
        return pd.read_csv(output_file)

    try:
        base_url = "https://api.exchange.coinbase.com"
        path = '/products/' + symbol
        headers = sign_request('GET', path)
        response = requests.get(f"{base_url}{path}", headers=headers)

        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")

        print("+ Connection test successful!")

        end_time = datetime.datetime.utcnow()
        start_time = end_time - datetime.timedelta(weeks=weeks)

        # === Adjust start_time if earlier than allowed ===
        if timeframe == '1m':
            earliest_allowed = datetime.datetime(2017, 1, 1)
        elif timeframe == '5m':
            earliest_allowed = datetime.datetime(2016, 1, 1)
        else:
            earliest_allowed = datetime.datetime(2015, 1, 1)

        if start_time < earliest_allowed:
            print(f"⏳ Adjusting start_time from {start_time} to {earliest_allowed} for {timeframe} candles.")
            start_time = earliest_allowed

        granularity = timeframe_to_granularity(timeframe)
        max_candles = 300
        chunk_seconds = max_candles * granularity

        start_ts = int(start_time.timestamp())
        end_ts = int(end_time.timestamp())

        all_candles = []
        current_start_ts = start_ts

        while current_start_ts < end_ts:
            current_end_ts = min(current_start_ts + chunk_seconds, end_ts)
            start_dt = datetime.datetime.utcfromtimestamp(current_start_ts)
            end_dt = datetime.datetime.utcfromtimestamp(current_end_ts)

            print(f"📊 Fetching from {start_dt} to {end_dt}")

            params = {
                'start': start_dt.isoformat(),
                'end': end_dt.isoformat(),
                'granularity': str(granularity)
            }

            path = f"/products/{symbol}/candles"
            success = False
            for attempt in range(5):
                response = requests.get(f"{base_url}{path}", params=params)
                if response.status_code == 200:
                    candles = response.json()
                    all_candles.extend(candles)
                    success = True
                    break
                elif response.status_code in [500, 502, 503, 504]:
                    wait_sec = 2 ** attempt
                    print(f"⚠️ {response.status_code} error → retrying in {wait_sec} sec...")
                    time.sleep(wait_sec)
                else:
                    raise Exception(f"API Error: {response.status_code} - {response.text}")

            if not success:
                print(f"⚠️ Giving up on chunk {start_dt} to {end_dt} after retries.")

            current_start_ts = current_end_ts
            time.sleep(0.5)

        print(f"✨ Successfully fetched {len(all_candles)} candles!")

        df = pd.DataFrame(all_candles)
        df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
        df['datetime'] = pd.to_datetime(df['datetime'], unit='s')
        df = df.set_index('datetime').sort_index()

        if SAVE_TO_POSTGRES:
            # ✅ Convert datetime64 to Python datetime before inserting into Postgres
            df_reset = df.reset_index()
            df_reset['datetime'] = pd.to_datetime(df_reset['datetime']).dt.to_pydatetime()

            # Create table name
            pair, timeframe_clean = symbol.replace('-', ''), timeframe
            raw_table = f"{pair.lower()}_{timeframe_clean}_raw"

            # Create table if not exists
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {raw_table} (
                datetime TIMESTAMP PRIMARY KEY,
                open NUMERIC,
                high NUMERIC,
                low NUMERIC,
                close NUMERIC,
                volume NUMERIC
            );
            """)

            # Insert rows
            rows = [tuple(r) for r in df_reset.to_numpy()]

            execute_values(
                cur,
                f"""
                INSERT INTO {raw_table} (datetime, open, high, low, close, volume)
                VALUES %s
                ON CONFLICT (datetime) DO NOTHING;
                """,
                rows
            )
            print(f"✅ Inserted {len(rows)} rows to {raw_table}")

        else:
            df.to_csv(output_file)
            print(f"📁 Data saved to {output_file}")

        return df

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise

# ==== MAIN RUN ====
SYMBOL = 'TAO-USD' # Trading pair symbol (e.g., 'BTC-USD', 'ETH-USD', 'SOL-USD')
TIMEFRAME = '1m' # timeframe (e.g., '1m', '5m', '1h', '6h', '1d')
WEEKS = 200 # How many weeks of data to fetch. Adjust as needed

print(get_historical_data(SYMBOL, TIMEFRAME, WEEKS))

if SAVE_TO_POSTGRES:
    cur.close()
    conn.close()
    print("🔑 DB connection closed.")