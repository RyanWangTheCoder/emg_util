# Figure 7 — Ghost Signal / Hardware Failure Diagnostic

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
