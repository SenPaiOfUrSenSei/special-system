import os
import sys
import time
import asyncio
import requests
import psycopg2
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timezone

# ──────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = "/app"
MODEL_PATH = os.path.join(PROJECT_ROOT, "AI ENGINE/model/settlement_model.joblib")
HISTORICAL_FEATURES_PATH = os.path.join(PROJECT_ROOT, "AI ENGINE/data/5min_features.csv")

ml_model = None
feature_cols = None
historical_buffer = None

def get_db_connection():
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/payment_portal")
    return psycopg2.connect(db_url)

def load_historical_buffer(csv_path, buffer_size=288):
    df = pd.read_csv(csv_path)
    df["bucket_5m"] = pd.to_datetime(df["bucket_5m"], utc=True)
    df = df.sort_values("bucket_5m").reset_index(drop=True)
    df = df.fillna(0)
    return df.tail(buffer_size).copy()

# ──────────────────────────────────────────────────────────────────────
# Feature Engineering Helpers
# ──────────────────────────────────────────────────────────────────────
LAG_COLS = [
    "tx_count",
    "normal_tx_count",
    "erc20_tx_count",
    "normal_eth_volume",
    "normal_gas_price_mean_gwei",
]
LAGS = [1, 12, 288]
ROLLING_WINDOWS = [12, 288]

def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in LAG_COLS:
        if col not in df.columns:
            continue
        for lag in LAGS:
            df[f"{col}_lag_{lag}"] = df[col].shift(lag)

    for col in LAG_COLS:
        if col not in df.columns:
            continue
        for window in ROLLING_WINDOWS:
            df[f"{col}_rolling_mean_{window}"] = df[col].rolling(window).mean()
            df[f"{col}_rolling_std_{window}"] = df[col].rolling(window).std()

    return df

def get_latest_market_data(csv_path="crypto_market_data.csv"):
    path = os.path.join(PROJECT_ROOT, csv_path)
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        if df.empty:
            return None
        return df.iloc[-1].to_dict()
    except Exception as e:
        print(f"[Warning] Failed to read {csv_path}: {e}")
        return None

def get_binance_klines():
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "ETHUSDT",
        "interval": "5m",
        "limit": 1
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data:
            k = data[0]
            open_val = float(k[1])
            high = float(k[2])
            low = float(k[3])
            close = float(k[4])
            volume = float(k[5])
            quote_volume = float(k[7])
            num_trades = int(k[8])
            taker_buy_base_vol = float(k[9])
            
            price_change_pct = (close - open_val) / open_val if open_val > 0 else 0
            price_range_pct = (high - low) / open_val if open_val > 0 else 0
            price_buy_ratio = taker_buy_base_vol / volume if volume > 0 else 0.5
            
            return {
                "price_open": open_val,
                "price_high": high,
                "price_low": low,
                "price_close": close,
                "price_volume": volume,
                "price_num_trades": num_trades,
                "price_change_pct": price_change_pct,
                "price_range_pct": price_range_pct,
                "price_buy_ratio": price_buy_ratio
            }
    except Exception as e:
        print(f"[Warning] Failed to fetch Binance klines: {e}")
    return {
        "price_open": 3500.0,
        "price_high": 3505.0,
        "price_low": 3495.0,
        "price_close": 3500.0,
        "price_volume": 1000.0,
        "price_num_trades": 100,
        "price_change_pct": 0.0,
        "price_range_pct": 0.002,
        "price_buy_ratio": 0.5
    }

def get_l2_metrics(conn, currency, start_time_epoch):
    cur = conn.cursor()
    cur.execute("""
        SELECT sender_id, recipient_id, source_currency, target_currency, source_amount, target_amount
        FROM transactions
        WHERE timestamp >= %s
    """, (start_time_epoch,))
    txs = cur.fetchall()
    cur.close()
    
    tx_count = 0
    normal_tx_count = 0
    erc20_tx_count = 0
    senders = set()
    receivers = set()
    eth_volume = 0.0
    
    token_counts = {
        "usdt": 0,
        "weth": 0,
        "usdc": 0,
        "dai": 0,
        "wbtc": 0
    }
    
    for tx in txs:
        sender_id, recipient_id, src_curr, tgt_curr, src_amt, tgt_amt = tx
        if src_curr == currency or tgt_curr == currency:
            tx_count += 1
            if src_curr == "ETH" or tgt_curr == "ETH":
                normal_tx_count += 1
                if src_curr == "ETH":
                    eth_volume += src_amt
                if tgt_curr == "ETH":
                    eth_volume += tgt_amt
            else:
                erc20_tx_count += 1
                
            if sender_id:
                senders.add(sender_id)
            if recipient_id:
                receivers.add(recipient_id)
                
            for c in [src_curr, tgt_curr]:
                if c:
                    cl = c.lower()
                    if cl in token_counts:
                        token_counts[cl] += 1
                        
    normal_unique_senders = len(senders) if normal_tx_count > 0 else 0
    normal_unique_receivers = len(receivers) if normal_tx_count > 0 else 0
    erc20_unique_senders = len(senders) if erc20_tx_count > 0 else 0
    erc20_unique_receivers = len(receivers) if erc20_tx_count > 0 else 0
    
    normal_eth_volume_mean = eth_volume / normal_tx_count if normal_tx_count > 0 else 0.0
    erc20_ratio = erc20_tx_count / tx_count if tx_count > 0 else 0.0
    
    return {
        "tx_count": tx_count,
        "normal_tx_count": normal_tx_count,
        "erc20_tx_count": erc20_tx_count,
        "erc20_ratio": erc20_ratio,
        "normal_unique_senders": normal_unique_senders,
        "normal_unique_receivers": normal_unique_receivers,
        "normal_eth_volume": eth_volume,
        "normal_eth_volume_mean": normal_eth_volume_mean,
        "erc20_unique_tokens": len([k for k, v in token_counts.items() if v > 0]),
        "erc20_unique_senders": erc20_unique_senders,
        "erc20_unique_receivers": erc20_unique_receivers,
        **{f"erc20_{k}_count": v for k, v in token_counts.items()}
    }

