---
title: "Field Validity of Wearable sEMG Fatigue Metrics in Tennis: Electrode Settling, Contact Quality, and IMU-Conditioned Interpretation"
author:
  - name: "[First Author]"
    affiliation: "[Institution]"
  - name: "[Second Author]"
    affiliation: "[Institution]"
date: "2026"
abstract: |
  Wearable surface electromyography (sEMG) is promising for monitoring muscle fatigue in sports,
  but in real tennis play the EMG signal can be distorted by electrode settling, changing contact
  quality, motion artifacts, and wireless session discontinuities. Objective local fatigue monitoring
  may complement subjective perception by enabling session-to-session workload tracking and future
  overuse-risk assessment, but only if the underlying sEMG fatigue metrics are valid under field
  conditions. This work studies the field validity of no-added-gel forearm sEMG fatigue metrics
  using a low-cost EMG-IMU wearable system. Rather than treating IMU and EMG as conventionally
  fused features, we introduce an IMU-conditioned EMG validity framework, where the forearm IMU
  serves as an independent biomechanical context channel. In a 63-min continuous tennis session
  with 626 detected swings, MDF exhibited a three-phase trajectory: early suppression during
  electrode settling (115.7 ± 33.5 Hz), mid-session recovery to a settled reference
  (167.6 ± 50.1 Hz), and late-session decline (149.5 ± 45.1 Hz) consistent with local
  forearm fatigue. Warmup-skip sensitivity showed baseline selection is a first-order determinant:
  a 10-min skip produced -2.6% MDF change while a 20-min skip revealed a 28.1% MDF decline and
  17.3% MNF decline. IMU peak gyro magnitude remained stable (r = +0.029, p = 0.468), suggesting
  the decline was not explained by reduced gross swing motion. A second session exposed a
  continuity failure: an apparent 28.7% MDF drop was caused by a 66-min BLE reconnection gap,
  while the first continuous segment alone showed only 4.9%. These findings show that field sEMG
  fatigue monitoring requires a trustworthiness-first analysis approach.
keywords: [surface EMG, fatigue monitoring, electrode settling, IMU, wearable sensors, tennis]
---

## 1. Introduction

Surface electromyography (sEMG) can quantify local muscle fatigue through spectral metrics such as median frequency (MDF) and mean frequency (MNF), which shift toward lower values as conduction velocity decreases with metabolite accumulation. Tennis players can often perceive general tiredness, but subjective perception is not a quantitative, muscle-specific measure of local fatigue. Objective EMG monitoring may complement perception by enabling session-to-session workload tracking and future overuse-risk assessment — upper-extremity tennis injuries are frequently chronic and repetitive, and lateral elbow tendinopathy is associated with repeated forearm muscle loading [1]. However, a player may maintain swing speed through compensation even as local forearm muscle physiology changes, making external kinematics an insufficient proxy.

Prior EMG fatigue studies in tennis used controlled laboratory conditions with gel electrodes and skin abrasion [2,3,4]. In real court deployment, gel and abrasion are impractical: gel smears during play and affects racket grip, and players resist pre-session preparation. This study intentionally evaluates a no-added-gel, field-deployable configuration, following the standard for wearable sports deployment [5]. In this setting, electrode-skin impedance starts high and decreases over time as sweat hydrates the interface — a process that can take substantially longer than the 5–10 min warmup skip commonly assumed in laboratory analyses.

Existing IMU–EMG wearable studies typically fuse both modalities as feature sources for activity or fatigue classification [6,7]. In contrast, this work uses the IMU as an **independent biomechanical context sensor** for EMG validity assessment. Because tennis swings generate repeatable forearm kinematic signatures, stable IMU swing intensity provides a reference: when EMG changes while IMU is stable, the cause — electrode settling, contact degradation, or local muscle fatigue — can be inferred from temporal context.

The contributions of this work are: (C1) field characterization of electrode settling (≥17–20 min in no-gel tennis); (C2) warmup-skip sensitivity as a required robustness audit; (C3) contact-quality-aware EMG interpretation; (C4) IMU-conditioned EMG validity framework; (C5) session-gap artifact detection in wearable fatigue analysis.

## 2. System Design

