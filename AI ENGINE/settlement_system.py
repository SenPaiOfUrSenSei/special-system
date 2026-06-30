"""
Settlement Decision System
==========================
End-to-end pipeline that simulates liquidity, makes settlement decisions,
trains a gradient boosting model, and evaluates performance.

Uses HistGradientBoostingClassifier (sklearn) as the ML backend.
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
import matplotlib

matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    confusion_matrix,
    classification_report,
)

# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────

DATA_PATH = "data/5min_features.csv"
INITIAL_BALANCE = 100_000.0
RANDOM_SEED = 42

# Columns used as features for ML (exclude timestamp and target)
EXCLUDE_COLS = {"bucket_5m", "settle"}


# ──────────────────────────────────────────────────────────────────────
# STEP 1: LOAD DATA
# ──────────────────────────────────────────────────────────────────────


def load_data() -> pd.DataFrame:
    """Load and prepare the 5-minute feature dataset."""
    print("=" * 60)
    print("  STEP 1: LOAD DATA")
    print("=" * 60)

    df = pd.read_csv(DATA_PATH)
    df["bucket_5m"] = pd.to_datetime(df["bucket_5m"], utc=True)
    df = df.sort_values("bucket_5m").reset_index(drop=True)

    # Fill any remaining NaN (shouldn't be any, but safe)
    df = df.fillna(0)

    print(f"  Rows:    {len(df):,}")
    print(f"  Columns: {len(df.columns)}")
    print(f"  Range:   {df['bucket_5m'].min()} -> {df['bucket_5m'].max()}")
    print(f"  Active intervals (tx_count > 0): {(df['tx_count'] > 0).sum():,}")
    print()

    return df


# ──────────────────────────────────────────────────────────────────────
# STEP 2: SIMULATE BALANCES (USDT LIQUIDITY)
# ──────────────────────────────────────────────────────────────────────


def simulate_balances(df: pd.DataFrame) -> pd.DataFrame:
    """
    Simulate USDT balance over time.

    Inflow  = small random % of tx_count (deposits arriving)
    Outflow = proportional to erc20_usdt_count + tx_count (withdrawals/settlements)
    Balance = previous + inflow - outflow, clamped at 0.
    """
    print("=" * 60)
    print("  STEP 2: SIMULATE BALANCES")
    print("=" * 60)

    rng = np.random.RandomState(RANDOM_SEED)
    n = len(df)

    tx = df["tx_count"].values
    usdt = df["erc20_usdt_count"].values

    # Inflow: 2-8% of tx_count * $200 per tx, with noise
    inflow = tx * 200 * (0.02 + 0.06 * rng.rand(n))

    # Outflow: USDT transfers drive outflow + base cost per tx
    outflow_proxy = usdt * 500 + tx * 10

    # Simulate balance walk
    balance = np.zeros(n)
    balance[0] = INITIAL_BALANCE
    for i in range(1, n):
        balance[i] = max(0.0, balance[i - 1] + inflow[i] - outflow_proxy[i])

    # Liquidity ratio: how many outflow-units the balance can cover
    liquidity_ratio = balance / (outflow_proxy + 1.0)

    df["balance_usdt"] = balance
    df["outflow_proxy"] = outflow_proxy
    df["liquidity_ratio"] = liquidity_ratio

    print(f"  Initial balance: ${INITIAL_BALANCE:,.0f}")
    print(f"  Final balance:   ${balance[-1]:,.0f}")
    print(f"  Min balance:     ${balance.min():,.0f}")
    print(f"  Min liquidity ratio: {liquidity_ratio.min():.4f}")
    print()

    return df


# ──────────────────────────────────────────────────────────────────────
# STEP 3: RULE-BASED SETTLEMENT ALGORITHM
# ──────────────────────────────────────────────────────────────────────


def should_settle(row) -> int:
    """
    Rule-based settlement decision.

    Risk captures how urgent settlement is:
      - outflow pressure (USDT + normal tx volume)
      - velocity (tx per minute)
      - price volatility
      - price drop magnitude
      - liquidity stress (inverse of liquidity ratio)

    Cost captures how expensive settlement is:
      - gas price
      - transaction volume
      - low-volatility opportunity cost

    Settle if risk exceeds cost by 20% safety margin.
    """
    # Risk components
    outflow = row["erc20_usdt_count"] + row["normal_tx_count"]
    velocity = row["tx_count"] / 5.0
    volatility = row["price_range_pct"]
    price_drop = max(0.0, -row["price_change_pct"])
    liquidity_ratio = row["liquidity_ratio"]

    liquidity_stress = 1.0 / (liquidity_ratio + 0.1)

    risk = (
        0.4 * outflow
        + 0.2 * velocity
        + 0.2 * volatility
        + 0.1 * price_drop
        + 0.5 * liquidity_stress
    )

    # Cost components
    gas = row["normal_gas_price_mean_gwei"]
    tx_count = row["tx_count"]

    cost = 0.5 * gas + 0.2 * tx_count + 0.3 * (1.0 - volatility)

    return 1 if risk > cost * 1.2 else 0


def apply_settlement_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Apply rule-based settlement algorithm to all rows."""
    print("=" * 60)
    print("  STEP 3: RULE-BASED SETTLEMENT LABELS")
    print("=" * 60)

    df["settle"] = df.apply(should_settle, axis=1)

    settle_count = df["settle"].sum()
    wait_count = len(df) - settle_count

    print(f"  SETTLE (1): {settle_count:,} ({settle_count / len(df) * 100:.1f}%)")
    print(f"  WAIT   (0): {wait_count:,} ({wait_count / len(df) * 100:.1f}%)")
    print()

    return df


