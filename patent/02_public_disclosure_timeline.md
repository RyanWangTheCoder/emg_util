# Public Disclosure Timeline
## Patent: Reliability-Gated Wearable EMG Monitoring Using RAW/ENV/IMU Consistency

> This document tracks all known and potential public disclosures relevant to the patent application.
> Fill in exact dates as they become known. Review with counsel before filing.

---

## Key Question for Each Event

> Did it disclose the specific combination of: RAW/ENV consistency checking + IMU as validity context + trustworthiness-gating of downstream fatigue/activation metrics?

---

## Disclosure Events

| # | Date | Event | Audience | Public? | Technical details disclosed | Discloses RAW/ENV/IMU validity gating? |
|---|------|--------|----------|---------|----------------------------|----------------------------------------|
| 1 | 2024-06-17 to 2024-06-20 | AAAS Pacific Division poster — "Low-cost wearable kit and algorithms to predict and prevent muscle overuse injuries" (R. Wang) | Science fair / conference attendees | Yes — presented publicly | Low-cost wearable system using Seeed Studio EMG sensor (no RAW output — ENV-only hardware) | **Not relevant** — sensor had no RAW channel; RAW/ENV consistency checking could not have been disclosed |
| 2 | TBD (expected ~2026-07) | ICPICS paper submission accepted / proceedings published — "A Robust Self-Describing BLE Platform for Real-Time Wearable EMG–IMU Sensing" | Conference attendees / proceedings readers | Upon publication | BLE TLV protocol, DMA/ADC decimation to paired 2 kHz ENV/RAW output, ±25 µs timestamp, dual-core FreeRTOS, BLE reconnect watchdog, hybrid abs_us timeline, **pogo-pin ghost-signal diagnostic** (high RAW/ENV correlation, near-zero RAW variance, post-filter flatline, solder-bypass repair) | **Partial** — discloses RAW/ENV paired acquisition and pogo-pin ghost-signal diagnostic; does NOT frame as validity-gating or trustworthiness framework; no IMU-conditioned validity logic |
| 3 | TBD (expected ~2026-07) | CNIB paper submission accepted / proceedings published — "Field Validity of Wearable sEMG Fatigue Metrics in Tennis: Electrode Settling, Contact Quality, and IMU-Conditioned Interpretation" | Conference attendees / proceedings readers | Upon publication | Electrode settling characterization (≥17–20 min), warmup-skip sensitivity, contact-quality metric (RMS/p90_rms), **IMU-conditioned EMG validity framework**, session-gap artifact detection (BLE gap → false 28.7% MDF drop) | **Yes — high overlap** — directly discloses IMU-conditioned validity, contact quality, session-gap artifact, and trustworthiness-first framing |
| 4 | N/A | GitHub repository (`wangxdflight/arduino` and `emg_util`) | Collaborators only | **No — repo is private** | emg_util analysis code, quality metrics, session continuity logic | Not a public disclosure while private; do not make public before filing |
| 5 | TBD | Any additional poster, slide deck, abstract, or science fair presentation | TBD | TBD | TBD | TBD |

---

## Filing Deadline Summary

| Scenario | US Provisional Deadline | International Deadline |
|----------|------------------------|----------------------|
| If ICPICS publishes first (~2026-07) | ~2027-07 (US grace period from publication date) | File **before** ICPICS publishes |
| If CNIB publishes first (~2026-07) | ~2027-07 (US grace period from publication date) | File **before** CNIB publishes |
| **Recommended action** | File provisional **before** either paper publishes | File provisional **before** either paper publishes |

> US grace period: AIA §102(b)(1)(A) gives inventors 1 year from their own public disclosure to file a US patent application.
> Most foreign jurisdictions (Europe, China, etc.) have no grace period — prior public disclosure by the inventor bars patentability.

---

## AAAS 2024 Poster — Resolved: Not Relevant

The 2024 AAAS Pacific Division poster used the Seeed Studio EMG sensor, which has no RAW output (ENV-only hardware). RAW/ENV consistency checking — the core of this invention — could not have been disclosed. This event is not a relevant prior disclosure and does not affect the patent or the filing deadline.

---

## Per-Paper Disclosure Analysis

### ICPICS — "A Robust Self-Describing BLE Platform for Real-Time Wearable EMG–IMU Sensing"

**What it discloses relevant to the patent:**
- Paired ENV/RAW EMG output from the same sensor (hardware architecture)
- Pogo-pin ghost-signal failure mode: high RAW/ENV correlation, near-zero RAW variance, post-filter flatline, repair by solder bypass
- BLE reconnect handling and hybrid `abs_us` timeline (session continuity infrastructure)

**What it does NOT disclose:**
- Validity-gating framework or trustworthiness-first framing
- IMU as an independent EMG validity context channel
- Baseline gating conditioned on signal quality
- Contact-quality metric or electrode settling characterization
- Session-gap artifact producing false fatigue conclusions

**Assessment:** Partial overlap with Family A (RAW/ENV acquisition) and Family D (pogo-pin diagnostic). The core validity-gating invention (Family A main concept) is not framed or claimed. Filing before ICPICS publishes is still preferable for international coverage, but US grace period likely applies from publication date.

---

### CNIB — "Field Validity of Wearable sEMG Fatigue Metrics in Tennis: Electrode Settling, Contact Quality, and IMU-Conditioned Interpretation"

**What it discloses relevant to the patent:**
- IMU-conditioned EMG validity framework (C4) — IMU as validity cross-check, not fusion feature
- Electrode settling characterization and warmup-skip sensitivity (C1, C2)
- Contact-quality metric: `contact_quality(t) = RMS(t) / session_p90_rms` (C3)
- Session-gap artifact: BLE reconnection gap producing false 28.7% MDF drop (C5)
- Trustworthiness-first framing of wearable EMG interpretation

**What it does NOT disclose:**
- RAW/ENV consistency checking (hardware envelope comparison)
- Software-derived envelope vs hardware envelope comparison
- ENV saturation detection
- RAW flatline / ghost-channel detection (covered by ICPICS)
- Multi-modal quality gate integrating all three signals (RAW + ENV + IMU)

**Assessment:** High overlap with Family A (IMU context, session continuity) and Family B (baseline gating). The unique novelty of the patent — combining RAW/ENV consistency with IMU validity context into a unified gate — is not fully disclosed by CNIB alone. But CNIB does disclose significant components.

---

## Action Items

- [x] ~~Confirm AAAS 2024 poster relevance~~ — resolved: Seeed sensor, no RAW output, not relevant
- [x] ~~Confirm GitHub repo visibility~~ — resolved: private, not a public disclosure; keep private until after filing
- [ ] Confirm expected publication date for ICPICS (expected ~2026-07)
- [ ] Confirm expected publication date for CNIB (expected ~2026-07)
- [ ] Fill in both TBD dates above as soon as known — these set the hard filing deadline
- [ ] File provisional **before** either paper goes public

---

*Last updated: 2026-06-01*
