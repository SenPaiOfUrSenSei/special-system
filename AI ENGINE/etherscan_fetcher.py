"""
Etherscan Transaction Fetcher
Fetches normal ETH and ERC-20 token transactions from high-volume addresses.
Designed for collecting training data for transaction forecasting AI models.
"""

import os
import csv
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

# Load API key
load_dotenv()
API_KEY = os.getenv("APIETHERSCAN")
BASE_URL = "https://api.etherscan.io/v2/api"
CHAIN_ID = 1  # Ethereum mainnet

# Rate limit: Free tier = 3 calls/sec
CALL_DELAY = 0.35

# Max records per page (Etherscan limit)
PAGE_SIZE = 10000

# High-volume addresses to scrape
ADDRESSES = {
    # Exchanges (high volume, will cap at 10K per week chunk)
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance_14",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "Binance_15",
    "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD1e": "Binance_8",
    # Contracts (moderate volume)
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": "WETH",
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": "USDC",
    "0xdAC17F958D2ee523a2206206994597C13D831ec7": "USDT",
    "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D": "UniswapV2_Router",
    "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9": "AAVE_Token",
    # DeFi protocols (moderate volume, good for forecasting)
    "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984": "Uniswap_UNI",
    "0x514910771AF9Ca656af840dff83E8264EcF986CA": "Chainlink_LINK",
    "0x6B175474E89094C44Da98b954EedeAC495271d0F": "DAI_Stablecoin",
    "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": "WBTC",
    # Whales / notable EOAs (lower volume, complete data)
    "0x1B3cB81E51011b549d78bf720b0d924ac763A7C2": "Known_Whale_1",
    "0x220866B1A2219f40e72f5c628B65D54268cA3A9D": "Known_Whale_2",
}

OUTPUT_DIR = Path("data")


def rate_limit():
    """Enforce rate limiting for Etherscan free tier."""
    time.sleep(CALL_DELAY)


def get_block_by_timestamp(timestamp: int, closest: str = "before") -> int:
    """Get block number closest to a given timestamp."""
    rate_limit()
    params = {
        "chainid": CHAIN_ID,
        "module": "block",
        "action": "getblocknobytime",
        "timestamp": timestamp,
        "closest": closest,
        "apikey": API_KEY,
    }
    resp = requests.get(BASE_URL, params=params, timeout=30)
    data = resp.json()
    if data["status"] == "1":
        return int(data["result"])
    return 0


def fetch_transactions(
    address: str,
    action: str,
    start_block: int = 0,
    end_block: int = 999999999,
) -> list[dict]:
    """Fetch up to 10,000 most recent transactions for an address.

    For high-volume addresses (exchanges, contracts), we cap at the API's
    10K limit which still provides a representative sample for ML training.

    Args:
        address: Ethereum address
        action: 'txlist' for normal ETH or 'tokentx' for ERC-20
        start_block: Starting block number
        end_block: Ending block number
    """
    rate_limit()
    params = {
        "chainid": CHAIN_ID,
        "module": "account",
        "action": action,
        "address": address,
        "startblock": start_block,
        "endblock": end_block,
        "page": 1,
        "offset": PAGE_SIZE,
        "sort": "desc",
        "apikey": API_KEY,
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=30)
        data = resp.json()
    except requests.RequestException as e:
        tqdm.write(f"    [!] Request error: {e}")
        return []

    if data["status"] != "1" or not data["result"]:
        if data["message"] != "No transactions found":
            tqdm.write(f"    [!] {data['message']}")
        return []

    return data["result"]


def save_to_csv(rows: list[dict], filepath: Path, fieldnames: list[str]):
    """Append rows to a CSV file. Creates header if file is new."""
    file_exists = filepath.exists() and filepath.stat().st_size > 0

    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def process_normal_tx(raw: list[dict], label: str) -> list[dict]:
    """Normalize raw normal transaction data."""
    processed = []
    for tx in raw:
        processed.append(
            {
                "address_label": label,
                "blockNumber": tx.get("blockNumber", ""),
                "timeStamp": tx.get("timeStamp", ""),
                "hash": tx.get("hash", ""),
                "from": tx.get("from", ""),
                "to": tx.get("to", ""),
                "value_eth": int(tx.get("value", 0)) / 1e18,
                "gas": tx.get("gas", ""),
                "gasPrice_gwei": int(tx.get("gasPrice", 0)) / 1e9,
                "gasUsed": tx.get("gasUsed", ""),
                "isError": tx.get("isError", ""),
                "input_length": len(tx.get("input", "0x")) // 2 - 1
                if tx.get("input", "0x") != "0x"
                else 0,
                "methodId": tx.get("methodId", ""),
                "tx_type": "normal",
            }
        )
    return processed


