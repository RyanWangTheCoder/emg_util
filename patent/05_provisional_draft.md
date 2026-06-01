# SYSTEMS AND METHODS FOR SIGNAL-QUALITY VALIDATION OF WEARABLE ELECTROMYOGRAPHY USING RAW/ENVELOPE CONSISTENCY AND INERTIAL CONTEXT

> Provisional patent application / invention disclosure working draft.  
> This document merges the primary provisional draft with the RAW/ENV/IMU signal-quality technical draft.  
> This is a technical drafting aid, not legal advice. A patent attorney should review before filing.

---

## 1. FIELD OF THE INVENTION

The present invention relates to wearable biosignal sensing and analysis, and more particularly to **systems and methods for validating signal quality in surface electromyography (sEMG) using combined electromyography and inertial sensing in dynamic field environments**.

In some embodiments, the invention relates to validating and improving wearable electromyography signal quality using simultaneously acquired:

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

## 3. SUMMARY OF THE INVENTION

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

## 4. SYSTEM ARCHITECTURE

In one embodiment, the system comprises:

- a wearable EMG sensor providing:
  - raw EMG output (RAW);
  - hardware envelope output (ENV);
- an inertial measurement unit (IMU);
- a processing unit, which may be embedded, host-side, mobile, or cloud-based;
- a data communication interface, wired or wireless;
- a host or mobile device for analysis, display, alerting, or storage.

### 4.1 Functional Components

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

### 4.2 Representative Hardware Embodiment

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

## 5. DATA STREAMS

### 5.1 Raw EMG Stream

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

### 5.2 Hardware Envelope Stream

The hardware envelope stream may be produced by an analog rectifier/low-pass circuit, a sensor module, or an embedded processor. It may have a lower bandwidth than the raw EMG signal.

The hardware envelope stream may be used to compute:

- envelope mean;
- envelope maximum;
- envelope saturation count;
- envelope saturation percentage;
- envelope dynamic range;
- envelope-to-raw ratio;
- envelope consistency over time.

### 5.3 IMU Stream

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

## 6. RAW-DERIVED ENVELOPE AND FEATURE COMPUTATION

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

## 7. SIGNAL-QUALITY METRICS

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

### 7.1 Amplitude Ratio

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

### 7.2 Correlation

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

### 7.3 Saturation Count

```text
n_env_saturated = count(env_hw >= saturation_threshold)
pct_env_saturated = n_env_saturated / n_events
```

Uses include:

- detecting hardware-envelope clipping;
- reducing confidence in envelope-derived contact or activation metrics;
- flagging sessions where envelope data cannot be used as a reliable quality proxy.

### 7.4 Raw Flatline Detection

```text
raw_variance < flatline_threshold
```

or:

```text
raw_rms < minimum_activity_threshold during movement events
```

Uses include:

- detecting disconnected electrodes;
- detecting failed raw input;
- detecting post-filter flatline;
- detecting dead channels.

### 7.5 Raw Variance / Dynamic Range

```text
raw_sd = standard_deviation(raw within window)
raw_peak_to_peak = max(raw) - min(raw)
```

Uses include:

- distinguishing true raw EMG from ghost signals;
- detecting contact failure;
- detecting insufficient signal amplitude.

### 7.6 Contact Quality Score

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

## 8. FAILURE MODE IDENTIFICATION

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

## 9. IMU-CONDITIONED VALIDITY LOGIC

IMU measurements provide independent context for interpreting EMG features.

In some embodiments:

- stable motion combined with early low-frequency EMG indicates electrode settling;
- stable motion combined with gradual frequency decline indicates fatigue-consistent changes;
- declining motion combined with EMG changes indicates reduced effort confound;
- transient IMU shocks corresponding to EMG anomalies indicate motion artifacts;
- discontinuities in session timing indicate cross-segment artifacts.

The IMU is used as a context channel rather than merely as a fused feature for classification.

### 9.1 Diagnostic Matrix

| IMU / Session Context | EMG Observation | Likely Interpretation | System Action |
|---|---|---|---|
| Stable movement intensity | Early-session low MDF/MNF or low RMS that later recovers | Electrode settling or contact hydration | Delay baseline; exclude early windows |
| Stable movement intensity | Gradual post-settling MDF/MNF decline | Candidate local fatigue | Accept with confidence if quality metrics pass |
| Declining movement intensity | EMG spectral or amplitude decline | Reduced effort or changed biomechanics may contribute | Do not attribute to fatigue alone; annotate |
| Large transient acceleration / gyro / jerk | Isolated EMG spectral outlier | Motion or impact artifact | Flag, down-weight, or exclude |
| IMU quiet but high EMG noise | Electrical/contact artifact or muscle tension | Use contact/noise logic; classify separately |
| BLE/session discontinuity | EMG baseline shift across segments | Cross-session artifact | Analyze segments separately |
| Stable IMU but RAW/ENV mismatch | Sensor/contact artifact | Warn user or reduce confidence |

