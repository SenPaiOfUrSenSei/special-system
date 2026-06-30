import os
import csv
import time
import requests
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────
# Env Parsing (Bulletproof fallback)
# ──────────────────────────────────────────────────────────────────────
def load_env(env_path=".env"):
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

# Load env from root directory
load_env()
API_KEY = os.getenv("ETHERSCAN_API_KEY")

# API Configuration
ETHERSCAN_URL = "https://api.etherscan.io/v2/api"
BTC_BLOCK_URL = "https://blockchain.info/latestblock"
BTC_TICKER_URL = "https://blockchain.info/ticker"

CSV_FILE = "crypto_market_data.csv"
CSV_FIELDS = [
    "timestamp",
    "eth_block",
    "eth_safe_gas_gwei",
    "eth_propose_gas_gwei",
    "eth_fast_gas_gwei",
    "eth_base_fee_gwei",
    "btc_block_height",
    "btc_block_hash",
    "btc_price_usd"
]

def fetch_eth_block() -> int:
    """Fetch latest Ethereum block number using Etherscan API V2."""
    if not API_KEY:
        return 0
    params = {
        "chainid": 1,
        "module": "proxy",
        "action": "eth_blockNumber",
        "apikey": API_KEY
    }
    try:
        resp = requests.get(ETHERSCAN_URL, params=params, timeout=10)
        data = resp.json()
        result = data.get("result", "")
        if isinstance(result, str) and result.startswith("0x"):
            return int(result, 16)
        return int(result)
    except Exception as e:
        print(f"[ETH Error] Failed to fetch block number: {e}")
        return 0

def fetch_eth_gas() -> dict:
    """Fetch current Ethereum gas price estimations."""
    if not API_KEY:
        return {}
    params = {
        "chainid": 1,
        "module": "gastracker",
        "action": "gasoracle",
        "apikey": API_KEY
    }
    try:
        resp = requests.get(ETHERSCAN_URL, params=params, timeout=10)
        data = resp.json()
        if data.get("status") == "1":
            res = data.get("result", {})
            return {
                "safe": float(res.get("SafeGasPrice", 0)),
                "propose": float(res.get("ProposeGasPrice", 0)),
                "fast": float(res.get("FastGasPrice", 0)),
                "base": float(res.get("suggestBaseFee", 0))
            }
    except Exception as e:
        print(f"[ETH Error] Failed to fetch gas details: {e}")
    return {}

def fetch_btc_block() -> dict:
    """Fetch latest Bitcoin block height and hash from Blockchain.com API."""
    try:
        resp = requests.get(BTC_BLOCK_URL, timeout=10)
        data = resp.json()
        return {
            "height": int(data.get("height", 0)),
            "hash": data.get("hash", "")
        }
    except Exception as e:
        print(f"[BTC Error] Failed to fetch latest block: {e}")
    return {}

def fetch_btc_price() -> float:
    """Fetch current Bitcoin USD price from Blockchain.com ticker API."""
    try:
        resp = requests.get(BTC_TICKER_URL, timeout=10)
        data = resp.json()
        usd_data = data.get("USD", {})
        return float(usd_data.get("last", 0.0))
    except Exception as e:
        print(f"[BTC Error] Failed to fetch price: {e}")
    return 0.0

def save_data(row: dict):
    """Save row data to CSV file."""
    file_exists = os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def main():
    if not API_KEY:
        print("[!] Warning: ETHERSCAN_API_KEY not found in .env file. ETH endpoints will be skipped.")
    
    print("=" * 60)
    print("        Crypto Poller (ETH & BTC Blockchain Data)")
    print("=" * 60)
    print(f"Logging data to: {os.path.abspath(CSV_FILE)}")
    print("Press Ctrl+C to stop.")
    print()

    # Create CSV directory structure if needed and initialize file
    row_count = 0
    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Fetch ETH details
            eth_block = fetch_eth_block()
            gas = fetch_eth_gas()
            
            # Fetch BTC details
            btc_block = fetch_btc_block()
            btc_price = fetch_btc_price()
            
            # Compile row
            row = {
                "timestamp": timestamp,
                "eth_block": eth_block if eth_block > 0 else "N/A",
                "eth_safe_gas_gwei": gas.get("safe", "N/A"),
                "eth_propose_gas_gwei": gas.get("propose", "N/A"),
                "eth_fast_gas_gwei": gas.get("fast", "N/A"),
                "eth_base_fee_gwei": gas.get("base", "N/A"),
                "btc_block_height": btc_block.get("height", "N/A"),
                "btc_block_hash": btc_block.get("hash", "N/A"),
                "btc_price_usd": btc_price if btc_price > 0 else "N/A"
            }
            
            # Save data
            save_data(row)
            row_count += 1
            
            # Dashboard console print
            print(f"[{timestamp}] Poll #{row_count} logged successfully:")
            print(f"  ETH  | Block: {row['eth_block']} | Gas Base Fee: {row['eth_base_fee_gwei']} Gwei (Safe: {row['eth_safe_gas_gwei']} / Fast: {row['eth_fast_gas_gwei']})")
            print(f"  BTC  | Block: {row['btc_block_height']} | Hash: {row['btc_block_hash'][:16]}... | Price: ${row['btc_price_usd']:,.2f}")
            print("-" * 60)
            
            # Poll every 10 seconds
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n[+] Poller stopped by user.")

if __name__ == "__main__":
    main()
