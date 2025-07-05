"""
db_restore.py

Restores your Postgres DB from a backup SQL file.
"""

import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# === Load .env ===
project_root = Path(__file__).resolve().parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# === Path to backup ===
backup_dir = project_root / "data" / "backup" / "sql"

# === Get latest backup file ===
try:
    latest = max(backup_dir.glob("*.sql"), key=os.path.getctime)
except ValueError:
    print("❌ No backup files found.")
    exit(1)

print(f"💾 Latest backup: {latest}")

# === Confirm restore DB name ===
restore_db = input(f"Enter database name to restore into (default={DB_NAME}): ").strip()
if restore_db == "":
    restore_db = DB_NAME

print(f"⚠️ Restoring INTO DATABASE: {restore_db}")

# === Auth for psql ===
os.environ["PGPASSWORD"] = DB_PASSWORD

# === Drop DB and recreate ===
print(f"🗑️ Dropping database {restore_db} if it exists...")
subprocess.run([
    "psql",
    "-h", DB_HOST,
    "-p", DB_PORT,
    "-U", DB_USER,
    "-c", f"DROP DATABASE IF EXISTS {restore_db};"
], check=True)

print(f"🆕 Creating database {restore_db}...")
subprocess.run([
    "psql",
    "-h", DB_HOST,
    "-p", DB_PORT,
    "-U", DB_USER,
    "-c", f"CREATE DATABASE {restore_db};"
], check=True)

# === Run restore ===
print(f"🔄 Restoring from {latest} into {restore_db}...")
subprocess.run([
    "psql",
    "-h", DB_HOST,
    "-p", DB_PORT,
    "-U", DB_USER,
    "-d", restore_db,
    "-f", str(latest)
], check=True)

print("✅ Restore complete!")

# Clean env
del os.environ["PGPASSWORD"]
