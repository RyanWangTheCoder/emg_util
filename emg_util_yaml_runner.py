#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""an.py

YAML-driven EMG+IMU analysis runner for the NEW btCentral.py capture format.

Input:
  --log-dir <DIR>   directory containing rotated logs:
    emg_log_<SESSIONID>_<OPENID>_<idx>.csv
    imu_log_<SESSIONID>_<OPENID>_<idx>.csv

Behavior:
- Analyze ALL sessions found in the directory (grouped by session_id), in chronological order.
- Output is written to session.out_dir/<session_id>/...

Modes:
- features.mode == "bout" (fast):
    * swing detection + bout summary + session/segment summaries
    * skips per-swing EMG features and skips plots/correlation
- features.mode == "both" (default):
    * swing windows + per-swing EMG features + bout summary
    * optional plots and feature correlation (if enabled)

Feature correlation (EMG vs IMU):
- If plots.enable == true AND diagnostics.emg_imu_correlation.enable == true,
  compute windowed features (via emg_util.compute) and save emg_imu_correlation.json.

"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import yaml

import emg_util as core
import capture_loader as loader
import capture_health as health


def log(msg: str) -> None:
    import time
    ts = time.strftime('%H:%M:%S')
    print(f'[{ts}] {msg}', flush=True)


def load_config(path: str) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


# robust_zscore() removed — use core.robust_zscore() (defined in emg_util.py)




# ----------------------------
# EMG health + swing filtering (additive)
# ----------------------------

def _health_cfg(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return (cfg.get('health', {}) or {})


def _overlaps_bad_emg(t0_ms: float, t1_ms: float, bad_emg_ms: List[Tuple[float, float]]) -> bool:
    return health.intervals_overlap(float(t0_ms), float(t1_ms), bad_emg_ms)


def _filter_swings_by_bad_emg(swings: pd.DataFrame, bad_emg_ms: List[Tuple[float, float]]) -> pd.DataFrame:
    if swings is None or len(swings) == 0 or not bad_emg_ms:
        return swings
    keep = []
    for a0, a1 in zip(swings['t_start_ms'].to_numpy(float), swings['t_end_ms'].to_numpy(float)):
        keep.append(not _overlaps_bad_emg(a0, a1, bad_emg_ms))
    return swings.loc[np.array(keep, dtype=bool)].reset_index(drop=True)
# ----------------------------
# IMU activity gating for WORK PERIODS (hybrid gyro+acc intensity)
# ----------------------------

def compute_gyro_mag(df: pd.DataFrame) -> np.ndarray:
    """Compute gyro magnitude sqrt(gx^2 + gy^2 + gz^2)."""
    return np.sqrt(df['gx'].to_numpy(float)**2 + df['gy'].to_numpy(float)**2 + df['gz'].to_numpy(float)**2)


def compute_acc_mag(df: pd.DataFrame) -> np.ndarray:
    """Compute accel magnitude sqrt(ax^2 + ay^2 + az^2)."""
    return np.sqrt(df['ax'].to_numpy(float)**2 + df['ay'].to_numpy(float)**2 + df['az'].to_numpy(float)**2)


def _robust_z(x: np.ndarray, ref_mask: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    """Robust z-score using median and MAD on reference subset."""
    x = np.asarray(x, dtype=float)
    ref_mask = np.asarray(ref_mask, dtype=bool)
    ref = x[ref_mask]
    ref = ref[np.isfinite(ref)]
    if ref.size < 50:
        ref = x[np.isfinite(x)]
    if ref.size == 0:
        return np.zeros_like(x, dtype=float)
    med = float(np.median(ref))
    mad = float(np.median(np.abs(ref - med)))
    scale = 1.4826 * mad
    if (not np.isfinite(scale)) or scale < eps:
        scale = float(np.nanstd(ref))
    if (not np.isfinite(scale)) or scale < eps:
        scale = 1.0
    return (x - med) / (scale + eps)


def _ema_smooth(x: np.ndarray, t_ms: np.ndarray, tau_ms: float) -> np.ndarray:
    """Exponential smoothing with time-aware alpha based on tau_ms."""
    x = np.asarray(x, dtype=float)
    t_ms = np.asarray(t_ms, dtype=float)
    if x.size == 0:
        return x
    if tau_ms <= 0:
        return x.copy()
    y = np.empty_like(x, dtype=float)
    y[0] = x[0]
    for i in range(1, len(x)):
        dt = float(t_ms[i] - t_ms[i-1])
        if not np.isfinite(dt) or dt <= 0:
            dt = 0.0
        alpha = dt / (tau_ms + dt) if (tau_ms + dt) > 0 else 1.0
        y[i] = y[i-1] + alpha * (x[i] - y[i-1])
    return y


def compute_hybrid_intensity(imu: pd.DataFrame, cfg: Dict[str, Any]) -> Dict[str, np.ndarray]:
    """Compute hybrid intensity (gyro + dynamic-acc), plus smoothed intensity.

    Returns dict with keys: t_ms, gyro_mag, acc_dyn, intensity, intensity_smooth.
    """
    ag = (cfg.get('activity_gating', {}) or {})

    t_ms = imu['ts_ms'].to_numpy(float)
    gyro_mag = compute_gyro_mag(imu)

    # dynamic accel: abs(|a|-1g) by default (assuming ax/ay/az in g)
    acc_dyn_method = str(ag.get('acc_dyn_method', 'abs_mag_minus_1g'))
    if all(c in imu.columns for c in ['ax','ay','az']):
        acc_mag = compute_acc_mag(imu)
    else:
        acc_mag = np.zeros_like(gyro_mag)

    if acc_dyn_method == 'abs_mag_minus_1g':
        acc_dyn = np.abs(acc_mag - 1.0)
    else:
        acc_dyn = np.abs(acc_mag - 1.0)

    # Reference mask for robust scaling based on skip_min
    skip_min = ag.get('skip_min', 0)
    if skip_min is None:
        skip_min = (cfg.get('baseline', {}) or {}).get('warmup_skip_min', 0)
    skip_ms = float(skip_min) * 60.0 * 1000.0
    t0 = float(t_ms[0])
    ref_mask = t_ms >= (t0 + skip_ms)
    if not np.any(ref_mask):
        ref_mask = np.ones_like(t_ms, dtype=bool)

    zg = _robust_z(gyro_mag, ref_mask)
    za = _robust_z(acc_dyn, ref_mask)

    w_g = float(ag.get('w_gyro', 0.8))
    w_a = float(ag.get('w_acc', 0.2))
    intensity = w_g * zg + w_a * za

    smooth_ms = float(ag.get('smooth_ms', 250.0))
    intensity_smooth = _ema_smooth(intensity, t_ms, tau_ms=smooth_ms)

    return {
        't_ms': t_ms,
        'gyro_mag': gyro_mag,
        'acc_dyn': acc_dyn,
        'intensity': intensity,
        'intensity_smooth': intensity_smooth,
        'ref_mask': ref_mask,
    }


def activity_segments_from_imu(imu_df: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    """Create ACTIVE segments representing WORK PERIODS.

    Uses smoothed hybrid intensity and percentile hysteresis.
    """
    ag = (cfg.get('activity_gating', {}) or {})
    if not bool(ag.get('enable', True)):
        return pd.DataFrame(columns=['t_start_ms','t_end_ms','duration_s'])

    if imu_df is None or len(imu_df) == 0:
        return pd.DataFrame(columns=['t_start_ms','t_end_ms','duration_s'])

    need_cols = ['ts_ms','gx','gy','gz']
    imu = imu_df.dropna(subset=need_cols).sort_values('ts_ms', kind='mergesort').reset_index(drop=True)
    if len(imu) == 0:
        return pd.DataFrame(columns=['t_start_ms','t_end_ms','duration_s'])

    sig = compute_hybrid_intensity(imu, cfg)
    t_ms = sig['t_ms']
    x = sig['intensity_smooth']
    ref_mask = sig['ref_mask']

    p_high = float(ag.get('p_high', 90))
    p_low  = float(ag.get('p_low', 75))
    p_high = float(np.clip(p_high, 50.0, 99.99))
    p_low  = float(np.clip(p_low,  10.0, p_high - 1e-6))

    ref = x[ref_mask]
    ref = ref[np.isfinite(ref)]
    if ref.size < 50:
        ref = x[np.isfinite(x)]
    if ref.size == 0:
        return pd.DataFrame(columns=['t_start_ms','t_end_ms','duration_s'])

    thr_high = float(np.nanpercentile(ref, p_high))
    thr_low  = float(np.nanpercentile(ref, p_low))

    # Hysteresis
    active = np.zeros(len(x), dtype=bool)
    state = False
    for i, v in enumerate(x):
        if not np.isfinite(v):
            active[i] = state
            continue
        if (not state) and v >= thr_high:
            state = True
        elif state and v <= thr_low:
            state = False
        active[i] = state

    # boolean -> segments
    segs = []
    in_seg = False
    s0 = 0.0
    for i, a in enumerate(active):
        if a and not in_seg:
            in_seg = True
            s0 = float(t_ms[i])
        if in_seg and (not a):
            segs.append((s0, float(t_ms[i-1])))
            in_seg = False
    if in_seg:
        segs.append((float(s0), float(t_ms[-1])))

    min_active_ms = float(ag.get('min_active_ms', 1000.0))
    merge_gap_ms  = float(ag.get('merge_gap_ms', 2000.0))
    expand_ms     = float(ag.get('expand_ms', 400.0))

    segs = [(a,b) for (a,b) in segs if (b-a) >= min_active_ms]
    segs.sort(key=lambda ab: ab[0])

    t_min = float(t_ms[0]); t_max = float(t_ms[-1])
    segs = [(max(t_min, a-expand_ms), min(t_max, b+expand_ms)) for (a,b) in segs]

    merged = []
    for a,b in segs:
        if not merged:
            merged.append([a,b])
            continue
        la,lb = merged[-1]
        if a - lb <= merge_gap_ms:
            merged[-1][1] = max(lb, b)
        else:
            merged.append([a,b])

    out = pd.DataFrame([{'t_start_ms':a, 't_end_ms':b, 'duration_s':(b-a)/1000.0} for a,b in merged])
    out.attrs['thr_high'] = thr_high
    out.attrs['thr_low'] = thr_low
    out.attrs['p_high'] = p_high
    out.attrs['p_low'] = p_low
    out.attrs['w_gyro'] = float(ag.get('w_gyro', 0.8))
    out.attrs['w_acc'] = float(ag.get('w_acc', 0.2))
    out.attrs['smooth_ms'] = float(ag.get('smooth_ms', 250.0))
    return out


def swing_in_active_mask(swings: pd.DataFrame, active_segs: pd.DataFrame) -> np.ndarray:
    """Return boolean mask for swings whose t_peak_ms is within any active segment."""
    if swings is None or len(swings) == 0 or active_segs is None or len(active_segs) == 0:
        return np.zeros(0, dtype=bool) if swings is None else np.zeros(len(swings), dtype=bool)
    t = swings['t_peak_ms'].to_numpy(float)
    starts = active_segs['t_start_ms'].to_numpy(float)
    ends = active_segs['t_end_ms'].to_numpy(float)
    order = np.argsort(starts)
    starts = starts[order]; ends = ends[order]
    idx = np.searchsorted(starts, t, side='right') - 1
    valid = idx >= 0
    idx2 = np.clip(idx, 0, len(starts)-1)
    return valid & (t >= starts[idx2]) & (t <= ends[idx2])


def plot_imu_activity_overlay(imu_df: pd.DataFrame, active_segs: pd.DataFrame, swings: pd.DataFrame, out_dir: str, cfg: Dict[str, Any]) -> None:
    """Save IMU activity overlay plot (smoothed intensity + active spans + swing peaks)."""
    diag = cfg.get('diagnostics', {}) or {}
    acfg = diag.get('activity_overlay', {}) or {}
    if not bool(acfg.get('enable', True)):
        return
    if imu_df is None or len(imu_df) == 0:
        return

    import matplotlib.pyplot as plt

    need_cols = ['ts_ms','gx','gy','gz']
    imu = imu_df.dropna(subset=need_cols).sort_values('ts_ms', kind='mergesort').reset_index(drop=True)
    if len(imu) == 0:
        return

    sig = compute_hybrid_intensity(imu, cfg)
    t0 = float(sig['t_ms'][0])
    t_s = (sig['t_ms'] - t0) / 1000.0

    plot_signal = str(acfg.get('plot_signal', 'intensity'))
    if plot_signal == 'gyro_mag':
        y = sig['gyro_mag']
        ylab = 'gyro magnitude'
    else:
        y = sig['intensity_smooth']
        ylab = 'hybrid intensity (smoothed)'

    fig, ax = plt.subplots(1,1, figsize=(12,4))
    ax.plot(t_s, y, lw=0.7, label=plot_signal)

    if active_segs is not None and len(active_segs):
        for a,b in zip(active_segs['t_start_ms'].to_numpy(float), active_segs['t_end_ms'].to_numpy(float)):
            ax.axvspan((a-t0)/1000.0, (b-t0)/1000.0, color='orange', alpha=0.18)

    if swings is not None and len(swings) and bool(acfg.get('plot_swings', True)) and 't_peak_ms' in swings.columns:
        sp = (swings['t_peak_ms'].to_numpy(float) - t0)/1000.0
        ax.vlines(sp, ymin=float(np.nanmin(y)), ymax=float(np.nanmax(y)), color='r', alpha=0.25, lw=0.8, label='swing peaks')

    try:
        th = active_segs.attrs.get('thr_high', None)
        tl = active_segs.attrs.get('thr_low', None)
        if th is not None:
            ax.axhline(float(th), color='k', ls='--', lw=1, alpha=0.5, label='enter thr')
        if tl is not None:
            ax.axhline(float(tl), color='k', ls=':', lw=1, alpha=0.5, label='exit thr')
    except Exception:
        pass

    ax.set_xlabel('time (s)')
    ax.set_ylabel(ylab)
    ax.set_title('IMU work-period activity gating overlay')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=8)

    os.makedirs(out_dir, exist_ok=True)
    fname = str(acfg.get('save_name', 'imu_activity_overlay.png'))
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, fname), dpi=150)
    plt.close(fig)


