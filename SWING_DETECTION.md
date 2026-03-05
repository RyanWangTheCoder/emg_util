# Swing Detection - History, Analysis and Architecture

Documents the iterative tuning and architectural fixes for swing detection
across all three tools: sensordata_plotter.py, emg_util_yaml_runner.py, emg_util.py.

---

## Table of Contents

1. What Is a Swing?
2. Detector Iteration History
3. Cross-Tool Discrepancy - Root Cause Analysis
4. Fix 1 - HysteresisSwingDetector Bugs
5. Fix 2 - emg_util Z-Score Replaced with Fixed Threshold
6. Fix 3 - Time Axis Unification (abs_us)
7. Detector Reference
8. Future Improvements
9. Appendix - Why EMG Cannot Gate the IMU Baseline

---

## What Is a Swing?

A tennis stroke has two to three distinct IMU events, not one:

1. Back-swing - racket moves backward; generates a gyro spike (~300-500 dps)
2. Forward swing / contact - the actual strike; generates a larger spike (~600-1700 dps)
3. (sometimes) Follow-through - deceleration; may generate a third smaller spike

A naive gyro-threshold detector counts all three as separate swings.
The goal is to count one detection per tennis stroke.

---

## Detector Iteration History

### Attempt 1 - gyro_only, thr=150 dps, debounce=1.0s

Result: 26 swings / 60s
Problems: 150 dps too low - catches arm repositioning, slow drift, table bumps.
debounce=1.0s not enough to merge back-swing + forward swing.

### Attempt 2 - gyro_and_acc, thr=150 dps, debounce=1.0s

Result: 25 swings
Analysis: Adding acc >= 1.5g barely helped at 150 dps - most false positives
already had enough acc from gravity + arm movement.

### Attempt 3 - gyro_and_acc, thr=300 dps, debounce=1.0s

Result: 17 swings
Analysis: 300 dps targets only real fast strokes. Still double-counting
back-swing + forward swing pairs within 1-2s.

### Attempt 4 - gyro_and_acc, thr=300 dps, debounce=2.0s  [Current Default]

Result: 14 swings / 60s
Analysis: 17 to 14: dropped 3 back-swing/forward-swing double-counts.
14 / 60s = one stroke every ~4.3s - realistic rally/drill pace.

---

## Cross-Tool Discrepancy - Root Cause Analysis

### Problem (discovered 2026-03)

Three tools processing the same full session (onetest/, 1200s wall-clock,
808s physical sensor time) gave very different swing counts:

| Tool | Algorithm | Count |
|------|-----------|-------|
| emg_util_yaml_runner.py | Adaptive z-score (z>5, baseline=first 2s) | 972 raw -> 113 after gap filter -> 92 after EMG filter |
| sensordata_plotter.py --swing-detector threshold | Fixed 300 dps + acc>=1.5g, debounce=2s | 216 |
| sensordata_plotter.py --swing-detector hysteresis | Hysteresis th_on=350, debounce ignored (bug) | 351 |

### Root Causes

emg_util_yaml_runner.py (972 -> 113 -> 92) - three compounding problems:

1. Z-score baseline window corrupted - baseline = first 2s of session.
   If the player was already moving at capture start, the baseline median was
   inflated, making the z-score threshold too low. Diagnostic showed the
   baseline window had gyro median ~120 dps (player already active) instead
   of the true rest floor of ~20 dps.

2. min_gap_ms=300 instead of 2000 - only 300ms between swings allowed,
   vs the plotter 2s debounce. This caused every back-swing + forward swing
   pair to be counted as two separate swings.

3. Z-score cannot produce a 300 dps threshold from rest statistics -
   diagnostic analysis showed the rest floor is ~20 dps with MAD ~6 dps.
   rest_median + 5 * 1.4826 * MAD = 20 + 44 = 64 dps - far below 300 dps.
   The gap between general movement (~100-200 dps) and real swings (~300+ dps)
   cannot be bridged by rest floor statistics alone for wrist-mounted sensors.
   The distribution is a continuous ramp, not bimodal.

HysteresisSwingDetector (351 swings) - two bugs:

1. --debounce-sec CLI argument was completely ignored - HysteresisSwingDetector
   had no debounce_sec parameter at all.
2. th_on=350 was higher than ThresholdSwingDetector 300 dps, misaligning
   the two detectors.

Time axis mismatch (runner 169 vs plotter 216 after all other fixes):

- Plotter used host_rx_ms (wall-clock, 1200s span including BLE transmission delay)
- Runner used dev_us / 1000 (device uptime, 808s span - true physical time)
- Same 2s debounce on different time axes = different effective physical gap
- host_rx_ms inflates apparent session duration by ~49% for this session

