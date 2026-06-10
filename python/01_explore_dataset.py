"""
Step 3: Load the agricultural IoT dataset and produce an initial exploration report.
Outputs: first 10 rows, column names & dtypes, and descriptive statistics.
"""

import pandas as pd
from pathlib import Path

RAW = Path(__file__).parent.parent / "data" / "raw" / "agri_iot_sensor_data.csv"

df = pd.read_csv(RAW, parse_dates=["timestamp"])

# ── 1. Shape ────────────────────────────────────────────────────────────────
print("=" * 70)
print("DATASET SHAPE")
print("=" * 70)
print(f"  Rows   : {df.shape[0]:,}")
print(f"  Columns: {df.shape[1]}")

# ── 2. First 10 rows ────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("FIRST 10 ROWS")
print("=" * 70)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 160)
pd.set_option("display.float_format", "{:.2f}".format)
print(df.head(10).to_string(index=False))

# ── 3. Column names & data types ────────────────────────────────────────────
print("\n" + "=" * 70)
print("COLUMN NAMES & DATA TYPES")
print("=" * 70)
dtype_df = pd.DataFrame({
    "column": df.columns,
    "dtype": df.dtypes.values,
    "non_null": df.notna().sum().values,
    "null_count": df.isna().sum().values,
})
print(dtype_df.to_string(index=False))

# ── 4. Basic statistics — numeric columns ───────────────────────────────────
print("\n" + "=" * 70)
print("DESCRIPTIVE STATISTICS  (numeric columns)")
print("=" * 70)
print(df.describe().T.to_string())

# ── 5. Categorical column summaries ─────────────────────────────────────────
cat_cols = ["equipment_id", "field_id", "crop_type", "operational_state"]
print("\n" + "=" * 70)
print("CATEGORICAL COLUMN VALUE COUNTS")
print("=" * 70)
for col in cat_cols:
    vc = df[col].value_counts()
    pct = (vc / len(df) * 100).round(1)
    summary = pd.DataFrame({"count": vc, "pct%": pct})
    print(f"\n{col}:\n{summary.to_string()}")

# ── 6. Date range ────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("TIME RANGE")
print("=" * 70)
print(f"  Start : {df['timestamp'].min()}")
print(f"  End   : {df['timestamp'].max()}")
print(f"  Span  : {df['timestamp'].max() - df['timestamp'].min()}")
print(f"  Freq  : hourly ({len(df):,} records)")

# ── 7. Duty cycle quick summary ──────────────────────────────────────────────
print("\n" + "=" * 70)
print("DUTY CYCLE SUMMARY (overall)")
print("=" * 70)
dc = df["operational_state"].value_counts()
dc_pct = (dc / len(df) * 100).round(2)
dc_df = pd.DataFrame({"hours": dc, "duty_cycle_%": dc_pct})
print(dc_df.to_string())
print(f"\n  Active utilisation rate: {dc_pct.get('ACTIVE', 0):.1f}%")

print("\n" + "=" * 70)
print("Exploration complete.")
print("=" * 70)
