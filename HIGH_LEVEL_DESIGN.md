# High-Level Design: EMG Fatigue Monitoring System

## Overview

This system captures raw EMG + IMU data from a BLE wearable sensor, performs real-time fatigue
monitoring during activity (tennis, FTC robotics, etc.), and supports deep offline analysis
after a session. The pipeline spans three layers: Android app, PC live plotter, and PC offline
analysis.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BLE Wearable Sensor                          │
│   EMG (2000 Hz, 12-bit ADC) + IMU (200 Hz, accel + gyro)           │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ BLE GATT notifications
          ┌─────────────────┴──────────────────────┐
          │                                        │
          ▼                                        ▼
┌─────────────────────┐                ┌──────────────────────────┐
│   Android App       │                │   btCentral.py (PC)      │
│   (btLeApp)         │                │   BLE central, captures  │
│                     │                │   to CSV logs            │
│  Java hot path:     │                │   + forwards UDP JSON    │
│  - BLE capture      │                │   to sensordata_plotter  │
│  - IMU ring buffer  │                └──────────┬───────────────┘
│  - Gyro threshold   │                           │ UDP JSON
│    swing trigger    │                           ▼
│  - frames.bin log   │                ┌──────────────────────────┐
│                     │                │  sensordata_plotter.py   │
│  Python cold path   │                │  Live UDP plotter        │
│  (Chaquopy):        │                │  + FatigueMonitor        │
│  - FatigueMonitor   │                │    (--fatigue flag)      │
│    per-swing MDF    │                └──────────────────────────┘
│  - analysis_bridge  │
│    (JSON API)       │                ┌──────────────────────────┐
│                     │                │  emg_util_yaml_runner.py │
│  On-device decode:  │                │  Offline analysis        │
│  frames.bin →       │                │  (bout/medium/both mode) │
│  rotated CSVs       │                │  analyze_tennis_session()│
└─────────────────────┘                └──────────────────────────┘
```

---

## Data Flow

### Real-time path (Android)

```
BLE notification (EMG sample)
  → Java: append to emgFatigueBuf (ring buffer, 2600 samples)
  → Java: append to frames.bin (raw capture log)

BLE notification (IMU sample)
  → Java: check gyro magnitude >= threshold (default ~150 dps)
  → if triggered AND debounce OK (300ms):
      → snapshot emgFatigueBuf (2600 samples = 1300ms @ 2000Hz)
      → fatigueThread: call analysis_bridge.push_swing_realtime(emg_json, t_peak_ms, gmag)
          → Python: FatigueMonitor.push_swing()
              → preprocess_emg() [bandpass + notch]
              → mnf_mdf() [Welch PSD → MDF]
              → rms, env_mean
              → baseline collection / fatigue delta
          → return JSON: {mdf, rms, mdf_drop_pct, fatigue_level, warning, ...}
      → Java: update UI overlay
```

### Real-time path (PC live plotter)

```
btCentral.py → UDP JSON → sensordata_plotter.py
  → raw/env/imu packets → rolling deque buffers → matplotlib animation

  IMU packet (gmag >= --imu-thr-dps, 300ms debounce):
    → snapshot emg_fatigue_buf (deque, maxlen=2600)
    → fatigue_q.put_nowait((snap, t_peak_ms, gmag))
    → fatigue_worker thread: FatigueMonitor.push_swing()
    → update MDF trend subplot + annotation
```

### Offline path (PC)

```
frames.bin (Android)
  → btcentral_offline_decode.py: decode_frames_bin_to_rotated_csv()
  → emg_log_<session_id>_<open_id>_<idx>.csv
  → imu_log_<session_id>_<open_id>_<idx>.csv

emg_util_yaml_runner.py --config config.yaml --log-dir <folder>
  → capture_loader.discover_sessions()
  → load_session_stitched() [stitch all BLE captures as one tennis session]
  → detect_swings_from_imu() [fixed 300 dps threshold → delegates to core.detect_swing_windows_from_imu()]
  → activity_segments_from_imu() [percentile hysteresis gating]
  → per_swing_emg_features_stitched() [full: MDF+RMS+MAV+WL+ZC+SSC+MNF]
     OR per_swing_emg_medium_stitched() [medium: envelope+MDF+RMS only]
     OR segment_bouts_from_active() [bout: IMU only, no EMG]
  → baseline selection + fatigue deltas
  → plots + session_summary.json
