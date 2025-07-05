"""
Get earliest and latest timestamps for ALL tables in coinbase_data DB.
"""

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
    print(f"✅ Connected to database {DB_NAME}")

    cur = conn.cursor()

    # === Get list of tables ===
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cur.fetchall()]

    results = []

    # === Loop through each table to get min/max datetime ===
    for table in tables:
        cur.execute(f"""
            SELECT 
                MIN(datetime) AS earliest, 
                MAX(datetime) AS latest,
                COUNT(*) AS rows
            FROM {table};
        """)
        data = cur.fetchone()
        earliest, latest, rows = data
        results.append({
            'table': table,
            'earliest': earliest,
            'latest': latest,
            'rows': rows
        })

    df = pd.DataFrame(results)
    pd.set_option('display.max_rows', None)
    print(df)

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    if conn:
        conn.close()
        print("🔑 DB connection closed.")
