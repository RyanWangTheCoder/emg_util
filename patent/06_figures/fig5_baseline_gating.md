# Figure 5 — Quality-Gated Baseline Selection

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
