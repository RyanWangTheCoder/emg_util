---
output:
  pdf_document:
    pandoc_args: ["--pdf-engine=xelatex"]
keywords: "wearable, EMG, IMU, BLE, ESP32, DMA, real-time, biosignal"
header-includes:
  - \usepackage{hyperxmp}
---

# A Robust Self-Describing BLE Platform for Real-Time Wearable EMG–IMU Sensing

**Ryan Wang** — Westview High School, San Diego, CA, USA
**Dr. YanMing Di** — Professor, Department of Statistics, Oregon State University, Corvallis, OR, USA

*2026*

## Abstract

Wearable EMG–IMU sensing can reveal how muscle effort and limb motion evolve during athletic movement, but research-grade systems are costly and low-cost prototypes often fail under field conditions. We present a $99 ESP32-based wearable for concurrent EMG and IMU acquisition over Bluetooth Low Energy (BLE). The system uses dual-core FreeRTOS scheduling, ADC DMA at 20 kHz per EMG channel, 10× boxcar decimation to paired 2 kHz ENV/RAW samples, a self-describing binary BLE protocol, and host-side timeline reconstruction across reconnects and device resets. Across 7,496,659 unique 2 kHz EMG output samples from a 63.1-min field session, 98.65% of received-sample intervals were within ±25 µs of the expected 500 µs period. Across 151 min of tennis field recordings, EMG sequence loss was 0.98% in the cleaner session and 2.64% across both sessions combined (with the noisier session at 7.66%), consistent with host-visible BLE/parser loss rather than confirmed device-side acquisition gaps. We also report a field-discovered pogo-pin ghost-signal failure with a quantitative diagnostic and solder-bypass repair. The result is a reproducible low-cost platform for field-debuggable EMG–IMU capture.

## I. Introduction

Surface electromyography (EMG) and inertial measurement (IMU) together support field studies of how muscle effort and limb motion evolve during athletic movement. Tennis is one well-studied case [1] — for example, prolonged practice changes upper-limb muscle activation patterns associated with fatigue — but the hardware and capture pipeline are application-agnostic and apply equally to rehabilitation assessment, gesture recognition, occupational ergonomics [2], or e-sports performance monitoring.

Commercial research-grade systems (e.g., Delsys Trigno [3], Noraxon Ultium [4]) capture EMG and IMU reliably but at $5,000–$30,000 per unit are out of reach for youth sport and most field research. Low-cost alternatives based on commodity microcontrollers face three practical challenges: (i) achieving 2000 Hz EMG sampling without sample loss requires careful ADC architecture, since naive timer-based sampling competes with the Bluetooth stack; (ii) reliable BLE streaming at the combined EMG + IMU data rate demands efficient packetization and reconnection handling; (iii) multi-sensor systems require precise timestamp alignment across sensors with different sampling rates (2000 Hz vs. 200 Hz). Prior low-cost wearable EMG systems [5,6,7] typically achieve adequate sampling in controlled laboratory settings but rarely document the failure modes encountered in field deployment — pogo-pin routing failures, ADC crosstalk, BLE reconnection, and timestamp drift.

This paper presents the design and field validation of a complete $99 wearable EMG–IMU acquisition system. Our contributions are: (1) DMA-driven 20 kHz/channel ADC acquisition decimated to paired 2 kHz ENV/RAW EMG output samples with empirically verified ±25 µs per-sample timestamp accuracy; (2) a self-describing BLE TLV protocol that carries IMU full-scale-range metadata so firmware revisions do not break host decoders; (3) dual-core FreeRTOS scheduling for concurrent 2 kHz EMG + 200 Hz IMU streaming with quantified per-session sample-loss accounting; (4) a device/host watchdog and hybrid `abs_us` timeline supporting recovery from BLE dropouts and device resets, with no file corruption observed across the recorded reconnect; and (5) a quantitative diagnosis and solder-bypass repair of a pogo-pin RAW-channel ghost-signal failure mode that survives visual inspection but is silently destroyed by routine high-pass filtering.

## II. Related Work

Commercial EMG systems such as Delsys Trigno [3] and Noraxon Ultium [4] provide synchronized EMG/IMU acquisition but cost \$5,000–\$30,000 and use mostly proprietary acquisition pipelines. Low-cost academic and wearable EMG systems [5]–[8] demonstrate feasibility, but typically emphasize sensor design, validation, or downstream analytics rather than the full acquisition stack needed for unattended field recording.

