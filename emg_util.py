
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
    * Detects fatigue onset (≥15% MDF drop after 20% of capture)
    * Saves fatigue_summary.csv and fatigue_trend.png
"""

from __future__ import annotations
import argparse, glob, os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

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
    return out.sort_values("ts_ms", kind="mergesort").reset_index(drop=True)

def load_vitals_log(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, engine="python")
    missing = [c for c in VITALS_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{path} missing required columns: {missing}")
    df = df[VITALS_COLS].copy()
    for c in VITALS_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["ts_ms"]).sort_values("ts_ms", kind="mergesort").reset_index(drop=True)

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


# -----------------------------
# Classic EMG features (time + spectral proxies)
# Inspired by feature_ml.py: MAV, RMS, WL, ZC, SSC
# -----------------------------

def feat_mav(sig: np.ndarray) -> float:
    return float(np.nanmean(np.abs(sig)))


def feat_rms(sig: np.ndarray) -> float:
    return float(np.sqrt(np.nanmean(sig * sig)))


def feat_wl(sig: np.ndarray) -> float:
    return float(np.nansum(np.abs(np.diff(sig))))


def feat_zc(sig: np.ndarray, thr: float = 0.01) -> float:
    s = sig - np.nanmean(sig)
    return float(np.nansum(((s[:-1] * s[1:]) < 0) & (np.abs(s[:-1] - s[1:]) > thr)))


def feat_ssc(sig: np.ndarray, thr: float = 0.01) -> float:
    s = sig - np.nanmean(sig)
    a = s[1:-1] - s[:-2]
    b = s[1:-1] - s[2:]
    return float(np.nansum((a * b > 0) & (np.abs(a) > thr) & (np.abs(b) > thr)))

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
    emg = df[df["raw"].notna()].copy().sort_values("ts_ms", kind="mergesort").reset_index(drop=True)
    imu = df[df[["ax","ay","az","gx","gy","gz"]].notna().any(axis=1)].copy().sort_values("ts_ms", kind="mergesort").reset_index(drop=True)
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
        vit = vitals.copy().dropna(subset=["ts_ms"]).sort_values("ts_ms", kind="mergesort").reset_index(drop=True)
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
    """Fatigue trend analysis.

    Backward/forward compatible with different feature column naming schemes.

    Expected (preferred) columns:
      - time: t_center_s
      - MDF : EMG_MDF_Hz
      - MNF : EMG_MNF_Hz

    Also supports:
      - time: t_center / time_s
      - MDF : mdf / MDF
      - MNF : mnf / MNF
    """

    if feats is None or len(feats) < 10:
        print("Not enough data for fatigue analysis.")
        return

    def pick_col(cands):
        for c in cands:
            if c in feats.columns:
                return c
        return None

    t_col = pick_col(["t_center_s", "t_center", "time_s", "time"])
    mdf_col = pick_col(["EMG_MDF_Hz", "mdf", "MDF", "emg_mdf_hz", "EMG_MDF"])
    mnf_col = pick_col(["EMG_MNF_Hz", "mnf", "MNF", "emg_mnf_hz", "EMG_MNF"])

    if t_col is None or mdf_col is None or mnf_col is None:
        raise KeyError(
            f"Fatigue analysis requires time+MDF+MNF columns. "
            f"Found columns: {list(feats.columns)}. "
            f"Looked for time in [t_center_s,t_center,time_s,time], "
            f"MDF in [EMG_MDF_Hz,mdf,MDF,...], MNF in [EMG_MNF_Hz,mnf,MNF,...]."
        )

    # Ensure numeric arrays
    t = pd.to_numeric(feats[t_col], errors='coerce').to_numpy(dtype=float)
    mdf = pd.to_numeric(feats[mdf_col], errors='coerce').to_numpy(dtype=float)
    mnf = pd.to_numeric(feats[mnf_col], errors='coerce').to_numpy(dtype=float)

    total_sec = float(np.nanmax(t))
    baseline_idx = max(1, int(len(feats) * 0.1))

    baseline_MDF = float(np.nanmean(mdf[:baseline_idx]))
    baseline_MNF = float(np.nanmean(mnf[:baseline_idx]))
    final_MDF = float(np.nanmean(mdf[-baseline_idx:]))
    final_MNF = float(np.nanmean(mnf[-baseline_idx:]))

    MDF_drop_pct = 100.0 * (baseline_MDF - final_MDF) / baseline_MDF if baseline_MDF else np.nan
    MNF_drop_pct = 100.0 * (baseline_MNF - final_MNF) / baseline_MNF if baseline_MNF else np.nan

    # Slopes (ignore NaNs)
    def safe_polyfit(x, y):
        m = np.isfinite(x) & np.isfinite(y)
        if m.sum() < 5:
            return np.nan
        return float(np.polyfit(x[m], y[m], 1)[0])

    slope_MDF = safe_polyfit(t, mdf)
    slope_MNF = safe_polyfit(t, mnf)

    # Onset detection: after 20% of capture, rolling average crosses threshold
    onset_time = np.nan
    if np.isfinite(baseline_MDF) and baseline_MDF != 0:
        threshold = baseline_MDF * 0.85
        min_time = total_sec * 0.2
        rolling = pd.Series(mdf).rolling(window=20, min_periods=5).mean().to_numpy(dtype=float)
        cand = np.where((t >= min_time) & (rolling <= threshold))[0]
        if len(cand):
            onset_time = float(t[cand[0]])

    summary = {
        "baseline_MDF": baseline_MDF,
        "baseline_MNF": baseline_MNF,
        "final_MDF": final_MDF,
        "final_MNF": final_MNF,
        "MDF_drop_pct": MDF_drop_pct,
        "MNF_drop_pct": MNF_drop_pct,
        "slope_MDF": slope_MDF,
        "slope_MNF": slope_MNF,
        "fatigue_onset_s": onset_time,
        "time_col": t_col,
        "mdf_col": mdf_col,
        "mnf_col": mnf_col,
    }

    print("[Fatigue] MDF drop % =", MDF_drop_pct, "; MNF drop % =", MNF_drop_pct, "; onset_s =", onset_time)

    # Save summary + plot
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        out_csv = os.path.join(save_dir, 'fatigue_summary.csv')
        pd.DataFrame([summary]).to_csv(out_csv, index=False)
        print(f"Saved: {out_csv}")

        try:
            fig, ax = plt.subplots(1, 1, figsize=(10, 4))
            ax.plot(t, mdf, label=f"MDF ({mdf_col})")
            ax.plot(t, mnf, label=f"MNF ({mnf_col})", alpha=0.85)
            if np.isfinite(baseline_MDF):
                ax.axhline(baseline_MDF, color='k', ls='--', lw=1, alpha=0.6, label='baseline MDF')
                ax.axhline(baseline_MDF*0.85, color='r', ls='--', lw=1, alpha=0.6, label='85% MDF threshold')
            if np.isfinite(onset_time):
                ax.axvline(onset_time, color='r', lw=1.5, alpha=0.8, label='fatigue onset')
            ax.set_xlabel('time (s)')
            ax.set_ylabel('frequency (Hz)')
            ax.set_title('Fatigue trend (MDF/MNF)')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='best')
            out_png = os.path.join(save_dir, 'fatigue_trend.png')
            fig.tight_layout()
            fig.savefig(out_png, dpi=150)
            plt.close(fig)
            print(f"Saved: {out_png}")
        except Exception as e:
            print(f"[WARN] Could not save fatigue plot: {e}")

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
    axes[4].set_title("EMG spectral features");
    axes[4].legend();
    axes[4].grid(True, alpha=0.2)
    axes[5].plot(feats["t_center_s"], feats["IMU_acc_rms"], lw=1.2, label="IMU acc RMS")
    axes[5].plot(feats["t_center_s"], feats["IMU_gyro_rms"], lw=1.2, label="IMU gyro RMS", alpha=0.85)
    axes[5].set_title("IMU activity features");
    axes[5].legend();
    axes[5].grid(True, alpha=0.2)
    fig.suptitle(title);
    plt.tight_layout()
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
        raw_y = res.emg_raw[i0:i1];
        proc_y = res.emg_proc[i0:i1];
        env_y = res.emg_env[i0:i1]
        fig, axes = plt.subplots(3, 1, figsize=(13, 8), sharex=True)
        span_note = f"t=[{t0:.2f}, {t1:.2f}] s (page {i + 1}/{len(starts)})"
        _emg_axes_plot(axes, tt, raw_y, proc_y, env_y, span_note)
        fig.suptitle(title);
        plt.tight_layout()
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            fname = f"page_{i + 1:02d}_t0-{t0:.2f}_t1-{t1:.2f}.png"
            fig.savefig(os.path.join(save_dir, fname), dpi=150)
        if not silent:
            plt.show()
        plt.close(fig)




# ============================
# IMU detailed analysis helpers
# ============================
try:
    import imu_feature as imu_feat  # leverages shared imu_feature.py
except Exception:
    imu_feat = None

def extract_imu_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows where any of ax..gz is present."""
    imu_cols = ["ax","ay","az","gx","gy","gz"]
    imu = df[df[imu_cols].notna().any(axis=1)].copy()
    imu = imu.sort_values("ts_ms", kind="mergesort").reset_index(drop=True)
    for c in imu_cols:
        imu[c] = pd.to_numeric(imu[c], errors="coerce")
    imu = imu.dropna(subset=["ts_ms"])
    return imu

