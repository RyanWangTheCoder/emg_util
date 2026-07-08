# Reverse Engineering Notes: Previous Low-Cost Wearable Fatigue / Overuse-Injury Research

**Project title from AAAS abstract:** Low Cost Wearable Kit and Algorithms to Predict and Prevent Muscle Overuse Injuries  
**Previous slide deck:** `fatigue_detection.pptx`  
**Original hardware generation:** Seeed Grove EMG Detector + Grove GSR Sensor + Arduino + Bluetooth / USB-serial  
**New hardware direction:** MyoWare EMG platform + IMU + mobile/cloud-ready data pipeline

> **Important scope note**  
> This document reconstructs the earlier research based on the AAAS abstract, the attached `fatigue_detection.pptx` deck, and public hardware documentation. It is intended for engineering/research documentation, not for medical diagnosis, treatment, or clinical claims.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Research Motivation](#2-research-motivation)
   - 2.1 [Problem](#21-problem)
   - 2.2 [Target Use Case](#22-target-use-case)
   - 2.3 [Core Research Hypothesis](#23-core-research-hypothesis)
3. [System Architecture Reconstructed from Previous Work](#3-system-architecture-reconstructed-from-previous-work)
   - 3.1 [Mobile / Bluetooth Path](#31-mobile--bluetooth-path)
   - 3.2 [Offline Data-Analysis Path](#32-offline-data-analysis-path)
4. [Hardware Components in the Previous Prototype](#4-hardware-components-in-the-previous-prototype)
   - 4.1 [EMG Sensor](#41-emg-sensor)
   - 4.2 [GSR Sensor](#42-gsr-sensor)
   - 4.3 [Arduino Board](#43-arduino-board)
   - 4.4 [Battery and Wearable Packaging](#44-battery-and-wearable-packaging)
5. [Data Collection and Processing Flow](#5-data-collection-and-processing-flow)
   - 5.1 [Acquisition](#51-acquisition)
   - 5.2 [Signal Processing Used in the Deck](#52-signal-processing-used-in-the-deck)
   - 5.3 [Reconstructed Processing Steps](#53-reconstructed-processing-steps)
6. [Algorithm Concept from Previous Research](#6-algorithm-concept-from-previous-research)
   - 6.1 [Personalized Baseline](#61-personalized-baseline)
   - 6.2 [Activity Magnitude Detection](#62-activity-magnitude-detection)
   - 6.3 [Overuse Pattern Detection](#63-overuse-pattern-detection)
   - 6.4 [Smart Coach App Concept](#64-smart-coach-app-concept)
7. [What the Previous Research Demonstrated](#7-what-the-previous-research-demonstrated)
8. [Gaps in the Previous Research Documentation](#8-gaps-in-the-previous-research-documentation)
   - 8.1 [Sampling and Timing](#81-sampling-and-timing)
   - 8.2 [EMG Signal Representation](#82-emg-signal-representation)
   - 8.3 [Sensor Placement](#83-sensor-placement)
   - 8.4 [Ground Truth Labels](#84-ground-truth-labels)
   - 8.5 [Fatigue-Specific Features](#85-fatigue-specific-features)
9. [Limitation of the Seeed EMG Sensor Platform](#9-limitation-of-the-seeed-emg-sensor-platform)
   - 9.1 [Main Limitation: No Documented RAW EMG Output](#91-main-limitation-no-documented-raw-emg-output)
   - 9.2 [Why RAW Matters for Fatigue Detection](#92-why-raw-matters-for-fatigue-detection)
   - 9.3 [Lack of Motion Context](#93-lack-of-motion-context)
   - 9.4 [Limited Multi-Session Reproducibility](#94-limited-multi-session-reproducibility)
   - 9.5 [Summary of Practical Seeed Limitations](#95-summary-of-practical-seeed-limitations)
10. [Key Differences: Seeed Grove EMG Detector vs. MyoWare EMG Sensor](#10-key-differences-seeed-grove-emg-detector-vs-myoware-emg-sensor)
11. [Rationale for Moving to the New MyoWare + IMU Platform](#11-rationale-for-moving-to-the-new-myoware--imu-platform)
    - 11.1 [Richer EMG Output Modes](#111-richer-emg-output-modes)
    - 11.2 [Better Fatigue Feature Extraction](#112-better-fatigue-feature-extraction)
    - 11.3 [IMU-Based Validity Context](#113-imu-based-validity-context)
    - 11.4 [Better Fit for Personalized Multi-Session Modeling](#114-better-fit-for-personalized-multi-session-modeling)
    - 11.5 [Stronger Research Contribution](#115-stronger-research-contribution)
12. [Recommended Structure for the Next Research Document / Paper](#12-recommended-structure-for-the-next-research-document--paper)
13. [Source Traceability](#13-source-traceability)
    - 13.1 [Sources from Previous Project Materials](#131-sources-from-previous-project-materials)
    - 13.2 [Public Hardware References](#132-public-hardware-references)
14. [Concise Summary](#14-concise-summary)

---

## 1. Executive Summary

The earlier research explored a low-cost wearable sensing kit to detect muscle activity, fatigue-related patterns, perspiration response, and activity context for overuse-injury prevention. The concept was to measure physiological and activity signals during tennis or other repetitive activity, derive user-specific baselines, and generate early warnings before discomfort or pain becomes apparent.

The prototype used:

- **EMG sensor** for muscle activity.
- **GSR sensor** for perspiration / skin response.
- **Arduino** for sensor acquisition and simple embedded processing.
- **Bluetooth link** to an Android phone for a “Smart coach App” path.
- **USB/Serial link** to a Windows PC for offline Python-based data processing.

The previous system successfully demonstrated that EMG signal magnitude changes can distinguish “no muscle contraction” from “muscle contraction,” especially after smoothing. However, the Seeed Grove EMG Detector exposes only a processed analog output path documented as amplified and filtered, with no documented raw EMG output. This limits advanced fatigue characterization, signal-quality validation, motion-artifact rejection, and reproducible ML feature extraction.

The new MyoWare + IMU platform is therefore motivated by the need to capture richer EMG representations, including raw / rectified / envelope signals where available, and to align EMG activity with motion context from IMU data. This enables a more robust fatigue and overuse-risk pipeline.

---

## 2. Research Motivation

### 2.1 Problem

Overuse injuries can disrupt daily life, reduce athletic performance, and potentially lead to long-term damage. Traditional treatment pathways are often reactive: intervention starts after discomfort, pain, or injury symptoms have already appeared. The previous research aimed to shift the focus from **post-injury treatment** to **early detection and prevention**.

### 2.2 Target Use Case

The slide deck frames the application as an **“Injury prevention - Smart tennis assistant.”** The intended system watches physiological signals during sports activity and provides actionable feedback through a mobile application.

### 2.3 Core Research Hypothesis

The central idea was:

> If muscle activity, perspiration, and activity patterns are monitored continuously and interpreted relative to each user’s personal baseline, then early warning indicators of excessive load or fatigue may be detected before overuse injury symptoms become severe.

---

## 3. System Architecture Reconstructed from Previous Work

The previous prototype had two operating modes.

### 3.1 Mobile / Bluetooth Path

```text
EMG sensor  ┐
            ├──> Arduino ── Bluetooth ──> Android phone ──> Smart coach app
GSR sensor  ┘
```

Purpose:

- Demonstrate a low-cost wearable kit.
- Stream sensor-derived signals to a phone.
- Provide a path toward real-time feedback or warnings.

### 3.2 Offline Data-Analysis Path

```text
EMG sensor  ┐
            ├──> Arduino ── USB/Serial ──> Windows PC ──> Python data processing
GSR sensor  ┘
```

Purpose:

- Capture sensor data for analysis.
- Validate signal behavior visually.
- Develop and test smoothing / feature-extraction logic.
- Separate experimental analysis from the mobile-app implementation.

---

## 4. Hardware Components in the Previous Prototype

### 4.1 EMG Sensor

The previous prototype used the **Seeed Grove EMG Detector**. Public Seeed documentation describes the module as collecting small muscle signals and processing them with amplification and filtering so that the output signal can be recognized by Arduino. The Seeed documentation also states:

- The module is Grove-compatible.
- It uses a 3.5 mm connector and disposable surface electrodes.
- Power supply voltage is 3.3 V to 5 V.
- In standby mode, output voltage is about 1.5 V.
- When muscle activity is detected, the output signal rises, with maximum voltage about 3.3 V.
- Hardware overview lists a Grove analog I/O interface, electrode connector, difference amplifier, and zero-drift amplifiers.

Engineering interpretation for the previous study:

- The Arduino likely sampled the Seeed module’s processed analog output.
- The observed output represented a conditioned muscle-activity signal rather than raw differential electrode potential.
- This was sufficient for early proof-of-concept contraction detection.

### 4.2 GSR Sensor

The previous prototype included a GSR sensor for perspiration / galvanic skin response. The AAAS abstract describes perspiration profile establishment and use of relative changes from relaxed or low-intensity baselines.

Engineering interpretation:

- GSR was used as a supporting physiological stress / exertion indicator.
- GSR alone is not muscle-specific, so it should be treated as a contextual signal rather than a direct fatigue marker.

### 4.3 Arduino Board

The Arduino board acted as the first-generation acquisition and transport controller:

- Reads EMG and GSR analog values.
- Sends data to either:
  - Android phone over Bluetooth, or
  - Windows PC over USB/Serial.

### 4.4 Battery and Wearable Packaging

The slide deck photo shows a battery, EMG electrodes, GSR sensor, wiring, and Arduino board. This indicates the previous design was already exploring a portable, low-cost, wearable-style kit, even if the integration was still prototyping-level.

---

## 5. Data Collection and Processing Flow

### 5.1 Acquisition

The previous data pipeline can be reconstructed as:

```text
Surface electrodes / GSR electrodes
        ↓
Analog sensor front-end modules
        ↓
Arduino ADC sampling
        ↓
Serial/Bluetooth packet stream
        ↓
Python analysis or Android application
        ↓
Feature extraction / smoothing / warning logic
```

### 5.2 Signal Processing Used in the Deck

The slide deck shows EMG data before and after moving-average smoothing. It labels two visually distinguishable regions:

- **No muscle contraction**
- **Muscle contraction**

The smoothed signal preserves the activity bursts while reducing high-frequency variation in the displayed trace. The previous analysis appears to have focused on amplitude-based activity detection rather than frequency-domain fatigue estimation.

### 5.3 Reconstructed Processing Steps

The likely processing chain was:

1. Collect Arduino analog values over time.
2. Plot original EMG sensor data against time.
3. Apply moving-average smoothing.
4. Compare baseline / relaxed periods against active contraction periods.
5. Use relative changes to identify muscle activity magnitude.
6. Combine with GSR trend and activity assumptions to reason about overuse-risk patterns.

---

## 6. Algorithm Concept from Previous Research

### 6.1 Personalized Baseline

The AAAS abstract describes creating personalized muscle activity and perspiration profiles using low-intensity and relaxed periods. This is important because absolute EMG and GSR values vary substantially across users, electrode placement, skin condition, hydration, sensor gain, and environment.

Baseline concept:

```text
relative_EMG_activity = current_EMG_feature / personal_relaxed_or_low_intensity_EMG_baseline
relative_GSR_change   = current_GSR_feature - personal_relaxed_or_low_intensity_GSR_baseline
```

The exact formulas were not specified in the slide deck, so the equations above should be treated as a documentation-friendly reconstruction of the intended baseline-normalization idea rather than the exact historical implementation.

### 6.2 Activity Magnitude Detection

The previous system used EMG amplitude behavior to separate:

- Relaxed / low-activity muscle state.
- Active contraction state.
- Repeated bursts of contraction.

This maps well to tennis, where repeated strokes create bursts of forearm muscle activation.

### 6.3 Overuse Pattern Detection

The AAAS abstract references clinical insights around overuse-causing patterns such as:

- Excessive muscle activity.
- High volume of load.
- Repeated activity patterns.

A reconstructed algorithmic approach is:

```text
For each time window:
    compute EMG activity magnitude
    compute activity burst count / duty cycle
    compute accumulated load proxy over session
    compute GSR / perspiration trend relative to baseline
    compare with personalized thresholds
    issue early warning if sustained high activity or abnormal trend is detected
```

### 6.4 Smart Coach App Concept

The intended mobile app would receive sensor-derived metrics and provide warnings or guidance, such as:

- Current muscle activity level.
- Accumulated activity load.
- Abnormal perspiration / exertion signal.
- Rest recommendation or warning if activity remains elevated.

---

## 7. What the Previous Research Demonstrated

Based on the deck and abstract, the previous project demonstrated:

1. **Feasibility of low-cost wearable sensing** using commodity EMG/GSR sensors and Arduino.
2. **Feasibility of mobile connectivity** via Bluetooth to an Android phone concept.
3. **Feasibility of offline data analysis** using USB/Serial to Windows PC and Python.
4. **Observable EMG activity patterns** where muscle contraction periods can be separated from no-contraction periods.
5. **Basic smoothing and visualization** to make activity bursts easier to interpret.
6. **Personalization concept** using low-intensity / relaxed baselines and relative changes.

---

## 8. Gaps in the Previous Research Documentation

The previous deck is useful as a proof-of-concept snapshot, but several details are missing or not fully specified:

### 8.1 Sampling and Timing

Not documented:

- Arduino sampling rate.
- ADC resolution.
- Timestamp precision.
- Bluetooth packet format.
- Whether samples were uniformly timed.

Why this matters:

- Fatigue estimation from EMG often depends on consistent sampling and frequency-domain features.
- Without timestamps and sampling-rate control, frequency analysis and multi-session reproducibility are hard.

### 8.2 EMG Signal Representation

The deck shows “original sensor data” and “smoothed data,” but it does not define whether the original signal was:

- Raw EMG,
- rectified EMG,
- envelope-like output,
- or another vendor-conditioned analog signal.

From the Seeed documentation, the output is a processed signal after amplification and filtering, and the public interface is a Grove analog output.

### 8.3 Sensor Placement

The deck photo shows electrode wiring, but the exact muscle placement is not documented:

- Target muscle group.
- Electrode spacing.
- Electrode orientation along muscle fibers.
- Reference electrode location.

Why this matters:

- EMG amplitude and spectral content are highly sensitive to placement.
- Without placement documentation, results are hard to reproduce.

### 8.4 Ground Truth Labels

The slides label no-contraction and contraction regions visually, but do not document:

- How labels were collected.
- Whether fatigue labels were self-reported.
- Whether pain or exertion scores were recorded.
- Whether labels were synchronized with the sensor stream.

### 8.5 Fatigue-Specific Features

The deck demonstrates contraction detection. It does not show fatigue-specific features such as:

- Median frequency / mean frequency shift.
- RMS trend across repeated contractions.
- Muscle activation duty cycle over a session.
- Recovery-rate metrics between bursts.
- Signal-quality or motion-artifact rejection.

This is understandable for a first prototype, but it is a major gap for a research paper focused on fatigue or overuse-risk prediction.

---

## 9. Limitation of the Seeed EMG Sensor Platform

### 9.1 Main Limitation: No Documented RAW EMG Output

The Seeed Grove EMG Detector documentation describes a module that gathers small muscle signals and processes them with amplification and filtering for Arduino-readable output. The public hardware overview lists the Grove analog I/O interface and amplifier stages, but the documentation does not expose a separate raw EMG output mode.

This creates a practical limitation:

> The previous platform appears suitable for coarse muscle-activity detection, but not ideal for research-grade fatigue feature extraction that requires access to raw or minimally processed EMG.

Important nuance:

- This does **not** prove that raw signal access is physically impossible by modifying the board.
- It means the documented, supported product interface does not provide a clean raw EMG output comparable to MyoWare’s documented RAW output.

### 9.2 Why RAW Matters for Fatigue Detection

Raw or minimally processed EMG is valuable because it enables:

- Better motion-artifact detection.
- Frequency-domain fatigue features such as median-frequency shift.
- Comparison between raw, rectified, and envelope features.
- Signal-quality gating based on waveform consistency.
- Reproducible ML-ready feature extraction.
- Separation of physiological change from vendor front-end behavior.

If only a smoothed or envelope-like processed output is available, many fatigue signatures may be suppressed, distorted, or made unavailable.

#### 9.2.1 Preserves waveform information

RAW EMG preserves high-frequency waveform behavior that is largely hidden once the signal is converted into a smoothed envelope. This matters because many fatigue-related EMG features depend on the raw waveform or its spectrum. MyoWare's documented RAW output gives access to that waveform, whereas the Seeed sensor's documented interface provides only a processed analog output. [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html), [\[wiki.seeedstudio.com\]](https://wiki.seeedstudio.com/Grove-EMG_Detector/), [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/technical-specifications/)

Engineering implication:

- With Seeed, we can mostly track "activity magnitude."
- With MyoWare RAW, we can analyze how the signal shape and spectral content change as fatigue develops.

#### 9.2.2 Enables frequency-domain fatigue features

A common fatigue-analysis direction is to evaluate whether EMG spectral content shifts during sustained or repeated contraction. RAW EMG is much more suitable for this than a smoothed envelope because the envelope intentionally removes much of the faster waveform variation. MyoWare's RAW output therefore enables features such as median-frequency trend, mean-frequency trend, spectral centroid, or band-power ratios. The availability of RAW output and filter path is documented; the specific feature list is an engineering recommendation for the fatigue-analysis pipeline. [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/technical-specifications/)

#### 9.2.3 Enables raw-vs-envelope consistency checks

Because MyoWare provides RAW, RECT, and ENV signal representations, we can compare whether the envelope behavior is consistent with the underlying raw waveform. [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/muscle-sensor/)

Engineering implication:

```text
If envelope increases but RAW signal quality is poor:
    possible motion artifact, electrode issue, or saturation

If RAW and envelope both show consistent activation:
    higher confidence in true muscle activity
```

This directly supports reliability-gated EMG: the algorithm should not trust an envelope-level increase unless the raw signal supports it.

#### 9.2.4 Helps detect artifacts and poor electrode contact

RAW EMG makes it easier to inspect abnormal waveform behavior such as sudden spikes, clipping, baseline drift, or electrode motion artifacts. For tennis specifically, forearm motion, racket impact, sweat, and electrode movement can all contaminate EMG. RAW data plus IMU context gives a much better chance of rejecting bad windows. The artifact-detection use is an engineering interpretation of why raw waveform access is valuable. [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/technical-specifications/)

#### 9.2.5 Supports ML-ready feature extraction

With RAW + RECT + ENV, the dataset can include multiple feature families:

```text
RAW EMG features:
  - RMS, waveform length, zero crossings, slope sign changes
  - spectral features (median/mean frequency, band-power ratios)

RECT features:
  - rectified amplitude statistics
  - burst shape, activation duration

ENV features:
  - smooth activation magnitude
  - duty cycle, cumulative load proxy, recovery slope
```

The availability of RAW/RECT/ENV is supported by MyoWare documentation; the feature set above is a proposed research feature design. [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/technical-specifications/)

### 9.3 Lack of Motion Context

The Seeed EMG + GSR + Arduino prototype did not include an IMU in the documented architecture. Without IMU context, it is difficult to distinguish:

- True muscle activation.
- Electrode motion artifact.
- Arm movement without target muscle fatigue.
- Tennis stroke phase.
- Rest periods versus active hitting.

This is especially important for tennis, where wrist/forearm motion and impact vibration can contaminate EMG measurements.

### 9.4 Limited Multi-Session Reproducibility

The first-generation setup did not document a complete multi-session calibration procedure. For overuse-risk prediction, the system needs consistency across days or weeks:

- Sensor placement repeatability.
- Baseline re-establishment.
- Session metadata.
- Activity-load accumulation.
- Ground-truth fatigue / pain / exertion labels.

### 9.5 Summary of Practical Seeed Limitations

- **No documented RAW EMG output** in the normal supported interface. This limits access to the original waveform needed for deeper fatigue analysis. [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html), [\[wiki.seeedstudio.com\]](https://wiki.seeedstudio.com/Grove-EMG_Detector/)
- **Limited signal-chain transparency** compared with MyoWare. Seeed documents amplification/filtering and amplifier components, but does not provide the same explicit RAW/RECT/ENV signal-path definitions as MyoWare. [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html), [\[wiki.seeedstudio.com\]](https://wiki.seeedstudio.com/Grove-EMG_Detector/)
- **Better suited for contraction detection than fatigue characterization.** The old slides show useful amplitude-based contraction/no-contraction separation after smoothing, but do not show raw EMG or fatigue-specific spectral features. [\[fatigue_detection \| PowerPoint\]](https://qualcomm-my.sharepoint.com/personal/wangx_qti_qualcomm_com/_layouts/15/Doc.aspx?sourcedoc=%7B23734B67-B680-4551-915B-F9C388D3F67C%7D&file=fatigue_detection.pptx&action=edit&mobileredirect=true)
- **No built-in motion context.** The previous documented system combined EMG + GSR + Arduino, but not IMU. Motion artifact and tennis stroke context were not directly captured. [\[fatigue_detection \| PowerPoint\]](https://qualcomm-my.sharepoint.com/personal/wangx_qti_qualcomm_com/_layouts/15/Doc.aspx?sourcedoc=%7B23734B67-B680-4551-915B-F9C388D3F67C%7D&file=fatigue_detection.pptx&action=edit&mobileredirect=true)
- **Harder to build a reproducible ML dataset.** Without raw signal, clear output modes, and motion context, it is harder to distinguish true physiological fatigue from placement changes, movement artifacts, or front-end processing effects. [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html), [\[wiki.seeedstudio.com\]](https://wiki.seeedstudio.com/Grove-EMG_Detector/)

---

## 10. Key Differences: Seeed Grove EMG Detector vs. MyoWare EMG Sensor

| Area                                             | Seeed Grove EMG Detector                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | MyoWare / MyoWare 2.0                                                                                                                                                                                                                                                                                                                                                        | Why it matters for our fatigue/overuse project                                                                                     |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **Primary design goal**                          | Simple Grove-compatible EMG detector for Arduino-readable muscle activity output. Seeed describes it as gathering small muscle signals, then amplifying/filtering them so Arduino can recognize the signal. [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html), [\[wiki.seeedstudio.com\]](https://wiki.seeedstudio.com/Grove-EMG_Detector/)                                                                                                                    | More complete EMG sensor ecosystem designed for Arduino-compatible muscle sensing, with compact wearable form factor and multiple output modes. [\[learn.sparkfun.com\]](https://learn.sparkfun.com/tutorials/getting-started-with-the-myoware-20-muscle-sensor-ecosystem/all), [\[sparkfun.com\]](https://www.sparkfun.com/myoware)                  | Seeed is good for proof-of-concept contraction detection; MyoWare is better for research-grade signal analysis.                    |
| **Output signal types**                          | Public documentation describes one processed analog output through Grove analog I/O. It documents standby output around **1.5 V** and activity rising up to about **3.3 V**, but does **not** document separate RAW / RECT / ENV output modes. [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html), [\[wiki.seeedstudio.com\]](https://wiki.seeedstudio.com/Grove-EMG_Detector/)                                                                                 | MyoWare 2.0 explicitly documents **three output modes**: EMG Envelope, Rectified EMG, and Raw EMG. [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/muscle-sensor/)                                                                                                                        | This is the biggest difference. RAW/RECT/ENV access enables better fatigue features and signal-quality validation.                 |
| **RAW EMG access**                               | No documented RAW EMG output in the normal supported interface. The documented output is already amplified/filtered for Arduino use. [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html), [\[wiki.seeedstudio.com\]](https://wiki.seeedstudio.com/Grove-EMG_Detector/)                                                                                                                                                                                           | RAW output is explicitly documented as an available output mode; MyoWare also documents rectified and envelope outputs. [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/technical-specifications/)                                                                                        | RAW access is important for frequency-domain fatigue analysis, artifact checks, and ML-ready feature extraction.                   |
| **Signal processing transparency**               | Seeed documentation mentions amplification and filtering, and lists amplifier components, but provides limited detail about the exact signal-processing chain exposed to the user. [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html), [\[wiki.seeedstudio.com\]](https://wiki.seeedstudio.com/Grove-EMG_Detector/)                                                                                                                                             | MyoWare documentation gives more explicit signal-chain information: raw gain, rectified gain, envelope gain, high-pass filter around 20.8 Hz, low-pass filter around 498.4 Hz, envelope detection around 3.6 Hz, and full-wave rectification. [\[myoware.com\]](https://myoware.com/products/technical-specifications/)                         | MyoWare is easier to document scientifically because the output modes and filtering behavior are better specified.                 |
| **Ease of early prototyping**                    | Very simple Grove interface; good fit for Arduino + Grove ecosystem. Previous project used this style with EMG, GSR, Arduino, Bluetooth/Android, and USB/Python paths. [\[fatigue_detection \| PowerPoint\]](https://qualcomm-my.sharepoint.com/personal/wangx_qti_qualcomm_com/_layouts/15/Doc.aspx?sourcedoc=%7B23734B67-B680-4551-915B-F9C388D3F67C%7D&file=fatigue_detection.pptx&action=edit&mobileredirect=true), [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html) | Also Arduino-compatible, but MyoWare 2.0 has a broader shield/snap ecosystem and multiple signal output options. [\[learn.sparkfun.com\]](https://learn.sparkfun.com/tutorials/getting-started-with-the-myoware-20-muscle-sensor-ecosystem/all), [\[sparkfun.com\]](https://www.sparkfun.com/myoware)                                                 | Seeed was enough for the AAAS-stage demo; MyoWare gives more room for the next research phase.                                     |
| **Electrode / wearable integration**             | Uses disposable surface electrodes and 3.5 mm connector/cable style. [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html), [\[wiki.seeedstudio.com\]](https://wiki.seeedstudio.com/Grove-EMG_Detector/)                                                                                                                                                                                                                                                           | MyoWare 2.0 supports direct electrode pad connectors, snap connectors, and shields; documentation emphasizes compact design and solderless ecosystem. [\[learn.sparkfun.com\]](https://learn.sparkfun.com/tutorials/getting-started-with-the-myoware-20-muscle-sensor-ecosystem/all), [\[myoware.com\]](https://myoware.com/products/muscle-sensor/) | MyoWare may be cleaner for wearable setup and repeatable experiments, though electrode placement still needs careful protocol.     |
| **Fatigue feature potential**                    | Best suited for coarse amplitude/activity detection, such as relaxed vs. contraction periods. Your old slides show this kind of result: original sensor data and moving-average-smoothed EMG separating no-contraction and contraction regions. [\[fatigue_detection \| PowerPoint\]](https://qualcomm-my.sharepoint.com/personal/wangx_qti_qualcomm_com/_layouts/15/Doc.aspx?sourcedoc=%7B23734B67-B680-4551-915B-F9C388D3F67C%7D&file=fatigue_detection.pptx&action=edit&mobileredirect=true)         | Supports richer feature extraction from raw, rectified, and envelope signals. MyoWare docs explicitly expose the signal representations needed for more advanced processing. [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/technical-specifications/)                                   | For fatigue detection, MyoWare is much stronger because fatigue analysis often needs more than a single processed amplitude trace. |
| **Compatibility with IMU-based validity gating** | Seeed EMG itself does not provide IMU context; the previous platform documented EMG + GSR, not EMG + IMU. [\[fatigue_detection \| PowerPoint\]](https://qualcomm-my.sharepoint.com/personal/wangx_qti_qualcomm_com/_layouts/15/Doc.aspx?sourcedoc=%7B23734B67-B680-4551-915B-F9C388D3F67C%7D&file=fatigue_detection.pptx&action=edit&mobileredirect=true)                                                                                                                                               | MyoWare also does not itself imply an IMU, but because it provides richer EMG outputs, it pairs better with a separate IMU for motion-context validation. [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/technical-specifications/)                                                      | For tennis, IMU helps separate true muscle activity from motion artifact, swing phase, and impact-related noise.                   |

### Sensor Data Quality Comparison

| Dimension                            | Seeed Grove EMG Detector                                                                                                                                                                                                                                                                                                                                     | MyoWare / MyoWare 2.0                                                                                                                                                                                                                                                                                                                                                                             | Practical impact                                                          |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **Documented output type**           | Processed analog output for Arduino. Standby around 1.5 V; muscle activity rises toward 3.3 V. [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html), [\[wiki.seeedstudio.com\]](https://wiki.seeedstudio.com/Grove-EMG_Detector/)                                                                             | Explicitly documents **EMG Envelope**, **Rectified EMG**, and **Raw EMG** output modes. [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/muscle-sensor/)                                                                                                                                                        | MyoWare provides richer signal representations for analysis.              |
| **RAW signal availability**          | No documented RAW output mode in public interface. [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html), [\[wiki.seeedstudio.com\]](https://wiki.seeedstudio.com/Grove-EMG_Detector/)                                                                                                                         | RAW output is explicitly documented; MyoWare describes raw, rectified, and envelope paths. [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/technical-specifications/)                                                                                                                                          | MyoWare is better for fatigue and signal-quality research.                |
| **Signal-chain documentation**       | Documents amplifier/filter concept and hardware components such as difference amplifier and zero-drift amplifiers. [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html), [\[wiki.seeedstudio.com\]](https://wiki.seeedstudio.com/Grove-EMG_Detector/)                                                         | Documents gain equations, high-pass filter around 20.8 Hz, low-pass filter around 498.4 Hz, envelope detection around 3.6 Hz, and full-wave rectification. [\[myoware.com\]](https://myoware.com/products/technical-specifications/)                                                                                                                                 | MyoWare is easier to describe in a research paper.                        |
| **Previous observed data quality**   | Old deck shows enough signal separation to identify contraction vs. no contraction after smoothing. [\[fatigue_detection \| PowerPoint\]](https://qualcomm-my.sharepoint.com/personal/wangx_qti_qualcomm_com/_layouts/15/Doc.aspx?sourcedoc=%7B23734B67-B680-4551-915B-F9C388D3F67C%7D&file=fatigue_detection.pptx&action=edit&mobileredirect=true) | Public docs show multiple output options and more detailed signal-path support; the new board can use this for richer analysis. [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/technical-specifications/)                                                                                                    | Seeed is enough for proof-of-concept; MyoWare supports deeper analysis.   |
| **Use for ML-ready fatigue dataset** | Limited because only a processed activity-like output is documented. [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html), [\[wiki.seeedstudio.com\]](https://wiki.seeedstudio.com/Grove-EMG_Detector/)                                                                                                       | Stronger because RAW/RECT/ENV outputs enable multiple feature families and cross-checks. [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/technical-specifications/)                                                                                                                                            | MyoWare better supports robust feature extraction and reliability gating. |
| **Wearable integration**             | Grove/cable style with disposable electrodes and 3.5 mm connector. [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html), [\[wiki.seeedstudio.com\]](https://wiki.seeedstudio.com/Grove-EMG_Detector/)                                                                                                         | MyoWare 2.0 uses a compact design, snap connector system, and shield ecosystem; documentation describes direct electrode pad connectors and solderless shield connections. [\[learn.sparkfun.com\]](https://learn.sparkfun.com/tutorials/getting-started-with-the-myoware-20-muscle-sensor-ecosystem/all), [\[myoware.com\]](https://myoware.com/products/muscle-sensor/) | MyoWare is cleaner for repeated wearable experiments.                     |

**Seeed data quality** is acceptable for detecting whether the muscle is active or inactive — the previous slides show that this signal can clearly reflect contraction periods after smoothing. The **MyoWare data quality** is more useful for research because it exposes multiple signal representations with explicit RAW, rectified, and envelope outputs plus filtering and rectification details.

> **Seeed gives a simple activity signal; MyoWare gives analyzable EMG signal representations.**

### Bottom Line

**Seeed Grove EMG Detector** was a good first-generation sensor for demonstrating that low-cost EMG can detect muscle contraction and support a basic smart-coach concept. It fits well with Arduino/Grove prototyping and the earlier AAAS-stage proof of concept. [\[fatigue_detection \| PowerPoint\]](https://qualcomm-my.sharepoint.com/personal/wangx_qti_qualcomm_com/_layouts/15/Doc.aspx?sourcedoc=%7B23734B67-B680-4551-915B-F9C388D3F67C%7D&file=fatigue_detection.pptx&action=edit&mobileredirect=true), [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html)

**MyoWare is the better platform for the next research phase** because it explicitly provides RAW, rectified, and envelope EMG outputs, and its documentation gives clearer signal-chain details. That makes it much more suitable for fatigue detection, raw/envelope consistency checks, motion-artifact rejection, feature extraction, and ML-ready dataset generation. [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/technical-specifications/)

> **The Seeed platform proved feasibility; the MyoWare + IMU platform enables scientifically stronger fatigue and overuse-risk modeling.**

---

## 11. Rationale for Moving to the New MyoWare + IMU Platform

### 11.1 Richer EMG Output Modes

MyoWare 2.0 documentation describes three output modes:

- EMG Envelope.
- Rectified EMG.
- Raw EMG.

It also provides technical details such as high-pass and low-pass filtering, full-wave rectification, envelope detection, and analog gain definitions. This directly supports a more research-oriented feature pipeline than the Seeed Grove EMG Detector.

### 11.2 Better Fatigue Feature Extraction

With access to raw / rectified / envelope signals, the new platform can support:

- Time-domain features: RMS, MAV, waveform length, zero crossings, slope sign changes.
- Frequency-domain features: median frequency, mean frequency, spectral centroid, high/low band power ratio.
- Envelope/load features: duty cycle, burst duration, cumulative activation, recovery slope.
- Reliability features: raw-vs-envelope consistency, saturation detection, dropout detection.

### 11.3 IMU-Based Validity Context

Adding an IMU enables the EMG signal to be interpreted with motion context:

- Detect stroke events and high-acceleration periods.
- Identify periods likely contaminated by motion artifact.
- Separate true muscle fatigue from gross motion intensity.
- Segment sessions into swings, rallies, rest, and recovery windows.
- Align muscle activity with forearm movement patterns.

### 11.4 Better Fit for Personalized Multi-Session Modeling

The new platform supports the next phase of the research:

```text
Session data collection
    ↓
Per-user baseline and sensor-quality calibration
    ↓
Window-level EMG + IMU feature extraction
    ↓
Session-level fatigue and load accumulation metrics
    ↓
Multi-session trend modeling
    ↓
Personalized overuse-risk warning
```

This aligns better with the goal of preventing overuse injuries, not merely detecting individual contraction bursts.

### 11.5 Stronger Research Contribution

The earlier work was valuable as a feasibility prototype. The new platform can elevate the work toward a stronger research contribution by adding:

- Better raw data access.
- Multi-sensor fusion.
- Reliability gating.
- Personalized baseline modeling.
- Reproducible data collection protocol.
- ML-ready dataset generation.

---

## 12. Recommended Structure for the Next Research Document / Paper

A strong follow-up paper or project report can use this structure:

1. **Introduction**
   - Overuse injury problem.
   - Need for proactive, low-cost, personalized monitoring.

2. **Related Work**
   - Wearable EMG for fatigue.
   - IMU-based sports activity recognition.
   - Multi-sensor fatigue / load monitoring.

3. **Previous Prototype and Lessons Learned**
   - Seeed EMG + GSR + Arduino architecture.
   - Proof-of-concept contraction detection.
   - Limitations of processed-only EMG and no IMU.

4. **New System Design**
   - MyoWare EMG platform.
   - IMU placement and sampling.
   - Mobile app / data logger.
   - User profile and baseline calibration.

5. **Signal Processing Pipeline**
   - Raw / rectified / envelope extraction.
   - EMG quality checks.
   - IMU segmentation.
   - Feature windows.

6. **Personalized Fatigue and Overuse-Risk Algorithm**
   - Baseline normalization.
   - Session load metrics.
   - Multi-session trend modeling.
   - Warning logic.

7. **Experimental Protocol**
   - Tennis sessions.
   - Sensor placement.
   - Ground-truth fatigue/pain/exertion labels.
   - Repeated sessions over days/weeks.

8. **Results**
   - Signal examples.
   - Fatigue trend examples.
   - Classifier/regression performance.
   - Ablation: EMG only vs EMG + IMU.

9. **Limitations and Safety Scope**
   - Not a medical diagnostic device.
   - Limited participants.
   - Sensor placement variability.
   - Need for broader validation.

10. **Conclusion**
    - Low-cost wearable approach is promising.
    - New platform addresses key limitations of the first prototype.

---

## 13. Source Traceability

### 13.1 Sources from Previous Project Materials

- `fatigue_detection.pptx`
  - Slide 1: “Injury prevention - Smart tennis assistant.”
  - Slide 2: content list: problem statement, literature, Arduino/BT/Android, sensor experiments, data analysis.
  - Slide 3: EMG + GSR + Arduino + Bluetooth + Android phone + Smart coach app.
  - Slide 4: EMG + GSR + Arduino + USB/Serial + Windows PC + Python data processing.
  - Slide 5: references to Seeed Grove GSR and Grove EMG Detector.
  - Slide 6: photo of EMG sensor, battery, GSR, Arduino board.
  - Slides 7-8: original and smoothed EMG sensor data, with no-contraction and contraction regions.

### 13.2 Public Hardware References

- [Seeed Grove EMG Detector product page](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html)
- [Seeed Grove EMG Detector wiki](https://wiki.seeedstudio.com/Grove-EMG_Detector/)
- [SparkFun MyoWare Muscle Sensors overview](https://www.sparkfun.com/myoware)
- [SparkFun MyoWare 2.0 Getting Started Guide](https://learn.sparkfun.com/tutorials/getting-started-with-the-myoware-20-muscle-sensor-ecosystem/all)
- [MyoWare 2.0 technical specifications](https://myoware.com/products/technical-specifications/)

---

## 14. Concise Summary

The previous AAAS-stage research built a practical first prototype for a low-cost wearable overuse-injury prevention kit using Seeed EMG, GSR, Arduino, Bluetooth, Android, and Python analysis. It demonstrated the feasibility of capturing muscle-activity changes and distinguishing no-contraction from contraction periods after smoothing.

The first-generation Seeed Grove EMG platform was effective for demonstrating low-cost muscle-activity detection, because its processed analog output could distinguish relaxed and contraction periods after smoothing. However, its documented interface exposes only a processed Arduino-readable analog signal and does not provide documented RAW, rectified, and envelope output modes. This limits its usefulness for fatigue-specific analysis, signal-quality validation, artifact rejection, and ML-ready dataset generation. In contrast, the MyoWare platform explicitly supports RAW, rectified, and envelope EMG outputs and provides clearer signal-chain documentation, including filtering, rectification, and envelope detection details. Therefore, moving from Seeed to MyoWare, especially when combined with IMU motion context, is a necessary step from proof-of-concept contraction detection toward robust personalized fatigue and overuse-risk modeling. [\[fatigue_detection \| PowerPoint\]](https://qualcomm-my.sharepoint.com/personal/wangx_qti_qualcomm_com/_layouts/15/Doc.aspx?sourcedoc=%7B23734B67-B680-4551-915B-F9C388D3F67C%7D&file=fatigue_detection.pptx&action=edit&mobileredirect=true), [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html), [\[wiki.seeedstudio.com\]](https://wiki.seeedstudio.com/Grove-EMG_Detector/), [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/technical-specifications/)

### Very Short Version

- **Seeed:** good for low-cost proof-of-concept and basic contraction detection.
- **Main Seeed limitation:** no documented RAW EMG output; only a processed analog activity signal is documented. [\[seeedstudio.com\]](https://www.seeedstudio.com/Grove-EMG-Detector-p-1737.html), [\[wiki.seeedstudio.com\]](https://wiki.seeedstudio.com/Grove-EMG_Detector/)
- **MyoWare:** better for research because it documents RAW, rectified, and envelope EMG outputs. [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/technical-specifications/)
- **Why RAW matters:** it preserves waveform and spectral information needed for fatigue features, artifact detection, and raw-vs-envelope reliability checks. [\[sparkfun.com\]](https://www.sparkfun.com/myoware), [\[myoware.com\]](https://myoware.com/products/technical-specifications/)
- **Bottom line:** Seeed proved feasibility; MyoWare enables robust fatigue analysis and ML-ready overuse-risk modeling.
