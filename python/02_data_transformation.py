"""
Step 5: Data cleaning, transformation, and Power BI export.

Reads:  data/raw/agri_iot_sensor_data.csv
Writes: data/processed/
    01_fact_sensor_readings.csv     — cleaned base fact table
    02_duty_cycle_by_state.csv      — KPI 1: duty cycle breakdown
    03_sensor_kpis_by_state.csv     — KPI 2: avg sensor readings per state
    04_monthly_trends.csv           — KPI 3: monthly performance trends
    05_fault_analysis.csv           — KPI 4: fault frequency per equipment
    06_fault_events.csv             — KPI 4b: individual fault event log
    07_hourly_activity_profile.csv  — KPI 5: active hours by hour-of-day
    08_heatmap_dow_hour.csv         — KPI 5b: day-of-week × hour heatmap
    09_equipment_scorecard.csv      — KPI 6: per-equipment summary
    10_dim_date.csv                 — date dimension table for Power BI
"""

import pandas as pd
import numpy as np
from pathlib import Path

RAW_PATH = Path(__file__).parent.parent / "data" / "raw" / "agri_iot_sensor_data.csv"
OUT_DIR  = Path(__file__).parent.parent / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def save(df: pd.DataFrame, filename: str, label: str) -> None:
    path = OUT_DIR / filename
    df.to_csv(path, index=False)
    print(f"  [OK] {filename:<45} {len(df):>6,} rows  — {label}")

# -----------------------------------------------------------------------------
# LOAD & CLEAN
# -----------------------------------------------------------------------------
print("\n-- Loading raw data -------------------------------------------------")
df = pd.read_csv(RAW_PATH, parse_dates=["timestamp"])
print(f"  Raw shape: {df.shape}")

# Enforce sensible dtypes
cat_cols = ["equipment_id", "field_id", "crop_type", "operational_state"]
for col in cat_cols:
    df[col] = df[col].astype("category")

# Derived time columns (used across multiple outputs)
df["year"]        = df["timestamp"].dt.year
df["month"]       = df["timestamp"].dt.month
df["month_name"]  = df["timestamp"].dt.strftime("%B")
df["year_month"]  = df["timestamp"].dt.to_period("M").astype(str)
df["hour"]        = df["timestamp"].dt.hour
df["day_of_week"] = df["timestamp"].dt.dayofweek          # 0=Mon … 6=Sun
df["dow_name"]    = df["timestamp"].dt.strftime("%A")
df["date"]        = df["timestamp"].dt.date

# Flag: is this reading in an "active" state?
df["is_active"] = (df["operational_state"] == "ACTIVE").astype(int)

# Clip sensor values to physical bounds (removes any generation artefacts)
clip_rules = {
    "engine_rpm":             (0,    2600),
    "engine_load_pct":        (0,    100),
    "fuel_consumption_lh":    (0,    25),
    "hydraulic_pressure_bar": (0,    250),
    "vibration_ms2":          (0,    10),
    "gps_speed_kmh":          (0,    30),
    "battery_voltage_v":      (10,   15),
    "ambient_temp_c":         (-20,  50),
    "humidity_pct":           (0,    100),
    "soil_moisture_pct":      (0,    100),
    "soil_ph":                (3,    9),
    "nitrogen_ppm":           (0,    500),
    "rainfall_mm":            (0,    50),
}
for col, (lo, hi) in clip_rules.items():
    df[col] = df[col].clip(lo, hi)

null_count = df.isna().sum().sum()
print(f"  Null values after cleaning: {null_count}")
print(f"  Cleaned shape: {df.shape}")

# -----------------------------------------------------------------------------
# OUTPUT 01 — Cleaned fact table (base for Power BI relationships)
# -----------------------------------------------------------------------------
print("\n-- Exporting processed tables ---------------------------------------")
fact_cols = [
    "timestamp", "year", "month", "year_month", "hour", "day_of_week",
    "equipment_id", "field_id", "crop_type", "operational_state", "is_active",
    "engine_rpm", "engine_load_pct", "fuel_consumption_lh", "engine_hours",
    "hydraulic_pressure_bar", "vibration_ms2", "gps_speed_kmh", "battery_voltage_v",
    "ambient_temp_c", "humidity_pct", "soil_moisture_pct", "soil_ph",
    "nitrogen_ppm", "rainfall_mm", "alarm_flag",
]
save(df[fact_cols], "01_fact_sensor_readings.csv", "Cleaned fact table")

# -----------------------------------------------------------------------------
# OUTPUT 02 — Duty cycle breakdown by operational state
# -----------------------------------------------------------------------------
duty = (
    df.groupby("operational_state", observed=True)
    .agg(
        total_hours      = ("timestamp", "count"),
        total_fuel_litres= ("fuel_consumption_lh", "sum"),
        avg_rpm          = ("engine_rpm", "mean"),
        avg_load_pct     = ("engine_load_pct", "mean"),
    )
    .reset_index()
)
duty["duty_cycle_pct"] = (duty["total_hours"] / duty["total_hours"].sum() * 100).round(2)
duty["total_fuel_litres"] = duty["total_fuel_litres"].round(1)
duty["avg_rpm"]           = duty["avg_rpm"].round(1)
duty["avg_load_pct"]      = duty["avg_load_pct"].round(1)
duty = duty.sort_values("total_hours", ascending=False)
save(duty, "02_duty_cycle_by_state.csv", "KPI 1 — duty cycle breakdown")

