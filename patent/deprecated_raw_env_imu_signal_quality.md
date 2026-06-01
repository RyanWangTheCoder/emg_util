# Provisional Patent Documentation Draft

# Systems and Methods for Signal-Quality Validation of Wearable Electromyography Using Simultaneous Raw EMG, Hardware Envelope, and Inertial Context

> Working document for invention disclosure / provisional patent preparation.  
> This is a technical drafting aid, not legal advice. A patent attorney should review before filing.

---

## 1. Working Title

**Systems and Methods for Signal-Quality Validation of Wearable Electromyography Using Simultaneous Raw EMG, Hardware Envelope, and Inertial Context**

Alternative titles:

1. **Reliability-Gated Wearable EMG Monitoring Using Raw/Envelope Consistency and IMU-Based Artifact Context**
2. **Methods for Validating and Improving Wearable EMG Signal Quality Using Hardware Envelope and Inertial Motion Data**
3. **Artifact-Aware Wearable Electromyography Using Raw EMG, Hardware Envelope, and Motion-Context Validation**
4. **Systems and Methods for Trustworthiness-Gated EMG Fatigue Monitoring in Dynamic Field Activity**

---

## 2. Short Invention Summary

The invention relates to validating and improving wearable electromyography (EMG) signal quality during dynamic real-world activity by using multiple simultaneously acquired signals from a wearable sensor system:

- a high-rate raw EMG channel;
- a low-rate or hardware-derived EMG envelope channel;
- inertial measurement unit (IMU) data including acceleration and/or gyroscope measurements.

The system derives signal-quality metrics by comparing raw EMG-derived amplitude or envelope features against the hardware envelope, and further interprets those metrics using IMU-derived motion context. The system can detect or classify signal-quality failure modes such as electrode settling, contact loss, hardware-envelope saturation, raw-channel flatline, ghost-signal coupling, movement artifact, impact artifact, reduced movement effort, or session discontinuity. Downstream EMG interpretations, including fatigue, activation, workload, or injury-risk metrics, may then be accepted, delayed, rejected, corrected, down-weighted, or annotated with a confidence score.

---

## 3. Core Problem Being Solved

Wearable EMG is valuable for monitoring muscle activity and fatigue during sports, rehabilitation, occupational work, and human-computer interaction. However, in real-world dynamic use, the EMG signal can be distorted by factors that are difficult to identify from raw EMG alone.

Important failure modes include:

1. **Electrode settling**
   - Dry or no-added-gel electrodes may require many minutes for the skin-electrode interface to stabilize.
   - During this period, EMG amplitude and spectral features can be distorted.

2. **Poor contact / contact loss**
   - Sweat, motion, snap-connector movement, skin stretch, or cable tugging can change contact quality.

3. **Motion artifact**
   - Rapid limb movement, vibration, impact, and cable motion can contaminate EMG windows.

4. **Hardware envelope saturation**
   - A low-rate hardware envelope may saturate even if the raw channel remains usable, reducing confidence in envelope-derived contact or activation metrics.

5. **Raw-channel flatline or ghost signal**
   - A high-impedance raw channel may fail mechanically and track another channel through ADC coupling or analog leakage.
   - The failure can pass visual inspection but disappear after filtering.

6. **Reduced movement effort confound**
   - EMG spectral or amplitude changes may reflect different movement intensity rather than muscle fatigue or physiology.

7. **BLE/session discontinuity**
   - Disconnected sessions or reconstructed timelines can create apparent baseline shifts that are not physiological.

Traditional EMG processing often assumes the input signal is valid. The invention treats wearable EMG analysis as a **signal-trustworthiness problem**: before interpreting EMG features physiologically, the system evaluates whether the EMG signal is reliable using hardware envelope consistency and inertial context.

---

## 4. Proposed Invention

The proposed invention is a system and method that receives synchronized or time-aligned raw EMG, hardware EMG envelope, and IMU data, and uses them to generate EMG signal-quality metrics and context-aware validity decisions.

At a high level, the method includes:

1. acquiring raw EMG samples from a wearable EMG sensor;
2. acquiring hardware envelope samples from the same or related EMG sensor;
3. acquiring IMU samples from the wearable system;
4. deriving a raw-based amplitude or software-envelope signal from the raw EMG;
5. comparing the raw-derived amplitude/envelope with the hardware envelope;
6. computing signal-quality metrics such as ratio, correlation, saturation, variance, flatline, and contact-quality scores;
7. computing IMU-derived context such as movement intensity, acceleration, gyroscope magnitude, impact, jerk, stillness, or event phase;
8. classifying EMG windows, events, bouts, or sessions as valid or affected by one or more failure modes;
9. modifying downstream EMG interpretation based on the classification.

---

## 5. System Architecture

### 5.1 Hardware Components

A representative embodiment includes:

| Component | Purpose |
|---|---|
| Raw EMG input | High-rate EMG waveform for spectral and amplitude analysis |
| Hardware EMG envelope input | Low-rate or analog-integrated envelope for amplitude/contact context |
| IMU | Acceleration and gyroscope data for motion context |
| Microcontroller | Sampling, timestamping, packetization, and optional real-time quality logic |
| BLE / wired / wireless transport | Streaming sensor data to a host or mobile device |
| Host / mobile processor | Signal-quality evaluation, fatigue monitoring, visualization, alerts |

The current project embodiment uses:

- MyoWare 2.0 EMG sensor with RAW and ENV outputs;
- ESP32 microcontroller;
- ICM-20948 IMU;
- BLE data streaming;
- host-side Python and/or Android analysis.

The invention is not limited to those components. Other EMG sensors, analog front ends, IMUs, wireless links, or processors may be used.

---

## 6. Data Streams

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

## 7. Raw-Derived Envelope Computation

A raw-derived software envelope may be computed from the raw EMG signal to compare with the hardware envelope.

A representative method:

1. estimate the raw EMG DC midpoint or baseline;
2. subtract the midpoint from each raw sample;
3. rectify the centered raw signal;
4. low-pass filter the rectified signal;
5. optionally scale or normalize the result to the hardware envelope.

Example:

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

---

## 8. Raw/Envelope Consistency Metrics

The system may compute one or more raw/envelope consistency metrics.

### 8.1 Amplitude Ratio

```text
raw_env_ratio = raw_rms / env_mean
```

or:

```text
raw_env_ratio = env_sw_scaled / env_hw
```

Uses:

- detect gain changes;
- detect contact changes;
- detect mismatch between raw and envelope behavior;
- detect periods where envelope is no longer a reliable contact proxy.

### 8.2 Correlation

```text
corr(raw_rms, env_mean)
corr(env_sw, env_hw)
corr(raw, env)
```

Uses:

- detect ghost-channel coupling;
- detect expected co-modulation;
- detect abnormal channel dependence.

A very high raw-to-envelope correlation combined with very low raw variance may indicate that the raw channel is not measuring independent muscle activity but is instead tracking the envelope or another analog channel.

### 8.3 Saturation Count

```text
n_env_saturated = count(env_hw >= saturation_threshold)
pct_env_saturated = n_env_saturated / n_events
```

Uses:

- detect hardware-envelope clipping;
- reduce confidence in envelope-derived contact or activation metrics;
- flag sessions where envelope data cannot be used as a reliable quality proxy.

### 8.4 Raw Flatline Detection

```text
raw_variance < flatline_threshold
```

or:

```text
raw_rms < minimum_activity_threshold during movement events
```

Uses:

- detect disconnected electrodes;
- detect failed raw input;
- detect post-filter flatline;
- detect dead channels.

### 8.5 Raw Variance / Dynamic Range

```text
raw_sd = standard_deviation(raw within window)
raw_peak_to_peak = max(raw) - min(raw)
```

Uses:

- distinguish true raw EMG from ghost signals;
- detect contact failure;
- detect insufficient signal amplitude.

### 8.6 Contact Quality Score

A relative contact quality score may be computed:

```text
contact_quality(t) = RMS_window(t) / session_p90_rms
```

or:

```text
contact_quality(event) = raw_rms(event) / percentile(raw_rms over session)
```