def imu_segments(imu: pd.DataFrame, gap_ms: float = 50.0, min_samples: int = 50) -> pd.DataFrame:
    """Split IMU stream into 'continuous' segments by timestamp gap."""
    if len(imu) == 0:
        return pd.DataFrame(columns=["seg_id","n","t0_ms","t1_ms","dur_s","fs_est_hz","gyro_max","gyro_mean","acc_range"])
    ts = imu["ts_ms"].to_numpy(dtype=np.int64)
    dt = np.diff(ts)
    breaks = np.where(dt > gap_ms)[0]
    starts = np.r_[0, breaks + 1]
    ends = np.r_[breaks + 1, len(imu)]
    rows = []
    imu_cols = ["ax","ay","az","gx","gy","gz"]
    for seg_id, (s,e) in enumerate(zip(starts, ends)):
        seg = imu.iloc[s:e]
        if len(seg) < min_samples:
            continue
        dur_s = (float(seg["ts_ms"].iloc[-1]) - float(seg["ts_ms"].iloc[0])) / 1000.0
        if dur_s <= 0:
            continue
        acc_mag = np.sqrt(seg["ax"]**2 + seg["ay"]**2 + seg["az"]**2)
        gyro_mag = np.sqrt(seg["gx"]**2 + seg["gy"]**2 + seg["gz"]**2)
        fs_est = (len(seg) - 1) / dur_s
        rows.append({
            "seg_id": seg_id,
            "s": int(s),
            "e": int(e),
            "n": int(len(seg)),
            "t0_ms": float(seg["ts_ms"].iloc[0]),
            "t1_ms": float(seg["ts_ms"].iloc[-1]),
            "dur_s": float(dur_s),
            "fs_est_hz": float(fs_est),
            "gyro_max": float(np.nanmax(gyro_mag)),
            "gyro_mean": float(np.nanmean(gyro_mag)),
            "gyro_std": float(np.nanstd(gyro_mag, ddof=1) if len(gyro_mag) > 1 else 0.0),
            "acc_range": float(np.nanmax(acc_mag) - np.nanmin(acc_mag)),
        })
    return pd.DataFrame(rows).sort_values(["t0_ms"]).reset_index(drop=True)

def build_time_axis_from_ts(imu: pd.DataFrame, fs_fallback: float = 200.0) -> np.ndarray:
    """Build a monotonically increasing time axis (seconds) even when ts_ms repeats.

    Many logs have multiple IMU samples with the same ts_ms. We spread samples within
    the next timestamp delta (or a robust median delta) to get usable time for filtering.
    """
    ts = imu["ts_ms"].to_numpy(dtype=np.int64)
    # group indices by identical ts
    # For each group, distribute samples within dt_to_next.
    uniq, idx_start, counts = np.unique(ts, return_index=True, return_counts=True)
    # compute dt between unique timestamps in seconds
    dt_u = np.diff(uniq.astype(np.float64)) / 1000.0
    dt_u_pos = dt_u[dt_u > 0]
    dt_med = float(np.median(dt_u_pos)) if len(dt_u_pos) else 1.0 / fs_fallback

    t = np.empty(len(ts), dtype=float)
    base = 0.0
    # map from unique index to its group slice in original order
    for k, (start, cnt) in enumerate(zip(idx_start, counts)):
        if k < len(dt_u):
            span = float(dt_u[k])
            if span <= 0:
                span = dt_med
        else:
            span = dt_med
        if cnt == 1:
            t[start] = base
        else:
            # distribute within [0, span) (not including endpoint to keep monotonicity)
            offs = np.linspace(0.0, span, cnt, endpoint=False)
            t[start:start+cnt] = base + offs
        base += span
    # shift to start at 0
    t -= t[0]
    # ensure strictly increasing (tiny epsilon if needed)
    eps = 1e-9
    for i in range(1, len(t)):
        if t[i] <= t[i-1]:
            t[i] = t[i-1] + eps
    return t

