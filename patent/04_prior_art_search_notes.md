# Prior Art Search Notes
## Patent: Reliability-Gated Wearable EMG Monitoring Using RAW/ENV/IMU Consistency

> A full patentability search is not required for a provisional filing, but this document records known prior art, categorizes risk by claim family, and captures the differentiating arguments. Review with counsel before filing the nonprovisional.

---

## 1. Known References (from ICPICS and CNIB papers)

### Signal Quality Assessment
| Ref | Citation | Relevance to Patent | Risk Level |
|-----|----------|---------------------|------------|
| Farago 2023 | E. Farago et al., "A review of techniques for surface electromyography signal quality analysis," *IEEE Rev. Biomed. Eng.*, vol. 16, pp. 494–511, 2023. | Reviews sEMG signal quality methods broadly; primarily laboratory-focused, impedance-based, or signal-level metrics | Medium — review paper, no system claim; does not address hardware ENV comparison or IMU validity context |
| Boyer 2023 | M. Boyer et al., "Reducing noise, artifacts and interference in single-channel EMG signals: a review," *Sensors*, 2023;23(6):2927. | Reviews artifact removal methods; does not address dual RAW/ENV channel consistency | Low — artifact removal, not validity gating |
| Ravichandran 2023 | V. Ravichandran et al., "Characterizing the impedance properties of dry e-textile electrodes based on contact force and perspiration," *Biosensors*, 2023;13(2):217. | Electrode contact impedance characterization; lab measurement, not runtime quality gating | Low — different modality (impedance), not RAW/ENV |

### EMG Fatigue and Sports
| Ref | Citation | Relevance to Patent | Risk Level |
|-----|----------|---------------------|------------|
| Rota 2014 | S. Rota et al., "Influence of fatigue on upper limb muscle activity and performance in tennis," *J. Electromyogr. Kinesiol.*, 2014;24(1):90–97. | Tennis EMG fatigue study; standard lab conditions, no field validity gating | Low — no signal quality or IMU validity framework |
| Fabre 2012 | J. B. Fabre et al., "Effect of playing surface on neuromuscular fatigue in tennis," *Med. Sci. Sports Exerc.*, 2012;44(1):75–83. | Tennis EMG fatigue; lab protocol | Low |
| Wang 2019 | L. H. Wang et al., "Skill level and forearm muscle fatigue effects on ball speed in tennis serve," *Sports Biomechanics*, 2019;18(5):566–579. | Forearm muscle fatigue in tennis; no wearable validity gating | Low |

### EMG + IMU Fusion and Wearable Systems
| Ref | Citation | Relevance to Patent | Risk Level |
|-----|----------|---------------------|------------|
| Bangaru 2022 | S. S. Bangaru et al., "Automated and continuous fatigue monitoring in construction workers using forearm EMG and IMU wearable sensors and recurrent neural network," *Sensors*, 2022;22(24):9729. | EMG + IMU fused for fatigue classification using RNN; IMU is a feature input, not a validity channel | Medium — EMG/IMU combination, but purpose is feature fusion not validity gating; no RAW/ENV comparison |
| Taborri 2020 | J. Taborri et al., "Sport biomechanics applications using inertial, force, and EMG sensors," *Appl. Bionics Biomech.*, 2020. | Survey of IMU+EMG sports applications; fusion-focused | Low — no validity gating |
| Cerone 2019 | G. L. Cerone et al., "A modular, smart, and wearable system for high density sEMG detection," *IEEE Trans. Biomed. Eng.*, 2019;66(12):3371–3380. | High-density sEMG wearable; acquisition focused, no dual-output quality check | Low |
| Lynn 2018 | S. K. Lynn et al., "Validity and reliability of surface electromyography measurements from a wearable athlete performance system," *J. Sports Sci. Med.*, 2018;17(2):205–215. | Wearable EMG validity study; focuses on test-retest reliability, not real-time signal quality gating | Low |
| Seong 2024 | M. Seong et al., "MultiSenseBadminton: wearable sensor-based biomechanical dataset for evaluation of badminton performance," *Sci. Data*, 2024;11:329. | Racket sport wearable dataset; acquisition focused | Low |

