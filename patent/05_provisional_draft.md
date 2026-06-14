# SYSTEMS AND METHODS FOR SIGNAL-QUALITY VALIDATION OF WEARABLE ELECTROMYOGRAPHY USING RAW/ENVELOPE CONSISTENCY AND INERTIAL CONTEXT

> Provisional patent application / invention disclosure working draft.  
> This document merges the primary provisional draft with the RAW/ENV/IMU signal-quality technical draft.  
> This is a technical drafting aid, not legal advice. A patent attorney should review before filing.

---

## 1. FIELD OF THE INVENTION

The present invention relates to wearable biosignal sensing and analysis, and more particularly to **systems and methods for validating signal quality in surface electromyography (sEMG) using combined electromyography and inertial sensing in dynamic field environments**.

In some embodiments, the invention relates to validating and improving wearable electromyography signal quality using concurrently acquired or time-aligned data streams, including:

1. a high-rate raw EMG channel;
2. a hardware-derived or low-rate EMG envelope channel; and
3. inertial measurement unit (IMU) data including acceleration and/or gyroscope measurements.

---

## 2. BACKGROUND

Surface electromyography (sEMG) is widely used to measure muscle activation and fatigue through features such as root mean square (RMS), median frequency (MDF), mean frequency (MNF), waveform length, zero crossings, and spectral power. In laboratory environments, these measurements often rely on controlled electrode preparation, gel or abrasive skin preparation, stable acquisition conditions, and controlled movement protocols.

However, in real-world field deployment—such as sports, rehabilitation, occupational monitoring, human-computer interaction, or prosthetic control—EMG signals are frequently degraded by multiple factors, including:

- electrode-skin contact instability and settling;
- dry or no-added-gel electrode impedance changes;
- motion artifacts due to limb movement, vibration, impact, or cable movement;
- signal drift and low signal-to-noise ratio (SNR);
- hardware limitations such as envelope saturation or clipping;
- raw signal channel failures, including flatline or floating input;
- ghost-channel coupling or ADC multiplexer charge-sharing artifacts;
- changes in movement intensity that confound physiological interpretation;
- wireless communication interruptions leading to session discontinuities.

Existing systems primarily focus on extracting EMG features or performing activity, gesture, workload, or fatigue classification. However, such approaches generally assume that the EMG signal is valid and do not explicitly determine whether the extracted features are trustworthy.

As a result, downstream interpretations—particularly fatigue estimation—can be incorrect or misleading. For example, a low-quality electrode contact period can distort baseline EMG spectral features, causing later valid muscle activity to be interpreted as an apparent negative fatigue trend. Similarly, a hardware envelope may saturate, a raw channel may flatline, or a wireless session discontinuity may cause a non-physiological baseline shift.

Accordingly, there is a need for a wearable EMG framework that evaluates whether EMG-derived metrics are trustworthy before interpreting them physiologically.

---

## 3. DEFINITIONS AND NON-LIMITING TERMINOLOGY

As used herein, **RAW** refers to a raw or substantially unprocessed electromyography waveform suitable for amplitude or spectral analysis. **ENV** refers to a hardware-derived, sensor-provided, analog-derived, digitized, or processor-derived envelope or amplitude channel corresponding to electromyography activity. **IMU context** refers to acceleration, gyroscope, jerk, movement intensity, impact, stability, stillness, or related motion information derived from an inertial measurement unit. A **trustworthiness state** refers to a classification, score, flag, label, or other output used to modify downstream interpretation of electromyography-derived metrics. These definitions are non-limiting; alternative terms with equivalent meanings may be used.

---

## 4. SUMMARY OF THE INVENTION

The present invention introduces a **reliability-gated framework for wearable EMG analysis**, in which EMG-derived metrics are conditioned on validated signal quality.

The system combines:

1. **Raw electromyography (RAW)** – high-frequency signal used for physiological analysis;
2. **Hardware envelope (ENV)** – amplitude signal reflecting sensor hardware behavior, envelope dynamics, contact conditions, and saturation;
3. **Inertial measurement unit (IMU)** – independent biomechanical context describing movement patterns.

Signal validity is determined using:

- consistency between RAW-derived features and hardware ENV;
- signal-quality metrics derived from RAW and ENV, including ratio, correlation, saturation, variance, flatline, and contact-quality measures;
- IMU-derived context for distinguishing physiological changes from movement-related artifacts, reduced effort, or impact events;
- session continuity information based on timestamps, sequence data, or connection boundaries.

Based on these inputs, the system determines a **signal trustworthiness state** and modifies downstream EMG interpretation accordingly, including:

- accepting or rejecting data segments;
- delaying or adjusting baseline estimation;
- down-weighting or suppressing unreliable features;
- segmenting analysis across discontinuities;
- producing confidence metrics, artifact labels, or user feedback.

In some embodiments, the system derives a software envelope from the raw EMG signal, compares the software envelope against the hardware envelope, identifies abnormal raw/envelope behavior, and uses IMU motion context to determine whether an EMG observation is likely due to valid muscle activity, contact change, settling, motion artifact, impact artifact, or reduced movement effort.

---

## 5. SYSTEM ARCHITECTURE

In one embodiment, the system comprises:

- a wearable EMG sensor providing:
  - raw EMG output (RAW);
  - hardware envelope output (ENV);
- an inertial measurement unit (IMU);
- a processing unit, which may be embedded, host-side, mobile, or cloud-based;
- a data communication interface, wired or wireless;
- a host or mobile device for analysis, display, alerting, or storage.

### 5.1 Functional Components

Functional components may include:

1. data acquisition module for RAW, ENV, and IMU;
2. timestamping or synchronization module;
3. signal processing module for feature extraction;
4. raw-derived envelope computation module;
5. RAW/ENV signal-quality evaluation module;
6. IMU context evaluation module;
7. validity classification module;
8. output modulation module for downstream interpretation;
9. alert or feedback module.

### 5.2 Representative Hardware Embodiment

A representative embodiment may include:

| Component | Purpose |
|---|---|
| Raw EMG input | High-rate EMG waveform for spectral and amplitude analysis |
| Hardware EMG envelope input | Low-rate or analog-integrated envelope for amplitude/contact context |
| IMU | Acceleration and gyroscope data for motion context |
| Microcontroller | Sampling, timestamping, packetization, optional real-time quality logic |
| BLE / wired / wireless transport | Streaming sensor data to a host or mobile device |
| Host / mobile processor | Signal-quality evaluation, fatigue monitoring, visualization, alerts |

One implemented project embodiment uses:

- MyoWare 2.0 EMG sensor with RAW and ENV outputs;
- ESP32 microcontroller;
- ICM-20948 IMU;
- BLE data streaming;
- host-side Python and/or Android analysis.

The invention is not limited to these components. Other EMG sensors, analog front ends, IMUs, wireless links, sampling rates, processors, or computing platforms may be used.

---

## 6. DATA STREAMS

### 6.1 Raw EMG Stream

The raw EMG stream may be sampled at a relatively high rate suitable for spectral analysis, for example:

- 1000 Hz;
- 2000 Hz;
- 4000 Hz;
- any rate sufficient to capture EMG frequency content.

The raw EMG stream may be used to compute:

- RMS;
- MAV;
- median frequency;
- mean frequency;
- zero crossings;
- waveform length;
- spectral power;
- software envelope;
- fatigue or activation metrics.

### 6.2 Hardware Envelope Stream

The hardware envelope stream may be produced by an analog rectifier/low-pass circuit, a sensor module, or an embedded processor. It may have a lower bandwidth than the raw EMG signal.

The hardware envelope stream may be used to compute:

- envelope mean;
- envelope maximum;
- envelope saturation count;
- envelope saturation percentage;
- envelope dynamic range;
- envelope-to-raw ratio;
- envelope consistency over time.

### 6.3 IMU Stream

The IMU stream may include:

- acceleration;
- gyroscope;
- magnetometer;
- derived acceleration magnitude;
- dynamic acceleration;
- gyroscope magnitude;
- jerk;
- impact markers;
- movement event peaks;
- stillness intervals.

The IMU stream provides an independent motion-context channel. It may be used for:

- activity gating;
- movement event detection;
- identifying high-motion or impact artifact risk;
- determining whether movement intensity is stable or changing;
- separating physiological EMG changes from reduced effort or changed biomechanics.

---

## 7. RAW-DERIVED ENVELOPE AND FEATURE COMPUTATION

In some embodiments, the system computes a software-derived envelope from RAW EMG by:

1. estimating or tracking a raw signal DC midpoint;
2. performing rectification relative to the DC midpoint;
3. applying low-pass filtering;
4. scaling or normalizing the resulting signal.

A representative method is:

```text
raw_dc(t) = slow_low_pass(raw(t))
raw_ac(t) = raw(t) - raw_dc(t)
env_sw(t) = low_pass(abs(raw_ac(t)))
```

In offline processing, the raw DC estimate may be:

```text
raw_dc = mean(raw over recording or selected segment)
```

