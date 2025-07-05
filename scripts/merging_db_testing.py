# ===== Imports =====
import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os
from pathlib import Path

# === Load .env ===
project_root = Path(__file__).resolve().parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

# === Get DB credentials ===
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# === Connect to Postgres ===
try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = True
    cur = conn.cursor()
    print(f"✅ Connected to database {DB_NAME}")

    # === PARAMETERS ===
    historical_table = "taousd_1d"
    raw_table = "taousd_1d_raw"

    # === Step B1. Get latest datetime in historical table ===
    cur.execute(f"SELECT MAX(datetime) FROM {historical_table};")
    latest_hist = cur.fetchone()[0]

    if latest_hist is None:
        print("⚠️ Historical table is empty. Will insert all raw data.")
        latest_hist = '1970-01-01'  # dummy old date if table is empty

    # === Step B2. Insert only newer rows from raw to historical ===
    insert_query = f"""
    INSERT INTO {historical_table} (datetime, open, high, low, close, volume)
    SELECT datetime, open, high, low, close, volume
    FROM {raw_table}
    WHERE datetime > %s
    ON CONFLICT (datetime) DO NOTHING;
    """

    cur.execute(insert_query, (latest_hist,))
    rows_inserted = cur.rowcount

    print(f"✅ Inserted {rows_inserted} new rows from {raw_table} to {historical_table}")

    # === Step C. Purge raw table ===
    cur.execute(f"TRUNCATE TABLE {raw_table};")
    print(f"🗑️ Purged table {raw_table}")

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    if conn:
        cur.close()
        conn.close()
        print("🔑 DB connection closed.")
