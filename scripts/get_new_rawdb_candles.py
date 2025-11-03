''''
Looks at historical data in Postgres and fetches new candles from Coinbase API. Basically doing what
coinbase_data_resumable_all.py does, but only for one symbol and timeframe for now
 
'''


# ===== Imports =====
import pandas as pd
import datetime
import os
from dotenv import load_dotenv
from pathlib import Path
import requests
import time
import psycopg2
from psycopg2.extras import execute_values
import sys

# === Fix Windows Unicode encoding for emojis ===
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# === Load .env ===
project_root = Path(__file__).resolve().parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

# === DB credentials ===
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

api_key = os.getenv('COINBASE_API_KEY')
api_secret = os.getenv('COINBASE_API_SECRET')

SAVE_TO_POSTGRES = True

# === Connect to Postgres ===
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

def sign_request(method, path, body='', timestamp=None):
    timestamp = timestamp or str(int(time.time()))
    headers = {
        'CB-ACCESS-KEY': api_key,
        'CB-ACCESS-TIMESTAMP': timestamp,
        'accept': 'application/json',
        'content-type': 'application/json',
    }
    return headers

def timeframe_to_granularity(timeframe):
    if 'm' in timeframe:
        return int(''.join([c for c in timeframe if c.isnumeric()])) * 60
    elif 'h' in timeframe:
        return int(''.join([c for c in timeframe if c.isnumeric()])) * 3600
    elif 'd' in timeframe:
        return int(''.join([c for c in timeframe if c.isnumeric()])) * 86400

def fetch_new_data(symbol, timeframe):
    base_url = "https://api.exchange.coinbase.com"

    # === Get latest datetime in historical table ===
    pair = symbol.replace('-', '').lower()
    hist_table = f"{pair}_{timeframe}_raw".replace("_raw", "")
    cur.execute(f"SELECT MAX(datetime) FROM {hist_table};")
    latest = cur.fetchone()[0]

    granularity = timeframe_to_granularity(timeframe)

    if latest is None:
        print("⚠️ No data in historical table. Starting from default (2010-07-17).")
        start_time = datetime.datetime(2010, 7, 17)  # Oldest BTC timestamp for safety
    else:
        # ✅ Adjust to fetch starting from NEXT candle to avoid re-fetching last
        start_time = latest + datetime.timedelta(seconds=granularity)
        print(f"🔍 Latest datetime in historical: {latest}")
        print(f"➡️  Fetching starting from next candle: {start_time}")
        
    # ✅ Enforce UTC timezone awareness
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=datetime.timezone.utc)

    end_time = datetime.datetime.utcnow()
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=datetime.timezone.utc)
    
    max_candles = 300
    chunk_seconds = max_candles * granularity

    all_candles = []
    current_start_ts = int(start_time.timestamp())
    end_ts = int(end_time.timestamp())

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
        for attempt in range(5):
            response = requests.get(f"{base_url}{path}", params=params)
            if response.status_code == 200:
                candles = response.json()
                all_candles.extend(candles)
                break
            elif response.status_code in [500, 502, 503, 504]:
                time.sleep(2 ** attempt)
            else:
                raise Exception(f"API Error: {response.status_code} - {response.text}")

        current_start_ts = current_end_ts
        time.sleep(0.5)

    print(f"✨ Fetched {len(all_candles)} candles!")

    if all_candles:
        df = pd.DataFrame(all_candles, columns=['datetime','low','high','open','close','volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='s')
        df = df[['datetime','open','high','low','close','volume']]
        df = df.sort_values('datetime')

        # === Insert into _raw table ===
        raw_table = f"{pair}_{timeframe}_raw"
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

        rows = [tuple(r) for r in df.to_numpy()]
        execute_values(
            cur,
            f"""
            INSERT INTO {raw_table} (datetime, open, high, low, close, volume)
            VALUES %s
            ON CONFLICT (datetime) DO NOTHING;
            """,
            rows
        )
        print(f"✅ Inserted {len(rows)} rows into {raw_table}")

# ==== MAIN RUN ====

SYMBOL = os.getenv("SYMBOL", "TAO-USD") # Default to TAO-USD if not set
TIMEFRAME = os.getenv("TIMEFRAME", "1d") # Default to 1d if not set

fetch_new_data(SYMBOL, TIMEFRAME)

cur.close()
conn.close()
print("🔑 DB connection closed.")



