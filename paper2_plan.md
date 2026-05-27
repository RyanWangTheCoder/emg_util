# Paper 2: Extended Journal Version of ICPICS System Paper

**Status:** Planning — write after [ICPICS submission](icpics_paper_plan.md) is submitted
**Target:** **MDPI Sensors** (primary) or **IEEE JBHI** (alternative) — journal venues only
**Format:** 10–14 pages journal article (extended from 6-page ICPICS conference paper)
**Depends on:** ICPICS conference paper ([icpics_paper_plan.md](icpics_paper_plan.md)) submitted; Paper 1 (CNIB) submitted
**Last Updated:** 2026-05-16

> **Read this first if you're new to the plan stack:**
> This is the **journal extension** of the ICPICS conference paper. Per IEEE policy, a journal extension must add ~30–50% new material and cite the conference paper. The added material lives in this plan; the engineering core (firmware, BLE protocol, host pipeline) is shared with the ICPICS paper.
>
> **Why not BSN:** BSN is a conference. ICPICS → BSN would be conference→conference and would trip self-plagiarism rules. ICPICS → MDPI Sensors / IEEE JBHI is the standard conference→journal extension path.

---

## Working Title

*"A Field-Deployed BLE Wearable for Real-Time EMG-IMU Acquisition: Firmware, Self-Describing Protocol, Hybrid Timeline Reconstruction, and Cross-Platform Analysis"*

(Extended from the ICPICS conference title; emphasises the four added contributions: hybrid `abs_us` validation, Chaquopy parity, deeper field-failure characterisation, and multi-session validation timeline.)

Alternative titles:
- *"End-to-End Engineering of a Field-Deployable EMG-IMU Wearable: From Firmware to On-Device Mobile Analysis"*
- *"From Sensor to Insight on a Mid-Range Android: A Field-Validated $99 BLE Wearable for Tennis Biosignal Capture"*

---

## Why a journal extension (vs. just the conference paper)

The ICPICS conference paper presents the engineering core: firmware, BLE protocol, host pipeline, basic field validation, and the pogo-pin diagnosis. It's a **modest-but-honest** systems paper. A journal extension is justified when there is enough additional analysis depth and new measurement data to clear the IEEE 30–50% new-material bar:

1. **Hybrid `abs_us` ground-truth validation.** ICPICS describes the algorithm in one paragraph. The journal version validates it: reconstruction error vs. `host_rx_ms` ground truth across all BLE reconnection events recorded in the field session (count to be confirmed from runtime health logs; at minimum 1 between-run reconnect is visible in the CSV file structure), accuracy bounds, comparison against device-clock-only and host-clock-only baselines.
2. **Chaquopy dual-platform benchmark.** ICPICS drops Android entirely. The journal version is the first published characterisation of scipy/numpy biosignal MDF computation on mid-range Android — per-swing latency distribution, PC↔Android numerical parity, cold-start cost.
3. **Deeper field-failure characterisation.** ICPICS gives the pogo-pin ghost signal a paragraph; the journal version expands to a section: pre/post correlation distributions, ADC-mux charge-sharing model, before/after standard-deviation behaviour, generalisation to other multiplexed-ADC wearables.
4. **Multi-session field-validation timeline.** ICPICS reports aggregate metrics; the journal version adds a frame-level reliability timeline (Figure 7: frame count, CRC errors, reconnections over the 150+ min session).
5. **Expanded Related Work and Discussion.** Doubled depth, protocol comparison table, positioning vs. Cerone 2019 / Lynn 2018 / Yang 2024 / Taborri 2020.

The pogo-pin failure mode and ADC crosstalk ghost signal (r = 0.998) appear in neither prior wearable EMG papers nor general embedded literature — the journal is where it gets full treatment.

---

## Core Contributions

