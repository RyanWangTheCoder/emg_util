# Paper 2: System Design Paper

**Status:** Planning — write after Paper 1 is submitted  
**Target:** IEEE Body Sensor Networks (BSN) or MDPI Sensors  
**Format:** 6-page conference paper or 8-page journal short paper  
**Depends on:** Paper 1 accepted/submitted (use Paper 1 data as field validation section)  
**Last Updated:** 2026-05-02

---

## Working Title

*"A Low-Cost BLE Wearable System for Real-Time EMG-IMU Acquisition: Firmware Design, Robust Capture Pipeline, and Tennis Field Validation"*

Alternative titles:
- *"End-to-End Design of a $99 EMG-IMU Wearable for Sports Field Deployment: Firmware, Protocol, and Dual-Platform Analysis"*
- *"From Sensor to Insight: A Field-Deployable ESP32 BLE System for Tennis EMG-IMU Monitoring"*

---

## Why This Is a Separate Paper

Paper 1 focuses on what we *found* (electrode settling, IMU quality validation). Paper 2 focuses on what we *built* and the engineering decisions that made robust field data collection possible. The system work constitutes a genuine contribution for the practitioner/builder audience:

1. Most published wearable EMG systems are laboratory prototypes or commercial products -- few document the specific engineering decisions, failure modes, and robustness fixes required for unattended field deployment.
2. The hybrid `abs_us` timeline stitching solves a problem every BLE logger eventually hits (BLE dropout vs. device reset produce different timestamp discontinuities) with a clean, general solution.
3. The pogo-pin failure mode and ADC crosstalk ghost signal are not documented anywhere -- practitioners building similar systems will encounter this exact failure and need this diagnosis.
4. The dual-platform design (same algorithm on PC and Android via Chaquopy) is an uncommon pattern that demonstrates practical portability of scipy/numpy signal processing to mobile.
5. The firmware architecture (DMA-driven ADC, FreeRTOS dual-core, host watchdog) achieves zero sample loss in production across 150+ minutes of field sessions -- a reliability claim worth documenting.

---

## Core Contributions

1. **Firmware architecture:** Dual-core ESP32 design with hardware DMA ADC at 40 kHz (10x oversampling to 2 kHz), per-sample timestamp back-calculation achieving +-25 us accuracy, and host-gated sampling watchdog (pause at 12s, reboot at 30s) for power efficiency and BLE recovery.

2. **BLE protocol:** Compact binary TLV framing with CRC16, self-describing IMU FSR codes embedded per-frame (enabling FSR changes without host-side reconfiguration), and 32-bit device clock extension to 64-bit monotonic timestamp.

3. **Robust capture pipeline:** Async BLE central with FrameParser re-sync on MAGIC bytes, rotating CSV logs with metadata, exponential-backoff reconnection, and optional UDP mirror for real-time visualisation -- zero data loss across 6 BLE reconnections in field sessions.

4. **Hybrid `abs_us` timeline stitching:** Two-case BLE reconnection handler: BLE-dropout-only (device clock continues, host_rx_ms gap used for inter-connection interval) vs. ESP32-reset (device clock restarts, same host_rx_ms gap approach). Unifies both cases without detecting which occurred. Enables the cross-session gap artifact analysis in Paper 1.

5. **Dual-platform analysis pipeline:** Same FatigueMonitor and signal processing algorithm running on PC (pandas, scipy) and Android (Chaquopy, pandas-free). Fatigue results match across platforms. Demonstrates that scipy/numpy-based MDF computation is viable on mid-range Android devices (~25-70 ms per swing).

6. **Field validation:** System deployed across 2 tennis sessions totalling 150+ minutes, 823 swings, 6 BLE reconnections. Zero sample drops, <0.01% CRC error rate. Electrode settling artifact and genuine fatigue detected (Paper 1 results), confirming pipeline fidelity.

**Unique practical contribution:** The RAW signal pogo-pin failure diagnosis -- ADC multiplexer charge sharing produces a ghost signal (r = 0.998 with ENV) that survives visual inspection but is eliminated by preprocessing, leaving a flatline. Documented with root cause, diagnostic test, and permanent fix.

---

## Target Venue