# ──────────────────────────────────────────────────────────────────────
# Main Decision Process
# ──────────────────────────────────────────────────────────────────────
def check_and_settle():
    global ml_model, feature_cols, historical_buffer
    
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n============================================================")
    print(f"  SETTLEMENT EVALUATION RUN: {timestamp_str}")
    print(f"============================================================")
    
    conn = None
    try:
        conn = get_db_connection()
    except Exception as e:
        print(f"[Database Error] Failed to connect: {e}")
        return

    try:
        cur = conn.cursor()
        cur.execute("SELECT currency, tracked_balance, exposure FROM system_pools")
        pools = cur.fetchall()
        cur.close()
        
        now_epoch = time.time()
        start_5m_epoch = now_epoch - 300
        
        kline = get_binance_klines()
        
        market_data = get_latest_market_data()
        if market_data:
            try:
                normal_gas_price_mean_gwei = float(market_data.get("eth_base_fee_gwei", 0.05))
                erc20_gas_price_mean_gwei = float(market_data.get("eth_safe_gas_gwei", 0.05))
            except Exception:
                normal_gas_price_mean_gwei = 0.05
                erc20_gas_price_mean_gwei = 0.05
        else:
            normal_gas_price_mean_gwei = 0.05
            erc20_gas_price_mean_gwei = 0.05
            
        for pool in pools:
            currency, tracked_balance, exposure = pool
            print(f"\n---> Evaluating Pool: {currency} (Tracked Balance: {tracked_balance:.4f}, Exposure: {exposure:.4f})")
            
            # 1. Get Hard Limit
            limit_key = f"SETTLEMENT_HARD_LIMIT_{currency}"
            limit_str = os.getenv(limit_key)
            if limit_str:
                try:
                    hard_limit = float(limit_str)
                except ValueError:
                    hard_limit = 5000.0 if currency in ["USDT", "USDC"] else (1.5 if currency == "ETH" else 35.0)
            else:
                hard_limit = 5000.0 if currency in ["USDT", "USDC"] else (1.5 if currency == "ETH" else 35.0)
                
            print(f"     Hard Limit: {hard_limit:.4f} (Exposure: {exposure:.4f})")
            
            # 2. Check Hard Limit Rule
            if abs(exposure) >= hard_limit:
                print(f"     [RULE TRIGGERED] Absolute exposure {abs(exposure):.4f} >= Hard Limit {hard_limit:.4f}")
                print(f"     >>> DECISION: SETTLE (Forced by Hard Limit)")
                
                cur = conn.cursor()
                cur.execute("UPDATE system_pools SET exposure = 0.0 WHERE currency = %s", (currency,))
                conn.commit()
                cur.close()
                
                print(f"[SETTLEMENT EVENT] Settle exposure completed for {currency}")
                print(f"  Settled Amount (Exposure Change) = {exposure:.4f}")
                print(f"  New Exposure = 0.0")
                print(f"  Current Tracked Balance = {tracked_balance:.4f}")
                continue
                
            # 3. Build ML Features
            l2_metrics = get_l2_metrics(conn, currency, start_5m_epoch)
            
            rates = {"USDT": 1.0, "USDC": 1.0, "ETH": kline["price_close"], "SOL": 150.0}
            rate = rates.get(currency, 1.0)
            usd_balance = tracked_balance * rate
            
            outflow_proxy = l2_metrics["erc20_usdt_count"] * 500 + l2_metrics["tx_count"] * 10
            liquidity_ratio = usd_balance / (outflow_proxy + 1.0)
            
            dt_now = datetime.now(timezone.utc)
            row_dict = {
                "bucket_5m": dt_now,
                "tx_count": l2_metrics["tx_count"],
                "normal_tx_count": l2_metrics["normal_tx_count"],
                "erc20_tx_count": l2_metrics["erc20_tx_count"],
                "erc20_ratio": l2_metrics["erc20_ratio"],
                "normal_unique_senders": l2_metrics["normal_unique_senders"],
                "normal_unique_receivers": l2_metrics["normal_unique_receivers"],
                "normal_eth_volume": l2_metrics["normal_eth_volume"],
                "normal_eth_volume_mean": l2_metrics["normal_eth_volume_mean"],
                "normal_gas_price_mean_gwei": normal_gas_price_mean_gwei,
                "normal_gas_used_total": 0.0,
                "normal_error_rate": 0.0,
                "erc20_unique_tokens": l2_metrics["erc20_unique_tokens"],
                "erc20_unique_senders": l2_metrics["erc20_unique_senders"],
                "erc20_unique_receivers": l2_metrics["erc20_unique_receivers"],
                "erc20_gas_price_mean_gwei": erc20_gas_price_mean_gwei,
                "erc20_gas_used_total": 0.0,
                "erc20_usdt_count": l2_metrics["erc20_usdt_count"],
                "erc20_weth_count": l2_metrics["erc20_weth_count"],
                "erc20_usdc_count": l2_metrics["erc20_usdc_count"],
                "erc20_dai_count": l2_metrics["erc20_dai_count"],
                "erc20_wbtc_count": l2_metrics["erc20_wbtc_count"],
                "price_open": kline["price_open"],
                "price_high": kline["price_high"],
                "price_low": kline["price_low"],
                "price_close": kline["price_close"],
                "price_volume": kline["price_volume"],
                "price_num_trades": kline["price_num_trades"],
                "price_change_pct": kline["price_change_pct"],
                "price_range_pct": kline["price_range_pct"],
                "price_buy_ratio": kline["price_buy_ratio"],
                "hour_of_day": dt_now.hour,
                "day_of_week": dt_now.weekday(),
                "is_weekend": 1 if dt_now.weekday() in [5, 6] else 0,
                "balance_usdt": usd_balance,
                "outflow_proxy": outflow_proxy,
                "liquidity_ratio": liquidity_ratio
            }
            
            new_row_df = pd.DataFrame([row_dict])
            combined_df = pd.concat([historical_buffer, new_row_df], ignore_index=True)
            combined_df = add_lag_features(combined_df)
            
            X_new = combined_df.iloc[-1][feature_cols].fillna(0).values.reshape(1, -1)
            
            prediction = ml_model.predict(X_new)[0]
            
            if prediction == 1:
                print(f"     [ML DECISION] Model predicted SETTLE (1)")
                print(f"     >>> DECISION: SETTLE (AI Driven)")
                
                cur = conn.cursor()
                cur.execute("UPDATE system_pools SET exposure = 0.0 WHERE currency = %s", (currency,))
                conn.commit()
                cur.close()
                
                print(f"[SETTLEMENT EVENT] Settle exposure completed for {currency}")
                print(f"  Settled Amount (Exposure Change) = {exposure:.4f}")
                print(f"  New Exposure = 0.0")
                print(f"  Current Tracked Balance = {tracked_balance:.4f}")
            else:
                print(f"     [ML DECISION] Model predicted WAIT (0)")
                print(f"     >>> DECISION: WAIT")
                
    except Exception as ex:
        print(f"[Inference Error] Failed checking pool settlement: {ex}")
    finally:
        if conn:
            conn.close()
    print(f"============================================================")

