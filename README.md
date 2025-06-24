# Coinbase Historical Crypto Data Fetcher

📈 **Description**  
This Python script helps you easily download historical trading data (candles) for any Coinbase trading pair, like BTC-USD or ETH-USD, using Coinbase’s API.

🔗 [Get your Coinbase API Key here](https://www.coinbase.com/developer-platform/products/exchange-api)

**Key Features:**
- Specify the trading pair (e.g., BTC-USD, ETH-USD, SOL-USD)
- Choose the timeframe (1m, 5m, 1h, 6h, 1d)
- Download hundreds of weeks worth of historical data
- Automatically saves the data as a clean CSV file
- Automatically adjusts your date range to avoid requesting non-existent data 

---

## 📁 Project Folder Structure

```
COINBASE_DATA/
├── data/
│   ├── append/          # New data chunks waiting to be merged
│   ├── backup/          # Verified backups of historical data
│   ├── historical/      # Main source of truth (cleaned, full history)
│   ├── raw/             # Raw fetched data before renaming
│   ├── last_timestamps.json  # Tracks last fetched candle per pair
│   ├── last_timestamps_TEST.json  # Sample JSON for test mode
│   └── .gitkeep
├── scripts/
│   ├── coinbase_data.py                 # Fetch large historical chunks (initial or big pulls)
│   ├── coinbase_data_resumable_all.py   # Resume fetch using last timestamps
│   ├── check_last_timestamp.py          # Check latest timestamps in historical files
│   ├── rename_raw_to_historical_files.py # Copy & rename raw data → historical
│   ├── merge_append.py                  # Merge new 'append' data into historical
│   ├── verify_and_backup.py             # Verify & sync backups for historical
│   └── [other helpers...]
├── test_data/                           # For test mode
├── .env                                 # Contains your API credentials
├── .gitignore
├── README.md
├── requirements.txt
```


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

Add your Coinbase API credentials:

```
COINBASE_API_KEY="organizations/{org_id}/apiKeys/{key_id}"
COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----\nYOUR PRIVATE KEY\n-----END EC PRIVATE KEY-----\n"
```



## 🚦 How to Use

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

---

## ✅ Key Scripts Quick Reference

| Script | Purpose |
|--------|---------|
| `coinbase_data.py` | Fetch large initial historical data |
| `check_last_timestamp.py` | Inspect last candle per pair |
| `coinbase_data_resumable_all.py` | Get only missing candles |
| `rename_raw_to_historical_files.py` | Copy & rename raw → historical |
| `merge_append.py` | Append new chunks to historical |
| `verify_and_backup.py` | Sync backups with historical |

---

## 🏁 You're Ready!

Happy clean crypto data collecting 🚀📊

---

📄 **Notes**

Never share your .env file or API keys publicly!

The script handles chunked requests to respect API limits. 

For extremely large time ranges, be patient — Coinbase’s API may rate limit you.

Existing CSVs are reused to save time on repeated runs.

---

🤝 **Contributing**

Feel free to fork, improve, and send pull requests!

This tool is for anyone who wants simple access to historical crypto data.

---

📜 **License**

MIT License