In live processing, the raw DC estimate may be a slow low-pass filter, for example with a 0.1 Hz cutoff.

The software envelope may be scaled to the hardware envelope:

```text
scale = max(ENV_hw) / max(ENV_sw)
ENV_sw_scaled = ENV_sw * scale
```

The comparison may be qualitative or quantitative depending on calibration.

Additional RAW-derived features include:

- RMS over sliding windows;
- MAV;
- spectral metrics such as MDF and MNF;
- variance or standard deviation;
- peak-to-peak dynamic range;
- filtered raw RMS;
- band-limited power.

The software-derived envelope and raw-derived features are compared to the hardware envelope (ENV) to assess consistency and signal validity.

---

## 8. SIGNAL-QUALITY METRICS

Signal quality is evaluated using one or more metrics, including:

- RAW-derived RMS or amplitude;
- software-derived envelope from RAW;
- hardware ENV amplitude, mean, or maximum;
- RAW–ENV consistency metrics, including correlation, ratio, shape similarity, and timing similarity;
- RAW variance or flatline detection;
- ENV saturation count or percentage;
- contact-quality indicators based on normalized RMS;
- IMU-derived motion intensity or transient events;
- session continuity indicators based on timestamps or sequence data.

### 8.1 Amplitude Ratio

```text
raw_env_ratio = raw_rms / env_mean
```

or:

```text
raw_env_ratio = env_sw_scaled / env_hw
```

Uses include:

- detecting gain changes;
- detecting contact changes;
- detecting mismatch between raw and envelope behavior;
- detecting periods where envelope is no longer a reliable contact proxy.

### 8.2 Correlation

```text
corr(raw_rms, env_mean)
corr(env_sw, env_hw)
corr(raw, env)
```

Uses include:

- detecting ghost-channel coupling;
- detecting expected co-modulation;
- detecting abnormal channel dependence.

A very high raw-to-envelope correlation combined with very low raw variance may indicate that the raw channel is not measuring independent muscle activity but is instead tracking the envelope or another analog channel.

### 8.3 Saturation Count

```text
n_env_saturated = count(env_hw >= saturation_threshold)
pct_env_saturated = n_env_saturated / n_events
```

In one embodiment, `saturation_threshold` is set to 95% of the sensor's maximum ADC output range. A session with `pct_env_saturated` exceeding 10% may be flagged for reduced confidence; a session exceeding 20% may suppress envelope-derived quality metrics entirely. In experimental field sessions, observed values ranged from 1.4% (low-load session, log0305) to 14.2% (high-load session, log0303).

Uses include:

- detecting hardware-envelope clipping;
- reducing confidence in envelope-derived contact or activation metrics;
- flagging sessions where envelope data cannot be used as a reliable quality proxy.

### 8.4 Raw Flatline Detection

```text
raw_variance < flatline_threshold
```

or:

```text
raw_rms < minimum_activity_threshold during movement events
```

In one embodiment, `flatline_threshold` is set to 1% of the expected raw EMG variance during active muscle contraction (e.g., variance < 1e-5 V² for a 12-bit ADC system sampling at 2 kHz). `minimum_activity_threshold` may be set to 2% of the session 90th-percentile RMS. A ghost-channel failure example exhibited near-zero raw variance with Pearson r = 0.998 between raw and ENV; post-repair r dropped to −0.013.

Uses include:

- detecting disconnected electrodes;
- detecting failed raw input;
- detecting post-filter flatline;
- detecting dead channels.

### 8.5 Raw Variance / Dynamic Range

```text
raw_sd = standard_deviation(raw within window)
raw_peak_to_peak = max(raw) - min(raw)
```

Uses include:

- distinguishing true raw EMG from ghost signals;
- detecting contact failure;
- detecting insufficient signal amplitude.

### 8.6 Contact Quality Score

A relative contact quality score may be computed:

```text
contact_quality(t) = RMS_window(t) / session_p90_rms
```

or:

```text
contact_quality(event) = raw_rms(event) / percentile(raw_rms over session)
```

Uses include:

- rejecting noise-dominated baseline windows;
- detecting electrode settling;
- detecting low-SNR windows;
- delaying fatigue analysis until signal stabilizes.

---

## 9. FAILURE MODE IDENTIFICATION

The system identifies signal-quality states or failure modes, including:

- valid EMG signal;
- electrode settling or unstable contact;
- low-SNR or contact degradation;
- hardware envelope saturation;
- raw-channel flatline or failure;
- ghost-channel coupling or cross-channel contamination;
- motion artifact due to impact or vibration;
- reduced-motion confound;
- session discontinuity artifact.

The classification may be assigned to a sample window, movement event, swing, repetition, bout, session segment, or full recording session.

---

## 10. IMU-CONDITIONED VALIDITY LOGIC

IMU measurements provide independent context for interpreting EMG features.

In some embodiments:

- stable motion combined with early low-frequency EMG indicates electrode settling;
- stable motion combined with gradual frequency decline indicates fatigue-consistent changes;
- declining motion combined with EMG changes indicates reduced effort confound;
- transient IMU shocks corresponding to EMG anomalies indicate motion artifacts;
- discontinuities in session timing indicate cross-segment artifacts.

The IMU is used as a context channel rather than merely as a fused feature for classification.

### 10.1 Diagnostic Matrix

| IMU / Session Context | EMG Observation | Likely Interpretation | System Action |
|---|---|---|---|
| Stable movement intensity | Early-session low MDF/MNF or low RMS that later recovers | Electrode settling or contact hydration | Delay baseline; exclude early windows |
| Stable movement intensity | Gradual post-settling MDF/MNF decline | Candidate local fatigue | Accept with confidence if quality metrics pass |
| Declining movement intensity | EMG spectral or amplitude decline | Reduced effort or changed biomechanics may contribute | Do not attribute to fatigue alone; annotate |
| Large transient acceleration / gyro / jerk | Isolated EMG spectral outlier | Motion or impact artifact | Flag, down-weight, or exclude |
| IMU quiet but high EMG noise | Electrical/contact artifact or muscle tension | Use contact/noise logic; classify separately |
| BLE/session discontinuity | EMG baseline shift across segments | Cross-session artifact | Analyze segments separately |
| Stable IMU but RAW/ENV mismatch | Sensor/contact artifact | Warn user or reduce confidence |

### 10.2 Movement Stability Test

Movement intensity may be represented by:

```text
imu_peak_gyro
imu_mean_acc_dyn
imu_peak_acc_dyn
gyro_mag
acc_mag
jerk
```

The system may compute trends over time:

```text
corr(imu_intensity, time)
slope(imu_intensity vs time)
```

If EMG changes while IMU intensity remains stable, the EMG change is less likely to be caused by reduced gross movement intensity.

### 10.3 High-Motion Artifact Detection

The system may identify a high artifact-risk window when:

```text
gyro_mag > gyro_threshold
acc_dyn > acc_threshold
jerk > jerk_threshold
```

In one embodiment, representative thresholds for a wrist/forearm tennis application are: `gyro_threshold` = 300 deg/s peak magnitude (corresponding to high-intensity swing events), `acc_dyn` = dynamic acceleration component exceeding 3g, and `jerk` = rate-of-change of acceleration exceeding 50 m/s³. These values are implementation-specific and may be adapted to application, body placement, and sensor gain. The key principle is that any of these conditions coinciding with an EMG spectral or amplitude outlier elevates the likelihood of motion artifact rather than physiological change.

or when an EMG outlier occurs near an IMU impact or shock event.

---

## 11. BASELINE SELECTION AND FATIGUE GATING

The system establishes EMG baseline values only from signals satisfying quality constraints.

Baseline candidates may be filtered by:

- minimum signal amplitude or RMS thresholds;
- acceptable RAW–ENV consistency;
- absence of hardware ENV saturation;
- absence of raw flatline;
- stable IMU context;
- absence of motion artifacts;
- continuous recording without session gaps.

The system may delay baseline initialization until sufficient high-quality segments are collected.

Downstream fatigue interpretation is gated based on signal validity.

### 11.1 Representative Baseline Selection Method

A representative baseline selection method comprises:

1. collecting candidate baseline events after an initial warmup or activity start;
2. computing raw EMG RMS for each candidate;
3. computing a robust high-percentile RMS reference, such as the 90th percentile;
4. rejecting candidates below a fraction of the reference, such as:

```text
rms_threshold = 0.25 * p90_rms
```

5. optionally requiring RAW/ENV consistency;
6. optionally requiring no envelope saturation;
7. optionally requiring no raw flatline;
8. optionally requiring IMU movement intensity within an expected range;
9. computing baseline EMG features from accepted candidates.

For live operation, candidates may be collected until enough valid events are found or until a maximum count is reached.

Example live logic:

```text
collect baseline candidates after warmup
after at least N candidates:
    p90_rms = percentile(candidate_rms, 90)
    valid = candidates with rms >= 0.25 * p90_rms
    if count(valid) >= N:
        finalize baseline from valid candidates
    elif count(candidates) >= 3N:
        finalize from best available candidates
```

