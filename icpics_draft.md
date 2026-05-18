---
output:
  pdf_document:
    pandoc_args: ["--pdf-engine=xelatex"]
keywords: "wearable, EMG, IMU, BLE, ESP32, DMA, real-time, biosignal"
header-includes:
  - \usepackage{hyperxmp}
---

# A Low-Cost ESP32 Wearable for Real-Time EMG–IMU Acquisition with DMA Sampling and Self-Describing BLE

**Ryan Wang** — Westview High School, San Diego, CA, USA

*2026*

## Abstract

Monitoring muscle activity and body motion together reveals how neuromuscular effort evolves during athletic movement — in tennis, for example, fatigue manifests as greater muscle activation required to produce the same swing. Surface electromyography (EMG) records the electrical activity of contracting muscles, capturing effort and fatigue before they are visible in motion; an inertial measurement unit (IMU) records the acceleration and rotation of the moving limb. Research-grade systems that capture both reliably cost \$5,000–\$30,000, while commodity-microcontroller alternatives are affordable but rarely survive the timing, wireless, and physical-contact failures of real field deployment.

We present a \$99 ESP32-based wearable that streams concurrent EMG and IMU data over Bluetooth Low Energy (BLE) with microsecond-scale timing accuracy and field-tested reliability. A dual-core architecture dedicates one CPU core entirely to sensor acquisition while the other handles wireless transmission, preventing BLE processing from interrupting sample collection. Analog-to-digital (ADC) sampling with direct memory access (DMA) at 20 kHz per channel, decimated 10× in software, yields a 2 kHz EMG output stream with per-sample timestamp accuracy of ±25 µs, empirically verified across 2.3 million samples. A self-describing binary frame format embeds sensor-range metadata in every packet so firmware gain changes do not break host parsers, and a two-layer device/host watchdog with hybrid timeline reconstruction recovers from BLE dropouts and full device resets without data corruption. Across 150+ minutes of tennis field recording, the system showed zero detected sample drops. We also document a field-discovered hardware failure — a pogo-pin contact producing a "ghost" signal that mimics real EMG until filtering reveals it as flat — together with a quantitative diagnostic and solder-bypass fix. Although demonstrated in tennis, the platform is application-agnostic and supports a broad range of wearable biosignal use cases.

## I. Introduction

As fatigue sets in during athletic activity, neuromuscular control gradually degrades — the muscle has to work harder to produce the same motion, and the resulting changes in technique can lead to injury. Detecting this objectively, *before* it shows up in performance, is a long-standing goal of sports biomechanics. The two sensor modalities that together can answer this question are *surface electromyography* (EMG) and *inertial measurement* (IMU). Surface EMG places small electrodes on the skin over a target muscle and records the tiny electrical potentials that accompany contraction; the amplitude and frequency content of this signal reveal how hard the muscle is working and how that effort changes over time. An IMU — the same family of sensor found in smartphones, combining a 3-axis accelerometer with a 3-axis gyroscope — records the motion of the limb it is attached to: when a swing happens, how fast, in what orientation.

Either sensor alone is incomplete: motion alone cannot distinguish a controlled swing from a fatigued one of the same speed, and muscle activity alone cannot tell which motion produced it. Recorded together and time-aligned, these signals address a central fatigue-monitoring question: *is the muscle working harder to produce the same motion?*

This work is motivated by tennis, where fatigue across a long practice session is known to alter upper-limb muscle activity and degrade stroke performance [1], and where coaches currently rely on subjective observation rather than instrumented measurement. The hardware and capture pipeline themselves, however, are application-agnostic: any wearable scenario that requires time-aligned muscle-and-motion data — rehabilitation assessment, gesture recognition, occupational ergonomics [2], or e-sports performance monitoring — can reuse the same platform without modification.

Commercial research-grade systems (e.g., Delsys Trigno, Noraxon) capture EMG and IMU reliably with sub-millisecond synchronization, but at \$5,000–\$30,000 per unit they are out of reach for youth sport, school athletic programs, and most field research outside well-funded laboratories. The principal barrier is engineering effort — sensing modalities and microcontroller hardware are inexpensive — and a low-cost alternative becomes feasible once the timing, wireless, and physical-contact failure modes are addressed systematically.

