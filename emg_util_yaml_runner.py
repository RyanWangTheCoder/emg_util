# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YAML-driven EMG+IMU analysis runner (Phase-1).

Design goals:
- Minimal CLI: --config only (optionally override input glob / out dir).
- Supports rotated multi-file logs via glob.
- Scalable by default: stroke-aligned (swing) + bout summaries.
- Works without FSR; uses robust z-score on IMU magnitude.

This runner intentionally keeps the CLI small and pushes tuning into YAML.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

# Import the existing processing functions from emg_util.py
# (keeps compatibility with your established filtering and MDF/MNF computation)
import emg_util as core


# ----------------------------
# Diagnostics outputs
# ----------------------------


def save_emg_imu_correlation(feats: pd.DataFrame, out_dir: str,
                             method: str = 'pearson',
                             fname: str = 'emg_imu_correlation.json') -> dict:
    """Compute EMG<->IMU correlation matrix over windowed features and save as JSON."""
    if feats is None or len(feats) == 0:
        return {}

    cols = ['EMG_RMS', 'EMG_ENV_mean', 'EMG_MNF_Hz', 'EMG_MDF_Hz',
            'IMU_acc_rms', 'IMU_gyro_rms']
    cols = [c for c in cols if c in feats.columns]
    if len(cols) < 2:
        return {}

    df = feats[cols].apply(pd.to_numeric, errors='coerce')
    corr = df.corr(method=method).to_dict()

    out = {
        'method': method,
        'n_rows': int(len(df)),
        'columns': cols,
        'correlation': corr,
    }

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, fname), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)

    return out


def save_swing_overlay(imu_df: pd.DataFrame, swings: pd.DataFrame, feats: Optional[pd.DataFrame], cfg: Dict[str, Any],
                       out_dir: str, fname: str = 'swing_overlay.png') -> None:
    """Overlay IMU z-scores with detected swing windows. Supports two-y-axes: left=gyro z, right=acc z."""
    if imu_df is None or len(imu_df) == 0 or swings is None or len(swings) == 0:
        return
    # Monotonic IMU time axis even if ts repeats
    t_rel_s = core.build_time_axis_from_ts(imu_df,
                                           fs_fallback=float(cfg.get('session', {}).get('imu_fs_fallback_hz', 200.0)))
    t0_ms = float(imu_df['ts_ms'].iloc[0])
    t_ms = t0_ms + 1000.0 * t_rel_s
    t_sec = (t_ms - t_ms[0]) / 1000.0
    # Magnitudes
    acc_mag = np.sqrt(
        imu_df['ax'].to_numpy(float) ** 2 + imu_df['ay'].to_numpy(float) ** 2 + imu_df['az'].to_numpy(float) ** 2)
    gyro_mag = np.sqrt(
        imu_df['gx'].to_numpy(float) ** 2 + imu_df['gy'].to_numpy(float) ** 2 + imu_df['gz'].to_numpy(float) ** 2)
    sd = cfg.get('swing_detection', {})
    total_s = float(np.nanmax(t_rel_s)) if len(t_rel_s) else 2.0
    b_s = min(float(sd.get('baseline_s', 2.0)), max(0.2 * total_s, 0.5))
    z_acc, _, _ = robust_zscore(acc_mag, t_rel_s <= b_s)
    z_gyro, _, _ = robust_zscore(gyro_mag, t_rel_s <= b_s)
    diag = cfg.get('diagnostics', {}) or {}
    ov_cfg = diag.get('swing_overlay', {}) or {}
    two_y = bool(ov_cfg.get('two_y_axes', True))
    plot_env = bool(ov_cfg.get('plot_env_mean', True))
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 1, figsize=(13, 4))
    if two_y:
        ax2 = ax.twinx()
        ln1 = ax.plot(t_sec, z_gyro, lw=0.9, color='tab:red', label='gyro z (L)')
        ln2 = ax2.plot(t_sec, z_acc, lw=0.9, color='tab:green', alpha=0.85, label='acc z (R)')
        ax.set_ylabel('gyro z-score (robust)')
        ax2.set_ylabel('acc z-score (robust)')
        lns = ln1 + ln2
        labels = [l.get_label() for l in lns]
        ax.legend(lns, labels, loc='upper right')
    else:
        ax.plot(t_sec, z_gyro, lw=0.9, color='tab:red', label='gyro z')
        ax.plot(t_sec, z_acc, lw=0.9, color='tab:green', alpha=0.85, label='acc z')
        ax.set_ylabel('robust z-score')
        ax.legend(loc='upper right')
    # Swing windows
    for r in swings.to_dict('records'):
        t0 = (float(r['t_start_ms']) - t_ms[0]) / 1000.0
        t1 = (float(r['t_end_ms']) - t_ms[0]) / 1000.0
        tp = (float(r['t_peak_ms']) - t_ms[0]) / 1000.0
        ax.axvspan(t0, t1, color='orange', alpha=0.12)
        ax.axvline(tp, color='black', lw=0.8, alpha=0.35)
    ax.set_xlabel('time (s)')
    ax.set_title('Swing overlay (gyro+acc z) + detected swing windows')
    ax.grid(True, alpha=0.25)
    # Optional EMG overlay (third signal). Put on right axis if present, else on ax.
    if plot_env and feats is not None and len(
            feats) and 't_center_s' in feats.columns and 'EMG_ENV_mean' in feats.columns:
        tt = pd.to_numeric(feats['t_center_s'], errors='coerce').to_numpy(float)
        yy = pd.to_numeric(feats['EMG_ENV_mean'], errors='coerce').to_numpy(float)
        if two_y:
            ax2.plot(tt, yy, color='tab:blue', lw=0.8, alpha=0.55, ls='--', label='EMG_ENV_mean')
            # refresh legend to include EMG
            h1, l1 = ax.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels()
            ax.legend(h1 + h2, l1 + l2, loc='upper right')
        else:
            ax.plot(tt, yy, color='tab:blue', lw=0.8, alpha=0.55, ls='--', label='EMG_ENV_mean')
            ax.legend(loc='upper right')
    os.makedirs(out_dir, exist_ok=True)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, fname), dpi=150)
    plt.close(fig)