This prevents poor contact or noise-dominated early windows from corrupting downstream fatigue or activation metrics.

---

## 12. QUALITY-GATED FATIGUE OR ACTIVATION MONITORING

Once signal quality is assessed, downstream metrics may be modified.

### 12.1 Accept

If RAW/ENV consistency is acceptable, IMU context is stable, and no artifacts are detected, the system accepts EMG-derived features.

### 12.2 Delay

If contact quality indicates settling, the system delays baseline initialization or fatigue monitoring.

### 12.3 Reject

If raw flatline, high saturation, ghost-channel coupling, or severe motion artifact is detected, the system rejects affected windows.

### 12.4 Down-Weight

If quality is marginal, the system down-weights the window in trend estimation.

### 12.5 Annotate

The system can output a confidence score or artifact label, such as:

```text
valid
settling
low_contact_quality
env_saturated
raw_flatline
motion_artifact
impact_artifact
movement_confounded
session_gap
```

In one embodiment, a scalar confidence score is derived as a weighted combination of signal-quality indicators:

```text
confidence = w1 * (1 - pct_env_saturated)
           + w2 * (contact_quality >= cq_threshold ? 1 : 0)
           + w3 * (raw_variance >= flatline_threshold ? 1 : 0)
           + w4 * (imu_intensity_stable ? 1 : 0)
           + w5 * (no_session_gap ? 1 : 0)
```

where weights w1–w5 sum to 1.0 and may be set equal (0.2 each) or tuned per application. A confidence score below 0.5 may suppress fatigue output; below 0.3 may reject the window entirely. These thresholds are examples and may be adapted.

### 12.6 Alert

In real-time systems, the system may alert the user:

- adjust electrode;
- wait for settling;
- reduce cable motion;
- sensor saturated;
- reconnect occurred;
- data not suitable for fatigue interpretation.

---

## 13. SESSION CONTINUITY MANAGEMENT

In wireless or segmented recording systems, interruptions may occur.

The system:

- detects discontinuities based on timestamps or sequence gaps;
- separates analysis across segments;
- prevents cross-segment comparisons that may introduce artifacts;
- flags or suppresses fatigue metrics spanning discontinuities.

In some embodiments, the system reconstructs an absolute or common timebase from device timestamps and host receive timestamps. Connection gaps, resets, or capture boundaries may be preserved rather than silently stitched so downstream EMG analyses can distinguish continuous physiological trends from cross-session artifacts.

---

## 14. EXEMPLARY EMBODIMENTS

### 14.1 RAW/ENV Consistency Validation

A raw-derived envelope is compared against hardware ENV to detect:

- saturation or clipping;
- contact degradation;
- channel mismatch;
- abnormal gain or scaling;
- unreliable envelope-based contact indicators.

A diagnostic may include:

- raw RMS vs hardware ENV scatter;
- RAW/ENV ratio over time;
- envelope saturation count;
- raw flatline count.

Example outcomes from project data:

| Session | ENV Saturation | RAW Flatline | Interpretation |
|---|---:|---:|---|
| log0305 | 1.4% | 0% | Reliable primary session |
| log0303 | 14.2% | 0% | High ENV saturation; reduced confidence |

### 14.2 Electrode Settling Detection

Early low-frequency EMG or low-amplitude EMG that later recovers under stable IMU motion is interpreted as contact settling rather than fatigue.

The system can identify settling when:

- EMG MDF/MNF is low early;
- raw/contact quality metrics are poor;
- IMU swing intensity remains stable or does not explain the EMG anomaly;
- EMG features recover later.

### 14.3 Motion Artifact Detection

EMG outliers coinciding with IMU shocks, high acceleration, high jerk, or high gyroscope magnitude are classified as motion artifacts and may be rejected or down-weighted.

### 14.4 Ghost Signal Detection

A RAW channel exhibiting:

- high correlation with ENV;
- near-zero variance;
- flatline after filtering;

is identified as a ghost signal due to channel coupling or hardware failure.

A generalized diagnostic may be:

```text
if corr(raw, env) > high_corr_threshold
and variance(raw) < low_variance_threshold
and filtered_raw_rms < flatline_threshold:
    classify as ghost_signal_or_raw_channel_failure
```

In one embodiment, `high_corr_threshold` = 0.95 (Pearson r), `low_variance_threshold` = 1% of expected active EMG variance, and `filtered_raw_rms` below 2% of session p90_rms after bandpass filtering. An experimentally observed ghost-channel failure showed r = 0.998 and near-zero variance; after hardware repair (solder bypass of failed pogo-pin routing), correlation dropped to r = −0.013.

### 14.5 Session Gap Artifact

Signals across long recording gaps are analyzed as separate sessions to prevent false fatigue trends. If a BLE reconnection or session discontinuity is detected, the system avoids comparing baseline and final features across the gap as though they were continuous physiological data.

In one embodiment, a gap exceeding 60 seconds in the reconstructed absolute timestamp (`abs_us`) timeline is classified as a session discontinuity requiring segment-isolated analysis. In an experimental example, a 66-minute BLE reconnection gap produced an apparent full-session MDF drop of 28.7% when analyzed naively; segment-isolated analysis of the first continuous segment alone showed a 4.9% change, preventing a false fatigue conclusion.

Session discontinuities may include BLE reconnection gaps, wired transport interruptions, file-boundary discontinuities, timestamp resets, device resets, dropped-packet intervals, upload gaps, clock-reconstruction boundaries, or any other discontinuity that may affect the interpretation of longitudinal EMG metrics across time.

### 14.6 IMU-Conditioned Interpretation

If IMU peak gyroscope magnitude remains stable over a session while EMG median frequency declines after contact quality stabilizes, the decline may be accepted as fatigue-consistent. If IMU intensity declines, the EMG change is annotated as movement-confounded.

---

## 15. OUTPUT AND ACTIONS

Based on signal validity, the system may:

- accept or reject signal segments;
- delay or adjust baseline estimation;
- down-weight unreliable segments;
- suppress fatigue output;
- provide confidence scores;
- generate user prompts, such as adjust electrode contact;
- segment the session into valid and invalid intervals;
- output artifact labels;
- prevent physiological interpretation of invalid windows;
- route only valid windows to downstream machine-learning models.

---

## 16. ADVANTAGES

The invention provides:

- improved reliability of EMG interpretation in field conditions;
- reduction of false fatigue detection;
- real-time signal validation capability;
- detection of both physiological and hardware-related errors;
- detection of contact settling and contact degradation;
- use of hardware envelope as a signal-validity channel rather than merely an EMG signal;
- use of IMU as an independent EMG-validity context channel;
- compatibility with low-cost wearable systems;
- applicability across multiple domains.

### 16.1 Compared with Raw EMG Alone

Raw EMG alone cannot easily distinguish:

- poor electrode contact;
- true low activation;
- motion artifact;
- baseline corruption;
- raw-channel failure.

The proposed system uses hardware envelope and IMU context to disambiguate these cases.

### 16.2 Compared with Hardware Envelope Alone

Hardware envelope alone lacks spectral information needed for many fatigue biomarkers. It can also saturate or obscure high-frequency raw EMG behavior. The proposed system uses envelope as a quality/context channel while preserving raw EMG for detailed analysis.

### 16.3 Compared with Generic EMG+IMU Fusion

Many EMG+IMU systems fuse both modalities as feature sources for activity or fatigue classification. The proposed system uses IMU as an independent validity channel to determine when EMG features are trustworthy.

### 16.4 Compared with Fixed Warmup

Fixed warmup intervals may fail when electrode settling duration varies. The proposed system can delay baseline selection until quality metrics indicate adequate signal validity.

---

## 17. VARIATIONS AND APPLICATIONS

The invention may be applied to:

- different muscles or body locations;
- multi-channel EMG systems;
- other biosignals, including ECG, EEG, EOG, mechanomyography, or force-myography;
- various activities including sports, rehabilitation, workplace monitoring, prosthetic control, and human-computer interaction;
- embedded devices, smartphones, host computers, or cloud processing;
- real-time or offline processing pipelines.

Potential commercial or application areas include:

- athletic training and fatigue monitoring;
- tennis, baseball, golf, badminton, pickleball, rowing, cycling, running, and throwing sports;
- rehabilitation and physical therapy;
- occupational ergonomics and worker fatigue;
- human-computer interaction and gesture control;
- prosthetic control;
- e-sports or fine motor monitoring;
- remote health monitoring;
- research-grade low-cost EMG acquisition.

---

## 18. CLAIM CONCEPTS (NON-LIMITING)

These are technical brainstorming drafts, not attorney-reviewed legal claims. Three independent concepts (C1–C3) and fifteen dependent concepts (C4–C18) are included to support broad claim coverage.

---

### C1 — Independent Method Concept

A method comprising:

1. receiving, by one or more processors, raw electromyography samples from a wearable electromyography sensor;
2. receiving hardware envelope samples acquired concurrently with, time-aligned with, or corresponding to a common monitoring interval as the raw electromyography samples, from the same wearable electromyography sensor, the same electrode pair, an associated acquisition path, or a sensor monitoring a common muscle region;
3. receiving inertial measurement samples from a wearable inertial sensor;
4. computing a raw-derived amplitude or envelope feature from the raw electromyography samples;
5. generating one or more signal-quality metrics by comparing the raw-derived amplitude or envelope feature with the hardware envelope samples;
6. determining a motion context from the inertial measurement samples;
7. classifying a trustworthiness state of one or more electromyography windows based on the signal-quality metrics and the motion context; and
8. modifying downstream interpretation of at least one electromyography-derived activation or fatigue metric based on the trustworthiness state.

---

### C2 — Independent System Concept

A wearable sensing system comprising:

- an electromyography sensor configured to output raw electromyography data and hardware envelope data concurrently, time-aligned, or corresponding to common monitoring intervals;
- an inertial measurement unit configured to output motion data; and
- one or more processors configured to:
  - derive a raw-based amplitude or envelope feature from the raw electromyography data;
  - compare the raw-based feature with the hardware envelope data to generate signal-quality metrics;
  - determine a motion context from the motion data;
  - classify a signal trustworthiness state based on the signal-quality metrics and the motion context; and
  - gate, adjust, suppress, segment, or annotate an electromyography-derived fatigue or activation metric based on the trustworthiness state.

---

### C3 — Independent Computer-Readable Medium Concept

A non-transitory computer-readable medium storing instructions that, when executed by one or more processors, cause the processors to:

1. receive raw electromyography samples, hardware envelope samples, and inertial measurement samples from a wearable sensor system;
2. compute signal-quality metrics by comparing raw-derived amplitude or envelope features with the hardware envelope samples;
3. determine motion context from the inertial measurement samples;
4. classify a trustworthiness state of one or more electromyography windows based on the signal-quality metrics and the motion context; and
5. modify downstream electromyography-derived fatigue or activation interpretation based on the trustworthiness state.

---

### C4 — Dependent: Modification Actions

The method of C1, wherein modifying downstream interpretation comprises one or more of: accepting a window for analysis, rejecting a window, delaying baseline initialization, down-weighting an unreliable window, correcting a metric, segmenting analysis across a session discontinuity, suppressing a fatigue output, annotating a metric with a confidence label, or prompting a user to adjust electrode placement.

---

### C5 — Dependent: Signal-Quality Metrics

The method of C1, wherein the signal-quality metrics comprise one or more of: raw electromyography variance, a ratio of raw-derived amplitude to hardware envelope amplitude, a correlation between the raw-derived envelope and the hardware envelope, a hardware envelope saturation count or percentage, a raw electromyography flatline indicator after bandpass filtering, or a contact-quality score computed as a ratio of a windowed raw electromyography RMS to a session-level RMS percentile.

---

### C6 — Dependent: Motion Context Classification

The method of C1, wherein determining a motion context comprises classifying the inertial measurement samples as indicating one or more of: stable movement intensity, declining movement intensity, a transient shock or impact event, a vibration artifact, or absence of movement.

---

### C7 — Dependent: Electrode Settling Detection

The method of C1, wherein classifying the trustworthiness state comprises detecting electrode settling when the signal-quality metrics indicate low raw electromyography amplitude with gradual recovery over time while the motion context indicates stable or consistent movement intensity.

---

### C8 — Dependent: Reduced-Effort Confound Detection

The method of C1, wherein classifying the trustworthiness state comprises detecting a reduced-effort confound when a decline in electromyography-derived spectral features coincides with declining inertial movement intensity, and wherein modifying downstream interpretation comprises down-weighting or suppressing a fatigue metric derived during that period.

---

### C9 — Dependent: Ghost-Channel / Hardware Failure Detection

The method of C1, wherein classifying the trustworthiness state comprises detecting a raw electromyography channel failure or ghost-channel coupling when: (a) a correlation between the raw electromyography signal and the hardware envelope signal exceeds a first threshold; (b) variance of the raw electromyography signal is below a second threshold; and (c) the raw electromyography signal after bandpass filtering is below a third threshold or is substantially flat.

---

### C10 — Dependent: Hardware Envelope Saturation Detection

The method of C1, wherein classifying the trustworthiness state comprises detecting hardware envelope saturation when one or more hardware envelope samples are at or near a maximum output level, and wherein modifying downstream interpretation comprises reducing reliance on the hardware envelope for signal-quality assessment during the saturation period.

---

### C11 — Dependent: Quality-Gated Baseline Selection

The method of C1, further comprising:

- collecting candidate baseline windows from a plurality of movement events;
- accepting a candidate baseline window only when: raw electromyography variance exceeds a flatline threshold, hardware envelope saturation is below a saturation threshold, the signal-quality metrics satisfy a consistency condition, the contact-quality score exceeds a minimum threshold, the motion context indicates stable movement intensity, and no session discontinuity is present within the window; and
- computing a baseline electromyography metric from the accepted baseline windows.

---

### C12 — Dependent: Session Continuity Audit

The method of C1, further comprising:

- detecting a session discontinuity based on a gap in sample timestamps, a wireless connection event, or a device reset indicator;
- assigning a segment identifier to samples on each side of the discontinuity; and
- performing electromyography analysis independently within each segment, without computing fatigue metrics that compare data across the discontinuity.

---

### C13 — Dependent: Raw-Derived Envelope Computation

The method of C1, wherein computing the raw-derived amplitude or envelope feature comprises: removing a direct-current component from the raw electromyography samples using a low-pass filter; rectifying the result; and applying a smoothing low-pass filter to produce a software envelope tracking the amplitude of the raw electromyography signal.

---

### C14 — Dependent: Contact-Quality Metric

The method of C1, wherein the signal-quality metrics include a contact-quality score computed as a ratio of a windowed root-mean-square amplitude of the raw electromyography samples to a high-percentile root-mean-square value derived from the full session, wherein a contact-quality score below a threshold indicates low signal-to-noise ratio or degraded electrode-skin contact.

---

### C15 — Dependent: Confidence Score Output

The method of C1, further comprising generating a confidence score associated with the electromyography-derived fatigue or activation metric, wherein the confidence score is based on one or more of the signal-quality metrics, the motion context, session continuity state, and the trustworthiness classification.

---

### C16 — Dependent: User Feedback and Electrode Adjustment Prompt

The method of C1, further comprising generating a user-perceptible alert when the trustworthiness state indicates raw channel failure, persistent low contact quality, or hardware envelope saturation, wherein the alert prompts a user to reposition, re-apply, or reseat the electromyography sensor.

---

### C17 — Dependent: Real-Time and Offline Operation

The method of C1, wherein the method is performed in real time during a monitoring session on a mobile device, wearable microcontroller, or edge processor; or performed offline during post-processing on a host computer or cloud system.

---

### C18 — Dependent: Application Scope

The method of C1, wherein the electromyography-derived fatigue or activation metric is applied to one or more of: athletic performance monitoring, sports injury prevention, physical rehabilitation, occupational ergonomics, prosthetic or orthotic control, human-computer gesture interfaces, or clinical muscle assessment.

---

## 19. DEPENDENT CLAIM FEATURE NOTES

The dependent concepts above (C4–C18) cover the following feature areas for attorney claim drafting:

| Feature area | Concepts |
|---|---|
| Action vocabulary (accept / reject / delay / down-weight / suppress / annotate) | C4 |
| Signal-quality metric enumeration | C5 |
| IMU context states | C6 |
| Electrode settling detection | C7 |
| Reduced-effort confound | C8 |
| Ghost-channel / raw failure detection | C9 |
| ENV saturation detection | C10 |
| Quality-gated baseline selection | C11 |
| Session continuity / BLE gap audit | C12 |
| Raw-derived envelope computation method | C13 |
| Contact-quality metric definition | C14 |
| Confidence score | C15 |
| User feedback / electrode prompt | C16 |
| Real-time vs. offline | C17 |
| Application domains | C18 |

---

## 20. FIGURES

### Figure 1 — System Architecture

## Purpose
Shows that the invention includes both hardware acquisition and host/mobile software decision logic. Establishes the three input channels (RAW, ENV, IMU) and the processing pipeline leading to gated EMG output.

## Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEARABLE SENSOR UNIT                         │
│                                                                 │
│  ┌──────────────────────────┐    ┌──────────────────────────┐  │
│  │     EMG SENSOR           │    │     IMU SENSOR           │  │
│  │  (e.g., MyoWare 2.0)     │    │  (e.g., LSM6DS3)         │  │
│  │                          │    │                          │  │
│  │  RAW output ─────────────┼────┼──► RAW channel (2 kHz)   │  │
│  │  ENV output ─────────────┼────┼──► ENV channel (2 kHz)   │  │
│  │                          │    │  Accel + Gyro (200 Hz) ◄─┼──┤
│  └──────────────────────────┘    └──────────────────────────┘  │
│                                                                 │
│              ┌──────────────────────────────────┐              │
│              │   MICROCONTROLLER / MCU           │              │
│              │   - DMA ADC sampling              │              │
│              │   - Per-sample timestamping       │              │
│              │   - BLE TLV packetization         │              │
│              │   - Session continuity tracking   │              │
│              └──────────────┬───────────────────┘              │
└─────────────────────────────┼───────────────────────────────────┘
                              │  BLE / Wired Link
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              HOST / MOBILE PROCESSING UNIT                      │
│                                                                 │
│   RAW EMG ──────────────────────────────────────────────────┐  │
│                                                             │  │
│   ENV ──────────────────────────────────────────────────┐   │  │
│                                                         │   │  │
│   IMU ──────────────────────────────────────────────┐   │   │  │
│                                                     │   │   │  │
│   Session Timeline ─────────────────────────────┐   │   │   │  │
│                                                 │   │   │   │  │
│                    ┌────────────────────────────▼───▼───▼───▼─┐│
│                    │     SIGNAL QUALITY EVALUATOR              ││
│                    │                                           ││
│                    │  1. RAW preprocessing                     ││
│                    │  2. RAW-derived envelope computation      ││
│                    │  3. RAW/ENV consistency check             ││
│                    │  4. IMU motion context analysis           ││
│                    │  5. Session continuity audit              ││
│                    │  6. Signal trustworthiness classification ││
│                    └───────────────────┬───────────────────────┘│
│                                        │                        │
│                    ┌───────────────────▼───────────────────────┐│
│                    │     QUALITY-GATED EMG ANALYTICS            ││
│                    │                                           ││
│                    │  - Baseline selection                     ││
│                    │  - MDF / MNF / RMS computation            ││
│                    │  - Fatigue / activation interpretation    ││
│                    │  - Confidence score / user alert          ││
│                    └───────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Caption

**Figure 1.** System architecture showing dual-output EMG sensor (RAW and ENV channels), IMU sensor, and microcontroller on the wearable unit, connected via BLE or wired link to a host or mobile processing unit. The host runs the signal quality evaluator, which combines RAW, ENV, IMU, and session-timeline inputs to classify trustworthiness before passing data to the quality-gated EMG analytics layer.

## Notes for Patent

- The processing split between MCU and host is not limiting — all logic may run on-device, on a mobile phone, or in the cloud.
- The RAW and ENV channels originate from the same EMG sensor, providing paired signals for consistency checking.
- IMU is an independent sensor used as a validity context channel, not as a feature-fusion input to fatigue classification.

---

### Figure 2 — Overall Method Flow

## Purpose
Defines the core method and makes the trustworthiness gate explicit as an ordered sequence of steps. Supports the independent method claim concept.

## Diagram

```
        ┌─────────────────────────────────────────────┐
        │  ACQUIRE simultaneously:                    │
        │    • RAW EMG samples (high rate, e.g. 2 kHz)│
        │    • ENV samples (hardware envelope)        │
        │    • IMU samples (accel + gyro, e.g. 200 Hz)│
        │    • Session timestamp / connection state   │
        └─────────────────────┬───────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────┐
        │  PREPROCESS RAW EMG                         │
        │    • DC removal                             │
        │    • Bandpass filtering (e.g. 20–450 Hz)    │
        │    • Artifact blanking (optional)           │
        └─────────────────────┬───────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────┐
        │  COMPUTE RAW-DERIVED FEATURES               │
        │    • RMS amplitude                          │
        │    • Software envelope (rectify + LPF)      │
        │    • Spectral features: MDF, MNF            │
        │    • RAW variance                           │
        └─────────────────────┬───────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────┐
        │  COMPUTE SIGNAL-QUALITY METRICS             │
        │    • RAW/ENV ratio                          │
        │    • RAW/ENV correlation                    │
        │    • ENV saturation count / %               │
        │    • RAW variance (flatline detection)      │
        │    • Contact quality = RMS / session_p90    │
        └─────────────────────┬───────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────┐
        │  DETERMINE IMU MOTION CONTEXT               │
        │    • Swing / activity intensity             │
        │    • Transient shock or vibration           │
        │    • Trend: stable / declining / absent     │
        └─────────────────────┬───────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────┐
        │  AUDIT SESSION CONTINUITY                   │
        │    • Detect BLE gaps / device resets        │
        │    • Assign segment IDs                     │
        │    • Flag cross-gap comparisons             │
        └─────────────────────┬───────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────┐
        │  CLASSIFY SIGNAL TRUSTWORTHINESS            │
        │                                             │
        │  ┌──────────────────────────────────────┐  │
        │  │  VALID_EMG                           │  │
        │  │  ELECTRODE_SETTLING                  │  │
        │  │  LOW_SNR / CONTACT_LOSS              │  │
        │  │  ENV_SATURATION                      │  │
        │  │  RAW_FLATLINE                        │  │
        │  │  GHOST_CHANNEL_COUPLING              │  │
        │  │  MOTION_ARTIFACT                     │  │
        │  │  REDUCED_MOTION_CONFOUND             │  │
        │  │  SESSION_GAP_CONFOUND                │  │
        │  └──────────────────────────────────────┘  │
        └─────────────────────┬───────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────┐
        │  MODIFY DOWNSTREAM EMG INTERPRETATION       │
        │                                             │
        │  ┌──────────────────────────────────────┐  │
        │  │  ACCEPT segment for analysis         │  │
        │  │  REJECT segment                      │  │
        │  │  DELAY_BASELINE initialization       │  │
        │  │  DOWN_WEIGHT unreliable window       │  │
        │  │  SEGMENT_SEPARATELY across gap       │  │
        │  │  SUPPRESS_FATIGUE_OUTPUT             │  │
        │  │  SHOW_CONFIDENCE_WARNING             │  │
        │  │  PROMPT_ELECTRODE_ADJUSTMENT         │  │
        │  └──────────────────────────────────────┘  │
        └─────────────────────┬───────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────┐
        │  OUTPUT                                     │
        │    • Fatigue / activation metrics           │
        │    • Confidence score                       │
        │    • Failure flags / artifact labels        │
        │    • User feedback / alerts                 │
        └─────────────────────────────────────────────┘
```

## Caption

**Figure 2.** Overall method flow for reliability-gated wearable EMG monitoring. RAW EMG, hardware ENV, IMU, and session-timeline data are acquired simultaneously. After preprocessing and feature computation, signal-quality metrics and IMU motion context are combined with session continuity state to classify signal trustworthiness. The trustworthiness classification then modifies downstream EMG interpretation by accepting, rejecting, delaying, down-weighting, segmenting, suppressing, or annotating fatigue and activation metrics.

## Notes for Patent

- Every step in this flow corresponds to a method claim element.
- The classification step (states) and action step (actions) are the core of the invention — signal quality is not merely detected but actively used to modify physiological interpretation.
- The flow is implementable in real time on embedded hardware, on a mobile device, or offline during post-processing.

---

### Figure 3 — RAW/ENV Consistency Validation

## Purpose
Supports the RAW/ENV comparison novelty — the use of hardware ENV as a signal-quality channel, not as the primary EMG signal. Shows the five diagnostic cases that distinguish valid EMG from failure modes.

## Diagram A — Case Table

```
┌─────────────────┬──────────────────────┬──────────────────────┬──────────────────────┬─────────────────────────────┬─────────────────────────────┐
│      CASE       │    RAW BEHAVIOR      │    ENV BEHAVIOR      │  RAW/ENV CORRELATION │      INTERPRETATION         │           ACTION            │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┼─────────────────────────────┼─────────────────────────────┤
│ Normal /        │ Oscillating AC       │ Smooth, tracks       │ Moderate positive    │ Valid EMG — hardware and    │ ACCEPT window               │
│ Valid EMG       │ waveform, adequate   │ RAW amplitude        │ (expected coupling)  │ signal path consistent      │                             │
│                 │ variance             │ appropriately        │                      │                             │                             │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┼─────────────────────────────┼─────────────────────────────┤
│ Electrode       │ Low amplitude,       │ Low or recovering    │ Moderate             │ Electrode-skin interface    │ DELAY_BASELINE;             │
│ Settling        │ gradually rising     │ amplitude            │                      │ not yet hydrated / stable;  │ annotate as settling        │
│                 │ over 15–20 min       │                      │                      │ SNR improving               │                             │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┼─────────────────────────────┼─────────────────────────────┤
│ Hardware ENV    │ High amplitude or    │ Clipped / flat at    │ Decoupled: RAW       │ ENV hardware circuit is     │ FLAG ENV saturation;        │
│ Saturation      │ normal oscillation   │ maximum rail         │ varies, ENV does not │ saturated; ENV no longer    │ reduce ENV trust;           │
│                 │                      │                      │                      │ tracks RAW faithfully       │ rely on RAW-derived only    │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┼─────────────────────────────┼─────────────────────────────┤
│ RAW Channel     │ Near-zero variance;  │ Normal or changing   │ Very high (RAW       │ RAW input floating or       │ REJECT RAW-derived metrics; │
│ Flatline /      │ flat after bandpass  │ amplitude            │ passively tracks     │ short-circuited; RAW signal │ FLAG hardware failure;      │
│ Ghost Signal    │ filtering            │                      │ ENV through coupling)│ contains no muscle content  │ PROMPT_ELECTRODE_ADJUSTMENT │
├─────────────────┼──────────────────────┼──────────────────────┼──────────────────────┼─────────────────────────────┼─────────────────────────────┤
│ Contact Loss /  │ Low amplitude,       │ Low amplitude,       │ Variable             │ Poor electrode-skin         │ DOWN_WEIGHT or REJECT;      │
│ Low SNR         │ noise-dominated      │ noise-dominated      │                      │ contact; low SNR            │ SHOW_CONFIDENCE_WARNING     │
└─────────────────┴──────────────────────┴──────────────────────┴──────────────────────┴─────────────────────────────┴─────────────────────────────┘
```