For sports biomechanics, prior EMG/IMU work has surveyed sensing modalities [9] and released multimodal datasets [10], but rarely reports the implementation details that determine whether low-cost systems survive field deployment: DMA sampling, BLE packetization, reconnect behavior, multi-clock timestamp reconstruction, firmware/host metadata compatibility, per-session sample-drop accounting, and physical-contact failure diagnostics. This paper focuses on those details for a concurrent 2 kHz EMG + 200 Hz IMU wearable.

## III. System Architecture

### A. Hardware

Table I summarizes the $99 hardware. The MyoWare 2.0 provides both envelope (ENV) and raw AC-coupled (RAW) outputs; the dual-output is essential for downstream spectral analysis (fatigue-biomarker computation itself is outside this paper). Earlier prototype work by the lead author [11] used a single-output Seeed Grove EMG Detector [12] that exposes only an amplified-filtered envelope, motivating the move to a sensor with explicit RAW access. The ICM-20948 provides 6-axis motion at 200 Hz; MAX30105 and MAX17048 modules are included for extensibility and battery monitoring but are not part of the EMG/IMU evaluation. A field-discovered routing failure on the MyoWare Wireless Shield is repaired by a direct solder jumper from the RAW pad to ESP32 GPIO 32 (ADC1 channel 4) and characterized quantitatively in §VII.D.

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

### B. Dual-Core FreeRTOS Architecture

The ESP32 dual-core architecture enables strict separation of real-time sensor acquisition from BLE protocol processing. Fig. 1 shows the task allocation.

![Fig. 1. System architecture showing dual-core task allocation, sensor connections, and host interfaces.](icpics_figures/fig_system_architecture.png)

**Core 1 (Sensor CPU):** Three tasks run concurrently:
- `emgDrainTask` (priority 2): drains ADC DMA buffer, decimates 10× to 2000 Hz, writes to ring buffer
- `imuTask` (priority 2): reads ICM-20948 at 200 Hz via timer-triggered I2C
- `spo2Task` (priority 0, optional / not evaluated): MAX30105 SpO2/HR background placeholder

**Core 0 (Protocol CPU):** `loop()` handles BLE notifications, host watchdog, LED state machine, and battery monitoring. This separation prevents BLE stack processing from interrupting sensor acquisition.

Task priority 2 for both `emgDrainTask` and `imuTask` was selected after observing that priority 1 allowed `spo2Task` I2C operations to occasionally starve IMU reads — a non-obvious interaction in FreeRTOS that is documented here to benefit other practitioners.

## IV. Signal Acquisition

### A. ADC DMA Oversampling and Decimation

The ESP32 ADC Continuous (DMA) driver is configured for 40,000 conversions/s across ENV and RAW (20 kHz/channel), avoiding the per-conversion ISR cost of timer-based sampling. *emgDrainTask* averages every 10 conversions per channel into one paired 2 kHz EMG output sample `(ENV, RAW, dev_us)`. The 10-tap boxcar provides first-stage attenuation with first null at the 2 kHz output rate and −3 dB near 880 Hz; combined with the MyoWare RAW analog band-limiting (passband below 1 kHz), this was adequate for the acquisition-platform evaluation reported here. A future firmware revision could substitute a sharper FIR if higher-frequency contamination becomes relevant. Tighter post-decimation band-limiting (50–450 Hz bandpass + 60/120 Hz notches) runs in the host pipeline before any spectral analysis. Throughout this paper, *EMG output sample* refers to one decimated 2 kHz output comprising a paired (ENV, RAW) value; *ADC conversion* refers to a pre-decimation 20 kHz reading on a single channel.

### B. Per-Sample Timestamp Back-Calculation

DMA frame completion notification may arrive up to 16 ms after the actual last sample in the frame. We correct this using the known frame duration: for each DMA frame of *N* samples drained at the ESP32 timer reading *t<sub>end</sub>*, the *i*-th sample's timestamp is back-calculated as *t<sub>end</sub>* − (*N* − *i*) · *T*, *T* = 500 µs. Empirical inter-sample interval distribution from log0305 is shown in Fig. 2 and Table III.

![Fig. 2. Inter-sample interval distribution across 7,496,659 unique 2 kHz EMG output samples (deduplicated by sequence number) from a 63.1-minute single-session field recording (log0305). 98.65% of received-sample intervals fall within ±25 µs of the expected 500 µs period.](icpics_figures/fig_timing_accuracy.png)

### C. Multi-Sensor I2C Bus Management