Low-cost alternatives based on commodity microcontrollers face three practical challenges. First, achieving 2000 Hz EMG sampling without sample loss requires careful analog-to-digital converter (ADC) architecture — naive timer-based sampling at this rate consumes excessive CPU and competes with Bluetooth stack processing. Second, reliable BLE streaming at the combined data rate of EMG + IMU demands efficient packetization and transmission. Third, multi-sensor systems require precise timestamp alignment across sensors with different sampling rates (2000 Hz vs. 200 Hz) to support downstream analysis.

Prior work on low-cost wearable EMG systems [4,5,6] typically achieves adequate sampling rates in controlled laboratory settings but rarely documents the failure modes encountered in field deployment — pogo-pin routing failures, ADC crosstalk, BLE reconnection handling, and timestamp drift. These practical challenges are as important as the nominal specifications for reproducible research.

This paper presents the design and field validation of a complete low-cost wearable EMG–IMU acquisition system that addresses these challenges. Our contributions span firmware, protocol, and capture-pipeline engineering:

1. **Reliable high-rate EMG sampling.** ADC samples stream directly to memory without CPU involvement; 20 kHz per-channel acquisition decimated 10× in software, combined with per-sample timestamp reconstruction, yields ±25 µs accuracy at the 2 kHz output rate, empirically validated over 2.3 million samples.
2. **Protocol robustness across firmware changes.** A self-describing BLE frame format embeds IMU full-scale-range codes in every frame, enabling firmware parameter updates without host decoder changes — demonstrated unchanged across three firmware FSR revisions.
3. **Concurrent sensing without wireless interference.** A dual-core FreeRTOS architecture with explicit task-priority assignment achieves zero detected sample drops during concurrent EMG (2 kHz) + IMU (200 Hz) BLE streaming, evaluated across 150+ minutes of field recordings.
4. **Recovery from field interruptions.** A two-layer device/host watchdog (device-side pause at 18 s, reboot at 30 s) combined with host-side hybrid timeline reconstruction (`abs_us`) handles BLE-dropout and ESP32-reset cases; field testing demonstrated clean recovery from an inter-run reconnect without file corruption or parser failure.
5. **Physical-contact failure diagnosis.** A pogo-pin ADC ghost signal consistent with charge sharing or floating-input coupling (r = 0.998 with the envelope channel) that survives visual inspection but is silently destroyed by routine high-pass filtering, with quantified diagnosis and a reproducible solder-bypass fix.

## II. Related Work

**Commercial wearable EMG.** Lab-grade systems such as Delsys Trigno [11] and Noraxon Ultium [12] provide research-quality EMG with sub-millisecond synchronization and validated electrode interfaces, but at $5,000–$30,000 per unit they are inaccessible for youth sport and field deployment. Their proprietary firmware and capture pipelines are also closed, providing little reproducible engineering reference for practitioners building similar systems.

**Low-cost wearable EMG systems.** Cerone et al. [4] presented a modular HD-sEMG system with detailed analog front-end design but limited documentation of the BLE capture pipeline and reconnection behavior. Lynn et al. [13] validated the Athos compression-shirt platform against laboratory EMG but treated the underlying acquisition system as a black box. Yang et al. [6] surveyed e-textile EMG sensors with focus on electrode design rather than capture pipeline engineering. These works generally do not document the timestamp accuracy or BLE reliability metrics required for unattended multi-session field recording.

**IMU-EMG fusion platforms.** Taborri et al. [3] surveyed inertial-and-EMG sensors for sports biomechanics applications; Bangaru et al. [2] document data collection for construction-worker fatigue but rarely the firmware or protocol that collected it. The MultiSenseBadminton dataset [14] provides multi-modal sport recordings but does not describe the engineering decisions that made robust capture possible. Multi-sensor synchronization across sample rates as different as 2 kHz EMG and 200 Hz IMU is acknowledged as challenging but is rarely characterized quantitatively.

**BLE wearable engineering.** Most published BLE biosignal systems report their scientific results without describing reconnection robustness, multi-clock timestamp reconstruction, or on-device protocol-evolution strategies. Engineering details — magic-byte resync, CRC error rates, exponential-backoff reconnection policies, hybrid device/host timeline reconstruction — are typically left to firmware repositories rather than published systematically.

