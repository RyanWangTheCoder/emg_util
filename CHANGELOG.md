# Changelog

All notable changes to `emg_util` are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

---

## [2026-02-25] — `preprocess_emg` single source of truth in `fatigue_monitor.py`

### Changed (`fatigue_monitor.py`)
- Renamed `_preprocess_emg` → `preprocess_emg` (public API).
  - `_preprocess_emg` kept as a private alias for internal use within the module.
- Updated docstring to document the 50 Hz low cutoff rationale and the public API contract.
- **`fatigue_monitor.py` is now the single source of truth for the EMG bandpass filter
  parameters** (50–450 Hz + 60/120 Hz notch). All callers import from here.

### Changed (`emg_util.py`)
- Removed duplicate `preprocess_emg` function definition (~20 lines).
- Added `from fatigue_monitor import preprocess_emg` — all callers (`compute()`,
  `emg_util_yaml_runner.py`, etc.) now use the same filter as `FatigueMonitor.push_swing()`.

### Changed (`emg_util_nopandas.py` — Android)
- Removed duplicate `preprocess_emg` function definition that still had the **old 20 Hz**
  low cutoff — it was never updated when `fatigue_monitor.py` was changed to 50 Hz.
- Added `preprocess_emg` to the existing `from fatigue_monitor import FatigueMonitor, preprocess_emg`.

### Motivation
Three copies of `preprocess_emg` existed with diverging filter parameters:
- `fatigue_monitor.py`: 50 Hz (correct, updated)
- `emg_util.py`: 50 Hz (duplicate, now removed)
- `emg_util_nopandas.py`: **20 Hz** (stale, now removed)

The Android path was silently using a different filter than the PC path, producing
inconsistent MDF/RMS features between offline PC analysis and on-device real-time
monitoring. This is now fixed.

**Maintenance rule:** to change the EMG filter, edit only `emg_util/fatigue_monitor.py`,
then run:
```
copy emg_util\fatigue_monitor.py btLeApp\app\src\main\python\fatigue_monitor.py
```

---

## [2026-02-25] — EMG bandpass low cutoff raised from 20 Hz to 50 Hz

### Changed (`fatigue_monitor.py`)
- `preprocess_emg`: low cutoff raised from **20 Hz → 50 Hz**.
  - Rationale: MyoWare sensor hardware bandpass is 50–500 Hz. Using 20 Hz in software
    passes motion artifact (5–20 Hz) that the hardware already rejects, inflating RMS
    and distorting MDF estimates.
  - Guard `if high <= 50.0: return y` updated accordingly.

---

## [2026-02-25] — Extract FatigueMonitor to canonical `fatigue_monitor.py`

### Added
- `emg_util/fatigue_monitor.py` — new self-contained canonical source for `FatigueMonitor`.
  - Zero pandas / matplotlib dependency.
  - Works on PC (full SciPy) and Android (Chaquopy, SciPy optional — numpy FFT fallback).
  - Contains private helpers `_filtfilt_safe`, `_preprocess_emg`, `_mnf_mdf` (prefixed `_` to avoid namespace pollution).
  - `FatigueMonitor` class with `reset()`, `push_swing()`, `get_summary()`.
- `btLeApp/app/src/main/python/fatigue_monitor.py` — copy of the above, deployed alongside `emg_util_nopandas.py` for Android/Chaquopy.

### Changed (`emg_util.py`)
- Removed `FatigueMonitor` class definition (~160 lines).
- Added `from fatigue_monitor import FatigueMonitor` — re-exports the class so all existing callers (`sensordata_plotter.py`, etc.) continue to work unchanged.

### Changed (`emg_util_nopandas.py`)
- Removed `FatigueMonitor` class definition (~160 lines).
- Added `from fatigue_monitor import FatigueMonitor` — re-exports the class so `analysis_bridge.py` continues to work unchanged.

### Motivation
`FatigueMonitor` was duplicated in `emg_util.py` (PC) and `emg_util_nopandas.py` (Android) and required manual sync on every change. Extracting to `fatigue_monitor.py` gives a single source of truth. The only maintenance task going forward is keeping the Android copy of `fatigue_monitor.py` in sync with `emg_util/fatigue_monitor.py` (copy on change).

---

## [2026-02-25] — Deduplication refactor: single source of truth in `emg_util.py`

### Added (`emg_util.py`)
- `feat_mav(sig)` — Mean Absolute Value (classic EMG time-domain feature)
- `feat_rms(sig)` — Root Mean Square
- `feat_wl(sig)` — Waveform Length
- `feat_zc(sig, thr)` — Zero Crossings
- `feat_ssc(sig, thr)` — Slope Sign Changes
- `robust_zscore(x, baseline_mask, eps)` — Robust z-score using median + MAD; canonical implementation moved here from `emg_util_yaml_runner.py`
- `select_baseline_swings(swings, session_t0_ms, warmup_skip_min, warmup_skip_swings, baseline_swings)` — canonical baseline swing selection
- `compute_baseline_from_swing_features(swing_feats)` — compute robust median baseline from per-swing feature DataFrame
- `apply_baseline_deltas(df, base, prefix)` — add `mdf_drop_pct` and `rms_increase_pct` columns relative to baseline

### Changed (`emg_util.py`)
- Removed `if __name__ == '__main__':` CLI entry point and `argparse` import.  
  `emg_util.py` is now a **pure importable library**; the CLI lives exclusively in `emg_util_yaml_runner.py`.