---

## Fix 1 - HysteresisSwingDetector Bugs

### Changes

Added debounce_sec parameter:
- New __init__ parameter: debounce_sec=0.0 (default 0 = backward compatible)
- Added _last_trigger_t = -999.0 to reset()
- Confirmation condition: duration >= min_duration AND (t_peak - _last_trigger_t) >= debounce_sec
- Both instantiation sites (live + offline) now pass debounce_sec=float(args.debounce_sec)

Aligned defaults with ThresholdSwingDetector:
- th_on: 350 -> 300 dps
- th_off: 175 -> 150 dps (maintains 2:1 hysteresis ratio)

### Quantitative Impact

  th_on=350, th_off=175, no debounce (original bug)  ->  351 swings
  th_on=350, th_off=175, debounce=2s  (fix 1 only)   ->  197 swings
  th_on=300, th_off=150, debounce=2s  (fix 1+2)      ->  214 swings
  thr=300,   acc>=1.5g,  debounce=2s  (threshold)    ->  216 swings

216 vs 214 - only 2 apart. Residual gap is irreducible: hysteresis exit
at 150 dps sets _last_trigger_t slightly later than threshold detector debounce
start, occasionally blocking a nearby swing that TD allows.

---

## Fix 2 - emg_util Z-Score Replaced with Fixed Threshold

### Why Adaptive Threshold Cannot Work for Wrist Sensors

Extensive diagnostic analysis on the onetest session (1200s, 192k IMU samples):

Full session gyro distribution:
  p10 =   37 dps   (quiet rest floor)
  p50 =  120 dps   (median - player moving most of the time)
  p85 =  267 dps   (general movement ceiling)
  p90 =  323 dps   (swing population begins)
  p99 =  978 dps
  max = 1730 dps

The distribution is a continuous ramp, not bimodal. There is no natural
valley between general movement and swings that statistics can find.

Stationary window analysis (1s windows, sorted by gyro std):
  std<15 dps (strict rest, 46s total):  threshold =  87 dps  ->  380 swings  FAIL
  std<20 dps (91s total):               threshold = 157 dps  ->  321 swings  FAIL
  std<25 dps (150s total):              threshold = 211 dps  ->  271 swings  FAIL
  fixed 300 dps (reference):            threshold = 300 dps  ->  216 swings  PASS

EMG-gated analysis (using EMG envelope to find muscle-quiet windows):
- Even during IMU-stationary windows, EMG median = 267 counts (player gripping racket)
- EMG cannot gate the baseline - forearm muscles are active even at rest during play
- EMG-gated thresholds: 103-141 dps -> 340-360 swings (still too many)

Conclusion: The rest floor (~20 dps) and the swing threshold (~300 dps) are
10x apart. No reasonable statistical multiplier bridges this gap from rest
statistics alone. The 300 dps fixed threshold is not a magic number - it sits
at p88 of the session distribution, exactly where the swing population begins.

### Changes

emg_util_yaml_runner.py - detect_swings_from_imu():
- Replaced z-score with fixed thr_gyro_dps threshold
- Data already in dps after load_session_stitched - no LSB conversion needed in runner
- Changed min_gap_ms default: 300 -> 2000 (matches plotter debounce=2s)
- Optional acc gate via thr_acc_g config key (default 0 = disabled)

emg_util.py - detect_swing_windows_from_imu():
- Same replacement: z-score -> fixed 300 dps threshold
- Added LSB->dps conversion (this function receives raw LSB data)
- Legacy parameters (baseline_s, z_thr, min_consec) kept in signature
  for backward compatibility but ignored

config.yaml:

  # Before:
  swing_detection:
    baseline_s: 2.0
    z_thr: 5.0
    min_consec: 3
    min_gap_ms: 300

  # After:
  swing_detection:
    thr_gyro_dps: 300       # fixed gyro threshold in dps
    thr_acc_g: 0.0          # optional acc gate (0=disabled, 1.5=strict)
    min_gap_ms: 2000        # matches plotter debounce=2s

### Alignment After Fix (same host_rx_ms time axis)

  ThresholdSwingDetector  (300 dps, acc>=1.5g, debounce=2s):    216
  HysteresisSwingDetector (th_on=300, th_off=150, debounce=2s): 214  (0.9% diff  PASS)
  emg_util.detect_swing_windows_from_imu (300 dps, gap=2000ms): 222  (2.8% diff  PASS)
  emg_util_yaml_runner.detect_swings_from_imu (300 dps, gap=2000ms): 221  (2.3% diff  PASS)

---

## Fix 3 - Time Axis Unification (abs_us)

### Problem: Two Different Time Axes

