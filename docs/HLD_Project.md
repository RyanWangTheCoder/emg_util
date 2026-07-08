# High-Level Design: EMG/IMU Biometric Analysis System

## 1. Purpose and Scope

This document describes the end-to-end EMG/IMU biometric analysis system across all major components:

- Wearable Arduino/ESP32 hardware and firmware.
- Bluetooth Low Energy protocol and binary frame design.
- PC-side Python receiving, recording, visualization, and offline analysis.
- Android BLE capture, live visualization, post-capture processing, and embedded Python execution.
- Shared `emg_util` algorithms reused across PC, Android, and cloud/Colab workflows.

The primary use case is tennis swing and fatigue analysis. The system captures forearm muscle activation, arm motion, vitals, and battery telemetry, then supports both real-time feedback and research-grade post-session analysis.

---

## 2. End-to-End Architecture

### 2.1 Data Flow Summary

```text
[Hardware Sensors]
  MyoWare EMG RAW/ENV
  ICM-20948 IMU
  MAX30105 SpO2/HR
  MAX17048 Battery
        |
        v
[ESP32 Arduino Firmware: myoware_imu_v2]
  ADC DMA EMG sampling
  IMU/vitals/battery acquisition
  timestamp correction
  TLV binary frame encoder
        |
        v
[BLE Nordic UART Service]
  binary frames over NUS TX notify
  PING/keepalive over NUS RX write
        |
        +-------------------------------+
        |                               |
        v                               v
[PC Python Host]                 [Android Host App]
  btCentral.py                    SessionCaptureActivity.java
  CSV recorder                    frames_*.bin raw recording
  UDP mirror                      live Java plots
  sensordata_plotter.py           realtime_bridge.py / Chaquopy
        |                               |
        +---------------+---------------+
                        |
                        v
[Analysis Layer: emg_util]
  shared fatigue_monitor.py
  emg_util.py on PC/cloud
  emg_util_nopandas.py on Android
  YAML runner / Colab notebook
```

### 2.2 Functional Tiers

| Tier | Purpose | Main Components |
|---|---|---|
| Tier 1 | Sensor acquisition and BLE streaming | MyoWare hardware, ESP32 firmware, binary TLV protocol |
| Tier 2 | Host recording and live feedback | PC `btCentral.py`, `sensordata_plotter.py`, Android capture UI |
| Tier 3 | Post-processing and deeper analysis | `emg_util`, Android Python bridge, PC YAML runner, Colab notebook |
| Cross-cutting | Algorithm reuse and consistency | Git submodule, no-pandas mobile implementation, regression tests |

---

## 3. Repositories and Component Ownership

| Workspace | Role |
|---|---|
| `/local/mnt/workspace/wangx/projects/arduino/myoware_imu_v2` | Arduino/ESP32 firmware and hardware documentation |
| `/local/mnt/workspace/wangx/projects/arduino/py_scripts` | PC-side BLE receiver, protocol documentation, CSV logging, UDP/live plotting |
| `/local/mnt/workspace/wangx/projects/btLeApp/app` | Android app, Java BLE/UI/session logic, Android Python integration |
| `/local/mnt/workspace/wangx/projects/emg_util` | Canonical signal-processing and tennis-analysis algorithms |
| `/local/mnt/workspace/wangx/projects/btLeApp/FastBleLib` | Android BLE support library used by the app |

`emg_util` is the algorithm source of truth. Android should reuse it directly through a submodule or package-style integration rather than duplicating algorithms manually.

---

## 4. Hardware Layer

### 4.1 Wearable Sensor Hardware

The wearable node combines:

- **ESP32 module**
  - BLE radio.
  - Dual-core FreeRTOS execution.
  - ADC1 channels for EMG.
  - I2C bus for IMU, vitals, and battery monitor.

- **MyoWare 2.0 EMG sensor**
  - `RAW`: high-frequency AC EMG after analog front-end bandpass filtering.
  - `ENV`: hardware rectified/smoothed envelope.
  - `REF`: reference electrode, physically important for signal quality even if not digitally logged.