Uses:

- reject noise-dominated baseline windows;
- detect electrode settling;
- detect low-SNR windows;
- delay fatigue analysis until signal stabilizes.

---

## 9. IMU-Conditioned Validity Logic

The IMU provides independent context for interpreting EMG changes.

### 9.1 Diagnostic Matrix

| IMU / Session Context | EMG Observation | Likely Interpretation | System Action |
|---|---|---|---|
| Stable movement intensity | Early-session low MDF/MNF or low RMS that later recovers | Electrode settling or contact hydration | Delay baseline; exclude early windows |
| Stable movement intensity | Gradual post-settling MDF/MNF decline | Candidate local fatigue | Accept with confidence if quality metrics pass |
| Declining movement intensity | EMG spectral or amplitude decline | Reduced effort or changed biomechanics may contribute | Do not attribute to fatigue alone; annotate |
| Large transient acceleration / gyro / jerk | Isolated EMG spectral outlier | Motion or impact artifact | Flag, down-weight, or exclude |
| IMU quiet but high EMG noise | Electrical/contact artifact or muscle tension | Use contact/noise logic; classify separately |
| BLE/session discontinuity | EMG baseline shift across segments | Cross-session artifact | Analyze segments separately |
| Stable IMU but raw/envelope mismatch | Sensor/contact artifact | Warn user or reduce confidence |

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

## 10. Signal-Quality-Gated Baseline Selection

A representative baseline selection method:

1. collect candidate baseline events after an initial warmup or activity start;
2. compute raw EMG RMS for each candidate;
3. compute a robust high-percentile RMS reference, such as the 90th percentile;
4. reject candidates below a fraction of the reference, such as:

```text
rms_threshold = 0.25 * p90_rms
```

5. optionally require raw/envelope consistency;
6. optionally require no envelope saturation;
7. optionally require no raw flatline;
8. optionally require IMU movement intensity within an expected range;
9. compute baseline EMG features from accepted candidates.

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

## 11. Quality-Gated Fatigue or Activation Monitoring

Once signal quality is assessed, downstream metrics may be modified.

Examples:

### 11.1 Accept

If raw/envelope consistency is acceptable, IMU context is stable, and no artifacts are detected, the system accepts EMG-derived features.

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

## 12. Example Embodiments from Current Project

### 12.1 RAW/ENV Consistency Diagnostic

A 2×2 diagnostic can be generated:

- raw RMS vs hardware ENV scatter;
- raw/ENV ratio over time;
- envelope saturation count;
- raw flatline count.

Example outcomes from project data:

| Session | ENV Saturation | RAW Flatline | Interpretation |
|---|---:|---:|---|
| log0305 | 1.4% | 0% | Reliable primary session |
| log0303 | 14.2% | 0% | High ENV saturation; reduced confidence |

### 12.2 Ghost-Signal Detection

A field failure was observed where the raw EMG input tracked the hardware envelope due to a high-impedance pogo-pin routing failure and ADC multiplexer coupling.

Diagnostic signature:

- raw vs envelope correlation near 1.0;
- raw variance near zero;
- post-filter raw signal flatlines;
- hardware fix restores independent raw activity.

Generalized diagnostic:

```text
if corr(raw, env) > high_corr_threshold
and variance(raw) < low_variance_threshold
and filtered_raw_rms < flatline_threshold:
    classify as ghost_signal_or_raw_channel_failure
```

### 12.3 Electrode Settling

In field tennis data, early low RMS and depressed MDF later recovered as electrode contact improved. The system can identify this as settling rather than fatigue when:

- EMG MDF/MNF is low early;
- raw/contact quality metrics are poor;
- IMU swing intensity remains stable or does not explain the EMG anomaly;
- EMG features recover later.

### 12.4 IMU-Conditioned Interpretation

If IMU peak gyroscope magnitude remains stable over a session while EMG median frequency declines after contact quality stabilizes, the decline may be accepted as fatigue-consistent. If IMU intensity declines, the EMG change is annotated as movement-confounded.

### 12.5 Session-Gap Artifact

