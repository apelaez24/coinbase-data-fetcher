"""
historical_to_postgres.py

This script loops through all CSVs in 'data/historical',
DROPS each table first (for a fresh load),
then recreates it,
and inserts ALL rows efficiently using execute_values.

Later, this same pattern can handle live streaming too.

Loads PostgreSQL connection info from your .env.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd

# === 1️⃣ CONFIG ===

# Project root: up from /scripts
project_root = Path(__file__).resolve().parent.parent

# Load .env
env_path = project_root / ".env"
load_dotenv(env_path)

# Read DB creds from .env
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

print(f"✅ Loaded DB config from .env: {DB_NAME}@{DB_HOST}:{DB_PORT}")

# Folder with historical CSVs
historical_dir = project_root / "data" / "historical"

# === 2️⃣ CONNECT ===

try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = True
    print(f"✅ Connected to PostgreSQL database: {DB_NAME}")

except Exception as e:
    print("❌ Connection failed:", e)
    exit()

cur = conn.cursor()

# === 3️⃣ LOOP THROUGH HISTORICAL FILES ===

for csv_file in historical_dir.glob("*.csv"):
    # Example: BTCUSD-1d=historical-data.csv → btcusd_1d
    pair_time = csv_file.stem.split("=")[0]
    pair, timeframe = pair_time.split("-")
    table_name = f"{pair.lower()}_{timeframe}"

    print(f"\n📄 Processing {csv_file.name} -> Table: {table_name}")

    # Load CSV
    df = pd.read_csv(csv_file, parse_dates=['datetime'], index_col='datetime').reset_index()

    # === DROP existing table ===
    drop_sql = f"DROP TABLE IF EXISTS {table_name};"
    cur.execute(drop_sql)
    print(f"🗑️  Dropped table if existed: {table_name}")

    # === Recreate table ===
    create_sql = f"""
    CREATE TABLE {table_name} (
        datetime TIMESTAMP PRIMARY KEY,
        open NUMERIC,
        high NUMERIC,
        low NUMERIC,
        close NUMERIC,
        volume NUMERIC
    );
    """
    cur.execute(create_sql)
    print(f"✅ Recreated table: {table_name}")

    # === Bulk insert with execute_values ===
    rows = [
        (
            row['datetime'],
            row['open'],
            row['high'],
            row['low'],
            row['close'],
            row['volume']
        )
        for _, row in df.iterrows()
    ]

    insert_sql = f"""
    INSERT INTO {table_name} (datetime, open, high, low, close, volume)
    VALUES %s
    ON CONFLICT (datetime) DO NOTHING;
    """

    execute_values(cur, insert_sql, rows)
    print(f"✅ Inserted rows for {table_name}: {len(rows)}")

# === 4️⃣ CLEAN UP ===
cur.close()
conn.close()
print("\n🎉 Fresh upload complete — all historical CSVs pushed fast to PostgreSQL!")