- **ICM-20948 IMU**
  - 3-axis accelerometer.
  - 3-axis gyroscope.
  - Used for swing motion, activity gating, and real-time swing triggering.

- **MAX30105**
  - SpO2 and heart-rate measurement.
  - Slow telemetry, not primary real-time fatigue input.

- **MAX17048**
  - Battery voltage and percentage telemetry.

### 4.2 EMG Hardware Signal Quality Considerations

The EMG fatigue pipeline depends on a valid `RAW` signal, not only `ENV`.

Important design observations:

- `ENV` is useful for live signal-quality visualization and amplitude trend checking.
- Frequency-domain fatigue metrics such as MDF and MNF require `RAW`.
- If the RAW pogo-pin or jumper connection fails, the ADC may read a floating or ghost signal.
- A disconnected RAW channel can appear as a weak, smoothed signal correlated with `ENV`, but it will fail high-pass preprocessing and produce invalid MDF/RMS results.
- Correct RAW wiring to ESP32 ADC GPIO 32 / ADC1 channel 4 is critical.

### 4.3 Electrode Placement

The system assumes forearm EMG placement for tennis-related wrist/forearm muscle activation.

Typical placement:

- MID and END electrodes over the target forearm flexor muscle region.
- REF electrode over a relatively electrically neutral bony landmark such as the lateral epicondyle region.
- Reference placement affects common-mode rejection and therefore downstream feature reliability.

---

## 5. ESP32 / Arduino Firmware Design

### 5.1 Firmware Responsibilities

The firmware in `myoware_imu_v2` is responsible for:

1. Sampling EMG, IMU, vitals, and battery data.
2. Timestamping samples close to capture time.
3. Buffering data in static ring buffers.
4. Encoding batches into compact binary TLV payloads.
5. Framing payloads with sequence numbers and CRC.
6. Streaming frames over BLE NUS.
7. Responding to host keepalive behavior.

### 5.2 Sampling Strategy

| Signal | Typical Rate | Firmware Mechanism | Notes |
|---|---:|---|---|
| EMG RAW/ENV | 2 kHz output | ADC DMA with oversampling | Highest-priority data path |
| IMU accel/gyro | 200 Hz | Timer/task + I2C read | Used for motion and swing detection |
| SpO2/HR | Slow, ~30 s update | Background task | Optional physiological context |
| Battery | Slow, cached | I2C read | Logged in vitals telemetry |

### 5.3 Firmware Architecture

The ESP32 firmware uses:

- ADC DMA to reduce jitter and CPU load.
- Static ring buffers for deterministic memory behavior.
- FreeRTOS tasks for EMG drain, IMU acquisition, and SpO2 processing.
- Atomic flags, spinlocks, and mutexes for synchronization.
- Backpressure rules to prioritize high-rate EMG when BLE bandwidth or buffers are constrained.
- Host-gated sampling to pause/recover when the host disconnects or stops sending keepalive PINGs.

### 5.4 Timestamping

The firmware emits a 32-bit microsecond timestamp in each frame. Batch TLVs include offsets from the frame timestamp, allowing the host to reconstruct per-sample timestamps:

```text
sample_t_us = frame_t_us + t0_offset + i * sample_period_us
```

This avoids sending a full timestamp for every sample while preserving precise timing.

---

## 6. Bluetooth Protocol Design

### 6.1 BLE Transport

The system uses Nordic UART Service (NUS):

| UUID | Role |
|---|---|
| `6E400001-B5A3-F393-E0A9-E50E24DCCA9E` | Service |
| `6E400003-B5A3-F393-E0A9-E50E24DCCA9E` | TX notify, device to host |
| `6E400002-B5A3-F393-E0A9-E50E24DCCA9E` | RX write, host to device |

Host-to-device commands include:

- `PING`: periodic keepalive.
- Optional ACK-style commands if needed by future protocol versions.

### 6.2 Binary Frame Format

Each device-to-host frame contains:

```text
magic0, magic1       0xA5, 0x5A
proto_ver            protocol version, current v2
flags                CRC and metadata flags
frame_seq            monotonically increasing frame sequence
frame_t_us           32-bit device timestamp
payload_len          TLV payload length
payload              one or more TLV records
crc16                CRC-CCITT over header + payload
```

### 6.3 TLV Payloads

The protocol is extensible through Type-Length-Value records.

| TLV | Meaning |
|---|---|
| `0x01` | EMG batch |
| `0x02` | IMU batch |
| `0x03` | Vitals/battery |

EMG batch contents include:

- First EMG sequence number.
- Timestamp offset from frame time.
- Sample rate.
- Channel mask/count.
- Interleaved `ENV`, `RAW`, optional `REF`.

IMU batch contents include:

- First IMU sequence number.
- Timestamp offset.
- Sample rate.
- Axis mask.
- Accelerometer and gyroscope full-scale metadata.
- Batched raw int16 accel/gyro samples.

Vitals include:

- SpO2.
- Heart rate.
- Age of computation.
- Validity flags.
- LED brightness.
- Battery percentage and voltage.

### 6.4 Protocol Design Goals

The protocol is designed to be:

- Compact enough for BLE throughput limits.
- Self-describing enough for host-side scaling and decoding.
- Robust against corruption via magic bytes and CRC16.
- Forward-compatible through TLV records and protocol version flags.
- Suitable for both PC and Android receivers.

---

## 7. PC Python Host Side

### 7.1 `btCentral.py`: BLE Receiver and Recorder

`btCentral.py` is the primary PC-side acquisition program.

Responsibilities:

- Scan/connect to the ESP32 BLE device.
- Subscribe to NUS TX notifications.
- Send periodic `PING` messages over NUS RX.
- Parse binary frames and validate CRC.
- Decode EMG, IMU, vitals, and battery TLVs.
- Extend 32-bit device timestamps to 64-bit monotonic timestamps.
- Write EMG and IMU to rotating CSV logs.
- Write vitals/battery to append-style CSV.
- Maintain health metrics and reconnect on stalls.

### 7.2 PC Recording Output

The PC recorder produces files such as:

```text
logs/
  emg_log_<session_id>_<open_id>_<idx>.csv
  emg_log_<session_id>_<open_id>_<idx>.meta.json
  imu_log_<session_id>_<open_id>_<idx>.csv
  imu_log_<session_id>_<open_id>_<idx>.meta.json
  vitals_log.csv
```

Rotation is a file-management mechanism, not a session boundary. A single recording session may contain multiple numbered segments.

### 7.3 UDP Mirror for Live Visualization

When enabled, `btCentral.py` mirrors decimated data over UDP as JSON:

- RAW EMG samples.
- ENV EMG samples.
- IMU magnitude samples.
- Vitals and battery.
- EMG metadata.

UDP is best-effort and non-blocking. CSV logging remains the source of truth.

### 7.4 `sensordata_plotter.py`: PC Visualization

The plotter consumes UDP JSON and provides:

- Rolling EMG RAW/ENV plots.
- IMU magnitude visualization.
- Optional local software envelope from `abs(raw)`.
- Optional real-time fatigue monitor integration.
- Offline CSV viewing for previously recorded logs.

The plotter is intentionally decoupled from BLE so that acquisition remains robust even if visualization drops packets or lags.

---

## 8. Android Application Side

### 8.1 Android Capture Architecture

The Android app provides mobile capture and feedback.

Main roles:

- BLE scan/connect/MTU negotiation.
- Notification subscription and binary frame collection.
- Real-time decode for UI plots.
- Raw binary session persistence to `frames_*.bin`.
- Live swing counting and fatigue display.
- Post-capture processing through Java and Python components.

Key Java-side classes include:

| Class | Purpose |
|---|---|
| `MainActivity.java` | BLE device scanning and connection |
| `SessionCaptureActivity.java` | Real-time capture, decode, plotting, swing detection |
| `ProcessingActivity.java` | Post-session decode and analysis flow |
| `EmgProcessor.java` | Pure Java EMG processing path |
| `SimplePlotView.java` / `RingBufferF.java` | Real-time plotting support |

