'''
This script renames historical CSV files in the 'data/historical' directory.
It strips accidental spaces, ensures consistent naming, and fixes misnamed files.
'''

from pathlib import Path

# === RESOLVE project root ===
project_root = Path(__file__).resolve().parent.parent  # e.g., from /scripts up to root

# === FOLDER ===
historical_dir = project_root / "data" / "historical"

# === LOOP & RENAME ===
for csv_file in historical_dir.glob("*.csv"):
    # Split at '=' and strip leading/trailing spaces
    parts = csv_file.stem.split("=")
    pair_time = parts[0].strip()

    new_name = f"{pair_time}=historical-data.csv"
    target = csv_file.with_name(new_name)

    print(f"🔍 Checking: '{csv_file.name}'  vs.  '{new_name}'")

    if csv_file.name.strip() == new_name.strip():
        print(f"✅ Already named correctly: {csv_file.name}")
        continue

    csv_file.rename(target)
    print(f"🔄 Renamed: '{csv_file.name}' ➜ '{target.name}'")

print("\n🎉 Done! All historical files renamed consistently.")