**Primary:** IEEE Body Sensor Networks (BSN) -- systems track, highly relevant audience  
**Alternative:** MDPI Sensors (open access, good fit for engineering systems papers)  
**Secondary:** IEEE Journal of Biomedical and Health Informatics (JBHI) -- if expanded to journal format  
**Format:** 6 pages (BSN) or 8 pages (MDPI journal short communication)

---

## Paper Structure (Proposed)

**Total target: ~3000 words body text** (6 pages with figures and references)

### 1. Introduction (~300 words)
- Motivation: wearable EMG-IMU for sports field deployment
- Challenge: lab-grade systems are expensive ($5k-$30k); hobbyist systems lack robustness (BLE dropout, timestamp errors, motion artifacts); neither is documented for unattended 60-90 min field sessions
- Gap: engineering decisions for robust field BLE wearables are under-documented; most papers publish results, not the system failures and fixes that made results possible
- Contributions: list 6 from Core Contributions above

### 2. Related Work (~250 words)
- Commercial wearable EMG: Delsys Trigno, Noraxon -- gold standard but $5k-$30k; inaccessible for field/youth sport
- Low-cost wearable EMG systems: Cerone et al. 2019 (modular HD-sEMG), Lynn et al. 2018 (Athos validation), Yang et al. 2024 (e-textiles) -- focus on electrode design, not capture pipeline robustness
- IMU-EMG fusion platforms: Taborri et al. 2020 (overview), MultiSenseBadminton 2024 -- focus on data collection, not protocol/firmware engineering
- BLE wearable systems: most papers describe data collected, not the firmware/protocol that collected it; reconnection robustness, timestamp accuracy, and multi-session stitching are rarely documented
- **Gap:** No published work documents the full stack from firmware DMA design through BLE protocol to analysis pipeline with field-validated reliability metrics.

### 3. Hardware Design (~300 words)
- Component selection rationale: MyoWare 2.0 (dual output ENV+RAW), ICM-20948 (6-axis, configurable FSR), ESP32 WROOM-32E (dual-core, BLE, ADC DMA)
- Total system cost: ~$99 (itemised BOM table)
- Critical hardware failure and fix: RAW pogo-pin failure, ADC crosstalk ghost signal diagnosis, GPIO 32 direct solder bypass
- EMG pin mapping: PIN_ENV = GPIO 39 (ADC1 ch3), PIN_RAW = GPIO 32 (ADC1 ch4) -- NOT the "A4" silk label (GPIO 21, I2C SDA, no ADC)
- IMU FSR history: 250 dps saturated every hard swing; raised to 1000 then 2000 dps; acc 2g -> 8g. FSR codes self-documenting in every TLV frame.

### 4. Firmware Architecture (~400 words)
- Dual-core split: Core 0 (BLE TX, host watchdog, LED), Core 1 (emgDrainTask prio 2, imuTask prio 2, spo2Task prio 0)
- ADC DMA design: 40 kHz continuous (2 channels interleaved), 10x decimation to 2 kHz, per-sample timestamp back-calculation (frameEndUs - age_us), +-25 us accuracy
- Synchronisation: spinlocks for ring buffers (<10 instructions), FreeRTOS mutex for I2C bus, atomics for cross-core flags
- Host watchdog state machine: PING every 1s -> pause sampling at 12s -> reboot at 30s; saves ~40 mA when host absent
- Power budget: ~148 mA active, ~5 mA standby; ~3-4 hours battery life at 500 mAh

### 5. BLE Protocol (~300 words)
- Frame structure: magic 0xA5 0x5A, 14-byte header (ver, flags, frame_seq u32, frame_t_us u32, payload_len u16), TLV payload, CRC16-CCITT
- TLV types: EMG_BATCH (0x01), IMU_BATCH (0x02), VITALS (0x03)
- IMU batch design: acc_fsr_code + gyro_fsr_code in every frame (self-describing, supports dynamic FSR changes without protocol bump)
- Timestamp design: t0_offset from frame timestamp, per-sample reconstruction; 32-bit clock wraps at 71.6 min, host extends to 64-bit via wrap detection
- Why binary TLV over JSON/CSV: 4-8x bandwidth reduction (12 bytes vs. ~60 bytes per IMU sample); CRC16 detects corruption; extensible without breaking old decoders
- Protocol version history: v1 (no FSR metadata) -> v2 (FSR codes + battery); host handles both