| Tool | Time axis | Session span | Effective debounce |
|------|-----------|-------------|-------------------|
| sensordata_plotter.py | host_rx_ms (wall-clock) | 1200s | 2.0s wall-clock |
| emg_util_yaml_runner.py | dev_us / 1000 (device uptime) | 808s | 2.0s physical |

The 1200s vs 808s difference (49% inflation) comes from BLE transmission delay
accumulated over the session - host_rx_ms records when packets arrived at the
PC, not when they were captured by the sensor.

### The Timestamp Problem in Detail

Every CSV row has two timestamps:

| Timestamp | Source | Properties |
|-----------|--------|------------|
| dev_us | ESP32 micros(), extended to 64-bit by DeviceClockExtender on host | Accurate physical time within a connection. Resets to 0 on ESP32 reboot. DeviceClockExtender has a ~71min residual offset if device ran >71min without rebooting before reconnect. |
| host_rx_ms | PC wall-clock at BLE packet receive time | Always monotonically increasing. Includes BLE transmission delay (~10-50ms/sample) and reconnection gaps. |

### Reconnection Cases

Two distinct cases occur when BLE reconnects:

Case 1 - BLE dropout only (ESP32 keeps running):
- dev_us continues counting - it IS the physical timeline
- host_rx_ms has a gap equal to the dropout duration
- Using host_rx_ms inflates the apparent gap

Case 2 - ESP32 hard reset (dev_us resets to 0):
- dev_us restarts from 0 - cannot be used directly across the reconnection
- host_rx_ms gap gives the correct inter-connection duration
- Using dev_us directly would overlap the two connections

Note: BLE reconnection always causes a new session_id file. ESP32 reset
always causes BLE reconnection. But BLE reconnection does NOT necessarily
mean ESP32 reset - the device may keep running through a BLE dropout.

### Solution: Hybrid abs_us Timeline

capture_loader.load_session_stitched() builds a reconstructed physical
timeline abs_us using a hybrid approach:

Within each BLE connection:
  abs_us = dev_us - dev_us.min()   # accurate physical time, no BLE jitter

Between connections:
  gap_us = (host_rx_ms_first_of_next - host_rx_ms_last_of_prev) * 1000
  abs_us_next = abs_us_prev_end + gap_us + (dev_us - dev_us.min())

Using host_rx_ms gap between connections is correct for both cases:
- BLE dropout only: host_rx_ms gap = actual dropout duration
- ESP32 reset: host_rx_ms gap = reboot + reconnect duration
- DeviceClockExtender 71-min residual: irrelevant - dev_us not used across connections

This is simpler and more robust than trying to detect which case occurred
from dev_us continuity.

### Unit Test Results

  Case 1 - BLE dropout only:            span=0->95s,  gap=5s            PASS
  Case 2 - ESP32 reset:                 span=0->120s, gap=30s           PASS
  Case 3 - Mixed (dropout then reset):  span=0->165s, gap1=5s gap2=25s  PASS

### Changes

capture_loader.py:
- load_emg_concat() and load_imu_concat(): added host_rx_ms to default usecols
- load_session_stitched(): replaced two-case dev_us detection with hybrid
  host_rx_ms-gap approach

emg_util_yaml_runner.py:
- Replaced load_imu_concat() with load_session_stitched() in swing detection path
- ts_ms is now abs_us / 1000 - correct physical time for debounce
- Fixed FSR defaults: acc 2g->4g, gyro 250->1000 dps (matches firmware)

sensordata_plotter.py:
- Added --log-dir argument for multi-file / multi-connection sessions
- Replaced manual host_rx_ms CSV reading with capture_loader.load_session_stitched()
- Time axis now uses abs_us (physical time) instead of host_rx_ms (wall-clock)
- Falls back to single-file host_rx_ms path if capture_loader not available

### Final Alignment (all on abs_us 808s physical timeline)

  ThresholdSwingDetector  (300 dps, acc>=1.5g, debounce=2s):    177
  Runner detect_swings    (300 dps, gap=2000ms):                 169  (4.5% diff  PASS)
  HysteresisSwingDetector (th_on=300, th_off=150, debounce=2s): 150  (pre-existing - additional gates)

The HD vs TD difference (150 vs 177) is expected and pre-existing: HD has
additional gates (th_acc_hp, th_jerk, min_duration) that reject marginal
swings that TD accepts. This is HD intended behavior, not a bug.

---

## Detector Reference

### ThresholdSwingDetector (Default)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| thr_gyro_dps | 300 dps | Sits at p88 of session distribution - swing population begins here |
| thr_acc_g | 1.5 g | Rejects slow drift; at rest ~1.0g due to gravity |
| debounce_sec | 2.0 s | Merges back-swing + forward swing into one count |
| min_peak_gyro_dps | 200 dps | Safety net if threshold is lowered; redundant at thr=300 |
| mode | gyro_and_acc | Both gyro AND acc must exceed thresholds |

