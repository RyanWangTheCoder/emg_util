#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
log_check.py

Quick validation of assumptions on a btCentral log directory:
- Sampling rate inferred from dev_us
- IMU FSR values (acc_fsr_g / gyro_fsr_dps)
- ENV usefulness as activation proxy (corr with RAW amplitude proxy)

Usage (Windows / PowerShell):
  cd C:\\wangx\\ftc\\emg_util
  python tools\\log_check.py --log-dir log0305
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


def _first_csv(log_dir: Path, prefix: str) -> Path:
    files = sorted([p for p in log_dir.iterdir() if p.name.startswith(prefix) and p.suffix.lower() == ".csv"])
    if not files:
        raise FileNotFoundError(f"No CSV files starting with {prefix!r} under {log_dir}")
    return files[0]


def _read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _fs_from_dev_us(series: np.ndarray) -> dict:
    if series.size < 10:
        return {"n": int(series.size)}
    dt = np.diff(series.astype(np.float64))
    dt = dt[np.isfinite(dt)]
    dt = dt[dt > 0]
    if dt.size == 0:
        return {"n": int(series.size), "err": "no positive diffs"}
    med = float(np.median(dt))
    p5 = float(np.percentile(dt, 5))
    p95 = float(np.percentile(dt, 95))
    fs_est = float(1e6 / med) if med > 0 else float("nan")
    return {"n": int(series.size), "dt_us_median": med, "dt_us_p5": p5, "dt_us_p95": p95, "fs_est_hz": fs_est}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log-dir", required=True, help="Directory containing emg_log_*.csv and imu_log_*.csv")
    ap.add_argument("--win-sec", type=float, default=1.0, help="Window size for ENV/RAW correlation")
    ap.add_argument("--emg-fs-hz", type=float, default=2000.0, help="Expected EMG sample rate")
    args = ap.parse_args()

    log_dir = Path(args.log_dir).expanduser().resolve()
    if not log_dir.exists():
        raise FileNotFoundError(log_dir)

    # Heuristic: try to find the meta.json for the first session id present
    emg_first = _first_csv(log_dir, "emg_log_")
    imu_first = _first_csv(log_dir, "imu_log_")

    # Session id extraction: emg_log_YYYYMMDD_HHMMSS_...
    session_id = None
    parts = emg_first.stem.split("_")
    if len(parts) >= 3:
        session_id = parts[2] + "_" + parts[3] if len(parts) >= 4 and len(parts[2]) == 8 else None

    # Known meta naming (from your logs): emg_log_<session>__000.meta.json
    emg_meta = log_dir / f"emg_log_{session_id}__000.meta.json" if session_id else None
    imu_meta = log_dir / f"imu_log_{session_id}__000.meta.json" if session_id else None

    print("=== LOG CHECK ===")
    print("log_dir:", str(log_dir))
    print("sample emg csv:", emg_first.name)
    print("sample imu csv:", imu_first.name)

    if emg_meta:
        print("\n=== META (if present) ===")
        j = _read_json(emg_meta)
        print(emg_meta.name, j)
        j = _read_json(imu_meta) if imu_meta else None
        if imu_meta:
            print(imu_meta.name, j)

    print("\n=== EMG FORMAT / RATE CHECK ===")
    emg = pd.read_csv(emg_first)
    print("columns:", list(emg.columns))
    if "dev_us" not in emg.columns:
        raise RuntimeError("EMG CSV missing dev_us")
    emg_fs_stats = _fs_from_dev_us(emg["dev_us"].values[:50000])
    print("dev_us stats:", emg_fs_stats)
    if "env" not in emg.columns or "raw" not in emg.columns:
        print("WARN: EMG CSV missing env/raw columns (expected).")

    print("\n=== IMU FORMAT / RATE & FSR CHECK ===")
    imu = pd.read_csv(imu_first)
    print("columns:", list(imu.columns))
    if "dev_us" not in imu.columns:
        raise RuntimeError("IMU CSV missing dev_us")
    imu_fs_stats = _fs_from_dev_us(imu["dev_us"].values[:20000])
    print("dev_us stats:", imu_fs_stats)

    for col in ["acc_fsr_g", "gyro_fsr_dps"]:
        if col in imu.columns:
            vals = imu[col].dropna().values[:50000]
            uniq = sorted(set(vals.tolist()))
            print(f"{col} unique (first 50k rows):", uniq[:20], ("..." if len(uniq) > 20 else ""))
        else:
            print(f"WARN: IMU CSV missing {col} (would require defaults).")

    print("\n=== ENV UTILITY CHECK (activation proxy) ===")
    # Proxy comparison: env_mean vs abs(raw - median(raw)) RMS over 1s windows
    if "raw" in emg.columns and "env" in emg.columns:
        raw = emg["raw"].astype(np.float64).values
        env = emg["env"].astype(np.float64).values

        raw_ac = raw - np.median(raw)
        abs_raw = np.abs(raw_ac)

        win = int(round(args.win_sec * args.emg_fs_hz))
        n = len(raw) // win
        if n < 20:
            print("Not enough data for windowed check; windows:", n)
        else:
            abs_raw_rms = np.sqrt(np.mean(abs_raw[: n * win].reshape(n, win) ** 2, axis=1))
            env_mean = np.mean(env[: n * win].reshape(n, win), axis=1)
            corr = float(np.corrcoef(abs_raw_rms, env_mean)[0, 1])

            print("windows:", n, "win_samples:", win)
            print("corr(env_mean, abs_raw_rms):", corr)
            print(
                "env_mean p10/p50/p90:",
                float(np.percentile(env_mean, 10)),
                float(np.percentile(env_mean, 50)),
                float(np.percentile(env_mean, 90)),
            )
            print(
                "abs_raw_rms p10/p50/p90:",
                float(np.percentile(abs_raw_rms, 10)),
                float(np.percentile(abs_raw_rms, 50)),
                float(np.percentile(abs_raw_rms, 90)),
            )
            # Simple suggested ENV gate threshold (heuristic)
            thr = float(np.percentile(env_mean, 75))
            print("suggested ENV gate (p75 of 1s env_mean):", thr)
    else:
        print("Skipping: need both env and raw columns in EMG.")

    print("\n=== INTERPRETATION GUIDE ===")
    print("- EMG fs_est_hz should be close to 2000 Hz (median dt_us ~ 500).")
    print("- IMU fs_est_hz should be close to 200 Hz (median dt_us ~ 5000).")
    print("- If acc_fsr_g=8 and gyro_fsr_dps=2000, thresholds in physical units are consistent with firmware.")
    print("- If corr(env_mean, abs_raw_rms) is high (e.g. >0.6), ENV is a strong activation proxy for gating.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