**Gap.** Few published low-cost wearable EMG systems document the full stack from firmware DMA design through BLE protocol to field-validated reliability metrics for a concurrent 2 kHz EMG + 200 Hz IMU wearable, including a quantitative analysis of physical-contact failure modes encountered in real deployment.

## III. System Architecture

### A. Hardware

The system uses five components totaling approximately $99 USD (Table I). The MyoWare 2.0 muscle sensor provides both a hardware-rectified envelope output (ENV) and a raw AC-coupled output (RAW) on separate pins, essential for concurrent amplitude and spectral EMG analysis.

**Table I.** Bill of Materials.

| Component | Function | Sampling Rate | Approx. Cost |
|:---|:---|:---|---:|
| MyoWare 2.0 | EMG (ENV + RAW) | 2000 Hz | $40 |
| ICM-20948 | 6-axis IMU | 200 Hz | $15 |
| MAX30105 | SpO2 / Heart Rate (optional) | ~0.03 Hz | $10 |
| MAX17048 | Battery fuel gauge | 0.1 Hz | $5 |
| ESP32 WROOM-32E | MCU + BLE | 240 MHz, dual-core | $12 |
| PCB / battery / wiring | Integration | — | ~$17 |
| **Total** | | | **≈ $99** |

The MAX30105 (SpO2/HR) and MAX17048 (battery gauge) are included for extensibility and device monitoring; the present evaluation focuses on EMG and IMU acquisition and the SpO2/HR channel is not part of the contributions reported here.

A field-discovered hardware issue: the MyoWare Wireless Shield routes the RAW signal through spring-loaded pogo pins to ESP32 GPIO 32. Under movement, pogo contact is unreliable, producing a ghost signal on the RAW channel that is highly correlated with ENV (r = 0.998), consistent with ADC multiplexer charge sharing or floating-input coupling — the floating RAW input appeared to track the previously sampled ENV voltage. After filtering, the ghost signal flatlines, causing silent loss of usable RAW spectral EMG. The fix is a direct solder jumper from the MyoWare RAW pad to GPIO 32 (ADC1 channel 4). Post-fix, the RAW channel shows the expected AC EMG waveform during contraction.

### B. Dual-Core FreeRTOS Architecture

The ESP32 dual-core architecture enables strict separation of real-time sensor acquisition from BLE protocol processing. Fig. 1 shows the task allocation.

![Fig. 1. System architecture showing dual-core task allocation, sensor connections, and host interfaces.](icpics_figures/fig_system_architecture.png)

**Core 1 (Sensor CPU):** Three tasks run concurrently:
- `emgDrainTask` (priority 2): drains ADC DMA buffer, decimates 10× to 2000 Hz, writes to ring buffer
- `imuTask` (priority 2): reads ICM-20948 at 200 Hz via timer-triggered I2C
- `spo2Task` (priority 0): computes SpO2/HR every ~30 seconds in background

**Core 0 (Protocol CPU):** `loop()` handles BLE notifications, host watchdog, LED state machine, and battery monitoring. This separation prevents BLE stack processing from interrupting sensor acquisition.

Task priority 2 for both `emgDrainTask` and `imuTask` was selected after observing that priority 1 allowed `spo2Task` I2C operations to occasionally starve IMU reads — a non-obvious interaction in FreeRTOS that is documented here to benefit other practitioners.

## IV. Signal Acquisition

### A. ADC DMA Oversampling

Timer-based ADC sampling at 2000 Hz would require 2000 ISR calls per second per channel, competing with FreeRTOS scheduling overhead. Instead, we use the ESP32 ADC Continuous (DMA) driver configured for 40,000 total conversions/s across the two channels (ENV and RAW), yielding 20,000 conversions/s per channel; `emgDrainTask` then applies 10× software decimation to produce the 2,000 Hz output rate per channel:

```
ADC DMA: 40,000 conv/s total ÷ 2 channels = 20,000 samples/s per channel (raw)
         ↓ 10× decimation in emgDrainTask
Output: 2,000 Hz per channel
```

