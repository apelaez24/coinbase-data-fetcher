# Coinbase Historical Crypto Data Fetcher

📈 **Description**  
This Python repository helps you fetch, store, and maintain historical cryptocurrency candles from Coinbase for any trading pair (e.g. BTC-USD, ETH-USD), with **full support for PostgreSQL pipelines** alongside CSV workflows.

🔗 [Get your Coinbase API Key here](https://www.coinbase.com/developer-platform/products/exchange-api)


---

## ✅ Key Scripts Quick Overview

| Script                              | Purpose                                                      |
| ----------------------------------- | ------------------------------------------------------------ |
| `coinbase_data.py`                  | Fetch large initial historical data (CSV)                    |
| `coinbase_data_db.py`               | Fetch large initial historical data (Postgres)               |
| `copy_rawdb_to_historicaldb.py`     | Copy raw DB tables to historical DB tables                   |
| `orchestrator_db.py`                | Main orchestrator for all pairs & timeframes (Postgres)      |
| `get_new_rawdb_candles.py`          | Fetch new candles for a single symbol + timeframe (Postgres) |
| `check_table_timestamps.py`         | Inspect earliest and latest timestamps for each table        |
| `verify_and_delete_test_rows.py`    | Delete last N rows from historical tables for testing        |
| `db_backup.py`                      | Full database dump + gzip compression                        |
| `merge_append.py`                   | Append new CSV chunks to historical                          |
| `rename_raw_to_historical_files.py` | Copy & rename raw CSVs → historical                          |
| `verify_and_backup.py`              | Sync backups with historical                                 |

---

## 📁 Project Folder Structure

```
COINBASE_DATA/
├── data/
│   ├── append/                  # New data chunks waiting to be merged (CSV)
│   ├── backup/
│   │   ├── sql/                 # Postgres backups (.sql.gz files)
│   ├── historical/              # Main source of truth (cleaned, full history) - CSV
│   ├── raw/                     # Raw fetched data before renaming - CSV
│   ├── last_timestamps.json     # Tracks last fetched candle per pair
│   ├── last_timestamps_TEST.json # Sample JSON for test mode
│   └── .gitkeep
├── scripts/
│   ├── [All scripts listed above]
├── test_data/                   # For test mode
├── .env                         # Contains your API credentials
├── .gitignore
├── README.md
├── requirements.txt
```

---

## ⚙️ Setup

### 1️⃣ Clone the Repo

```
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

### 2️⃣ Install Dependencies

```
pip install -r requirements.txt
```

### 3️⃣ Create .env

```env
COINBASE_API_KEY="organizations/{org_id}/apiKeys/{key_id}"
COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----\nYOUR PRIVATE KEY\n-----END EC PRIVATE KEY-----\n"

# Postgres
DB_NAME="coinbase_data"
DB_USER="YOUR_USERNAME"
DB_PASSWORD="YOUR_PASSWORD"
DB_HOST="localhost"
DB_PORT="5432"
```

---

## 🚦 CSV Workflow

<details>
<summary>Click to expand CSV workflow details</summary>

### ✅ Initial Setup: One-Time Historical Pull

1. **Run `coinbase_data.py`**  
   Fetches large blocks of historical data and saves them to `data/raw`.

   ```
   python scripts/coinbase_data.py
   ```

2. **Rename & Organize Raw Data**  
   Use `rename_raw_to_historical_files.py` to copy & rename raw files into the `historical` folder with clean names:

   ```
   python scripts/rename_raw_to_historical_files.py
   ```

   ✔️ Example rename:  
   `BTCUSD-1d=raw-data.csv` → `BTCUSD-1d=historical-data.csv`

3. **Backup**  
   (Optional but recommended): Copy all files from `historical` to `backup`. Then clear out `raw` to keep things tidy.

### ✅ Regular Updates (Ongoing)

When you want to refresh your data for existing pairs:


1. **Check Last Timestamps**  
   Runs a check on all historical files and records the most recent timestamp for each pair in `last_timestamps.json`.

   ```
   python scripts/check_last_timestamp.py
   ```

2. **Fetch New Data**  
   Uses the saved timestamps to download only the new missing candles. Saves fresh chunks to data/append.

   ```
   python scripts/coinbase_data_resumable_all.py
   ```

3. **Merge New Data**  
   Merges the new chunks from append into the corresponding historical files in historical. Ensures history stays continuous.
   
   ```
   python scripts/merge_append.py
   ```

4. **Verify & Backup**  
   Compares updated historical files to existing backups. Renames or overwrites backup files to match the latest version.

   ```
   python scripts/verify_and_backup.py
   ```

</details>

---

## 🗄️ PostgreSQL Data Workflow

In addition to the CSV pipeline, this repository supports **direct PostgreSQL storage for scalable, production-grade data handling**.

### 📌 Workflow Summary

#### 1. Initial Data Fetch (`coinbase_data_db.py`)

Fetch historical data for the first time for your chosen pair and timeframe.

Saves data into a Postgres table ending with `_raw` (e.g., `taousd_1m_raw`).

```
python scripts/coinbase_data_db.py
```

---

#### 2. Copy to Historical Table (`copy_rawdb_to_historicaldb.py`)

Copies your freshly fetched `_raw` table into a new historical table without the `_raw` suffix.

Creates the table if it does not exist and sets `datetime` as the primary key.

⚠️ **Use only once per new pair or timeframe** to establish historical tables for future appends.

```
python scripts/copy_rawdb_to_historicaldb.py
```

---

#### 3. Truncate Raw Table

After copying, truncate (empty) your `_raw` table to prepare it for future incremental data pulls.

✅ The orchestrator checks if the `_raw` table exists and will create it if missing.

---

#### 4. Ongoing Updates (`orchestrator_db.py`)

The orchestrator handles incremental updates:

* Fetches only new candles
* Inserts into `_raw`
* Appends to historical tables
* Truncates `_raw` after merging
* Creates timestamped, compressed backups

Run this weekly or daily to keep your database updated:

```
python scripts/orchestrator_db.py
```

---

#### 5. Testing & Verification (`verify_and_delete_test_rows.py`)

Simulate missing data by deleting N rows from your historical tables to test orchestrator retrieval, insertion, and validation logic.

```
python scripts/verify_and_delete_test_rows.py
```

---

#### 6. Inspect Table Date Ranges (`check_table_timestamps.py`)

Print earliest and latest timestamps + row counts for every table to confirm data integrity:

```
python scripts/check_table_timestamps.py
```

---

### ✅ Why this Workflow?

* **First-Time Loads**: Efficiently establish historical tables for new pairs/timeframes.
* **Clean Incremental Updates**: Avoid duplicates with orchestrator merges.
* **Robust Testing**: Verify pipeline correctness by re-fetching deleted data.

---

### 💡 Pro Tips

* The orchestrator auto-creates missing tables.
* Always truncate raw tables after initializing historical data to avoid duplicates.
* Backups are timestamped, compressed, and old backups (30+ days) are purged automatically.

---

## 📝 Schema

| Column   | Type                    |
| -------- | ----------------------- |
| datetime | TIMESTAMP (Primary Key) |
| open     | NUMERIC                 |
| high     | NUMERIC                 |
| low      | NUMERIC                 |
| close    | NUMERIC                 |
| volume   | NUMERIC                 |

🗃️ **Example Tables**: `btcusd_1m`, `btcusd_1m_raw`, `ethusd_1h`, `taousd_1d`

---

## 🛑 Backups

* **Location**: `data/backup/sql/`
* **Format**: `{DB_NAME}_backup_{YYYYMMDD_HHMMSS}.sql.gz`
* **Retention**: 30 days (older backups auto-deleted).

---

## 🔧 Why Move to Postgres?

✅ Handles massive datasets efficiently
✅ Enables advanced queries for backtesting & analytics
✅ Scales better than CSVs alone for production pipelines

---

## 🤝 Contributing

Fork, improve, and submit PRs to expand this data engineering toolkit for crypto quant research.

---

## 📜 License

MIT License

---

Happy clean crypto data collecting 🚀📊

---

