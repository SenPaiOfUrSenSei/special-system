"""
Data Aggregator v2 — 5-Minute Intervals
Aggregates raw Ethereum transactions + Binance ETH price into 5-min feature buckets.
Trimmed feature set for transaction forecasting models.
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data")


# ──────────────────────────────────────────────────────────────────────
# Loading
# ──────────────────────────────────────────────────────────────────────


def load_raw_txns() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load raw normal and ERC-20 transaction CSVs."""
    normal_path = DATA_DIR / "raw_normal_transactions.csv"
    erc20_path = DATA_DIR / "raw_erc20_transactions.csv"

    normal_df, erc20_df = None, None

    if normal_path.exists():
        print(f"[*] Loading {normal_path}...")
        normal_df = pd.read_csv(normal_path, low_memory=False)
        print(f"    {len(normal_df):,} rows")

    if erc20_path.exists():
        print(f"[*] Loading {erc20_path}...")
        erc20_df = pd.read_csv(erc20_path, low_memory=False)
        print(f"    {len(erc20_df):,} rows")

    return normal_df, erc20_df


def load_price() -> pd.DataFrame:
    """Load 1-min Binance price data."""
    price_path = DATA_DIR / "price_1min.csv"
    if not price_path.exists():
        print("[!] price_1min.csv not found. Run fetch_price.py first.")
        return pd.DataFrame()

    print(f"[*] Loading {price_path}...")
    df = pd.read_csv(price_path, low_memory=False)
    print(f"    {len(df):,} rows")
    return df


# ──────────────────────────────────────────────────────────────────────
# Preprocessing
# ──────────────────────────────────────────────────────────────────────


def preprocess_txns(df: pd.DataFrame, tx_type: str) -> pd.DataFrame:
    """Parse timestamps and floor to 5-min buckets."""
    df = df.copy()
    df["datetime"] = pd.to_datetime(
        pd.to_numeric(df["timeStamp"], errors="coerce"), unit="s", utc=True
    )
    df["bucket_5m"] = df["datetime"].dt.floor("5min")

    # Numeric coercion
    if tx_type == "normal":
        df["value_eth"] = pd.to_numeric(df["value_eth"], errors="coerce").fillna(0)
    else:
        df["value_tokens"] = pd.to_numeric(df["value_tokens"], errors="coerce").fillna(
            0
        )

    df["gasPrice_gwei"] = pd.to_numeric(df["gasPrice_gwei"], errors="coerce").fillna(0)
    df["gasUsed"] = pd.to_numeric(df["gasUsed"], errors="coerce").fillna(0)

    if tx_type == "normal":
        df["isError"] = pd.to_numeric(df["isError"], errors="coerce").fillna(0)

    return df