The DMA frame size is 256 bytes (64 results × 4 bytes each), covering 1.6 ms of acquisition — well within FreeRTOS task scheduling jitter. `emgDrainTask` is notified by DMA completion and drains frames from a circular DMA buffer.

### B. Per-Sample Timestamp Back-Calculation

A key challenge is that DMA frame completion notification may arrive up to 16 ms after the actual last sample in the frame (FreeRTOS scheduling jitter). We correct this using the known DMA frame duration:

```
t0_us = frameEndUs - (count × EMG_PERIOD_US)
sample_i_us = t0_us + (i × EMG_PERIOD_US)
```

where `frameEndUs` is the ESP32 `esp_timer_get_time()` at frame drain, `count` is the number of samples in the frame, and `EMG_PERIOD_US = 500 µs` (2000 Hz period).

Fig. 2 shows the empirical inter-sample interval distribution across 2.3 million samples from a 131.7-second field session. The result confirms that 99.03% of samples fall within ±25 µs of the expected 500 µs interval, with 97.7% at exactly 500 µs. The outliers at p99.9 (925 µs) correspond to DMA buffer stalls during brief BLE transmission bursts and represent less than 0.1% of samples.

![Fig. 2. Inter-sample interval distribution across 2.3 million samples. 99.03% of samples fall within ±25 µs of the expected 500 µs period (2000 Hz).](icpics_figures/fig_timing_accuracy.png)

### C. Multi-Sensor I2C Bus Management

The IMU, SpO2, and battery gauge share a single I2C bus. A FreeRTOS mutex (`wireMutex`) serializes access across `imuTask`, `spo2Task`, and `loop()`. Without this, concurrent I2C access caused occasional sensor read failures that were difficult to reproduce. The I2C clock is set to 400 kHz; ICM-20948 reads at 200 Hz consume approximately 3% of available I2C bandwidth, leaving ample margin for SpO2 and battery reads.

## V. Protocol Design

### A. Binary TLV Frame Format

Fig. 3 shows the binary frame format. All multi-byte fields are little-endian.

![Fig. 3. Binary TLV frame format. PROTO_VER = 0x02 adds IMU FSR metadata in FLAG_IMU_META_V2.](icpics_figures/fig_protocol.png)

The 14-byte header contains: 2-byte magic (0xA5 0x5A), protocol version byte, flags byte, 4-byte sequence number, 4-byte frame timestamp (32-bit µs, extended to 64-bit by host), and 2-byte payload length. The CRC16-CCITT checksum over header + payload enables corruption detection on noisy BLE channels.

Three TLV types are defined: `TLV_EMG_BATCH (0x01)`, `TLV_IMU_BATCH (0x02)`, and `TLV_VITALS (0x03)`. Multiple TLV blocks can be concatenated in one frame, enabling efficient batching of sensor data.

### B. Self-Describing IMU FSR Protocol

A practical problem in iterative firmware development: when the IMU full-scale range (FSR) setting changes (e.g., gyroscope ±250 → ±1000 → ±2000 dps across three firmware versions to prevent saturation during hard tennis swings), the host decoder must apply the correct scale factor. Hardcoding the FSR in host code creates brittle coupling.

Our solution: every `TLV_IMU_BATCH` frame includes two bytes specifying `acc_fsr_code` and `gyro_fsr_code` when `FLAG_IMU_META_V2` is set. The host maps these codes to physical scale factors at runtime:

```python
ACC_FSR_CODE_TO_G    = {0: 2, 1: 4, 2: 8, 3: 16}    # g
GYRO_FSR_CODE_TO_DPS = {0: 250, 1: 500, 2: 1000, 3: 2000}  # dps
```

This design was validated across three firmware FSR changes with no host decoder changes required.

**Table III.** IMU full-scale-range (FSR) revisions across firmware iterations.

| Firmware revision | Gyro FSR | Acc FSR | Gyro code | Acc code | Reason for change |
|:---|:---:|:---:|:---:|:---:|:---|
| v1 (initial) | ±250 dps | ±2 g | 0 | 0 | ICM-20948 default; saturated on hard tennis swings |
| v2 (mid-development) | ±1000 dps | ±4 g | 2 | 1 | Reduce gyro saturation; still occasional acc clipping |
| v3 (current, since 2026-03-03) | ±2000 dps | ±8 g | 3 | 2 | Eliminate saturation across all observed swings |