The journal version inherits the ICPICS contributions and adds three. Contributions 1–5 below are shared with [icpics_paper_plan.md](icpics_paper_plan.md) (condensed in the journal version, citing ICPICS); contributions 6–8 are NEW to the journal extension and constitute the ~30–50% new material.

### Shared with ICPICS (condensed in journal version)

1. **DMA-driven 2 kHz EMG acquisition** with 10× hardware oversampling and per-sample timestamp back-calculation, empirically validated to ±25 µs across 2.3 M samples.
2. **Self-describing BLE protocol** — IMU FSR codes embedded in every frame, validated across three firmware FSR revisions with zero host code changes.
3. **Dual-core FreeRTOS architecture** with explicit task-priority assignment, achieving zero-drop concurrent EMG (2 kHz) + IMU (200 Hz) streaming.
4. **Two-layer field-recovery mechanism**: device-side host watchdog + host-side `abs_us` reconnection handling.
5. **Field-failure documentation**: pogo-pin ADC charge-sharing ghost signal — ICPICS gives the diagnosis; journal expands to characterisation depth (see contribution 8).

### NEW in journal extension (~30–50% added material)

6. **Hybrid `abs_us` timeline reconstruction with ground-truth validation.** Two-case BLE reconnection algorithm (BLE-dropout vs. ESP32-reset) unified by one rule. **Validated against `host_rx_ms` ground truth** across the BLE reconnection events recorded in 150+ min of field data (count: at least 1 between-run reconnect from CSV structure; within-run re-subscriptions to be enumerated from runtime health logs); reconstruction error bounds derived; comparison against device-clock-only and host-clock-only alternatives. Generalisable to any BLE logger with `dev_us` + `host_rx_ms` columns.
7. **Cross-platform analysis pipeline with Chaquopy benchmark.** Same scipy/numpy `FatigueMonitor` running on PC (pandas) and Android (Chaquopy, pandas-free). **NEW measurements:** per-swing latency distribution across 626 swings (log0305) on mid-range Android (target hardware: \[device model TBD\]), MDF result agreement PC↔Android (Pearson r, mean abs error), cold-start cost. Demonstrates viability of community signal-processing libraries on mobile without rewriting in Java/Kotlin.
8. **Pogo-pin ghost signal characterisation.** Beyond the ICPICS one-paragraph diagnosis: quantified ghost amplitude vs. ENV amplitude across the pre-bypass session, ADC-mux charge-sharing model and order-of-magnitude derivation, before/after RAW-channel standard-deviation distributions, post-filter flatline behaviour, generalisation criteria for other multiplexed-ADC wearables.

> **Field validation** (ICPICS Section VII) is treated as **evaluation**, not a separate contribution, in both papers. The journal version adds Figure 7 (multi-session timeline) but does not promote it to a contribution-level claim.

---

## Target Venue

**Primary:** IEEE Body Sensor Networks (BSN) -- systems track, highly relevant audience  
**Alternative:** MDPI Sensors (open access, good fit for engineering systems papers)  
**Secondary:** IEEE Journal of Biomedical and Health Informatics (JBHI) -- if expanded to journal format  
**Format:** 6 pages (BSN) or 8 pages (MDPI journal short communication)

---

## Paper Structure (Proposed)

**Total target: ~6500 words body text** (10–14 pages MDPI Sensors / IEEE JBHI journal format with figures and references; ~2× the ICPICS conference paper).

> **Section labels:**
> [SHARED] = condensed from ICPICS, citing the conference paper; kept short.
> [EXPANDED] = appears in ICPICS but substantially deeper here (more analysis, more measurements).
> [NEW] = new in journal extension; constitutes the ~30–50% added material per IEEE policy.

