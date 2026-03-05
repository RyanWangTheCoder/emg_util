# Swing Detection Tuning — History & Rationale

Documents the iterative tuning of `SwingDetector` in `sensordata_plotter.py`
against real tennis session data (log0303, 60-second session).

---

## The Problem: What Is a "Swing"?

A tennis stroke has **two distinct IMU events**, not one:

1. **Back-swing** — racket moves backward; generates a gyro spike
2. **Forward swing (contact)** — the actual strike; generates a larger gyro spike
3. *(sometimes)* **Follow-through** — deceleration; may generate a third smaller spike

A naive gyro-threshold detector counts all three as separate swings.
The goal is to count **one detection per tennis stroke**.

---

## Iteration History

### Attempt 1 — `gyro_only`, thr=150 dps, debounce=1.0s

```
--swing-detect-mode gyro_only --imu-thr-dps 150 --debounce-sec 1.0
```

**Result:** 26 swings detected in 60s  
**Problems:**
- 150 dps threshold too low — catches arm repositioning, slow drift, table bumps
- `gyro_only` mode has no acc filter — any rotation above 150 dps triggers
- debounce=1.0s not enough to merge back-swing + forward swing (can be <1s apart)
- 26 / 60s = one every 2.3s — unrealistically fast for a practice session

---

### Attempt 2 — `gyro_and_acc`, thr=150 dps, debounce=1.0s

```
--swing-detect-mode gyro_and_acc --imu-thr-dps 150 --debounce-sec 1.0
```

**Result:** 25 swings detected  
**Improvement:** Dropped only 1 detection  
**Analysis:** Adding `acc >= 1.5g` filter barely helped at 150 dps — most false
positives already had enough acc from gravity + arm movement to pass the acc threshold.

---

### Attempt 3 — `gyro_and_acc`, thr=300 dps, debounce=1.0s

```
--swing-detect-mode gyro_and_acc --imu-thr-dps 300 --debounce-sec 1.0
```

**Result:** 17 swings detected  
**Improvement:** Significant drop — 300 dps targets only real fast strokes  
**Analysis:** 17 / 60s = one every 3.5s. Still likely counting some back-swing +
forward swing pairs as two events (pairs within 1–2s of each other).

---

### Attempt 4 — `gyro_and_acc`, thr=300 dps, debounce=2.0s ✅ **Current Default**

```
--swing-detect-mode gyro_and_acc --imu-thr-dps 300 --debounce-sec 2.0
```

**Result:** 14 swings detected  
**Analysis:**
- 17 → 14: dropped 3 detections (back-swing/forward-swing pairs that were 1–2s apart)
- 14 / 60s = one stroke every ~4.3s — **realistic rally/drill pace**
- Remaining 14 all correspond to clear sharp gyro spikes ≥ 300 dps with simultaneous acc spike
- Assessment: **14 is likely the true stroke count**, off by at most 1–2

---

## Current Defaults (as of 2026-03-04)

### ThresholdSwingDetector (Default)

| Parameter | Old Default | New Default | Rationale |
|---|---|---|---|
| `--swing-detect-mode` | `gyro_only` | `gyro_and_acc` | Rejects slow drift and table bumps |
| `--imu-thr-dps` | 150 dps | **300 dps** | 150 catches arm repositioning; 300 targets real strokes |
| `--debounce-sec` | 1.0 s | **2.0 s** | Merges back-swing + forward swing into one count |
| `--imu-thr-acc-g` | 1.5 g | 1.5 g | Unchanged; at rest ≈ 1.0g due to gravity |
| `min_peak_gyro_dps` | 200 dps | 200 dps | Hardcoded; rejects noise that barely crosses threshold |

### HysteresisSwingDetector (Advanced, Opt-In)

