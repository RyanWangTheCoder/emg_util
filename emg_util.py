
# -*- coding: utf-8 -*-
"""
emg_util_bt.py

btCentral EMG/IMU/Vitals offline analysis + plotting + fatigue analysis.

Features:
- Handles interleaved EMG/IMU CSV logs (splits EMG vs IMU rows).
- Supports multiple CSV files via glob pattern.
- Computes:
    * Raw EMG
    * Preprocessed EMG (detrend + bandpass + notch)
    * Envelope (rectify + low-pass)
    * Windowed features (RMS, MNF, MDF, IMU activity)
- Plot modes:
    1) --full : full-duration EMG traces (decimated for performance)
    2) --page-sec : paged plots (full resolution per segment)
- Auto-save:
    * Full-duration plot saved as:
      full_duration_fs{sampling_rate}_total{seconds}s.png
    * Paged plots saved as:
      page_{index:02d}_t0-{start:.2f}_t1-{end:.2f}.png
- Silent mode (--silent): skip interactive display, save only.
- Fatigue analysis:
    * Computes MDF/MNF trends
    * Detects fatigue onset (≥15% MDF drop)
    * Saves fatigue_summary.csv and fatigue_trend.png

Example:
    python emg_util_bt.py --emg-imu "logs/emg_imu_log_*.csv" --emg-fs 2000 \
        --plot --full --page-sec 10 --page-count 5 \
        --save-pages ./emg_pages --silent
"""

from __future__ import annotations
import argparse, glob, os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, iirnotch, detrend, welch

EMG_IMU_COLS = ["ts_ms", "env", "raw", "ref", "ax", "ay", "az", "gx", "gy", "gz"]
VITALS_COLS = ["ts_ms", "spo2", "hr_bpm", "age_ms", "flags", "brightness"]

# -----------------------------
# Loading
# -----------------------------
def load_emg_imu_logs(pattern_or_paths: str | Iterable[str]) -> pd.DataFrame:
    if isinstance(pattern_or_paths, (str, Path)):
        paths = sorted(glob.glob(str(pattern_or_paths)))
        if not paths:
            paths = [str(pattern_or_paths)]
    else:
        paths = list(pattern_or_paths)

    dfs = []
    for p in paths:
        df = pd.read_csv(p, engine="python")
        missing = [c for c in EMG_IMU_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"{p} missing required columns: {missing}")
        df = df[EMG_IMU_COLS].copy()
        for c in EMG_IMU_COLS:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        dfs.append(df)

    out = pd.concat(dfs, ignore_index=True)
    return out.sort_values("ts_ms").reset_index(drop=True)

def load_vitals_log(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, engine="python")
    missing = [c for c in VITALS_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{path} missing required columns: {missing}")
    df = df[VITALS_COLS].copy()
    for c in VITALS_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["ts_ms"]).sort_values("ts_ms").reset_index(drop=True)

