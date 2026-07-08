#!/usr/bin/env python3
"""Generate Fig. 4: synchronized EMG–IMU example showing concurrent acquisition.

Plots a ~5-second window of raw EMG amplitude and IMU gyro magnitude during a
tennis swing, demonstrating that EMG activation and IMU motion are time-aligned
on the platform's hybrid abs_us timeline.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent
EMG_CSV = sorted(ROOT.glob("data/log0305/emg_log_*_000.csv"))[0]
IMU_CSV = sorted(ROOT.glob("data/log0305/imu_log_*_000.csv"))[0]
OUT = ROOT / "papers/icpics_figures/fig_emg_imu_sync.png"


def main():
    # Load EMG (2 kHz) and IMU (200 Hz)
    emg = pd.read_csv(EMG_CSV, usecols=["dev_us", "raw"])
    imu = pd.read_csv(IMU_CSV, usecols=["dev_us", "gx", "gy", "gz", "gyro_fsr_dps"])

    # Dedup and sort: BLE retransmission can produce repeated rows
    emg = emg.drop_duplicates(subset="dev_us").sort_values("dev_us").reset_index(drop=True)
    imu = imu.drop_duplicates(subset="dev_us").sort_values("dev_us").reset_index(drop=True)

    # Convert to seconds since first EMG sample
    t0 = emg["dev_us"].iloc[0]
    emg["t"] = (emg["dev_us"] - t0) / 1e6
    imu["t"] = (imu["dev_us"] - t0) / 1e6

    # IMU gyro magnitude (dps) — smoothed slightly for readability
    fsr = imu["gyro_fsr_dps"].iloc[0]
    scale = fsr / 32768.0
    imu["gmag"] = np.sqrt(
        (imu["gx"] * scale) ** 2 + (imu["gy"] * scale) ** 2 + (imu["gz"] * scale) ** 2
    )
    imu["gmag_s"] = imu["gmag"].rolling(15, center=True, min_periods=1).mean()

    # Find a swing event: peak of gyro magnitude after ~1 minute (skip early settling).
    # Limit search to first 3 minutes for speed.
    search = imu[(imu["t"] > 60) & (imu["t"] < 180)].copy()
    peak_idx = search["gmag"].idxmax()
    peak_t = imu.loc[peak_idx, "t"]

    # 4-second window centered on the swing peak
    win_start = peak_t - 1.5
    win_end = peak_t + 2.5

    emg_w = emg[(emg["t"] >= win_start) & (emg["t"] <= win_end)].copy()
    imu_w = imu[(imu["t"] >= win_start) & (imu["t"] <= win_end)].copy()

    # Detrend EMG raw and compute envelope via rolling RMS (50 ms window @ 2 kHz = 100 samples)
    emg_w["raw_dt"] = emg_w["raw"] - emg_w["raw"].mean()
    win_n = 100
    emg_w["env"] = emg_w["raw_dt"].pow(2).rolling(win_n, center=True, min_periods=10).mean().pow(0.5)

    # Reset time axis to start at 0
    t_origin = win_start
    emg_w["tt"] = emg_w["t"] - t_origin
    imu_w["tt"] = imu_w["t"] - t_origin

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(5.5, 2.6), sharex=True,
        gridspec_kw={"hspace": 0.12, "left": 0.13, "right": 0.97, "top": 0.93, "bottom": 0.16},
    )

    # EMG envelope
    ax1.plot(emg_w["tt"], emg_w["env"], color="#3a78c0", linewidth=1.0)
    ax1.set_ylabel("EMG envelope\n(ADC counts)", fontsize=8)
    ax1.tick_params(labelsize=7)
    ax1.grid(alpha=0.3)
    ax1.set_title("Concurrent EMG (2 kHz) and IMU (200 Hz) during a tennis swing",
                  fontsize=9)

    # IMU gyro magnitude (smoothed)
    ax2.plot(imu_w["tt"], imu_w["gmag_s"], color="#c97a2b", linewidth=1.2)
    ax2.set_ylabel("IMU gyro\nmagnitude (dps)", fontsize=8)
    ax2.set_xlabel("Time (s) within window", fontsize=8)
    ax2.tick_params(labelsize=7)
    ax2.grid(alpha=0.3)

    # Highlight swing peak time
    swing_t = peak_t - t_origin
    for ax in (ax1, ax2):
        ax.axvline(swing_t, color="red", linestyle="--", linewidth=0.8, alpha=0.6)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"Saved: {OUT}")
    print(f"Swing at t={peak_t:.2f} s; window {win_start:.2f}–{win_end:.2f} s")


if __name__ == "__main__":
    main()
