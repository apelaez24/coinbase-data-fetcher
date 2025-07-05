''''
This script deletes all data from the raw database tables in PostGres. Currently using for testing purposes only.
Could possibly integrate into the orchestrator script to clear raw data before fetching new data

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

# === Connect and truncate raw tables ===
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

    # === List of raw tables ===
    raw_tables = [
        "wifusd_1d_raw", "wifusd_1h_raw", "wifusd_6h_raw",  "wifusd_1d", "wifusd_1h", "wifusd_6h", #this is where you add the raw table names
        # add btc/eth/sol raw tables here once created
    ]

    for table in raw_tables:
        cur.execute(f"DROP TABLE {table};")
        print(f"🗑️ Dropped table {table}")

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    if conn:
        cur.close()
        conn.close()
        print("🔑 DB connection closed.")

### ---------------------------------------------------
'''
Use this in postgres to delete the last 3 rows from the specified table
-----
DELETE FROM wifusd_1h
WHERE datetime IN (
    SELECT datetime FROM wifusd_1h
    ORDER BY datetime DESC
    LIMIT 3
);
'''