### 1. Introduction (~400 words) [EXPANDED]
- Same motivation as ICPICS, but contribution list expanded to include the 3 new contributions (#6 `abs_us` validation, #7 Chaquopy benchmark, #8 ghost signal characterisation)
- Add explicit sentence: "An earlier version of the firmware and BLE protocol design appeared in [ICPICS reference]; this journal version extends that work with ground-truth validation of the timeline reconstruction algorithm, a cross-platform analysis benchmark on Android, and quantitative characterisation of the pogo-pin ADC charge-sharing failure."

### 2. Related Work (~500 words) [EXPANDED]
- Commercial wearable EMG: Delsys Trigno, Noraxon -- gold standard but $5k-$30k; inaccessible for field/youth sport
- Low-cost wearable EMG systems: Cerone et al. 2019 (modular HD-sEMG), Lynn et al. 2018 (Athos validation), Yang et al. 2024 (e-textiles) -- focus on electrode design, not capture pipeline robustness
- IMU-EMG fusion platforms: Taborri et al. 2020 (overview), MultiSenseBadminton 2024 -- focus on data collection, not protocol/firmware engineering
- BLE wearable systems: most papers describe data collected, not the firmware/protocol that collected it; reconnection robustness, timestamp accuracy, and multi-session stitching are rarely documented
- **Cross-platform mobile biosignal pipelines:** Java/Kotlin reimplementations are typical; Chaquopy-based scipy/numpy on Android is uncommon — survey of prior work and what's missing
- **Multi-clock timestamp reconstruction:** prior approaches (device-clock-only, host-clock-only, NTP-style sync); position `abs_us` against these
- **Gap:** Few published works document the full stack from firmware DMA design through BLE protocol to *validated cross-platform* analysis pipeline with ground-truth timeline accuracy bounds.

### 3. Hardware Design (~300 words) [SHARED — condensed, citing ICPICS]
- Component selection rationale, BOM, pin mapping
- Critical hardware failure and fix mentioned briefly here; full characterisation moved to § 9 (NEW section)

### 4. Firmware Architecture (~400 words) [SHARED — condensed, citing ICPICS]
- Dual-core split, ADC DMA, synchronisation, watchdog, power budget — same as ICPICS

### 5. BLE Protocol (~300 words) [SHARED — condensed, citing ICPICS]
- Frame structure, TLV types, self-describing FSR, timestamp design

### 6. Host Capture Pipeline (~300 words) [SHARED — condensed, citing ICPICS]
- BLE central, FrameParser, rotating CSV, watchdog/reconnect, UDP mirror

### 7. Hybrid `abs_us` Timeline Reconstruction (~700 words) [NEW]
- Algorithm description in detail (mentioned briefly in ICPICS § VI; here it's a full section)
- Two-case unification: BLE-dropout vs. ESP32-reset, and why one rule handles both
- **Validation against `host_rx_ms` ground truth:** for each BLE reconnection event recorded in the field session (1 between-run reconnect verified from CSVs; within-run re-subscriptions to be counted from runtime health logs), compute reconstruction error vs. host-clock reference; report distribution, max, p95, p99
- **Comparison against alternatives:** device-clock-only (fails on ESP32 reset), host-clock-only (sub-millisecond resolution + system-clock NTP jitter), `abs_us` hybrid (best of both)
- Generalisation: any BLE logger with `dev_us` + `host_rx_ms` columns can apply the same approach
- Limitations: ESP32 reboot detected indirectly (sequence reset); no explicit reset signal in current protocol — future protocol revision recommendation

### 8. Cross-Platform Analysis Pipeline (~700 words) [NEW]
- Three-tier architecture: real-time Tier 1 (`fatigue_monitor.py` + Android `realtime_bridge.py` / PC `sensordata_plotter.py`), post-capture Tier 2, offline Tier 3
- Same `FatigueMonitor` core (canonical, pandas-free) running on PC and Android via Chaquopy
- Brief mention of preprocessing: detrend → bandpass(50–450 Hz) → notch → Welch — but defer details to Paper 1 / cite
- Swing detection: 300 dps threshold + 2000 ms debounce
- **Chaquopy benchmark (NEW measurements required):**
  - Per-swing latency distribution across 626 swings (log0305) on target Android hardware
  - Decomposition: JNI overhead + filtfilt + Welch PSD
  - PC↔Android numerical parity: Pearson r and mean abs error of MDF values
  - Cold-start cost (first import + warmup)
- Discussion: when does Chaquopy work? Acceptable latency budget for post-trigger fatigue display; not for per-sample real-time

### 9. Pogo-Pin Ghost Signal Characterisation (~600 words) [NEW]
- ICPICS gives this one paragraph; here it's a full section with the figure and quantitative analysis
- Pre-bypass observation: r = 0.998 ENV↔RAW correlation, ~37–44% amplitude ratio
- ADC-mux charge-sharing model: S/H capacitor C_sh, parasitic floating-pin capacitance C_par, ratio analysis
- Before/after RAW-channel standard deviation: pre-bypass < 5 ADC counts; post-bypass > 100 ADC counts during contraction
- Post-filter behaviour: ghost signal flatlines after 50 Hz high-pass — silent but complete data loss in offline analysis
- Generalisation: criteria for other multiplexed-ADC wearables to check for the same failure mode (any floating ADC channel adjacent to an actively driven channel)
- Detection heuristic: r(ENV, RAW) > 0.95 with σ(RAW) < 5 counts is diagnostic

### 10. Field Validation (~500 words) [EXPANDED]
- Two sessions: log0303 (87.9 min, 197 swings, 2 BLE connections), log0305 (63.1 min, 626 swings, 1 connection)
- Reliability metrics: zero detected sample drops during active streaming, CRC error rate <0.01%, BLE reconnection events handled without file corruption (1 between-run reconnect from CSV evidence; full count from runtime health logs)
- IMU FSR self-description: 250→1000→2000 dps progression handled by host parser without code changes
- **NEW: multi-session reliability timeline (Figure 7)**: frame count, CRC errors, reconnection events plotted over the 150+ min session
- **NEW: end-to-end timeline reconstruction validation:** the 66-min reconnection gap in log0303 is the natural ground-truth check for `abs_us` (combines § 7 method with § 10 data)
- Scientific output cross-reference: Paper 1 results confirm pipeline fidelity end-to-end

### 11. Discussion (~500 words) [EXPANDED]
- Generalisability: pogo-pin ghost signal applies to any multiplexed-ADC + spring-contact wearable
- `abs_us` portability: applies to any BLE logger with paired device and host clocks
- Chaquopy trade-off analysis: when scipy/numpy on Android is the right call vs. when Java/Kotlin reimplementation pays off
- Limitations: single sport; BLE 4.2 throughput near capacity; single-device test for Chaquopy benchmark; no formal worst-case latency bound proof
- Future work: AD5933 impedance monitoring, dynamic sample-rate negotiation, multi-device sync, adding GPS

### 12. Conclusion (~200 words)
- Recap 5 ICPICS contributions + 3 journal extensions
- Open-source release pointers (firmware repo, Python pipeline repo, hardware schematics)

---

## Figures Needed

| # | Figure | Status | Content |
|---|--------|--------|---------|
| 1 | System block diagram | [SHARED] from ICPICS | Sensor → firmware → BLE → btCentral → CSV → analysis → results |
| 2 | Inter-sample interval distribution | [SHARED] from ICPICS | Per-sample timing accuracy (±25 µs over 2.3 M samples) |
| 3 | Binary frame structure | [SHARED] from ICPICS | TLV layout with field sizes |
| 4 | Pogo-pin ghost signal diagnosis | [SHARED] from ICPICS, expanded | RAW vs ENV pre-bypass (r=0.998), post-filter flatline; in journal: add quantitative ghost amplitude vs ENV amplitude scatter |
| 5 | `abs_us` stitching diagram + validation | [NEW] | Two BLE connections with gap, showing dev_us / host_rx_ms / abs_us reconstruction; **ground-truth error distribution overlay** for all BLE reconnection events recorded in the field session |
| 6 | Chaquopy per-swing latency distribution | [NEW] | Histogram across 626 swings; decomposition (JNI + filtfilt + Welch); annotated mean/p95/p99 |
| 7 | Field validation: session timeline | [NEW] | Frame count, CRC errors, reconnection events over 150+ min — multi-track timeline |

---

## Tables Needed

| # | Table | Status | Content |
|---|-------|--------|---------|
| 1 | Hardware BOM | [SHARED] from ICPICS | Component, part number, cost (~$99 total) |
| 2 | Inter-sample interval statistics | [SHARED] from ICPICS | p50/p95/p99/within-±25 µs |
| 3 | IMU FSR history | [SHARED] from ICPICS | Session, FSR setting, saturation events, scale factor |
| 4 | Field validation metrics summary | [SHARED] from ICPICS | Sessions, duration, swings, BLE reconnections, CRC errors, sample drops |
| 5 | Protocol comparison | [NEW] | Binary TLV vs JSON vs CSV: bytes/sample, parse overhead, extensibility |
| 6 | `abs_us` reconstruction error | [NEW] | Per-reconnection: dev_us-only error, host-only error, abs_us error vs host_rx_ms ground truth |
| 7 | Chaquopy benchmark | [NEW] | Per-swing latency stats (mean, p50, p95, p99); cold-start cost; PC↔Android MDF parity (Pearson r, MAE) |

---

## Relationship to ICPICS conference paper and Paper 1

| Aspect | Paper 1 (CNIB) | ICPICS conference paper | This journal extension |
|--------|----------------|--------------------------|--------------------------|
| Primary contribution | Electrode settling characterisation + IMU quality validation | Engineering core: firmware + BLE + PC pipeline + pogo-pin diagnosis | ICPICS contributions + `abs_us` validation + Chaquopy benchmark + ghost-signal characterisation depth |
| Data used | log0303, log0305 | Same sessions (basic field validation) | Same sessions (with new ground-truth analysis on all BLE reconnection events) |
| Reader | Biomedical / sports science | Embedded systems / wearable engineering practitioners | Same as ICPICS, plus mobile-biosignal-pipeline and timeline-reconstruction researchers |
| Venue | EMBC (student/biomedical track) | ICPICS (systems track) | **MDPI Sensors (primary)** or **IEEE JBHI** |
| Status | Write first | Write second | Write third (after ICPICS submission) |
| New material vs. ICPICS | n/a | n/a | ~30–50% (per IEEE policy) — primarily §§ 7, 8, 9 (`abs_us` validation, Chaquopy benchmark, ghost-signal characterisation) |

This journal version cites the ICPICS paper for the engineering core; ICPICS sections (3–6) are condensed here, citing ICPICS rather than duplicating the content. Paper 1 remains a separate biomedical paper; the journal version cites Paper 1 for the scientific findings.

---

## Next Steps

> Ordered to reflect ICPICS-first strategy. Items marked [NEEDS NEW EXPERIMENTS] are blocking for the journal version but not for ICPICS.

1. [ ] Submit Paper 1 (CNIB) — independent track
2. [ ] Submit ICPICS conference paper — see [icpics_paper_plan.md](icpics_paper_plan.md) action list
3. [ ] [NEEDS NEW EXPERIMENTS] **Chaquopy benchmark on Android** (target hardware: \[device model TBD\]):
   - Run `analysis_bridge.process_session_compat()` over log0305 (626 swings) on device
   - Capture per-swing latency distribution; decompose JNI / filtfilt / Welch contributions
   - Compute MDF agreement vs. PC (Pearson r, MAE)
   - Capture cold-start cost (first import + first swing)
   - Output: data + Figure 6 + Table 7
4. [ ] [NEEDS NEW EXPERIMENTS] **`abs_us` ground-truth validation:**
   - For each BLE reconnection event in the field session (1 between-run from CSVs; within-run re-subscriptions from runtime health logs): compute reconstruction error vs `host_rx_ms` ground truth
   - Quantify error distribution, max, p95, p99
   - Compare against device-clock-only and host-clock-only baselines
   - Output: data + Figure 5 + Table 6
5. [ ] [NEEDS NEW EXPERIMENTS] **Pogo-pin ghost signal characterisation depth:**
   - Quantitative ghost amplitude vs ENV amplitude scatter from log0303 pre-bypass data
   - Before/after RAW-channel std distribution
   - ADC-mux charge-sharing model (analytical, not empirical)
   - Output: figure overlay on Figure 4 + § 9 prose
6. [ ] **Multi-session timeline plot (Figure 7):** frame count, CRC errors, reconnection events over 150+ min
7. [ ] Write `abs_us` section (§ 7) drawing from `capture_loader.load_session_stitched()` source
8. [ ] Write Chaquopy section (§ 8) drawing from `btLeApp/.../python/analysis_bridge.py` source
9. [ ] Write ghost-signal characterisation section (§ 9) drawing from `myoware_imu_v2/HARDWARE.md` and `arduino/py_scripts/PROTOCOL.md`
10. [ ] Expand Related Work section (§ 2) with cross-platform mobile biosignal and multi-clock-timestamp positioning
11. [ ] Expand Discussion section (§ 11) with generalisation criteria and limitations
12. [ ] Open-source the firmware and Python pipeline (GitHub repo) before submission

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

### Hardware Bench / New-Session Experiments

#### H1. Electrode Impedance Measurement
Near-term: handheld LCR meter (or multimeter @ 1 kHz) at t=0,5,10,15,20,30 min during one
active forearm session. Record electrode-skin impedance on all three snap contacts at each
time point. Goal: replace the indirect MDF/RMS settling inference with a direct impedance
curve to confirm the 17–20 min settling window. Compare slope against literature dry-electrode
curves (Joutsen 2024, Ravichandran 2023).
Paper 2: AD5933 chip on ESP32 I2C bus for automatic per-sample impedance logging.

#### H2. Gel vs. No-Gel Comparative Session
One paired session: snap electrodes applied with standard EMG gel (e.g., Signa Spray or
conductive gel pad) and standard skin prep (light abrasion), same forearm placement,
same exercise protocol as log0305. Run the full analysis pipeline and compare:
- Phase I settling duration (expected: shorter or absent with gel)
- Baseline MDF level (expected: higher with gel due to lower impedance)
- Warmup-skip sensitivity curve (expected: 5–10 min skip sufficient with gel)
- Contact quality metric trajectory

This directly validates the no-gel Phase I claim: if gel eliminates Phase I, it confirms
dry-electrode contact dynamics as the cause, not physiology. If Phase I persists with gel,
it suggests the settling is partly physiological (Ag/AgCl equilibration, not just impedance).
Value: converts the journal limitation ("no gel comparison") into a controlled confirmation.

#### H3. Pogo-Pin Ghost Signal Bench Characterisation
From log0303 pre-bypass data: quantitative ghost amplitude vs. ENV amplitude scatter,
before/after RAW-channel std distribution, ADC-mux charge-sharing analytical model.
Needed for journal §9 ghost-signal section depth (paper2_plan.md Next Step 5).

---

## Paper 1 Scope Boundary (what NOT to include in CNIB submission)

- Firmware architecture internals (dual-core, mutex details) — Paper 2
- Android/Chaquopy implementation — Paper 2
- Detailed BLE protocol (TLV format, CRC) — one sentence in Paper 1 max
- Pogo-pin ghost signal — one sentence for signal validity in Paper 1 max
- E-series impact-gating algorithms — one future-work sentence in Paper 1 max
- Audio/acoustic validation (E7) — Paper 2 or future
- Adaptive settling endpoint (Exp 9 null result) — one future-work sentence in Paper 1