# -----------------------------
# Filtering helpers
# -----------------------------
def filtfilt_safe(b, a, x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    n = x.size
    if n == 0:
        return x
    padlen = 3 * (max(len(a), len(b)) - 1)
    if n <= padlen:
        return filtfilt(b, a, x, method="gust")
    return filtfilt(b, a, x)

def preprocess_emg(x: np.ndarray, fs: float) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        return x
    y = detrend(x, type="constant")
    nyq = fs / 2.0
    high = min(450.0, 0.95 * nyq)
    if high <= 20.0:
        return y
    b, a = butter(4, [20.0 / nyq, high / nyq], btype="bandpass")
    y = filtfilt_safe(b, a, y)
    for f0 in (60.0, 120.0):
        if f0 < nyq - 1:
            b, a = iirnotch(w0=f0 / nyq, Q=30.0)
            y = filtfilt_safe(b, a, y)
    return y

def envelope(x: np.ndarray, fs: float, cutoff_hz: float = 3.6) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        return x
    rect = np.abs(x)
    nyq = fs / 2.0
    c = min(cutoff_hz, 0.95 * nyq)
    b, a = butter(2, c / nyq, btype="low")
    return np.maximum(filtfilt_safe(b, a, rect), 0.0)

# -----------------------------
# Feature helpers
# -----------------------------
def rms(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    return float(np.sqrt(np.mean(x * x))) if x.size else np.nan

def mnf_mdf(x: np.ndarray, fs: float) -> Tuple[float, float]:
    x = np.asarray(x, dtype=float)
    if x.size < 2:
        return np.nan, np.nan
    f, Pxx = welch(x, fs=fs, nperseg=min(1024, len(x)), noverlap=min(512, len(x)//2),
                   window="hann", scaling="density")
    if len(Pxx) == 0:
        return np.nan, np.nan
    Pxx = np.maximum(Pxx, 1e-20)
    s = float(np.sum(Pxx))
    mnf_val = float(np.sum(f * Pxx) / s)
    cdf = np.cumsum(Pxx)
    mdf_val = float(f[min(np.searchsorted(cdf, 0.5 * s), len(f) - 1)])
    return mnf_val, mdf_val

def imu_mags(imu_df: pd.DataFrame) -> pd.DataFrame:
    out = imu_df.copy()
    out["acc_mag"] = np.sqrt(out["ax"]**2 + out["ay"]**2 + out["az"]**2)
    out["gyro_mag"] = np.sqrt(out["gx"]**2 + out["gy"]**2 + out["gz"]**2)
    return out

@dataclass
class Results:
    feats: pd.DataFrame
    emg_ts_ms: np.ndarray
    emg_raw: np.ndarray
    emg_proc: np.ndarray
    emg_env: np.ndarray

def compute(emg_imu: pd.DataFrame, emg_fs_hz: float, win_sec: float = 1.0, step_sec: float = 0.25,
            vitals: Optional[pd.DataFrame] = None, treat_zero_as_nan: bool = False) -> Results:
    df = emg_imu.copy()
    emg = df[df["raw"].notna()].copy().sort_values("ts_ms").reset_index(drop=True)
    imu = df[df[["ax","ay","az","gx","gy","gz"]].notna().any(axis=1)].copy().sort_values("ts_ms").reset_index(drop=True)
    if len(emg) == 0:
        raise ValueError("No EMG rows found.")
    if len(imu) > 0:
        imu = imu_mags(imu)
    raw = emg["raw"].astype(float).to_numpy()
    if treat_zero_as_nan:
        raw[raw == 0] = np.nan
        raw = pd.Series(raw).interpolate(limit=100, limit_direction="both").to_numpy(dtype=float)
    t0_ms = float(emg["ts_ms"].iloc[0])
    emg_ts_ms = t0_ms + (np.arange(len(raw)) / float(emg_fs_hz)) * 1000.0
    proc = preprocess_emg(raw, float(emg_fs_hz))
    env = envelope(proc, float(emg_fs_hz))
    win_samp = max(int(round(win_sec * emg_fs_hz)), 256)
    step_samp = max(int(round(step_sec * emg_fs_hz)), 1)
    vit = None
    if vitals is not None and len(vitals):
        vit = vitals.copy().dropna(subset=["ts_ms"]).sort_values("ts_ms").reset_index(drop=True)
    rows = []
    for i0 in range(0, len(raw) - win_samp + 1, step_samp):
        i1 = i0 + win_samp
        tc_s = (i0 + i1) / 2.0 / emg_fs_hz
        t_start_ms = emg_ts_ms[i0]
        t_end_ms = emg_ts_ms[i1 - 1]
        seg = proc[i0:i1]
        seg_env = env[i0:i1]
        mnf_val, mdf_val = mnf_mdf(seg, emg_fs_hz)
        acc_rms = gyro_rms = np.nan
        if len(imu):
            iseg = imu[(imu["ts_ms"] >= t_start_ms) & (imu["ts_ms"] <= t_end_ms)]
            if len(iseg):
                acc_rms = rms(iseg["acc_mag"].to_numpy())
                gyro_rms = rms(iseg["gyro_mag"].to_numpy())
        hr_mean = spo2_mean = np.nan
        if vit is not None:
            vseg = vit[(vit["ts_ms"] >= t_start_ms) & (vit["ts_ms"] <= t_end_ms)]
            if len(vseg) == 0:
                idx = int(np.searchsorted(vit["ts_ms"].to_numpy(), 0.5*(t_start_ms+t_end_ms)))
                idx = int(np.clip(idx, 0, len(vit)-1))
                vseg = vit.iloc[[idx]]
            hr_mean = float(np.nanmean(vseg["hr_bpm"].to_numpy(float)))
            spo2_mean = float(np.nanmean(vseg["spo2"].to_numpy(float)))
        rows.append({
            "t_center_s": tc_s,
            "EMG_RMS": rms(seg),
            "EMG_ENV_mean": float(np.nanmean(seg_env)),
            "EMG_MNF_Hz": mnf_val,
            "EMG_MDF_Hz": mdf_val,
            "IMU_acc_rms": acc_rms,
            "IMU_gyro_rms": gyro_rms,
            "HR_mean_bpm": hr_mean,
            "SpO2_mean": spo2_mean,
        })
    feats = pd.DataFrame(rows)
    return Results(feats=feats, emg_ts_ms=emg_ts_ms, emg_raw=raw, emg_proc=proc, emg_env=env)

# -----------------------------
# Fatigue Analysis
# -----------------------------
def analyze_fatigue(feats: pd.DataFrame, save_dir: Optional[str]):
    if len(feats) < 10:
        print("Not enough data for fatigue analysis.")
        return
    total_sec = feats["t_center_s"].iloc[-1]
    baseline_idx = int(len(feats) * 0.1)
    baseline_MDF = np.nanmean(feats["EMG_MDF_Hz"].iloc[:baseline_idx])
    baseline_MNF = np.nanmean(feats["EMG_MNF_Hz"].iloc[:baseline_idx])
    final_MDF = np.nanmean(feats["EMG_MDF_Hz"].iloc[-baseline_idx:])
    final_MNF = np.nanmean(feats["EMG_MNF_Hz"].iloc[-baseline_idx:])
    MDF_drop_pct = 100 * (baseline_MDF - final_MDF) / baseline_MDF
    MNF_drop_pct = 100 * (baseline_MNF - final_MNF) / baseline_MNF
    slope_MDF = np.polyfit(feats["t_center_s"], feats["EMG_MDF_Hz"], 1)[0]
    slope_MNF = np.polyfit(feats["t_center_s"], feats["EMG_MNF_Hz"], 1)[0]
    onset_time = np.nan
    threshold = baseline_MDF * 0.85
    onset_candidates = feats[feats["EMG_MDF_Hz"] <= threshold]
    if len(onset_candidates):
        onset_time = onset_candidates["t_center_s"].iloc[0]
    print(f"Fatigue Analysis:")
    print(f"Baseline MDF: {baseline_MDF:.2f} Hz, Final MDF: {final_MDF:.2f} Hz, Drop: {MDF_drop_pct:.1f}%")
    print(f"Baseline MNF: {baseline_MNF:.2f} Hz, Final MNF: {final_MNF:.2f} Hz, Drop: {MNF_drop_pct:.1f}%")
    print(f"MDF slope: {slope_MDF:.4f} Hz/s, MNF slope: {slope_MNF:.4f} Hz/s")
    if not np.isnan(onset_time):
        print(f"Estimated fatigue onset: ~{onset_time:.1f}s")
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        summary_path = os.path.join(save_dir, "fatigue_summary.csv")
        pd.DataFrame([{
            "baseline_MDF": baseline_MDF,
            "baseline_MNF": baseline_MNF,
            "final_MDF": final_MDF,
            "final_MNF": final_MNF,
            "MDF_drop_pct": MDF_drop_pct,
            "MNF_drop_pct": MNF_drop_pct,
            "slope_MDF": slope_MDF,
            "slope_MNF": slope_MNF,
            "onset_time_s": onset_time
        }]).to_csv(summary_path, index=False)
        # Plot trend
        plt.figure(figsize=(10,5))
        plt.plot(feats["t_center_s"], feats["EMG_MDF_Hz"], label="MDF")
        plt.plot(feats["t_center_s"], feats["EMG_MNF_Hz"], label="MNF")
        if not np.isnan(onset_time):
            plt.axvline(onset_time, color="r", linestyle="--", label="Fatigue onset")
        plt.xlabel("Time (s)"); plt.ylabel("Frequency (Hz)")
        plt.title("Fatigue Trend (MDF & MNF)")
        plt.legend(); plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, "fatigue_trend.png"), dpi=150)
        plt.close()

# -----------------------------
# CLI
# -----------------------------
def main():
    ap = argparse.ArgumentParser(description="btCentral EMG/IMU/Vitals analysis + fatigue detection")
    ap.add_argument("--emg-imu", required=True, help="Path or glob to emg_imu_log_###.csv")
    ap.add_argument("--emg-fs", type=float, required=True, help="EMG sampling rate in Hz (e.g., 2000)")
    ap.add_argument("--vitals", default=None, help="Path to vitals_log.csv (optional)")
    ap.add_argument("--win", type=float, default=1.0, help="Window length in seconds")
    ap.add_argument("--step", type=float, default=0.25, help="Step (hop) in seconds")
    ap.add_argument("--out", default="features.csv", help="Output CSV of windowed features")
    ap.add_argument("--plot", action="store_true", help="Show plots")
    ap.add_argument("--full", action="store_true", help="Full-duration EMG traces (decimated)")
    ap.add_argument("--emg-max-points", type=int, default=200000, help="Max points for full-duration EMG (decimation target)")
    ap.add_argument("--page-sec", type=float, default=0.0, help="If >0, plot paged EMG views with this page length (seconds)")
    ap.add_argument("--page-start", type=float, default=0.0, help="Start time for paged plots (seconds)")
    ap.add_argument("--page-count", type=int, default=1, help="How many pages to show; <=0 means show all pages")
    ap.add_argument("--page-step", type=float, default=0.0, help="Hop between pages (seconds). 0 means equal to page-sec")
    ap.add_argument("--save-pages", default=None, help="Directory to save plots and fatigue summary")
    ap.add_argument("--silent", action="store_true", help="Silent mode: do not display plots, only save files")
    ap.add_argument("--dropout-zeros", action="store_true", help="Treat raw==0 as dropout (experimental)")
    args = ap.parse_args()

    emg_imu = load_emg_imu_logs(args.emg_imu)
    vitals = load_vitals_log(args.vitals) if args.vitals else None
    res = compute(emg_imu, emg_fs_hz=args.emg_fs, win_sec=args.win, step_sec=args.step,
                  vitals=vitals, treat_zero_as_nan=args.dropout_zeros)
    res.feats.to_csv(args.out, index=False)
    print(f"Saved {args.out} (rows={len(res.feats)})")

    # Fatigue analysis
    analyze_fatigue(res.feats, save_dir=args.save_pages)

    if args.plot:
        plot_all(res, emg_fs_hz=args.emg_fs, title=f"EMG/IMU (fs={args.emg_fs:.0f} Hz)",
                 full_duration=args.full, emg_max_points=args.emg_max_points,
                 save_dir=args.save_pages, silent=args.silent)

        if args.page_sec and args.page_sec > 0:
            hop = args.page_step if args.page_step and args.page_step > 0 else args.page_sec
            plot_paged(
                res,
                emg_fs_hz=args.emg_fs,
                page_sec=args.page_sec,
                page_start_sec=args.page_start,
                page_count=args.page_count,
                page_step_sec=hop,
                title=f"EMG pages (fs={args.emg_fs:.0f} Hz)",
                save_dir=args.save_pages,
                silent=args.silent,
            )


# -----------------------------
# Plotting
# -----------------------------
def _emg_axes_plot(axes, t_s, raw_y, proc_y, env_y, span_note: str):
    axes[0].plot(t_s, raw_y, lw=0.6, color="k")
    axes[0].set_title(f"Raw EMG ({span_note})")
    axes[0].set_ylabel("ADC")
    axes[0].grid(True, alpha=0.2)
    axes[1].plot(t_s, proc_y, lw=0.6, color="tab:blue")
    axes[1].set_title("Preprocessed EMG (detrend + bandpass + notch)")
    axes[1].set_ylabel("a.u.")
    axes[1].grid(True, alpha=0.2)
    axes[2].plot(t_s, env_y, lw=0.8, color="tab:orange")
    axes[2].set_title("Envelope (rectify + low-pass)")
    axes[2].set_ylabel("a.u.")
    axes[2].set_xlabel("Time (s)")
    axes[2].grid(True, alpha=0.2)

def plot_all(res: Results, emg_fs_hz: float, title: str, full_duration: bool,
             emg_max_points: int, save_dir: Optional[str], silent: bool):
    feats = res.feats
    fig, axes = plt.subplots(6, 1, figsize=(13, 14), sharex=False)
    if full_duration:
        n = len(res.emg_raw)
        stride = max(1, int(np.ceil(n / max(1, int(emg_max_points)))))
        idx = np.arange(0, n, stride)
        t = idx / emg_fs_hz
        raw_plot = res.emg_raw[idx]
        proc_plot = res.emg_proc[idx]
        env_plot = res.emg_env[idx]
        span_note = f"Full duration (decimated: stride={stride}, points={len(idx)})"
    else:
        n = min(len(res.emg_raw), int(3 * emg_fs_hz))
        t = np.arange(n) / emg_fs_hz
        raw_plot = res.emg_raw[:n]
        proc_plot = res.emg_proc[:n]
        env_plot = res.emg_env[:n]
        span_note = "First 3 seconds"
    _emg_axes_plot(axes[:3], t, raw_plot, proc_plot, env_plot, span_note)
    axes[3].plot(feats["t_center_s"], feats["EMG_RMS"], lw=1.2, label="EMG RMS")
    axes[3].plot(feats["t_center_s"], feats["EMG_ENV_mean"], lw=1.2, label="ENV mean", alpha=0.85)
    axes[3].set_title("EMG amplitude features"); axes[3].legend(); axes[3].grid(True, alpha=0.2)
    axes[4].plot(feats["t_center_s"], feats["EMG_MNF_Hz"], lw=1.2, label="MNF")
    axes[4].plot(feats["t_center_s"], feats["EMG_MDF_Hz"], lw=1.2, label="MDF", alpha=0.85)
    axes[4].set_title("EMG spectral features"); axes[4].legend(); axes[4].grid(True, alpha=0.2)
    axes[5].plot(feats["t_center_s"], feats["IMU_acc_rms"], lw=1.2, label="IMU acc RMS")
    axes[5].plot(feats["t_center_s"], feats["IMU_gyro_rms"], lw=1.2, label="IMU gyro RMS", alpha=0.85)
    axes[5].set_title("IMU activity features"); axes[5].legend(); axes[5].grid(True, alpha=0.2)
    fig.suptitle(title); plt.tight_layout()
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        total_sec = len(res.emg_raw) / emg_fs_hz
        fname = f"full_duration_fs{int(emg_fs_hz)}_total{int(total_sec)}s.png"
        fig.savefig(os.path.join(save_dir, fname), dpi=150)
    if not silent:
        plt.show()
    plt.close(fig)

def plot_paged(res: Results, emg_fs_hz: float, page_sec: float, page_start_sec: float,
               page_count: int, page_step_sec: Optional[float], title: str,
               save_dir: Optional[str], silent: bool):
    total_sec = len(res.emg_raw) / float(emg_fs_hz)
    hop = float(page_step_sec) if page_step_sec else float(page_sec)
    starts = []
    t = float(page_start_sec)
    while t < total_sec - 1e-9:
        starts.append(t)
        t += hop
        if page_count > 0 and len(starts) >= page_count:
            break
    for i, t0 in enumerate(starts):
        t1 = min(t0 + float(page_sec), total_sec)
        i0 = int(max(0, np.floor(t0 * emg_fs_hz)))
        i1 = int(min(len(res.emg_raw), np.ceil(t1 * emg_fs_hz)))
        tt = np.arange(i0, i1) / emg_fs_hz
        raw_y = res.emg_raw[i0:i1]; proc_y = res.emg_proc[i0:i1]; env_y = res.emg_env[i0:i1]
        fig, axes = plt.subplots(3, 1, figsize=(13, 8), sharex=True)
        span_note = f"t=[{t0:.2f}, {t1:.2f}] s (page {i+1}/{len(starts)})"
        _emg_axes_plot(axes, tt, raw_y, proc_y, env_y, span_note)
        fig.suptitle(title); plt.tight_layout()
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            fname = f"page_{i+1:02d}_t0-{t0:.2f}_t1-{t1:.2f}.png"
            fig.savefig(os.path.join(save_dir, fname), dpi=150)
        if not silent:
            plt.show()
        plt.close(fig)

if __name__ == "__main__":
    main()
