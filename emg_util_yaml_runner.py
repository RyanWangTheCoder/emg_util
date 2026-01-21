#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""emg_util_yaml_runner.py

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


def log(msg: str) -> None:
    import time
    ts = time.strftime('%H:%M:%S')
    print(f'[{ts}] {msg}', flush=True)


def load_config(path: str) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def robust_zscore(x: np.ndarray, baseline_mask: np.ndarray, eps: float = 1e-9):
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
    return (x - med) / (scale + eps), med, scale




# ----------------------------
# IMU percentile-based activity gating (conservative)
# ----------------------------

def compute_gyro_mag(df: pd.DataFrame) -> np.ndarray:
    """Compute gyro magnitude sqrt(gx^2 + gy^2 + gz^2)."""
    return np.sqrt(df['gx'].to_numpy(float)**2 + df['gy'].to_numpy(float)**2 + df['gz'].to_numpy(float)**2)


def activity_segments_from_imu(imu_df: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    """Create ACTIVE segments using percentile hysteresis on gyro_mag.

    cfg.activity_gating:
      p_high (enter), p_low (exit), min_active_ms, merge_gap_ms, skip_min

    If skip_min is None, falls back to baseline.warmup_skip_min.

    Returns DataFrame with columns: t_start_ms, t_end_ms, duration_s.
    Stores thresholds in out.attrs: thr_high, thr_low.
    """
    ag = (cfg.get('activity_gating', {}) or {})
    if not bool(ag.get('enable', True)):
        return pd.DataFrame(columns=['t_start_ms','t_end_ms','duration_s'])

    if imu_df is None or len(imu_df) == 0:
        return pd.DataFrame(columns=['t_start_ms','t_end_ms','duration_s'])

    imu = imu_df.dropna(subset=['ts_ms','gx','gy','gz']).sort_values('ts_ms', kind='mergesort').reset_index(drop=True)
    if len(imu) == 0:
        return pd.DataFrame(columns=['t_start_ms','t_end_ms','duration_s'])

    t_ms = imu['ts_ms'].to_numpy(float)
    t0_ms = float(t_ms[0])

    skip_min = ag.get('skip_min', None)
    if skip_min is None:
        skip_min = (cfg.get('baseline', {}) or {}).get('warmup_skip_min', 0)
    skip_ms = float(skip_min) * 60.0 * 1000.0
    mask = t_ms >= (t0_ms + skip_ms)
    if not np.any(mask):
        mask = np.ones_like(t_ms, dtype=bool)

    mag = compute_gyro_mag(imu)
    ref = mag[mask]
    ref = ref[np.isfinite(ref)]
    if ref.size < 50:
        ref = mag[np.isfinite(mag)]

    p_high = float(ag.get('p_high', 99))
    p_low  = float(ag.get('p_low', 95))
    p_high = float(np.clip(p_high, 50.0, 99.99))
    p_low  = float(np.clip(p_low, 10.0, p_high - 1e-6))

    thr_high = float(np.nanpercentile(ref, p_high))
    thr_low  = float(np.nanpercentile(ref, p_low))

    # hysteresis
    active = np.zeros(len(mag), dtype=bool)
    state = False
    for i, v in enumerate(mag):
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

    min_active_ms = float(ag.get('min_active_ms', 150.0))
    merge_gap_ms  = float(ag.get('merge_gap_ms', 300.0))
    segs = [(a,b) for (a,b) in segs if (b-a) >= min_active_ms]
    segs.sort(key=lambda ab: ab[0])

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
    out.attrs['skip_min'] = float(skip_min)
    return out


def filter_df_by_segments(df: pd.DataFrame, segs: pd.DataFrame, t_col: str = 'ts_ms') -> pd.DataFrame:
    """Filter df rows whose t_col lies inside any [t_start_ms, t_end_ms] segment."""
    if df is None or len(df) == 0 or segs is None or len(segs) == 0:
        return df
    t = df[t_col].to_numpy(float)
    starts = segs['t_start_ms'].to_numpy(float)
    ends = segs['t_end_ms'].to_numpy(float)
    order = np.argsort(starts)
    starts = starts[order]; ends = ends[order]
    idx = np.searchsorted(starts, t, side='right') - 1
    valid = idx >= 0
    idx2 = np.clip(idx, 0, len(starts)-1)
    inside = valid & (t >= starts[idx2]) & (t <= ends[idx2])
    return df.loc[inside].copy().reset_index(drop=True)


def segment_bouts_from_active(active_segs: pd.DataFrame, swings: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    """Segment bouts using ACTIVE segments as primary structure, then swing density."""
    bt = cfg.get('bout', {}) or {}
    gap_thr_s = float(bt.get('gap_thr_s', 10))
    gap_long_s = float(bt.get('gap_thr_long_s', 30))
    min_bout_swings = int(bt.get('min_bout_swings', 3))

    if active_segs is None or len(active_segs) == 0:
        return pd.DataFrame(columns=['bout_id','t_start_ms','t_end_ms','duration_s','num_swings','swings_per_min'])

    segs = active_segs.sort_values('t_start_ms').reset_index(drop=True)
    merged=[]
    cur_a=float(segs.loc[0,'t_start_ms']); cur_b=float(segs.loc[0,'t_end_ms'])
    for i in range(1, len(segs)):
        a=float(segs.loc[i,'t_start_ms']); b=float(segs.loc[i,'t_end_ms'])
        gap_s=(a-cur_b)/1000.0
        if gap_s >= gap_long_s or gap_s >= gap_thr_s:
            merged.append((cur_a,cur_b)); cur_a,cur_b=a,b
        else:
            cur_b=max(cur_b,b)
    merged.append((cur_a,cur_b))

    sw = swings.sort_values('t_peak_ms').reset_index(drop=True) if swings is not None and len(swings) else pd.DataFrame(columns=['t_peak_ms'])
    tpeaks = sw['t_peak_ms'].to_numpy(float) if 't_peak_ms' in sw.columns and len(sw) else np.array([], dtype=float)

    bouts=[]; bid=0
    for a,b in merged:
        num = int(np.sum((tpeaks>=a)&(tpeaks<=b))) if tpeaks.size else 0
        if num < min_bout_swings:
            continue
        dur_s=(b-a)/1000.0
        bouts.append({'bout_id':bid,'t_start_ms':a,'t_end_ms':b,'duration_s':dur_s,'num_swings':num,
                      'swings_per_min': float(num/max(dur_s/60.0,1e-9))})
        bid += 1
    return pd.DataFrame(bouts)


def plot_imu_activity_overlay(imu_df: pd.DataFrame, active_segs: pd.DataFrame, swings: pd.DataFrame, out_dir: str, cfg: Dict[str, Any]) -> None:
    """Save an IMU activity overlay plot (gyro_mag + ACTIVE spans + optional swing peaks)."""
    diag = cfg.get('diagnostics', {}) or {}
    acfg = diag.get('activity_overlay', {}) or {}
    if not bool(acfg.get('enable', True)):
        return
    if imu_df is None or len(imu_df) == 0:
        return

    import matplotlib.pyplot as plt
    imu = imu_df.dropna(subset=['ts_ms','gx','gy','gz']).sort_values('ts_ms', kind='mergesort').reset_index(drop=True)
    if len(imu) == 0:
        return

    t0=float(imu['ts_ms'].iloc[0])
    t_s=(imu['ts_ms'].to_numpy(float)-t0)/1000.0
    mag=compute_gyro_mag(imu)

    fig, ax = plt.subplots(1,1, figsize=(12,4))
    ax.plot(t_s, mag, lw=0.6, label='gyro_mag')

    if active_segs is not None and len(active_segs):
        for a,b in zip(active_segs['t_start_ms'].to_numpy(float), active_segs['t_end_ms'].to_numpy(float)):
            ax.axvspan((a-t0)/1000.0, (b-t0)/1000.0, color='orange', alpha=0.18)

    if swings is not None and len(swings) and bool(acfg.get('plot_swings', True)) and 't_peak_ms' in swings.columns:
        sp=(swings['t_peak_ms'].to_numpy(float)-t0)/1000.0
        ax.vlines(sp, ymin=float(np.nanmin(mag)), ymax=float(np.nanmax(mag)), color='r', alpha=0.25, lw=0.8, label='swing peaks')

    try:
        th=active_segs.attrs.get('thr_high', None)
        tl=active_segs.attrs.get('thr_low', None)
        if th is not None:
            ax.axhline(float(th), color='k', ls='--', lw=1, alpha=0.5, label='P99 threshold')
        if tl is not None:
            ax.axhline(float(tl), color='k', ls=':', lw=1, alpha=0.5, label='P95 threshold')
    except Exception:
        pass

    ax.set_xlabel('time (s)')
    ax.set_ylabel('gyro magnitude')
    ax.set_title('IMU activity gating overlay (percentile hysteresis)')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=8)

    os.makedirs(out_dir, exist_ok=True)
    fname=str(acfg.get('save_name','imu_activity_overlay.png'))
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, fname), dpi=150)
    plt.close(fig)

