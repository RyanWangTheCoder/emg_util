# Figure 1 — System Architecture

## Purpose
Shows that the invention includes both hardware acquisition and host/mobile software decision logic. Establishes the three input channels (RAW, ENV, IMU) and the processing pipeline leading to gated EMG output.

## Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEARABLE SENSOR UNIT                         │
│                                                                 │
│  ┌──────────────────────────┐    ┌──────────────────────────┐  │
│  │     EMG SENSOR           │    │     IMU SENSOR           │  │
│  │  (e.g., MyoWare 2.0)     │    │  (e.g., LSM6DS3)         │  │
│  │                          │    │                          │  │
│  │  RAW output ─────────────┼────┼──► RAW channel (2 kHz)   │  │
│  │  ENV output ─────────────┼────┼──► ENV channel (2 kHz)   │  │
│  │                          │    │  Accel + Gyro (200 Hz) ◄─┼──┤
│  └──────────────────────────┘    └──────────────────────────┘  │
│                                                                 │
│              ┌──────────────────────────────────┐              │
│              │   MICROCONTROLLER / MCU           │              │
│              │   - DMA ADC sampling              │              │
│              │   - Per-sample timestamping       │              │
│              │   - BLE TLV packetization         │              │
│              │   - Session continuity tracking   │              │
│              └──────────────┬───────────────────┘              │
└─────────────────────────────┼───────────────────────────────────┘
                              │  BLE / Wired Link
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              HOST / MOBILE PROCESSING UNIT                      │
│                                                                 │
│   RAW EMG ──────────────────────────────────────────────────┐  │
│                                                             │  │
│   ENV ──────────────────────────────────────────────────┐   │  │
│                                                         │   │  │
│   IMU ──────────────────────────────────────────────┐   │   │  │
│                                                     │   │   │  │
│   Session Timeline ─────────────────────────────┐   │   │   │  │
│                                                 │   │   │   │  │
│                    ┌────────────────────────────▼───▼───▼───▼─┐│
│                    │     SIGNAL QUALITY EVALUATOR              ││
│                    │                                           ││
│                    │  1. RAW preprocessing                     ││
│                    │  2. RAW-derived envelope computation      ││
│                    │  3. RAW/ENV consistency check             ││
│                    │  4. IMU motion context analysis           ││
│                    │  5. Session continuity audit              ││
│                    │  6. Signal trustworthiness classification ││
│                    └───────────────────┬───────────────────────┘│
│                                        │                        │
│                    ┌───────────────────▼───────────────────────┐│
│                    │     QUALITY-GATED EMG ANALYTICS            ││
│                    │                                           ││
│                    │  - Baseline selection                     ││
│                    │  - MDF / MNF / RMS computation            ││
│                    │  - Fatigue / activation interpretation    ││
│                    │  - Confidence score / user alert          ││
│                    └───────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Caption

**Figure 1.** System architecture showing dual-output EMG sensor (RAW and ENV channels), IMU sensor, and microcontroller on the wearable unit, connected via BLE or wired link to a host or mobile processing unit. The host runs the signal quality evaluator, which combines RAW, ENV, IMU, and session-timeline inputs to classify trustworthiness before passing data to the quality-gated EMG analytics layer.

## Notes for Patent

- The processing split between MCU and host is not limiting — all logic may run on-device, on a mobile phone, or in the cloud.
- The RAW and ENV channels originate from the same EMG sensor, providing paired signals for consistency checking.
- IMU is an independent sensor used as a validity context channel, not as a feature-fusion input to fatigue classification.