If a BLE reconnection or session discontinuity is detected, the system avoids comparing baseline and final features across the gap as though they were continuous physiological data.

---

## 13. Candidate Independent Claim Concepts

> These are technical brainstorming drafts, not attorney-reviewed legal claims.

### Claim Concept 1 — Method

A method for validating wearable electromyography signal quality, comprising:

1. receiving raw electromyography samples from a wearable electromyography sensor;
2. receiving hardware envelope samples acquired simultaneously with the raw electromyography samples;
3. receiving inertial measurement samples from a wearable inertial sensor;
4. computing a raw-derived amplitude signal from the raw electromyography samples;
5. comparing the raw-derived amplitude signal with the hardware envelope samples to determine at least one signal-quality metric;
6. determining a movement context from the inertial measurement samples;
7. classifying a time window, movement event, or session according to the signal-quality metric and the movement context; and
8. modifying interpretation of at least one electromyography-derived metric based on the classification.

### Claim Concept 2 — System

A wearable sensing system comprising:

- an electromyography sensor configured to output raw electromyography data and hardware envelope data;
- an inertial measurement unit configured to output motion data;
- one or more processors configured to:
  - derive an amplitude or envelope feature from the raw electromyography data;
  - compare the derived feature with the hardware envelope data;
  - determine a motion context from the motion data;
  - generate a signal-quality classification; and
  - gate, adjust, suppress, or annotate an electromyography-derived fatigue or activation metric based on the signal-quality classification.

### Claim Concept 3 — Baseline Gating

A method for selecting a wearable EMG baseline, comprising:

1. detecting movement events using IMU data;
2. extracting raw EMG features and hardware-envelope features for each movement event;
3. rejecting candidate baseline events based on one or more of low raw RMS, raw/envelope mismatch, envelope saturation, raw flatline, or abnormal IMU context;
4. computing a baseline from remaining candidate events; and
5. using the baseline to compute downstream EMG changes.

### Claim Concept 4 — Ghost Signal Detection

A method for detecting a failed raw EMG channel, comprising:

1. acquiring raw EMG and hardware envelope signals from a wearable EMG sensor;
2. computing correlation between the raw EMG signal and hardware envelope signal;
3. computing variance or dynamic range of the raw EMG signal;
4. filtering the raw EMG signal to remove low-frequency or envelope-like components;
5. classifying the raw EMG channel as failed or ghost-coupled when correlation is high, variance is low, and the filtered signal is flat or below a threshold.

### Claim Concept 5 — IMU Artifact Context

A method for identifying motion-contaminated EMG events, comprising:

1. detecting a movement event from IMU data;
2. extracting an EMG feature from a window around the movement event;
3. computing IMU shock, jerk, acceleration, or gyroscope features for the same window;
4. identifying the EMG feature as artifact-prone when it is an outlier and coincides with a high-motion or high-impact IMU feature;
5. down-weighting or excluding the EMG feature from fatigue or activation analysis.

---

## 14. Candidate Dependent Claim Features

Dependent claims may include:

- raw EMG sampled at 1000 Hz or higher;
- hardware envelope sampled at lower bandwidth than raw EMG;
- raw-derived envelope generated by DC tracking, rectification, and low-pass filtering;
- DC tracking using a slow low-pass filter;
- hardware envelope saturation threshold;
- raw flatline threshold;
- raw/envelope ratio;
- raw/envelope correlation;
- contact quality score based on RMS percentile;
- rejecting baseline windows below a fraction of a session RMS percentile;
- using IMU gyro magnitude for movement event detection;
- using IMU acceleration or jerk to detect impact artifacts;
- classifying electrode settling based on early low EMG quality with later recovery;
- classifying movement-confounded fatigue when IMU intensity decreases;
- outputting a confidence score;
- outputting a user instruction to adjust electrodes;
- applying to tennis, racket sports, throwing sports, rehabilitation, occupational ergonomics, e-sports, or gesture control;
- operating in real time on a mobile device;
- operating offline after session capture;
- preserving session discontinuities and preventing cross-gap baseline comparisons.

---

## 15. Advantages Over Conventional Approaches

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