### 9.2 Movement Stability Test

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

### 9.3 High-Motion Artifact Detection

The system may identify a high artifact-risk window when:

```text
gyro_mag > gyro_threshold
acc_dyn > acc_threshold
jerk > jerk_threshold
```

or when an EMG outlier occurs near an IMU impact or shock event.

---

## 10. BASELINE SELECTION AND FATIGUE GATING

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

### 10.1 Representative Baseline Selection Method

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

## 11. QUALITY-GATED FATIGUE OR ACTIVATION MONITORING

Once signal quality is assessed, downstream metrics may be modified.

### 11.1 Accept

If RAW/ENV consistency is acceptable, IMU context is stable, and no artifacts are detected, the system accepts EMG-derived features.

### 11.2 Delay

If contact quality indicates settling, the system delays baseline initialization or fatigue monitoring.

### 11.3 Reject

If raw flatline, high saturation, ghost-channel coupling, or severe motion artifact is detected, the system rejects affected windows.

### 11.4 Down-Weight

If quality is marginal, the system down-weights the window in trend estimation.

### 11.5 Annotate

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

### 11.6 Alert

In real-time systems, the system may alert the user:

- adjust electrode;
- wait for settling;
- reduce cable motion;
- sensor saturated;
- reconnect occurred;
- data not suitable for fatigue interpretation.

---

## 12. SESSION CONTINUITY MANAGEMENT

In wireless or segmented recording systems, interruptions may occur.

The system:

- detects discontinuities based on timestamps or sequence gaps;
- separates analysis across segments;
- prevents cross-segment comparisons that may introduce artifacts;
- flags or suppresses fatigue metrics spanning discontinuities.

In some embodiments, the system reconstructs an absolute or common timebase from device timestamps and host receive timestamps. Connection gaps, resets, or capture boundaries may be preserved rather than silently stitched so downstream EMG analyses can distinguish continuous physiological trends from cross-session artifacts.

---

## 13. EXEMPLARY EMBODIMENTS

### 13.1 RAW/ENV Consistency Validation

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

### 13.2 Electrode Settling Detection

Early low-frequency EMG or low-amplitude EMG that later recovers under stable IMU motion is interpreted as contact settling rather than fatigue.

The system can identify settling when:

- EMG MDF/MNF is low early;
- raw/contact quality metrics are poor;
- IMU swing intensity remains stable or does not explain the EMG anomaly;
- EMG features recover later.

### 13.3 Motion Artifact Detection

EMG outliers coinciding with IMU shocks, high acceleration, high jerk, or high gyroscope magnitude are classified as motion artifacts and may be rejected or down-weighted.

### 13.4 Ghost Signal Detection

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

### 13.5 Session Gap Artifact

Signals across long recording gaps are analyzed as separate sessions to prevent false fatigue trends. If a BLE reconnection or session discontinuity is detected, the system avoids comparing baseline and final features across the gap as though they were continuous physiological data.

### 13.6 IMU-Conditioned Interpretation

If IMU peak gyroscope magnitude remains stable over a session while EMG median frequency declines after contact quality stabilizes, the decline may be accepted as fatigue-consistent. If IMU intensity declines, the EMG change is annotated as movement-confounded.

---

## 14. OUTPUT AND ACTIONS

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

## 15. ADVANTAGES

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

### 15.1 Compared with Raw EMG Alone

Raw EMG alone cannot easily distinguish:

- poor electrode contact;
- true low activation;
- motion artifact;
- baseline corruption;
- raw-channel failure.

The proposed system uses hardware envelope and IMU context to disambiguate these cases.

### 15.2 Compared with Hardware Envelope Alone

Hardware envelope alone lacks spectral information needed for many fatigue biomarkers. It can also saturate or obscure high-frequency raw EMG behavior. The proposed system uses envelope as a quality/context channel while preserving raw EMG for detailed analysis.

### 15.3 Compared with Generic EMG+IMU Fusion