The IMU, SpO2, and battery gauge share a 400 kHz I2C bus serialized by a FreeRTOS mutex (`wireMutex`); ICM-20948 reads at 200 Hz consume ~3% of bandwidth.

## V. Protocol Design

### A. Binary TLV Frame Format

Fig. 3 shows the binary frame format (multi-byte fields little-endian). The 14-byte header carries 2-byte magic (0xA5 0x5A), version, flags, 4-byte BLE-frame sequence number, 4-byte 32-bit µs frame timestamp (host-extended to 64-bit), and 2-byte payload length. A CRC16-CCITT covers header + payload. Three TLV types — `TLV_EMG_BATCH (0x01)`, `TLV_IMU_BATCH (0x02)`, `TLV_VITALS (0x03)` — concatenate into one frame. Two distinct sequence notions are used in this paper: the *BLE-frame sequence number* (in the header) indexes outgoing notifications, and the *EMG / IMU sample sequence number* is assigned per-sample inside the EMG/IMU TLV payloads and recorded as `emg_seq` / `imu_seq` in the captured CSVs. Sample-loss analyses in §VII use the per-sample sequence numbers.

![Fig. 3. Binary TLV frame format. PROTO_VER = 0x02 adds IMU FSR metadata in FLAG_IMU_META_V2.](icpics_figures/fig_protocol.png)

### B. Self-Describing Sensor-Metadata Protocol

When the IMU full-scale range (FSR) changes (e.g., gyroscope ±250 → ±1000 → ±2000 dps to prevent saturation during hard tennis swings), the host decoder must apply the correct scale factor; hardcoding the FSR creates brittle coupling. Each `TLV_IMU_BATCH` includes `acc_fsr_code` and `gyro_fsr_code` when `FLAG_IMU_META_V2` is set; the host maps these codes to physical scale factors at runtime (e.g., `GYRO_FSR_CODE_TO_DPS = {0:250, 1:500, 2:1000, 3:2000}`). This was validated unchanged across the three FSR revisions in Table II.

**Table II.** IMU full-scale-range (FSR) revisions across firmware iterations.

| Firmware revision | Gyro FSR | Acc FSR | Gyro code | Acc code | Reason for change |
|:---|:---:|:---:|:---:|:---:|:---|
| v1 (initial) | ±250 dps | ±2 g | 0 | 0 | ICM-20948 default; saturated on hard swings |
| v2 (mid-development) | ±1000 dps | ±4 g | 2 | 1 | Reduce gyro saturation; occasional acc clipping |
| v3 (since 2026-03-03) | ±2000 dps | ±8 g | 3 | 2 | Eliminate saturation across all observed swings |

### C. Host Watchdog with Graceful Degradation

A three-state device watchdog driven by host PINGs (~1 s): **Normal** (< 18 s) — streaming; **Pause** (18–30 s) — ADC DMA stopped (~40 mA reduction), IMU/SpO2 suspended; **Reboot** (> 30 s) — hardware reset, BLE advertising restarts. This was exercised by a between-run reconnect in the 150+-min corpus; recording resumed cleanly into a new file series and no file corruption was observed.

## VI. Host Capture Pipeline

The host receiver (`btCentral.py`, Bleak) queues BLE notifications onto an `asyncio.Queue`, resynchronizes on the 0xA5 0x5A magic bytes, validates each frame's CRC16, and flushes decoded EMG/IMU TLVs to time-rotating CSV files (default 30 min/segment) every 2 s, with sidecar `.meta.json` (FSR codes, sample rate, MAC, segment open/close times) written tmp-then-rename for atomicity. If notifications stop for 5 s, the host first re-subscribes to NUS TX; if that fails it triggers a full reconnect with exponential backoff (0.5 → 20 s). For analysis, the host constructs a hybrid `abs_us` timeline: within a BLE connection it follows the host-extended device microsecond clock (precise to ±25 µs from §IV.B); across reconnects or device resets it advances by the difference in `host_rx_ms`, unifying BLE-dropout and device-reset cases. Formal validation of `abs_us` against `host_rx_ms` ground truth is deferred to a journal extension.

## VII. Evaluation

### A. Timestamp Accuracy

Table III reports inter-sample interval statistics for 7,496,659 unique 2 kHz EMG output samples (deduplicated by sequence number) from log0305. 98.65% of received-sample intervals fall within ±25 µs of the expected 500 µs period and 99.98% within ±500 µs. Timing distributions from log0303 segments agreed within 0.3 percentage points. Intervals outside ±25 µs include both device-side scheduling jitter and intervals adjacent to unrecovered missing samples, and are interpreted together with the sequence-loss analysis in Table IV.

