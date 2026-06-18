# Agricultural IoT Analytics Dashboard

A data analytics portfolio project demonstrating end-to-end IoT sensor data analysis for agricultural equipment — from raw telemetry ingestion through SQL-based KPI computation to a Power BI duty cycle dashboard.

## Project Goal

Build a **duty cycle analysis dashboard** that shows the operational states and KPIs of farm equipment (tractors, harvesters) across a full year of hourly sensor readings.

## Tech Stack

| Layer | Tool |
|---|---|
| Data generation & EDA | Python 3, Pandas, NumPy |
| Data transformation | SQL (SQLite / DuckDB) |
| Visualisation | Power BI |
| Version control | Git / GitHub |

## Dataset

`data/raw/agri_iot_sensor_data.csv` — 8,760 hourly records (full calendar year 2024) across 4 equipment units and 4 fields.

| Column | Type | Description |
|---|---|---|
| timestamp | datetime | Hourly UTC timestamp |
| equipment_id | string | TRACTOR_01/02, IRRIGATOR_01, HARVESTER_01 |
| field_id | string | FIELD_A through D |
| crop_type | string | Wheat, Maize, Barley, Potato |
| operational_state | string | ACTIVE / IDLE / MAINTENANCE / FAULT |
| engine_rpm | float | Engine revolutions per minute |
| engine_load_pct | float | Engine load percentage (%) |
| fuel_consumption_lh | float | Fuel consumption (L/h) |
| engine_hours | float | Cumulative engine hours |
| hydraulic_pressure_bar | float | Hydraulic system pressure (bar) |
| vibration_ms2 | float | Chassis vibration (m/s²) |
| gps_speed_kmh | float | GPS-reported ground speed (km/h) |
| battery_voltage_v | float | Battery voltage (V) |
| ambient_temp_c | float | Ambient air temperature (°C) |
| humidity_pct | float | Relative humidity (%) |
| soil_moisture_pct | float | Soil volumetric moisture (%) |
| soil_ph | float | Soil pH reading |
| nitrogen_ppm | float | Soil nitrogen (ppm) |
| rainfall_mm | float | Rainfall per hour (mm) |
| alarm_flag | int | 1 = fault/alarm active |

### Key statistics

- **8,760 rows** × **20 columns** — zero nulls
- Time range: 2024-01-01 → 2024-12-30 (hourly)
- Active utilisation rate: **50.8%**
- Duty cycle breakdown: ACTIVE 50.8% · IDLE 39.3% · MAINTENANCE 7.8% · FAULT 2.1%

## Project Structure

```
agricultural-iot-analytics/
├── data/
│   ├── raw/                        # Source CSV
│   └── processed/                  # Cleaned / aggregated outputs
├── notebooks/                      # Jupyter EDA notebooks (coming soon)
├── sql/                            # KPI queries and transformations
├── python/
│   ├── generate_dataset.py         # Synthetic dataset generator
│   └── 01_explore_dataset.py       # Step 3 EDA script
└── README.md
```

## Quickstart

```bash
# 1. Install dependencies
pip install pandas numpy

# 2. Generate the dataset (already included in data/raw/)
python python/generate_dataset.py

# 3. Run the exploration report
python python/01_explore_dataset.py
```

## Planned KPIs (Power BI Dashboard)

- Equipment duty cycle % by unit and field
- Daily / monthly active hours trend
- Fuel efficiency (L/h vs. engine load %)
- Fault frequency and MTBF (mean time between failures)
- Soil moisture vs. rainfall correlation
- Engine load heat map by hour of day

## Status

- [x] Folder structure
- [x] Dataset (raw CSV, 8,760 rows × 20 columns)
- [x] Python EDA script
- [x] SQL KPI queries (6 query blocks)
- [x] Data transformation (10 processed CSVs)
- [x] Power BI dashboard (4 pages — Overview, Monthly Trends, Operations, Equipment Scorecard)
- [ ] Jupyter notebook (visualisations) — coming soon
