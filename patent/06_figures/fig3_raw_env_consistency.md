# Figure 3 — RAW/ENV Consistency Validation

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