def process_erc20_tx(raw: list[dict], label: str) -> list[dict]:
    """Normalize raw ERC-20 transaction data."""
    processed = []
    for tx in raw:
        decimals = int(tx.get("tokenDecimal", 18))
        raw_value = int(tx.get("value", 0))
        processed.append(
            {
                "address_label": label,
                "blockNumber": tx.get("blockNumber", ""),
                "timeStamp": tx.get("timeStamp", ""),
                "hash": tx.get("hash", ""),
                "from": tx.get("from", ""),
                "to": tx.get("to", ""),
                "contractAddress": tx.get("contractAddress", ""),
                "tokenName": tx.get("tokenName", ""),
                "tokenSymbol": tx.get("tokenSymbol", ""),
                "tokenDecimal": decimals,
                "value_tokens": raw_value / (10**decimals),
                "gas": tx.get("gas", ""),
                "gasPrice_gwei": int(tx.get("gasPrice", 0)) / 1e9,
                "gasUsed": tx.get("gasUsed", ""),
                "tx_type": "erc20",
            }
        )
    return processed


NORMAL_FIELDS = [
    "address_label",
    "blockNumber",
    "timeStamp",
    "hash",
    "from",
    "to",
    "value_eth",
    "gas",
    "gasPrice_gwei",
    "gasUsed",
    "isError",
    "input_length",
    "methodId",
    "tx_type",
]

ERC20_FIELDS = [
    "address_label",
    "blockNumber",
    "timeStamp",
    "hash",
    "from",
    "to",
    "contractAddress",
    "tokenName",
    "tokenSymbol",
    "tokenDecimal",
    "value_tokens",
    "gas",
    "gasPrice_gwei",
    "gasUsed",
    "tx_type",
]


def main():
    if not API_KEY:
        print("ERROR: APIETHERSCAN not found in .env file")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)
    normal_csv = OUTPUT_DIR / "raw_normal_transactions.csv"
    erc20_csv = OUTPUT_DIR / "raw_erc20_transactions.csv"

    # Remove old files to start fresh
    for f in [normal_csv, erc20_csv]:
        if f.exists():
            f.unlink()

    # Calculate block range for 1 year
    now = int(time.time())
    one_year_ago = now - 365 * 24 * 60 * 60

    print(
        f"[*] Fetching transactions from {datetime.fromtimestamp(one_year_ago).date()} to {datetime.fromtimestamp(now).date()}"
    )
    print(f"[*] Resolving block numbers...")

    start_block = get_block_by_timestamp(one_year_ago, "after")
    rate_limit()
    end_block = get_block_by_timestamp(now, "before")

    print(f"[*] Block range: {start_block} -> {end_block}")
    print(f"[*] Addresses to scan: {len(ADDRESSES)}")
    print()

    total_normal = 0
    total_erc20 = 0

    pbar = tqdm(ADDRESSES.items(), desc="Fetching", unit="addr")
    for address, label in pbar:
        pbar.set_postfix(addr=f"{label}")

        # Fetch normal ETH transactions
        tqdm.write(f"  [>] {label} | Normal ETH transactions...")
        normal_raw = fetch_transactions(address, "txlist", start_block, end_block)
        if normal_raw:
            normal_processed = process_normal_tx(normal_raw, label)
            save_to_csv(normal_processed, normal_csv, NORMAL_FIELDS)
            total_normal += len(normal_raw)
            tqdm.write(f"    -> {len(normal_raw)} normal txns")
        else:
            tqdm.write(f"    -> 0 normal txns")

        # Fetch ERC-20 token transactions
        tqdm.write(f"  [>] {label} | ERC-20 transactions...")
        erc20_raw = fetch_transactions(address, "tokentx", start_block, end_block)
        if erc20_raw:
            erc20_processed = process_erc20_tx(erc20_raw, label)
            save_to_csv(erc20_processed, erc20_csv, ERC20_FIELDS)
            total_erc20 += len(erc20_raw)
            tqdm.write(f"    -> {len(erc20_raw)} ERC-20 txns")
        else:
            tqdm.write(f"    -> 0 ERC-20 txns")

        tqdm.write("")

    print(f"[+] Done!")
    print(f"[+] Normal ETH transactions: {total_normal}")
    print(f"[+] ERC-20 transactions: {total_erc20}")
    print(f"[+] Saved to:")
    print(f"    {normal_csv}")
    print(f"    {erc20_csv}")


if __name__ == "__main__":
    main()