# ──────────────────────────────────────────────────────────────────────
# STEP 4: TRAIN ML MODEL
# ──────────────────────────────────────────────────────────────────────


def train_model(df: pd.DataFrame):
    """
    Train HistGradientBoostingClassifier on active (tx_count > 0) rows.

    Uses time-based 80/20 split (no shuffle).
    Computes class_weight='balanced' to handle imbalance.
    """
    print("=" * 60)
    print("  STEP 4: TRAIN ML MODEL")
    print("=" * 60)

    # Filter to active intervals only
    df_active = df[df["tx_count"] > 0].copy()
    print(f"  Active rows for training: {len(df_active):,}")

    # Features and target
    feature_cols = [c for c in df_active.columns if c not in EXCLUDE_COLS]
    X = df_active[feature_cols].values
    y = df_active["settle"].values

    # Time-based split (80/20)
    split_idx = int(len(df_active) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print(f"  Train: {len(X_train):,} rows")
    print(f"  Test:  {len(X_test):,} rows")

    # Class weights for imbalance
    pos_count = (y_train == 1).sum()
    neg_count = (y_train == 0).sum()
    print(f"  Train class distribution: SETTLE={pos_count:,} WAIT={neg_count:,}")

    # Train model with balanced class weights
    model = HistGradientBoostingClassifier(
        max_iter=200,
        max_depth=6,
        learning_rate=0.1,
        class_weight="balanced",
        random_state=RANDOM_SEED,
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)

    print()
    print("  ── Model Performance ──")
    print(f"  Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
    print(f"  Precision: {precision_score(y_test, y_pred, zero_division=0):.4f}")
    print(f"  Recall:    {recall_score(y_test, y_pred, zero_division=0):.4f}")
    print()
    print("  Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"    TN={cm[0, 0]:<6} FP={cm[0, 1]:<6}")
    print(f"    FN={cm[1, 0]:<6} TP={cm[1, 1]:<6}")
    print()
    print("  Classification Report:")
    print(
        classification_report(
            y_test, y_pred, target_names=["WAIT", "SETTLE"], zero_division=0
        )
    )

    # Save model bundle (model + feature names)
    MODEL_DIR = Path("model")
    MODEL_DIR.mkdir(exist_ok=True)
    bundle = {"model": model, "features": feature_cols}
    model_path = MODEL_DIR / "settlement_model.joblib"
    joblib.dump(bundle, model_path)
    print(f"  Saved: {model_path}")
    print()

    return model, feature_cols, df_active, X_test, y_test, y_pred


# ──────────────────────────────────────────────────────────────────────
# STEP 5: SIMULATION ENGINE
# ──────────────────────────────────────────────────────────────────────


def run_simulation(df: pd.DataFrame, model, feature_cols: list[str]) -> pd.DataFrame:
    """
    Simulate system performance using the trained model.

    Loop through all rows (including zero-activity):
      - Model predicts SETTLE or WAIT
      - If SETTLE: deduct gas cost from balance
      - If WAIT: check for low-liquidity failure events

    Tracks: total settlements, total cost, failures.
    """
    print("=" * 60)
    print("  STEP 5: SIMULATION ENGINE")
    print("=" * 60)

    rng = np.random.RandomState(RANDOM_SEED)

    X_all = df[feature_cols].values
    predictions = model.predict(X_all)
    df["model_settle"] = predictions

    # Simulation state
    balance = INITIAL_BALANCE
    total_settlements = 0
    total_cost = 0.0
    total_failures = 0

    balances = []
    costs = []
    failures = []

    # Settlement cost: gas * estimated gas units (21000 for simple transfer)
    GAS_UNITS = 21_000

    for i in range(len(df)):
        row = df.iloc[i]
        gas_price = row["normal_gas_price_mean_gwei"]

        if predictions[i] == 1:
            # SETTLE: apply cost
            cost_eth = (gas_price * GAS_UNITS) / 1e9  # gwei to ETH
            # Convert to USD (approximate using price_close)
            eth_price = row["price_close"]
            cost_usd = cost_eth * eth_price

            balance -= cost_usd
            total_cost += cost_usd
            total_settlements += 1
            costs.append(cost_usd)
        else:
            costs.append(0.0)

            # Check for failure: liquidity ratio below threshold
            if row["liquidity_ratio"] < 0.1:
                total_failures += 1

        balance = max(0.0, balance)
        balances.append(balance)
        failures.append(total_failures)

    df["sim_balance"] = balances
    df["sim_cost"] = costs
    df["sim_cum_failures"] = failures

    # Settlement frequency
    active_rows = (df["tx_count"] > 0).sum()
    settle_freq = total_settlements / max(active_rows, 1)

    print()
    print("  ── Simulation Summary ──")
    print(f"  Total intervals:      {len(df):,}")
    print(f"  Total settlements:    {total_settlements:,}")
    print(f"  Settlement frequency: {settle_freq:.2%} (of active intervals)")
    print(f"  Total cost:           ${total_cost:,.2f}")
    print(f"  Final balance:        ${balance:,.2f}")
    print(f"  Total failures:       {total_failures:,}")
    print(f"  Failure rate:         {total_failures / len(df) * 100:.3f}%")
    print()

    return df


# ──────────────────────────────────────────────────────────────────────
# STEP 6: OUTPUT RESULTS
# ──────────────────────────────────────────────────────────────────────


def plot_results(df: pd.DataFrame):
    """Generate and save performance plots."""
    print("=" * 60)
    print("  STEP 6: OUTPUT RESULTS")
    print("=" * 60)

    fig, axes = plt.subplots(2, 1, figsize=(16, 10), sharex=True)

    # ── Plot 1: Balance over time with settlement markers ──
    ax1 = axes[0]
    ax1.plot(
        df["bucket_5m"],
        df["sim_balance"],
        color="#2196F3",
        linewidth=0.8,
        label="Balance (USD)",
        alpha=0.9,
    )

    # Mark settlement events
    settle_mask = df["model_settle"] == 1
    ax1.scatter(
        df.loc[settle_mask, "bucket_5m"],
        df.loc[settle_mask, "sim_balance"],
        color="#F44336",
        s=4,
        alpha=0.5,
        label="Settle event",
        zorder=3,
    )

    ax1.set_ylabel("Balance (USD)", fontsize=12)
    ax1.set_title("Simulated Balance Over Time", fontsize=14, fontweight="bold")
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    # ── Plot 2: Settlement decisions timeline ──
    ax2 = axes[1]

    # Color by decision
    colors = df["model_settle"].map({0: "#4CAF50", 1: "#F44336"})
    ax2.scatter(
        df["bucket_5m"],
        df["model_settle"],
        c=colors,
        s=2,
        alpha=0.6,
    )
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(["WAIT (0)", "SETTLE (1)"])
    ax2.set_ylabel("Decision", fontsize=12)
    ax2.set_title("Settlement Decisions Over Time", fontsize=14, fontweight="bold")
    ax2.grid(True, alpha=0.3)

    # Format x-axis
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig("balance_over_time.png", dpi=150, bbox_inches="tight")
    print("  Saved: balance_over_time.png")
    plt.close()

    # ── Plot 3: Cumulative cost ──
    fig2, ax3 = plt.subplots(figsize=(16, 5))
    ax3.fill_between(
        df["bucket_5m"],
        df["sim_cost"].cumsum(),
        color="#FF9800",
        alpha=0.7,
    )
    ax3.set_ylabel("Cumulative Cost (USD)", fontsize=12)
    ax3.set_title("Cumulative Settlement Costs", fontsize=14, fontweight="bold")
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax3.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("cumulative_cost.png", dpi=150, bbox_inches="tight")
    print("  Saved: cumulative_cost.png")
    plt.close()

    print()


# ──────────────────────────────────────────────────────────────────────
# UTILITY: LOAD SAVED MODEL
# ──────────────────────────────────────────────────────────────────────


def load_model(path: str = "model/settlement_model.joblib"):
    """Load saved model bundle for inference.

    Returns:
        model: trained classifier
        features: list of feature column names

    Usage:
        model, features = load_model()
        predictions = model.predict(new_df[features])
    """
    bundle = joblib.load(path)
    return bundle["model"], bundle["features"]


# ──────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────


def main():
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║           SETTLEMENT DECISION SYSTEM                    ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # Step 1: Load
    df = load_data()

    # Step 2: Simulate balances
    df = simulate_balances(df)

    # Step 3: Rule-based labels
    df = apply_settlement_labels(df)

    # Step 4: Train model
    model, feature_cols, df_active, X_test, y_test, y_pred = train_model(df)

    # Step 5: Simulation
    df = run_simulation(df, model, feature_cols)

    # Step 6: Output
    plot_results(df)

    print("╔══════════════════════════════════════════════════════════╗")
    print("║                  PIPELINE COMPLETE                      ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()


if __name__ == "__main__":
    main()
