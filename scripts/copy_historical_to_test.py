'''
This script copies historical CSV files 
from "data/historical" to "test_data", 
adding "_TEST" before ".csv".
'''

from pathlib import Path
import shutil

# === CONFIG ===
# This always gets the *real* project root: one level up from /scripts
project_root = Path(__file__).resolve().parent.parent

data_dir = project_root / "data" / "historical"
test_data_dir = project_root / "test_data"
test_data_dir.mkdir(exist_ok=True)

# === LOOP ===
for file in data_dir.glob("*.csv"):
    # Insert _TEST before ".csv"
    test_name = f"{file.stem}_TEST.csv"
    target = test_data_dir / test_name

    print(f"📁 Copying: {file} ➜ {target}")
    shutil.copy2(file, target)

print("✅ All historical CSVs copied to test_data with _TEST suffix.")
