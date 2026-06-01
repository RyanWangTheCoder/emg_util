# Figure 2 — Overall Method Flow

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