def detect_swings_from_imu(imu_df: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    sd = cfg.get('swing_detection', {})
    use_gyro = bool(sd.get('use_gyro', True))
    baseline_s = float(sd.get('baseline_s', 2.0))
    z_thr = float(sd.get('z_thr', 5.0))
    min_consec = int(sd.get('min_consec', 3))
    min_gap_ms = float(sd.get('min_gap_ms', 300.0))
    pre_ms = float(sd.get('pre_ms', 250.0))
    post_ms = float(sd.get('post_ms', 450.0))

    if imu_df is None or len(imu_df) == 0:
        return pd.DataFrame(columns=['swing_id', 't_start_ms', 't_peak_ms', 't_end_ms', 'peak_z', 'peak_mag'])

    imu = imu_df.dropna(subset=['ts_ms']).sort_values('ts_ms', kind='mergesort').reset_index(drop=True)
    if len(imu) == 0:
        return pd.DataFrame(columns=['swing_id', 't_start_ms', 't_peak_ms', 't_end_ms', 'peak_z', 'peak_mag'])

    t_ms = imu['ts_ms'].to_numpy(dtype=float)
    t0 = float(t_ms[0])
    t_rel_s = (t_ms - t0) / 1000.0
    for i in range(1, len(t_rel_s)):
        if t_rel_s[i] <= t_rel_s[i - 1]:
            t_rel_s[i] = t_rel_s[i - 1] + 1e-9

    if use_gyro:
        mag = np.sqrt(imu['gx'].to_numpy(float) ** 2 + imu['gy'].to_numpy(float) ** 2 + imu['gz'].to_numpy(float) ** 2)
    else:
        mag = np.sqrt(imu['ax'].to_numpy(float) ** 2 + imu['ay'].to_numpy(float) ** 2 + imu['az'].to_numpy(float) ** 2)

    total_s = float(np.nanmax(t_rel_s)) if len(t_rel_s) else baseline_s
    b_s = min(baseline_s, max(0.2 * total_s, 0.5))
    z, _, _ = robust_zscore(mag, t_rel_s <= b_s)

    active = z > z_thr
    if min_consec > 1:
        run = 0
        flags = np.zeros_like(active, dtype=bool)
        for i, v in enumerate(active):
            run = run + 1 if v else 0
            flags[i] = run >= min_consec
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
        return pd.DataFrame(columns=['swing_id', 't_start_ms', 't_peak_ms', 't_end_ms', 'peak_z', 'peak_mag'])

    # enforce min gap
    peaks = sorted(peaks, key=lambda k: t_ms[k])
    kept = []
    last_t = -1e18
    for k in peaks:
        if (t_ms[k] - last_t) >= min_gap_ms:
            kept.append(k)
            last_t = t_ms[k]
        else:
            if kept and z[k] > z[kept[-1]]:
                kept[-1] = k
                last_t = t_ms[k]

    rows = []
    for sid, k in enumerate(kept):
        tp = float(t_ms[k])
        rows.append({
            'swing_id': int(sid),
            't_start_ms': tp - pre_ms,
            't_peak_ms': tp,
            't_end_ms': tp + post_ms,
            'peak_z': float(z[k]),
            'peak_mag': float(mag[k]),
        })

    out = pd.DataFrame(rows).sort_values('t_start_ms').reset_index(drop=True)
    out['swing_id'] = np.arange(len(out), dtype=int)
    return out


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
    for ii, r in enumerate(swings.to_dict('records'), start=1):
        if n >= 50 and (ii % 25 == 0 or ii == n):
            log(f'  per-swing EMG features: {ii}/{n}')

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
            mav = float(np.mean(np.abs(proc)))
            rms = float(np.sqrt(np.mean(proc * proc)))
            wl = float(np.sum(np.abs(np.diff(proc))))
            s = proc - float(np.mean(proc))
            zc = float(np.sum(((s[:-1] * s[1:]) < 0) & (np.abs(s[:-1] - s[1:]) > zc_thr))) if s.size > 2 else np.nan
            a = s[1:-1] - s[:-2]
            b = s[1:-1] - s[2:]
            ssc = float(np.sum((a * b > 0) & (np.abs(a) > ssc_thr) & (np.abs(b) > ssc_thr))) if s.size > 3 else np.nan
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
    b = cfg.get('baseline', {})
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
    base: Dict[str, float] = {}
    for k in ['mdf', 'rms', 'mav', 'wl', 'emg_env_mean', 'emg_iemg']:
        if k in df.columns:
            base[k] = float(np.nanmedian(df[k].to_numpy(dtype=float)))
    return base


def apply_deltas(df: pd.DataFrame, base: Dict[str, float], prefix: str = '') -> pd.DataFrame:
    out = df.copy()
    if not base:
        return out
    if 'mdf' in out.columns and base.get('mdf', 0):
        out[prefix + 'mdf_drop_pct'] = (base['mdf'] - out['mdf']) / base['mdf'] * 100.0
    if 'rms' in out.columns and base.get('rms', 0):
        out[prefix + 'rms_increase_pct'] = (out['rms'] - base['rms']) / base['rms'] * 100.0
    return out


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


def main():
    ap = argparse.ArgumentParser(description='YAML-driven EMG/IMU analysis for new btCentral capture format')
    ap.add_argument('--config', default='config.yaml', help='Path to YAML config')
    ap.add_argument('--log-dir', required=True, help='Directory containing btCentral logs (rotated emg_log_*, imu_log_*)')
    ap.add_argument('--out-dir', default=None, help='Override output directory (else session.out_dir)')
    args = ap.parse_args()

    cfg = load_config(args.config)
    sess_cfg = cfg.get('session', {})

    out_root = args.out_dir if args.out_dir is not None else sess_cfg.get('out_dir', 'out')
    os.makedirs(out_root, exist_ok=True)

    log(f'Loaded config: {args.config}')
    log(f'Output root: {out_root}')
    log(f'Scanning log_dir: {args.log_dir}')

    sessions = loader.discover_sessions(args.log_dir,
                                        emg_glob=sess_cfg.get('emg_glob', 'emg_log_*.csv'),
                                        imu_glob=sess_cfg.get('imu_glob', 'imu_log_*.csv'),
                                        vitals_name=sess_cfg.get('vitals_path', 'vitals_log.csv'))
    session_ids = sorted(sessions.keys())
    if not session_ids:
        raise SystemExit('No sessions found')
    log(f'Found {len(session_ids)} session(s): {", ".join(session_ids)}')

    mode = (cfg.get('features', {}) or {}).get('mode', 'both')
    pl = cfg.get('plots', {}) or {}
    diag = cfg.get('diagnostics', {}) or {}
    corr_cfg = (diag.get('emg_imu_correlation', {}) or {})

    for si, session_id in enumerate(session_ids, start=1):
        files = sessions[session_id]
        out_dir = os.path.join(out_root, session_id)
        os.makedirs(out_dir, exist_ok=True)

        log(f'=== [{si}/{len(session_ids)}] Processing session {session_id} ===')
        log(f'EMG files: {len(files.emg_paths)} | IMU files: {len(files.imu_paths)}')

        sdata = loader.summarize_session(files)
        pd.DataFrame([s.__dict__ for s in sdata.emg_segments]).to_csv(os.path.join(out_dir, 'segment_summary_emg.csv'), index=False)
        pd.DataFrame([s.__dict__ for s in sdata.imu_segments]).to_csv(os.path.join(out_dir, 'segment_summary_imu.csv'), index=False)

        # IMU load + activity gating + swing detection
        imu_df = loader.load_imu_concat(files.imu_paths,
                                        use_physical_units=bool(sess_cfg.get('use_physical_units', True)),
                                        acc_fsr_default_g=float(sess_cfg.get('acc_fsr_default_g', 2)),
                                        gyro_fsr_default_dps=float(sess_cfg.get('gyro_fsr_default_dps', 250)))

        # Percentile-based activity gating (gyro_mag) -> ACTIVE segments
        active_segs = activity_segments_from_imu(imu_df, cfg)
        active_segs.to_csv(os.path.join(out_dir, 'active_segments.csv'), index=False)

        # Swing detection on full IMU; then keep only swings whose peak is inside ACTIVE segments
        swings = detect_swings_from_imu(imu_df, cfg)
        if active_segs is not None and len(active_segs):
            swings = filter_df_by_segments(swings.rename(columns={'t_peak_ms':'ts_ms'}), active_segs, t_col='ts_ms').rename(columns={'ts_ms':'t_peak_ms'})

        swings.to_csv(os.path.join(out_dir, 'swing_windows.csv'), index=False)

        # Diagnostics: IMU activity overlay
        plot_imu_activity_overlay(imu_df, active_segs, swings, out_dir, cfg)

        log(f'Detected swings: {len(swings)}')

        # If no swings detected, skip per-swing feature extraction to avoid downstream errors
        if len(swings) == 0:
            bout_df = segment_bouts_from_active(active_segs, swings, cfg)
            bout_df.to_csv(os.path.join(out_dir, 'bout_summary.csv'), index=False)
            with open(os.path.join(out_dir, 'session_summary.json'), 'w', encoding='utf-8') as f:
                json.dump({**sdata.session_summary, 'num_swings': 0, 'num_bouts': int(len(bout_df)), 'num_active_segments': int(len(active_segs)) if active_segs is not None else 0, 'active_total_s': float(active_segs['duration_s'].sum()) if active_segs is not None and len(active_segs) else 0.0, 'activity_thr_high': float(getattr(active_segs, 'attrs', {}).get('thr_high', np.nan)), 'activity_thr_low': float(getattr(active_segs, 'attrs', {}).get('thr_low', np.nan)), 'mode': mode}, f, indent=2)
            log(f'Finished session {session_id} (no swings). Outputs -> {out_dir}')
            continue


        # Fast mode: skip heavy work
        if mode == 'bout':
            bout_df = segment_bouts_from_active(active_segs, swings, cfg)
            bout_df.to_csv(os.path.join(out_dir, 'bout_summary.csv'), index=False)
            with open(os.path.join(out_dir, 'session_summary.json'), 'w', encoding='utf-8') as f:
                json.dump({**sdata.session_summary, 'num_swings': int(len(swings)), 'num_bouts': int(len(bout_df)), 'mode': mode}, f, indent=2)
            log(f'Finished session {session_id} (fast). Outputs -> {out_dir}')
            continue

        # Default/both mode: per-swing EMG features
        emg_idx = file_time_index(files.emg_paths, time_col='dev_us')
        swing_feat_df = per_swing_emg_features(swings, emg_idx, cfg)
        # baseline
        session_t0_ms = float(sdata.session_summary.get('session_start_dev_us', 0) / 1000.0)
        base_sw = select_baseline_swings(swings, session_t0_ms=session_t0_ms, cfg=cfg)
        base_feats = swing_feat_df[swing_feat_df['swing_id'].isin(base_sw['swing_id'])]
        base = baseline_from_features(base_feats)
        swing_feat_df = apply_deltas(swing_feat_df, base, prefix='swing_')
        swing_feat_df.to_csv(os.path.join(out_dir, 'swing_features.csv'), index=False)
        with open(os.path.join(out_dir, 'baseline.json'), 'w', encoding='utf-8') as f:
            json.dump({'baseline': base, 'selected_swings': base_sw.to_dict('records')}, f, indent=2)

        # bouts
        bout_df = segment_bouts_from_active(active_segs, swings, cfg)
        bout_df.to_csv(os.path.join(out_dir, 'bout_summary.csv'), index=False)

        # windowed features for plots + correlation
        if bool(pl.get('enable', False)):
            emg_df = loader.load_emg_concat(files.emg_paths, usecols=['dev_us', 'env', 'raw', 'ref'])
            emg_imu_df = loader.make_interleaved_df(emg_df, imu_df)
            res = core.compute(emg_imu_df,
                               emg_fs_hz=float(sess_cfg.get('emg_fs_hz', 2000)),
                               win_sec=float(pl.get('win_sec', 1.0)),
                               step_sec=float(pl.get('step_sec', 0.25)))

            if bool(corr_cfg.get('enable', False)):
                save_emg_imu_correlation(res.feats, out_dir,
                                         method=str(corr_cfg.get('method', 'pearson')),
                                         fname=str(corr_cfg.get('save_name', 'emg_imu_correlation.json')))
                log('Saved emg_imu_correlation.json')

            # plots + fatigue using existing emg_util functions
            core.plot_all(res,
                          emg_fs_hz=float(sess_cfg.get('emg_fs_hz', 2000)),
                          title=f'EMG/IMU summary session={session_id}',
                          full_duration=bool(pl.get('full_duration', True)),
                          emg_max_points=int(pl.get('emg_max_points', 300000)),
                          save_dir=out_dir,
                          silent=True)
            if bool(pl.get('do_fatigue', False)):
                core.analyze_fatigue(res.feats, save_dir=out_dir)

        # session summary
        with open(os.path.join(out_dir, 'session_summary.json'), 'w', encoding='utf-8') as f:
            json.dump({**sdata.session_summary, 'num_swings': int(len(swings)), 'num_bouts': int(len(bout_df)), 'mode': mode}, f, indent=2)

        log(f'Finished session {session_id}. Outputs -> {out_dir}')


if __name__ == '__main__':
    main()
