# Changelog

All notable changes to `emg_util` are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

---

## [2026-03-02] — Feature: Add dynamic RAW zoom & fix IMU scaling (`sensordata_plotter.py`)

### Added (`sensordata_plotter.py`)
- Added `--raw-zoom` argument to optionally zoom the RAW subplot Y-axis.
  - In **offline mode**, it zooms the Y-axis to `+/- 500` counts around the DC bias midpoint (`emg_ymax / 2.0`), which is ideal for inspecting low-gain resting-state noise.
  - In **live mode**, it enables **dynamic Y-axis zooming** that automatically tracks the min/max of the rolling `raw_buf` (with a minimum padding of 100 counts to prevent extreme magnification of the baseline noise floor). This ensures the RAW signal optimally fills the screen regardless of the sensor gain setting or muscle effort.

### Changed (`sensordata_plotter.py`)
- **IMU Subplot Scaling Fixed:** Removed dynamic zooming from the IMU (accelerometer) subplot. It now uses a fixed absolute minimum scale (0 to 4g) to preserve the visual sense of activity intensity. The axis will dynamically expand upwards only if extreme acceleration exceeds the 4g threshold, preventing data clipping while maintaining an absolute visual baseline.

---

## [2026-03-02] — Fix: plotter stuck after BLE reconnect (`sensordata_plotter.py`)

### Fixed (`sensordata_plotter.py`)
- **Plot frozen/stuck after BLE disconnect + reconnect.**
  - **Root cause**: when `btCentral.py` reconnects it sends a new `emg_meta` packet
    with `seg=0`. The device's `dev_us` hardware timer resets to 0 on reconnect.
    The old code only reset the `FatigueMonitor` on `seg=0`, but left `t0_dev_us`
    pointing at the old (large) timestamp from the previous session.
    Every new `dev_us` value was therefore a large negative number relative to
    `t0_dev_us`, so `prune()` immediately discarded every incoming sample and the
    rolling-window plot appeared frozen.
  - **Fix** (inside the `emg_meta` / `seg=0` handler in `update()`):
    - `t0_dev_us = None` — forces re-anchor to the first new packet's timestamp.
    - `raw_buf`, `env_dev_buf`, `env_lpf_buf`, `imu_buf` cleared — removes stale
      pre-disconnect data so the rolling window starts fresh.
    - `recent_raw_dev_us` cleared — prevents sr-inference from mixing old/new timestamps.
    - `env_filter` re-created (if `emg_sr_hz` is known) — clears IIR state so the
      LPF does not carry stale history into the new session.
    - `in_peak` and `peak_gyro_mag` reset — fixes a pre-existing minor bug where a
      peak in progress at disconnect time would leave `in_peak=True` indefinitely.
  - **No behaviour change for normal operation**: the guard `meta_seg == 0 and
    t0_dev_us is not None` is identical to the original; first connection
    (`t0_dev_us is None`) and segment rotations (`seg ≥ 1`) are unaffected.
    `swing_count`, `fatigue_result`, and `last_vitals` are intentionally NOT reset
    (session-level state that should survive a BLE reconnect).

---

## [2026-02-25] — IMU FSR raised: gyro 250→1000 dps, acc 2→4 g (anti-saturation)

### Changed (`myoware_imu_v2/myoware_imu_v2.ino`)
- `IMU_GYRO_FSR_DPS`: 250 → **1000** dps
  - Tennis swings peak at ~500–1000 dps. FSR=250 saturated on every hard swing,
    clipping `gx/gy/gz` at ±32767 and making gyro-based swing detection unreliable.
- `IMU_ACC_FSR_G`: 2 → **4** g
  - `imu_peak_acc_dyn` was showing median=2.464g (at the 2g ceiling). FSR=4g
    doubles the range while keeping 12-bit resolution at 0.122 mg/LSB.
- Both FSR codes are transmitted in every IMU meta frame (`FLAG_IMU_META_V2`),
  so the Python decoder applies the correct physical-unit scaling automatically.
  No decoder changes needed when changing these values.

### Changed (fallback defaults — updated to match new firmware)
- `btCentral.py` lines 493-494: `cur_acc_fsr_g = 2` → `4`, `cur_gyro_fsr_dps = 250` → `1000`
  - Used when a capture file has no FSR meta (old firmware or missing FLAG_IMU_META_V2).
- `emg_util/capture_loader.py` `load_imu_concat()` and `load_session_stitched()`:
  `acc_fsr_default_g=2.0` → `4.0`, `gyro_fsr_default_dps=250.0` → `1000.0`
- `emg_util/config.yaml`: `acc_fsr_default_g: 2` → `4`, `gyro_fsr_default_dps: 250` → `1000`
- `emg_util/config_fast.yaml`: same as above
- `emg_util/tennis_analysis_cloud.ipynb` Cell 5 `CLOUD_CONFIG`:
  `acc_fsr_default_g: 2` → `4`, `gyro_fsr_default_dps: 250` → `1000`

### Note: Android `btcentral_offline_decode.py` — no change needed
- The FSR lookup tables (`ACC_FSR_CODE_TO_G`, `GYRO_FSR_CODE_TO_DPS`) are correct
  (they map all 4 FSR codes). The decoder reads FSR from the frame and writes it to
  CSV; no hardcoded defaults exist in the Android decoder.

---

## [2026-02-25] — Per-swing IMU accelerometer features + acc_drop_pct fatigue indicator

### Added (`emg_util_yaml_runner.py`)
- `per_swing_emg_features_stitched()` now accepts optional `imu_df` parameter.
  When provided, computes per-swing IMU accelerometer features:
  - `imu_mean_acc_dyn` — mean `|acc_mag - 1g|` within swing window (effort/impact proxy)
  - `imu_peak_acc_dyn` — peak `|acc_mag - 1g|` within swing window
  - Note: gyro features omitted — gyro saturates at FSR=250 dps for tennis swings.
    Increase `gyro_fsr_dps` to 1000+ in firmware to unlock gyro-based features.
- `_plot_fatigue_trend_stitched()` now adds a 4th subplot (`acc_drop_pct`) when
  `swing_acc_drop_pct` is present in `swing_features.csv`.
  - Teal scatter + rolling median trend line
  - Reference lines: 0% (baseline), +10% (mild), +20% (significant)

### Added (`emg_util.py`)
- `compute_baseline_from_swing_features()` now includes `imu_mean_acc_dyn` in the
  baseline dict (median of baseline swings).
- `apply_baseline_deltas()` now computes `{prefix}acc_drop_pct`:
  - `acc_drop_pct > 0` means swing force decreased relative to baseline (fatigue signal)
  - Only added when `imu_mean_acc_dyn` is present in both the DataFrame and baseline dict.

### Changed (`analyze_tennis_session()`)
- Full mode now passes `imu_df` to `per_swing_emg_features_stitched()`.

### Verified (log0207 session, 71 min, 6 BLE connections)
- `swing_features.csv`: 653 swings, all new columns present
  - `imu_mean_acc_dyn`: median=0.869g (not saturated, reliable fatigue signal)
  - `imu_peak_acc_dyn`: median=2.464g (saturated at 2g FSR — expected)
  - `swing_acc_drop_pct`: median=+2.4% (slight force decrease over session)
- `baseline.json`: `imu_mean_acc_dyn=0.8991g` captured in baseline
- `fatigue_trend.png`: 4-subplot layout (MDF, RMS, MDF drop%, acc drop%)

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
