"""
This script copies ALL CSVs from 'data/raw' to 'data/historical',
renaming them from '{pair_time}=raw-data.csv' to '{pair_time}=historical-data.csv'.

Original raw files remain unchanged. Only use on setup or when tracking a new crypto pair.
"""

from pathlib import Path
import shutil

# === 1️⃣  Resolve project root ===
project_root = Path(__file__).resolve().parent.parent

# === 2️⃣  Define folders ===
raw_dir = project_root / "data" / "raw"
historical_dir = project_root / "data" / "historical"

# Make sure historical dir exists
historical_dir.mkdir(parents=True, exist_ok=True)

# === 3️⃣  Loop and copy + rename ===
for csv_file in raw_dir.glob("*.csv"):
    # Split at '=' and remove spaces
    parts = csv_file.stem.split("=")
    pair_time = parts[0].strip()

    # New file name
    new_name = f"{pair_time}=historical-data.csv"

    # Full destination path
    destination = historical_dir / new_name

    # Copy file with new name
    shutil.copy(csv_file, destination)

    print(f"✅ Copied and renamed: '{csv_file.name}' ➜ '{destination.name}'")

print("\n🎉 Done! All raw files copied and renamed to historical.")