### 6. Host Capture Pipeline (~300 words)
- Architecture: async BLE (Bleak) -> asyncio queue (20k chunks) -> FrameParser -> consumer task -> CSV writer task
- FrameParser: MAGIC re-sync, CRC16 validation, TLV decode; drops malformed frames without stalling
- Rotating CSV files: emg_log_<session_id>_<open_id>_<idx>.csv, 30-min segments; metadata in .meta.json; atomic write (tmp file + rename)
- Watchdog/reconnect: stall detection at 5s (no notify), resubscribe attempt, then reconnect with exponential backoff (0.5s -> 20s max); no data loss on reconnect
- UDP mirror: optional, non-blocking, best-effort; never delays CSV writes; decimated to 500/50/50 Hz for RAW/ENV/IMU

### 7. Software Analysis Pipeline (~350 words)
- Signal processing: detrend -> bandpass(50-450 Hz) -> notch(60, 120 Hz) -> Welch PSD (nperseg=1024) -> MDF/MNF
- Why 50 Hz low cutoff (not 20 Hz): rejects motion artifact in 20-50 Hz band; MyoWare hardware already bandpasses at 20-500 Hz; 20-50 Hz contains little useful fatigue information for surface EMG
- Swing detection: fixed 300 dps threshold (replaces z-score; justified from p88 of session distribution), 2000 ms debounce
- Baseline protection: 3-layer (5-min warmup skip + RMS quality filter at 0.25 x p90 + 75th percentile for baseline MDF)
- Hybrid abs_us stitching: within-connection uses dev_us (accurate physical time); between-connections uses host_rx_ms gap (handles both BLE-dropout and ESP32-reset cases). Enables cross-session analysis and gap detection.
- Dual-platform: FatigueMonitor in fatigue_monitor.py (pandas-free, scipy-optional) runs identically on PC and Android via Chaquopy; ~25-70 ms per swing on mid-range Android

### 8. Field Validation (~300 words)
- Two sessions: log0303 (87.9 min, 197 swings, 2 BLE connections), log0305 (63.1 min, 626 swings, 1 connection)
- Reliability metrics: zero sample drops (verified by sequence number continuity), CRC error rate <0.01%, 6 BLE reconnections handled without data loss
- Timestamp accuracy: abs_us stitching correctly reconstructs 66-min reconnection gap in log0303 (verified against host_rx_ms reference)
- IMU FSR self-description: gyro FSR upgrade (250->1000->2000 dps across sessions) handled automatically by host parser without code changes
- Scientific output: see Paper 1 for full findings; system pipeline produced validated electrode settling and fatigue results, confirming end-to-end data fidelity

### 9. Discussion (~250 words)
- The pogo-pin failure and ghost signal are likely encountered by many builders of similar systems; documenting it saves future practitioners hours of debugging
- The abs_us stitching approach is general -- any BLE logger with dev_us + host_rx_ms columns can apply the same two-case reconstruction
- Dual-platform design trade-off: Python on Android via Chaquopy is ~2-6s cold-start but <70 ms per swing thereafter; acceptable for post-trigger fatigue analysis (not per-sample)
- Limitations: single sport; BLE throughput near capacity (2 kHz EMG + 200 Hz IMU); adding more sensors requires rate reduction; GPS/outdoor use untested

### 10. Conclusion (~150 words)
- We present a complete, open-source, $99 EMG-IMU wearable system validated across 150 min of field tennis
- Key contributions: DMA-driven firmware, self-describing BLE protocol, hybrid timeline stitching, dual-platform fatigue pipeline
- The pogo-pin ghost signal diagnosis and abs_us stitching are practical contributions that generalise beyond tennis or EMG
- System is open and reproducible; all code and hardware schematics available at [repo]

---

## Figures Needed

| # | Figure | Content |
|---|--------|---------|
| 1 | System block diagram | Sensor -> firmware -> BLE -> btCentral -> CSV -> analysis -> results |
| 2 | Firmware dual-core architecture | Core 0/1 split, task priorities, ring buffers, synchronisation |
| 3 | Binary frame structure | TLV layout with field sizes (visual) |
| 4 | Ghost signal diagnosis | RAW vs ENV plot showing ghost (r=0.998) and flatline after preprocessing |
| 5 | abs_us stitching diagram | Two BLE connections with gap, showing dev_us vs host_rx_ms vs abs_us reconstruction |
| 6 | Android Chaquopy latency breakdown | Per-swing timing: JNI + filtfilt + Welch = 25-70 ms |
| 7 | Field validation: session timeline | Frame count, CRC errors, reconnection events over session duration |