The host parser uses the per-frame `gyro_fsr_code` and `acc_fsr_code` to apply the correct LSB-to-physical-unit scale at decode time; no host code changes were required across these three revisions.

### C. Host Watchdog with Graceful Degradation

Unattended field recording requires the device to recover from host disconnection or BLE stack hangs. We implement a three-state watchdog based on received PING messages from the host (sent every ~1 second via the BLE RX characteristic):

1. **Normal** (< 18 s since last PING): streaming active
2. **Pause** (18–30 s): ADC DMA stopped, observed approximately 40 mA current reduction; IMU and SpO2 suspend
3. **Reboot** (> 30 s): hardware reset, BLE advertising restarts automatically

This mechanism was exercised during a between-run BLE reconnect event in field sessions totaling over 150 minutes, with no detected sample drops in recorded active-stream segments and no file corruption after reconnection.

## VI. Host Capture Pipeline

The PC host receiver (`btCentral.py`) is built on the Bleak BLE library and uses an asynchronous task pipeline: BLE notifications enqueue raw bytes onto an `asyncio.Queue`, a consumer task drains the queue in batches, a `FrameParser` re-synchronizes on the 0xA5 0x5A magic bytes and validates each frame's CRC16, decoded TLVs are appended to in-memory row buffers, and a writer task flushes buffers to disk every 2 s. The BLE callback does only enqueue work; all parsing and disk I/O happen in asyncio tasks, so a slow disk write never delays the BLE callback chain.

Captured frames are logged to time-rotating CSV files named `emg_log_<session_id>_<open_id>_<idx>.csv` and `imu_log_<session_id>_<open_id>_<idx>.csv` (default 30 min per segment), each with a sidecar `.meta.json` recording session metadata (FSR codes, sample rate, MAC address, segment open/close times). Vitals are appended to a single `vitals_log.csv`. Metadata files are written via tmp-file-then-rename for atomicity. A separate UDP mirror (best-effort, non-blocking, decimated to 500/50/50 Hz for RAW/ENV/IMU) feeds an optional real-time plotter without affecting the recording path.

A host-side watchdog task complements the device-side watchdog. If no BLE notifications arrive for 5 s, the watchdog first attempts a re-subscribe to the NUS TX characteristic; if that fails, it triggers a full reconnect with exponential backoff (0.5 s → 20 s cap). All buffered rows are flushed before the reconnect, preventing loss of already buffered rows. After reconnection, the host resumes recording into the same file series; sequence-number continuity is preserved on the device side (the device clock and `frame_seq` keep running through pure BLE dropout).

To handle the harder case — when the device itself reboots and the device clock restarts — the host computes a hybrid `abs_us` timeline. Within a single BLE connection, `abs_us` follows the host-extended device timestamp (`dev_us`), which is precise (±25 µs from § IV.B). Between connections, `abs_us` is advanced by the difference in `host_rx_ms` across the reconnection gap. This rule unifies BLE-dropout and ESP32-reset cases without requiring the host to detect which occurred: in either case, the gap is bounded by the wall-clock interval the host observed. We treat formal validation against `host_rx_ms` ground truth across the inter-run gap as out of scope for this conference paper and defer it to an extended journal version.

## VII. Evaluation

### A. Timestamp Accuracy

As shown in Fig. 2 and Table II, empirical analysis of 2.3 million samples from a 131.7-second field recording confirms the ±25 µs timestamp accuracy claim. The 0.97% of samples outside ±25 µs are bounded within ±500 µs (99.96%), corresponding to brief DMA stalls during BLE TX bursts.

**Table II.** Inter-sample interval statistics (log0305, 2,324,791 samples).

| Metric | Value |
|:---|:---|
| Expected interval | 500 µs (2000 Hz) |
| p50 (median) | 500 µs |
| p95 | 500 µs |
| p99 | 505 µs |
| Within ±25 µs | **99.03%** |
| Exactly 500 µs | 97.7% |
| Within ±500 µs | 99.96% |

### B. Data Throughput and Drop Rate