# -----------------------------------------------------------------------------
# OUTPUT 03 — Average sensor KPIs per operational state
# -----------------------------------------------------------------------------
sensor_kpis = (
    df.groupby("operational_state", observed=True)
    .agg(
        avg_engine_rpm          = ("engine_rpm",              "mean"),
        avg_load_pct            = ("engine_load_pct",         "mean"),
        avg_fuel_lh             = ("fuel_consumption_lh",     "mean"),
        avg_hydraulic_bar       = ("hydraulic_pressure_bar",  "mean"),
        avg_vibration_ms2       = ("vibration_ms2",           "mean"),
        avg_speed_kmh           = ("gps_speed_kmh",           "mean"),
        avg_battery_v           = ("battery_voltage_v",       "mean"),
    )
    .round(2)
    .reset_index()
)
save(sensor_kpis, "03_sensor_kpis_by_state.csv", "KPI 2 — avg sensors per state")

# -----------------------------------------------------------------------------
# OUTPUT 04 — Monthly performance trends
# -----------------------------------------------------------------------------
monthly = (
    df.groupby("year_month")
    .agg(
        total_records       = ("timestamp",            "count"),
        active_hours        = ("is_active",            "sum"),
        fault_hours         = ("alarm_flag",           "sum"),
        avg_rpm             = ("engine_rpm",           "mean"),
        avg_load_pct        = ("engine_load_pct",      "mean"),
        total_fuel_litres   = ("fuel_consumption_lh",  "sum"),
        avg_temp_c          = ("ambient_temp_c",       "mean"),
        avg_soil_moisture   = ("soil_moisture_pct",    "mean"),
        total_rainfall_mm   = ("rainfall_mm",          "sum"),
    )
    .reset_index()
)
monthly["idle_hours"]        = (
    monthly["total_records"] - monthly["active_hours"] - monthly["fault_hours"]
)
monthly["active_duty_pct"]   = (monthly["active_hours"] / monthly["total_records"] * 100).round(2)
monthly["fault_rate_pct"]    = (monthly["fault_hours"]  / monthly["total_records"] * 100).round(2)
monthly["avg_rpm"]           = monthly["avg_rpm"].round(1)
monthly["avg_load_pct"]      = monthly["avg_load_pct"].round(1)
monthly["total_fuel_litres"] = monthly["total_fuel_litres"].round(1)
monthly["avg_temp_c"]        = monthly["avg_temp_c"].round(1)
monthly["avg_soil_moisture"] = monthly["avg_soil_moisture"].round(1)
monthly["total_rainfall_mm"] = monthly["total_rainfall_mm"].round(1)
save(monthly, "04_monthly_trends.csv", "KPI 3 — monthly performance trends")

# -----------------------------------------------------------------------------
# OUTPUT 05 — Fault frequency per equipment
# -----------------------------------------------------------------------------
fault_summary = (
    df.groupby("equipment_id", observed=True)
    .agg(
        total_readings = ("timestamp",    "count"),
        fault_count    = ("alarm_flag",   "sum"),
        avg_load_pct   = ("engine_load_pct", "mean"),
    )
    .reset_index()
)
fault_summary["fault_rate_pct"] = (
    fault_summary["fault_count"] / fault_summary["total_readings"] * 100
).round(2)
fault_summary["mtbf_hours"] = (
    fault_summary["total_readings"] / fault_summary["fault_count"].replace(0, np.nan)
).round(1)
fault_summary["avg_load_pct"] = fault_summary["avg_load_pct"].round(1)
fault_summary = fault_summary.sort_values("fault_count", ascending=False)
save(fault_summary, "05_fault_analysis.csv", "KPI 4 — fault frequency per equipment")

# -----------------------------------------------------------------------------
# OUTPUT 06 — Individual fault event log
# -----------------------------------------------------------------------------
fault_events = df[df["alarm_flag"] == 1][[
    "timestamp", "equipment_id", "field_id", "operational_state",
    "engine_rpm", "engine_load_pct", "hydraulic_pressure_bar",
    "vibration_ms2", "ambient_temp_c",
]].copy().reset_index(drop=True)
save(fault_events, "06_fault_events.csv", "KPI 4b — fault event log")