def detect_movement_intervals(t_s: np.ndarray, acc_mag: np.ndarray, gyro_mag: np.ndarray,
                             baseline_s: float = 1.0, z_thr: float = 3.0,
                             min_consec: int = 5) -> list[tuple[float,float]]:
    """Z-score based movement detection from acc/gyro magnitudes."""
    t_s = np.asarray(t_s, dtype=float)
    acc_mag = np.asarray(acc_mag, dtype=float)
    gyro_mag = np.asarray(gyro_mag, dtype=float)
    base = t_s <= min(baseline_s, t_s.max() / 5.0 if t_s.size else baseline_s)
    if not np.any(base):
        base = slice(0, min(len(t_s), 10))
    acc_mu = float(np.nanmean(acc_mag[base]))
    acc_sd = float(np.nanstd(acc_mag[base], ddof=1)) if np.sum(base) > 1 else 1.0
    gy_mu  = float(np.nanmean(gyro_mag[base]))
    gy_sd  = float(np.nanstd(gyro_mag[base], ddof=1)) if np.sum(base) > 1 else 1.0
    acc_z = (acc_mag - acc_mu) / (acc_sd if acc_sd > 1e-9 else 1e-9)
    gy_z  = (gyro_mag - gy_mu) / (gy_sd if gy_sd > 1e-9 else 1e-9)
    move = (np.abs(acc_z) > z_thr) | (np.abs(gy_z) > z_thr)

    flags = np.zeros_like(move, dtype=bool)
    cnt = 0
    for i, v in enumerate(move):
        cnt = cnt + 1 if v else 0
        flags[i] = cnt >= min_consec

    intervals = []
    active = False
    start = None
    for i, f in enumerate(flags):
        if f and not active:
            active = True
            start = float(t_s[i])
        if active and (not f or i == len(flags)-1):
            end = float(t_s[i])
            intervals.append((start, end))
            active = False
    return intervals

def run_imu_detail(emg_imu_df: pd.DataFrame, save_dir: str | None,
                   gap_ms: float = 50.0, min_samples: int = 50,
                   win_s: float = 0.5, overlap: float = 0.5,
                   baseline_s: float = 1.0, z_thr: float = 3.0):
    """Compute IMU segments + features + movement intervals; save CSV/plots."""
    imu = extract_imu_rows(emg_imu_df)
    if len(imu) == 0:
        print("No IMU rows found; skipping IMU detail.")
        return

    segs = imu_segments(imu, gap_ms=gap_ms, min_samples=min_samples)
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        segs.to_csv(os.path.join(save_dir, 'imu_segments_summary.csv'), index=False)
        print(f"Saved: {os.path.join(save_dir, 'imu_segments_summary.csv')}")

    # choose candidate segments: top by gyro_max (movement) but also keep the latest segment
    candidates = []
    if len(segs):
        top = segs.sort_values('gyro_max', ascending=False).head(3)
        last = segs.sort_values('t0_ms', ascending=False).head(1)
        cand = pd.concat([top, last]).drop_duplicates(subset=['s','e']).reset_index(drop=True)
        candidates = cand.to_dict('records')

    all_feat_rows = []
    for c in candidates:
        s, e = int(c['s']), int(c['e'])
        seg = imu.iloc[s:e].copy()
        t = build_time_axis_from_ts(seg)
        seg = seg.reset_index(drop=True)
        seg['time'] = t
        seg['acc_mag'] = np.sqrt(seg['ax']**2 + seg['ay']**2 + seg['az']**2)
        seg['gyro_mag'] = np.sqrt(seg['gx']**2 + seg['gy']**2 + seg['gz']**2)
        intervals = detect_movement_intervals(seg['time'].to_numpy(), seg['acc_mag'].to_numpy(),
                                             seg['gyro_mag'].to_numpy(), baseline_s=baseline_s,
                                             z_thr=z_thr, min_consec=5)
        # feature extraction using imu_feature if available
        feats = None
        if imu_feat is not None and hasattr(imu_feat, 'compute_features'):
            feat_df = seg[['time','ax','ay','az','gx','gy','gz']].rename(columns={'time':'time'})
            fs_est = float(c.get('fs_est_hz', 200.0))
            # Adapt window length so we always have at least one window in short segments
            fs_est = float(c.get('fs_est_hz', 200.0))
            n_samp = len(seg)
            win_samples = int(round(win_s * fs_est))
            win_samples = max(20, min(win_samples, n_samp))  # clamp
            win_s_eff = win_samples / fs_est
            overlap_eff = float(np.clip(overlap, 0.0, 0.95))
            feats = imu_feat.compute_features(feat_df, fs=fs_est, win_s=win_s_eff, overlap=overlap_eff,
                                              baseline_mask=(0.0, baseline_s))
            feats['seg_id'] = c['seg_id']
            feats['seg_t0_offset_s'] = (c['t0_ms'] - float(emg_imu_df['ts_ms'].min()))/1000.0
            all_feat_rows.append(feats)

        # plotting
        if save_dir:
            import matplotlib.pyplot as plt
            fig, axes = plt.subplots(3, 1, figsize=(12, 7), sharex=True)
            axes[0].plot(seg['time'], seg['acc_mag'], lw=1.0)
            axes[0].set_ylabel('acc_mag (raw)')
            axes[0].grid(True, alpha=0.3)
            axes[1].plot(seg['time'], seg['gyro_mag'], lw=1.0, color='tab:red')
            axes[1].set_ylabel('gyro_mag (raw)')
            axes[1].grid(True, alpha=0.3)
            axes[2].plot(seg['time'], seg['ax'], label='ax', alpha=0.7)
            axes[2].plot(seg['time'], seg['ay'], label='ay', alpha=0.7)
            axes[2].plot(seg['time'], seg['az'], label='az', alpha=0.7)
            axes[2].set_ylabel('acc axes (raw)')
            axes[2].set_xlabel('time (s)')
            axes[2].legend(ncol=3, fontsize=8)
            axes[2].grid(True, alpha=0.3)
            for (a,b) in intervals:
                for ax in axes:
                    ax.axvspan(a,b, color='orange', alpha=0.15)
            fig.suptitle(f"IMU segment seg_id={c['seg_id']} offset=[{c['t0_ms']:.0f},{c['t1_ms']:.0f}]ms, intervals={len(intervals)}")
            fig.tight_layout()
            outp = os.path.join(save_dir, f"imu_segment_{int(c['seg_id']):03d}.png")
            fig.savefig(outp, dpi=150)
            plt.close(fig)
            print(f"Saved: {outp}")

            if feats is not None and len(feats):
                fig, ax = plt.subplots(1,1, figsize=(12,4))
                tt = 0.5*(feats['t_start'] + feats['t_end'])
                ax.plot(tt, feats['gyro_rms'], label='gyro_rms')
                ax.plot(tt, feats['acc_rms'], label='acc_rms', alpha=0.85)
                ax.plot(tt, feats['jerk_rms'], label='jerk_rms', alpha=0.85)
                ax.set_xlabel('time (s)')
                ax.set_title('IMU windowed features')
                ax.grid(True, alpha=0.3)
                ax.legend()
                outp2 = os.path.join(save_dir, f"imu_features_{int(c['seg_id']):03d}.png")
                fig.tight_layout()
                fig.savefig(outp2, dpi=150)
                plt.close(fig)
                print(f"Saved: {outp2}")

    if save_dir and all_feat_rows:
        all_feats = pd.concat(all_feat_rows, ignore_index=True)
        all_feats.to_csv(os.path.join(save_dir, 'imu_window_features.csv'), index=False)
        print(f"Saved: {os.path.join(save_dir, 'imu_window_features.csv')}")



