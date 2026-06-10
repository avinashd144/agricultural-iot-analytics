-- =============================================================================
-- Agricultural IoT Analytics Dashboard — KPI Queries
-- Engine: SQLite / DuckDB compatible
-- Source table: agri_iot_sensor_data  (loaded from data/raw/agri_iot_sensor_data.csv)
-- =============================================================================


-- =============================================================================
-- KPI 1: DUTY CYCLE BREAKDOWN BY OPERATIONAL STATE
-- Hours spent in each state and percentage of total operating time.
-- Powers the "State Distribution" donut/bar chart in Power BI.
-- =============================================================================

SELECT
    operational_state,
    COUNT(*)                                              AS total_hours,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2)   AS duty_cycle_pct,
    ROUND(SUM(fuel_consumption_lh), 1)                    AS total_fuel_litres,
    ROUND(AVG(engine_rpm), 1)                             AS avg_rpm,
    ROUND(AVG(engine_load_pct), 1)                        AS avg_load_pct
FROM agri_iot_sensor_data
GROUP BY operational_state
ORDER BY total_hours DESC;


-- =============================================================================
-- KPI 2: AVERAGE SENSOR READINGS PER OPERATIONAL STATE
-- Mean RPM, engine load, fuel consumption, hydraulic pressure, vibration,
-- and GPS speed broken down by state.
-- Powers the "State vs. Sensor KPIs" clustered bar chart in Power BI.
-- =============================================================================

SELECT
    operational_state,
    ROUND(AVG(engine_rpm),              1)  AS avg_engine_rpm,
    ROUND(AVG(engine_load_pct),         1)  AS avg_load_pct,
    ROUND(AVG(fuel_consumption_lh),     2)  AS avg_fuel_lh,
    ROUND(AVG(hydraulic_pressure_bar),  1)  AS avg_hydraulic_bar,
    ROUND(AVG(vibration_ms2),           2)  AS avg_vibration_ms2,
    ROUND(AVG(gps_speed_kmh),           1)  AS avg_speed_kmh,
    ROUND(AVG(battery_voltage_v),       2)  AS avg_battery_v
FROM agri_iot_sensor_data
GROUP BY operational_state
ORDER BY operational_state;


-- =============================================================================
-- KPI 3: MONTHLY PERFORMANCE TRENDS
-- Aggregated by year-month across all equipment.
-- Powers the "Monthly Trend" line chart in Power BI.
-- =============================================================================