## Diagram B — RAW/ENV Ratio Over Time (Schematic)

```
RAW/ENV
ratio
  │
  │    Normal band
  │  ┌──────────────────────────────────────────────────────┐
1.0 ─┤                                                      │
  │  │   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~│── ACCEPT
  │  └──────────────────────────────────────────────────────┘
  │
  │  ENV saturation region (ratio > threshold)
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ ── FLAG ENV
  │
0.0 ─┤  Ghost signal / flatline region (ratio ≈ 0 or abnormal)
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ ── REJECT
  │
  └──────────────────────────────────────────────────────────► time
     t=0          Settling zone         Post-settling
```

## Diagram C — RAW/ENV Scatter (Schematic)

```
ENV
amplitude
  │
  │                              ● ● ●
  │                         ● ● ●          ← Normal: ENV tracks RAW
  │                    ● ● ●                  (moderate correlation)
  │               ● ●
  │          ● ●
  │     ● ●
  │
  │  ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■               ← Ghost signal: ENV varies,
  │                                            RAW near-zero (vertical cluster)
  │
  │        ▲ ▲ ▲ ▲ ▲ ▲ ▲ ▲ ▲               ← ENV saturation: ENV flat,
  │ ───────────────────────────               RAW varies (horizontal cluster)
  │
  └──────────────────────────────────────► RAW amplitude
```

## Caption

**Figure 3.** RAW/ENV consistency validation. (A) Case table showing five diagnostic scenarios and the corresponding actions taken by the system. (B) Schematic RAW/ENV ratio over time, with normal, saturation, and ghost-signal regions indicated. (C) Schematic RAW/ENV amplitude scatter, illustrating distinct cluster signatures for normal operation, ghost-channel coupling, and ENV saturation.

## Notes for Patent

- Diagram B and C show that each failure mode has a geometrically distinct signature in the RAW/ENV feature space — this is the basis for the classification step.
- The ghost-signal case (very high RAW/ENV correlation + near-zero RAW variance) was confirmed empirically with Pearson r = 0.998 before hardware repair, dropping to r = −0.013 after solder bypass (log0303 pogo-pin failure).
- ENV saturation was observed at 14.2% of windows in log0303 vs. 1.4% in log0305.

---

### Figure 4 — IMU-Conditioned EMG Validity Matrix

## Purpose
Distinguishes this invention from generic EMG/IMU feature fusion. The IMU is used as an independent validity context channel — its role is to determine whether an observed EMG change is physiologically meaningful or explained by a non-physiological cause (reduced effort, motion artifact, session discontinuity).

## Diagram A — Decision Matrix

```
┌───────────────────────────────┬────────────────────────────┬──────────────────────────────────┬─────────────────────────────────┐
│   IMU / SESSION CONTEXT       │   EMG OBSERVATION          │       INTERPRETATION             │         ACTION                  │
├───────────────────────────────┼────────────────────────────┼──────────────────────────────────┼─────────────────────────────────┤
│ Stable movement intensity     │ Early low MDF/MNF,         │ Electrode settling — interface   │ DELAY_BASELINE;                 │
│ (consistent swing kinematics) │ gradually recovering       │ not yet stable; not physiological│ annotate settling period        │
│                               │ over 15–20 min             │                                  │                                 │
├───────────────────────────────┼────────────────────────────┼──────────────────────────────────┼─────────────────────────────────┤
│ Stable movement intensity     │ Gradual MDF/MNF decline    │ Fatigue-consistent change —      │ ACCEPT;                         │
│ (consistent swing kinematics) │ after post-settling        │ spectral shift not explained by  │ report as fatigue-consistent    │
│                               │ baseline                   │ reduced effort or contact change │                                 │
├───────────────────────────────┼────────────────────────────┼──────────────────────────────────┼─────────────────────────────────┤
│ Declining movement intensity  │ MDF/MNF decline            │ Reduced-effort confound —        │ DOWN_WEIGHT or                  │
│ (lower swing magnitude        │                            │ spectral shift may reflect lower │ SUPPRESS_FATIGUE_OUTPUT;        │
│  over time)                   │                            │ activation, not true fatigue     │ annotate effort confound        │
├───────────────────────────────┼────────────────────────────┼──────────────────────────────────┼─────────────────────────────────┤
│ Transient high shock or       │ Isolated EMG amplitude     │ Motion artifact — transient      │ DOWN_WEIGHT or REJECT           │
│ vibration event               │ spike or dropout           │ mechanical coupling to electrode │ affected window(s)              │
├───────────────────────────────┼────────────────────────────┼──────────────────────────────────┼─────────────────────────────────┤
│ Session discontinuity         │ Baseline shift or apparent │ Cross-segment artifact — gap     │ SEGMENT_SEPARATELY;             │
│ (BLE gap / device reset)      │ MDF drop across gap        │ changes electrode contact state  │ SUPPRESS cross-gap fatigue      │
│                               │                            │ independently of fatigue         │ comparison                      │
└───────────────────────────────┴────────────────────────────┴──────────────────────────────────┴─────────────────────────────────┘
```

## Diagram B — IMU as Validity Channel (Schematic Timeline)

```
time →    0        10       20       30       40       50       60 min
          │        │        │        │        │        │        │
IMU       ├────────┼────────┼────────┼────────┼────────┼────────┤
intensity │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
(stable)  │         (Pearson r = +0.01 vs time in log0305)      │
          │
MDF       ├────────┼────────┼────────┼────────┼────────┼────────┤
          │ /‾‾‾\   ↑settling ends                    \         │
          │/      \_____________________________stable  \───     │
          │                                              fatigue │
          │   Phase I      Phase II (stable)        Phase III    │
          │  (settling)                              (fatigue)   │
          │
IMU       │  IMU stable throughout all three phases
context:  │  → Phase I low MDF = settling, not effort reduction
          │  → Phase III MDF decline = fatigue-consistent
```

## Diagram C — Contrast: IMU Context vs IMU Feature Fusion

```
CONVENTIONAL EMG/IMU FUSION          THIS INVENTION
─────────────────────────────        ─────────────────────────────────────
EMG features  ─────┐                 RAW EMG features  ─────┐
                   ├──► classifier   ENV quality metrics ────┤
IMU features  ─────┘    (activity /  IMU context        ─────┤──► trustworthiness
                         fatigue)                            │    classifier
                                     Session continuity ─────┘
                                              │
                                              ▼
                                     Gate / modify fatigue output
                                     (not: fuse into single feature vector)
```

## Caption

**Figure 4.** IMU-conditioned EMG validity matrix. (A) Decision matrix mapping IMU/session context and EMG observation to interpretation and action. (B) Schematic timeline showing stable IMU intensity across all three phases of a 63-minute tennis session (log0305), supporting the interpretation that Phase I MDF suppression is electrode settling and Phase III MDF decline is fatigue-consistent. (C) Contrast between conventional EMG/IMU feature fusion and this invention's use of IMU as an independent validity context channel.

## Notes for Patent

- The IMU in this invention is not fused with EMG features to improve classification accuracy. Its role is orthogonal: it determines whether the EMG observation is interpretable as physiology, given the movement context.
- In log0305, IMU swing-intensity Pearson r = +0.029, p = 0.468 across 626 swings — confirming stable biomechanics throughout the session. This is the empirical basis for the "stable IMU → settling / fatigue-consistent" interpretation.
- The session-gap case (log0303) showed full-session apparent MDF drop of 28.7% vs. first-segment-only 4.9%.

---

### Figure 5 — Quality-Gated Baseline Selection

## Purpose
Supports the baseline-gating embodiment (Family B). Shows that baseline windows are accepted only when all quality conditions are satisfied — preventing settling-contaminated baselines that would invert or distort fatigue metrics.

## Diagram A — Baseline Selection Flowchart