# ============================
# Phase-1 Windowed + Swing-aligned features (no FSR required)
# ============================

def robust_zscore(x: np.ndarray, baseline_mask: np.ndarray, eps: float = 1e-9) -> tuple[np.ndarray, float, float]:
    """Robust z-score using median and MAD."""
    x = np.asarray(x, dtype=float)
    baseline_mask = np.asarray(baseline_mask, dtype=bool)
    xb = x[baseline_mask]
    xb = xb[np.isfinite(xb)]
    if len(xb) < 10:
        xb = x[np.isfinite(x)]
    med = float(np.median(xb)) if len(xb) else float(np.nanmedian(x))
    mad = float(np.median(np.abs(xb - med))) if len(xb) else float(np.nanmedian(np.abs(x - med)))
    scale = 1.4826 * mad
    if not np.isfinite(scale) or scale < eps:
        scale = float(np.nanstd(xb)) if len(xb) else float(np.nanstd(x))
        if not np.isfinite(scale) or scale < eps:
            scale = 1.0
    z = (x - med) / (scale + eps)
    return z, med, scale


def detect_swing_windows_from_imu(imu_df: pd.DataFrame,
                                 baseline_s: float = 2.0,
                                 z_thr: float = 5.0,
                                 min_consec: int = 3,
                                 min_gap_ms: float = 300.0,
                                 pre_ms: float = 250.0,
                                 post_ms: float = 450.0,
                                 use_gyro: bool = True) -> pd.DataFrame:
    """Detect swing windows from IMU magnitude using robust z-score (no FSR needed)."""
    if imu_df is None or len(imu_df) == 0:
        return pd.DataFrame(columns=["swing_id","t_start_ms","t_peak_ms","t_end_ms","peak_z","peak_mag"])

    imu = imu_df.copy().dropna(subset=["ts_ms"]).sort_values("ts_ms", kind="mergesort").reset_index(drop=True)
    if len(imu) == 0:
        return pd.DataFrame(columns=["swing_id","t_start_ms","t_peak_ms","t_end_ms","peak_z","peak_mag"])

    t_rel_s = build_time_axis_from_ts(imu, fs_fallback=200.0)
    t0_ms = float(imu["ts_ms"].iloc[0])
    t_ms = t0_ms + 1000.0 * t_rel_s

    if use_gyro:
        mag = np.sqrt(imu["gx"].to_numpy(float)**2 + imu["gy"].to_numpy(float)**2 + imu["gz"].to_numpy(float)**2)
    else:
        mag = np.sqrt(imu["ax"].to_numpy(float)**2 + imu["ay"].to_numpy(float)**2 + imu["az"].to_numpy(float)**2)

    total_s = float(np.nanmax(t_rel_s)) if len(t_rel_s) else float(baseline_s)
    b_s = min(float(baseline_s), max(0.2 * total_s, 0.5))
    z, _, _ = robust_zscore(mag, t_rel_s <= b_s)

    active = z > float(z_thr)
    if int(min_consec) > 1:
        run = 0
        flags = np.zeros_like(active, dtype=bool)
        for i, v in enumerate(active):
            run = run + 1 if v else 0
            flags[i] = run >= int(min_consec)
        active = flags

    peaks = []
    i = 0
    while i < len(active):
        if not active[i]:
            i += 1
            continue
        j = i
        while j < len(active) and active[j]:
            j += 1
        seg = slice(i, j)
        k = int(i + np.nanargmax(z[seg]))
        peaks.append(k)
        i = j

    if not peaks:
        return pd.DataFrame(columns=["swing_id","t_start_ms","t_peak_ms","t_end_ms","peak_z","peak_mag"])

    peaks_sorted = sorted(peaks, key=lambda k: t_ms[k])
    kept = []
    last_t = -1e18
    for k in peaks_sorted:
        if (t_ms[k] - last_t) >= float(min_gap_ms):
            kept.append(k)
            last_t = t_ms[k]
        else:
            if kept and z[k] > z[kept[-1]]:
                kept[-1] = k
                last_t = t_ms[k]

    rows = []
    for si, k in enumerate(kept):
        tp = float(t_ms[k])
        rows.append({
            "swing_id": int(si),
            "t_start_ms": tp - float(pre_ms),
            "t_peak_ms": tp,
            "t_end_ms": tp + float(post_ms),
            "peak_z": float(z[k]),
            "peak_mag": float(mag[k]),
        })

    win = pd.DataFrame(rows).sort_values("t_start_ms").reset_index(drop=True)
    merged = []
    cur = win.iloc[0].to_dict()
    for r in win.iloc[1:].to_dict('records'):
        if r["t_start_ms"] <= cur["t_end_ms"]:
            cur["t_end_ms"] = max(cur["t_end_ms"], r["t_end_ms"])
            if r["peak_z"] > cur["peak_z"]:
                cur.update({"t_peak_ms": r["t_peak_ms"], "peak_z": r["peak_z"], "peak_mag": r["peak_mag"]})
        else:
            merged.append(cur)
            cur = r
    merged.append(cur)
    out = pd.DataFrame(merged)
    out["swing_id"] = np.arange(len(out), dtype=int)
    return out[["swing_id","t_start_ms","t_peak_ms","t_end_ms","peak_z","peak_mag"]]