**Hardware.** The system uses a MyoWare 2.0 muscle sensor (2000 Hz, 12-bit ADC, ENV + RAW dual outputs), ICM-20948 IMU (200 Hz, ±2000 dps / ±8g), and ESP32 MCU with BLE streaming — approximately $99 total. The RAW signal (required for spectral analysis) is routed via a direct solder bypass from the MyoWare PTH pad to ESP32 GPIO 32, correcting a field-discovered pogo-pin routing failure that produced a ghost signal indistinguishable by eye but flatlined after preprocessing. REF electrode was placed over the lateral epicondyle (bony prominence, opposite side of forearm from flexors), consistent with vendor guidance [8]. ADC DMA at 40 kHz with 10× oversampling yields ±25 µs timestamp accuracy at 2000 Hz.

**Software pipeline.** `btCentral.py` (BLE central, Python/Bleak) streams binary TLV frames to rotating CSV logs. `capture_loader.py` reconstructs a hybrid `abs_us` timeline — using device timestamps within each BLE connection and host receive-time gaps between reconnections — enabling correct detection of session discontinuities. `emg_util_yaml_runner.py` performs per-swing MDF/MNF/RMS feature extraction.

**Swing detection.** Fixed 300 dps gyro magnitude threshold with 2000 ms debounce. Z-score adaptive approaches failed because forearm gyro distributions during tennis are continuous ramps with no natural valley between general movement and swings. The 300 dps threshold sits at the 88th percentile of the session distribution, cleanly separating swing peaks.

## 3. Methods

**Electrode preparation.** Gel and skin preparation are standard in laboratory EMG [5] but were not used. This study intentionally evaluates a no-added-gel, field-deployable configuration, motivating the characterisation of dry-electrode settling under field conditions.

**Physical basis of settling.** When a dry snap electrode is applied to unabraded skin, the interface presents high impedance (10–100 kΩ). Two processes reduce it: (1) sweat accumulation — eccrine glands produce saline that hydrates the electrode-skin gap; (2) Ag/AgCl half-cell equilibration — the electrode potential drifts toward equilibrium with the local electrolyte. During settling, the unstable high-impedance interface degrades common-mode rejection and increases low-frequency-dominant contamination near the lower part of the 50–450 Hz analysis band, pulling MDF downward.

**IMU-conditioned EMG interpretation framework.** We define Table 1 to distinguish EMG spectral changes by their IMU/session context. The diagnostic value arises from modality mismatch: when IMU swing intensity remains stable but EMG spectral metrics change, the change is unlikely to be caused by reduced gross swing motion.

**Table 1.** IMU-conditioned interpretation of EMG spectral changes.

| IMU / session context | EMG observation | Likely interpretation |
|:---|:---|:---|
| Stable swing intensity | Early low MDF recovering upward | Electrode settling / contact hydration |
| Stable swing intensity | Gradual post-settling MDF/MNF decline | Fatigue-consistent spectral shift |
| Declining swing intensity | MDF decline | Reduced effort may contribute |
| Large IMU shock/vibration | Isolated EMG spectral outlier | Candidate mechanical artifact |
| BLE/session discontinuity | EMG baseline shift | Cross-segment artifact |

**Warmup-skip sensitivity analysis.** The analysis was re-run with warmup exclusion windows of 10, 15, and 20 min to quantify how baseline selection affects the fatigue conclusion. The 20-min skip is the primary result; warmup-skip sensitivity is reported as a robustness audit.

**Contact quality.** `contact_quality(t) = RMS(t) / session_p90_rms` — used as a qualitative relative indicator; not validated against direct impedance.

**Sessions.** log0305: 63 min, 626 swings, single continuous BLE connection. log0303: 88 min, 197 swings, two BLE connections with a 66-min reconnection gap.

## 4. Results

### 4.1 Three-Phase MDF Trajectory

Figure 2 shows the central empirical finding: a three-phase MDF trajectory rather than a simple monotonic decline.

![Figure 2. Three-phase MDF trajectory in log0305. Panel A: full-session MDF with three shaded phases — Phase I (settling, 0–18 min), Phase II (stable reference, 18–38 min), Phase III (fatigue-consistent, 38–63 min). Warmup markers at 10/15/20 min shown. Panel B: phase mean ± std bar chart. Panel C: IMU flat across all phases (r = +0.029, p = 0.468). IMU peak magnitude is a kinematic proxy, not a direct force measurement.](paper_figures/fig2_electrode_settling.png)