The combined data rate is approximately 12.5 KB/s (EMG: 8000 bytes/s, IMU: 2400 bytes/s, headers/CRC: ~2100 bytes/s), near BLE 4.2 throughput capacity with MTU=244 bytes at CONNECTION_PRIORITY_HIGH. Across two field sessions totaling 150+ minutes and 823 detected swings, sequence-number continuity analysis showed **zero detected EMG or IMU sample drops during active streaming**. The CRC error rate was computed as CRC-rejected frames divided by total received frame candidates reported by the host parser. The single between-run reconnect was handled without file corruption, parser lockup, or host-side recording failure. All evaluation metrics in this section were computed from the logged CSV files and parser metadata generated by `btCentral.py`. Table IV summarizes per-session reliability metrics.

**Table IV.** Field validation summary.

| Session | Duration (min) | Swings | btCentral runs | Inter-run reconnects | Sample drops | CRC errors |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| log0303 | 87.9 | 197 | 2 | 1 | 0 | <0.01% |
| log0305 | 63.1 | 626 | 1 | 0 | 0 | <0.01% |
| **Total** | **151.0** | **823** | **3** | **1** | **0** | **<0.01%** |

### C. BLE Reconnection Robustness

One between-run BLE reconnect event was observed across the field sessions, separating two `btCentral.py` runs within the log0303 directory (session_id changed from `20260303_183639` to `20260303_191258`). Recording resumed cleanly into a new file series after the reconnect; the host used frame-sequence and session metadata to distinguish continuous active-stream segments from the inter-run gap. The hybrid `abs_us` timeline reconstruction correctly preserved the inter-run gap, enabling downstream analysis to detect session discontinuities rather than treating them as continuous data. Within-run BLE re-subscriptions (handled by the host watchdog re-subscribing to NUS TX without process restart) are not separately quantified here and are deferred to the journal extension.

### D. Field Failure: Pogo-Pin Ghost Signal

Before the GPIO 32 solder bypass, the RAW channel exhibited a ghost signal with Pearson r = 0.998 vs. the ENV channel, with near-zero variance (standard deviation < 5 ADC counts vs. expected 50–500 during contraction). After bandpass filtering (50–450 Hz), the ghost flatlined entirely, causing silent loss of usable RAW spectral EMG. Post-bypass validation confirmed independent AC EMG oscillation (standard deviation > 100 counts during contraction) and ENV-RAW correlation dropping to r = −0.013 for filtered signals, as expected for independent signal paths. This diagnosis was supported by the extremely high RAW–ENV correlation, near-zero RAW variance, post-filter flatline, and disappearance after direct solder bypass. Fig. 4 shows the live `sensordata_plotter.py` view before and after the bypass.

![Fig. 4. Pogo-pin ghost-signal failure mode before and after direct RAW-to-GPIO32 solder bypass. Pre-bypass, RAW ghost-tracked ENV (r = 0.998) and the preprocessed EMG channel flatlined. Post-bypass, RAW showed independent AC oscillation during contraction and retained spectral content after preprocessing.](icpics_figures/fig_pogo_pin_pre_post.png)

### E. Data Collection and Consent

Field recordings were collected using non-invasive wearable sEMG/IMU sensors during normal tennis practice. Written informed consent was obtained from a parent or legal guardian, and participant assent was obtained where applicable. Data were anonymized before analysis and publication.

## VIII. Discussion

**Generalization of the pogo-pin failure mode.** ADC multiplexer charge sharing is not specific to MyoWare or to pogo pins. Any wearable that routes a high-impedance analog signal through a non-soldered contact (pogo pin, snap, spring contact, ZIF socket) and samples it on a multiplexed ADC is vulnerable to the same failure mode. The diagnostic heuristic generalizes: a Pearson correlation greater than 0.95 between two channels that should be electrically independent, accompanied by near-zero variance on one of them, indicates crosstalk or a floating pin. We recommend that practitioners building similar systems explicitly check for this signature in early field captures rather than trusting visual inspection of the raw waveform — high-pass filtering will silently destroy the ghost signal, leaving a flatline that is easy to miss in offline analysis.