def compute_emg_window_features(proc: np.ndarray, env: np.ndarray, emg_ts_ms: np.ndarray,
                                emg_fs_hz: float, win_sec: float, step_sec: float,
                                emg_thr_zc: float = 0.01, emg_thr_ssc: float = 0.01) -> pd.DataFrame:
    """Compute windowed EMG features on processed signal plus envelope features."""
    win_samp = max(int(round(win_sec * emg_fs_hz)), 256)
    step_samp = max(int(round(step_sec * emg_fs_hz)), 1)
    rows = []
    for i0 in range(0, len(proc) - win_samp + 1, step_samp):
        i1 = i0 + win_samp
        t_start_ms = float(emg_ts_ms[i0])
        t_end_ms = float(emg_ts_ms[i1 - 1])
        seg = proc[i0:i1]
        seg_env = env[i0:i1]
        mnf_val, mdf_val = mnf_mdf(seg, emg_fs_hz)
        rows.append({
            "t_start_ms": t_start_ms,
            "t_end_ms": t_end_ms,
            "t_center_s": 0.5*(t_start_ms + t_end_ms)/1000.0,
            "mav": feat_mav(seg),
            "rms": feat_rms(seg),
            "wl": feat_wl(seg),
            "zc": feat_zc(seg, thr=emg_thr_zc),
            "ssc": feat_ssc(seg, thr=emg_thr_ssc),
            "mnf": float(mnf_val),
            "mdf": float(mdf_val),
            "env_mean": float(np.nanmean(seg_env)),
            "env_peak": float(np.nanmax(seg_env)),
        })
    return pd.DataFrame(rows)


def compute_swing_emg_features(res: Results, emg_fs_hz: float, swings: pd.DataFrame,
                              mdf_pad_ms: float = 300.0,
                              thr_zc: float = 0.01, thr_ssc: float = 0.01) -> pd.DataFrame:
    """Compute per-swing EMG features. MDF is computed on a padded window for PSD stability."""
    if swings is None or len(swings) == 0:
        return pd.DataFrame(columns=["swing_id","t_start_ms","t_peak_ms","t_end_ms","peak_z","peak_mag",
                                     "emg_env_peak","emg_env_mean","emg_iemg",
                                     "mav","rms","wl","zc","ssc","mdf","mnf"])

    ts = res.emg_ts_ms
    proc = res.emg_proc
    env = res.emg_env
    dt = 1.0 / float(emg_fs_hz)

    rows = []
    for r in swings.to_dict('records'):
        t0 = float(r['t_start_ms'])
        t1 = float(r['t_end_ms'])

        # envelope features on exact swing window
        i0 = int(np.searchsorted(ts, t0, side='left'))
        i1 = int(np.searchsorted(ts, t1, side='right'))
        i0 = max(0, min(i0, len(ts)-1))
        i1 = max(i0+1, min(i1, len(ts)))
        seg_env = env[i0:i1]
        emg_env_peak = float(np.nanmax(seg_env))
        emg_env_mean = float(np.nanmean(seg_env))
        emg_iemg = float(np.nansum(seg_env) * dt)

        # processed features on padded window
        t0p = t0 - float(mdf_pad_ms)
        t1p = t1 + float(mdf_pad_ms)
        j0 = int(np.searchsorted(ts, t0p, side='left'))
        j1 = int(np.searchsorted(ts, t1p, side='right'))
        j0 = max(0, min(j0, len(ts)-1))
        j1 = max(j0+1, min(j1, len(ts)))
        seg = proc[j0:j1]
        mnf_val, mdf_val = mnf_mdf(seg, emg_fs_hz)

        rows.append({
            "swing_id": int(r['swing_id']),
            "t_start_ms": t0,
            "t_peak_ms": float(r['t_peak_ms']),
            "t_end_ms": t1,
            "peak_z": float(r.get('peak_z', np.nan)),
            "peak_mag": float(r.get('peak_mag', np.nan)),
            "emg_env_peak": emg_env_peak,
            "emg_env_mean": emg_env_mean,
            "emg_iemg": emg_iemg,
            "mav": feat_mav(seg),
            "rms": feat_rms(seg),
            "wl": feat_wl(seg),
            "zc": feat_zc(seg, thr=thr_zc),
            "ssc": feat_ssc(seg, thr=thr_ssc),
            "mnf": float(mnf_val),
            "mdf": float(mdf_val),
        })

    return pd.DataFrame(rows)