Phase I (settling): MDF 115.7 ± 33.5 Hz — substantially below the settled reference. Phase II (reference): MDF 167.6 ± 50.1 Hz — post-settling stable baseline. Phase III (fatigue-consistent): MDF 149.5 ± 45.1 Hz — decline after the settled reference. **The critical observation: early and late low-MDF regions have different causes.** Early suppression reflects contact settling — MDF subsequently recovered while IMU swing intensity remained stable, consistent with electrode contact improvement rather than physiological fatigue. Late decline occurs after the settled reference and is fatigue-consistent.

### 4.2 Warmup-Skip Sensitivity

Figure 3 shows that the same session gives completely different fatigue conclusions depending on warmup exclusion.

![Figure 3. Warmup-skip sensitivity. Left: baseline MDF per skip condition vs. stable settled reference (166 Hz). Right: MDF drop % per condition. Positive = MDF declined (fatigue-consistent); negative = inverted/missed.](paper_figures/fig4_warmup_skip_sensitivity.png)

A 10-min skip produces −2.6% MDF change (fatigue-consistent decline missed entirely). A 15-min skip produces −26.2% (inverted — baseline still in settling). A 20-min skip reveals +28.1% MDF decline and +17.3% MNF decline. The non-monotone behaviour (15-min worse than 10-min) reflects the RMS-based baseline selector catching swings from the steepest part of the settling transition. These results demonstrate that warmup-skip sensitivity analysis is a necessary robustness audit for no-gel field sEMG fatigue studies.

### 4.3 IMU-Conditioned Validity

Figure 4 shows the IMU–EMG diagnostic matrix, the visual proof of IMU-conditioned validity.

![Figure 4. IMU–EMG diagnostic matrix (log0305). IMU peak gyro magnitude (x-axis, kinematic proxy) vs. MDF (y-axis) for all 626 swings, coloured by session third. Early and Late swings cluster at lower MDF than Mid despite similar IMU intensity. IMU peak magnitude remained flat (r = +0.029, p = 0.468). IMU is a kinematic proxy, not a direct force measurement.](paper_figures/fig7_imu_emg_diagnostic_matrix.png)

All three session thirds show similar IMU intensity, confirming that reduced gross swing kinematics is an unlikely explanation for either Phase I suppression or Phase III decline. The MDF changes are attributed to electrode contact evolution (Phase I) and fatigue-consistent spectral shift (Phase III), supported by the IMU context (Table 1, rows 1–2).

### 4.4 Session-Gap Artifact (log0303)

Figure 5 shows the log0303 continuity failure mode.

![Figure 5. log0303 gap artifact. Full session (orange): apparent 28.7% MDF drop. First continuous BLE segment alone (navy diamonds, 0–13.5 min): 4.9% change. A 66-min BLE reconnection gap separates the two segments (purple shading).](paper_figures/fig6_log0303_gap_artifact.png)

The full-session 28.7% MDF drop compares Segment 1 (fresh electrode) against Segment 2 (re-applied electrode, different contact state) across a 66-min gap. Segment 1 alone shows 4.9% — below any meaningful fatigue threshold for 13.5 min of play. Treating disconnected BLE recordings as continuous physiological sessions is a real wearable failure mode requiring continuity auditing.

## 5. Discussion

**Three-phase trajectory.** The MDF trajectory was not monotonic. Phase I (0–18 min) reflects electrode contact evolution, not fatigue — MDF subsequently recovered to Phase II while IMU swing intensity remained flat. Phase III (38–63 min) occurs after the settled reference and is fatigue-consistent. This three-phase pattern explains why both short warmup skips failed: 10 and 15 min fall inside Phase I, producing contaminated or inverted baselines.

**Practical recommendation.** Extend warmup skip to ≥20 min for no-gel forearm snap-electrode deployments in field tennis. Warmup-skip sensitivity should be reported as a standard robustness check in field sEMG fatigue studies — the same session changed from −2.6% to +28.1% MDF drop depending solely on this parameter.