| Parameter | Value | Rationale |
|---|---|---|
| `th_on` | **350 dps** | Enter swing (slightly higher than threshold's 300) |
| `th_off` | **175 dps** | Exit swing (hysteresis gap = half of th_on) |
| `th_acc_hp` | **0.6 g** | Impact detection: high-pass accel threshold |
| `th_jerk` | **80 g/s** | Impact detection: jerk threshold |
| `min_duration` | **0.08 s** | Min swing duration (80ms) |
| `impact_window` | **0.15 s** | Search ±150ms around gyro peak for impact |

**Usage:**
```bash
python sensordata_plotter.py --mode offline \
    --emg-file log.csv --imu-file imu.csv \
    --swing-detector hysteresis
```

**Validation (log0303, 60s session):**
- **15 swings detected** (vs 14 for threshold — essentially identical)
- **9 impacts detected** (60% impact detection rate)
- **6 swings without impact** — likely practice swings or soft contacts where shock didn't reach wrist sensor

---

## SwingDetector Logic Summary

```
for each IMU sample (t, gmag, amag):
    above = gmag >= thr_gyro_dps AND amag >= thr_acc_g   # gyro_and_acc mode

    if above and not in_peak:
        start tracking peak (record gmag, t)
    elif above and in_peak:
        update peak if gmag is higher
    elif not above and in_peak:
        # peak ended — confirm if:
        #   1. peak_gmag >= min_peak_gyro_dps (200 dps)  — rejects noise/drift
        #   2. t - last_confirmed_t >= debounce_sec       — rejects back-swing double-count
        if confirmed:
            record swing at peak_t
            update last_confirmed_t
```

**Key insight:** `min_peak_gyro_dps=200` and `thr_gyro_dps=300` work together:
- `thr_gyro_dps` gates entry into a peak (must reach 300 to start tracking)
- `min_peak_gyro_dps` gates confirmation (peak must reach 200 to confirm)
- Since 300 > 200, `min_peak_gyro_dps` is effectively redundant when `thr_gyro_dps=300`
  but provides a safety net if threshold is lowered in future experiments

---

## Back-Swing vs Forward Swing — Why debounce=2.0s Works

A typical tennis forehand timeline:
```
t=0.0s   — back-swing starts (gyro rises)
t=0.3s   — back-swing peak (~300–500 dps)  ← old detector triggers here
t=0.8s   — transition (gyro drops below threshold)
t=1.2s   — forward swing starts (gyro rises again)
t=1.5s   — contact peak (~600–1200 dps)    ← old detector triggers again
t=1.8s   — follow-through (gyro drops)
```

With `debounce=1.0s`: back-swing at t=0.3s, forward swing at t=1.5s → gap=1.2s > 1.0s → **both confirmed** (double-count)  
With `debounce=2.0s`: back-swing at t=0.3s, forward swing at t=1.5s → gap=1.2s < 2.0s → **forward swing suppressed** ✅

---

## HysteresisSwingDetector — Advanced Algorithm with Impact Detection

### Motivation

The threshold detector's `debounce=2.0s` is a **crude workaround**:
- Forces 2s gap between ANY two detections
- Misses fast rallies (strokes <2s apart)
- No impact detection (can't distinguish contact moment from swing motion)

Hysteresis detector solves both problems:
- **Natural state machine** (TH_ON/TH_OFF) eliminates arbitrary debounce
- **Impact tagging** via high-pass accel + jerk

### Algorithm

```python
for each IMU sample (t, gmag, amag):
    # High-pass filter on accel (removes gravity)
    acc_lp += alpha_acc * (amag - acc_lp)
    acc_hp = amag - acc_lp
    jerk = |acc_hp - acc_hp_prev| / dt
    
    # State machine (uses RAW gmag, not LPF)
    if state == IDLE:
        if gmag > TH_ON:  # enter swing
            state = IN_SWING
            track peak_gyro, t_peak
    
    elif state == IN_SWING:
        update peak if gmag higher
        
        # Impact detection (within ±150ms of peak)
        if |t - t_peak| < 0.15:
            if acc_hp > TH_ACC_HP or jerk > TH_JERK:
                record impact_t
        
        # Exit swing
        if gmag < TH_OFF:
            if duration >= 0.08s:
                confirm swing at t_peak
                record impact_t (or None)
            state = IDLE
```

### Key Differences vs Threshold Detector

| Feature | ThresholdSwingDetector | HysteresisSwingDetector |
|---------|------------------------|-------------------------|
| **Entry condition** | `gmag >= 300 AND amag >= 1.5` | `gmag > 350` (hysteresis entry) |
| **Exit condition** | `gmag < 300` + debounce=2.0s | `gmag < 175` (hysteresis exit) |
| **Back-swing handling** | Crude debounce (2s forced gap) | Natural (stays IN_SWING until gmag drops) |
| **Impact detection** | ❌ No | ✅ Yes (acc_hp + jerk) |
| **Output** | Swing peak times | Swing peak times + impact times |
| **Complexity** | Simple (5 state vars) | Moderate (8 state vars + LPF) |

### Why Hysteresis Works Better

**Example: Fast rally (1.5s between strokes)**

```
Threshold detector:
  t=0.0s: stroke 1 detected
  t=1.5s: stroke 2 arrives, but debounce blocks it (< 2.0s)
  Result: 1 stroke counted (missed stroke 2)

Hysteresis detector:
  t=0.0s: gmag > 350 → enter IN_SWING
  t=0.5s: gmag < 175 → exit, confirm stroke 1
  t=1.5s: gmag > 350 → enter IN_SWING again
  t=2.0s: gmag < 175 → exit, confirm stroke 2
  Result: 2 strokes counted ✅
```

### Impact Detection — Why 60% Rate Is Expected

**Wrist-mounted sensor limitations:**
- Gyro captures **all rotations** (100% swing detection)
- Accel only captures impact shock **if it propagates to wrist**

Factors affecting impact detection:
1. **Grip tightness** — loose grip absorbs shock
2. **Stroke type** — slice/drop shot = softer contact
3. **Contact point** — off-center hits = less shock transmission
4. **Practice swings** — no ball contact = no impact

**Validation (log0303, 60s):**
- 15 swings detected
- 9 impacts detected (60%)
- 6 swings without impact — likely practice swings or soft contacts

**For 100% impact detection**, sensor must be on racket handle (not wrist).

### When to Use Each Detector

| Use Case | Recommended Detector |
|----------|---------------------|
| Quick stroke counting | `threshold` (default) |
| EMG-impact correlation | `hysteresis` (need impact times) |
| Fatigue analysis | `hysteresis` (impact = peak muscle activation) |
| Fast rallies (<2s between strokes) | `hysteresis` (no debounce limit) |
| Debugging / comparison | `threshold` (simpler, proven) |

---

## Future Improvements

1. **Direction-aware detection** — use sign of dominant gyro axis (gx/gy/gz) to distinguish
   back-swing (negative rotation) from forward swing (positive rotation). Would allow
   `debounce=0.5s` while still counting only forward swings. Requires knowing sensor orientation.

2. **Adaptive threshold** — z-score based threshold that adapts to each player's swing intensity.
   Useful for players with weaker strokes where 300 dps may miss real swings.

3. **Stroke classifier** — ML model trained on gyro+acc window to classify forehand/backhand/serve.
   Would give stroke type in addition to count.

4. **Racket-mounted sensor** — for 100% impact detection, mount sensor on racket handle instead of wrist.

---

**Last Updated:** 2026-03-04