---

## Tables Needed

| # | Table | Content |
|---|-------|---------|
| 1 | Hardware BOM | Component, part number, cost (~$99 total) |
| 2 | Protocol comparison | Binary TLV vs JSON vs CSV: bytes/sample, parse overhead, extensibility |
| 3 | IMU FSR history | Session, FSR setting, saturation events, scale factor |
| 4 | Field validation metrics | Sessions, duration, swings, BLE reconnections, CRC errors, sample drops |

---

## Relationship to Paper 1

| Aspect | Paper 1 | Paper 2 |
|--------|---------|---------|
| Primary contribution | Electrode settling characterisation + IMU quality validation | System design + engineering + field robustness |
| Data used | log0303, log0305 | Same sessions (as field validation) |
| Reader | Biomedical / sports science | Embedded systems / wearable engineering |
| Venue | EMBC (student/biomedical track) | BSN / MDPI Sensors (systems track) |
| Status | Write first | Write after Paper 1 submitted |

Paper 2 cites Paper 1 for the scientific findings. Paper 1 cites the system (brief description, ~500 words) but does not claim system design as a contribution.

---

## Next Steps

1. [ ] Submit Paper 1 first
2. [ ] Write Paper 2 draft after Paper 1 submission (estimated: 3 months from now)
3. [ ] Generate Figure 4 (ghost signal diagnosis) -- raw data available in log0303 early captures
4. [ ] Generate Figure 5 (abs_us stitching diagram) -- illustrate the two-case reconstruction
5. [ ] Write firmware architecture section (draw from `myoware_imu_v2/HIGH_LEVEL_DESIGN.md`)
6. [ ] Write protocol section (draw from `py_scripts/PROTOCOL.md`)
7. [ ] Write pipeline section (draw from `emg_util/HIGH_LEVEL_DESIGN.md` and `SYSTEM_HIGH_LEVEL_DESIGN.md`)
8. [ ] Prepare hardware BOM table with actual part numbers and costs
9. [ ] Open-source the firmware and Python pipeline (GitHub repo) before submission

---

## Appendix E Algorithms (Moved from paper_plan.md 2026-05-10)

> All E-series algorithms below are PAPER 2 / FUTURE WORK. None are validated Paper 1 contributions.

### E1. Forearm-Only Impact-Risk Gating
v1 DONE 2026-05-03 (sample masking, mean shift 0.12 Hz — insufficient).
v2 BLOCKED: Experiment 10 null result — acc_dyn finds swing apex not ball contact.
Requires Level 1 racket tap test before revisiting.

### E2. Noise Floor Tracker
Implemented as Experiment 6 (paper_figures.py, fig9_rest_noise_floor.png). Sliding-window IMU-quiet scan. Useful corroborating evidence; Paper 1 appendix.

### E5. Pre-Impact Phase MDF
BLOCKED pending valid impact trigger (see Experiment 10 null result).

### E7. IMU-Gated Acoustic Impact Labeling
Validation tool. Blocked by Experiment 10. Revisit after Level 1 racket tap.

### E8 Validation Protocol Status
Level 0 (Exp 10): ✅ DONE — null result, acc_dyn not a valid trigger
Levels 1-5: ☐ Not done

### Impedance Measurement
Near-term: handheld LCR meter at t=0,5,10,15,20,30 min during one session.
Paper 2: AD5933 chip on ESP32 I2C bus for automatic impedance logging.

---

## Paper 1 Scope Boundary (what NOT to include in CNIB submission)

- Firmware architecture internals (dual-core, mutex details) — Paper 2
- Android/Chaquopy implementation — Paper 2
- Detailed BLE protocol (TLV format, CRC) — one sentence in Paper 1 max
- Pogo-pin ghost signal — one sentence for signal validity in Paper 1 max
- E-series impact-gating algorithms — one future-work sentence in Paper 1 max
- Audio/acoustic validation (E7) — Paper 2 or future
- Adaptive settling endpoint (Exp 9 null result) — one future-work sentence in Paper 1