**Generalization of `abs_us`.** The hybrid timeline reconstruction has no MyoWare- or tennis-specific assumptions. Any BLE logger that records a device microsecond timestamp and a host millisecond receive time can apply the same two-case rule. The reconstruction gap is bounded by the BLE notification interval on the dropout end (typically 7.5–30 ms) and by the BLE advertising interval on the reset end, both observable at millisecond-scale host timestamp resolution.

**Limitations.** Validation rests on a single sport, one subject, and two sessions totaling 150+ minutes; broader subject and sport diversity are needed to confirm generality. The combined data rate (~12.5 KB/s) is near BLE 4.2 sustained throughput at MTU 244, so adding more sensors will require rate reduction or migration to BLE 5.0 with 2M PHY. Formal validation of `abs_us` reconstruction error against `host_rx_ms` ground truth is deferred to an extended journal version.

**Future work.** AD5933-based on-board electrode-impedance monitoring to detect contact loss before silent data corruption, dynamic BLE-side sample-rate negotiation, multi-device synchronized acquisition for bilateral EMG, and an Android Chaquopy port enabling on-device biosignal spectral analysis without a PC.

## IX. Conclusion

We presented a low-cost ($99) ESP32 wearable achieving reliable concurrent EMG (2000 Hz) and IMU (200 Hz) BLE streaming through five specific engineering contributions: DMA-driven oversampling ADC with ±25 µs timestamp accuracy (empirically verified, 99.03% over 2.3M samples), self-describing IMU FSR protocol surviving three firmware FSR revisions, dual-core FreeRTOS architecture with zero detected sample drops during active streaming, device-side host-ping watchdog and host reconnect handling enabling unattended field sessions, and documented field-failure diagnosis and repair for the pogo-pin ghost signal. The system, field-tested across 150+ minutes of sports deployment, provides a reproducible low-cost platform for wearable biosignal acquisition research.

## References

[1] Rota S, Morel B, Saboul D, Rogowski I, Hautier C. "Influence of fatigue on upper limb muscle activity and performance in tennis." J Electromyogr Kinesiol. 2014;24(1):90–97.

[2] Bangaru SS, Wang C, Aghazadeh F. "Automated and continuous fatigue monitoring in construction workers using forearm EMG and IMU wearable sensors and recurrent neural network." Sensors. 2022;22(24):9729.

[3] Taborri J, et al. "Sport biomechanics applications using inertial, force, and EMG sensors: A literature overview." Appl Bionics Biomech. 2020;2020:2041549.

[4] Cerone GL, Botter A, Gazzoni M. "A modular, smart, and wearable system for high density sEMG detection." IEEE Trans Biomed Eng. 2019;66(12):3371–3380.

[5] Farago E, et al. "A review of techniques for surface electromyography signal quality analysis." IEEE Rev Biomed Eng. 2022;16:494–511.

[6] Yang K, et al. "E-textiles for sports and fitness sensing: current state, challenges, and future opportunities." Sensors. 2024;24(4):1058.

[7] Hermens HJ, et al. "Development of recommendations for SEMG sensors and sensor placement procedures." J Electromyogr Kinesiol. 2000;10(5):361–374.

[8] Joutsen A, et al. "ECG signal quality in intermittent long-term dry electrode recordings." Sci Rep. 2024;14:8936.

[9] Boyer M, et al. "Reducing noise, artifacts and interference in single-channel EMG signals: a review." Sensors. 2023;23(6):2927.

[10] SparkFun Electronics. MyoWare 2.0 Muscle Sensor Advanced Guide. 2023.

[11] Delsys Inc. "Trigno Wireless EMG System — Technical Specifications." Natick, MA, USA, 2024.

[12] Noraxon USA. "Ultium EMG Sensor System — Product Documentation." Scottsdale, AZ, USA, 2024.

[13] Lynn SK, Watkins CM, Wong MA, Balfany K, Feeney DF. "Validity and reliability of surface electromyography measurements from a wearable athlete performance system." J Sports Sci Med. 2018;17(2):205–215.

[14] Seong M, Kim G, Yeo D, et al. "MultiSenseBadminton: Wearable sensor-based biomechanical dataset for evaluation of badminton performance." Sci Data. 2024;11:343.