# ──────────────────────────────────────────────────────────────────────
# Async Loop
# ──────────────────────────────────────────────────────────────────────
async def start_scheduler():
    global ml_model, feature_cols, historical_buffer
    
    print("=" * 60)
    print("        Bridgr Dynamic Settlement Decision System")
    print("=" * 60)
    print("[INITIALIZATION] Bridgr Dynamic Settlement Decision System initialized successfully.")
    print("Running every 5 minutes in background task...")
    print()
    
    # Load model and buffer
    try:
        if not os.path.exists(MODEL_PATH):
            print(f"[ERROR] ML Model file not found at {MODEL_PATH}")
            return
        if not os.path.exists(HISTORICAL_FEATURES_PATH):
            print(f"[ERROR] Historical features CSV not found at {HISTORICAL_FEATURES_PATH}")
            return
            
        model_bundle = joblib.load(MODEL_PATH)
        ml_model = model_bundle["model"]
        feature_cols = model_bundle["features"]
        
        historical_buffer = load_historical_buffer(HISTORICAL_FEATURES_PATH)
        print(f"[+] Loaded ML model and {len(historical_buffer)} rows for historical buffer.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize ML Settlement system: {e}")
        return
        
    # Execute loop
    while True:
        try:
            await asyncio.to_thread(check_and_settle)
        except Exception as e:
            print(f"[ERROR] Unexpected error in scheduler thread: {e}")
        await asyncio.sleep(300)