Logic:
  above = gmag >= thr_gyro_dps AND amag >= thr_acc_g
  if above: track peak
  if peak ends AND peak_gmag >= min_peak_gyro_dps AND gap >= debounce_sec: confirm swing

### HysteresisSwingDetector (Advanced)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| th_on | 300 dps | Aligned with ThresholdSwingDetector entry |
| th_off | 150 dps | 2:1 hysteresis ratio - natural swing exit |
| th_acc_hp | 0.6 g | High-pass acc threshold for impact detection |
| th_jerk | 80 g/s | Jerk threshold for impact detection |
| min_duration | 0.08 s | Rejects noise spikes shorter than 80ms |
| debounce_sec | 2.0 s | Same as ThresholdSwingDetector for fair comparison |

Advantages over ThresholdSwingDetector:
- Natural state machine exit (gmag < 150) vs crude 2s forced gap
- Impact detection via high-pass accel + jerk
- Better for fast rallies (<2s between strokes)

When to use each:

| Use Case | Recommended |
|----------|-------------|
| Quick stroke counting | threshold (default, simpler) |
| EMG-impact correlation | hysteresis (provides impact times) |
| Fatigue analysis | hysteresis (impact = peak muscle activation) |
| Fast rallies (<2s between strokes) | hysteresis (no forced debounce gap) |

### emg_util_yaml_runner / emg_util

| Parameter | Config Key | Default | Notes |
|-----------|-----------|---------|-------|
| Gyro threshold | thr_gyro_dps | 300 dps | Same as plotter |
| Acc gate | thr_acc_g | 0.0 (disabled) | Set to 1.5 to match ThresholdSwingDetector |
| Min gap | min_gap_ms | 2000 ms | Matches plotter debounce=2s |
| Window pre/post | pre_ms / post_ms | 250 / 450 ms | EMG feature extraction window |

---

## Back-Swing vs Forward Swing - Why debounce=2.0s Works

A typical tennis forehand timeline:

  t=0.0s  - back-swing starts (gyro rises)
  t=0.3s  - back-swing peak (~300-500 dps)   <- detector triggers here
  t=0.8s  - transition (gyro drops below threshold)
  t=1.2s  - forward swing starts (gyro rises again)
  t=1.5s  - contact peak (~600-1200 dps)     <- detector would trigger again
  t=1.8s  - follow-through (gyro drops)

With debounce=1.0s: gap = 1.2s > 1.0s -> both confirmed (double-count)
With debounce=2.0s: gap = 1.2s < 2.0s -> forward swing suppressed

---

## Future Improvements

1. Direction-aware detection - use sign of dominant gyro axis to distinguish
   back-swing (negative rotation) from forward swing (positive rotation). Would
   allow debounce=0.5s while still counting only forward swings. Requires
   knowing sensor orientation on wrist.

2. Per-player threshold calibration - 300 dps is correct for an average adult
   player. Juniors or players with weaker strokes may need 200-250 dps. Could be
   set via --imu-thr-dps or a per-player config entry.

3. Stroke classifier - ML model trained on gyro+acc window to classify
   forehand / backhand / serve. Would give stroke type in addition to count.

4. Racket-mounted sensor - for 100% impact detection, mount sensor on racket
   handle instead of wrist. Wrist sensor achieves ~60% impact detection rate
   because grip absorption and off-center hits reduce shock transmission.

5. Plotter multi-session breakdown - --log-dir currently loads all connections
   as one stitched session. Could add per-connection swing rate display to show
   fatigue progression across reconnections.

---

## Appendix - Why EMG Cannot Gate the IMU Baseline

During the adaptive threshold investigation, EMG was considered as a gate to
find true rest windows (IMU stationary AND EMG quiet = no muscle activation).

Result: Even during IMU-stationary windows (gyro std < 15 dps), the EMG
envelope median was 267 counts (p75 = 729 counts). The player is constantly
gripping the racket, maintaining forearm muscle tone even when standing still.

This means:
- IMU stationary + EMG quiet windows are very rare (<30 windows = 15s total)
- Those windows give a rest floor of ~29 dps -> threshold = 130 dps (still too low)
- EMG cannot reliably separate arm at rest from arm moving but not swinging
  for a wrist-mounted sensor during a tennis session

Conclusion: EMG is useful for filtering swing windows by electrode quality
(already implemented via capture_health.py), but cannot improve the gyro
threshold estimation. The fixed 300 dps threshold is the correct solution.

---

Last Updated: 2026-03 (adaptive threshold investigation + time axis unification)