### 8.2 Android Raw Session Format

Android records binary frames directly to files such as:

```text
frames_YYYYMMDD_HHMMSS.bin
```

This preserves the original BLE protocol stream and allows later decoding without loss of protocol detail.

### 8.3 Android Real-Time Analysis

During capture, Android uses lightweight algorithms:

- Gyroscope magnitude peak detection for swing count.
- Debounce logic to avoid double-counting backswing/forward swing.
- Real-time plot buffers for EMG and IMU.
- Optional fatigue computation via Chaquopy bridge and shared Python code.
- Java-side feature extraction for RMS, MNF, MDF, entropy, and other metrics where needed.

### 8.4 Android Python Integration

Android uses Chaquopy to run Python code inside the app.

Important Python-side files:

| File | Purpose |
|---|---|
| `realtime_bridge.py` | Bridge from Java real-time events to Python fatigue monitor |
| `offline_runner.py` | Post-capture session processing entry point |
| `btcentral_offline_decode.py` | Decodes binary `frames_*.bin` into CSV-equivalent streams |
| `analysis_bridge.py` | Legacy or auxiliary bridge for analysis calls |
| `emg_util_nopandas.py` | Android-compatible subset of `emg_util` |
| `fatigue_monitor.py` | Shared real-time fatigue monitor |

Android avoids heavy dependencies such as pandas where possible, so `emg_util_nopandas.py` uses dicts/lists/numpy arrays instead of pandas DataFrames.

---

## 9. Core Analysis Layer: `emg_util`

### 9.1 Role of `emg_util`

`emg_util` is the canonical implementation of the core signal-processing and tennis-analysis algorithms.

It supports:

- PC offline analysis.
- Android post-capture analysis.
- Android/PC real-time fatigue monitoring.
- Cloud/Colab notebook workflows.
- Regression tests validating algorithm consistency.

### 9.2 Core Signal Processing

Common EMG processing steps include:

1. Load EMG/IMU/vitals data.
2. Validate RAW signal quality.
3. Detrend / remove DC offset.
4. Apply bandpass filtering for EMG.
5. Apply notch filtering for power-line interference.
6. Compute envelope when needed.
7. Segment windows around swings or activity bouts.
8. Extract time-domain and frequency-domain features.

Core features include:

| Feature | Purpose |
|---|---|
| RMS | Muscle activation amplitude |
| MAV | Mean absolute value |
| WL | Waveform length |
| ZC | Zero crossings |
| SSC | Slope sign changes |
| MNF | Mean frequency |
| MDF | Median frequency, fatigue indicator |
| Wavelet entropy | Complexity/frequency structure |
| Sample entropy | Signal regularity |

### 9.3 Swing and Activity Analysis

The system uses two complementary swing detection philosophies:

#### Real-time gyro-based detection

Used by:

- Android live session UI.
- PC live plotter/fatigue monitor.

Properties:

- Fast and low-latency.
- Based on gyroscope magnitude threshold and peak tracking.
- Good for live swing counting and immediate feedback.
- Less computationally expensive.

#### Offline EMG/IMU-based detection

Used by:

- PC offline analysis.
- Cloud/Colab analysis.
- Android post-capture workflows where appropriate.

Properties:

- More accurate and more configurable.
- Can use EMG envelope, IMU activity, and session context.
- Can inspect data before and after the event.
- Better suited to research-grade fatigue trends.

### 9.4 Fatigue Analysis

Fatigue analysis is based primarily on spectral changes in EMG, especially MDF decline.

Typical pipeline:

1. Detect swings or active bouts.
2. Extract EMG windows around each swing.
3. Preprocess RAW EMG.
4. Compute MDF/MNF and amplitude features.
5. Select baseline swings after warm-up.
6. Apply RMS quality filtering to avoid noise-dominated baseline swings.
7. Compute baseline from robust high-quality early swings.
8. Report deltas:
   - MDF drop percentage.
   - RMS increase percentage.
   - Acceleration or activity changes.