Many EMG+IMU systems fuse both modalities as feature sources for activity or fatigue classification. The proposed system uses IMU as an independent validity channel to determine when EMG features are trustworthy.

### 15.4 Compared with Fixed Warmup

Fixed warmup intervals may fail when electrode settling duration varies. The proposed system can delay baseline selection until quality metrics indicate adequate signal validity.

---

## 16. VARIATIONS AND APPLICATIONS

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

## 17. CLAIM CONCEPTS (NON-LIMITING)

These are technical brainstorming drafts, not attorney-reviewed legal claims. Three independent concepts (C1–C3) and fifteen dependent concepts (C4–C18) are included to support broad claim coverage.

---

### C1 — Independent Method Concept

A method comprising:

1. receiving, by one or more processors, raw electromyography samples from a wearable electromyography sensor;
2. receiving hardware envelope samples acquired simultaneously from the same wearable electromyography sensor;
3. receiving inertial measurement samples from a wearable inertial sensor;
4. computing a raw-derived amplitude or envelope feature from the raw electromyography samples;
5. generating one or more signal-quality metrics by comparing the raw-derived amplitude or envelope feature with the hardware envelope samples;
6. determining a motion context from the inertial measurement samples;
7. classifying a trustworthiness state of one or more electromyography windows based on the signal-quality metrics and the motion context; and
8. modifying downstream interpretation of at least one electromyography-derived activation or fatigue metric based on the trustworthiness state.

---

### C2 — Independent System Concept

A wearable sensing system comprising:

- an electromyography sensor configured to output raw electromyography data and hardware envelope data simultaneously;
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

## 18. DEPENDENT CLAIM FEATURE NOTES

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

## 19. FIGURES

Figures are drafted in `patent/06_figures/`. Each file contains ASCII diagrams, caption, and patent notes.

### Figure 1 — System Architecture
**File:** `patent/06_figures/fig1_system_architecture.md`

Shows wearable sensor unit (EMG RAW + ENV outputs, IMU), microcontroller, BLE/wired link, and host/mobile processing unit. The host runs the signal quality evaluator (RAW + ENV + IMU + session timeline → trustworthiness classifier) feeding into the quality-gated EMG analytics layer.

```
EMG Sensor (RAW + ENV) ─┐
                         ├──► MCU ──► BLE/Wired ──► Signal Quality Evaluator ──► Gated EMG Analytics
IMU ────────────────────┘
```

### Figure 2 — Overall Method Flow
**File:** `patent/06_figures/fig2_method_flow.md`

Step-by-step flowchart: acquire → preprocess RAW → compute RAW features → compute signal-quality metrics → determine IMU context → audit session continuity → classify trustworthiness (9 states) → modify downstream interpretation (8 actions) → output.

```
Acquire RAW, ENV, IMU, session state
        ↓
Preprocess RAW EMG
        ↓
Compute RAW-derived RMS, envelope, MDF, MNF
        ↓
Compute signal-quality metrics (RAW/ENV ratio, correlation, variance, contact quality)
        ↓
Determine IMU motion context
        ↓
Audit session continuity
        ↓
Classify signal trustworthiness
        ↓
Accept / reject / delay / down-weight / segment / suppress / annotate EMG interpretation
        ↓
Output: fatigue metrics + confidence score + failure flags
```

### Figure 3 — RAW/ENV Consistency Validation
**File:** `patent/06_figures/fig3_raw_env_consistency.md`

Five-case diagnostic table (Normal, Settling, ENV Saturation, RAW Flatline/Ghost, Contact Loss) with RAW/ENV ratio timeline and scatter diagrams. Shows distinct cluster signatures for each failure mode in the RAW/ENV feature space.

### Figure 4 — IMU-Conditioned EMG Validity Matrix
**File:** `patent/06_figures/fig4_imu_decision_matrix.md`

Decision matrix mapping IMU/session context × EMG observation to interpretation and action. Includes schematic MDF timeline for log0305 showing stable IMU across all three phases (settling / stable / fatigue-consistent). Contrast diagram: conventional EMG/IMU feature fusion vs. this invention's use of IMU as an independent validity context channel.

### Figure 5 — Quality-Gated Baseline Selection
**File:** `patent/06_figures/fig5_baseline_gating.md`

Six-condition baseline gate flowchart. Empirical warmup-skip sensitivity diagram: baselines at 10 / 15 / 20 min yield MDF results of −2.6% / −26.2% / +28.1%, demonstrating that baseline quality determines fatigue interpretation. Schematic showing how a settling-contaminated baseline inverts apparent fatigue direction.