### Changed (`emg_util_yaml_runner.py`)
- Removed duplicate `robust_zscore()` function; `detect_swings_from_imu()` now calls `core.robust_zscore()`.
- `select_baseline_swings()` is now a thin wrapper that extracts YAML config params and delegates to `core.select_baseline_swings()`.
- `baseline_from_features()` is now a thin wrapper delegating to `core.compute_baseline_from_swing_features()`.
- `apply_deltas()` is now a thin wrapper delegating to `core.apply_baseline_deltas()`.
- Inline `mav / rms / wl / zc / ssc` computation blocks in `per_swing_emg_features()` replaced with `core.feat_mav/rms/wl/zc/ssc()` calls.
- Inline `mav / rms / wl / zc / ssc` computation blocks in `per_swing_emg_features_stitched()` replaced with `core.feat_mav/rms/wl/zc/ssc()` calls.

### Motivation
All EMG feature math now has a single source of truth in `emg_util.py`.  
Future fixes or tuning to `feat_zc`, `robust_zscore`, baseline logic, etc. only need to be made in one place.

---

## [2026-02-25] — Tennis session stitching + medium mode

### Added (`emg_util_yaml_runner.py`)
- `analyze_tennis_session(log_dir, cfg, out_dir)` — treats all BLE connections in a folder as one continuous tennis session; stitches EMG + IMU timelines using wall-clock `session_id` timestamps.
- `per_swing_emg_medium_stitched()` — fast per-swing features (envelope + MDF + RMS only); skips wl/zc/ssc/mnf/mav for speed.
- `windowed_emg_rms_stitched()` — fixed-window RMS/MAV across the full stitched session (O(N), no per-swing alignment).
- `_plot_fatigue_trend_stitched()` — MDF + RMS fatigue trend plot with BLE reconnection boundary markers.
- `_plot_windowed_rms()` — windowed RMS/MAV plot with reconnection markers.
- `_plot_imu_overlay_with_reconnections()` — IMU activity overlay with reconnection markers.
- `_save_tennis_session_summary()` — saves `session_summary.json` for the full tennis session.
- `features.mode == "medium"` — new analysis mode between `"bout"` (fast) and `"both"` (full).

### Added (`capture_loader.py`)
- `load_session_stitched(sessions, ...)` — stitches multiple BLE capture sessions into one continuous `abs_us` timeline; returns `(emg_df, imu_df, reconnection_times_s, capture_ids)`.

### Changed (`emg_util_yaml_runner.py`)
- `main()` now calls `analyze_tennis_session()` instead of the old per-BLE-connection loop.
- Old per-connection loop preserved as a comment for debugging reference.

---

## [2026-02-25] — Activity gating + EMG health check

### Added (`emg_util_yaml_runner.py`)
- `compute_hybrid_intensity(imu, cfg)` — hybrid gyro+dynamic-acc intensity signal with EMA smoothing.
- `activity_segments_from_imu(imu_df, cfg)` — percentile hysteresis segmentation of WORK PERIODS from IMU intensity.
- `swing_in_active_mask(swings, active_segs)` — boolean mask for swings within active segments.
- `plot_imu_activity_overlay(...)` — saves `imu_activity_overlay.png`.
- `segment_bouts_from_active(active_segs, swings, cfg)` — bout summary using active segments as primary structure.
- `_robust_z(x, ref_mask)` — internal robust z-score for activity gating (reference-mask variant; distinct from `robust_zscore`).
- `_ema_smooth(x, t_ms, tau_ms)` — time-aware exponential moving average.

### Added (`capture_health.py`)
- `emg_bad_intervals_us(emg_paths, cfg)` — detects sporadic EMG disconnect/contact-loss intervals.
- `intervals_overlap(t0, t1, intervals)` — interval overlap test.

### Changed (`emg_util_yaml_runner.py`)
- `analyze_single_session()` now runs EMG health check and optionally filters swings overlapping bad EMG intervals (`health.filter_swings_by_emg_bad`).

---

## [2026-01-19] — Initial btCentral capture format support

### Added
- `emg_util.py` — core EMG/IMU analysis library:
  - `load_emg_imu_logs()`, `load_vitals_log()`
  - `preprocess_emg()`, `envelope()`, `filtfilt_safe()`
  - `mnf_mdf()`, `rms()`
  - `compute()` — windowed feature extraction (RMS, MNF, MDF, IMU activity)
  - `analyze_fatigue()` — MDF/MNF trend + onset detection
  - `plot_all()`, `plot_paged()`
  - `FatigueMonitor` — stateful real-time per-session fatigue tracker
  - IMU detail helpers: `extract_imu_rows()`, `imu_segments()`, `build_time_axis_from_ts()`, `detect_movement_intervals()`, `run_imu_detail()`
  - Phase-1 swing-aligned helpers: `detect_swing_windows_from_imu()`, `compute_emg_window_features()`, `compute_swing_emg_features()`
- `emg_util_yaml_runner.py` — YAML-driven CLI runner
- `capture_loader.py` — session discovery and data loading
- `config.yaml`, `config_fast.yaml` — analysis configuration
- `capture_loader.py` — `discover_sessions()`, `load_emg_concat()`, `load_imu_concat()`, `summarize_session()`, `make_interleaved_df()`