9. Identify fatigue onset or fatigue level.

### 9.5 Baseline Protection

Baseline quality is critical. The design includes:

- Warm-up skip to avoid early setup/noise periods.
- Baseline swing count configuration, commonly 20 swings.
- RMS quality filter using session P90 RMS.
- 75th-percentile MDF baseline to represent fresh high-quality muscle activation.
- Fallback logic when too few baseline candidates remain.

---

## 10. Colab and Cloud Analysis

### 10.1 Purpose of Colab Workflow

The Colab workflow supports portable, shareable, research-grade analysis without requiring a local PC environment.

Typical use cases:

- Upload CSV logs exported from PC or Android.
- Run the same `emg_util` algorithms in a notebook.
- Generate plots for fatigue trends, swing features, and activity periods.
- Share reproducible analysis with collaborators.
- Prepare figures/tables for reports, papers, IRB documents, or patent drafts.

### 10.2 Relationship to PC Offline Analysis

Colab should not define a separate algorithm. It should reuse the same core logic as PC offline analysis:

```text
PC YAML runner  ─┐
                 ├── shared emg_util algorithms
Colab notebook ──┘
```

The notebook may differ in UI and plotting style, but algorithmic steps and default parameters should remain consistent.

### 10.3 Data Inputs

Colab can consume:

- PC `btCentral.py` CSV files.
- Android-decoded CSV files generated from `frames_*.bin`.
- Session metadata and YAML-like configuration.
- Optional annotated swing labels or manual event markers.

---

## 11. Implementation Reuse and Algorithm Consistency

### 11.1 Single Source of Truth

The intended reuse model is:

```text
emg_util/
  fatigue_monitor.py       shared real-time fatigue and preprocessing
  emg_util.py              full PC/cloud implementation, pandas-based
  emg_util_nopandas.py     Android-compatible implementation
  emg_util_yaml_runner.py  PC batch/session runner
  tennis_analysis_cloud.ipynb or Colab notebook
```

Android imports the shared code through a Git submodule or equivalent version-pinned packaging approach.

### 11.2 Shared Algorithms

The following algorithmic pieces should remain consistent across PC, Android, and Colab:

| Algorithm / Parameter | PC | Android | Colab |
|---|---|---|---|
| EMG preprocessing | `fatigue_monitor.py` / `emg_util.py` | `fatigue_monitor.py` / `emg_util_nopandas.py` | `emg_util` |
| Bandpass / notch settings | yes | yes | yes |
| Envelope computation | yes | yes | yes |
| MDF/MNF computation | yes | yes | yes |
| RMS/MAV/WL/ZC/SSC features | yes | yes | yes |
| Swing window extraction | yes | yes, no-pandas | yes |
| Baseline swing selection | yes | yes | yes |
| RMS baseline quality filter | yes | yes | yes |
| Baseline delta formulas | yes | yes | yes |

### 11.3 Differences by Design

Some differences are intentional.

| Area | PC / Colab | Android |
|---|---|---|
| Data structures | pandas DataFrames | dict/list/numpy arrays |
| Visualization | matplotlib/notebook plots | Android custom views |
| Dependencies | pandas/scipy/matplotlib allowed | avoid pandas; minimize APK size |
| Processing time | offline, can be slow | constrained by phone CPU/battery |
| UI | CLI/YAML/notebook | Java/Kotlin activities and views |

### 11.4 Reuse Strategy

Preferred workflow:

1. Implement or update algorithm in `emg_util`.
2. Add or update regression tests.
3. Verify PC results.
4. Verify Android no-pandas equivalent.
5. Update Android submodule reference.
6. Verify Android bridge tests.
7. Use same code in Colab notebook.

This avoids manually maintaining divergent implementations.

---

## 12. Post-Processing Workflows

### 12.1 PC Recording to PC Analysis

```text
btCentral.py
  -> emg_log_*.csv / imu_log_*.csv / vitals_log.csv
  -> emg_util_yaml_runner.py
  -> swing features, fatigue trends, plots, summaries
```

