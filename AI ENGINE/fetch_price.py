"""
Binance ETH/USDT Price Fetcher
Fetches 1-minute kline (candlestick) data from Binance API.
No API key required. Free, reliable, no rate limit issues for this volume.
"""

import csv
import time
import requests
from datetime import datetime, timezone
from pathlib import Path

from tqdm import tqdm

BASE_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "ETHUSDT"
INTERVAL = "1m"
LIMIT = 1000  # max per request

OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "price_1min.csv"

CSV_FIELDS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "num_trades",
    "taker_buy_base_vol",
    "taker_buy_quote_vol",
]


def fetch_klines(start_ms: int, end_ms: int, max_retries: int = 5) -> list[list]:
    """Fetch a batch of klines with retry logic."""
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "startTime": start_ms,
        "endTime": end_ms,
        "limit": LIMIT,
    }
    for attempt in range(max_retries):
        try:
            resp = requests.get(BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            wait = min(2**attempt, 30)
            if attempt < max_retries - 1:
                time.sleep(wait)
            else:
                tqdm.write(f"  [!] Failed after {max_retries} retries: {e}")
                return []


def kline_to_row(k: list) -> dict:
    """Convert Binance kline array to flat dict."""
    return {
        "open_time": int(k[0]),
        "open": float(k[1]),
        "high": float(k[2]),
        "low": float(k[3]),
        "close": float(k[4]),
        "volume": float(k[5]),
        "close_time": int(k[6]),
        "quote_volume": float(k[7]),
        "num_trades": int(k[8]),
        "taker_buy_base_vol": float(k[9]),
        "taker_buy_quote_vol": float(k[10]),
    }


def save_rows(rows: list[dict], filepath: Path):
    """Append rows to CSV, creating header if needed."""
    file_exists = filepath.exists() and filepath.stat().st_size > 0
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def get_time_range_from_txns() -> tuple[int, int]:
    """Determine time range from existing raw transaction data."""
    import pandas as pd

    normal_path = OUTPUT_DIR / "raw_normal_transactions.csv"
    erc20_path = OUTPUT_DIR / "raw_erc20_transactions.csv"

    min_ts = float("inf")
    max_ts = 0

    for path in [normal_path, erc20_path]:
        if path.exists():
            df = pd.read_csv(path, usecols=["timeStamp"], low_memory=False)
            df["ts"] = pd.to_numeric(df["timeStamp"], errors="coerce")
            min_ts = min(min_ts, df["ts"].min())
            max_ts = max(max_ts, df["ts"].max())

    # Convert to milliseconds, add 1-day buffer
    start_ms = int((min_ts - 86400) * 1000)
    end_ms = int((max_ts + 86400) * 1000)

    return start_ms, end_ms


def get_resume_start() -> int:
    """Find the last timestamp in existing price CSV to resume from."""
    if not OUTPUT_FILE.exists() or OUTPUT_FILE.stat().st_size == 0:
        return 0
    import csv as csv_mod

    last_ts = 0
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv_mod.DictReader(f)
        for row in reader:
            try:
                last_ts = int(row["open_time"])
            except (ValueError, KeyError):
                pass
    return last_ts + 1 if last_ts > 0 else 0


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    start_ms, end_ms = get_time_range_from_txns()

    # Resume from last fetched candle
    resume_from = get_resume_start()
    if resume_from > 0 and resume_from > start_ms:
        start_ms = resume_from
        start_dt = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc)
        print(f"[*] Resuming from {start_dt}")
    else:
        # Fresh start - remove old file
        if OUTPUT_FILE.exists():
            OUTPUT_FILE.unlink()
    start_dt = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc)

    print(f"[*] Fetching 1-min ETH/USDT klines from Binance")
    print(f"[*] Time range: {start_dt.date()} -> {end_dt.date()}")
    print()

    # Each batch = 1000 minutes ≈ 16.7 hours
    # Total batches = (end - start) / (1000 * 60000)
    total_minutes = (end_ms - start_ms) / 60000
    est_batches = int(total_minutes / LIMIT) + 1
    print(f"[*] Estimated {total_minutes:,.0f} minutes ≈ {est_batches} batches")

    cursor = start_ms
    total_rows = 0

    pbar = tqdm(total=est_batches, desc="Fetching", unit="batch")
    while cursor < end_ms:
        batch_end = min(cursor + LIMIT * 60000, end_ms)

        klines = fetch_klines(cursor, batch_end)

        if not klines:
            # If no data, skip ahead
            cursor = batch_end + 1
            pbar.update(1)
            continue

        rows = [kline_to_row(k) for k in klines]
        save_rows(rows, OUTPUT_FILE)
        total_rows += len(rows)

        # Advance cursor past last candle's close time
        last_close = klines[-1][6]  # close_time in ms
        cursor = last_close + 1  # 1ms after last close

        pbar.update(1)
        pbar.set_postfix(rows=f"{total_rows:,}")

        # Binance rate limit: weight 1 per request, 6000/min. Very safe.
        time.sleep(0.12)

    pbar.close()

    print()
    print(f"[+] Done! {total_rows:,} 1-min candles saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
