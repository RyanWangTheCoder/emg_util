# Figure 4 — IMU-Conditioned EMG Validity Matrix

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