This is the most direct workflow for research-grade analysis.

### 12.2 Android Recording to Android Decode

```text
SessionCaptureActivity.java
  -> frames_*.bin
  -> offline_runner.py
  -> btcentral_offline_decode.py
  -> decoded CSV-equivalent data
  -> optional on-device summary
```

This supports capture in the field without a PC.

### 12.3 Android Recording to PC/Colab Analysis

```text
Android frames_*.bin
  -> Android decode to CSV
  -> transfer CSV to PC or Colab
  -> emg_util analysis
```

This workflow combines mobile capture with full offline analysis.

### 12.4 PC Live Monitoring

```text
btCentral.py --udp-enable
  -> UDP JSON
  -> sensordata_plotter.py
  -> live EMG/IMU visualization
  -> optional fatigue_monitor.py
```

This is useful for sensor placement verification and live data-quality monitoring.

---

## 13. Testing and Validation

### 13.1 Protocol Validation

Validate:

- BLE connection and MTU negotiation.
- Magic bytes and frame resynchronization.
- CRC16 correctness.
- TLV length correctness.
- Timestamp monotonicity and wrap handling.
- Frame sequence gaps.

### 13.2 Hardware Validation

Validate:

- RAW EMG rests near the expected ADC midpoint.
- RAW shows high-frequency AC bursts during contraction.
- ENV rises with muscle activation.
- RAW is not merely a ghost of ENV.
- IMU does not saturate for expected tennis motion.
- Battery/vitals fields are decoded correctly.

### 13.3 Algorithm Regression Tests

Regression testing should cover:

- EMG preprocessing.
- MDF/MNF computation.
- Classic feature extraction.
- Swing detection.
- Baseline selection.
- RMS baseline quality filter.
- Android no-pandas equivalence.
- Android bridge calls and default parameters.

### 13.4 Cross-Platform Equivalence

For the same decoded session data:

- PC `emg_util.py`.
- Android `emg_util_nopandas.py`.
- Colab notebook.

should produce matching or intentionally explainable results for key metrics such as swing count, MDF, RMS, baseline values, and fatigue deltas.

---

## 14. Design Principles

1. **Raw data first:** Preserve raw binary or CSV logs as the source of truth.
2. **Protocol stability:** Keep BLE frame format documented and backward-compatible.
3. **Real-time and offline are different:** Use fast gyro detection for live feedback, deeper EMG/IMU analysis offline.
4. **Shared algorithms:** Keep core EMG/fatigue logic in `emg_util`.
5. **Android constraints are real:** Avoid unnecessary heavy dependencies in mobile Python.
6. **Quality gates matter:** Detect hardware signal issues before trusting fatigue metrics.
7. **Reproducibility:** PC, Android, and Colab should use the same algorithm defaults where possible.
8. **Test before changing defaults:** Any parameter or algorithm update should include regression coverage.

---

## 15. Key Reference Documents

| Document | Purpose |
|---|---|
| `arduino/py_scripts/PROTOCOL.md` | Authoritative BLE protocol and PC recording design |
| `arduino/py_scripts/SYSTEM_HIGH_LEVEL_DESIGN.md` | End-to-end PC-side architecture overview |
| `arduino/myoware_imu_v2/HIGH_LEVEL_DESIGN.md` | Firmware design and ESP32 task/data-flow details |
| `arduino/myoware_imu_v2/HARDWARE.md` | Sensor wiring, electrode placement, RAW/ENV hardware notes |
| `btLeApp/app/APP_HLD.md` | Android app architecture |
| `btLeApp/app/INTEGRATION_SUMMARY.md` | Android Java EMG processor integration |
| `btLeApp/app/src/main/python/ANDROID_HLD.md` | Android Python, Chaquopy, submodule, and three-tier analysis design |
| `btLeApp/app/src/main/python/REGRESSION_TEST.md` | Android Python regression strategy |
| `emg_util/HIGH_LEVEL_DESIGN.md` | Analysis-library-focused HLD |
| `emg_util/HLD_Project.md` | This cross-component project HLD |