'''
Orchestrator v5: Adds BTC, ETH, SOL, TAO orchestration with schema verification, backups, and execution timer.
'''

# ===== Imports =====
import psycopg2
from dotenv import load_dotenv
import os
from pathlib import Path
import subprocess
import time
import sys

# === Fix Windows Unicode encoding for emojis ===
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# === Start timer ===
start_time = time.time()

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

# === CONFIG ===
PAIRS = ["TAO-USD", "BTC-USD", "ETH-USD", "SOL-USD"]
TIMEFRAMES = ["1d", "6h", "1h", "5m", "1m"]

expected_columns_types = [
    ('datetime', 'timestamp without time zone'),
    ('open', 'numeric'),
    ('high', 'numeric'),
    ('low', 'numeric'),
    ('close', 'numeric'),
    ('volume', 'numeric')
]

# === Define pre-run table check ===
def pre_run_check(cur, table_name):
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = %s
        );
    """, (table_name,))
    exists = cur.fetchone()[0]

    if not exists:
        print(f"⚠️ Table {table_name} missing. Creating it.")
        cur.execute(f"""
            CREATE TABLE {table_name} (
                datetime TIMESTAMP PRIMARY KEY,
                open NUMERIC,
                high NUMERIC,
                low NUMERIC,
                close NUMERIC,
                volume NUMERIC
            );
        """)
        return True

    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position;
    """, (table_name,))
    columns_types = cur.fetchall()

    if columns_types != expected_columns_types:
        print(f"❌ Schema/type mismatch in {table_name}. Found: {columns_types}")
        return False

    print(f"✅ Schema verified for {table_name}")
    return True

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

    for pair in PAIRS:
        for tf in TIMEFRAMES:
            symbol_clean = pair.replace('-', '').lower()
            historical_table = f"{symbol_clean}_{tf}"
            raw_table = f"{symbol_clean}_{tf}_raw"

            print(f"\n🔎 Processing {pair} {tf}...")

            if not pre_run_check(cur, historical_table):
                continue
            if not pre_run_check(cur, raw_table):
                continue

            cur.execute(f"SELECT COUNT(*) FROM {historical_table};")
            prev_count = cur.fetchone()[0]
            print(f"🔢 Previous row count: {prev_count}")

            cur.execute(f"SELECT MAX(datetime) FROM {historical_table};")
            latest_hist = cur.fetchone()[0]

            if latest_hist is None:
                print("⚠️ Historical table empty, setting earliest date.")
                latest_hist = '2015-01-01'
            else:
                print(f"🔍 Latest datetime in historical: {latest_hist}")

            print("🚀 Running fetch script...")
            fetch_env = os.environ.copy()
            fetch_env["SYMBOL"] = pair
            fetch_env["TIMEFRAME"] = tf

            subprocess.run(
                ["python", "scripts/get_new_rawdb_candles.py"],
                check=True,
                env=fetch_env
            )

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

            cur.execute(f"TRUNCATE TABLE {raw_table};")
            print(f"🗑️ Purged table {raw_table}")

            cur.execute(f"SELECT COUNT(*) FROM {historical_table};")
            new_count = cur.fetchone()[0]
            print(f"📊 New row count: {new_count}")
            print(f"🌟 Rows inserted this run: {new_count - prev_count}")

    subprocess.run(["python", "scripts/db_backup.py"], check=True)

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    if conn:
        cur.close()
        conn.close()
        print("🔑 DB connection closed.")

# === Print total runtime ===
end_time = time.time()
print(f"⏱️ Total script runtime: {round(end_time - start_time, 2)} seconds")