SELECT
    STRFTIME('%Y-%m', timestamp)              AS year_month,
    COUNT(*)                                  AS total_records,
    SUM(CASE WHEN operational_state = 'ACTIVE'      THEN 1 ELSE 0 END) AS active_hours,
    SUM(CASE WHEN operational_state = 'IDLE'        THEN 1 ELSE 0 END) AS idle_hours,
    SUM(CASE WHEN operational_state = 'MAINTENANCE' THEN 1 ELSE 0 END) AS maintenance_hours,
    SUM(CASE WHEN operational_state = 'FAULT'       THEN 1 ELSE 0 END) AS fault_hours,
    ROUND(
        SUM(CASE WHEN operational_state = 'ACTIVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    )                                         AS active_duty_cycle_pct,
    ROUND(AVG(engine_rpm),              1)    AS avg_engine_rpm,
    ROUND(AVG(engine_load_pct),         1)    AS avg_load_pct,
    ROUND(SUM(fuel_consumption_lh),     1)    AS total_fuel_litres,
    ROUND(AVG(ambient_temp_c),          1)    AS avg_temp_c,
    ROUND(AVG(soil_moisture_pct),       1)    AS avg_soil_moisture_pct,
    SUM(rainfall_mm)                          AS total_rainfall_mm,
    SUM(alarm_flag)                           AS total_faults
FROM agri_iot_sensor_data
GROUP BY STRFTIME('%Y-%m', timestamp)
ORDER BY year_month;


-- =============================================================================
-- KPI 4: FAULT FREQUENCY ANALYSIS
-- Fault count, fault rate, and mean time between faults (MTBF) per equipment.
-- Powers the "Fault Analysis" table and KPI cards in Power BI.
-- =============================================================================

-- 4a. Fault count and rate per equipment unit
SELECT
    equipment_id,
    COUNT(*)                                                        AS total_readings,
    SUM(alarm_flag)                                                 AS fault_count,
    ROUND(SUM(alarm_flag) * 100.0 / COUNT(*), 2)                   AS fault_rate_pct,
    ROUND(
        CAST(COUNT(*) AS REAL) / NULLIF(SUM(alarm_flag), 0),
        1
    )                                                               AS mtbf_hours
FROM agri_iot_sensor_data
GROUP BY equipment_id
ORDER BY fault_count DESC;

-- 4b. Fault events by month (trend)
SELECT
    STRFTIME('%Y-%m', timestamp)   AS year_month,
    equipment_id,
    SUM(alarm_flag)                AS fault_count
FROM agri_iot_sensor_data
GROUP BY STRFTIME('%Y-%m', timestamp), equipment_id
ORDER BY year_month, equipment_id;

-- 4c. Sensor readings immediately preceding a fault (fault context)
SELECT
    timestamp,
    equipment_id,
    engine_rpm,
    engine_load_pct,
    hydraulic_pressure_bar,
    vibration_ms2,
    ambient_temp_c,
    alarm_flag
FROM agri_iot_sensor_data
WHERE alarm_flag = 1
ORDER BY timestamp;


-- =============================================================================
-- KPI 5: PEAK OPERATIONAL HOURS BY TIME OF DAY
-- Hour-of-day profile showing when equipment is most active.
-- Powers the "Hourly Heatmap" or "Activity by Hour" bar chart in Power BI.
-- =============================================================================

-- 5a. Active hours count per hour-of-day bucket
SELECT
    CAST(STRFTIME('%H', timestamp) AS INTEGER)       AS hour_of_day,
    COUNT(*)                                          AS total_readings,
    SUM(CASE WHEN operational_state = 'ACTIVE' THEN 1 ELSE 0 END) AS active_hours,
    ROUND(
        SUM(CASE WHEN operational_state = 'ACTIVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    )                                                 AS active_pct,
    ROUND(AVG(engine_rpm),          1)                AS avg_rpm,
    ROUND(AVG(engine_load_pct),     1)                AS avg_load_pct,
    ROUND(AVG(fuel_consumption_lh), 2)                AS avg_fuel_lh
FROM agri_iot_sensor_data
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- 5b. Heatmap grid: day-of-week × hour-of-day active rate
SELECT
    CAST(STRFTIME('%w', timestamp) AS INTEGER)        AS day_of_week,   -- 0=Sun … 6=Sat
    CAST(STRFTIME('%H', timestamp) AS INTEGER)        AS hour_of_day,
    COUNT(*)                                          AS total_readings,
    SUM(CASE WHEN operational_state = 'ACTIVE' THEN 1 ELSE 0 END) AS active_hours,
    ROUND(
        SUM(CASE WHEN operational_state = 'ACTIVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    )                                                 AS active_pct
FROM agri_iot_sensor_data
GROUP BY day_of_week, hour_of_day
ORDER BY day_of_week, hour_of_day;


-- =============================================================================
-- KPI 6 (BONUS): PER-EQUIPMENT SUMMARY SCORECARD
-- One row per equipment — overall utilisation, fuel used, total faults.
-- Powers the "Equipment Scorecard" matrix in Power BI.
-- =============================================================================

SELECT
    equipment_id,
    field_id,
    crop_type,
    COUNT(*)                                                            AS total_hours,
    SUM(CASE WHEN operational_state = 'ACTIVE'      THEN 1 ELSE 0 END) AS active_hours,
    SUM(CASE WHEN operational_state = 'IDLE'        THEN 1 ELSE 0 END) AS idle_hours,
    SUM(CASE WHEN operational_state = 'MAINTENANCE' THEN 1 ELSE 0 END) AS maintenance_hours,
    SUM(CASE WHEN operational_state = 'FAULT'       THEN 1 ELSE 0 END) AS fault_hours,
    ROUND(
        SUM(CASE WHEN operational_state = 'ACTIVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    )                                                                   AS utilisation_pct,
    ROUND(SUM(fuel_consumption_lh),  1)                                 AS total_fuel_litres,
    ROUND(AVG(engine_load_pct),      1)                                 AS avg_load_pct,
    SUM(alarm_flag)                                                     AS total_faults,
    ROUND(MAX(engine_hours) - MIN(engine_hours), 0)                     AS engine_hours_logged
FROM agri_iot_sensor_data
GROUP BY equipment_id, field_id, crop_type
ORDER BY equipment_id;
