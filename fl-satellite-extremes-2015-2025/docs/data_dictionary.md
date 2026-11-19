# Derived data in `out/`

| File | Rows | Columns |
|---|---|---|
| `atlas14_miami_intl_pds.csv` | 19 | duration, 1-yr (in), 2-yr (in), 5-yr (in), 10-yr (in), 25-yr (in), 50-yr (in), 100-yr (in), 200-yr (in), 500-yr (in), 1000-yr (in) |
| `complete_days_by_station_year.csv` | 132 | STATION, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| `conditional_scores.csv` | 1,188 | threshold, nbhd, condition, level, product, label, n_events, n_stations, hit_strict, hit_se, hit_ge10, ratio_median |
| `detection_scores.csv` | 144 | product, label, type, threshold, nbhd, n_events, hit_strict, hit_strict_lo, hit_strict_hi, hit_strict_pm1h, hit_ge10, hit_ge1, ratio_median, ratio_q25 … |
| `event_counts_summary.csv` | 4 | threshold, hours, events, stations, flagged_hours, wet_season_frac |
| `event_product_values.parquet` | 426,745 | event_id, STATION, name, lat, lon, source_group, first_hour_utc, last_hour_utc, n_exceed_hours, peak_mm_h, flag, peak_hour_utc, k, s … |
| `events_ge20.csv` | 7,466 | event_id, STATION, name, lat, lon, source_group, first_hour_utc, last_hour_utc, n_exceed_hours, peak_mm_h, flag, peak_hour_utc |
| `events_ge20_hours.csv` | 8,632 | event_id, STATION, name, lat, lon, source_group, hour_start_utc, hour_end_utc, precip_mm_h, prev_hour_mm, next_hour_mm, flag |
| `events_ge20_labeled.csv` | 7,466 | event_id, STATION, name, lat, lon, source_group, first_hour_utc, last_hour_utc, n_exceed_hours, peak_mm_h, flag, peak_hour_utc, k, s … |
| `events_ge30.csv` | 2,996 | event_id, STATION, name, lat, lon, source_group, first_hour_utc, last_hour_utc, n_exceed_hours, peak_mm_h, flag, peak_hour_utc |
| `events_ge30_hours.csv` | 3,271 | event_id, STATION, name, lat, lon, source_group, hour_start_utc, hour_end_utc, precip_mm_h, prev_hour_mm, next_hour_mm, flag |
| `events_ge30_labeled.csv` | 2,996 | event_id, STATION, name, lat, lon, source_group, first_hour_utc, last_hour_utc, n_exceed_hours, peak_mm_h, flag, peak_hour_utc, k, s … |
| `events_ge40.csv` | 1,169 | event_id, STATION, name, lat, lon, source_group, first_hour_utc, last_hour_utc, n_exceed_hours, peak_mm_h, flag, peak_hour_utc |
| `events_ge40_hours.csv` | 1,244 | event_id, STATION, name, lat, lon, source_group, hour_start_utc, hour_end_utc, precip_mm_h, prev_hour_mm, next_hour_mm, flag |
| `events_ge40_labeled.csv` | 1,169 | event_id, STATION, name, lat, lon, source_group, first_hour_utc, last_hour_utc, n_exceed_hours, peak_mm_h, flag, peak_hour_utc, k, s … |
| `events_ge50.csv` | 485 | event_id, STATION, name, lat, lon, source_group, first_hour_utc, last_hour_utc, n_exceed_hours, peak_mm_h, flag, peak_hour_utc |
| `events_ge50_hours.csv` | 511 | event_id, STATION, name, lat, lon, source_group, hour_start_utc, hour_end_utc, precip_mm_h, prev_hour_mm, next_hour_mm, flag |
| `events_ge50_labeled.csv` | 485 | event_id, STATION, name, lat, lon, source_group, first_hour_utc, last_hour_utc, n_exceed_hours, peak_mm_h, flag, peak_hour_utc, k, s … |
| `fl_station_inventory.csv` | 256 | id, lat, lon, elev, state, name, years_with_file, has_hourly_precip, n_valid_years, valid, source_group |
| `miami_2020-05-26_rain_vs_atlas14.csv` | 6 | metric, mm, inches, atlas14_context |
| `miami_lsr_2020-05-26.csv` | 13 | id, type, wfo, type.1, magf, county, typetext, state, remark, city, source, unit, valid, lon … |
| `miami_storm_events_2020-05.csv` | 7 | BEGIN_DAY, BEGIN_TIME, END_TIME, EVENT_TYPE, CZ_NAME, BEGIN_LOCATION, DAMAGE_PROPERTY, INJURIES_DIRECT, DEATHS_DIRECT, FLOOD_CAUSE, EVENT_ID, EPISODE_ID, EVENT_NARRATIVE, EPISODE_NARRATIVE … |
| `neighborhood_definitions.csv` | 36 | product, label, type, pixel_dx_km, pixel_dy_km, nbhd, block, side_km, area_km2, stations_covered |
| `product_time_alignment.csv` | 9 | product, applied_extra_lag_h, note |
| `station_attributes.csv` | 79 | id, name, lat, lon, source_group, coast_km, urban, region, coastal |
| `stations_added_if_2yr_rule.csv` | 8 | id, name, lat, lon, source_group, n_valid_years, hours_ge20, hours_ge50 |
| `valid_stations.csv` | 79 | id, lat, lon, elev, state, name, years_with_file, has_hourly_precip, n_valid_years, valid, source_group, valid_years, complete_days_total |
| `product_neighborhood_hourly.parquet` (release asset, 99 MB) | 9,458,480 | product, hour_start_utc, station, N1max, N1mean, N4max, N4mean, N9max, N9mean, N16max, N16mean, __index_level_0__ |