### Electrode Contact and Settling
| Ref | Citation | Relevance to Patent | Risk Level |
|-----|----------|---------------------|------------|
| Hermens 2000 | H. J. Hermens et al., "Development of recommendations for SEMG sensors and sensor placement procedures," *J. Electromyogr. Kinesiol.*, 2000;10(5):361–374. | SENIAM electrode placement standards; lab preparation standards, not runtime contact quality gating | Medium — establishes that electrode-skin contact matters, but proposes pre-session preparation rather than runtime detection |
| Joutsen 2024 | A. Joutsen et al., "ECG signal quality in intermittent long-term dry electrode recordings," *Sci. Rep.*, 2024;14:8936. | Dry electrode signal quality for ECG (not EMG); quality index for long-term recordings | Medium — closest to runtime quality detection concept, but ECG not EMG, no RAW/ENV hardware comparison, no IMU context |

### Commercial Systems
| Ref | Citation | Relevance to Patent | Risk Level |
|-----|----------|---------------------|------------|
| Delsys Trigno | Delsys Inc., "Trigno Wireless EMG System," 2024. | Commercial research-grade EMG/IMU; does not expose dual RAW/ENV hardware channel for consistency checking | Low — no RAW/ENV comparison, no public validity-gating architecture |
| Noraxon Ultium | Noraxon USA, "Ultium EMG Sensor System," 2024. | Commercial research-grade; similar to Delsys | Low |
| MyoWare 2.0 | SparkFun Electronics, "MyoWare 2.0 Muscle Sensor Advanced Guide," 2023. | Hardware sensor used in this invention; RAW and ENV outputs documented; does not describe validity-gating logic using those outputs | Low — hardware datasheet, not a system or method claim |

---

## 2. Risk Assessment by Claim Family

### Family A — RAW/ENV/IMU Signal-Quality Validity Gate

**Key novelty:** Using hardware ENV as a signal-quality channel (not just as the EMG signal); comparing RAW-derived features against hardware ENV; using IMU as an independent validity context (not feature fusion); classifying trustworthiness and gating downstream metrics.

**Closest prior art:** Farago 2023 (signal quality review), Joutsen 2024 (dry electrode quality index), Bangaru 2022 (EMG/IMU fusion).

**Differentiating argument:**
- Farago 2023 reviews signal quality methods but does not disclose a system that uses a *hardware envelope output* as the quality reference channel — existing methods use impedance, SNR thresholds, or statistical outlier detection on a single channel.
- Joutsen 2024 addresses dry-electrode ECG quality, not EMG, and does not compare a software-derived envelope against a hardware envelope channel.
- Bangaru 2022 fuses IMU features with EMG features for classification — IMU is a *co-input* to a fatigue classifier, not an independent *validity context* channel. This invention uses IMU to determine whether the EMG observation is interpretable, not to classify fatigue.
- No known prior art describes: simultaneously acquiring RAW + hardware ENV from the same EMG sensor; computing a software envelope from RAW; comparing the two to detect settling, saturation, flatline, or ghost coupling; and using IMU context to distinguish physiological change from artifact.

**Risk level: Low-Medium** — prior art covers individual components but not the integrated combination.

---

### Family B — Quality-Gated Baseline Selection

**Key novelty:** Baseline window accepted only when all quality conditions (RAW, ENV, IMU, continuity) are satisfied; settling-aware adaptive baseline.

**Closest prior art:** Hermens 2000 (electrode preparation standards), Rota 2014 / Fabre 2012 (EMG fatigue with warmup).

**Differentiating argument:**
- Hermens 2000 recommends pre-session electrode skin preparation to minimize settling but does not describe a runtime system that monitors settling and delays or rejects baseline computation accordingly.
- Standard EMG fatigue studies use a fixed warmup period (e.g., 5–10 min) as a heuristic, not a quality-conditioned gate. The warmup-skip sensitivity result (−2.6% to +28.1% depending on skip duration) demonstrates that fixed heuristics fail and motivates an adaptive, quality-gated approach.
- No known prior art describes a baseline selection gate conditioned on all of: RAW variance, ENV saturation, RAW/ENV consistency, contact quality, IMU stability, and session continuity simultaneously.