# -----------------------------------------------------------------------------
# OUTPUT 07 — Hourly activity profile (0–23)
# -----------------------------------------------------------------------------
hourly = (
    df.groupby("hour")
    .agg(
        total_readings = ("timestamp",            "count"),
        active_hours   = ("is_active",            "sum"),
        avg_rpm        = ("engine_rpm",            "mean"),
        avg_load_pct   = ("engine_load_pct",       "mean"),
        avg_fuel_lh    = ("fuel_consumption_lh",   "mean"),
    )
    .reset_index()
)
hourly["active_pct"] = (hourly["active_hours"] / hourly["total_readings"] * 100).round(2)
hourly["avg_rpm"]     = hourly["avg_rpm"].round(1)
hourly["avg_load_pct"]= hourly["avg_load_pct"].round(1)
hourly["avg_fuel_lh"] = hourly["avg_fuel_lh"].round(2)
save(hourly, "07_hourly_activity_profile.csv", "KPI 5 — active % by hour-of-day")

# -----------------------------------------------------------------------------
# OUTPUT 08 — Day-of-week × Hour heatmap grid
# -----------------------------------------------------------------------------
heatmap = (
    df.groupby(["day_of_week", "dow_name", "hour"])
    .agg(
        total_readings = ("timestamp",  "count"),
        active_hours   = ("is_active",  "sum"),
    )
    .reset_index()
)
heatmap["active_pct"] = (heatmap["active_hours"] / heatmap["total_readings"] * 100).round(2)
save(heatmap, "08_heatmap_dow_hour.csv", "KPI 5b — day-of-week × hour heatmap")

# -----------------------------------------------------------------------------
# OUTPUT 09 — Per-equipment scorecard
# -----------------------------------------------------------------------------
scorecard = (
    df.groupby(["equipment_id", "field_id", "crop_type"], observed=True)
    .agg(
        total_hours         = ("timestamp",         "count"),
        active_hours        = ("is_active",         "sum"),
        fault_hours         = ("alarm_flag",        "sum"),
        total_fuel_litres   = ("fuel_consumption_lh","sum"),
        avg_load_pct        = ("engine_load_pct",   "mean"),
        engine_hours_logged = ("engine_hours",      lambda x: x.max() - x.min()),
    )
    .reset_index()
)
scorecard["idle_hours"]        = (
    scorecard["total_hours"] - scorecard["active_hours"] - scorecard["fault_hours"]
)
scorecard["utilisation_pct"]   = (
    scorecard["active_hours"] / scorecard["total_hours"] * 100
).round(2)
scorecard["total_fuel_litres"] = scorecard["total_fuel_litres"].round(1)
scorecard["avg_load_pct"]      = scorecard["avg_load_pct"].round(1)
scorecard["engine_hours_logged"]= scorecard["engine_hours_logged"].round(0).astype(int)
save(scorecard, "09_equipment_scorecard.csv", "KPI 6 — equipment scorecard")

# -----------------------------------------------------------------------------
# OUTPUT 10 — Date dimension table (for Power BI time intelligence)
# -----------------------------------------------------------------------------
all_dates = pd.date_range(
    start=df["timestamp"].min().normalize(),
    end=df["timestamp"].max().normalize(),
    freq="D",
)
dim_date = pd.DataFrame({
    "date":         all_dates.date,
    "year":         all_dates.year,
    "month":        all_dates.month,
    "month_name":   all_dates.strftime("%B"),
    "quarter":      all_dates.quarter,
    "week":         all_dates.isocalendar().week.values,
    "day_of_week":  all_dates.dayofweek,           # 0=Mon
    "dow_name":     all_dates.strftime("%A"),
    "is_weekend":   (all_dates.dayofweek >= 5).astype(int),
    "year_month":   all_dates.to_period("M").astype(str),
    "year_quarter": all_dates.to_period("Q").astype(str),
})
save(dim_date, "10_dim_date.csv", "Date dimension (Power BI time intelligence)")

# -----------------------------------------------------------------------------
# SUMMARY
# -----------------------------------------------------------------------------
print("\n-- Transformation complete ------------------------------------------")
processed_files = sorted(OUT_DIR.glob("*.csv"))
total_size = sum(f.stat().st_size for f in processed_files)
print(f"  Files written : {len(processed_files)}")
print(f"  Total size    : {total_size / 1024:.1f} KB")
print(f"  Output folder : {OUT_DIR}")

print("\n-- Power BI import checklist ----------------------------------------")
checklist = [
    ("01_fact_sensor_readings.csv",    "Main fact table — link to dim tables via equipment_id, year_month, date"),
    ("02_duty_cycle_by_state.csv",     "Donut / bar chart — operational state distribution"),
    ("03_sensor_kpis_by_state.csv",    "Clustered bar — sensor averages by state"),
    ("04_monthly_trends.csv",          "Line chart — monthly KPI trends"),
    ("05_fault_analysis.csv",          "Table + KPI card — MTBF and fault rate per equipment"),
    ("06_fault_events.csv",            "Detail table — drill-through on fault events"),
    ("07_hourly_activity_profile.csv", "Bar chart — active % by hour-of-day"),
    ("08_heatmap_dow_hour.csv",        "Matrix heatmap — activity by day × hour"),
    ("09_equipment_scorecard.csv",     "Matrix / scorecard — per-equipment summary KPIs"),
    ("10_dim_date.csv",                "Date dimension — enable time intelligence slicers"),
]
for fname, note in checklist:
    print(f"  {fname:<45} -> {note}")