def preprocess_price(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate 1-min candles into 5-min OHLCV buckets."""
    df = df.copy()
    df["datetime"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["bucket_5m"] = df["datetime"].dt.floor("5min")

    agg = (
        df.groupby("bucket_5m")
        .agg(
            price_open=("open", "first"),
            price_high=("high", "max"),
            price_low=("low", "min"),
            price_close=("close", "last"),
            price_volume=("volume", "sum"),
            price_quote_volume=("quote_volume", "sum"),
            price_num_trades=("num_trades", "sum"),
            price_taker_buy_vol=("taker_buy_base_vol", "sum"),
        )
        .reset_index()
    )

    agg["price_change_pct"] = (
        (agg["price_close"] - agg["price_open"]) / agg["price_open"]
    ).replace([np.inf, -np.inf], 0)

    agg["price_range_pct"] = (
        (agg["price_high"] - agg["price_low"]) / agg["price_open"]
    ).replace([np.inf, -np.inf], 0)

    agg["price_buy_ratio"] = (agg["price_taker_buy_vol"] / agg["price_volume"]).replace(
        [np.inf, -np.inf, np.nan], 0.5
    )

    return agg


# ──────────────────────────────────────────────────────────────────────
# Transaction Aggregation
# ──────────────────────────────────────────────────────────────────────

# Only keep these top tokens — everything else is noise/spam
KEEP_TOKENS = {"USDT", "WETH", "USDC", "DAI", "WBTC", "LINK", "UNI", "AAVE"}


def aggregate_normal_5m(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate normal ETH transactions into 5-min buckets."""
    if df is None or df.empty:
        return pd.DataFrame()

    df = preprocess_txns(df, "normal")

    agg = (
        df.groupby("bucket_5m")
        .agg(
            normal_tx_count=("hash", "count"),
            normal_unique_senders=("from", "nunique"),
            normal_unique_receivers=("to", "nunique"),
            normal_eth_volume=("value_eth", "sum"),
            normal_eth_volume_mean=("value_eth", "mean"),
            normal_gas_price_mean_gwei=("gasPrice_gwei", "mean"),
            normal_gas_used_total=("gasUsed", "sum"),
            normal_gas_used_mean=("gasUsed", "mean"),
            normal_error_count=("isError", "sum"),
        )
        .reset_index()
    )

    agg["normal_error_rate"] = agg["normal_error_count"] / agg["normal_tx_count"]
    agg["normal_error_rate"] = agg["normal_error_rate"].fillna(0)

    return agg


def aggregate_erc20_5m(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate ERC-20 transactions into 5-min buckets."""
    if df is None or df.empty:
        return pd.DataFrame()

    df = preprocess_txns(df, "erc20")

    agg = (
        df.groupby("bucket_5m")
        .agg(
            erc20_tx_count=("hash", "count"),
            erc20_unique_tokens=("tokenSymbol", "nunique"),
            erc20_unique_senders=("from", "nunique"),
            erc20_unique_receivers=("to", "nunique"),
            erc20_gas_price_mean_gwei=("gasPrice_gwei", "mean"),
            erc20_gas_used_total=("gasUsed", "sum"),
        )
        .reset_index()
    )

    # Per-token counts for only the tokens we care about
    for token in KEEP_TOKENS:
        token_df = df[df["tokenSymbol"] == token]
        if not token_df.empty:
            token_agg = (
                token_df.groupby("bucket_5m")
                .agg(**{f"erc20_{token.lower()}_count": ("hash", "count")})
                .reset_index()
            )
            agg = agg.merge(token_agg, on="bucket_5m", how="left")

    return agg


# ──────────────────────────────────────────────────────────────────────
# Feature Assembly
# ──────────────────────────────────────────────────────────────────────


def build_features(
    normal_agg: pd.DataFrame,
    erc20_agg: pd.DataFrame,
    price_agg: pd.DataFrame,
) -> pd.DataFrame:
    """Merge all sources into a single 5-min feature set."""

    # Start from price buckets (most complete time coverage)
    if not price_agg.empty:
        features = price_agg[["bucket_5m"]].copy()
    elif not normal_agg.empty:
        features = normal_agg[["bucket_5m"]].copy()
    elif not erc20_agg.empty:
        features = erc20_agg[["bucket_5m"]].copy()
    else:
        return pd.DataFrame()

    # Merge
    if not normal_agg.empty:
        features = features.merge(normal_agg, on="bucket_5m", how="left")
    if not erc20_agg.empty:
        features = features.merge(erc20_agg, on="bucket_5m", how="left")
    if not price_agg.empty:
        features = features.merge(price_agg, on="bucket_5m", how="left")

    # Fill NaN for tx columns with 0 (no transactions in that bucket)
    tx_cols = [c for c in features.columns if c != "bucket_5m"]
    features[tx_cols] = features[tx_cols].fillna(0)

    # Derived features
    features["tx_count"] = features.get("normal_tx_count", 0) + features.get(
        "erc20_tx_count", 0
    )
    features["erc20_ratio"] = features.get("erc20_tx_count", 0) / features[
        "tx_count"
    ].replace(0, 1)

    # Time features
    features["hour_of_day"] = features["bucket_5m"].dt.hour
    features["day_of_week"] = features["bucket_5m"].dt.dayofweek
    features["is_weekend"] = features["day_of_week"].isin([5, 6]).astype(int)

    features = features.sort_values("bucket_5m").reset_index(drop=True)

    return features


# ──────────────────────────────────────────────────────────────────────
# Lag & Rolling Features (trimmed)
# ──────────────────────────────────────────────────────────────────────

LAG_COLS = [
    "tx_count",
    "normal_tx_count",
    "erc20_tx_count",
    "normal_eth_volume",
    "normal_gas_price_mean_gwei",
]

# 5-min lags: 1 = 5min, 12 = 1hr, 288 = 1day
LAGS = [1, 12, 288]

# Rolling windows: 12 = 1hr, 288 = 1day
ROLLING_WINDOWS = [12, 288]


def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add trimmed lag and rolling features."""
    for col in LAGS_COLS:
        if col not in df.columns:
            continue
        for lag in LAGS:
            df[f"{col}_lag_{lag}"] = df[col].shift(lag)

    for col in LAGS_COLS:
        if col not in df.columns:
            continue
        for window in ROLLING_WINDOWS:
            df[f"{col}_rolling_mean_{window}"] = df[col].rolling(window).mean()
            df[f"{col}_rolling_std_{window}"] = df[col].rolling(window).std()

    return df


# Use same list for both lag and rolling
LAGS_COLS = LAG_COLS


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

FINAL_COLUMNS = [
    # Timestamp
    "bucket_5m",
    # Transactions
    "tx_count",
    "normal_tx_count",
    "erc20_tx_count",
    "erc20_ratio",
    "normal_unique_senders",
    "normal_unique_receivers",
    "normal_eth_volume",
    "normal_eth_volume_mean",
    "normal_gas_price_mean_gwei",
    "normal_gas_used_total",
    "normal_error_rate",
    "erc20_unique_tokens",
    "erc20_unique_senders",
    "erc20_unique_receivers",
    "erc20_gas_price_mean_gwei",
    "erc20_gas_used_total",
    # Top token counts
    "erc20_usdt_count",
    "erc20_weth_count",
    "erc20_usdc_count",
    "erc20_dai_count",
    "erc20_wbtc_count",
    # Price
    "price_open",
    "price_high",
    "price_low",
    "price_close",
    "price_volume",
    "price_num_trades",
    "price_change_pct",
    "price_range_pct",
    "price_buy_ratio",
    # Time
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    # Lags
    "tx_count_lag_1",
    "tx_count_lag_12",
    "tx_count_lag_288",
    "normal_tx_count_lag_1",
    "normal_tx_count_lag_12",
    "normal_tx_count_lag_288",
    "erc20_tx_count_lag_1",
    "erc20_tx_count_lag_12",
    "normal_eth_volume_lag_1",
    "normal_eth_volume_lag_12",
    "normal_gas_price_mean_gwei_lag_1",
    "normal_gas_price_mean_gwei_lag_12",
    # Rolling
    "tx_count_rolling_mean_12",
    "tx_count_rolling_std_12",
    "tx_count_rolling_mean_288",
    "tx_count_rolling_std_288",
    "normal_tx_count_rolling_mean_12",
    "normal_tx_count_rolling_mean_288",
    "normal_eth_volume_rolling_mean_12",
    "normal_eth_volume_rolling_mean_288",
    "normal_gas_price_mean_gwei_rolling_mean_12",
    "normal_gas_price_mean_gwei_rolling_mean_288",
]


def main():
    print("=" * 60)
    print("  Ethereum 5-Min Feature Aggregator")
    print("=" * 60)
    print()

    # Load data
    normal_df, erc20_df = load_raw_txns()
    price_df = load_price()

    if normal_df is None and erc20_df is None:
        print("[!] No raw transaction data found.")
        return

    print()

    # Aggregate transactions by 5-min buckets
    print("[*] Aggregating normal transactions (5-min)...")
    normal_agg = (
        aggregate_normal_5m(normal_df) if normal_df is not None else pd.DataFrame()
    )
    print(f"    {len(normal_agg):,} buckets")

    print("[*] Aggregating ERC-20 transactions (5-min)...")
    erc20_agg = aggregate_erc20_5m(erc20_df) if erc20_df is not None else pd.DataFrame()
    print(f"    {len(erc20_agg):,} buckets")

    # Aggregate price
    print("[*] Aggregating price data (5-min)...")
    price_agg = preprocess_price(price_df) if not price_df.empty else pd.DataFrame()
    print(f"    {len(price_agg):,} buckets")

    # Build feature set
    print("[*] Building combined features...")
    features = build_features(normal_agg, erc20_agg, price_agg)
    print(f"    {len(features):,} rows before lags")

    # Add lag/rolling features
    print("[*] Adding lag and rolling features...")
    features = add_lag_features(features)

    # Trim to final columns (keep only what exists)
    keep = [c for c in FINAL_COLUMNS if c in features.columns]
    features = features[keep]

    # Drop rows with NaN from lag/rolling warmup (first 288 rows = 1 day)
    full_rows = len(features)
    features = features.dropna().reset_index(drop=True)
    dropped = full_rows - len(features)

    # Save
    output_path = DATA_DIR / "5min_features.csv"
    features.to_csv(output_path, index=False)

    print()
    print(f"[+] Results:")
    print(f"    5-min intervals: {len(features):,}")
    print(f"    Rows dropped (NaN from lags): {dropped:,}")
    print(f"    Columns: {len(features.columns)}")
    print(f"    Saved to: {output_path}")

    # Date range
    if "bucket_5m" in features.columns:
        print(
            f"    Date range: {features['bucket_5m'].min()} -> {features['bucket_5m'].max()}"
        )

    print()
    print("[*] Feature list:")
    for i, col in enumerate(features.columns, 1):
        print(f"    {i:2d}. {col}")

    print()
    print("[*] First 5 rows:")
    print(features.head().to_string())

    print()
    print("[+] Aggregation complete!")


if __name__ == "__main__":
    main()
