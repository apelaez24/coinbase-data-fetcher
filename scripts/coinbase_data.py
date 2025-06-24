'''
STEPS TO USE
1. create a .env file that looks like this:
    COINBASE_API_KEY="organizations/{org_id}/apiKeys/{key_id}"
    COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----\nYOUR PRIVATE KEY\n------END EC PRIVATE KEY-----\n"
2. select the symbol you want to fetch data for
3. select the timeframe you want to fetch data for
4. select the number of weeks of data to fetch
5. run the script 
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

# Get the project root directory (2 levels up from this file)
project_root = Path(__file__).parent  # NOT .parent.parent
env_path = project_root / '.env'

#===== Angel's Configurations =====
SYMBOL = 'WIF-USD'   # Trading pair symbol (e.g., 'BTC-USD', 'ETH-USD', 'SOL-USD')
TIMEFRAME = '1d'     # timeframe (e.g., '1m', '5m', '1h', '6h', '1d')
WEEKS = 2         # How many weeks of data to fetch. Adjust as needed
SAVE_DIR = project_root / 'data' #Directory to save the data files, we can update this later
# Create save directory if it doesn't exist
os.makedirs(SAVE_DIR, exist_ok=True)
print(f"📁 Save directory ready: {SAVE_DIR}")

# === Get project root ===
project_root = Path(__file__).resolve().parent.parent  # 👈 from /scripts up to root

# === .env file location ===
env_path = project_root / ".env"

# === Directory for saving raw data ===
SAVE_DIR = project_root / "data" / "raw"  # 👈 place raw fetches in /data/raw

# === Make sure it exists ===
os.makedirs(SAVE_DIR, exist_ok=True)

print(f"📁 Save directory ready: {SAVE_DIR}")
print(f"🔍 Looking for .env file in: {env_path}")

# === Load env ===
load_dotenv(env_path)

api_key = os.getenv('COINBASE_API_KEY')
api_secret = os.getenv('COINBASE_API_SECRET')
print("🔑 API Key loaded:", "✅" if api_key else "❌")
print("🔒 API Secret loaded:", "✅" if api_secret else "❌")

if not api_key or not api_secret:
    print("❌ Error: API credentials not found in .env file")
    print("💡 Make sure your .env file exists and contains:")
    print("  COINBASE_API_KEY=organizations/{org_id}/apiKeys/{key_id}")
    print("  COINBASE_API_SECRET=your-secret-key")
    raise ValueError("Missing API credentials")

print("🌙 Coinbase Data Fetcher Initialized! 🚀")

def sign_request(method, path, body='', timestamp=None):
    "Sign a request using the API secret"
    timestamp = timestamp or str(int(time.time()))
    
    # Remove the '/api/v3/brokerage' prefix from path for signing
    if path.startswith('/api/v3/brokerage'):
        path = path[len('/api/v3/brokerage'):]
        
    # Create the message to sign
    message = f"{timestamp}{method}{path}{body}"
    
    try:
        # Print debug info without exposing secrets
        print(f"✍️ Signing request for: {method} {path}")
        # Create JWT token
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
    "Convert timeframe to granularity in seconds"
    if 'm' in timeframe:
        return int(''.join([char for char in timeframe if char.isnumeric()])) * 60
    elif 'h' in timeframe:
        return int(''.join([char for char in timeframe if char.isnumeric()])) * 60 * 60
    elif 'd' in timeframe:
        return int(''.join([char for char in timeframe if char.isnumeric()])) * 24 * 60 * 60

def get_historical_data(symbol, timeframe, weeks):
    print(f"🔍 Script is fetching {weeks} weeks of {timeframe} data for {symbol}")

    # Where to save
    output_file = SAVE_DIR / f"{symbol.replace('-', '')}-{timeframe}=raw-data.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)  # always safe!

    if output_file.exists():
        print(f"📁 Found existing data file!")
        return pd.read_csv(output_file)

    try:
        # Test API connection (product details)
        print("🌐 Testing API connection...")
        base_url = "https://api.exchange.coinbase.com"
        path = '/products/' + symbol

        # ⚡ For product details, you can sign (optional)
        headers = sign_request('GET', path)
        response = requests.get(f"{base_url}{path}", headers=headers)

        if response.status_code != 200:
            print(f"❌ Response Headers: {response.headers}")
            print(f"❌ Response Body: {response.text}")
            raise Exception(f"API Error: {response.status_code} - {response.text}")

        print("+ Connection test successful!")

        # === Chunk setup ===
        end_time = datetime.datetime.utcnow()
        start_time = end_time - datetime.timedelta(weeks=weeks)
        # After you compute start_time:
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

        print(f"📊 Using {chunk_seconds} second chunks for {timeframe} timeframe")

        # Align start timestamp to granularity boundary
        import math
        start_ts = math.floor(start_time.timestamp() // granularity) * granularity
        end_ts = end_time.timestamp()

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

            # === ✅ Robust retry ===
            success = False
            for attempt in range(5):  # try up to 5 times
                response = requests.get(f"{base_url}{path}", params=params)

                if response.status_code == 200:
                    candles = response.json()
                    all_candles.extend(candles)
                    success = True
                    break

                elif response.status_code in [500, 502, 503, 504]:
                    wait_sec = 2 ** attempt  # exponential backoff
                    print(f"⚠️  {response.status_code} error → retrying in {wait_sec} sec...")
                    time.sleep(wait_sec)
                else:
                    print(f"❌ Response Headers: {response.headers}")
                    print(f"❌ Response Body: {response.text}")
                    raise Exception(f"API Error: {response.status_code} - {response.text}")

            if not success:
                print(f"⚠️  Giving up on chunk {start_dt} to {end_dt} after retries. Skipping.")
                # Do NOT crash — just move to next chunk

            current_start_ts = current_end_ts
            time.sleep(0.5)  # gentle pacing

        print(f"✨ Successfully fetched {len(all_candles)} candles!")

        # === To DataFrame ===
        df = pd.DataFrame(all_candles)
        df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
        df['datetime'] = pd.to_datetime(df['datetime'], unit='s')
        df = df.set_index('datetime').sort_index()

        df.to_csv(output_file)
        print(f"📁 Data saved to {output_file}")

        return df

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("💡 Tips:")
        print("  1. Make sure your dates are realistic")
        print("  2. Check timeframe vs weeks for total candles")
        print("  3. Double-check API keys if other endpoints fail")
        raise

print(get_historical_data(SYMBOL, TIMEFRAME, WEEKS))


