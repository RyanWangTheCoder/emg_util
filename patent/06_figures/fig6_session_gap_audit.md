# Figure 6 — Session Continuity Audit

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
