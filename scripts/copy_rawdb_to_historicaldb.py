
''''
This script copies data from the raw table `taousd_1d_raw` to the historical table `taousd_1d`.
It creates the historical table if it doesn't exist, and adds a PRIMARY KEY constraint on the `datetime` column if possible.
Only use when getting new data from coinbase for the first time. Not necessary after we have historical data, 
run the get_new_rawdbcandles.py script instead.

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

    # === Step 1. Create taousd_1m table from taousd_1m_raw ===
    create_table_query = """
    CREATE TABLE IF NOT EXISTS taousd_1m AS
    SELECT * FROM taousd_1m_raw;
    """
    cur.execute(create_table_query)
    print("✅ Created table taousd_1m from taousd_1m_raw")

    # === Step 2. Add PRIMARY KEY constraint on datetime if possible ===
    try:
        cur.execute("""
        ALTER TABLE taousd_1m
        ADD PRIMARY KEY (datetime);
        """)
        print("✅ Added PRIMARY KEY on datetime in taousd_1m")
    except psycopg2.errors.UniqueViolation:
        print("⚠️ Duplicate datetimes found. PRIMARY KEY not added.")
    except psycopg2.errors.DuplicateTable:
        print("⚠️ Table taousd_1m already exists with PRIMARY KEY.")
    except Exception as e:
        print(f"❌ Error adding PRIMARY KEY: {e}")

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    if conn:
        cur.close()
        conn.close()
        print("🔑 DB connection closed.")
