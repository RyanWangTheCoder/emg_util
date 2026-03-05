#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""capture_loader.py

Loader/adapter for the NEW btCentral.py capture format:
- Rotated EMG CSVs:  emg_log_<SESSIONID>_<OPENID>_<idx>.csv
- Rotated IMU CSVs:  imu_log_<SESSIONID>_<OPENID>_<idx>.csv
- Optional vitals:    vitals_log.csv

This module is intentionally *I/O + alignment + scaling only*.
All DSP / feature extraction remains in emg_util.py.

Time base:
- Uses device-derived timestamps (dev_us) as canonical.
- Provides derived ts_ms for compatibility with existing analysis paths.

IMU scaling:
- Converts raw counts to physical units by default using per-row FSR columns:
  acc_fsr_g, gyro_fsr_dps.

"""

from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# Filename patterns produced by btCentral.py.
# open_id may be YYYYMMDD_HHMMSS (old) or YYYYMMDD_HHMMSS_mmm (new — millisecond
# suffix added to avoid rare same-second rotation collisions).
_RE_EMG = re.compile(r"^emg_log_(\d{8}_\d{6})_(\d{8}_\d{6}(?:_\d{3})?)_(\d{3})\.csv$")
_RE_IMU = re.compile(r"^imu_log_(\d{8}_\d{6})_(\d{8}_\d{6}(?:_\d{3})?)_(\d{3})\.csv$")


@dataclass
class SegmentSummary:
    kind: str  # 'emg' or 'imu'
    path: str
    session_id: str
    open_id: str
    index: int
    start_dev_us: int
    end_dev_us: int
    duration_s: float
    n_rows: int
    est_rate_hz: float


@dataclass
class SessionFiles:
    session_id: str
    emg_paths: List[str]
    imu_paths: List[str]
    vitals_path: Optional[str]


@dataclass
class SessionData:
    session_id: str
    emg_paths: List[str]
    imu_paths: List[str]
    vitals_path: Optional[str]
    emg_segments: List[SegmentSummary]
    imu_segments: List[SegmentSummary]
    session_summary: Dict


def _acc_lsb_per_g(acc_fsr_g: float) -> float:
    # ICM-20948 mapping used in btCentral.py
    m = {2.0: 16384.0, 4.0: 8192.0, 8.0: 4096.0, 16.0: 2048.0}
    return float(m.get(float(acc_fsr_g), 16384.0))


def _gyro_lsb_per_dps(gyro_fsr_dps: float) -> float:
    m = {250.0: 131.0, 500.0: 65.5, 1000.0: 32.8, 2000.0: 16.4}
    return float(m.get(float(gyro_fsr_dps), 131.0))


def discover_sessions(log_dir: str,
                      emg_glob: str = "emg_log_*.csv",
                      imu_glob: str = "imu_log_*.csv",
                      vitals_name: str = "vitals_log.csv") -> Dict[str, SessionFiles]:
    """Discover all sessions in a directory.

    Returns mapping: session_id -> SessionFiles.
    """
    log_dir = os.path.abspath(log_dir)
    emg_paths = sorted(glob.glob(os.path.join(log_dir, emg_glob)))
    imu_paths = sorted(glob.glob(os.path.join(log_dir, imu_glob)))

    by_session: Dict[str, Dict[str, List[str]]] = {}

    def add_path(p: str, kind: str):
        base = os.path.basename(p)
        m = _RE_EMG.match(base) if kind == 'emg' else _RE_IMU.match(base)
        if not m:
            return
        session_id, open_id, idx = m.group(1), m.group(2), int(m.group(3))
        d = by_session.setdefault(session_id, {'emg': [], 'imu': []})
        d[kind].append(p)

    for p in emg_paths:
        add_path(p, 'emg')
    for p in imu_paths:
        add_path(p, 'imu')

    vitals_path = os.path.join(log_dir, vitals_name)
    vitals_exists = os.path.exists(vitals_path)

    out: Dict[str, SessionFiles] = {}
    for session_id, d in by_session.items():
        # sort each list by open_id then idx using filename regex
        def sort_key(path: str):
            b = os.path.basename(path)
            mm = _RE_EMG.match(b) or _RE_IMU.match(b)
            if not mm:
                return ("", 0)
            return (mm.group(2), int(mm.group(3)))

        emg_sorted = sorted(d['emg'], key=sort_key)
        imu_sorted = sorted(d['imu'], key=sort_key)
        out[session_id] = SessionFiles(
            session_id=session_id,
            emg_paths=emg_sorted,
            imu_paths=imu_sorted,
            vitals_path=(vitals_path if vitals_exists else None)
        )
    return out


def _summarize_segment(path: str, kind: str) -> SegmentSummary:
    base = os.path.basename(path)
    m = _RE_EMG.match(base) if kind == 'emg' else _RE_IMU.match(base)
    if not m:
        raise ValueError(f"Unrecognized {kind} filename: {base}")
    session_id, open_id, idx = m.group(1), m.group(2), int(m.group(3))

    # Read dev_us only (fast)
    df = pd.read_csv(path, usecols=['dev_us'], engine='python')
    dev = pd.to_numeric(df['dev_us'], errors='coerce').dropna().astype(np.int64)
    n_rows = int(len(dev))
    if n_rows == 0:
        start = end = 0
        dur_s = 0.0
        est_rate = 0.0
    else:
        start = int(dev.min())
        end = int(dev.max())
        dur_s = float(max(end - start, 0)) / 1e6
        est_rate = float((n_rows - 1) / dur_s) if dur_s > 1e-9 else 0.0

    return SegmentSummary(
        kind=kind,
        path=path,
        session_id=session_id,
        open_id=open_id,
        index=idx,
        start_dev_us=start,
        end_dev_us=end,
        duration_s=dur_s,
        n_rows=n_rows,
        est_rate_hz=est_rate
    )


def summarize_session(files: SessionFiles) -> SessionData:
    """Compute per-file segment summaries and a session-level summary."""
    emg_segs = [_summarize_segment(p, 'emg') for p in files.emg_paths]
    imu_segs = [_summarize_segment(p, 'imu') for p in files.imu_paths]

    def gaps(segs: List[SegmentSummary]) -> Dict[str, float]:
        segs2 = sorted(segs, key=lambda s: (s.start_dev_us, s.end_dev_us))
        if len(segs2) <= 1:
            return {'n_gaps': 0, 'total_gap_s': 0.0, 'max_gap_s': 0.0}
        g = []
        prev_end = segs2[0].end_dev_us
        for s in segs2[1:]:
            if s.start_dev_us > prev_end:
                g.append((s.start_dev_us - prev_end) / 1e6)
            prev_end = max(prev_end, s.end_dev_us)
        if not g:
            return {'n_gaps': 0, 'total_gap_s': 0.0, 'max_gap_s': 0.0}
        return {'n_gaps': int(len(g)), 'total_gap_s': float(np.sum(g)), 'max_gap_s': float(np.max(g))}

    # Session overall time span across EMG+IMU (if present)
    starts = [s.start_dev_us for s in emg_segs + imu_segs if s.n_rows > 0]
    ends = [s.end_dev_us for s in emg_segs + imu_segs if s.n_rows > 0]
    if starts and ends:
        session_start = int(min(starts))
        session_end = int(max(ends))
        session_dur_s = float(max(session_end - session_start, 0)) / 1e6
    else:
        session_start = session_end = 0
        session_dur_s = 0.0

    summary = {
        'session_id': files.session_id,
        'n_emg_files': int(len(files.emg_paths)),
        'n_imu_files': int(len(files.imu_paths)),
        'session_start_dev_us': session_start,
        'session_end_dev_us': session_end,
        'session_duration_s': session_dur_s,
        'emg_gaps': gaps(emg_segs),
        'imu_gaps': gaps(imu_segs),
    }

    return SessionData(
        session_id=files.session_id,
        emg_paths=files.emg_paths,
        imu_paths=files.imu_paths,
        vitals_path=files.vitals_path,
        emg_segments=emg_segs,
        imu_segments=imu_segs,
        session_summary=summary
    )


def load_emg_concat(paths: List[str], usecols: Optional[List[str]] = None) -> pd.DataFrame:
    """Load and concatenate EMG CSVs, sorted by dev_us.

    Default columns: dev_us, env, raw, ref.
    Adds derived ts_ms column.
    """
    if usecols is None:
        usecols = ['dev_us', 'env', 'raw', 'ref', 'host_rx_ms']
    parts = []
    for p in paths:
        df = pd.read_csv(p, usecols=usecols, engine='python')
        for c in usecols:
            df[c] = pd.to_numeric(df[c], errors='coerce')
        df = df.dropna(subset=['dev_us'])
        parts.append(df)
    if not parts:
        return pd.DataFrame(columns=['dev_us', 'ts_ms', 'env', 'raw', 'ref'])
    out = pd.concat(parts, ignore_index=True)
    out = out.sort_values('dev_us', kind='mergesort').reset_index(drop=True)
    out['dev_us'] = out['dev_us'].astype(np.int64)
    out['ts_ms'] = out['dev_us'].astype(np.float64) / 1000.0
    return out


def load_imu_concat(paths: List[str],
                    use_physical_units: bool = True,
                    acc_fsr_default_g: float = 4.0,    # matches firmware IMU_ACC_FSR_G=4
                    gyro_fsr_default_dps: float = 1000.0,  # matches firmware IMU_GYRO_FSR_DPS=1000
                    usecols: Optional[List[str]] = None) -> pd.DataFrame:
    """Load and concatenate IMU CSVs, sorted by dev_us.

    If use_physical_units=True, converts ax..az to g and gx..gz to dps.
    Adds derived ts_ms column.
    """
    if usecols is None:
        usecols = ['dev_us', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 'acc_fsr_g', 'gyro_fsr_dps', 'host_rx_ms']
    parts = []
    for p in paths:
        df = pd.read_csv(p, usecols=usecols, engine='python')
        for c in usecols:
            df[c] = pd.to_numeric(df[c], errors='coerce')
        df = df.dropna(subset=['dev_us'])
        parts.append(df)
    if not parts:
        cols = ['dev_us', 'ts_ms', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 'acc_fsr_g', 'gyro_fsr_dps']
        return pd.DataFrame(columns=cols)
    out = pd.concat(parts, ignore_index=True)
    out = out.sort_values('dev_us', kind='mergesort').reset_index(drop=True)
    out['dev_us'] = out['dev_us'].astype(np.int64)
    out['ts_ms'] = out['dev_us'].astype(np.float64) / 1000.0

    # Fill FSR missing values with forward-fill, then defaults
    if 'acc_fsr_g' in out.columns:
        out['acc_fsr_g'] = out['acc_fsr_g'].ffill().fillna(acc_fsr_default_g)
    else:
        out['acc_fsr_g'] = float(acc_fsr_default_g)

    if 'gyro_fsr_dps' in out.columns:
        out['gyro_fsr_dps'] = out['gyro_fsr_dps'].ffill().fillna(gyro_fsr_default_dps)
    else:
        out['gyro_fsr_dps'] = float(gyro_fsr_default_dps)

    if use_physical_units:
        # Map FSR to scale factors
        acc_lsb = out['acc_fsr_g'].map(lambda v: _acc_lsb_per_g(v)).astype(np.float64)
        gyr_lsb = out['gyro_fsr_dps'].map(lambda v: _gyro_lsb_per_dps(v)).astype(np.float64)
        for c in ['ax', 'ay', 'az']:
            out[c] = out[c].astype(np.float64) / acc_lsb
        for c in ['gx', 'gy', 'gz']:
            out[c] = out[c].astype(np.float64) / gyr_lsb

    return out


def load_vitals(path: str) -> pd.DataFrame:
    """Load vitals_log.csv if present."""
    if path is None or (not os.path.exists(path)):
        return pd.DataFrame()
    df = pd.read_csv(path, engine='python')
    # Attempt to standardize a time column: prefer dev_us_computed if present
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='ignore')
    # Provide ts_ms if we can
    if 'dev_us_computed' in df.columns:
        df['ts_ms'] = pd.to_numeric(df['dev_us_computed'], errors='coerce') / 1000.0
    elif 'dev_us_frame' in df.columns:
        df['ts_ms'] = pd.to_numeric(df['dev_us_frame'], errors='coerce') / 1000.0
    return df


# ============================
# NEW: Stitched session loader
# Treats all BLE connections in a folder as one continuous tennis session.
# Uses wall-clock session_id timestamps to compute absolute time offsets,
# correctly handling device reboots between BLE connections.
# ============================

def _parse_session_datetime(session_id: str):
    """Parse session_id (YYYYMMDD_HHMMSS) as a datetime object."""
    from datetime import datetime
    return datetime.strptime(session_id, '%Y%m%d_%H%M%S')


def load_session_stitched(
    sessions: Dict[str, 'SessionFiles'],
    use_physical_units: bool = True,
    acc_fsr_default_g: float = 4.0,    # matches firmware IMU_ACC_FSR_G=4
    gyro_fsr_default_dps: float = 1000.0,  # matches firmware IMU_GYRO_FSR_DPS=1000
) -> Tuple[pd.DataFrame, pd.DataFrame, List[float], List[str]]:
    """Load all BLE connections in a folder as one stitched tennis session.

    Each BLE connection has its own device clock (dev_us = microseconds since
    device boot). This function builds a reconstructed physical timeline (abs_us)
    using a hybrid approach:

    Within each connection:
        Uses dev_us for intra-sample timing -- accurate physical time with no
        BLE transmission jitter. dev_us is already 64-bit extended by
        DeviceClockExtender on the host so 32-bit rollover (~71min) is handled.

    Between connections:
        Uses host_rx_ms gap between the last sample of connection N and the
        first sample of connection N+1. This gives the actual BLE gap in
        milliseconds and is correct regardless of whether the ESP32 reset or
        not, and regardless of the DeviceClockExtender 71-min residual offset.

    This is simpler and more robust than trying to detect BLE-dropout-only vs
    ESP32-reset from dev_us continuity.

    The returned DataFrames have:
      - abs_us  : absolute microseconds from the start of the tennis session
      - ts_ms   : abs_us / 1000.0  (for compatibility with existing analysis)
      - session_id : which BLE connection this row came from
      - capture_idx: integer index (0 = first connection, 1 = second, ...)

    Args:
        sessions: dict of session_id -> SessionFiles (from discover_sessions())
        use_physical_units: convert IMU raw counts to g / dps
        acc_fsr_default_g: default accelerometer FSR if not in CSV
        gyro_fsr_default_dps: default gyroscope FSR if not in CSV

    Returns:
        emg_df            : stitched EMG DataFrame
        imu_df            : stitched IMU DataFrame
        reconnection_times_s : list of reconnection times in seconds from
                               session start (one entry per BLE connection
                               after the first)
        capture_ids       : list of session_ids in chronological order
    """
    # Sort BLE connections by wall-clock time (session_id = YYYYMMDD_HHMMSS)
    sorted_items = sorted(sessions.items(), key=lambda x: _parse_session_datetime(x[0]))
    if not sorted_items:
        empty = pd.DataFrame()
        return empty, empty, [], []

    emg_parts: List[pd.DataFrame] = []
    imu_parts: List[pd.DataFrame] = []
    reconnection_times_s: List[float] = []
    capture_ids: List[str] = []

    # Running abs_us end of the previous connection for each stream.
    # Used to compute the inter-connection offset for the next connection.
    emg_abs_end_us: int = 0          # abs_us of last EMG sample so far
    imu_abs_end_us: int = 0          # abs_us of last IMU sample so far
    emg_host_end_ms: Optional[float] = None   # host_rx_ms of last EMG sample
    imu_host_end_ms: Optional[float] = None   # host_rx_ms of last IMU sample

    for i, (session_id, files) in enumerate(sorted_items):
        capture_ids.append(session_id)

        # --- Load EMG ---
        if files.emg_paths:
            emg = load_emg_concat(files.emg_paths)
            if len(emg) > 0:
                dev_start = int(emg['dev_us'].min())
                # Intra-connection time: dev_us relative to this connection's start
                dev_rel = emg['dev_us'].astype(np.int64) - dev_start
                if i == 0:
                    # First connection: abs_us starts at 0
                    emg['abs_us'] = dev_rel
                else:
                    # Inter-connection gap from host_rx_ms (ms resolution).
                    # Works for both BLE-dropout-only and ESP32-reset cases.
                    host_start_ms = float(emg['host_rx_ms'].iloc[0]) if 'host_rx_ms' in emg.columns and emg['host_rx_ms'].notna().any() else None
                    if host_start_ms is not None and emg_host_end_ms is not None:
                        gap_us = max(0, int((host_start_ms - emg_host_end_ms) * 1000))
                    else:
                        gap_us = 0  # fallback: no gap (conservative)
                    emg['abs_us'] = emg_abs_end_us + gap_us + dev_rel
                    reconnection_times_s.append(float(emg_abs_end_us + gap_us) / 1e6)
                emg_abs_end_us  = int(emg['abs_us'].max())
                emg_host_end_ms = float(emg['host_rx_ms'].iloc[-1]) if 'host_rx_ms' in emg.columns and emg['host_rx_ms'].notna().any() else None
                emg['session_id'] = session_id
                emg['capture_idx'] = i
                emg_parts.append(emg)

        # --- Load IMU ---
        if files.imu_paths:
            imu = load_imu_concat(
                files.imu_paths,
                use_physical_units=use_physical_units,
                acc_fsr_default_g=acc_fsr_default_g,
                gyro_fsr_default_dps=gyro_fsr_default_dps,
            )
            if len(imu) > 0:
                dev_start_imu = int(imu['dev_us'].min())
                dev_rel_imu   = imu['dev_us'].astype(np.int64) - dev_start_imu
                if i == 0:
                    imu['abs_us'] = dev_rel_imu
                else:
                    host_start_ms_imu = float(imu['host_rx_ms'].iloc[0]) if 'host_rx_ms' in imu.columns and imu['host_rx_ms'].notna().any() else None
                    if host_start_ms_imu is not None and imu_host_end_ms is not None:
                        gap_us_imu = max(0, int((host_start_ms_imu - imu_host_end_ms) * 1000))
                    else:
                        gap_us_imu = 0
                    imu['abs_us'] = imu_abs_end_us + gap_us_imu + dev_rel_imu
                    # Only append reconnection time once (use IMU if EMG not present)
                    if not files.emg_paths:
                        reconnection_times_s.append(float(imu_abs_end_us + gap_us_imu) / 1e6)
                imu_abs_end_us  = int(imu['abs_us'].max())
                imu_host_end_ms = float(imu['host_rx_ms'].iloc[-1]) if 'host_rx_ms' in imu.columns and imu['host_rx_ms'].notna().any() else None
                imu['session_id'] = session_id
                imu['capture_idx'] = i
                imu_parts.append(imu)

    # Concatenate and sort by absolute time
    if emg_parts:
        emg_out = (pd.concat(emg_parts, ignore_index=True)
                   .sort_values('abs_us', kind='mergesort')
                   .reset_index(drop=True))
        emg_out['ts_ms'] = emg_out['abs_us'].astype(np.float64) / 1000.0
    else:
        emg_out = pd.DataFrame()

    if imu_parts:
        imu_out = (pd.concat(imu_parts, ignore_index=True)
                   .sort_values('abs_us', kind='mergesort')
                   .reset_index(drop=True))
        imu_out['ts_ms'] = imu_out['abs_us'].astype(np.float64) / 1000.0
    else:
        imu_out = pd.DataFrame()

    return emg_out, imu_out, reconnection_times_s, capture_ids


def make_interleaved_df(emg_df: pd.DataFrame, imu_df: pd.DataFrame) -> pd.DataFrame:
    """Create an interleaved dataframe compatible with legacy analysis paths.

    Produces a dataframe with columns including:
      ts_ms, env, raw, ref, ax..gz
    with EMG rows having NaNs for IMU columns and vice versa.

    This does NOT change the source format externally; it is only for reuse
    of existing compute/plot routines.
    """
    # Normalize columns
    emg = emg_df.copy()
    imu = imu_df.copy()

    # Ensure required columns exist
    for c in ['ts_ms', 'env', 'raw', 'ref']:
        if c not in emg.columns:
            emg[c] = np.nan
    for c in ['ts_ms', 'ax', 'ay', 'az', 'gx', 'gy', 'gz']:
        if c not in imu.columns:
            imu[c] = np.nan

    emg_rows = emg[['ts_ms', 'env', 'raw', 'ref']].copy()
    for c in ['ax', 'ay', 'az', 'gx', 'gy', 'gz']:
        emg_rows[c] = np.nan

    imu_rows = imu[['ts_ms', 'ax', 'ay', 'az', 'gx', 'gy', 'gz']].copy()
    for c in ['env', 'raw', 'ref']:
        imu_rows[c] = np.nan

    df = pd.concat([emg_rows, imu_rows], ignore_index=True)
    df['ts_ms'] = pd.to_numeric(df['ts_ms'], errors='coerce')
    df = df.dropna(subset=['ts_ms']).sort_values('ts_ms', kind='mergesort').reset_index(drop=True)
    return df