**IMU as validity channel, not fusion feature.** The IMU contribution is not conventional feature fusion. Stable IMU intensity across all 626 swings (r = +0.029, p = 0.468) makes reduced gross swing kinematics an unlikely explanation for Phase I suppression or Phase III decline. The IMU adds zero hardware cost since it is already required for swing detection.

**Limitations.** Single player, two sessions (pilot case study); no MVC, RPE, grip-force, or ball-speed ground truth — findings are fatigue-consistent rather than physiologically confirmed; settling duration varies with sweat rate, ambient conditions, and electrode state; the 20-min skip is empirically selected for this session (not a universal threshold); per-swing statistics are descriptive rather than population-level inference; contact quality not validated against direct impedance.

**Future work.** Multi-player study with RPE integration and MVC validation; adaptive warmup skip calibrated across sessions; multi-session workload monitoring toward overuse-risk assessment.

## 6. Conclusion

The key observation is not simply that MDF decreased, but that MDF first recovered from early contact-induced suppression before declining later — a three-phase trajectory separating electrode settling from fatigue-consistent spectral change. In no-gel field tennis sEMG, the same session changed from −2.6% to +28.1% MDF drop depending only on the warmup exclusion window, demonstrating that baseline selection is a first-order determinant of fatigue interpretation. The onboard IMU, as an independent kinematic context channel, provides a zero-cost reference for EMG validity assessment. A second session demonstrated that a 66-min BLE reconnection gap created an apparent 28.7% fatigue signal that disappeared to 4.9% for the first continuous segment. These findings establish a trustworthiness-first framework for wearable sEMG fatigue monitoring in field sports deployment.

## References

1. American Academy of Orthopaedic Surgeons. Tennis Elbow (Lateral Epicondylitis). OrthoInfo. 2023.
2. Rota S, Morel B, Saboul D, Rogowski I, Hautier C. Influence of fatigue on upper limb muscle activity and performance in tennis. J Electromyogr Kinesiol. 2014;24(1):90–97.
3. Wang LH, Lo KC, Su FC. Skill level and forearm muscle fatigue effects on ball speed in tennis serve. Sports Biomechanics. 2019;18(5):566–579.
4. Girard O, Racinais S, Micallef JP, Millet GP. Spinal modulations accompany peripheral fatigue during prolonged tennis. Scand J Med Sci Sports. 2011;21(3):455–464.
5. Hermens HJ, Freriks B, Disselhorst-Klug C, Rau G. Development of recommendations for SEMG sensors and sensor placement procedures. J Electromyogr Kinesiol. 2000;10(5):361–374.
6. Taborri J, Keogh J, Kos A, et al. Sport biomechanics applications using inertial, force, and EMG sensors: A literature overview. Appl Bionics Biomech. 2020;2020:2041549.
7. Bangaru SS, Wang C, Aghazadeh F. Automated and continuous fatigue monitoring using forearm EMG and IMU sensors and recurrent neural network. Sensors. 2022;22(21):8217.
8. SparkFun Electronics. MyoWare 2.0 Muscle Sensor Advanced Guide. 2023.
9. Joutsen A, Cömert A, Kaappa E, et al. ECG signal quality in intermittent long-term dry electrode recordings. Sci Rep. 2024;14:8936.
10. Boyer M, Bouyer L, Roy JS, Campeau-Lecours A. Reducing noise, artifacts and interference in single-channel EMG signals: a review. Sensors. 2023;23(6):2927.
11. Rigozzi CJ, Vio GA, Poronnik P. Grip strength, forearm muscle activity, and shock transmission in the forehand stroke of experienced and recreational tennis players. Sensors. 2023;23(11):5146.
12. Fabre JB, Martin V, Gondin J, Cottin F, Grelot L. Effect of playing surface on neuromuscular fatigue in tennis. Med Sci Sports Exerc. 2012;44(1):75–83.
13. Seong H, et al. MultiSenseBadminton: wearable sensor-based biomechanical dataset for evaluation of badminton performance. Sci Data. 2024;11:329.
14. Ravichandran V, et al. Characterizing the impedance properties of dry e-textile electrodes based on contact force and perspiration. Biosensors. 2023;13(2):217.
15. Farago E, MacIsaac D, Suk M, et al. A review of techniques for surface electromyography signal quality analysis. IEEE Rev Biomed Eng. 2022;16:494–511.