```

---

## Key Files

| File | Location | Purpose |
|------|----------|---------|
| `emg_util.py` | `emg_util/` | Core library: preprocessing, features, swing detection, offline analysis |
| `fatigue_monitor.py` | `emg_util/` | **Canonical** `FatigueMonitor` + `preprocess_emg` (pandas-free, Android-compatible) |
| `emg_util_yaml_runner.py` | `emg_util/` | YAML-driven CLI: offline tennis session analysis |
| `capture_loader.py` | `emg_util/` | Session discovery, CSV loading, stitching |
| `capture_health.py` | `emg_util/` | EMG signal health check (contact loss detection) |
| `config.yaml` | `emg_util/` | Full analysis config |
| `config_fast.yaml` | `emg_util/` | Fast/medium mode config |
| `emg_util_nopandas.py` | `btLeApp/.../python/` | Pandas-free subset of emg_util.py for Android (Chaquopy) |
| `analysis_bridge.py` | `btLeApp/.../python/` | Python↔Java API: reset_fatigue_monitor, push_swing_realtime, get_fatigue_summary |
| `btCentral.py` | `py_scripts/` | PC BLE central: capture to CSV + UDP forwarding |
| `sensordata_plotter.py` | `py_scripts/` | Live UDP plotter + real-time FatigueMonitor |

---

## Analysis Modes (offline, `emg_util_yaml_runner.py`)

Configured via `features.mode` in YAML:

| Mode | Speed | What it computes |
|------|-------|-----------------|
| `bout` | Fastest | IMU swing detection + bout segmentation only. No EMG feature extraction. |
| `medium` | Fast | Envelope + MDF + RMS per swing + windowed RMS. Skips MAV/WL/ZC/SSC/MNF. |
| `both` (default) | Full | All features: MDF + RMS + MAV + WL + ZC + SSC + MNF per swing + windowed features + bout summary. |

---

## Real-time vs Offline Feature Comparison

| Feature | FatigueMonitor (real-time) | medium mode (offline) | both mode (offline) |
|---------|--------------------------|----------------------|---------------------|
| MDF | ✅ Welch PSD | ✅ Welch PSD | ✅ Welch PSD |
| RMS | ✅ | ✅ | ✅ |
| env_mean | ✅ `nanmean(abs(raw))` | ✅ `envelope()` LPF | ✅ `envelope()` LPF |
| MAV | ❌ | ❌ | ✅ |
| WL | ❌ | ❌ | ✅ |
| ZC / SSC | ❌ | ❌ | ✅ |
| MNF | ❌ | ❌ | ✅ |
| Baseline | ✅ median of first N swings | ✅ | ✅ |
| mdf_drop_pct | ✅ | ✅ | ✅ |
| Activity gating | ❌ (threshold trigger) | ✅ percentile hysteresis | ✅ |
| Bout segmentation | ❌ | ✅ | ✅ |

> **Note:** `env_mean` means different things in real-time vs offline:
> - Real-time: `nanmean(abs(raw))` — fast MAV proxy, no filtering
> - Offline: output of `envelope()` (rectify + 2nd-order Butterworth LPF at 3.6 Hz)
> Column names differ: `env_mean` (FatigueMonitor) vs `emg_env_mean` (offline swing features).

---

## Swing Detection: Real-time vs Offline

| | Real-time Android (Java) | Real-time PC plotter | Offline (yaml_runner) |
|---|---|---|---|
| **Method** | Fixed threshold on gyro magnitude | Fixed threshold on gyro magnitude | Fixed threshold on gyro magnitude |
| **Threshold** | ~150 dps (TODO: align to 300 dps) | 300 dps (`ThresholdSwingDetector`) | 300 dps (`thr_gyro_dps` config) |
| **Debounce** | 300ms (TODO: align to 2000ms) | 2000ms (`debounce_sec=2.0`) | 2000ms (`min_gap_ms` config) |
| **Implementation** | Java hot path | `ThresholdSwingDetector` / `HysteresisSwingDetector` | `core.detect_swing_windows_from_imu(already_in_dps=True)` |
| **Data format** | Raw LSB (converted in Java) | dps (converted by plotter) | dps (converted by `load_session_stitched()`) |
| **Window merge** | N/A | N/A | ✅ overlapping windows merged |

> **Known misalignment**: Android Java still uses ~150 dps / 300ms debounce while the plotter
> and offline analysis use 300 dps / 2000ms. This causes Android to count ~3× more "swings"
> than offline analysis. The Android threshold/debounce should be raised to match.

---

## Python on Android: Performance Analysis

### Why Python (Chaquopy) is acceptable for this use case

The key insight is that **Python is only called post-trigger, once per swing** (~every 1–3 seconds),
not per-sample. Java owns the hot path.

### Per-swing latency breakdown (mid-range Android, Snapdragon 6xx)

| Operation | Estimated time |
|-----------|---------------|
| Chaquopy JNI call overhead | 1–5 ms |
| `filtfilt` bandpass (2600 samples) | 5–15 ms |
| `filtfilt` notch × 2 | 4–10 ms |
| `scipy.signal.welch` (nperseg=1024) | 15–40 ms |
| RMS + env_mean | < 1 ms |
| **Total per swing** | **~25–70 ms** |

Swing interval during active play: **1–3 seconds**.
Processing runs in background thread → **no UI blocking**.
Effective CPU overhead: **3–10% of swing interval** — completely acceptable.

### Memory costs (one-time, loaded at app start)

| Component | RAM |
|-----------|-----|
| Python interpreter | ~20–30 MB |
| NumPy | ~20–30 MB |
| SciPy | ~40–60 MB |
| **Total** | **~80–150 MB** |

Startup cost: **2–6 seconds** cold start (one-time per app launch).

### When to reconsider Java/Kotlin

Convert to Java only if:
1. Targeting devices with **< 2 GB RAM** (150 MB Python overhead is too much)
2. Need **< 20 ms** per-swing latency (e.g., real-time visual feedback mid-swing)
3. Hard APK size constraint (SciPy adds ~15–25 MB)

### Quick win: drop SciPy dependency

`emg_util_nopandas.py` already has a **NumPy-only FFT fallback** for `mnf_mdf()` that activates
when SciPy is absent. Dropping SciPy saves ~60–80 MB RAM and ~15–25 MB APK size.
Tradeoff: plain FFT PSD vs Welch PSD — slightly less accurate MDF, acceptable for fatigue monitoring.

### What to NEVER do

**Never call Python per-sample at 2000 Hz.** JNI overhead alone (~1–5 ms/call) would consume
2–10 seconds of CPU per second of data — completely unusable. The ring-buffer + post-trigger
design correctly avoids this.

---

## FatigueMonitor: Canonical Implementation

`FatigueMonitor` and `preprocess_emg` live in **`fatigue_monitor.py`** — the single source of truth:

| File | Role |
|------|------|
| `emg_util/fatigue_monitor.py` | **Canonical** implementation (pandas-free, Android-compatible) |
| `emg_util/emg_util.py` | Re-exports `FatigueMonitor` and `preprocess_emg` via `from fatigue_monitor import ...` |
| `btLeApp/.../emg_util_nopandas.py` | Android copy — imports from `fatigue_monitor` submodule (git submodule) |

`fatigue_monitor.py` is intentionally pandas-free and scipy-optional so it can run on Android
via Chaquopy. Any change to `FatigueMonitor` or `preprocess_emg` is made **once** in
`fatigue_monitor.py` and automatically available to all callers.

### FatigueMonitor parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `fs` | 2000.0 Hz | EMG sampling rate |
| `warmup_skip_min` | 5.0 min | Skip first N minutes before collecting baseline (use 0.0 for testing) |
| `baseline_swings` | 20 | Number of swings to establish baseline (median MDF + RMS) |
| `mdf_warn_pct` | 12.0% | MDF drop threshold for "moderate" fatigue warning |
| `mdf_high_pct` | 20.0% | MDF drop threshold for "high" fatigue |

### Fatigue levels

| Level | Condition |
|-------|-----------|
| `warming_up` | In warmup period OR baseline not yet established |
| `fresh` | fatigue_pct < 33% (MDF drop < 6.6% of high threshold) |
| `moderate` | 33% ≤ fatigue_pct < 67% |
| `high` | fatigue_pct ≥ 67% (MDF drop ≥ 13.4% of high threshold) |

### EMG window for push_swing()

- **Size**: 2600 samples = 1300 ms @ 2000 Hz
- **Includes**: ±300 ms padding around swing peak for PSD stability
- **Collected by**: Java ring buffer (Android) / Python deque (sensordata_plotter)

---

## Known Issues / Maintenance Notes

1. **Android swing threshold/debounce misalignment** — Android Java uses ~150 dps / 300ms while
   the PC plotter and offline analysis use 300 dps / 2000ms. Android counts ~3× more "swings".
   Fix: raise Android `GYRO_SWING_THRESHOLD_DPS` to 300 and debounce to 2000ms.

2. **`warmup_skip_min` default differs** between `sensordata_plotter.py` (default=0.0, for testing)
   and `analysis_bridge.py` singleton (5.0, production). Use `--fatigue-warmup-min 5.0` for real
   sessions with the plotter.

3. **`imu_peak_mag` in `analysis_bridge.py`** is described as "acceleration magnitude" in the
   docstring but `sensordata_plotter.py` passes gyro magnitude (dps). The parameter is an effort
   proxy only and does not affect fatigue math, but the docstring is misleading.

4. **`env_mean` column name** means different things in real-time (`nanmean(abs(raw))`) vs offline
   (`emg_env_mean` from `envelope()` LPF). Do not compare these values directly.

5. **`_filter_baseline_by_rms` (offline) vs `FatigueMonitor` adaptive filter (real-time)** use
   different reference RMS values by design: offline uses session-wide p90 (all data available);
   real-time uses candidate pool p90 (best available approximation). Do not expect identical
   baseline MDF values between the two paths.

---

*See also: `CHANGELOG.md` for history of changes.*