**Risk level: Low** — fixed warmup heuristics are well known but the quality-conditioned gate is not.

---

### Family C — Session Continuity / BLE Gap Validity Audit

**Key novelty:** Detect wireless gaps; assign segment IDs; prevent cross-gap fatigue comparisons; hybrid abs_us timeline.

**Closest prior art:** General BLE reliability literature; no specific EMG fatigue gap-artifact prior art identified.

**Differentiating argument:**
- No known prior art describes detecting BLE session discontinuities as a source of false fatigue conclusions and suppressing or segmenting longitudinal EMG fatigue analysis accordingly.
- The specific failure mode (66-min BLE gap producing 28.7% apparent MDF drop that disappears to 4.9% in the first segment alone) is a novel empirical demonstration of the problem and the solution.

**Risk level: Low** — this failure mode appears to be undocumented in prior art.

---

### Family D — Pogo-Pin / Ghost-Channel Diagnostic

**Key novelty:** Three-condition signature (high RAW/ENV correlation + near-zero RAW variance + post-filter flatline) for detecting floating ADC input or analog coupling.

**Closest prior art:** General ADC crosstalk literature; no EMG-specific ghost-channel diagnostic prior art identified.

**Differentiating argument:**
- The pogo-pin ghost-signal failure mode and its specific three-condition diagnostic signature are not described in any known prior art.
- General ADC crosstalk is known in electronics but the specific manifestation in wearable biosignal acquisition — where a floating input passively couples to a nearby analog envelope output, producing a pathologically high inter-channel correlation and a post-filter flatline — is not described in accessible prior art.

**Risk level: Low** — highly specific failure mode with a concrete diagnostic.

---

## 3. Search Areas Not Yet Covered

The following search areas from the patent plan have not been formally searched and should be completed before nonprovisional filing:

| Search category | Suggested query terms | Priority |
|----------------|----------------------|----------|
| sEMG signal quality index systems | "sEMG signal quality index" "wearable EMG artifact detection" "EMG contact quality real-time" | High |
| Hardware envelope + raw EMG comparison | "dual output EMG sensor quality" "EMG envelope raw comparison" "hardware envelope validity" | High |
| Floating ADC input / multiplexer crosstalk | "ADC multiplexer crosstalk biosignal" "floating ADC input EMG" "charge sharing wearable sensor" | Medium |
| EMG baseline selection / settling | "EMG fatigue baseline selection" "dry electrode settling time" "sEMG warmup period" | Medium |
| BLE / wireless biosignal gap artifact | "wearable BLE EMG discontinuity" "wireless biosignal reconnect artifact" "session gap EMG" | Medium |

Recommended search databases: Google Patents, USPTO Patent Full-Text Database, Espacenet (EPO), IEEE Xplore, PubMed.

---

## 4. Summary: Strongest Differentiators for Claims

1. **RAW/ENV as paired quality channels** — using the hardware envelope output of a dual-output EMG sensor as a quality reference, not as the EMG signal itself. Not described in prior art.
2. **IMU as validity context, not fusion feature** — IMU determines whether an EMG observation is physiologically interpretable, not what the EMG classification label is. Distinct from all known EMG/IMU fusion systems.
3. **Integrated trustworthiness gate** — the combination of RAW/ENV consistency + IMU context + session continuity → classification → downstream action. The individual components exist in prior art but the integrated gate does not.
4. **Ghost-channel three-condition diagnostic** — specific to the RAW/ENV paired acquisition architecture; not described elsewhere.
5. **Session-gap false-fatigue detection** — BLE reconnect gap as a source of false fatigue conclusions; suppression by segment-aware analysis. Not described in prior art.

---

*Last updated: 2026-06-01*
