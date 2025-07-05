"""
db_backup.py
Creates a timestamped dump of the entire database,
compresses it with gzip, and deletes backups older than 7 days.
"""

import os
import datetime
import time
from dotenv import load_dotenv
from pathlib import Path
import subprocess
import gzip
import shutil

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

# === Backup output directory ===
backup_dir = project_root / "data" / "backup" / "sql"
backup_dir.mkdir(parents=True, exist_ok=True)

# === Filename with timestamp ===
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = backup_dir / f"{DB_NAME}_backup_{timestamp}.sql"

# === Set environment variable for pg_dump authentication ===
os.environ["PGPASSWORD"] = DB_PASSWORD

try:
    # === Run pg_dump ===
    subprocess.run([
        "pg_dump",
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", DB_USER,
        "-F", "p",           # Plain SQL format for easy gzip compression
        "-v",                # Verbose
        "-f", str(backup_file),
        DB_NAME
    ], check=True)
    print(f"✅ Database backup successful: {backup_file}")

    # === Compress the backup ===
    compressed_file = str(backup_file) + ".gz"
    with open(backup_file, 'rb') as f_in:
        with gzip.open(compressed_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(backup_file)
    print(f"✅ Compressed backup saved: {compressed_file}")

    # === Delete backups older than 30 days ===
    retention_days = 30
    now = time.time()

    for file in backup_dir.glob("*.gz"):
        if file.stat().st_mtime < now - retention_days * 86400:
            file.unlink()
            print(f"🗑️ Deleted old backup: {file.name}")

except subprocess.CalledProcessError as e:
    print(f"❌ Backup failed: {e}")

finally:
    # Clean up sensitive env var
    del os.environ["PGPASSWORD"]
