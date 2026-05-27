# Invention Disclosure

## 1. Title  
**Reliability-Gated Wearable EMG Monitoring Using Raw/Envelope Consistency and IMU-Based Validity Context**

---

## 2. Field of the Invention  
The present invention relates to wearable biosignal sensing and analysis, specifically to **surface electromyography (sEMG) signal-quality validation in dynamic field environments** using combined electromyography and inertial sensing.

---

## 3. Problem Statement  

Wearable EMG systems deployed outside laboratory conditions suffer from **unreliable signal quality**, which directly corrupts downstream metrics such as muscle activation and fatigue (e.g., MDF/MNF).

Key failure modes include:

- Electrode-skin contact instability (e.g., dry electrode settling)
- Signal amplitude drift and low signal-to-noise ratio
- Hardware envelope saturation and clipping
- Raw EMG channel failure (e.g., flatline or floating input)
- Motion artifacts caused by impact, vibration, or cable movement
- Changes in movement intensity confounding fatigue interpretation
- Wireless session discontinuities (e.g., BLE reconnect gaps)

Existing approaches primarily focus on:
- Feature extraction (e.g., RMS, MDF)
- Activity or fatigue classification using EMG and IMU

However, they **assume EMG signals are valid**, and do not determine whether the extracted features are trustworthy.

---

## 4. Key Insight  

The invention frames wearable EMG analysis as a **signal trustworthiness problem**:

> EMG-derived physiological metrics should only be interpreted when the underlying signal is validated using independent consistency and context checks.

This is achieved by combining three complementary channels:

1. **Raw EMG (RAW)** – high-frequency physiological signal for spectral analysis  
2. **Hardware Envelope (ENV)** – low-rate or parallel amplitude signal reflecting hardware behavior, contact, and saturation  
3. **Inertial Measurement Unit (IMU)** – independent biomechanical context describing movement intensity and artifacts  

The key novelty lies in using:
- **RAW/ENV consistency** to validate signal integrity and detect hardware/contact issues  
- **IMU context** to distinguish physiological changes from motion-related artifacts or effort changes  
- **Integrated decision logic** to gate downstream interpretation  

---

## 5. Technical Solution (Overview)  

A system and method for **validating and gating wearable EMG interpretation**, comprising:

1. Acquiring:
   - Raw EMG samples from an EMG sensor  
   - Simultaneous hardware envelope samples from the same sensor  
   - IMU measurements (e.g., acceleration, gyroscope)  

2. Computing features:
   - Raw-derived amplitude metrics (e.g., RMS, software envelope)  
   - Spectral features (e.g., MDF, MNF)  
   - IMU-derived motion intensity and transient events  

3. Generating signal-quality metrics:
   - RAW/ENV consistency (e.g., correlation, ratio, shape similarity)  
   - RAW variance / flatline detection  
   - ENV saturation indicators  
   - Relative contact-quality metrics (e.g., RMS normalized to session statistics)  
   - Session continuity indicators  

4. Determining a **signal validity state**, including:
   - Valid EMG  
   - Electrode settling / unstable contact  
   - Low-SNR or contact degradation  
   - Hardware saturation  
   - Raw-channel failure  
   - Motion artifact  
   - Reduced-motion confound  
   - Session-gap artifact  

5. Modifying downstream EMG interpretation by:
   - Accepting or rejecting signal segments  
   - Delaying baseline initialization  
   - Down-weighting or suppressing unreliable estimates  
   - Segmenting analysis across session discontinuities  
   - Generating confidence scores or user feedback  

---

## 6. Representative Embodiments  

### (a) RAW/ENV Consistency Validation  
A software-derived envelope computed from raw EMG is compared to a hardware envelope to detect:
- Saturation (ENV clipping)
- Channel mismatch
- Contact degradation
- Ghost-channel coupling (e.g., high correlation + low RAW variance)

### (b) IMU-Conditioned Validity  
IMU data provides independent motion context:

| IMU Context | EMG Observation | Interpretation |
|------------|----------------|----------------|
| Stable motion | Early low spectral frequency recovering | Electrode settling |
| Stable motion | Gradual spectral decline | Fatigue-consistent |
| Declining motion | Spectral decline | Effort confound |
| High shock/vibration | Isolated EMG outlier | Motion artifact |
| Session discontinuity | Baseline shift | Segment artifact |

### (c) Quality-Gated Baseline Selection  
Baseline EMG is established only from segments satisfying:
- Adequate signal amplitude/contact quality  
- Acceptable RAW/ENV consistency  
- Stable IMU context  
- Continuous recording without session gaps  

### (d) Session Continuity Audit  
Wireless disconnects introduce discontinuities that can produce false fatigue trends.  
The system detects such gaps and analyzes segments separately.

---

## 7. Advantages  

- Prevents incorrect fatigue interpretation due to poor signal quality  
- Enables reliable EMG analysis in real-world field conditions  
- Provides **confidence-aware physiological metrics**, not just raw outputs  
- Detects both hardware failures and physiological ambiguities  
- Works with low-cost wearable systems with minimal additional hardware  
- Generalizable across sports, rehabilitation, and occupational monitoring  

---

## 8. Potential Applications  

- Sports performance and fatigue monitoring  
- Injury prevention and overuse risk detection  
- Rehabilitation and physical therapy  
- Occupational ergonomics and fatigue tracking  
- Wearable human–machine interfaces  

---

## 9. Summary  

The invention introduces a **trustworthiness-first framework for wearable EMG**, in which:

> EMG-derived metrics are conditioned on validated signal quality using RAW/ENV consistency and IMU-derived context, ensuring that physiological interpretations are only made when the data is reliable.

This approach shifts wearable EMG from feature extraction to **reliability-aware sensing and decision-making**, enabling robust deployment in uncontrolled, real-world environments.