```
       ┌─────────────────────────────────────────────────────┐
       │  CANDIDATE BASELINE WINDOWS                         │
       │  (e.g., swings or epochs after warmup skip)         │
       └──────────────────────┬──────────────────────────────┘
                              │
                              ▼
       ┌─────────────────────────────────────────────────────┐
       │  QUALITY GATE — check all conditions:               │
       │                                                     │
       │  1. RAW variance > flatline threshold?          Y/N │
       │  2. ENV saturation < max threshold?             Y/N │
       │  3. RAW/ENV ratio within normal band?           Y/N │
       │  4. Contact quality > minimum threshold?        Y/N │
       │     (RMS / session_p90_rms > Qmin)                  │
       │  5. IMU movement context: stable intensity?     Y/N │
       │  6. No session gap or BLE discontinuity?        Y/N │
       └──────────┬───────────────────────────┬──────────────┘
                  │ ALL pass                  │ ANY fail
                  ▼                           ▼
       ┌──────────────────────┐    ┌──────────────────────────┐
       │  ACCEPTED BASELINE   │    │  REJECTED / DEFERRED     │
       │  POOL                │    │                          │
       │  (trusted windows)   │    │  - Mark as settling      │
       └──────────┬───────────┘    │  - Mark as low-SNR       │
                  │                │  - Mark as motion        │
                  │                │  - Mark as gap           │
                  │                └──────────────────────────┘
                  ▼
       ┌──────────────────────────────────────────────────────┐
       │  ROBUST BASELINE ESTIMATION                          │
       │  (median or percentile MDF/RMS across accepted pool) │
       └──────────────────────┬───────────────────────────────┘
                              │
                              ▼
       ┌──────────────────────────────────────────────────────┐
       │  FATIGUE METRICS COMPUTED RELATIVE TO TRUSTED        │
       │  BASELINE ONLY                                       │
       │  (MDF drop %, MNF drop %, RMS trend)                 │
       └──────────────────────────────────────────────────────┘
```

## Diagram B — Warmup-Skip Sensitivity (Empirical Example)

```
 MDF
 Hz
 200 ─                                         ● baseline (w20, 199 Hz)
     │
 160 ─                      ● baseline (v2, 166 Hz)
     │
 140 ─  ● baseline (w10, 137 Hz)
     │
 110 ─              ● baseline (w15, 112 Hz)   ← lower than w10: mid-transition
     │
     │   SETTLING ZONE     │   POST-SETTLING
     │◄──────────────────► │◄───────────────
     │
     └──────┬──────┬───────┬──────────────────► warmup skip (min)
            10    15      20

 MDF drop result:
   w10 skip: −2.6%   (false negative — baseline inside settling)
   w15 skip: −26.2%  (inverted — baseline at mid-transition dip)
   w20 skip: +28.1%  ✅ (post-settling — true fatigue revealed)
```

## Diagram C — Effect of Baseline Quality on Fatigue Interpretation

```
 Without quality-gated baseline:               With quality-gated baseline:

 MDF                                           MDF
  │  ╲                                          │                    ╲
  │   ╲  apparent fatigue                       │  settling period    ╲ fatigue
  │    ╲  (actually: baseline                   │  (rejected from      ╲ (real)
  │     ╲  in settling zone)                    │   baseline pool)      ╲
  │      ─────                                  │        ────────────────╲────
  │                                             │        ↑ trusted baseline
  └──────────────► time                         └───────────────────────► time
```

## Caption

**Figure 5.** Quality-gated baseline selection. (A) Flowchart showing six quality checks applied to candidate baseline windows. Only windows passing all checks enter the accepted baseline pool. (B) Empirical warmup-skip sensitivity from log0305: baselines computed at 10, 15, and 20-minute warmup skips yield MDF results of −2.6%, −26.2%, and +28.1% respectively, demonstrating that baseline quality is a first-order determinant of fatigue interpretation. (C) Schematic showing how an unvalidated baseline (inside the settling zone) inverts the apparent fatigue direction.

## Notes for Patent

- The warmup-skip sensitivity numbers (−2.6% at 10 min, −26.2% at 15 min, +28.1% at 20 min) are from log0305 and are the central empirical finding of the CNIB paper.
- The non-monotone sensitivity (15 min baseline lower than 10 min) demonstrates that a fixed time skip is an unreliable heuristic — a quality-aware adaptive skip is more robust.
- `contact_quality(t) = RMS(t) / session_p90_rms` is the relative contact-quality metric used as one of the six gate conditions.

---

### Figure 6 — Session Continuity Audit

## Purpose
Supports the wireless/session discontinuity embodiment (Family C). Shows that treating a multi-segment session as continuous produces a false fatigue conclusion, and that segment-aware analysis gives the correct result.

## Diagram A — Session Timeline with BLE Gap (log0303)

```
 abs_us timeline →

 t = 0 min                t = 13.5 min                          t = 80 min       t = 87.9 min
 │                        │                                     │                │
 ├────────────────────────┤                                     ├────────────────┤
 │  SEGMENT 1             │         BLE GAP (66 min)            │  SEGMENT 2     │
 │  (first connection)    │◄───────────────────────────────────►│  (reconnect)   │
 │  111 swings            │         no data                     │  ~56 swings    │
 │  Contact state: fresh  │                                     │  Contact: ?    │
 └────────────────────────┘                                     └────────────────┘
                           ↑
                    Reconnect event
                    (hybrid abs_us
                     timeline flags gap)


 NAIVE ANALYSIS (ignores gap):
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │  Treats all swings as one continuous session                                 │
 │  Baseline MDF: 210.9 Hz (from early swings in Segment 1)                    │
 │  Final MDF:   151.2 Hz  (from late swings in Segment 2)                     │
 │  Apparent MDF drop: 28.7%  ← ARTIFACT, not physiological fatigue            │
 └──────────────────────────────────────────────────────────────────────────────┘

 CONTINUITY-AWARE ANALYSIS (segments separately):
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │  Segment 1 only (13.5 min, 111 swings):                                      │
 │  Baseline MDF: 210.9 Hz  →  Final MDF: 200.5 Hz                             │
 │  MDF drop: 4.9%  ← no meaningful within-segment fatigue                     │
 │                                                                              │
 │  Segment 2: insufficient duration / different contact state                  │
 │  → suppress cross-gap fatigue comparison                                     │
 └──────────────────────────────────────────────────────────────────────────────┘
```

## Diagram B — MDF Over Full Session Schematic

```
 MDF
 Hz
 220 ─  ●●●●●●●                         (Segment 1 swings)
     │         ●●●●●●●●
 200 ─                 ●●●●●●●
     │                        ●●●
     │
     │                            ╔══════ BLE GAP (66 min) ══════╗
     │                            ║  no data                     ║
     │                            ╚══════════════════════════════╝
     │
 160 ─                                                    ●●●●●● (Segment 2)
     │                                               ●●●●●
 150 ─                                          ●●●●
     │
     │   ← naive: compares these two regions → 28.7% "fatigue"
     │   ← correct: Seg 1 alone → 4.9% (no fatigue)
     │
     └────────────────────────────────────────────────────────► time
          0        13.5 min                            80–88 min
```

## Diagram C — Continuity Audit Logic

```
       ┌─────────────────────────────────────────┐
       │  For each sample / swing:               │
       │    Check abs_us gap to previous         │
       └────────────────┬────────────────────────┘
                        │
           ┌────────────▼────────────┐
           │  Gap > threshold?       │
           └────┬────────────┬───────┘
                │ YES         │ NO
                ▼             ▼
       ┌─────────────┐  ┌──────────────────────────┐
       │  New        │  │  Continue current segment │
       │  segment ID │  └──────────────────────────┘
       │  assigned   │
       └──────┬──────┘
              │
              ▼
       ┌──────────────────────────────────────────┐
       │  Per-segment analysis:                   │
       │    - Baseline computed within segment    │
       │    - Fatigue metric within segment       │
       │    - No cross-gap comparisons            │
       └──────────────────────────────────────────┘
```

## Caption

**Figure 6.** Session continuity audit. (A) Timeline of log0303 showing two BLE connection segments separated by a 66-minute gap. Naive analysis treating both segments as continuous produces a 28.7% apparent MDF drop (artifact). Continuity-aware analysis of Segment 1 alone shows 4.9% change (no meaningful fatigue). (B) Schematic MDF plot over the full session, illustrating the non-physiological apparent drop produced by the gap. (C) Continuity audit logic assigning segment IDs and preventing cross-gap fatigue comparisons.

## Notes for Patent

- The `abs_us` (absolute microsecond) hybrid timeline reconstructs session continuity across BLE dropouts and device resets by combining device-side timestamps with host-side clock stitching.
- The 66-minute gap in log0303 is the experimental basis for Family C (session continuity management).
- Cross-gap MDF comparison is a specific failure mode of naive longitudinal fatigue analysis and is the primary motivation for segment-aware processing.

---

### Figure 7 — Ghost Signal / Hardware Failure Diagnostic

## Purpose
Supports the pogo-pin ghost-signal embodiment (Family D). Shows the three-part diagnostic signature — high RAW/ENV correlation, near-zero RAW variance, and post-filter flatline — and the before/after repair comparison.

## Diagram A — Failure Signature