def segment_bouts_from_active(active_segs: pd.DataFrame, swings: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    """Create bout summary using ACTIVE segments as primary structure."""
    bt = cfg.get('bout', {}) or {}
    gap_thr_s = float(bt.get('gap_thr_s', 10))
    gap_long_s = float(bt.get('gap_thr_long_s', 30))
    min_bout_swings = int(bt.get('min_bout_swings', 3))

    if active_segs is None or len(active_segs) == 0:
        return pd.DataFrame(columns=['bout_id','t_start_ms','t_end_ms','duration_s','num_swings','swings_per_min'])

    segs = active_segs.sort_values('t_start_ms').reset_index(drop=True)
    merged = []
    cur_a = float(segs.loc[0,'t_start_ms'])
    cur_b = float(segs.loc[0,'t_end_ms'])
    for i in range(1, len(segs)):
        a = float(segs.loc[i,'t_start_ms']); b = float(segs.loc[i,'t_end_ms'])
        gap_s = (a - cur_b)/1000.0
        if gap_s >= gap_long_s or gap_s >= gap_thr_s:
            merged.append((cur_a, cur_b))
            cur_a, cur_b = a, b
        else:
            cur_b = max(cur_b, b)
    merged.append((cur_a, cur_b))

    sw = swings.sort_values('t_peak_ms').reset_index(drop=True) if swings is not None and len(swings) else pd.DataFrame(columns=['t_peak_ms'])
    tpeaks = sw['t_peak_ms'].to_numpy(float) if 't_peak_ms' in sw.columns and len(sw) else np.array([], dtype=float)

    bouts = []
    bid = 0
    for a,b in merged:
        num = int(np.sum((tpeaks >= a) & (tpeaks <= b))) if tpeaks.size else 0
        if num < min_bout_swings:
            continue
        dur_s = (b-a)/1000.0
        bouts.append({'bout_id': bid, 't_start_ms': a, 't_end_ms': b, 'duration_s': dur_s,
                      'num_swings': num, 'swings_per_min': float(num/max(dur_s/60.0,1e-9))})
        bid += 1
    return pd.DataFrame(bouts)

def detect_swings_from_imu(imu_df: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    """Thin wrapper: extracts config params and delegates to core.detect_swing_windows_from_imu().

    Data from load_session_stitched() is already in physical units (dps / g),
    so already_in_dps=True skips the FSR LSB->dps conversion in the core function.
    The core function also applies the window-merge step (merges overlapping
    [t_start, t_end] windows) which was absent from the previous local implementation.
    """
    sd = cfg.get("swing_detection", {})
    return core.detect_swing_windows_from_imu(
        imu_df,
        thr_gyro_dps   = float(sd.get("thr_gyro_dps", 300.0)),
        thr_acc_g      = float(sd.get("thr_acc_g", 0.0)),
        min_gap_ms     = float(sd.get("min_gap_ms", 2000.0)),
        pre_ms         = float(sd.get("pre_ms", 250.0)),
        post_ms        = float(sd.get("post_ms", 450.0)),
        use_gyro       = bool(sd.get("use_gyro", True)),
        already_in_dps = True,  # load_session_stitched() returns physical units
    )



def file_time_index(paths: List[str], time_col: str = 'dev_us') -> List[Tuple[str, int, int]]:
    idx: List[Tuple[str, int, int]] = []
    for p in paths:
        df = pd.read_csv(p, usecols=[time_col], engine='python')
        t = pd.to_numeric(df[time_col], errors='coerce').dropna().astype(np.int64)
        idx.append((p, int(t.min()) if len(t) else 0, int(t.max()) if len(t) else 0))
    return idx


def read_emg_segment(paths_index: List[Tuple[str, int, int]], t0_us: int, t1_us: int,
                     chunksize: int = 500000) -> np.ndarray:
    segs = []
    for p, mn, mx in paths_index:
        if mx < t0_us or mn > t1_us:
            continue
        for chunk in pd.read_csv(p, usecols=['dev_us', 'raw'], chunksize=chunksize, engine='python'):
            chunk['dev_us'] = pd.to_numeric(chunk['dev_us'], errors='coerce')
            chunk['raw'] = pd.to_numeric(chunk['raw'], errors='coerce')
            sub = chunk[(chunk['dev_us'] >= t0_us) & (chunk['dev_us'] <= t1_us) & chunk['raw'].notna()]
            if len(sub):
                segs.append(sub['raw'].to_numpy(dtype=float))
    return np.concatenate(segs) if segs else np.array([], dtype=float)


def per_swing_emg_features(swings: pd.DataFrame, emg_idx: List[Tuple[str, int, int]], cfg: Dict[str, Any]) -> pd.DataFrame:
    fs = float(cfg.get('session', {}).get('emg_fs_hz', 2000.0))
    pad_ms = float(cfg.get('swing_detection', {}).get('mdf_pad_ms', 300.0))
    zc_thr = float(cfg.get('features', {}).get('zc_thr', 0.01))
    ssc_thr = float(cfg.get('features', {}).get('ssc_thr', 0.01))

    rows = []
    n = int(len(swings))
    log(f'Computing per-swing EMG features for {n} swings...')
    for ii, r in enumerate(swings.to_dict('records'), start=1):
        # Progress every 10 swings or at milestones
        if ii == 1 or ii % 10 == 0 or ii == n or ii in [25, 50, 100, 200, 300, 400, 500]:
            log(f'  Processing swing {ii}/{n} ({100*ii//n}%)')

        t0_ms = float(r['t_start_ms']); t1_ms = float(r['t_end_ms'])
        raw_exact = read_emg_segment(emg_idx, int(round(t0_ms * 1000.0)), int(round(t1_ms * 1000.0)))
        raw_pad = read_emg_segment(emg_idx,
                                   int(round((t0_ms - pad_ms) * 1000.0)),
                                   int(round((t1_ms + pad_ms) * 1000.0)))

        # effort proxies on exact
        if raw_exact.size:
            env_mean = float(np.mean(np.abs(raw_exact)))
            env_peak = float(np.max(np.abs(raw_exact)))
            iemg = float(np.sum(np.abs(raw_exact)) / fs)
        else:
            env_mean = env_peak = iemg = np.nan

        # spectral/time features on padded
        if raw_pad.size >= 32:
            proc = core.preprocess_emg(raw_pad, fs)
            mnf, mdf = core.mnf_mdf(proc, fs)
            mav = core.feat_mav(proc)
            rms = core.feat_rms(proc)
            wl = core.feat_wl(proc)
            zc = core.feat_zc(proc, thr=zc_thr)
            ssc = core.feat_ssc(proc, thr=ssc_thr)
        else:
            mnf = mdf = mav = rms = wl = zc = ssc = np.nan

        rows.append({
            'swing_id': int(r['swing_id']),
            't_start_ms': t0_ms,
            't_peak_ms': float(r['t_peak_ms']),
            't_end_ms': t1_ms,
            'imu_peak_z': float(r.get('peak_z', np.nan)),
            'imu_peak_mag': float(r.get('peak_mag', np.nan)),
            'emg_env_mean': env_mean,
            'emg_env_peak': env_peak,
            'emg_iemg': iemg,
            'mav': mav,
            'rms': rms,
            'wl': wl,
            'zc': zc,
            'ssc': ssc,
            'mnf': float(mnf) if mnf is not None else np.nan,
            'mdf': float(mdf) if mdf is not None else np.nan,
        })

    return pd.DataFrame(rows)


def select_baseline_swings(swings: pd.DataFrame, session_t0_ms: float, cfg: Dict[str, Any]) -> pd.DataFrame:
    """Wrapper: extracts params from cfg and delegates to core.select_baseline_swings()."""
    b = cfg.get('baseline', {})
    warm_sw = int(b.get('warmup_skip_swings', 0))
    return core.select_baseline_swings(
        swings, session_t0_ms,
        warmup_skip_min=float(b.get('warmup_skip_min', 5)),
        warmup_skip_swings=warm_sw if warm_sw > 0 else None,
        baseline_swings=int(b.get('baseline_swings', 20)),
    )


def baseline_from_features(df: pd.DataFrame) -> Dict[str, float]:
    """Wrapper: delegates to core.compute_baseline_from_swing_features()."""
    return core.compute_baseline_from_swing_features(df)


def apply_deltas(df: pd.DataFrame, base: Dict[str, float], prefix: str = '') -> pd.DataFrame:
    """Wrapper: delegates to core.apply_baseline_deltas()."""
    return core.apply_baseline_deltas(df, base, prefix=prefix)


def segment_bouts(swings: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    bt = cfg.get('bout', {})
    gap_thr = float(bt.get('gap_thr_s', 10))
    gap_long = float(bt.get('gap_thr_long_s', 30))
    min_bout_swings = int(bt.get('min_bout_swings', 3))

    if swings is None or len(swings) == 0:
        return pd.DataFrame(columns=['bout_id', 't_start_ms', 't_end_ms', 'duration_s', 'num_swings', 'swings_per_min'])

    sw = swings.sort_values('t_peak_ms').reset_index(drop=True)
    boundaries = [0]
    for i in range(len(sw) - 1):
        t_i = float(sw.loc[i, 't_peak_ms'])
        t_j = float(sw.loc[i + 1, 't_peak_ms'])
        dt = (t_j - t_i) / 1000.0
        if dt >= gap_long or dt >= gap_thr:
            boundaries.append(i + 1)
    boundaries.append(len(sw))
    boundaries = sorted(set(boundaries))

    bouts = []
    bid = 0
    for a, b in zip(boundaries[:-1], boundaries[1:]):
        seg = sw.iloc[a:b]
        if len(seg) < min_bout_swings:
            continue
        t0 = float(seg['t_start_ms'].min())
        t1 = float(seg['t_end_ms'].max())
        dur_s = (t1 - t0) / 1000.0
        bouts.append({
            'bout_id': int(bid),
            't_start_ms': t0,
            't_end_ms': t1,
            'duration_s': dur_s,
            'num_swings': int(len(seg)),
            'swings_per_min': float(len(seg) / max(dur_s / 60.0, 1e-9)),
        })
        bid += 1

    return pd.DataFrame(bouts)


def save_emg_imu_correlation(feats: pd.DataFrame, out_dir: str, method: str = 'pearson', fname: str = 'emg_imu_correlation.json') -> Dict[str, Any]:
    if feats is None or len(feats) == 0:
        return {}
    cols = ['EMG_RMS', 'EMG_ENV_mean', 'EMG_MNF_Hz', 'EMG_MDF_Hz', 'IMU_acc_rms', 'IMU_gyro_rms']
    cols = [c for c in cols if c in feats.columns]
    if len(cols) < 2:
        return {}
    df = feats[cols].apply(pd.to_numeric, errors='coerce')
    corr = df.corr(method=method).to_dict()
    out = {'method': method, 'n_rows': int(len(df)), 'columns': cols, 'correlation': corr}
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, fname), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    return out


# ---------------------------------------------------------
# NEW: Reusable Analysis Function (Decoupled from CLI)
# ---------------------------------------------------------
def analyze_single_session(session_id: str, files: Any, cfg: Dict[str, Any], out_root: str, session_idx: int = None, total_sessions: int = None) -> str:
    """
    Process a single session. Can be called by CLI main() or by External Notebook.
    Returns the path to the output directory.
    """
    # Create session output directory
    out_dir = os.path.join(out_root, session_id)
    os.makedirs(out_dir, exist_ok=True)

    if session_idx is not None and total_sessions is not None:
        log(f'=== [{session_idx}/{total_sessions}] Processing session {session_id} ===')
    else:
        log(f'=== Processing session {session_id} ===')

    log(f'EMG files: {len(files.emg_paths)} | IMU files: {len(files.imu_paths)}')
    
    # --- Load Session Data & Summary ---
    sdata = loader.summarize_session(files)
    pd.DataFrame([s.__dict__ for s in sdata.emg_segments]).to_csv(os.path.join(out_dir, 'segment_summary_emg.csv'), index=False)
    pd.DataFrame([s.__dict__ for s in sdata.imu_segments]).to_csv(os.path.join(out_dir, 'segment_summary_imu.csv'), index=False)

    sess_cfg = cfg.get('session', {})

    # --- IMU Loading & Activity Gating ---
    # Use load_session_stitched so abs_us-based ts_ms is the canonical time axis.
    # This correctly handles BLE dropouts and ESP32 resets across multiple
    # connections: within each connection dev_us gives accurate physical time;
    # between connections host_rx_ms gap gives the correct inter-connection offset.
    _, imu_df, _, _ = loader.load_session_stitched(
        {session_id: files},
        use_physical_units=bool(sess_cfg.get('use_physical_units', True)),
        acc_fsr_default_g=float(sess_cfg.get('acc_fsr_default_g', 4)),
        gyro_fsr_default_dps=float(sess_cfg.get('gyro_fsr_default_dps', 1000))
    )
    
    active_segs = activity_segments_from_imu(imu_df, cfg)
    active_segs.to_csv(os.path.join(out_dir, 'active_segments.csv'), index=False)

    # --- Swing Detection ---
    swings = detect_swings_from_imu(imu_df, cfg)
    
    in_active = swing_in_active_mask(swings, active_segs)
    if len(swings):
        swings = swings.copy()
        swings['in_active'] = in_active.astype(int)

    ag_cfg = (cfg.get('activity_gating', {}) or {})
    if bool(ag_cfg.get('filter_swings', False)) and len(swings):
        swings = swings.loc[swings['in_active'].astype(bool)].reset_index(drop=True)

    swings.to_csv(os.path.join(out_dir, 'swing_windows.csv'), index=False)
    
    # Diagnostics
    plot_imu_activity_overlay(imu_df, active_segs, swings, out_dir, cfg)
    log(f'Detected swings: {len(swings)}')


    # --- EMG health (sporadic disconnect/contact) and optional swing filtering ---
    # EMG is more fragile than IMU due to cabling/electrodes. When IMU is good, we can
    # keep the session and simply skip swing windows that overlap BAD EMG intervals.
    hcfg = _health_cfg(cfg)
    bad_emg_ms: List[Tuple[float, float]] = []
    try:
        if bool(hcfg.get('enable', True)) and files.emg_paths:
            bad_us = health.emg_bad_intervals_us(files.emg_paths, cfg)
            bad_emg_ms = [(a/1000.0, b/1000.0) for (a,b) in bad_us]
            # Save EMG bad intervals for debugging
            if bad_us:
                pd.DataFrame([
                    {'start_dev_us': a, 'end_dev_us': b, 'duration_s': (b - a) / 1e6}
                    for (a, b) in bad_us
                ]).to_csv(os.path.join(out_dir, 'emg_bad_intervals.csv'), index=False)
    except Exception as e:
        log(f'[WARN] EMG bad-interval detection failed: {e}')

    # Optional knob: filter swings that overlap BAD EMG intervals
    if bad_emg_ms and bool(hcfg.get('filter_swings_by_emg_bad', False)) and len(swings):
        swings_before = len(swings)
        swings = _filter_swings_by_bad_emg(swings, bad_emg_ms)
        if len(swings) != swings_before:
            # Preserve an explicit record of what was used
            swings.to_csv(os.path.join(out_dir, 'swing_windows_emg_filtered.csv'), index=False)
            log(f'[EMG] Filtered swings by BAD EMG intervals: {swings_before} -> {len(swings)}')

    mode = (cfg.get('features', {}) or {}).get('mode', 'both')

    # --- Early Exit if No Swings ---
    if len(swings) == 0:
        bout_df = segment_bouts_from_active(active_segs, swings, cfg)
        bout_df.to_csv(os.path.join(out_dir, 'bout_summary.csv'), index=False)
        # Save minimal summary
        with open(os.path.join(out_dir, 'session_summary.json'), 'w', encoding='utf-8') as f:
            json.dump({**sdata.session_summary, 'num_swings': 0, 'num_bouts': int(len(bout_df)), 'num_active_segments': int(len(active_segs)) if active_segs is not None else 0, 'active_total_s': float(active_segs['duration_s'].sum()) if active_segs is not None and len(active_segs) else 0.0, 'mode': mode}, f, indent=2)
        log(f'Finished session {session_id} (no swings). Outputs -> {out_dir}')
        return out_dir

    # --- Fast Mode (Bout Only) ---
    if mode == 'bout':
        bout_df = segment_bouts_from_active(active_segs, swings, cfg)
        bout_df.to_csv(os.path.join(out_dir, 'bout_summary.csv'), index=False)
        with open(os.path.join(out_dir, 'session_summary.json'), 'w', encoding='utf-8') as f:
            json.dump({**sdata.session_summary, 'num_swings': int(len(swings)), 'num_bouts': int(len(bout_df)), 'mode': mode}, f, indent=2)
        log(f'Finished session {session_id} (fast). Outputs -> {out_dir}')
        return out_dir

    # --- Full Mode: EMG Processing ---
    # 1. Per-Swing Features
    emg_idx = file_time_index(files.emg_paths, time_col='dev_us')
    swing_feat_df = per_swing_emg_features(swings, emg_idx, cfg)
    
    # 2. Baseline
    session_t0_ms = float(sdata.session_summary.get('session_start_dev_us', 0) / 1000.0)
    base_sw = select_baseline_swings(swings, session_t0_ms=session_t0_ms, cfg=cfg)
    base_feats = swing_feat_df[swing_feat_df['swing_id'].isin(base_sw['swing_id'])]
    base = baseline_from_features(base_feats)
    swing_feat_df = apply_deltas(swing_feat_df, base, prefix='swing_')
    
    swing_feat_df.to_csv(os.path.join(out_dir, 'swing_features.csv'), index=False)
    with open(os.path.join(out_dir, 'baseline.json'), 'w', encoding='utf-8') as f:
        json.dump({'baseline': base, 'selected_swings': base_sw.to_dict('records')}, f, indent=2)

    # 3. Bouts
    bout_df = segment_bouts_from_active(active_segs, swings, cfg)
    bout_df.to_csv(os.path.join(out_dir, 'bout_summary.csv'), index=False)

    # 4. Plots & Correlation (Windowed)
    pl = cfg.get('plots', {}) or {}
    if bool(pl.get('enable', False)):
        emg_df = loader.load_emg_concat(files.emg_paths, usecols=['dev_us', 'env', 'raw', 'ref'])
        emg_imu_df = loader.make_interleaved_df(emg_df, imu_df)
        res = core.compute(emg_imu_df,
                           emg_fs_hz=float(sess_cfg.get('emg_fs_hz', 2000)),
                           win_sec=float(pl.get('win_sec', 1.0)),
                           step_sec=float(pl.get('step_sec', 0.25)))

        corr_cfg = (cfg.get('diagnostics', {}) or {}).get('emg_imu_correlation', {})
        if bool(corr_cfg.get('enable', False)):
            save_emg_imu_correlation(res.feats, out_dir,
                                     method=str(corr_cfg.get('method', 'pearson')),
                                     fname=str(corr_cfg.get('save_name', 'emg_imu_correlation.json')))
            log('Saved emg_imu_correlation.json')

        core.plot_all(res,
                      emg_fs_hz=float(sess_cfg.get('emg_fs_hz', 2000)),
                      title=f'EMG/IMU summary session={session_id}',
                      full_duration=bool(pl.get('full_duration', True)),
                      emg_max_points=int(pl.get('emg_max_points', 300000)),
                      save_dir=out_dir,
                      silent=True)
        
        if bool(pl.get('do_fatigue', False)):
            warmup_skip = float(cfg.get('baseline', {}).get('warmup_skip_min', 10.0))
            core.analyze_fatigue(res.feats, save_dir=out_dir, warmup_skip_min=warmup_skip)

    # 5. Final Session Summary
    with open(os.path.join(out_dir, 'session_summary.json'), 'w', encoding='utf-8') as f:
        json.dump({**sdata.session_summary, 'num_swings': int(len(swings)), 'num_bouts': int(len(bout_df)), 'mode': mode}, f, indent=2)

    log(f'Finished session {session_id}. Outputs -> {out_dir}')
    return out_dir


# ---------------------------------------------------------
# NEW: Per-swing EMG features from stitched in-memory DataFrame
# Unlike per_swing_emg_features() which reads from CSV files by dev_us,
# this version uses the stitched EMG DataFrame indexed by abs_us.
# ---------------------------------------------------------

def per_swing_emg_medium_stitched(
    swings: pd.DataFrame,
    emg_df: pd.DataFrame,
    cfg: Dict[str, Any],
) -> pd.DataFrame:
    """Fast per-swing EMG features: envelope + MDF + RMS only.

    Faster than per_swing_emg_features_stitched() because it skips
    wl, zc, ssc, mnf, mav. Computes only the two most useful fatigue
    indicators (MDF ↓ = fatigue, RMS ↑ = effort) plus envelope proxies.

    Suitable for 'medium' mode where speed matters but some EMG insight
    is still needed.
    """
    fs = float(cfg.get('session', {}).get('emg_fs_hz', 2000.0))
    pad_ms = float(cfg.get('swing_detection', {}).get('mdf_pad_ms', 300.0))

    emg_sorted = emg_df.dropna(subset=['raw']).sort_values('abs_us').reset_index(drop=True)
    abs_us_arr = emg_sorted['abs_us'].to_numpy(dtype=np.int64)
    raw_arr = emg_sorted['raw'].to_numpy(dtype=float)

    rows = []
    n = int(len(swings))
    log(f'Computing per-swing EMG envelope+MDF for {n} swings (medium mode)...')

    for ii, r in enumerate(swings.to_dict('records'), start=1):
        if ii == 1 or ii % 50 == 0 or ii == n:
            log(f'  Swing {ii}/{n} ({100 * ii // n}%)')

        t0_ms = float(r['t_start_ms'])
        t1_ms = float(r['t_end_ms'])
        t0_us = int(t0_ms * 1000)
        t1_us = int(t1_ms * 1000)
        t0p_us = int((t0_ms - pad_ms) * 1000)
        t1p_us = int((t1_ms + pad_ms) * 1000)

        i0 = int(np.searchsorted(abs_us_arr, t0_us, side='left'))
        i1 = int(np.searchsorted(abs_us_arr, t1_us, side='right'))
        raw_exact = raw_arr[i0:i1]

        j0 = int(np.searchsorted(abs_us_arr, t0p_us, side='left'))
        j1 = int(np.searchsorted(abs_us_arr, t1p_us, side='right'))
        raw_pad = raw_arr[j0:j1]

        # Envelope features (no FFT, no preprocessing)
        if raw_exact.size:
            env_mean = float(np.mean(np.abs(raw_exact)))
            env_peak = float(np.max(np.abs(raw_exact)))
            iemg = float(np.sum(np.abs(raw_exact)) / fs)
        else:
            env_mean = env_peak = iemg = np.nan

        # MDF + RMS on padded window (with preprocessing — key fatigue indicators)
        if raw_pad.size >= 32:
            proc = core.preprocess_emg(raw_pad, fs)
            _, mdf = core.mnf_mdf(proc, fs)
            rms = float(np.sqrt(np.mean(proc * proc)))
        else:
            mdf = rms = np.nan

        rows.append({
            'swing_id': int(r['swing_id']),
            't_start_ms': t0_ms,
            't_peak_ms': float(r['t_peak_ms']),
            't_end_ms': t1_ms,
            'imu_peak_z': float(r.get('peak_z', np.nan)),
            'imu_peak_mag': float(r.get('peak_mag', np.nan)),
            'emg_env_mean': env_mean,
            'emg_env_peak': env_peak,
            'emg_iemg': iemg,
            'rms': rms,
            'mdf': float(mdf) if mdf is not None else np.nan,
        })

    return pd.DataFrame(rows)


def windowed_emg_rms_stitched(
    emg_df: pd.DataFrame,
    cfg: Dict[str, Any],
    win_s: float = 10.0,
    step_s: float = 5.0,
) -> pd.DataFrame:
    """Compute windowed EMG RMS/MAV across the full stitched session.

    Uses fixed-size windows on the raw EMG signal (no per-swing alignment).
    Very fast: O(N) where N = total EMG samples.

    Returns DataFrame with columns: t_ms (window center), rms, mav.
    """
    if emg_df is None or len(emg_df) == 0:
        return pd.DataFrame(columns=['t_ms', 'rms', 'mav'])

    fs = float(cfg.get('session', {}).get('emg_fs_hz', 2000.0))
    win_samples = max(1, int(win_s * fs))
    step_samples = max(1, int(step_s * fs))

    emg_sorted = emg_df.dropna(subset=['raw']).sort_values('abs_us').reset_index(drop=True)
    raw_arr = emg_sorted['raw'].to_numpy(dtype=float)
    t_ms_arr = emg_sorted['ts_ms'].to_numpy(dtype=float)

    rows = []
    i = 0
    while i + win_samples <= len(raw_arr):
        seg = raw_arr[i:i + win_samples]
        t_center = float(t_ms_arr[i + win_samples // 2])
        rms = float(np.sqrt(np.mean(seg * seg)))
        mav = float(np.mean(np.abs(seg)))
        rows.append({'t_ms': t_center, 'rms': rms, 'mav': mav})
        i += step_samples

    return pd.DataFrame(rows)


def _plot_windowed_rms(
    win_rms_df: pd.DataFrame,
    reconnection_times_s: List[float],
    out_dir: str,
) -> None:
    """Plot windowed EMG RMS across the full session with reconnection markers."""
    if win_rms_df is None or len(win_rms_df) == 0:
        return
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return

    t_s = win_rms_df['t_ms'].to_numpy(float) / 1000.0

    fig, ax = plt.subplots(1, 1, figsize=(14, 3))
    ax.plot(t_s, win_rms_df['rms'].to_numpy(float),
            lw=1.0, color='darkorange', label='RMS (windowed)')
    if 'mav' in win_rms_df.columns:
        ax.plot(t_s, win_rms_df['mav'].to_numpy(float),
                lw=0.8, color='steelblue', alpha=0.6, label='MAV (windowed)')

    for rt in reconnection_times_s:
        ax.axvline(rt, color='navy', ls='--', lw=1.0, alpha=0.6)
        ax.text(rt, float(np.nanmax(win_rms_df['rms'])) * 0.95,
                f' {rt/60:.1f}m', fontsize=7, color='navy', va='top', rotation=90)

    ax.set_xlabel('time (s)')
    ax.set_ylabel('EMG amplitude')
    ax.set_title('Windowed EMG RMS/MAV — full session (navy dashed = BLE reconnection)')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    fig.savefig(os.path.join(out_dir, 'windowed_rms.png'), dpi=150)
    plt.close(fig)
    log('Saved windowed_rms.png')


def per_swing_emg_features_stitched(
    swings: pd.DataFrame,
    emg_df: pd.DataFrame,
    cfg: Dict[str, Any],
    imu_df: pd.DataFrame = None,
) -> pd.DataFrame:
    """Compute per-swing EMG + IMU features from stitched in-memory data.

    Args:
        swings:  swing windows with t_start_ms / t_end_ms in absolute ms
        emg_df:  stitched EMG DataFrame with abs_us and raw columns
        cfg:     config dict
        imu_df:  optional stitched IMU DataFrame (ts_ms, ax, ay, az, gx, gy, gz)
                 When provided, adds per-swing accelerometer features:
                   imu_mean_acc_dyn  — mean |acc_mag - 1g| (effort/impact proxy)
                   imu_peak_acc_dyn  — peak |acc_mag - 1g|
                 Note: gyro features are omitted because gyro saturates at FSR=250 dps
                 for tennis swings. Increase gyro_fsr_dps to 1000+ in firmware to unlock.
    """
    fs = float(cfg.get('session', {}).get('emg_fs_hz', 2000.0))
    pad_ms = float(cfg.get('swing_detection', {}).get('mdf_pad_ms', 300.0))
    zc_thr = float(cfg.get('features', {}).get('zc_thr', 0.01))
    ssc_thr = float(cfg.get('features', {}).get('ssc_thr', 0.01))

    # Pre-sort EMG by abs_us for fast binary-search indexing
    emg_sorted = emg_df.dropna(subset=['raw']).sort_values('abs_us').reset_index(drop=True)
    abs_us_arr = emg_sorted['abs_us'].to_numpy(dtype=np.int64)
    raw_arr = emg_sorted['raw'].to_numpy(dtype=float)

    # Pre-sort IMU by ts_ms for fast binary-search indexing
    imu_ts_arr = None
    imu_acc_dyn = None
    if imu_df is not None and len(imu_df) > 0:
        imu_s = imu_df.dropna(subset=['ts_ms']).sort_values('ts_ms').reset_index(drop=True)
        imu_ts_arr = imu_s['ts_ms'].to_numpy(dtype=float)
        ax = imu_s['ax'].to_numpy(dtype=float)
        ay = imu_s['ay'].to_numpy(dtype=float)
        az = imu_s['az'].to_numpy(dtype=float)
        acc_mag = np.sqrt(ax**2 + ay**2 + az**2)
        imu_acc_dyn = np.abs(acc_mag - 1.0)  # remove gravity (assumes physical units in g)

    rows = []
    n = int(len(swings))
    log(f'Computing per-swing EMG features for {n} swings (stitched)...')

    for ii, r in enumerate(swings.to_dict('records'), start=1):
        if ii == 1 or ii % 10 == 0 or ii == n or ii in [25, 50, 100, 200, 300, 400, 500]:
            log(f'  Processing swing {ii}/{n} ({100 * ii // n}%)')

        t0_ms = float(r['t_start_ms'])
        t1_ms = float(r['t_end_ms'])

        # Convert ms to us for indexing into abs_us array
        t0_us = int(t0_ms * 1000)
        t1_us = int(t1_ms * 1000)
        t0p_us = int((t0_ms - pad_ms) * 1000)
        t1p_us = int((t1_ms + pad_ms) * 1000)

        # Extract exact window using binary search
        i0 = int(np.searchsorted(abs_us_arr, t0_us, side='left'))
        i1 = int(np.searchsorted(abs_us_arr, t1_us, side='right'))
        raw_exact = raw_arr[i0:i1]

        # Extract padded window
        j0 = int(np.searchsorted(abs_us_arr, t0p_us, side='left'))
        j1 = int(np.searchsorted(abs_us_arr, t1p_us, side='right'))
        raw_pad = raw_arr[j0:j1]

        # Effort proxies on exact window
        if raw_exact.size:
            env_mean = float(np.mean(np.abs(raw_exact)))
            env_peak = float(np.max(np.abs(raw_exact)))
            iemg = float(np.sum(np.abs(raw_exact)) / fs)
        else:
            env_mean = env_peak = iemg = np.nan

        # Spectral/time features on padded window
        if raw_pad.size >= 32:
            proc = core.preprocess_emg(raw_pad, fs)
            mnf, mdf = core.mnf_mdf(proc, fs)
            mav = core.feat_mav(proc)
            rms = core.feat_rms(proc)
            wl = core.feat_wl(proc)
            zc = core.feat_zc(proc, thr=zc_thr)
            ssc = core.feat_ssc(proc, thr=ssc_thr)
        else:
            mnf = mdf = mav = rms = wl = zc = ssc = np.nan

        # Per-swing IMU accelerometer features
        imu_mean_acc_dyn = np.nan
        imu_peak_acc_dyn = np.nan
        if imu_ts_arr is not None:
            ia0 = int(np.searchsorted(imu_ts_arr, t0_ms, side='left'))
            ia1 = int(np.searchsorted(imu_ts_arr, t1_ms, side='right'))
            seg_acc = imu_acc_dyn[ia0:ia1]
            if seg_acc.size > 0:
                imu_mean_acc_dyn = float(np.nanmean(seg_acc))
                imu_peak_acc_dyn = float(np.nanmax(seg_acc))

        rows.append({
            'swing_id': int(r['swing_id']),
            't_start_ms': t0_ms,
            't_peak_ms': float(r['t_peak_ms']),
            't_end_ms': t1_ms,
            'imu_peak_z': float(r.get('peak_z', np.nan)),
            'imu_peak_mag': float(r.get('peak_mag', np.nan)),
            'imu_mean_acc_dyn': imu_mean_acc_dyn,
            'imu_peak_acc_dyn': imu_peak_acc_dyn,
            'emg_env_mean': env_mean,
            'emg_env_peak': env_peak,
            'emg_iemg': iemg,
            'mav': mav,
            'rms': rms,
            'wl': wl,
            'zc': zc,
            'ssc': ssc,
            'mnf': float(mnf) if mnf is not None else np.nan,
            'mdf': float(mdf) if mdf is not None else np.nan,
        })

    return pd.DataFrame(rows)


def _plot_fatigue_trend_stitched(
    swing_feat_df: pd.DataFrame,
    reconnection_times_s: List[float],
    out_dir: str,
    cfg: Dict[str, Any],
    warmup_skip_ms: float = 0.0,
) -> None:
    """Plot MDF and RMS fatigue trend across the full stitched session.

    Vertical dashed lines mark BLE reconnection boundaries.
    Pre-warmup swings (t < warmup_skip_ms) are excluded from the plot to avoid
    misleading high drop % values caused by poor electrode contact at session start.
    A vertical line marks the warmup boundary.
    """
    if swing_feat_df is None or len(swing_feat_df) == 0:
        return
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        log('[WARN] matplotlib not available; skipping fatigue trend plot')
        return

    # Exclude pre-warmup swings from the plot (poor electrode contact → misleading MDF)
    warmup_skip_s = warmup_skip_ms / 1000.0
    if warmup_skip_ms > 0:
        plot_df = swing_feat_df[swing_feat_df['t_peak_ms'] >= warmup_skip_ms].copy()
        if len(plot_df) == 0:
            plot_df = swing_feat_df.copy()  # fallback: show all if nothing remains
    else:
        plot_df = swing_feat_df.copy()

    t_s = plot_df['t_peak_ms'].to_numpy(float) / 1000.0

    # Determine available subplots
    has_drop = 'swing_mdf_drop_pct' in plot_df.columns
    has_acc = 'swing_acc_drop_pct' in plot_df.columns
    n_rows = 2 + int(has_drop) + int(has_acc)
    fig, axes = plt.subplots(n_rows, 1, figsize=(14, 4 * n_rows), sharex=True)

    for ax, col, ylabel, color in [
        (axes[0], 'mdf', 'MDF (Hz)', 'steelblue'),
        (axes[1], 'rms', 'RMS', 'darkorange'),
    ]:
        if col not in plot_df.columns:
            continue
        y = plot_df[col].to_numpy(float)
        ax.scatter(t_s, y, s=8, alpha=0.5, color=color, label=col.upper())

        # Rolling median trend line (window = 20 swings)
        win = min(20, max(3, len(y) // 10))
        if len(y) >= win:
            from numpy.lib.stride_tricks import sliding_window_view
            try:
                yw = sliding_window_view(y, win)
                tw = t_s[win - 1:]
                trend = np.nanmedian(yw, axis=1)
                ax.plot(tw, trend, lw=1.5, color=color, alpha=0.9, label=f'{col.upper()} trend')
            except Exception:
                pass

        # BLE reconnection markers
        for rt in reconnection_times_s:
            ax.axvline(rt, color='gray', ls='--', lw=1.0, alpha=0.7)

        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=8)

    # Third subplot: MDF drop % relative to active-swing baseline
    subplot_idx = 2
    if has_drop:
        ax3 = axes[subplot_idx]
        subplot_idx += 1
        drop = plot_df['swing_mdf_drop_pct'].to_numpy(float)
        ax3.scatter(t_s, drop, s=8, alpha=0.5, color='purple', label='MDF drop %')
        win = min(20, max(3, len(drop) // 10))
        if len(drop) >= win:
            from numpy.lib.stride_tricks import sliding_window_view
            try:
                dw = sliding_window_view(drop, win)
                tw = t_s[win - 1:]
                ax3.plot(tw, np.nanmedian(dw, axis=1), lw=1.5, color='purple',
                         alpha=0.9, label='MDF drop trend')
            except Exception:
                pass
        ax3.axhline(0.0,  color='k',      ls='-',  lw=1.0, alpha=0.5, label='baseline (0%)')
        ax3.axhline(12.0, color='orange', ls='--', lw=1.0, alpha=0.7, label='mild fatigue (+12%)')
        ax3.axhline(20.0, color='red',    ls='--', lw=1.0, alpha=0.7, label='significant (+20%)')
        for rt in reconnection_times_s:
            ax3.axvline(rt, color='gray', ls='--', lw=1.0, alpha=0.7)
        ax3.set_ylabel('MDF drop % (↑ = fatigue)')
        ax3.grid(True, alpha=0.3)
        ax3.legend(loc='best', fontsize=8)

    # Fourth subplot: acc_drop_pct (IMU accelerometer fatigue indicator)
    # acc_drop_pct > 0 means swing force decreased relative to baseline → fatigue
    # Note: gyro is saturated at FSR=250 dps; acc_dyn is the reliable IMU fatigue signal.
    if has_acc:
        ax4 = axes[subplot_idx]
        acc_drop = plot_df['swing_acc_drop_pct'].to_numpy(float)
        ax4.scatter(t_s, acc_drop, s=8, alpha=0.5, color='teal', label='acc drop %')
        win = min(20, max(3, len(acc_drop) // 10))
        if len(acc_drop) >= win:
            from numpy.lib.stride_tricks import sliding_window_view
            try:
                dw = sliding_window_view(acc_drop, win)
                tw = t_s[win - 1:]
                ax4.plot(tw, np.nanmedian(dw, axis=1), lw=1.5, color='teal',
                         alpha=0.9, label='acc drop trend')
            except Exception:
                pass
        ax4.axhline(0.0,  color='k',      ls='-',  lw=1.0, alpha=0.5, label='baseline (0%)')
        ax4.axhline(10.0, color='orange', ls='--', lw=1.0, alpha=0.7, label='mild (+10%)')
        ax4.axhline(20.0, color='red',    ls='--', lw=1.0, alpha=0.7, label='significant (+20%)')
        for rt in reconnection_times_s:
            ax4.axvline(rt, color='gray', ls='--', lw=1.0, alpha=0.7)
        ax4.set_ylabel('Acc drop % (↑ = less force)')
        ax4.grid(True, alpha=0.3)
        ax4.legend(loc='best', fontsize=8)

    axes[-1].set_xlabel('time (s)')

    # Annotate reconnection times and warmup boundary on all axes
    for ax in axes:
        if warmup_skip_s > 0:
            ax.axvline(warmup_skip_s, color='green', ls=':', lw=1.2, alpha=0.7)
    if warmup_skip_s > 0:
        axes[0].text(warmup_skip_s, axes[0].get_ylim()[1],
                     f' warmup end\n {warmup_skip_s/60:.1f}min',
                     fontsize=7, color='green', va='top', rotation=90)

    if reconnection_times_s:
        for rt in reconnection_times_s:
            axes[0].text(rt, axes[0].get_ylim()[1], f' {rt/60:.1f}min',
                         fontsize=7, color='gray', va='top', rotation=90)

    if not has_drop and not has_acc:
        axes[1].set_xlabel('time (s)')
    title_suffix = f' | warmup={warmup_skip_s/60:.0f}min excluded' if warmup_skip_s > 0 else ''
    fig.suptitle(f'Fatigue trend — full tennis session (dashed = BLE reconnection){title_suffix}', fontsize=11)
    fig.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    fig.savefig(os.path.join(out_dir, 'fatigue_trend.png'), dpi=150)
    plt.close(fig)
    log(f'Saved fatigue_trend.png')


# ---------------------------------------------------------
# Per-swing fatigue summary (replaces windowed analyze_fatigue)
# ---------------------------------------------------------

def _compute_per_swing_fatigue_summary(
    swing_feat_df: pd.DataFrame,
    out_dir: str,
    warmup_skip_ms: float = 0.0,
    ext_baseline_mdf: float = None,
) -> None:
    """Compute fatigue summary from per-swing MDF and save to fatigue_summary.csv.

    Per-swing MDF is more reliable than windowed MDF because it only samples
    windows when the muscle is actively contracting (swing events), not during
    rest periods between rallies where the signal is noise-dominated.

    Args:
        swing_feat_df:    per-swing feature DataFrame (must have 'mdf' column)
        out_dir:          output directory for fatigue_summary.csv
        warmup_skip_ms:   exclude swings before this time (ms) from analysis
        ext_baseline_mdf: pre-computed baseline MDF from baseline.json (median of
                          first N post-warmup swings after RMS filtering). When
                          provided, this value is used directly so that
                          fatigue_summary.csv is consistent with baseline.json and
                          swing_features.csv (swing_mdf_drop_pct). Falls back to
                          mean of first 10% of post-warmup swings if None.

    Replaces the call to core.analyze_fatigue(res.feats, ...) which uses
    1-second windowed features and is corrupted by rest-period noise.
    """
    if swing_feat_df is None or len(swing_feat_df) == 0:
        return

    # Filter out pre-warmup swings (poor electrode contact → misleading MDF)
    if warmup_skip_ms > 0:
        df = swing_feat_df[swing_feat_df['t_peak_ms'] >= warmup_skip_ms].copy()
        if len(df) == 0:
            df = swing_feat_df.copy()
    else:
        df = swing_feat_df.copy()

    if 'mdf' not in df.columns:
        return

    mdf = df['mdf'].to_numpy(float)
    t_s = df['t_peak_ms'].to_numpy(float) / 1000.0
    valid = np.isfinite(mdf)
    mdf = mdf[valid]
    t_s = t_s[valid]

    if len(mdf) < 10:
        log('[Fatigue] Not enough post-warmup swings for fatigue summary.')
        return

    # baseline_n is always needed for MNF computation (MNF has no external baseline).
    baseline_n = max(1, int(len(mdf) * 0.1))

    # Baseline MDF: use pre-computed value from baseline.json when available so that
    # fatigue_summary.csv is consistent with swing_features.csv (swing_mdf_drop_pct).
    # The pre-computed baseline uses median + RMS filtering (noise-dominated swings
    # removed), which is more robust than the first-10%-mean fallback below.
    if ext_baseline_mdf is not None and np.isfinite(float(ext_baseline_mdf)) and float(ext_baseline_mdf) > 0:
        baseline_mdf = float(ext_baseline_mdf)
        baseline_source = 'baseline_json'
    else:
        # Fallback: mean of first 10% of post-warmup swings (no RMS filter)
        baseline_mdf = float(np.nanmean(mdf[:baseline_n]))
        baseline_source = 'first_10pct_mean'

    # Final: last 10% of post-warmup swings
    final_n = max(1, int(len(mdf) * 0.1))
    final_mdf = float(np.nanmean(mdf[-final_n:]))

    mdf_drop_pct = (
        100.0 * (baseline_mdf - final_mdf) / baseline_mdf
        if (np.isfinite(baseline_mdf) and baseline_mdf > 0) else np.nan
    )

    # MNF if available (full mode only)
    mnf_drop_pct = np.nan
    if 'mnf' in df.columns:
        mnf = df['mnf'].to_numpy(float)[valid]
        if np.sum(np.isfinite(mnf)) >= 10:
            baseline_mnf = float(np.nanmean(mnf[:baseline_n]))
            final_mnf = float(np.nanmean(mnf[-final_n:]))
            mnf_drop_pct = (
                100.0 * (baseline_mnf - final_mnf) / baseline_mnf
                if (np.isfinite(baseline_mnf) and baseline_mnf > 0) else np.nan
            )

    # Onset: first time rolling-median MDF drops below 85% of baseline
    onset_time = np.nan
    if np.isfinite(baseline_mdf) and baseline_mdf > 0:
        threshold = baseline_mdf * 0.85
        min_time = float(np.nanmax(t_s)) * 0.2
        rolling = pd.Series(mdf).rolling(window=20, min_periods=5).mean().to_numpy(float)
        cand = np.where((t_s >= min_time) & (rolling <= threshold))[0]
        if len(cand):
            onset_time = float(t_s[cand[0]])

    onset_str = f'{onset_time:.1f}' if np.isfinite(onset_time) else 'n/a'
    mnf_str = f'{mnf_drop_pct:.2f}' if np.isfinite(mnf_drop_pct) else 'n/a'
    log(f'[Fatigue/per-swing] MDF drop % = {mdf_drop_pct:.2f} ; '
        f'MNF drop % = {mnf_str} ; '
        f'onset_s = {onset_str}')

    summary = {
        'baseline_MDF': round(baseline_mdf, 3),
        'final_MDF': round(final_mdf, 3),
        'MDF_drop_pct': round(mdf_drop_pct, 3) if np.isfinite(mdf_drop_pct) else np.nan,
        'MNF_drop_pct': round(mnf_drop_pct, 3) if np.isfinite(mnf_drop_pct) else np.nan,
        'fatigue_onset_s': round(onset_time, 1) if np.isfinite(onset_time) else np.nan,
        'n_swings_post_warmup': int(len(mdf)),
        'warmup_skip_min': round(warmup_skip_ms / 60000.0, 1),
        'source': 'per_swing',
        'baseline_source': baseline_source,
    }

    os.makedirs(out_dir, exist_ok=True)
    pd.DataFrame([summary]).to_csv(os.path.join(out_dir, 'fatigue_summary.csv'), index=False)
    log('Saved fatigue_summary.csv (per-swing)')


# ---------------------------------------------------------
# Baseline quality filter
# ---------------------------------------------------------

def _filter_baseline_by_rms_with_logging(
    base_feats: pd.DataFrame,
    all_swing_feats: pd.DataFrame,
    rms_fraction: float = 0.25,
    min_keep: int = 3,
) -> pd.DataFrame:
    """Wrapper around core.filter_baseline_by_rms that adds diagnostic logging.
    
    Delegates to emg_util.filter_baseline_by_rms for the actual filtering logic,
    then logs the results for diagnostic purposes.
    """
    if base_feats is None or len(base_feats) == 0:
        return base_feats
    if 'rms' not in base_feats.columns or 'rms' not in all_swing_feats.columns:
        return base_feats

    # Compute session p90 RMS for logging
    all_rms = all_swing_feats['rms'].dropna().to_numpy(dtype=float)
    if len(all_rms) < 5:
        return base_feats
    session_p90_rms = float(np.nanpercentile(all_rms, 90))
    if session_p90_rms <= 0 or not np.isfinite(session_p90_rms):
        return base_feats

    # Call core filter function
    filtered = core.filter_baseline_by_rms(base_feats, all_swing_feats, rms_fraction, min_keep)

    # Log results
    n_dropped = len(base_feats) - len(filtered)
    if n_dropped > 0:
        threshold = rms_fraction * session_p90_rms
        if len(filtered) >= min_keep:
            log(f'[Baseline] Dropped {n_dropped}/{len(base_feats)} low-RMS swings '
                f'(threshold={threshold:.2f}, session_p90_rms={session_p90_rms:.2f}). '
                f'Baseline now uses {len(filtered)} swings.')
        else:
            threshold_fallback = 0.10 * session_p90_rms
            log(f'[Baseline] Strict filter dropped too many. Used fallback threshold={threshold_fallback:.2f}, '
                f'dropped {n_dropped}/{len(base_feats)} swings.')
    elif len(filtered) < len(base_feats):
        log(f'[Baseline] Low-RMS filter would leave only {len(filtered)} swings '
            f'(< min_keep={min_keep}); keeping original {len(base_feats)} swings.')

    return filtered


# ---------------------------------------------------------
# NEW: Tennis Session Analysis (Folder-Level)
# Treats ALL BLE connections in a folder as ONE continuous tennis session.
# Replaces the per-BLE-connection loop in main().
# ---------------------------------------------------------

def analyze_tennis_session(log_dir: str, cfg: Dict[str, Any], out_dir: str) -> str:
    """Analyze a full tennis session from a folder of BLE capture files.

    All BLE connections in log_dir are stitched into one continuous timeline
    using wall-clock session_id timestamps. Analysis (swing detection, fatigue,
    bouts) runs on the full stitched data as one unit.

    Args:
        log_dir: directory containing all BLE capture CSV files for the session
        cfg:     config dict (from config.yaml)
        out_dir: output directory — all outputs written here, no subdirectories

    Returns:
        out_dir path
    """
    os.makedirs(out_dir, exist_ok=True)
    sess_cfg = cfg.get('session', {}) or {}

    log(f'=== Analyzing tennis session: {log_dir} ===')
    log(f'Output: {out_dir}')

    # 1. Discover all BLE connections in the folder
    sessions = loader.discover_sessions(
        log_dir,
        emg_glob=str(sess_cfg.get('emg_glob', 'emg_log_*.csv')),
        imu_glob=str(sess_cfg.get('imu_glob', 'imu_log_*.csv')),
        vitals_name=str(sess_cfg.get('vitals_path', 'vitals_log.csv')),
    )

    if not sessions:
        raise SystemExit(f'No capture files found in {log_dir}')

    capture_ids_sorted = sorted(sessions.keys())
    log(f'Found {len(sessions)} BLE connection(s): {capture_ids_sorted}')

    # 2. Stitch all BLE connections into one continuous timeline
    # Defaults match firmware IMU_ACC_FSR_G=4 / IMU_GYRO_FSR_DPS=1000 (updated 2026-02-25).
    # Using the old defaults (2.0 / 250.0) would scale gyro 4× too small, causing
    # zero swings detected when no config file is provided.
    emg_df, imu_df, reconnection_times_s, capture_ids = loader.load_session_stitched(
        sessions,
        use_physical_units=bool(sess_cfg.get('use_physical_units', True)),
        acc_fsr_default_g=float(sess_cfg.get('acc_fsr_default_g', 4.0)),
        gyro_fsr_default_dps=float(sess_cfg.get('gyro_fsr_default_dps', 1000.0)),
    )

    total_dur_s = (
        float(emg_df['abs_us'].max() - emg_df['abs_us'].min()) / 1e6
        if len(emg_df) else 0.0
    )
    log(f'Stitched: {len(emg_df)} EMG rows, {len(imu_df)} IMU rows, '
        f'total={total_dur_s:.1f}s ({total_dur_s/60:.1f}min)')
    log(f'BLE reconnections at: {[f"{t:.1f}s ({t/60:.1f}min)" for t in reconnection_times_s]}')

    # Save capture segment info for reference
    pd.DataFrame({
        'capture_id': capture_ids,
        'reconnection_time_s': [0.0] + reconnection_times_s,
    }).to_csv(os.path.join(out_dir, 'capture_segments.csv'), index=False)

    # 3. Activity gating on full IMU stream
    # ts_ms is already set to abs_us/1000 by load_session_stitched, so
    # all existing activity_segments_from_imu() logic works unchanged.
    active_segs = activity_segments_from_imu(imu_df, cfg)
    active_segs.to_csv(os.path.join(out_dir, 'active_segments.csv'), index=False)
    log(f'Active segments: {len(active_segs)}')

    # 4. Swing detection on full IMU stream
    swings = detect_swings_from_imu(imu_df, cfg)

    in_active = swing_in_active_mask(swings, active_segs)
    if len(swings):
        swings = swings.copy()
        swings['in_active'] = in_active.astype(int)

    ag_cfg = (cfg.get('activity_gating', {}) or {})
    if bool(ag_cfg.get('filter_swings', False)) and len(swings):
        swings = swings.loc[swings['in_active'].astype(bool)].reset_index(drop=True)
        swings['swing_id'] = np.arange(len(swings), dtype=int)

    swings.to_csv(os.path.join(out_dir, 'swing_windows.csv'), index=False)
    log(f'Detected {len(swings)} swings across full session')

    # 5. IMU activity overlay plot (with reconnection markers)
    _plot_imu_overlay_with_reconnections(imu_df, active_segs, swings,
                                         reconnection_times_s, out_dir, cfg)

    # 6. EMG health check — run per BLE connection, convert to absolute time
    hcfg = _health_cfg(cfg)
    bad_emg_ms: List[Tuple[float, float]] = []
    try:
        if bool(hcfg.get('enable', True)):
            from datetime import datetime
            first_dt = datetime.strptime(capture_ids[0], '%Y%m%d_%H%M%S')
            for session_id, files in sessions.items():
                if not files.emg_paths:
                    continue
                bad_us = health.emg_bad_intervals_us(files.emg_paths, cfg)
                if bad_us:
                    sess_dt = datetime.strptime(session_id, '%Y%m%d_%H%M%S')
                    wall_offset_us = int((sess_dt - first_dt).total_seconds() * 1e6)
                    cap_emg = emg_df[emg_df['session_id'] == session_id]
                    if len(cap_emg):
                        dev_start = int(cap_emg['dev_us'].min())
                        for a_us, b_us in bad_us:
                            a_abs = (wall_offset_us + (a_us - dev_start)) / 1000.0
                            b_abs = (wall_offset_us + (b_us - dev_start)) / 1000.0
                            bad_emg_ms.append((a_abs, b_abs))
        if bad_emg_ms:
            pd.DataFrame([
                {'start_abs_ms': a, 'end_abs_ms': b, 'duration_s': (b - a) / 1000.0}
                for (a, b) in bad_emg_ms
            ]).to_csv(os.path.join(out_dir, 'emg_bad_intervals.csv'), index=False)
    except Exception as e:
        log(f'[WARN] EMG bad-interval detection failed: {e}')

    if bad_emg_ms and bool(hcfg.get('filter_swings_by_emg_bad', False)) and len(swings):
        swings_before = len(swings)
        swings = _filter_swings_by_bad_emg(swings, bad_emg_ms)
        if len(swings) != swings_before:
            swings.to_csv(os.path.join(out_dir, 'swing_windows_emg_filtered.csv'), index=False)
            log(f'[EMG] Filtered swings by BAD EMG: {swings_before} -> {len(swings)}')

    mode = (cfg.get('features', {}) or {}).get('mode', 'both')

    # --- Early exit if no swings ---
    if len(swings) == 0:
        bout_df = segment_bouts_from_active(active_segs, swings, cfg)
        bout_df.to_csv(os.path.join(out_dir, 'bout_summary.csv'), index=False)
        _save_tennis_session_summary(out_dir, capture_ids, reconnection_times_s,
                                     total_dur_s, 0, len(bout_df), mode)
        log(f'Finished (no swings). Outputs -> {out_dir}')
        return out_dir

    # --- Fast mode (bout only, no EMG) ---
    if mode == 'bout':
        bout_df = segment_bouts_from_active(active_segs, swings, cfg)
        bout_df.to_csv(os.path.join(out_dir, 'bout_summary.csv'), index=False)
        _save_tennis_session_summary(out_dir, capture_ids, reconnection_times_s,
                                     total_dur_s, len(swings), len(bout_df), mode)
        log(f'Finished (fast mode). Outputs -> {out_dir}')
        return out_dir

    # --- Medium mode: envelope + MDF + RMS per swing + windowed RMS ---
    # Faster than full mode: skips wl/zc/ssc/mnf/mav, no health check overhead.
    # Gives the two key fatigue indicators (MDF ↓, RMS ↑) plus effort proxies.
    if mode == 'medium':
        feat_cfg = cfg.get('features', {}) or {}
        win_rms_s = float(feat_cfg.get('win_rms_s', 10.0))
        step_rms_s = float(feat_cfg.get('step_rms_s', 5.0))

        swing_feat_df = per_swing_emg_medium_stitched(swings, emg_df, cfg)

        # Windowed RMS for continuous fatigue trend
        win_rms_df = windowed_emg_rms_stitched(emg_df, cfg,
                                                win_s=win_rms_s, step_s=step_rms_s)
        win_rms_df.to_csv(os.path.join(out_dir, 'windowed_rms.csv'), index=False)

        # Baseline from first N swings — filter out noise-dominated (low-RMS) swings
        # so that poor-electrode-contact periods at session start don't corrupt the
        # baseline MDF (noise MDF ≈ 100 Hz vs active-muscle MDF ≈ 150-200 Hz).
        base_sw = select_baseline_swings(swings, session_t0_ms=0.0, cfg=cfg)
        base_feats = swing_feat_df[swing_feat_df['swing_id'].isin(base_sw['swing_id'])]
        base_feats = _filter_baseline_by_rms_with_logging(base_feats, swing_feat_df)
        base = baseline_from_features(base_feats)
        swing_feat_df = apply_deltas(swing_feat_df, base, prefix='swing_')

        swing_feat_df.to_csv(os.path.join(out_dir, 'swing_features.csv'), index=False)
        with open(os.path.join(out_dir, 'baseline.json'), 'w', encoding='utf-8') as f:
            json.dump({'baseline': base, 'selected_swings': base_sw.to_dict('records')},
                      f, indent=2)

        bout_df = segment_bouts_from_active(active_segs, swings, cfg)
        bout_df.to_csv(os.path.join(out_dir, 'bout_summary.csv'), index=False)

        warmup_skip_ms = float(cfg.get('baseline', {}).get('warmup_skip_min', 0.0)) * 60.0 * 1000.0
        _plot_fatigue_trend_stitched(swing_feat_df, reconnection_times_s, out_dir, cfg,
                                     warmup_skip_ms=warmup_skip_ms)
        _plot_windowed_rms(win_rms_df, reconnection_times_s, out_dir)
        _compute_per_swing_fatigue_summary(swing_feat_df, out_dir, warmup_skip_ms=warmup_skip_ms,
                                           ext_baseline_mdf=base.get('mdf'))

        _save_tennis_session_summary(out_dir, capture_ids, reconnection_times_s,
                                     total_dur_s, len(swings), len(bout_df), mode)
        log(f'Finished (medium mode). Outputs -> {out_dir}')
        return out_dir

    # --- Full mode: per-swing EMG features ---
    swing_feat_df = per_swing_emg_features_stitched(swings, emg_df, cfg, imu_df=imu_df)

    # Baseline: first N swings of the full session — filter out noise-dominated
    # (low-RMS) swings so that poor-electrode-contact periods at session start
    # don't corrupt the baseline MDF (noise MDF ≈ 100 Hz vs active MDF ≈ 150-200 Hz).
    base_sw = select_baseline_swings(swings, session_t0_ms=0.0, cfg=cfg)
    base_feats = swing_feat_df[swing_feat_df['swing_id'].isin(base_sw['swing_id'])]
    base_feats = _filter_baseline_by_rms_with_logging(base_feats, swing_feat_df)
    base = baseline_from_features(base_feats)
    swing_feat_df = apply_deltas(swing_feat_df, base, prefix='swing_')

    swing_feat_df.to_csv(os.path.join(out_dir, 'swing_features.csv'), index=False)
    with open(os.path.join(out_dir, 'baseline.json'), 'w', encoding='utf-8') as f:
        json.dump({'baseline': base, 'selected_swings': base_sw.to_dict('records')}, f, indent=2)

    # Bouts
    bout_df = segment_bouts_from_active(active_segs, swings, cfg)
    bout_df.to_csv(os.path.join(out_dir, 'bout_summary.csv'), index=False)

    # Windowed plots (optional)
    pl = cfg.get('plots', {}) or {}
    if bool(pl.get('enable', False)):
        emg_imu_df = loader.make_interleaved_df(emg_df, imu_df)
        res = core.compute(
            emg_imu_df,
            emg_fs_hz=float(sess_cfg.get('emg_fs_hz', 2000)),
            win_sec=float(pl.get('win_sec', 1.0)),
            step_sec=float(pl.get('step_sec', 0.25)),
        )

        corr_cfg = (cfg.get('diagnostics', {}) or {}).get('emg_imu_correlation', {})
        if bool(corr_cfg.get('enable', False)):
            save_emg_imu_correlation(
                res.feats, out_dir,
                method=str(corr_cfg.get('method', 'pearson')),
                fname=str(corr_cfg.get('save_name', 'emg_imu_correlation.json')),
            )
            log('Saved emg_imu_correlation.json')

        label = str(sess_cfg.get('label', os.path.basename(log_dir.rstrip('/\\'))))
        core.plot_all(
            res,
            emg_fs_hz=float(sess_cfg.get('emg_fs_hz', 2000)),
            title=f'EMG/IMU summary | {label}',
            full_duration=bool(pl.get('full_duration', True)),
            emg_max_points=int(pl.get('emg_max_points', 300000)),
            save_dir=out_dir,
            silent=True,
        )

        if bool(pl.get('do_fatigue', False)):
            # NOTE: core.analyze_fatigue uses windowed features (1-second windows including
            # rest periods) which gives unreliable MDF. We skip it here and use
            # _compute_per_swing_fatigue_summary instead (per-swing MDF only).
            pass

    # Fatigue trend plot with reconnection markers (exclude pre-warmup swings)
    warmup_skip_ms = float(cfg.get('baseline', {}).get('warmup_skip_min', 0.0)) * 60.0 * 1000.0
    _plot_fatigue_trend_stitched(swing_feat_df, reconnection_times_s, out_dir, cfg,
                                 warmup_skip_ms=warmup_skip_ms)
    # Per-swing fatigue summary (replaces windowed analyze_fatigue).
    # Pass base['mdf'] so fatigue_summary.csv uses the same baseline as baseline.json
    # and swing_features.csv (swing_mdf_drop_pct). Without this, the function would
    # recompute the baseline from the first 10% of post-warmup swings (no RMS filter),
    # giving a different (lower) value than the RMS-filtered median in baseline.json.
    _compute_per_swing_fatigue_summary(swing_feat_df, out_dir, warmup_skip_ms=warmup_skip_ms,
                                       ext_baseline_mdf=base.get('mdf'))

    # Session summary
    _save_tennis_session_summary(out_dir, capture_ids, reconnection_times_s,
                                 total_dur_s, len(swings), len(bout_df), mode)

    log(f'Finished. Outputs -> {out_dir}')
    return out_dir


def _save_tennis_session_summary(
    out_dir: str,
    capture_ids: List[str],
    reconnection_times_s: List[float],
    total_dur_s: float,
    num_swings: int,
    num_bouts: int,
    mode: str,
) -> None:
    """Save session_summary.json for the full tennis session."""
    summary = {
        'n_capture_files': len(capture_ids),
        'capture_ids': capture_ids,
        'total_duration_s': round(total_dur_s, 3),
        'total_duration_min': round(total_dur_s / 60.0, 2),
        'num_swings': num_swings,
        'num_bouts': num_bouts,
        'reconnection_times_s': reconnection_times_s,
        'mode': mode,
    }
    with open(os.path.join(out_dir, 'session_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)


def _plot_imu_overlay_with_reconnections(
    imu_df: pd.DataFrame,
    active_segs: pd.DataFrame,
    swings: pd.DataFrame,
    reconnection_times_s: List[float],
    out_dir: str,
    cfg: Dict[str, Any],
) -> None:
    """IMU activity overlay plot with BLE reconnection boundary markers."""
    diag = cfg.get('diagnostics', {}) or {}
    acfg = diag.get('activity_overlay', {}) or {}
    if not bool(acfg.get('enable', True)):
        return
    if imu_df is None or len(imu_df) == 0:
        return

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return

    need_cols = ['ts_ms', 'gx', 'gy', 'gz']
    imu = imu_df.dropna(subset=need_cols).sort_values('ts_ms', kind='mergesort').reset_index(drop=True)
    if len(imu) == 0:
        return

    sig = compute_hybrid_intensity(imu, cfg)
    t0 = float(sig['t_ms'][0])
    t_s = (sig['t_ms'] - t0) / 1000.0

    plot_signal = str(acfg.get('plot_signal', 'intensity'))
    y = sig['gyro_mag'] if plot_signal == 'gyro_mag' else sig['intensity_smooth']
    ylab = 'gyro magnitude' if plot_signal == 'gyro_mag' else 'hybrid intensity (smoothed)'

    fig, ax = plt.subplots(1, 1, figsize=(14, 4))
    ax.plot(t_s, y, lw=0.7, label=plot_signal)

    if active_segs is not None and len(active_segs):
        for a, b in zip(active_segs['t_start_ms'].to_numpy(float),
                        active_segs['t_end_ms'].to_numpy(float)):
            ax.axvspan((a - t0) / 1000.0, (b - t0) / 1000.0, color='orange', alpha=0.18)

    if (swings is not None and len(swings) and bool(acfg.get('plot_swings', True))
            and 't_peak_ms' in swings.columns):
        sp = (swings['t_peak_ms'].to_numpy(float) - t0) / 1000.0
        ax.vlines(sp, ymin=float(np.nanmin(y)), ymax=float(np.nanmax(y)),
                  color='r', alpha=0.25, lw=0.8, label='swing peaks')

    # BLE reconnection markers
    for rt in reconnection_times_s:
        ax.axvline(rt, color='navy', ls='--', lw=1.2, alpha=0.7)
        ax.text(rt, float(np.nanmax(y)) * 0.95, f' {rt/60:.1f}min',
                fontsize=7, color='navy', va='top', rotation=90)

    try:
        th = active_segs.attrs.get('thr_high', None)
        tl = active_segs.attrs.get('thr_low', None)
        if th is not None:
            ax.axhline(float(th), color='k', ls='--', lw=1, alpha=0.5, label='enter thr')
        if tl is not None:
            ax.axhline(float(tl), color='k', ls=':', lw=1, alpha=0.5, label='exit thr')
    except Exception:
        pass

    ax.set_xlabel('time (s)')
    ax.set_ylabel(ylab)
    ax.set_title('IMU activity overlay — full tennis session (navy dashed = BLE reconnection)')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=8)

    os.makedirs(out_dir, exist_ok=True)
    fname = str(acfg.get('save_name', 'imu_activity_overlay.png'))
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, fname), dpi=150)
    plt.close(fig)
    log(f'Saved {fname}')


# ---------------------------------------------------------
# CLI Main (Keep this for PC compatibility)
# ---------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description='YAML-driven EMG/IMU analysis')
    ap.add_argument('--config', default='config.yaml', help='Path to YAML config')
    ap.add_argument('--log-dir', required=True, help='Directory containing btCentral logs')
    ap.add_argument('--out-dir', default=None, help='Override output directory')
    args = ap.parse_args()

    # Load YAML from disk
    cfg = load_config(args.config)
    sess_cfg = cfg.get('session', {})

    out_root = args.out_dir if args.out_dir is not None else sess_cfg.get('out_dir', 'out')
    os.makedirs(out_root, exist_ok=True)

    log(f'Loaded config: {args.config}')
    log(f'Output root: {out_root}')
    log(f'Scanning log_dir: {args.log_dir}')

    # Analyze the entire folder as one tennis session
    analyze_tennis_session(args.log_dir, cfg, out_root)

    # NOTE: The old per-BLE-connection loop is preserved below for reference.
    # It is no longer called by default. Use analyze_single_session() directly
    # if you need per-capture-file debugging output.
    #
    # sessions = loader.discover_sessions(args.log_dir, ...)
    # for si, session_id in enumerate(sorted(sessions.keys()), start=1):
    #     analyze_single_session(session_id, sessions[session_id], cfg, out_root,
    #                            session_idx=si, total_sessions=len(sessions))

if __name__ == '__main__':
    main()