**Table III.** Inter-sample interval statistics (log0305, 7,496,659 unique 2 kHz EMG output samples).

| Metric | Value |
|:---|:---|
| Expected interval | 500 µs (2000 Hz) |
| Within ±25 µs | **98.65%** |
| Exactly 500 µs | 97.68% |
| Within ±500 µs | 99.98% |

### B. Data Throughput and Drop Rate

The combined data rate is ~12.5 KB/s (EMG 8000 B/s = two 16-bit channels at 2 kHz; IMU 2400 B/s = six 16-bit axes at 200 Hz; headers/CRC ~2100 B/s), near BLE 4.2 capacity at MTU 244 with CONNECTION_PRIORITY_HIGH. The MAX30105 vitals payload is excluded from this figure since the present evaluation reports EMG/IMU streaming only. Across 150+ minutes and 823 swings, sequence-number continuity gives an aggregate EMG sample loss of 266,368 / 10,078,200 = 2.64% (log0305: 0.98%; log0303: 7.66% across two BLE sub-sessions of 11.74% and 0.37%); log0303 was an early field session with the v3 firmware shortly after its 2026-03-03 rollout and is retained as worst-case characterization, while log0305 reflects the same firmware in a more stable RF environment. The single between-run reconnect was handled without file corruption or parser lockup. The host validates CRC16-CCITT on every frame and drops failures, but per-session CRC failure counts were not retained as separate counters in this evaluation. Table IV summarizes per-session reliability.

**Table IV.** Field validation summary. EMG sample drops = `max_seq − min_seq + 1 − unique_seq_count` per BLE session.

| Session | Duration (min) | Swings | btCentral runs | Inter-run reconnects | EMG sample drops |
|:---|:---:|:---:|:---:|:---:|:---|
| log0303 | 87.9 | 197 | 2 | 1 | 192,231 / 2,508,204 (7.66%) |
| log0305 | 63.1 | 626 | 1 | 0 | 74,137 / 7,570,796 (0.98%) |
| **Total** | **151.0** | **823** | **3** | **1** | **266,368 / 10,078,200 (2.64%)** |

Fig. 4 illustrates the time-aligned concurrent acquisition: a 4-second window around a tennis swing shows EMG envelope and gyro magnitude co-registered on the platform's *abs_us* timeline, demonstrating that 2 kHz EMG and 200 Hz IMU streams remain mutually synchronized through capture and host reconstruction. The relative timing of the EMG envelope rise and the gyro-magnitude peak is shown for visual context only; quantitative biomechanical or fatigue-related interpretation of that timing is outside the scope of this platform paper.

