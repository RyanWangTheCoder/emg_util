# -*- coding: utf-8 -*-
"""capture_health.py

Lightweight EMG capture health utilities.

Use-case:
- IMU defines swings; EMG can be sporadically bad due to cabling/electrode contact.
- Detect EMG BAD intervals using EMG-only self-health rules (zeros/flatline/gaps)
  so the runner can optionally filter swing windows that overlap BAD intervals.

This module works directly on rotated EMG CSV logs (emg_log_*.csv).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Optional

import numpy as np
import pandas as pd


def _health_cfg(cfg: Dict[str, Any]) -> Dict[str, Any]:
    h = (cfg.get('health', {}) or {}).copy()
    h.setdefault('enable', True)
    h.setdefault('window_s', 1.0)
    h.setdefault('bad_persist_s', 2.0)
    h.setdefault('emg_zero_frac_bad', 0.90)
    h.setdefault('emg_flat_std_bad', 1.0)
    h.setdefault('emg_gap_bad_us', 200_000)
    return h


def _scan_minmax_dev_us(paths: List[str], col: str = 'dev_us', chunksize: int = 1_000_000) -> Tuple[int, int]:
    mn = None
    mx = None
    for p in paths:
        for ch in pd.read_csv(p, usecols=[col], chunksize=chunksize, engine='python'):
            t = pd.to_numeric(ch[col], errors='coerce').dropna().astype(np.int64)
            if len(t) == 0:
                continue
            mn = int(t.min()) if mn is None else min(mn, int(t.min()))
            mx = int(t.max()) if mx is None else max(mx, int(t.max()))
    return (0, 0) if mn is None else (int(mn), int(mx))


def _merge_bad_runs(win_start_us: np.ndarray, win_end_us: np.ndarray, bad: np.ndarray, persist_w: int) -> List[Tuple[int, int]]:
    bad = np.asarray(bad, dtype=bool)
    out: List[Tuple[int, int]] = []
    i = 0
    n = len(bad)
    while i < n:
        if not bad[i]:
            i += 1
            continue
        j = i
        while j < n and bad[j]:
            j += 1
        if (j - i) >= persist_w:
            out.append((int(win_start_us[i]), int(win_end_us[j - 1])))
        i = j
    return out


def emg_bad_intervals_us(emg_paths: List[str], cfg: Dict[str, Any], chunksize: int = 1_000_000) -> List[Tuple[int, int]]:
    """Return list of (start_dev_us, end_dev_us) intervals where EMG is considered BAD."""
    h = _health_cfg(cfg)
    if not emg_paths or not bool(h.get('enable', True)):
        return []

    t0, t1 = _scan_minmax_dev_us(emg_paths, col='dev_us', chunksize=chunksize)
    if t0 == 0 and t1 == 0:
        return []

    win_s = float(h.get('window_s', 1.0))
    win_us = int(round(win_s * 1e6))
    persist_w = int(np.ceil(float(h.get('bad_persist_s', 2.0)) / win_s))

    nwin = int(np.floor((t1 - t0) / win_us)) + 1

    n = np.zeros(nwin, dtype=np.int64)
    zraw = np.zeros(nwin, dtype=np.int64)
    zenv = np.zeros(nwin, dtype=np.int64)
    sraw = np.zeros(nwin, dtype=np.float64)
    ssraw = np.zeros(nwin, dtype=np.float64)
    senv = np.zeros(nwin, dtype=np.float64)
    ssenv = np.zeros(nwin, dtype=np.float64)
    gapmax = np.zeros(nwin, dtype=np.int64)

    prev_t: Optional[int] = None
    prev_w: Optional[int] = None

    usecols = ['dev_us', 'raw', 'env']
    for p in emg_paths:
        for ch in pd.read_csv(p, usecols=lambda c: c in usecols, chunksize=chunksize, engine='python'):
            if 'dev_us' not in ch.columns or 'raw' not in ch.columns:
                continue
            t = pd.to_numeric(ch['dev_us'], errors='coerce').to_numpy(dtype=np.float64)
            raw = pd.to_numeric(ch['raw'], errors='coerce').to_numpy(dtype=np.float64)
            env = pd.to_numeric(ch['env'], errors='coerce').to_numpy(dtype=np.float64) if 'env' in ch.columns else np.full_like(raw, np.nan)

            m = np.isfinite(t)
            if not np.any(m):
                continue
            t = t[m].astype(np.int64)
            raw = raw[m]
            env = env[m]

            w = ((t - t0) // win_us).astype(np.int64)
            w = np.clip(w, 0, nwin - 1)

            for ti, wi, r, e in zip(t, w, raw, env):
                n[wi] += 1
                if np.isfinite(r):
                    if r == 0:
                        zraw[wi] += 1
                    sraw[wi] += r
                    ssraw[wi] += r * r
                if np.isfinite(e):
                    if e == 0:
                        zenv[wi] += 1
                    senv[wi] += e
                    ssenv[wi] += e * e

                if prev_t is not None and prev_w is not None:
                    dt = int(ti - prev_t)
                    if dt > gapmax[prev_w]:
                        gapmax[prev_w] = dt
                prev_t = int(ti)
                prev_w = int(wi)

    with np.errstate(divide='ignore', invalid='ignore'):
        mean_raw = sraw / np.maximum(n, 1)
        var_raw = ssraw / np.maximum(n, 1) - mean_raw * mean_raw
        std_raw = np.sqrt(np.maximum(var_raw, 0.0))

        mean_env = senv / np.maximum(n, 1)
        var_env = ssenv / np.maximum(n, 1) - mean_env * mean_env
        std_env = np.sqrt(np.maximum(var_env, 0.0))

        zero_frac_raw = zraw / np.maximum(n, 1)
        zero_frac_env = zenv / np.maximum(n, 1)

    zero_thr = float(h.get('emg_zero_frac_bad', 0.90))
    flat_thr = float(h.get('emg_flat_std_bad', 1.0))
    gap_thr = int(h.get('emg_gap_bad_us', 200_000))

    env_has = (ssenv != 0) | (senv != 0)

    bad = (n == 0) | (zero_frac_raw >= zero_thr) | (std_raw <= flat_thr) | (gapmax >= gap_thr)
    bad = bad | ((zero_frac_env >= zero_thr) & env_has) | ((std_env <= flat_thr) & env_has)

    win_start = t0 + np.arange(nwin, dtype=np.int64) * win_us
    win_end = np.minimum(win_start + win_us, t1)

    return _merge_bad_runs(win_start, win_end, bad, persist_w=persist_w)


def intervals_overlap(a0: float, a1: float, intervals: List[Tuple[float, float]]) -> bool:
    for b0, b1 in intervals:
        if a1 >= b0 and a0 <= b1:
            return True
    return False