### Figure 6 — Session Continuity Audit
**File:** `patent/06_figures/fig6_session_gap_audit.md`

log0303 session timeline showing 66-minute BLE gap between Segment 1 (13.5 min, 111 swings) and Segment 2. Naive analysis: 28.7% apparent MDF drop (artifact). Continuity-aware analysis: Segment 1 alone shows 4.9% (no meaningful fatigue). Continuity audit logic flowchart with segment-ID assignment.

### Figure 7 — Ghost Signal / Hardware Failure Diagnostic
**File:** `patent/06_figures/fig7_ghost_signal_diagnostic.md`

Three-part diagnostic signature: near-zero RAW variance, RAW/ENV Pearson r ≈ 1.0, post-filter RAW flatline. Before/after repair comparison: r = 0.998 (pogo-pin failure) → r = −0.013 (after solder bypass). Three-condition detection flowchart.

---

## 20. EXPERIMENTAL SUPPORT TO INCLUDE

### 20.1 log0305

- Continuous 63.1-min tennis session.
- 626 swings.
- Low ENV saturation: 1.4%.
- Zero RAW flatlines.
- Stable IMU swing-intensity proxy.
- Demonstrates reliable session after quality validation.

### 20.2 log0303

- Two BLE segments separated by a large gap.
- Higher ENV saturation: 14.2%.
- Zero RAW flatlines.
- Session discontinuity and contact-state change.
- Demonstrates need for quality and continuity validation.

### 20.3 Pogo-Pin Failure

- RAW channel failure caused ghost signal.
- Diagnostic: high raw/env correlation, near-zero raw variance, post-filter flatline.
- Fixed by solder bypass.
- Demonstrates practical value of RAW/ENV consistency checks.

---

## 21. KNOWN PRIOR-ART RISK AREAS

Likely prior art includes:

- EMG signal-quality assessment;
- EMG envelope computation;
- EMG fatigue metrics using MDF/MNF/RMS;
- IMU+EMG fusion for activity classification;
- wearable sports monitoring;
- electrode impedance and contact quality studies.

The strongest novelty should therefore emphasize:

1. simultaneous raw EMG and hardware envelope comparison;
2. use of hardware envelope as a signal-validity channel, not merely as the EMG signal itself;
3. IMU as an independent EMG-validity context channel;
4. classification/action logic that gates downstream EMG interpretation;
5. field-specific failure modes such as settling, saturation, ghost coupling, and motion artifact.

---

## 22. DISCLOSURE / FILING NOTES

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

## 23. NEXT DRAFTING TASKS

- [ ] Create an attorney-facing one-page invention disclosure.
- [ ] Add system diagrams.
- [ ] Add example figures from existing paper outputs.
- [ ] Draft provisional specification sections in full prose.
- [ ] Draft 10–20 claim-style concepts.
- [ ] Build a public-disclosure timeline.
- [ ] List inventors and contributor roles.
- [ ] Identify closest prior art references.
- [ ] Decide whether to file before conference / journal submission.

---

## 24. ONE-PARAGRAPH ATTORNEY SUMMARY

This invention provides systems and methods for validating wearable EMG signal quality by combining a high-rate raw EMG channel, a simultaneously acquired hardware envelope channel, and IMU-derived motion context. A processor derives raw EMG amplitude or software-envelope features, compares them with the hardware envelope to detect saturation, flatline, contact degradation, electrode settling, and ghost-channel coupling, and uses IMU data to distinguish valid muscle activity from reduced movement intensity, impact artifact, or motion-contaminated EMG. The resulting signal-quality classification gates downstream EMG interpretation, including baseline selection and fatigue monitoring, by accepting, rejecting, delaying, down-weighting, correcting, or annotating EMG-derived metrics with a confidence score. The approach addresses practical field-deployment failures in dynamic wearable EMG that are not resolved by conventional raw-only EMG processing or generic EMG/IMU feature fusion.

---

## 25. CONCLUSION

The invention provides a **trustworthiness-first framework for wearable EMG systems**, in which physiological interpretation is conditioned on validated signal quality.

By integrating RAW EMG, hardware envelope signals, and IMU-based context, the system enables robust EMG analysis in dynamic, real-world environments where conventional approaches fail. The framework validates signal quality before interpreting EMG-derived physiological metrics, thereby improving reliability of wearable fatigue monitoring, activation tracking, rehabilitation assessment, sports analytics, occupational monitoring, and related applications.