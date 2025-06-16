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

## ⚙️ How to Use

1️⃣ **Clone this repository**  
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

cd YOUR_REPO_NAME

2️⃣ **Install dependencies**
pip install -r requirements.txt


3️⃣ **Create a .env file**
Add your Coinbase API credentials:

COINBASE_API_KEY="organizations/{org_id}/apiKeys/{key_id}"
COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----\nYOUR PRIVATE KEY\n-----END EC PRIVATE KEY-----\n"


4️⃣ **Edit coinbase_data.py**
Inside the script, adjust:

- SYMBOL (e.g., 'BTC-USD')

- TIMEFRAME (e.g., '1h')

- WEEKS (number of weeks back to fetch data)

5️⃣ **Run the script**
python coinbase_data.py

✅ The historical data will be saved in the data/ folder as a .csv file.

📄 **Notes**
Never share your .env file or API keys publicly!

The script handles chunked requests to respect API limits. 

For extremely large time ranges, be patient — Coinbase’s API may rate limit you.

Existing CSVs are reused to save time on repeated runs.


🤝 **Contributing**
Feel free to fork, improve, and send pull requests!
This tool is for anyone who wants simple access to historical crypto data.

📜 **License**
MIT License