```
GHOST-CHANNEL FAILURE STATE
(RAW channel floating / pogo-pin open circuit)

Signal behavior:
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  RAW (raw):  ─────────────────────────────────────────── (no AC)    │
│              Low-amplitude, structureless, passively coupled to ENV  │
│                                                                      │
│  ENV:        ╱╲  ╱╲  ╱╲  ╱╲  ╱╲  ╱╲  ╱╲  ╱╲  ╱╲  ╱╲              │
│              Normal muscle envelope activity                         │
│                                                                      │
│  RAW (post-bandpass filter):  ════════════════════════  FLATLINE     │
│              Bandpass removes the DC-coupled ghost; nothing remains  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

Diagnostic metrics:
  • RAW variance:            near zero        (< flatline threshold)
  • RAW/ENV Pearson r:       0.998            (pathologically high)
  • Post-filter RAW std:     ~0               (flatline confirmed)
  • RAW spectral content:    no EMG band power
```

## Diagram B — Before/After Repair Comparison

```
                     BEFORE REPAIR              AFTER REPAIR
                  (pogo-pin open circuit)      (solder bypass)
                 ┌───────────────────────┐   ┌───────────────────────┐
 RAW waveform    │  ──────────────────── │   │  ╱╲  ╱╲  ╱╲  ╱╲  ╱╲  │
                 │  (no AC content)      │   │  (normal EMG waveform) │
                 └───────────────────────┘   └───────────────────────┘

 RAW/ENV         │  r = 0.998            │   │  r = −0.013            │
 correlation     │  (near-perfect)       │   │  (independent)         │

 RAW variance    │  ≈ 0                  │   │  normal EMG level      │

 Post-filter RAW │  ════ flatline ════   │   │  ╱╲ ╱╲ ╱╲ normal ╱╲   │

 Interpretation  │  Ghost channel:       │   │  Valid RAW channel:    │
                 │  RAW = passive copy   │   │  RAW has independent   │
                 │  of ENV through       │   │  EMG AC content        │
                 │  analog coupling      │   │                        │

 Action          │  REJECT RAW metrics   │   │  ACCEPT RAW metrics    │
                 │  FLAG hardware fault  │   │                        │
```

## Diagram C — Detection Flowchart

```
       ┌──────────────────────────────────────────────────────┐
       │  For each analysis window:                           │
       │    compute RAW variance, RAW/ENV correlation,        │
       │    post-filter RAW standard deviation                │
       └──────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────▼────────────────┐
          │  RAW variance < V_thresh       │
          │  AND                           │
          │  RAW/ENV correlation > R_thresh│
          │  AND                           │
          │  post-filter RAW std < F_thresh│
          └───────┬──────────────┬─────────┘
                  │ ALL TRUE      │ NOT ALL TRUE
                  ▼               ▼
       ┌──────────────────┐  ┌──────────────────────────────┐
       │  GHOST_CHANNEL   │  │  Continue normal processing  │
       │  _COUPLING state │  └──────────────────────────────┘
       │                  │
       │  Actions:        │
       │  - REJECT RAW    │
       │    spectral/RMS  │
       │  - FLAG hardware │
       │    failure       │
       │  - PROMPT repair │
       └──────────────────┘
```

## Caption

**Figure 7.** Ghost-signal / hardware failure diagnostic. (A) Failure signature showing that a floating RAW input passively couples to ENV through analog paths, producing near-zero RAW variance, near-perfect RAW/ENV correlation, and a flatline after bandpass filtering. (B) Before/after repair comparison from the log0303 pogo-pin failure: RAW/ENV Pearson r drops from 0.998 to −0.013 after solder bypass, confirming independent RAW channel operation. (C) Three-condition detection flowchart for ghost-channel classification.

## Notes for Patent

- The empirical data (r = 0.998 before, r = −0.013 after) is from the ICPICS paper and log0303 analysis.
- The three-condition gate (variance + correlation + post-filter std) is the implementable diagnostic core of Family D.
- The physical cause in this embodiment was pogo-pin contact failure in the RAW signal routing path — but the diagnostic applies to any floating ADC input, multiplexer charge-sharing, or analog coupling failure.
- The RAW flatline after bandpass filtering is the most reliable single indicator: it shows there is no independent AC muscle content in the RAW channel.

## 21. EXPERIMENTAL SUPPORT TO INCLUDE

### 21.1 log0305

- Continuous 63.1-min tennis session.
- 626 swings.
- Low ENV saturation: 1.4%.
- Zero RAW flatlines.
- Stable IMU swing-intensity proxy.
- Demonstrates reliable session after quality validation.

### 21.2 log0303

- Two BLE segments separated by a large gap.
- Higher ENV saturation: 14.2%.
- Zero RAW flatlines.
- Session discontinuity and contact-state change.
- Demonstrates need for quality and continuity validation.

### 21.3 Pogo-Pin Failure

- RAW channel failure caused ghost signal.
- Diagnostic: high raw/env correlation, near-zero raw variance, post-filter flatline.
- Fixed by solder bypass.
- Demonstrates practical value of RAW/ENV consistency checks.

---

## 22. KNOWN PRIOR-ART RISK AREAS

Likely prior art includes:

- EMG signal-quality assessment;
- EMG envelope computation;
- EMG fatigue metrics using MDF/MNF/RMS;
- IMU+EMG fusion for activity classification;
- wearable sports monitoring;
- electrode impedance and contact quality studies.

The strongest novelty should therefore emphasize:

1. concurrent, time-aligned, or common-interval raw EMG and hardware envelope comparison;
2. use of hardware envelope as a signal-validity channel, not merely as the EMG signal itself;
3. IMU as an independent EMG-validity context channel;
4. classification/action logic that gates downstream EMG interpretation;
5. field-specific failure modes such as settling, saturation, ghost coupling, and motion artifact.

---

## 23. DISCLOSURE / FILING NOTES

Important issues to review with counsel:

1. **Public disclosure**
   - Determine whether GitHub, papers, posters, abstracts, PDFs, or presentations already publicly disclosed these ideas.
   - U.S. may have a one-year inventor grace period; many non-U.S. jurisdictions do not.

2. **Ownership**
   - Determine whether school, university, collaborators, funding, or employer policies affect ownership.

3. **Inventorship**
   - Identify who contributed to conception of the RAW/ENV/IMU signal-quality validation approach.

4. **Filing strategy**
   - Consider filing a U.S. provisional before submitting or publishing additional manuscripts.

---

## 24. ADMINISTRATIVE NOTES — NOT PART OF CLAIMED TECHNICAL SCOPE

> **Internal working note — not part of the invention disclosure.** This section records filing-preparation status for internal tracking only and is not part of the claimed technical scope of the invention.

All pre-filing drafting tasks are complete as of 2026-06-01.

### Completed

- [x] One-page invention disclosure — `01_invention_disclosure.md`
- [x] System diagrams and figures 1–7 — `06_figures/`
- [x] Full prose specification — this document
- [x] 18 claim-style concepts (3 independents + 15 dependents) — §18
- [x] Public disclosure timeline — `02_public_disclosure_timeline.md`
- [x] Inventor/contributor matrix — `03_inventor_contribution_matrix.md`
- [x] Prior art search notes — `04_prior_art_search_notes.md`
- [x] Filing strategy determined — file provisional before ICPICS/CNIB publish (~2026-07)

### Remaining before filing

- [ ] Obtain ICPICS and CNIB publication dates — fill into `02_public_disclosure_timeline.md`
- [ ] Open and verify `05_provisional_draft.pdf` — confirm title, all sections present, figures 1–7 readable, no stale draft-only wording
- [ ] Confirm with USPTO Patent Center instructions who must sign/submit the provisional cover sheet for a minor inventor
- [ ] File provisional via USPTO Patent Center — upload this PDF, complete cover sheet, pay micro-entity fee (~$320)
- [ ] Record filing receipt in `07_filing_receipt.md`

---

## 25. ONE-PARAGRAPH ATTORNEY SUMMARY

This invention provides systems and methods for validating wearable EMG signal quality by combining a high-rate raw EMG channel, a concurrently acquired hardware envelope channel, and IMU-derived motion context. A processor derives raw EMG amplitude or software-envelope features, compares them with the hardware envelope to detect saturation, flatline, contact degradation, electrode settling, and ghost-channel coupling, and uses IMU data to distinguish valid muscle activity from reduced movement intensity, impact artifact, or motion-contaminated EMG. The resulting signal-quality classification gates downstream EMG interpretation, including baseline selection and fatigue monitoring, by accepting, rejecting, delaying, down-weighting, correcting, or annotating EMG-derived metrics with a confidence score. The approach addresses practical field-deployment failures in dynamic wearable EMG that are not resolved by conventional raw-only EMG processing or generic EMG/IMU feature fusion.

---

## 26. CONCLUSION

The invention provides a **trustworthiness-first framework for wearable EMG systems**, in which physiological interpretation is conditioned on validated signal quality.

By integrating RAW EMG, hardware envelope signals, and IMU-based context, the system enables robust EMG analysis in dynamic, real-world environments where conventional approaches fail. The framework validates signal quality before interpreting EMG-derived physiological metrics, thereby improving reliability of wearable fatigue monitoring, activation tracking, rehabilitation assessment, sports analytics, occupational monitoring, and related applications.