Most EMG+IMU systems fuse both modalities as feature sources for activity or fatigue classification. The proposed system uses IMU as an independent validity channel to determine when EMG features are trustworthy.

### 15.4 Compared with Fixed Warmup

Fixed warmup intervals may fail when electrode settling duration varies. The proposed system can delay baseline selection until quality metrics indicate adequate signal validity.

---

## 16. Potential Figures for Provisional

1. **System block diagram**
   - RAW EMG + hardware ENV + IMU → quality evaluator → gated EMG analytics.

2. **Raw-derived envelope computation**
   - raw signal → DC tracker → rectifier → LPF → software envelope → comparison to hardware ENV.

3. **Quality decision matrix**
   - raw/envelope metrics combined with IMU context.

4. **Example RAW/ENV diagnostic**
   - raw RMS vs ENV scatter;
   - raw/ENV ratio over time.

5. **Ghost-signal diagnostic**
   - high raw/env correlation and raw flatline before fix;
   - independent raw after fix.

6. **Baseline gating flowchart**
   - collect candidates → quality filter → baseline finalization → fatigue output.

7. **IMU-conditioned interpretation**
   - stable IMU with early EMG recovery = settling;
   - stable IMU with late EMG decline = candidate fatigue.

---

## 17. Experimental Support to Include

### 17.1 log0305

- Continuous 63.1-min tennis session.
- 626 swings.
- Low ENV saturation: 1.4%.
- Zero RAW flatlines.
- Stable IMU swing-intensity proxy.
- Demonstrates reliable session after quality validation.

### 17.2 log0303

- Two BLE segments separated by a large gap.
- Higher ENV saturation: 14.2%.
- Zero RAW flatlines.
- Session discontinuity and contact-state change.
- Demonstrates need for quality and continuity validation.

### 17.3 Pogo-Pin Failure

- RAW channel failure caused ghost signal.
- Diagnostic: high raw/env correlation, near-zero raw variance, post-filter flatline.
- Fixed by solder bypass.
- Demonstrates practical value of raw/envelope consistency checks.

---

## 18. Potential Commercial / Application Areas

- Athletic training and fatigue monitoring.
- Tennis, baseball, golf, badminton, pickleball, rowing, cycling, running.
- Rehabilitation and physical therapy.
- Occupational ergonomics and worker fatigue.
- Human-computer interaction and gesture control.
- Prosthetic control.
- E-sports / fine motor monitoring.
- Remote health monitoring.
- Research-grade low-cost EMG acquisition.

---

## 19. Known Prior-Art Risk Areas

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

## 20. Disclosure / Filing Notes

Important issues to review with counsel:

1. **Public disclosure**
   - Determine whether GitHub, papers, posters, abstracts, PDFs, or presentations already publicly disclosed these ideas.
   - U.S. may have a one-year inventor grace period; many non-U.S. jurisdictions do not.

2. **Ownership**
   - Determine whether school, university, collaborators, funding, or employer policies affect ownership.

3. **Inventorship**
   - Identify who contributed to conception of the raw/envelope/IMU signal-quality validation approach.

4. **Filing strategy**
   - Consider filing a U.S. provisional before submitting or publishing additional manuscripts.

---

## 21. Next Drafting Tasks

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

## 22. One-Paragraph Attorney Summary

This invention provides systems and methods for validating wearable EMG signal quality by combining a high-rate raw EMG channel, a simultaneously acquired hardware envelope channel, and IMU-derived motion context. A processor derives raw EMG amplitude or software-envelope features, compares them with the hardware envelope to detect saturation, flatline, contact degradation, electrode settling, and ghost-channel coupling, and uses IMU data to distinguish valid muscle activity from reduced movement intensity, impact artifact, or motion-contaminated EMG. The resulting signal-quality classification gates downstream EMG interpretation, including baseline selection and fatigue monitoring, by accepting, rejecting, delaying, down-weighting, correcting, or annotating EMG-derived metrics with a confidence score. The approach addresses practical field-deployment failures in dynamic wearable EMG that are not resolved by conventional raw-only EMG processing or generic EMG/IMU feature fusion.