def select_baseline_swings(swings: pd.DataFrame, session_t0_ms: float,
                           warmup_skip_min: float = 5.0,
                           warmup_skip_swings: int | None = None,
                           baseline_swings: int = 20) -> pd.DataFrame:
    """Select baseline swings after warm-up skip (time-based default) and optional swing-count skip."""
    if swings is None or len(swings) == 0:
        return swings
    sw = swings.sort_values('t_peak_ms').reset_index(drop=True)
    cutoff = float(session_t0_ms) + float(warmup_skip_min) * 60.0 * 1000.0
    sw2 = sw[sw['t_peak_ms'] >= cutoff].reset_index(drop=True)
    if len(sw2) < max(3, baseline_swings//2):
        sw2 = sw
    if warmup_skip_swings is not None and warmup_skip_swings > 0:
        sw2 = sw2.iloc[int(warmup_skip_swings):].reset_index(drop=True)
    return sw2.iloc[:int(baseline_swings)].reset_index(drop=True)


def compute_baseline_from_swing_features(swing_feats: pd.DataFrame) -> dict:
    """Compute robust baseline values from per-swing features (median)."""
    base = {}
    if swing_feats is None or len(swing_feats) == 0:
        return base
    for k in ['mdf','rms','mav','wl','emg_env_mean','emg_iemg']:
        if k in swing_feats.columns:
            base[k] = float(np.nanmedian(swing_feats[k].to_numpy(dtype=float)))
    return base


def compute_baseline_from_windows(win_feats: pd.DataFrame, baseline_window_sec: float = 60.0) -> dict:
    """Compute baseline values from first baseline_window_sec seconds of windowed features."""
    base = {}
    if win_feats is None or len(win_feats) == 0:
        return base
    t0 = float(win_feats['t_start_ms'].min())
    cutoff = t0 + float(baseline_window_sec) * 1000.0
    seg = win_feats[win_feats['t_end_ms'] <= cutoff]
    if len(seg) < 5:
        seg = win_feats.iloc[:min(20, len(win_feats))]
    for k in ['mdf','rms','mav','wl','env_mean','emg_env_mean','emg_iemg']:
        if k in seg.columns:
            base[k] = float(np.nanmedian(seg[k].to_numpy(dtype=float)))
    return base


def apply_baseline_deltas(df: pd.DataFrame, base: dict, prefix: str = '') -> pd.DataFrame:
    """Add baseline-relative percentage deltas for MDF drop and RMS increase."""
    out = df.copy()
    if not base:
        return out
    if 'mdf' in out.columns and 'mdf' in base and base['mdf'] not in (0, None) and np.isfinite(base['mdf']):
        out[prefix + 'mdf_drop_pct'] = (base['mdf'] - out['mdf']) / base['mdf'] * 100.0
    if 'rms' in out.columns and 'rms' in base and base['rms'] not in (0, None) and np.isfinite(base['rms']):
        out[prefix + 'rms_increase_pct'] = (out['rms'] - base['rms']) / base['rms'] * 100.0
    return out


# -----------------------------
# Real-time fatigue monitor (pandas-free — works on PC, Colab, and Android)
#
# SYNC NOTE: This class is the primary development version.
#   Keep in sync with emg_util_nopandas.py::FatigueMonitor (Android/Chaquopy).
#   Workflow: develop/polish here, then port changes back to emg_util_nopandas.py.
#
# Uses preprocess_emg() and mnf_mdf() from this file (scipy-based, full quality).
# No pandas dependency — safe to import in any context.
# -----------------------------

class FatigueMonitor:
    """Stateful per-session fatigue tracker for real-time use.

    Designed for use with sensordata_plotter.py (live UDP) and offline CSV playback.

    Usage:
        monitor = FatigueMonitor(fs=2000.0, warmup_skip_min=0.0, baseline_swings=20)
        monitor.reset()
        result = monitor.push_swing(emg_raw_list, t_peak_ms, imu_peak_mag)
        # result is a plain dict -- JSON-serializable

    Fatigue levels:
        "warming_up"  -- before baseline is established
        "fresh"       -- MDF drop < mdf_warn_pct  (green)
        "moderate"    -- MDF drop >= mdf_warn_pct  (yellow)
        "high"        -- MDF drop >= mdf_high_pct  (red)

    Baseline is established from the first `baseline_swings` swings
    that occur after `warmup_skip_min` minutes.
    """

    def __init__(
        self,
        fs: float = 2000.0,
        warmup_skip_min: float = 5.0,
        baseline_swings: int = 20,
        mdf_warn_pct: float = 12.0,
        mdf_high_pct: float = 20.0,
    ):
        self._fs = float(fs)
        self._warmup_skip_ms = warmup_skip_min * 60.0 * 1000.0
        self._baseline_swings = int(baseline_swings)
        self._mdf_warn_pct = float(mdf_warn_pct)   # yellow threshold
        self._mdf_high_pct = float(mdf_high_pct)   # red threshold

        # Session state (reset on each new session)
        self._swing_id: int = 0
        self._t_session_start_ms: Optional[float] = None
        self._baseline_mdf: Optional[float] = None
        self._baseline_rms: Optional[float] = None
        self._baseline_samples: List[Tuple[float, float]] = []  # (mdf, rms)
        self._history: List[dict] = []

    def reset(self) -> None:
        """Call at the start of each new session."""
        self._swing_id = 0
        self._t_session_start_ms = None
        self._baseline_mdf = None
        self._baseline_rms = None
        self._baseline_samples = []
        self._history = []

    def push_swing(
        self,
        emg_raw: List[float],
        t_peak_ms: float,
        imu_peak_mag: float,
    ) -> dict:
        """Process one swing window and return fatigue metrics.

        Args:
            emg_raw:      raw EMG samples at self._fs Hz
                          (2600 samples = 1300ms at 2000Hz, includes +/-300ms MDF padding)
            t_peak_ms:    absolute time of swing peak in ms (from session start)
            imu_peak_mag: IMU gyro magnitude at swing peak (dps)

        Returns:
            dict with keys:
                swing_id                int
                t_peak_ms               float
                mdf                     float  (Hz, None until first valid swing)
                rms                     float
                env_mean                float
                imu_peak_mag            float
                mdf_drop_pct            float  (None until baseline established)
                rms_increase_pct        float  (None until baseline established)
                fatigue_pct             float  (0-100, None until baseline established)
                fatigue_level           str    ("warming_up"|"fresh"|"moderate"|"high")
                warning                 bool
                baseline_ready          bool
                baseline_swings_collected int
                baseline_mdf            float  (None until baseline established)
        """
        t_peak_ms = float(t_peak_ms)
        imu_peak_mag = float(imu_peak_mag)

        # Record session start time on first swing
        if self._t_session_start_ms is None:
            self._t_session_start_ms = t_peak_ms

        # Compute EMG features
        raw = np.asarray(emg_raw, dtype=np.float64)
        mdf_val = float('nan')
        rms_val = float('nan')
        env_mean = float('nan')

        if raw.size >= 32:
            proc = preprocess_emg(raw, self._fs)
            _, mdf_val = mnf_mdf(proc, self._fs)
            rms_val = float(np.sqrt(np.nanmean(proc * proc)))
            env_mean = float(np.nanmean(np.abs(raw)))

        # Baseline collection: after warmup, first N valid swings
        t_elapsed_ms = t_peak_ms - self._t_session_start_ms
        in_warmup = t_elapsed_ms < self._warmup_skip_ms
        baseline_ready = self._baseline_mdf is not None

        if not baseline_ready and not in_warmup:
            if np.isfinite(mdf_val) and np.isfinite(rms_val):
                self._baseline_samples.append((mdf_val, rms_val))
                if len(self._baseline_samples) >= self._baseline_swings:
                    mdfs = [s[0] for s in self._baseline_samples]
                    rmss = [s[1] for s in self._baseline_samples]
                    self._baseline_mdf = float(np.median(mdfs))
                    self._baseline_rms = float(np.median(rmss))

        # Fatigue deltas (only after baseline is established)
        mdf_drop_pct = float('nan')
        rms_increase_pct = float('nan')
        fatigue_pct = float('nan')
        warning = False

        if baseline_ready and np.isfinite(mdf_val):
            if self._baseline_mdf and self._baseline_mdf > 0:
                mdf_drop_pct = (self._baseline_mdf - mdf_val) / self._baseline_mdf * 100.0
            if self._baseline_rms and self._baseline_rms > 0 and np.isfinite(rms_val):
                rms_increase_pct = (rms_val - self._baseline_rms) / self._baseline_rms * 100.0

            # Fatigue % based on MDF drop (clamped 0-100)
            if np.isfinite(mdf_drop_pct):
                fatigue_pct = float(np.clip(mdf_drop_pct / self._mdf_high_pct * 100.0, 0.0, 100.0))
                warning = mdf_drop_pct >= self._mdf_warn_pct

        # Fatigue level label
        if in_warmup or not baseline_ready:
            level = 'warming_up'
        elif not np.isfinite(fatigue_pct):
            level = 'unknown'
        elif fatigue_pct < 33.0:
            level = 'fresh'
        elif fatigue_pct < 67.0:
            level = 'moderate'
        else:
            level = 'high'

        result = {
            'swing_id': int(self._swing_id),
            't_peak_ms': t_peak_ms,
            'mdf': round(mdf_val, 2) if np.isfinite(mdf_val) else None,
            'rms': round(rms_val, 4) if np.isfinite(rms_val) else None,
            'env_mean': round(env_mean, 2) if np.isfinite(env_mean) else None,
            'imu_peak_mag': round(imu_peak_mag, 1),
            'mdf_drop_pct': round(mdf_drop_pct, 2) if np.isfinite(mdf_drop_pct) else None,
            'rms_increase_pct': round(rms_increase_pct, 2) if np.isfinite(rms_increase_pct) else None,
            'fatigue_pct': round(fatigue_pct, 1) if np.isfinite(fatigue_pct) else None,
            'fatigue_level': level,
            'warning': bool(warning),
            'baseline_ready': bool(baseline_ready),
            'baseline_swings_collected': len(self._baseline_samples),
            'baseline_mdf': round(self._baseline_mdf, 2) if self._baseline_mdf is not None else None,
        }

        self._history.append(result)
        self._swing_id += 1
        return result

    def get_summary(self) -> dict:
        """Return session summary dict (JSON-serializable)."""
        n = len(self._history)
        if n == 0:
            return {'num_swings': 0, 'baseline_ready': False}

        mdfs  = [r['mdf']          for r in self._history if r['mdf']          is not None]
        drops = [r['mdf_drop_pct'] for r in self._history if r['mdf_drop_pct'] is not None]
        warnings = sum(1 for r in self._history if r['warning'])

        return {
            'num_swings': n,
            'baseline_ready': bool(self._baseline_mdf is not None),
            'baseline_mdf': round(self._baseline_mdf, 2) if self._baseline_mdf is not None else None,
            'baseline_rms': round(self._baseline_rms, 4) if self._baseline_rms is not None else None,
            'latest_mdf': round(mdfs[-1], 2) if mdfs else None,
            'latest_mdf_drop_pct': round(drops[-1], 2) if drops else None,
            'max_mdf_drop_pct': round(max(drops), 2) if drops else None,
            'warning_swings': warnings,
            'fatigue_level': self._history[-1]['fatigue_level'] if self._history else 'unknown',
        }


# -----------------------------
# CLI
# -----------------------------
def main():
    ap = argparse.ArgumentParser(description="btCentral EMG/IMU/Vitals analysis + fatigue detection (windowed + swing-aligned)")
    ap.add_argument("--emg-imu", required=True, help="Path or glob to emg_imu_log_###.csv")
    ap.add_argument("--emg-fs", type=float, required=True, help="EMG sampling rate in Hz (e.g., 2000)")

    ap.add_argument("--mode", choices=["windowed","swing","both"], default="both",
                    help="Compute windowed features, swing-aligned features, or both")

    ap.add_argument("--win", type=float, default=1.0, help="Window length in seconds (windowed mode)")
    ap.add_argument("--step", type=float, default=0.25, help="Step (hop) in seconds (windowed mode)")

    ap.add_argument("--out", default="features.csv", help="Output CSV of windowed features")
    ap.add_argument("--save-pages", default=None, help="Directory to save plots/CSVs")

    ap.add_argument("--dropout-zeros", action="store_true", help="Treat raw==0 as dropout (experimental)")

    # Swing detection parameters
    ap.add_argument("--swing-baseline-s", type=float, default=2.0, help="Baseline duration (s) for IMU z-score")
    ap.add_argument("--swing-z", type=float, default=5.0, help="Z threshold for swing peak detection")
    ap.add_argument("--swing-min-consec", type=int, default=3, help="Min consecutive IMU samples above threshold")
    ap.add_argument("--swing-min-gap-ms", type=float, default=300.0, help="Min gap (ms) between swing peaks")
    ap.add_argument("--swing-pre-ms", type=float, default=250.0, help="Swing window start relative to peak (ms)")
    ap.add_argument("--swing-post-ms", type=float, default=450.0, help="Swing window end relative to peak (ms)")
    ap.add_argument("--swing-use-acc", action="store_true", help="Use accelerometer magnitude instead of gyro")

    # Baseline policies
    ap.add_argument("--baseline-mode", choices=["swing","window"], default="swing",
                    help="How to form baseline for fatigue deltas")
    ap.add_argument("--warmup-skip-min", type=float, default=5.0, help="Warm-up skip (minutes) for swing baseline")
    ap.add_argument("--warmup-skip-swings", type=int, default=0, help="Optional: skip first K swings after warm-up")
    ap.add_argument("--baseline-swings", type=int, default=20, help="Number of swings to use for baseline")
    ap.add_argument("--baseline-window-sec", type=float, default=60.0, help="Window baseline duration (seconds)")

    # MDF pad
    ap.add_argument("--swing-mdf-pad-ms", type=float, default=300.0, help="Pad swing window by ±ms when computing MDF")

    args = ap.parse_args()

    save_dir = args.save_pages
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)

    emg_imu = load_emg_imu_logs(args.emg_imu)

    # Compute EMG signals
    df = emg_imu.copy()
    emg_df = df[df["raw"].notna()].copy().sort_values("ts_ms", kind="mergesort").reset_index(drop=True)
    if len(emg_df) == 0:
        raise ValueError("No EMG rows found.")

    raw = emg_df["raw"].astype(float).to_numpy()
    if args.dropout_zeros:
        raw[raw == 0] = np.nan
        raw = pd.Series(raw).interpolate(limit=100, limit_direction="both").to_numpy(dtype=float)

    t0_ms = float(emg_df["ts_ms"].iloc[0])
    emg_ts_ms = t0_ms + (np.arange(len(raw)) / float(args.emg_fs)) * 1000.0
    proc = preprocess_emg(raw, float(args.emg_fs))
    env = envelope(proc, float(args.emg_fs))

    res = Results(feats=pd.DataFrame(), emg_ts_ms=emg_ts_ms, emg_raw=raw, emg_proc=proc, emg_env=env)

    window_feats = None
    swing_windows = None
    swing_feats = None

    if args.mode in ("windowed", "both"):
        window_feats = compute_emg_window_features(proc, env, emg_ts_ms, float(args.emg_fs),
                                                   win_sec=args.win, step_sec=args.step)
        # Baseline deltas will be applied later
        window_feats.to_csv(args.out, index=False)
        print(f"Saved {args.out} (rows={len(window_feats)})")
        res.feats = window_feats

    if args.mode in ("swing", "both"):
        imu_df = df[df[["ax","ay","az","gx","gy","gz"]].notna().any(axis=1)].copy()
        imu_df = imu_df.dropna(subset=["ts_ms"]).sort_values("ts_ms", kind="mergesort").reset_index(drop=True)
        if len(imu_df) == 0:
            print("[WARN] No IMU rows found; cannot do swing detection.")
        else:
            swing_windows = detect_swing_windows_from_imu(
                imu_df,
                baseline_s=args.swing_baseline_s,
                z_thr=args.swing_z,
                min_consec=args.swing_min_consec,
                min_gap_ms=args.swing_min_gap_ms,
                pre_ms=args.swing_pre_ms,
                post_ms=args.swing_post_ms,
                use_gyro=(not args.swing_use_acc)
            )
            swing_feats = compute_swing_emg_features(res, float(args.emg_fs), swing_windows,
                                                     mdf_pad_ms=args.swing_mdf_pad_ms)
            if save_dir:
                swing_windows.to_csv(os.path.join(save_dir, 'swing_windows.csv'), index=False)
                swing_feats.to_csv(os.path.join(save_dir, 'swing_emg_features.csv'), index=False)
                print(f"Saved: {os.path.join(save_dir, 'swing_windows.csv')}")
                print(f"Saved: {os.path.join(save_dir, 'swing_emg_features.csv')}")

    # Baseline
    base = {}
    if args.baseline_mode == 'swing' and swing_windows is not None and swing_feats is not None and len(swing_feats):
        warmup_skip_swings = args.warmup_skip_swings if args.warmup_skip_swings > 0 else None
        base_sw = select_baseline_swings(swing_windows, session_t0_ms=t0_ms,
                                         warmup_skip_min=args.warmup_skip_min,
                                         warmup_skip_swings=warmup_skip_swings,
                                         baseline_swings=args.baseline_swings)
        base_feats = swing_feats[swing_feats['swing_id'].isin(base_sw['swing_id'])]
        base = compute_baseline_from_swing_features(base_feats)
    elif args.baseline_mode == 'window' and window_feats is not None and len(window_feats):
        base = compute_baseline_from_windows(window_feats, baseline_window_sec=args.baseline_window_sec)

    if save_dir and base:
        with open(os.path.join(save_dir, 'baseline.json'), 'w', encoding='utf-8') as f:
            json.dump({'mode': args.baseline_mode, 'baseline': base,
                       'params': {
                           'warmup_skip_min': args.warmup_skip_min,
                           'warmup_skip_swings': args.warmup_skip_swings,
                           'baseline_swings': args.baseline_swings,
                           'baseline_window_sec': args.baseline_window_sec,
                           'swing_mdf_pad_ms': args.swing_mdf_pad_ms,
                       }}, f, indent=2)
        print(f"Saved: {os.path.join(save_dir, 'baseline.json')}")

    # Apply baseline deltas
    if base:
        if window_feats is not None and len(window_feats):
            window_feats2 = apply_baseline_deltas(window_feats, base)
            window_feats2.to_csv(args.out, index=False)
            print(f"Updated {args.out} with baseline deltas")
            res.feats = window_feats2
        if swing_feats is not None and len(swing_feats) and save_dir:
            swing_feats2 = apply_baseline_deltas(swing_feats, base, prefix='swing_')
            swing_feats2.to_csv(os.path.join(save_dir, 'swing_emg_features.csv'), index=False)
            print(f"Updated: {os.path.join(save_dir, 'swing_emg_features.csv')} with baseline deltas")

    # Fatigue analysis on windowed features (uses flexible analyze_fatigue from emg_util_fixed)
    if res.feats is not None and len(res.feats) and args.mode in ("windowed","both"):
        analyze_fatigue(res.feats, save_dir=save_dir)


if __name__ == "__main__":
    main()