![Fig. 4. Time-aligned EMG (2 kHz) and IMU (200 Hz) over a 4-second window centered on a tennis swing (red dashed line). EMG envelope (top, 50-ms rolling RMS) and gyro magnitude (bottom) plotted on the platform's `abs_us` timeline; the figure illustrates cross-modality co-registration only.](icpics_figures/fig_emg_imu_sync.png)

### C. BLE Reconnection Robustness

One between-run BLE reconnect was observed (within log0303, session_id changed from `20260303_183639` to `20260303_191258`). Recording resumed cleanly into a new file series; the hybrid `abs_us` timeline preserved the inter-run gap, enabling downstream analysis to detect session discontinuities rather than treating them as continuous data.

### D. Field Failure: Pogo-Pin Ghost Signal

The MyoWare Wireless Shield originally routes RAW through spring-loaded pogo pins to ESP32 GPIO 32; under movement, pogo contact is unreliable and the floating ADC input tracks the previously sampled ENV voltage (consistent with multiplexer charge sharing). Before the solder bypass the RAW channel exhibited Pearson r = 0.998 vs. ENV with near-zero variance (SD < 5 ADC counts vs. expected 50–500 during contraction); after 50–450 Hz bandpass the ghost flatlined entirely. Post-bypass, RAW showed independent AC oscillation (SD > 100) and filtered ENV–RAW correlation dropped to r = −0.013. The diagnostic signature — high cross-channel correlation + near-zero per-channel variance + post-filter flatline that disappears after solder bypass — generalizes to any high-impedance analog input routed through a non-soldered contact and sampled on a multiplexed ADC.

## VIII. Discussion

The main field lesson is that physical contacts can fail silently: a floating RAW input can track ENV through ADC coupling, pass visual inspection, and then disappear after filtering. Early captures should therefore check cross-channel correlation and per-channel variance before downstream analysis. The current BLE 4.2 path also operates near its practical throughput limit, producing measurable host-visible sequence loss; future versions should add onboard buffering with retransmission, tighter TLV batching, dedicated CRC/resync counters, or BLE 5 2M PHY. The hybrid `abs_us` reconstruction has no MyoWare- or tennis-specific assumptions and applies to any BLE logger that records both a device microsecond timestamp and a host millisecond receive time.

**Limitations and future work.** Validation rests on a single sport, one subject, and 150+ minutes; broader subject and sport diversity are needed. Spectral fatigue-biomarker computation and validation (e.g., MDF/MNF on the RAW channel) are out of scope here and are the subject of a separate methodology study. Future firmware will retain CRC failure, parser-resync, and dropped-frame counters as first-class telemetry rather than only post-validation CSV rows. Formal `abs_us` validation against `host_rx_ms` ground truth, on-board impedance monitoring, multi-device synchronized acquisition, and an Android Chaquopy port are deferred to a journal extension.

## IX. Conclusion

We presented a $99 ESP32 wearable for field-tested concurrent 2 kHz EMG and 200 Hz IMU BLE streaming with five engineering contributions: DMA-driven oversampling ADC with ±25 µs timestamp accuracy (98.65% of 7.5 M EMG output samples over 63.1 minutes), self-describing sensor-metadata protocol surviving three FSR revisions, dual-core FreeRTOS architecture with measured EMG sequence loss of 0.98% in the cleaner session and 2.64% across 150+ minutes combined, two-layer device/host watchdog with hybrid timeline reconstruction, and quantitative diagnosis and repair of a pogo-pin ghost-signal failure mode. The platform serves as a reproducible low-cost building block for downstream signal processing, sensor-data fusion, and movement-analysis pipelines on time-aligned EMG–IMU streams.

## References

[1] S. Rota, B. Morel, D. Saboul, I. Rogowski, and C. Hautier, "Influence of fatigue on upper limb muscle activity and performance in tennis," *J. Electromyogr. Kinesiol.*, vol. 24, no. 1, pp. 90–97, Feb. 2014.

[2] S. S. Bangaru, C. Wang, and F. Aghazadeh, "Automated and continuous fatigue monitoring in construction workers using forearm EMG and IMU wearable sensors and recurrent neural network," *Sensors*, vol. 22, no. 24, art. no. 9729, 2022.

[3] Delsys Inc., "Trigno Wireless EMG System — Technical Specifications," Natick, MA, USA, 2024.

[4] Noraxon USA, "Ultium EMG Sensor System — Product Documentation," Scottsdale, AZ, USA, 2024.

[5] G. L. Cerone, A. Botter, and M. Gazzoni, "A modular, smart, and wearable system for high density sEMG detection," *IEEE Trans. Biomed. Eng.*, vol. 66, no. 12, pp. 3371–3380, Dec. 2019.

[6] E. Farago, D. MacIsaac, M. Suk, and A. D. C. Chan, "A review of techniques for surface electromyography signal quality analysis," *IEEE Rev. Biomed. Eng.*, vol. 16, pp. 494–511, 2023.

[7] K. Yang *et al.*, "E-textiles for sports and fitness sensing: Current state, challenges, and future opportunities," *Sensors*, vol. 24, no. 4, art. no. 1058, 2024.

[8] S. K. Lynn, C. M. Watkins, M. A. Wong, K. Balfany, and D. F. Feeney, "Validity and reliability of surface electromyography measurements from a wearable athlete performance system," *J. Sports Sci. Med.*, vol. 17, no. 2, pp. 205–215, 2018.

[9] J. Taborri *et al.*, "Sport biomechanics applications using inertial, force, and EMG sensors: A literature overview," *Appl. Bionics Biomech.*, vol. 2020, art. no. 2041549, 2020.

[10] M. Seong, G. Kim, D. Yeo *et al.*, "MultiSenseBadminton: Wearable sensor-based biomechanical dataset for evaluation of badminton performance," *Sci. Data*, vol. 11, art. no. 343, 2024.

[11] R. Wang, "Low-cost wearable kit and algorithms to predict and prevent muscle overuse injuries," poster, 102nd Annual Meeting, AAAS Pacific Division, University of San Diego, San Diego, CA, USA, June 17–20, 2024.

[12] Seeed Studio, "Grove – EMG Detector," product documentation. [Online]. Available: https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html (accessed May 2026).
