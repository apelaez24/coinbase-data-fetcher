'''
1. Connects to your DB.

2. Loops through each pair and timeframe specified.

3. Prints the 5 most recent timestamps before deletion.

4. Deletes the last N rows (default 10) for testing.

5. Prints the new latest timestamp for confidence.

Run BEFORE you run the orchestrator for testing purposes. 

'''
# ===== Imports =====
import psycopg2
from dotenv import load_dotenv
import os
from pathlib import Path

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
PAIRS = ["wifusd", "taousd"]
TIMEFRAMES = ["1d", "1h", "6h"]
ROWS_TO_DELETE = 10  # 🔥 Adjust as needed

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
            table = f"{pair}_{tf}"
            print(f"\n🔎 Checking {table}...")

            # === Show current latest 5 timestamps ===
            cur.execute(f"SELECT datetime FROM {table} ORDER BY datetime DESC LIMIT 5;")
            rows = cur.fetchall()
            print("🕒 Latest 5 timestamps BEFORE delete:")
            for r in rows:
                print(f"   {r[0]}")

            # === Delete last ROWS_TO_DELETE rows ===
            delete_query = f"""
            DELETE FROM {table}
            WHERE datetime IN (
                SELECT datetime FROM {table}
                ORDER BY datetime DESC
                LIMIT {ROWS_TO_DELETE}
            );
            """
            cur.execute(delete_query)
            print(f"🗑️ Deleted {cur.rowcount} rows from {table}")

            # === Show new latest timestamp ===
            cur.execute(f"SELECT MAX(datetime) FROM {table};")
            new_latest = cur.fetchone()[0]
            print(f"✅ New latest datetime: {new_latest}")

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    if conn:
        cur.close()
        conn.close()
        print("🔑 DB connection closed.")