def deep_update(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively update dict dst with src."""
    for k, v in (src or {}).items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            deep_update(dst[k], v)
        else:
            dst[k] = v
    return dst


def load_config(path: str) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f) or {}
    return cfg


def robust_zscore(x: np.ndarray, baseline_mask: np.ndarray, eps: float = 1e-9) -> Tuple[np.ndarray, float, float]:
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


def detect_swings(imu_df: pd.DataFrame, cfg: Dict[str, Any], imu_fs_fallback: float = 200.0) -> pd.DataFrame:
    sd = cfg['swing_detection']
    use_gyro = bool(sd.get('use_gyro', True))

    imu = imu_df.dropna(subset=['ts_ms']).sort_values('ts_ms', kind='mergesort').reset_index(drop=True)
    if len(imu) == 0:
        return pd.DataFrame(columns=["swing_id", "t_start_ms", "t_peak_ms", "t_end_ms", "peak_z", "peak_mag"])

    t_rel_s = core.build_time_axis_from_ts(imu, fs_fallback=float(imu_fs_fallback))
    t0_ms = float(imu['ts_ms'].iloc[0])
    t_ms = t0_ms + 1000.0 * t_rel_s

    if use_gyro:
        mag = np.sqrt(imu['gx'].to_numpy(float) ** 2 + imu['gy'].to_numpy(float) ** 2 + imu['gz'].to_numpy(float) ** 2)
    else:
        mag = np.sqrt(imu['ax'].to_numpy(float) ** 2 + imu['ay'].to_numpy(float) ** 2 + imu['az'].to_numpy(float) ** 2)

    total_s = float(np.nanmax(t_rel_s)) if len(t_rel_s) else float(sd.get('baseline_s', 2.0))
    b_s = min(float(sd.get('baseline_s', 2.0)), max(0.2 * total_s, 0.5))
    z, _, _ = robust_zscore(mag, t_rel_s <= b_s)

    active = z > float(sd.get('z_thr', 5.0))
    min_consec = int(sd.get('min_consec', 3))
    if min_consec > 1:
        run = 0
        flags = np.zeros_like(active, dtype=bool)
        for i, v in enumerate(active):
            run = run + 1 if v else 0
            flags[i] = run >= min_consec
        active = flags

    # Peak per active region
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
        return pd.DataFrame(columns=["swing_id", "t_start_ms", "t_peak_ms", "t_end_ms", "peak_z", "peak_mag"])

    # Enforce min gap
    peaks_sorted = sorted(peaks, key=lambda k: t_ms[k])
    kept = []
    last_t = -1e18
    min_gap_ms = float(sd.get('min_gap_ms', 300.0))
    for k in peaks_sorted:
        if (t_ms[k] - last_t) >= min_gap_ms:
            kept.append(k)
            last_t = t_ms[k]
        else:
            if kept and z[k] > z[kept[-1]]:
                kept[-1] = k
                last_t = t_ms[k]

    pre_ms = float(sd.get('pre_ms', 250.0))
    post_ms = float(sd.get('post_ms', 450.0))

    rows = []
    for si, k in enumerate(kept):
        tp = float(t_ms[k])
        rows.append({
            'swing_id': int(si),
            't_start_ms': tp - pre_ms,
            't_peak_ms': tp,
            't_end_ms': tp + post_ms,
            'peak_z': float(z[k]),
            'peak_mag': float(mag[k]),
        })

    win = pd.DataFrame(rows).sort_values('t_start_ms').reset_index(drop=True)
    # merge overlaps
    merged = []
    cur = win.iloc[0].to_dict()
    for r in win.iloc[1:].to_dict('records'):
        if r['t_start_ms'] <= cur['t_end_ms']:
            cur['t_end_ms'] = max(cur['t_end_ms'], r['t_end_ms'])
            if r['peak_z'] > cur['peak_z']:
                cur.update({'t_peak_ms': r['t_peak_ms'], 'peak_z': r['peak_z'], 'peak_mag': r['peak_mag']})
        else:
            merged.append(cur)
            cur = r
    merged.append(cur)

    out = pd.DataFrame(merged)
    out['swing_id'] = np.arange(len(out), dtype=int)
    return out[['swing_id', 't_start_ms', 't_peak_ms', 't_end_ms', 'peak_z', 'peak_mag']]


def file_time_index(paths: List[str]) -> List[Tuple[str, float, float]]:
    """Return list of (path, min_ts_ms, max_ts_ms) for quick window lookup."""
    idx = []
    for p in paths:
        df = pd.read_csv(p, usecols=['ts_ms'], engine='python')
        ts = pd.to_numeric(df['ts_ms'], errors='coerce')
        idx.append((p, float(ts.min()), float(ts.max())))
    return idx


def read_emg_segment(paths_index: List[Tuple[str, float, float]], t0_ms: float, t1_ms: float) -> np.ndarray:
    """Read EMG raw samples whose ts_ms falls in [t0_ms, t1_ms] across rotated files."""
    segs = []
    for p, mn, mx in paths_index:
        if mx < t0_ms or mn > t1_ms:
            continue
        # chunk read to reduce memory
        for chunk in pd.read_csv(p, usecols=['ts_ms', 'raw'], chunksize=500000, engine='python'):
            chunk['ts_ms'] = pd.to_numeric(chunk['ts_ms'], errors='coerce')
            chunk['raw'] = pd.to_numeric(chunk['raw'], errors='coerce')
            sub = chunk[(chunk['ts_ms'] >= t0_ms) & (chunk['ts_ms'] <= t1_ms) & chunk['raw'].notna()]
            if len(sub):
                segs.append(sub['raw'].to_numpy(dtype=float))
    if not segs:
        return np.array([], dtype=float)
    return np.concatenate(segs)


def per_swing_features(swings: pd.DataFrame, paths_index: List[Tuple[str, float, float]],
                       cfg: Dict[str, Any]) -> pd.DataFrame:
    """Compute per-swing EMG features by reading EMG samples around each swing window."""
    sd = cfg['swing_detection']
    fs = float(cfg['session']['emg_fs_hz'])
    pad = float(sd.get('mdf_pad_ms', 300.0))
    zc_thr = float(cfg['features'].get('zc_thr', 0.01))
    ssc_thr = float(cfg['features'].get('ssc_thr', 0.01))

    rows = []
    for r in swings.to_dict('records'):
        # window for envelope effort (exact)
        t0 = float(r['t_start_ms'])
        t1 = float(r['t_end_ms'])
        raw_exact = read_emg_segment(paths_index, t0, t1)

        # padded window for spectral features (MDF/MNF)
        raw_pad = read_emg_segment(paths_index, t0 - pad, t1 + pad)

        # If too few samples, skip heavy features
        def safe_feats(x: np.ndarray):
            if x.size < 32:
                return dict(mav=np.nan, rms=np.nan, wl=np.nan, zc=np.nan, ssc=np.nan, mnf=np.nan, mdf=np.nan)
            proc = core.preprocess_emg(x, fs)
            mnf, mdf = core.mnf_mdf(proc, fs)
            # time features on proc
            mav = float(np.mean(np.abs(proc)))
            rms = float(np.sqrt(np.mean(proc * proc)))
            wl = float(np.sum(np.abs(np.diff(proc))))
            s = proc - float(np.mean(proc))
            zc = float(np.sum(((s[:-1] * s[1:]) < 0) & (np.abs(s[:-1] - s[1:]) > zc_thr))) if s.size > 2 else np.nan
            a = s[1:-1] - s[:-2]
            b = s[1:-1] - s[2:]
            ssc = float(np.sum((a * b > 0) & (np.abs(a) > ssc_thr) & (np.abs(b) > ssc_thr))) if s.size > 3 else np.nan
            return dict(mav=mav, rms=rms, wl=wl, zc=zc, ssc=ssc, mnf=float(mnf), mdf=float(mdf))

        # envelope-like effort: mean abs on exact window
        if raw_exact.size:
            env_mean = float(np.mean(np.abs(raw_exact)))
            env_peak = float(np.max(np.abs(raw_exact)))
            iemg = float(np.sum(np.abs(raw_exact)) / fs)
        else:
            env_mean = env_peak = iemg = np.nan

        f = safe_feats(raw_pad)

        rows.append({
            'swing_id': int(r['swing_id']),
            't_start_ms': t0,
            't_peak_ms': float(r['t_peak_ms']),
            't_end_ms': t1,
            'imu_peak_z': float(r.get('peak_z', np.nan)),
            'imu_peak_mag': float(r.get('peak_mag', np.nan)),
            'emg_env_mean': env_mean,
            'emg_env_peak': env_peak,
            'emg_iemg': iemg,
            **f,
        })

    return pd.DataFrame(rows)


def select_baseline_swings(swings: pd.DataFrame, session_t0_ms: float, cfg: Dict[str, Any]) -> pd.DataFrame:
    b = cfg['baseline']
    warm_min = float(b.get('warmup_skip_min', 5))
    warm_sw = int(b.get('warmup_skip_swings', 0))
    N = int(b.get('baseline_swings', 20))

    sw = swings.sort_values('t_peak_ms').reset_index(drop=True)
    cutoff = float(session_t0_ms) + warm_min * 60.0 * 1000.0
    sw2 = sw[sw['t_peak_ms'] >= cutoff].reset_index(drop=True)
    if len(sw2) < max(3, N // 2):
        sw2 = sw
    if warm_sw > 0:
        sw2 = sw2.iloc[warm_sw:].reset_index(drop=True)
    return sw2.iloc[:N].reset_index(drop=True)


def baseline_from_features(df: pd.DataFrame) -> Dict[str, float]:
    base = {}
    for k in ['mdf', 'rms', 'mav', 'wl', 'emg_env_mean', 'emg_iemg']:
        if k in df.columns:
            base[k] = float(np.nanmedian(df[k].to_numpy(dtype=float)))
    return base


def apply_deltas(df: pd.DataFrame, base: Dict[str, float], prefix: str = '') -> pd.DataFrame:
    out = df.copy()
    if not base:
        return out
    if 'mdf' in out.columns and 'mdf' in base and base['mdf']:
        out[prefix + 'mdf_drop_pct'] = (base['mdf'] - out['mdf']) / base['mdf'] * 100.0
    if 'rms' in out.columns and 'rms' in base and base['rms']:
        out[prefix + 'rms_increase_pct'] = (out['rms'] - base['rms']) / base['rms'] * 100.0
    return out


def segment_bouts(swings: pd.DataFrame, imu_df: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    """Bout segmentation (Option C) using swing gaps + IMU activity with EMG gating optional.

    For Phase-1, we produce bout boundaries primarily from swing gaps and IMU rest intervals.
    """
    bt = cfg['bout']
    gap_thr = float(bt.get('gap_thr_s', 10))
    gap_long = float(bt.get('gap_thr_long_s', 30))
    rest_dur = float(bt.get('rest_dur_s', 4))
    imu_low = float(bt.get('imu_z_low', 1.2))
    imu_high = float(bt.get('imu_z_high', 2.5))
    min_bout_swings = int(bt.get('min_bout_swings', 3))

    if swings is None or len(swings) == 0:
        return pd.DataFrame(columns=['bout_id', 't_start_ms', 't_end_ms', 'num_swings', 'duration_s'])

    sw = swings.sort_values('t_peak_ms').reset_index(drop=True)

    # Build IMU activity z-score time series
    imu = imu_df.dropna(subset=['ts_ms']).sort_values('ts_ms', kind='mergesort').reset_index(drop=True)
    if len(imu):
        t_rel_s = core.build_time_axis_from_ts(imu, fs_fallback=float(cfg['session'].get('imu_fs_fallback_hz', 200)))
        t0_ms = float(imu['ts_ms'].iloc[0])
        imu_t_ms = t0_ms + 1000.0 * t_rel_s
        mag = np.sqrt(imu['gx'].to_numpy(float) ** 2 + imu['gy'].to_numpy(float) ** 2 + imu['gz'].to_numpy(float) ** 2)
        total_s = float(np.nanmax(t_rel_s)) if len(t_rel_s) else 2.0
        b_s = min(2.0, max(0.2 * total_s, 0.5))
        z, _, _ = robust_zscore(mag, t_rel_s <= b_s)
    else:
        imu_t_ms = np.array([], dtype=float)
        z = np.array([], dtype=float)

    def imu_rest_between(a_ms: float, b_ms: float) -> bool:
        if imu_t_ms.size < 10:
            return False
        m = (imu_t_ms >= a_ms) & (imu_t_ms <= b_ms)
        if m.sum() < 5:
            return False
        # check if z stays low for rest_dur seconds (approx: fraction of samples low)
        # For simplicity, require >80% low
        return float(np.mean(z[m] < imu_low)) > 0.8

    def imu_active_between(a_ms: float, b_ms: float) -> bool:
        if imu_t_ms.size < 10:
            return False
        m = (imu_t_ms >= a_ms) & (imu_t_ms <= b_ms)
        if m.sum() < 5:
            return False
        return float(np.percentile(z[m], 90)) > imu_high

    # Bout boundaries
    boundaries = [0]
    for i in range(len(sw) - 1):
        t_i = float(sw.loc[i, 't_peak_ms'])
        t_j = float(sw.loc[i + 1, 't_peak_ms'])
        dt = (t_j - t_i) / 1000.0
        if dt >= gap_long:
            boundaries.append(i + 1)
            continue
        if dt >= gap_thr:
            # Candidate: confirm with IMU rest (and not contradicted by high IMU)
            if imu_rest_between(t_i, t_j) and (not imu_active_between(t_i, t_j)):
                boundaries.append(i + 1)

    boundaries.append(len(sw))
    boundaries = sorted(set(boundaries))

    # Build bouts
    bouts = []
    bout_id = 0
    for a, b in zip(boundaries[:-1], boundaries[1:]):
        seg = sw.iloc[a:b]
        if len(seg) < min_bout_swings:
            continue
        t0 = float(seg['t_start_ms'].min())
        t1 = float(seg['t_end_ms'].max())
        bouts.append({
            'bout_id': bout_id,
            't_start_ms': t0,
            't_end_ms': t1,
            'duration_s': (t1 - t0) / 1000.0,
            'num_swings': int(len(seg)),
            'swings_per_min': float(len(seg) / max((t1 - t0) / 60000.0, 1e-9)),
        })
        bout_id += 1

    return pd.DataFrame(bouts)


def main():
    ap = argparse.ArgumentParser(description='YAML-driven EMG/IMU analysis (minimal CLI)')
    ap.add_argument('--config', default='config.yaml', help='Path to YAML config (default: config.yaml)')
    ap.add_argument('--emg-imu', default=None, help='Optional override input glob/path (else use session.emg_imu_glob)')
    ap.add_argument('--out-dir', default=None, help='Optional override output directory (else use session.out_dir)')
    args = ap.parse_args()

    cfg = load_config(args.config)

    # Apply minimal CLI overrides
    if args.emg_imu:
        cfg.setdefault('session', {})['emg_imu_glob'] = args.emg_imu
    if args.out_dir:
        cfg.setdefault('session', {})['out_dir'] = args.out_dir

    # Resolve inputs
    pattern = cfg.get('session', {}).get('emg_imu_glob', 'emg_imu_log_*.csv')
    paths = sorted(glob.glob(pattern))
    if not paths:
        paths = [pattern]

    out_dir = cfg.get('session', {}).get('out_dir', 'out')
    os.makedirs(out_dir, exist_ok=True)

    # If plots are enabled, cache loaded DataFrames to avoid re-reading CSVs.
    plots_enabled = bool((cfg.get('plots', {}) or {}).get('enable', False))
    all_dfs = [] if plots_enabled else None

    # Save effective config for reproducibility
    with open(os.path.join(out_dir, 'effective_config.json'), 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)

    # Load IMU rows only (fast)
    imu_parts = []
    session_min_ts = None
    for p in paths:
        df = pd.read_csv(p, engine='python')
        if all_dfs is not None: all_dfs.append(df)
        # coerce numeric
        for c in ['ts_ms', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 'raw']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')
        if session_min_ts is None:
            session_min_ts = float(df['ts_ms'].min())
        else:
            session_min_ts = min(session_min_ts, float(df['ts_ms'].min()))
        imu = df[df[['ax', 'ay', 'az', 'gx', 'gy', 'gz']].notna().any(axis=1)][
            ['ts_ms', 'ax', 'ay', 'az', 'gx', 'gy', 'gz']].copy()
        if len(imu):
            imu_parts.append(imu)

    imu_df = pd.concat(imu_parts, ignore_index=True) if imu_parts else pd.DataFrame(
        columns=['ts_ms', 'ax', 'ay', 'az', 'gx', 'gy', 'gz'])
    imu_df = imu_df.sort_values('ts_ms', kind='mergesort').reset_index(drop=True)

    # Detect swings
    swings = detect_swings(imu_df, cfg, imu_fs_fallback=float(cfg['session'].get('imu_fs_fallback_hz', 200)))
    swings.to_csv(os.path.join(out_dir, 'swing_windows.csv'), index=False)

    mode = cfg.get('features', {}).get('mode', 'both')

    # Build file time index for selective EMG reads
    idx = None
    if mode in ('swing', 'both'):
        # Build file time index for selective EMG reads
        idx = file_time_index(paths)

    swing_feat_df = None
    if mode in ('swing', 'both'):
        swing_feat_df = per_swing_features(swings, idx, cfg)
        # Baseline swing selection
        base_sw = select_baseline_swings(swings, session_t0_ms=float(session_min_ts or swings['t_start_ms'].min()),
                                         cfg=cfg)
        base_feats = swing_feat_df[swing_feat_df['swing_id'].isin(base_sw['swing_id'])]
        base = baseline_from_features(base_feats)
        swing_feat_df = apply_deltas(swing_feat_df, base, prefix='swing_')
        swing_feat_df.to_csv(os.path.join(out_dir, 'swing_features.csv'), index=False)
        with open(os.path.join(out_dir, 'baseline.json'), 'w', encoding='utf-8') as f:
            json.dump({'baseline': base, 'selected_swings': base_sw.to_dict('records')}, f, indent=2)

    # Bout summaries
    if mode in ('bout', 'both'):
        bout_df = segment_bouts(swings, imu_df, cfg)
        bout_df.to_csv(os.path.join(out_dir, 'bout_summary.csv'), index=False)

        # Optional: join in per-bout aggregated swing features if available
        if swing_feat_df is not None and len(bout_df):
            # Assign each swing to bout by time overlap
            bout_rows = []
            for b in bout_df.to_dict('records'):
                m = (swing_feat_df['t_peak_ms'] >= b['t_start_ms']) & (swing_feat_df['t_peak_ms'] <= b['t_end_ms'])
                seg = swing_feat_df[m]
                if len(seg):
                    bout_rows.append({
                        'bout_id': b['bout_id'],
                        'emg_iemg_median': float(np.nanmedian(seg['emg_iemg'])),
                        'mdf_median': float(np.nanmedian(seg['mdf'])),
                        'imu_peak_z_median': float(np.nanmedian(seg['imu_peak_z'])),
                    })
            if bout_rows:
                bout_extra = pd.DataFrame(bout_rows)
                bout_out = bout_df.merge(bout_extra, on='bout_id', how='left')
                bout_out.to_csv(os.path.join(out_dir, 'bout_summary.csv'), index=False)

    # Optional plots + diagnostics (requires plots.enable: true)
    pl = cfg.get('plots', {}) or {}
    if bool(pl.get('enable', False)):
        if all_dfs is not None and len(all_dfs):
            emg_imu_plot = pd.concat(all_dfs, ignore_index=True)
        else:
            emg_imu_plot = pd.concat([pd.read_csv(pp, engine='python') for pp in paths], ignore_index=True)
        for c in ['ts_ms', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 'raw']:
            if c in emg_imu_plot.columns:
                emg_imu_plot[c] = pd.to_numeric(emg_imu_plot[c], errors='coerce')
        win_sec = float(pl.get('win_sec', 1.0))
        step_sec = float(pl.get('step_sec', 0.25))
        res_plot = core.compute(emg_imu_plot, emg_fs_hz=float(cfg['session']['emg_fs_hz']), win_sec=win_sec,
                                step_sec=step_sec)
        core.plot_all(res_plot, emg_fs_hz=float(cfg['session']['emg_fs_hz']), title='EMG/IMU summary',
                      full_duration=bool(pl.get('full_duration', True)),
                      emg_max_points=int(pl.get('emg_max_points', 300000)),
                      save_dir=out_dir, silent=True)
        paged = pl.get('paged', {}) or {}
        if bool(paged.get('enable', False)):
            core.plot_paged(res_plot, emg_fs_hz=float(cfg['session']['emg_fs_hz']),
                            page_sec=float(paged.get('page_sec', 5.0)),
                            page_start_sec=float(paged.get('page_start_sec', 0.0)),
                            page_count=int(paged.get('page_count', 0)),
                            page_step_sec=paged.get('page_step_sec', None),
                            title='EMG/IMU paged', save_dir=out_dir, silent=True)
        if bool(pl.get('do_fatigue', False)):
            core.analyze_fatigue(res_plot.feats, save_dir=out_dir)
        # Diagnostics
        diag = cfg.get('diagnostics', {}) or {}
        corr_cfg = diag.get('emg_imu_correlation', {}) or {}
        if bool(corr_cfg.get('enable', False)):
            save_emg_imu_correlation(res_plot.feats, out_dir, method=str(corr_cfg.get('method', 'pearson')),
                                     fname=str(corr_cfg.get('save_name', 'emg_imu_correlation.json')))
        ov_cfg = diag.get('swing_overlay', {}) or {}
        if bool(ov_cfg.get('enable', False)):
            save_swing_overlay(imu_df, swings, res_plot.feats, cfg, out_dir,
                               fname=str(ov_cfg.get('save_name', 'swing_overlay.png')))
    # Session summary
    session_summary = {
        'num_files': len(paths),
        'num_swings': int(len(swings)),
        'mode': mode,
    }
    if 'bout_df' in locals() and bout_df is not None:
        session_summary.update({
            'num_bouts': int(len(bout_df)),
            'total_active_s': float(np.nansum(bout_df['duration_s'])) if len(bout_df) else 0.0,
        })
    with open(os.path.join(out_dir, 'session_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(session_summary, f, indent=2)

    print(f"[OK] Saved outputs to: {out_dir}")


if __name__ == '__main__':
    main()
