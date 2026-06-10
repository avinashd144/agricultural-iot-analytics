"""
Generates a realistic synthetic Agricultural IoT sensor dataset.
Mimics real Kaggle datasets (e.g., IoT Agriculture 2024, Smart Farming SF24)
with timestamped sensor readings, equipment operational states, and field metrics.
"""

import pandas as pd
import numpy as np
from pathlib import Path

SEED = 42
rng = np.random.default_rng(SEED)

N_ROWS = 8760  # hourly readings for one year
START = "2024-01-01 00:00:00"

EQUIPMENT_IDS = ["TRACTOR_01", "TRACTOR_02", "IRRIGATOR_01", "HARVESTER_01"]
FIELD_IDS = ["FIELD_A", "FIELD_B", "FIELD_C", "FIELD_D"]
CROP_TYPES = ["Wheat", "Maize", "Barley", "Potato"]
OP_STATES = ["IDLE", "ACTIVE", "MAINTENANCE", "FAULT"]

timestamps = pd.date_range(start=START, periods=N_ROWS, freq="h")

# Assign equipment/field cycling through IDs
equipment_id = [EQUIPMENT_IDS[i % len(EQUIPMENT_IDS)] for i in range(N_ROWS)]
field_id = [FIELD_IDS[i % len(FIELD_IDS)] for i in range(N_ROWS)]
crop_type = [CROP_TYPES[i % len(CROP_TYPES)] for i in range(N_ROWS)]

# Operational state — weighted: mostly ACTIVE during daytime hours
hour_of_day = timestamps.hour.to_numpy()
state_weights = np.where(
    (hour_of_day >= 6) & (hour_of_day <= 20), 0.70, 0.20
)
op_state = []
for w in state_weights:
    probs = [1 - w - 0.08 - 0.02, w, 0.08, 0.02]  # IDLE, ACTIVE, MAINT, FAULT
    op_state.append(rng.choice(OP_STATES, p=probs))

op_state = np.array(op_state)
is_active = op_state == "ACTIVE"

# Engine RPM — high when active, near-zero otherwise
engine_rpm = np.where(
    is_active,
    rng.normal(2200, 150, N_ROWS).clip(1800, 2600),
    rng.normal(800, 100, N_ROWS).clip(600, 1000),
)
engine_rpm = np.where(op_state == "FAULT", 0, engine_rpm).round(1)

# Engine load %
engine_load_pct = np.where(
    is_active,
    rng.normal(72, 10, N_ROWS).clip(50, 95),
    rng.normal(15, 5, N_ROWS).clip(5, 30),
)
engine_load_pct = np.where(op_state == "FAULT", 0, engine_load_pct).round(1)

# Fuel consumption L/h
fuel_consumption_lh = (engine_load_pct / 100 * 18 + rng.normal(0, 0.5, N_ROWS)).clip(0).round(2)

# Seasonal temperature curve + noise
day_of_year = timestamps.day_of_year.to_numpy()
ambient_temp_c = (
    10 * np.sin(2 * np.pi * (day_of_year - 80) / 365)  # seasonal
    + 5 * np.sin(2 * np.pi * hour_of_day / 24)           # diurnal
    + rng.normal(12, 2, N_ROWS)
).round(1)

# Soil moisture % — inverse relationship with temperature + rainfall events
rainfall_mm = rng.exponential(0.3, N_ROWS).round(2)
soil_moisture_pct = (
    45 - 0.4 * ambient_temp_c + 3 * rainfall_mm + rng.normal(0, 3, N_ROWS)
).clip(10, 90).round(1)

# Humidity %
humidity_pct = (
    60 + 0.5 * soil_moisture_pct - 0.3 * ambient_temp_c + rng.normal(0, 5, N_ROWS)
).clip(20, 100).round(1)

# Soil pH
soil_ph = rng.normal(6.5, 0.4, N_ROWS).clip(5.5, 8.0).round(2)

# Nitrogen sensor ppm
nitrogen_ppm = rng.normal(180, 30, N_ROWS).clip(80, 300).round(1)

# Vibration (engine/chassis) — higher when active
vibration_ms2 = np.where(
    is_active,
    rng.normal(4.5, 1.0, N_ROWS).clip(2.0, 8.0),
    rng.normal(0.8, 0.3, N_ROWS).clip(0.1, 2.0),
).round(2)

# GPS speed km/h
gps_speed_kmh = np.where(
    is_active,
    rng.normal(8, 2, N_ROWS).clip(2, 20),
    rng.uniform(0, 0.5, N_ROWS),
).round(1)

# Battery voltage V
battery_voltage_v = rng.normal(12.6, 0.3, N_ROWS).clip(11.5, 14.4).round(2)

# Hydraulic pressure bar
hydraulic_pressure_bar = np.where(
    is_active,
    rng.normal(180, 15, N_ROWS).clip(140, 220),
    rng.normal(20, 5, N_ROWS).clip(5, 40),
).round(1)

# Cumulative engine hours (monotonically increasing)
base_hours = 1250.0
engine_hours = (base_hours + np.arange(N_ROWS) / 1.0).round(1)

# Alarm flag
alarm_flag = np.where(op_state == "FAULT", 1, 0)

df = pd.DataFrame({
    "timestamp": timestamps,
    "equipment_id": equipment_id,
    "field_id": field_id,
    "crop_type": crop_type,
    "operational_state": op_state,
    "engine_rpm": engine_rpm,
    "engine_load_pct": engine_load_pct,
    "fuel_consumption_lh": fuel_consumption_lh,
    "engine_hours": engine_hours,
    "hydraulic_pressure_bar": hydraulic_pressure_bar,
    "vibration_ms2": vibration_ms2,
    "gps_speed_kmh": gps_speed_kmh,
    "battery_voltage_v": battery_voltage_v,
    "ambient_temp_c": ambient_temp_c,
    "humidity_pct": humidity_pct,
    "soil_moisture_pct": soil_moisture_pct,
    "soil_ph": soil_ph,
    "nitrogen_ppm": nitrogen_ppm,
    "rainfall_mm": rainfall_mm,
    "alarm_flag": alarm_flag,
})

out_path = Path(__file__).parent.parent / "data" / "raw" / "agri_iot_sensor_data.csv"
df.to_csv(out_path, index=False)
print(f"Dataset saved: {out_path}")
print(f"Shape: {df.shape}")
