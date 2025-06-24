'''
This is the last script in the series, which verifies and normalizes backup filenames for historical data. 
Run this last for backups of historical data.
'''

import shutil
import filecmp
from pathlib import Path


# === CONFIG ===
project_root = Path(__file__).resolve().parent.parent  # from /scripts → root
historical_dir = project_root / "data" / "historical"
backup_dir = project_root / "data" / "backup"

# === Ensure backup folder exists ===
backup_dir.mkdir(parents=True, exist_ok=True)

# === Reporting lists ===
unchanged = []
copied = []
renamed = []
missing_in_backup = []


# === Loop over all historical .csv files ===
for hist_file in historical_dir.glob("*.csv"):
    # Extract pair + timeframe for standardized name
    pair_timeframe = hist_file.stem.split("=")[0]  # e.g., BTCUSD-1d
    target_backup_name = f"{pair_timeframe}=backup.csv"
    backup_file = backup_dir / target_backup_name

    # --- Check for legacy backup files ---
    # E.g. BTCUSD-1d=raw-data.csv → BTCUSD-1d=backup.csv
    legacy_matches = list(backup_dir.glob(f"{pair_timeframe}=raw-data.csv"))
    for legacy in legacy_matches:
        legacy.rename(backup_file)
        print(f"🔑 Renamed old backup: {legacy.name} → {backup_file.name}")
        renamed.append(f"{legacy.name} → {backup_file.name}")

    # If backup version exists now (renamed or previously correct):
    if backup_file.exists():
        same = filecmp.cmp(hist_file, backup_file, shallow=False)
        if same:
            print(f"✅ Unchanged: {backup_file.name}")
            unchanged.append(backup_file.name)
        else:
            shutil.copy2(hist_file, backup_file)
            print(f"🔄 Updated: {backup_file.name} (new version copied)")
            copied.append(backup_file.name)
    else:
        # If still missing, copy as new backup
        shutil.copy2(hist_file, backup_file)
        print(f"🆕 Created: {backup_file.name} (was missing in backup)")
        missing_in_backup.append(backup_file.name)

# === Final summary ===
print("\n=== ✅ BACKUP SYNC SUMMARY ===")
print(f"Unchanged: {unchanged if unchanged else 'None'}")
print(f"Updated:   {copied if copied else 'None'}")
print(f"Renamed:   {renamed if renamed else 'None'}")
print(f"Newly backed up: {missing_in_backup if missing_in_backup else 'None'}")

print("\n🎉 Done! Verified + normalized backup filenames, synced up-to-date versions.")
