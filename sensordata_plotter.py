#!/usr/bin/env python3
"""sensordata_plotter.py — Realtime UDP plotter (device-time aligned) + offline viewer + EMG fatigue.

Improvements vs previous device-time plotter:
  1) Works even if started AFTER btCentral: if emg_meta is missed, it infers sr_hz from dev_us deltas.
  2) Still uses emg_meta when available and will reinitialize LPF if sr_hz changes.
  3) Optional real-time EMG fatigue monitoring via FatigueMonitor (--fatigue flag).

UDP messages expected (JSON):
  EMG meta:  {"k":"emg_meta", "sr_hz":<int>, "ch":<int>, "adc_bits":<int>, "ymax":<int>, "seg":<int>}
  EMG raw:   {"k":"raw",  "dev_us":<int>, "raw":<int>,   "seg":<int>, "t":<host_ms optional>}
  EMG env:   {"k":"env",  "dev_us":<int>, "env":<int>,   "seg":<int>, "t":<host_ms optional>}
  IMU:       {"k":"imu",  "dev_us":<int>, "amag":<float>, "gmag":<float>, "seg":<int>}
               amag = accel magnitude (g), gmag = gyro magnitude (dps) -- added by btCentral.py
  Vitals:    {"k":"vitals", "pct":<int>, "v":<float>, "spo2":<int>, "hr":<float>, "seg":<int>}

Fatigue monitoring (--fatigue):
  - Maintains a 2600-sample ring buffer of raw EMG at full rate (1300ms @ 2000Hz, +/-300ms MDF padding)
  - Triggers on IMU gyro magnitude >= --imu-thr-dps (default 150 dps) with 300ms debounce
  - Calls FatigueMonitor.push_swing() in a background thread (same class as Android)
  - Displays: text annotation on EMG plot + 3rd MDF trend subplot
  - FatigueMonitor is imported from fatigue_monitor.py (--emg-util-path points to emg_util/ dir)

Usage (live with fatigue):
  python sensordata_plotter.py --mode live --fatigue --imu-thr-dps 150 --fatigue-warmup-min 0

Offline fatigue replay (--mode offline --fatigue):
  Reads EMG + IMU CSV files, feeds them through the same run_live() pipeline via CsvReplayFeeder.
  All fatigue logic (ring buffer, peak detection, FatigueMonitor, MDF trend) is reused exactly.

  Instant replay (all data at once, animation scrolls to end):
    python sensordata_plotter.py --mode offline --fatigue \\
        --emg-file logs/emg_log_*.csv --imu-file logs/imu_log_*.csv

  Instant replay + freeze x-axis at end to show full session:
    python sensordata_plotter.py --mode offline --fatigue --replay-no-scroll \\
        --emg-file logs/emg_log_*.csv --imu-file logs/imu_log_*.csv

  Real-time replay at 2× speed:
    python sensordata_plotter.py --mode offline --fatigue --replay-speed 2.0 \\
        --emg-file logs/emg_log_*.csv --imu-file logs/imu_log_*.csv
"""

import argparse
import csv
import json
import os
import queue
import socket
import sys
import threading
import time
from collections import deque

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


# ---------------------------------------------------------------------------
# FatigueMonitor import (optional -- graceful fallback if not found)
# ---------------------------------------------------------------------------
_FatigueMonitor = None  # set by _try_import_fatigue_monitor()


def _try_import_fatigue_monitor(path: str) -> bool:
    """Try to import FatigueMonitor from fatigue_monitor.py at the given directory path.

    fatigue_monitor.py is the canonical source (emg_util/fatigue_monitor.py).
    It is self-contained: zero pandas/matplotlib dependency.
    """
    global _FatigueMonitor
    resolved = os.path.normpath(path) if path else ''
    if resolved and os.path.isdir(resolved):
        if resolved not in sys.path:
            sys.path.insert(0, resolved)
    try:
        from fatigue_monitor import FatigueMonitor as _FM
        _FatigueMonitor = _FM
        print(f'[Fatigue] Loaded FatigueMonitor from fatigue_monitor at {resolved}')
        return True
    except ImportError as e:
        print(f'[Fatigue] WARNING: Could not import FatigueMonitor from fatigue_monitor at {resolved!r}: {e}')
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description='Realtime UDP plotter (device-time aligned, robust meta)')
    ap.add_argument('--mode', choices=['live', 'offline'], default='live')
    ap.add_argument('--listen-host', default='127.0.0.1')
    ap.add_argument('--listen-port', type=int, default=9999)

    ap.add_argument('--emg-window-sec', type=float, default=2.0)
    ap.add_argument('--imu-window-sec', type=float, default=None)
    ap.add_argument('--fps', type=float, default=30.0)

    ap.add_argument('--emg-ymax', type=float, default=4095.0)
    ap.add_argument('--raw-zoom', action='store_true',
                    help='Enable dynamic Y-axis zoom for RAW plot (live mode) or +/-500 zoom (offline mode)')
    ap.add_argument('--cutoff-hz', type=float, default=3.6)

    # Meta inference
    ap.add_argument('--infer-sr', action='store_true',
                    help='Infer sr_hz from dev_us deltas if emg_meta missed')
    ap.add_argument('--infer-min-hz', type=float, default=100.0)
    ap.add_argument('--infer-max-hz', type=float, default=4000.0)
    ap.add_argument('--infer-min-samples', type=int, default=30)

    # Offline
    ap.add_argument('--emg-file', default=None)
    ap.add_argument('--imu-file', default=None)
    ap.add_argument('--max-points', type=int, default=400000)
    ap.add_argument('--sr-hz', type=float, default=2000.0)

    # Fatigue monitoring
    ap.add_argument('--fatigue', action='store_true',
                    help='Enable real-time EMG fatigue monitoring')
    ap.add_argument('--emg-util-path', default=None,
                    help='Path to directory containing emg_util.py '
                         '(default: ../../emg_util relative to this script)')
    ap.add_argument('--imu-thr-dps', type=float, default=150.0,
                    help='Gyro magnitude trigger threshold in dps (default 150)')
    ap.add_argument('--fatigue-warmup-min', type=float, default=0.0,
                    help='Warmup skip before baseline collection in minutes '
                         '(default 0 = start immediately; use 5.0 for real sessions)')
    ap.add_argument('--fatigue-baseline-swings', type=int, default=20,
                    help='Number of swings to collect for baseline (default 20)')

    # CSV replay (--mode offline --fatigue)
    ap.add_argument('--replay-speed', type=float, default=0.0,
                    help='CSV replay speed multiplier (0=instant dump, 1.0=realtime, 2.0=2×). '
                         'Only used with --mode offline --fatigue.')
    ap.add_argument('--replay-no-scroll', action='store_true',
                    help='After CSV replay finishes, freeze x-axis to show full session. '
                         'Only used with --mode offline --fatigue.')

    return ap.parse_args()


# ---------------------------------------------------------------------------
# Butterworth LPF (causal, sample-by-sample)
# ---------------------------------------------------------------------------

class ButterLPF:
    def __init__(self, fs_hz: float, cutoff_hz: float = 3.6):
        from scipy.signal import butter, lfilter_zi
        self.fs_hz = float(fs_hz)
        self.cutoff_hz = float(cutoff_hz)
        self.b, self.a = butter(2, self.cutoff_hz / (self.fs_hz / 2.0), btype='low')
        self.zi = lfilter_zi(self.b, self.a) * 0.0

    def update(self, x: float) -> float:
        from scipy.signal import lfilter
        y, self.zi = lfilter(self.b, self.a, [float(x)], zi=self.zi)
        return float(max(y[0], 0.0))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_env_sw_scale(env_hw_max: float, env_sw_max: float) -> float:
    """Scale factor to match ENV_sw's dynamic range to ENV_hw's.

    Returns max(ENV_hw) / max(ENV_sw), or 1.0 if ENV_sw is near zero.
    Used identically in live mode (wrapped in EMA) and offline mode (applied once).
    """
    return (env_hw_max / env_sw_max) if env_sw_max > 1.0 else 1.0


def infer_sr_from_dev_us(dev_us_list, min_hz: float, max_hz: float):
    if len(dev_us_list) < 3:
        return None
    diffs = np.diff(np.array(dev_us_list, dtype=np.int64))
    diffs = diffs[diffs > 0]
    if diffs.size < 3:
        return None
    dt_us = float(np.median(diffs))
    if dt_us <= 0:
        return None
    sr = 1_000_000.0 / dt_us
    if sr < min_hz or sr > max_hz:
        return None
    return float(int(round(sr)))


# ---------------------------------------------------------------------------
# Live mode
# ---------------------------------------------------------------------------

def run_live(args: argparse.Namespace, recv_fn=None, feeder=None) -> None:
    if recv_fn is None:
        # Normal live UDP mode
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((args.listen_host, int(args.listen_port)))
        sock.setblocking(False)
        def recv_fn():
            data, _addr = sock.recvfrom(8192)
            return data

    raw_buf = deque()
    env_dev_buf = deque()
    env_lpf_buf = deque()
    imu_buf = deque()
    gyro_buf = deque()   # gyro magnitude (dps) — separate from imu_buf (acc, g)

    # Track recent raw dev_us to infer sr_hz if needed
    recent_raw_dev_us = deque(maxlen=200)

    t0_dev_us = None
    emg_sr_hz = None
    emg_ch = None
    env_filter = None
    last_vitals = {}

    # DC offset tracker: slow LPF (0.1 Hz) to estimate RAW's true midpoint.
    # MyoWare DC bias shifts center from theoretical 2048 to ~1830-1843.
    # Initialized to 1843 (typical observed value) to minimize convergence time.
    # alpha = 1 - exp(-2pi * 0.1 / sr_hz); set when sr_hz is known.
    raw_dc_state = {'lpf': 1843.0, 'alpha': None}

    emg_win = float(args.emg_window_sec)
    imu_win = float(args.imu_window_sec) if args.imu_window_sec is not None else emg_win

    # -----------------------------------------------------------------------
    # Fatigue monitoring setup
    # -----------------------------------------------------------------------
    # EMG ring buffer: 2600 samples = 1300ms at 2000Hz (includes +/-300ms MDF padding)
    # Matches Android emgFatigueBuf exactly.
    EMG_FATIGUE_BUF_SIZE = 2600
    fatigue_enabled = bool(args.fatigue)
    monitor = None
    fatigue_q = None
    fatigue_lock = threading.Lock()
    # Shared result dict updated by fatigue_worker, read by animation update()
    fatigue_result = {
        'swing_id': -1,
        'mdf': None,
        'mdf_drop_pct': None,
        'fatigue_level': 'warming_up',
        'warning': False,
        'baseline_ready': False,
        'baseline_swings_collected': 0,
        'baseline_mdf': None,
        'history': [],   # list of {t_peak_ms, mdf, mdf_drop_pct, fatigue_level}
    }
    emg_fatigue_buf = deque(maxlen=EMG_FATIGUE_BUF_SIZE)

    # Peak detection state (matches Android implementation)
    last_imu_trigger_t = [-999.0]   # mutable container (avoids nonlocal float)
    imu_thr_dps = float(args.imu_thr_dps)
    in_peak = [False]           # mutable: currently tracking a peak
    peak_gyro_mag = [0.0]       # mutable: highest gyro value in current peak
    peak_time_sec = [0.0]       # mutable: time of peak
    swing_count = [0]           # mutable: total swings detected this session

    if fatigue_enabled:
        util_path = args.emg_util_path
        if util_path is None:
            # Default: ../../emg_util relative to this script (C:\wangx\ftc\emg_util)
            util_path = os.path.normpath(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..', '..', 'emg_util',
            ))
        if _try_import_fatigue_monitor(util_path):
            monitor = _FatigueMonitor(
                fs=2000.0,   # updated when emg_meta arrives with actual sr_hz
                warmup_skip_min=float(args.fatigue_warmup_min),
                baseline_swings=int(args.fatigue_baseline_swings),
            )
            fatigue_q = queue.Queue(maxsize=1)
            print(f'[Fatigue] Enabled | thr={imu_thr_dps:.0f} dps | '
                  f'warmup={args.fatigue_warmup_min} min | '
                  f'baseline={args.fatigue_baseline_swings} swings')
        else:
            fatigue_enabled = False

    def fatigue_worker():
        """Background thread: consume EMG snapshots, call FatigueMonitor, update shared result."""
        while True:
            try:
                item = fatigue_q.get(timeout=1.0)
            except queue.Empty:
                continue
            if item is None:   # sentinel to stop
                break
            emg_snap, t_peak_ms, imu_peak_mag = item
            try:
                result = monitor.push_swing(emg_snap, t_peak_ms, imu_peak_mag)
                with fatigue_lock:
                    fatigue_result.update(result)
                    fatigue_result['history'].append({
                        't_peak_ms': result['t_peak_ms'],
                        'mdf': result['mdf'],
                        'mdf_drop_pct': result['mdf_drop_pct'],
                        'fatigue_level': result['fatigue_level'],
                    })
                level = result['fatigue_level']
                mdf = result.get('mdf')
                drop = result.get('mdf_drop_pct')
                sid = result.get('swing_id', '?')
                print(f'[Fatigue] Swing #{sid} | MDF={mdf} Hz | Drop={drop}% | {level.upper()}')
            except Exception as exc:
                print(f'[Fatigue] Error in push_swing: {exc}')
            finally:
                fatigue_q.task_done()

    if fatigue_enabled and fatigue_q is not None:
        fat_thread = threading.Thread(target=fatigue_worker, daemon=True, name='fatigue_worker')
        fat_thread.start()

    # -----------------------------------------------------------------------
    # Figure layout:
    #   Without fatigue: 3 rows  (raw, env_compare, imu)
    #   With fatigue:    4 rows  (raw, env_compare, imu, fat)
    #
    # ax_raw, ax_env, ax_imu share x-axis (rolling time window).
    # ax_fat has independent x-axis (swing index).
    #
    # ENV comparison subplot (ax_env):
    #   - Orange solid  : ENV_hw  — MyoWare hardware analog envelope (quality/validity indicator)
    #   - Green dashed  : ENV_sw  — abs(RAW) → Butterworth LPF (software computed, same concept)
    #   - Red dotted    : saturation threshold (4000 counts)
    #   - Gray dotted   : dead-signal threshold (50 counts)
    # -----------------------------------------------------------------------
    if fatigue_enabled:
        fig = plt.figure(figsize=(12, 14), layout='constrained')
        gs = fig.add_gridspec(4, 1, hspace=0.50)
        ax_raw = fig.add_subplot(gs[0])
        ax_env = fig.add_subplot(gs[1], sharex=ax_raw)
        ax_imu = fig.add_subplot(gs[2], sharex=ax_raw)
        ax_fat = fig.add_subplot(gs[3])   # independent x-axis: swing #
    else:
        fig = plt.figure(figsize=(11, 10), layout='constrained')
        gs = fig.add_gridspec(3, 1, hspace=0.50)
        ax_raw = fig.add_subplot(gs[0])
        ax_env = fig.add_subplot(gs[1], sharex=ax_raw)
        ax_imu = fig.add_subplot(gs[2], sharex=ax_raw)
        ax_fat = None

    ax_emg = ax_raw  # backward-compat alias (title_text / status still reference ax_emg)

    # --- RAW EMG subplot ---
    (ln_raw,) = ax_raw.plot([], [], lw=0.8, color='steelblue', label='RAW')
    title_text = ax_raw.set_title('Realtime monitoring (dev_us timebase)')
    ax_raw.set_ylabel('ADC (counts)')
    if args.raw_zoom:
        ax_raw.set_ylim((float(args.emg_ymax) / 2.0) - 500.0, (float(args.emg_ymax) / 2.0) + 500.0)
    else:
        ax_raw.set_ylim(0, float(args.emg_ymax))
    ax_raw.grid(True, alpha=0.3)
    ax_raw.legend(loc='upper right', fontsize=8)

    # --- ENV comparison subplot ---
    (ln_env_dev,) = ax_env.plot([], [], lw=1.4, color='tab:orange',
                                label='ENV_hw  (MyoWare hardware analog envelope)')
    (ln_env_lpf,) = ax_env.plot([], [], lw=1.4, color='tab:green', ls='--',
                                label='ENV_sw  (abs(RAW) → Butterworth LPF)')
    # Quality threshold reference lines
    _sat_thr  = 4000.0 * float(args.emg_ymax) / 4095.0
    _dead_thr =   50.0 * float(args.emg_ymax) / 4095.0
    ax_env.axhline(_sat_thr,  color='red',        ls=':', lw=1.2, alpha=0.75,
                   label='Saturation  (>4000 = clipped)')
    ax_env.axhline(_dead_thr, color='dimgray',    ls=':', lw=1.2, alpha=0.75,
                   label='Dead signal (<50  = no contact)')
    ax_env.set_ylabel('ADC (counts)')
    ax_env.set_ylim(0, float(args.emg_ymax))
    ax_env.set_title('ENV comparison — HW (MyoWare) vs SW (abs(RAW)→LPF)  |  quality/validity check')
    ax_env.grid(True, alpha=0.3)
    ax_env.legend(loc='upper right', fontsize=7, ncol=2)
    # Quality status annotation (top-left of ENV subplot)
    env_quality_ann = ax_env.text(
        0.01, 0.97, 'Quality: --',
        transform=ax_env.transAxes, va='top', fontsize=9, fontfamily='monospace',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.88, edgecolor='gray'),
    )

    # Fatigue text annotation (bottom-left of RAW plot)
    if fatigue_enabled:
        fatigue_ann = ax_raw.text(
            0.01, 0.04,
            'Fatigue: waiting for first swing...',
            transform=ax_raw.transAxes,
            va='bottom', fontsize=9, fontfamily='monospace',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow',
                      alpha=0.88, edgecolor='gray'),
        )
    else:
        fatigue_ann = None

    # --- IMU subplot: acc_mag (left Y-axis, blue) + gyro_mag (right Y-axis, red) ---
    # acc_mag (g) shows total acceleration including gravity (~1g at rest).
    # gyro_mag (dps) shows rotation rate — the primary indicator of movement intensity.
    # At rest: gyro_mag ≈ 0 dps.  During a tennis swing: gyro_mag → 500–1000 dps.
    (ln_imu,) = ax_imu.plot([], [], lw=1.2, color='tab:blue', label='acc_mag (g)')
    ax_imu_gyro = ax_imu.twinx()   # secondary Y-axis shares x-axis with ax_imu
    (ln_gyro,) = ax_imu_gyro.plot([], [], lw=1.2, color='tab:red', alpha=0.85,
                                   label='gyro_mag (dps)')
    ax_imu.set_ylabel('g', color='tab:blue')
    ax_imu.tick_params(axis='y', labelcolor='tab:blue')
    ax_imu_gyro.set_ylabel('dps', color='tab:red')
    ax_imu_gyro.tick_params(axis='y', labelcolor='tab:red')
    ax_imu_gyro.set_ylim(0, 1000)
    if not fatigue_enabled:
        ax_imu.set_xlabel('Time (s) (device dev_us)')
    ax_imu.grid(True, alpha=0.3)
    # Combined legend for both axes
    _imu_lines = [ln_imu, ln_gyro]
    ax_imu.legend(_imu_lines, [l.get_label() for l in _imu_lines],
                  loc='upper right', fontsize=8)

    # MDF trend subplot (fatigue only)
    ln_mdf_scatter = ln_mdf_trend = None
    fat_baseline_line = [None]   # mutable container for the axhline reference

    if fatigue_enabled and ax_fat is not None:
        (ln_mdf_scatter,) = ax_fat.plot(
            [], [], 'o', ms=5, alpha=0.7, color='steelblue', label='MDF per swing')
        (ln_mdf_trend,) = ax_fat.plot(
            [], [], '-', lw=2.0, alpha=0.85, color='steelblue',
            label='MDF trend (rolling median)')
        ax_fat.set_ylabel('MDF (Hz)')
        ax_fat.set_xlabel('Swing #')
        ax_fat.set_title('Fatigue trend -- MDF per swing')
        ax_fat.grid(True, alpha=0.3)
        ax_fat.legend(loc='upper right', fontsize=8)
        ax_fat.set_xlim(-0.5, 10)
        ax_fat.set_ylim(50, 500)

    # Status text (top-left of EMG plot)
    status = ax_emg.text(0.01, 0.98, '', transform=ax_emg.transAxes, va='top', fontsize=8)

    # -----------------------------------------------------------------------
    # Prune old samples from rolling buffers
    # -----------------------------------------------------------------------
    def prune(now_t: float) -> None:
        while raw_buf and (now_t - raw_buf[0][0]) > emg_win:
            raw_buf.popleft()
        while env_dev_buf and (now_t - env_dev_buf[0][0]) > emg_win:
            env_dev_buf.popleft()
        while env_lpf_buf and (now_t - env_lpf_buf[0][0]) > emg_win:
            env_lpf_buf.popleft()
        while imu_buf and (now_t - imu_buf[0][0]) > imu_win:
            imu_buf.popleft()
        while gyro_buf and (now_t - gyro_buf[0][0]) > imu_win:
            gyro_buf.popleft()

    # -----------------------------------------------------------------------
    # Animation update callback
    # -----------------------------------------------------------------------
    # ENV_sw scale factor: updated each frame so ENV_sw's dynamic range matches
    # ENV_hw's. ENV_hw (hardware) has higher gain than RAW; after DC removal
    # ENV_sw is much smaller. EMA (tau ≈ 20 frames) prevents rapid changes.
    _env_sw_scale = [1.0]

    def update(_frame):
        nonlocal t0_dev_us, emg_sr_hz, emg_ch, env_filter, last_vitals
        last_seg = None
        rx_count = 0

        # Drain all pending UDP packets
        while True:
            try:
                data = recv_fn()
            except (BlockingIOError, queue.Empty):
                break
            except Exception:
                break

            try:
                msg = json.loads(data.decode('utf-8'))
            except Exception:
                continue

            k = msg.get('k')
            if k not in ('raw', 'env', 'imu'):
                print(f'[Plotter DEBUG] Received packet: {msg}')
            seg = msg.get('seg')
            if seg is not None:
                last_seg = seg

            # --- Metadata packets (no dev_us) ---

            if k == 'emg_meta':
                sr = msg.get('sr_hz')
                ch = msg.get('ch')
                meta_seg = msg.get('seg')
                if sr is not None:
                    sr = float(sr)
                    if (emg_sr_hz is None) or (float(emg_sr_hz) != sr):
                        emg_sr_hz = sr
                        emg_ch = ch
                        env_filter = ButterLPF(fs_hz=emg_sr_hz, cutoff_hz=float(args.cutoff_hz))
                        # Keep FatigueMonitor fs in sync via public setter
                        if fatigue_enabled and monitor is not None:
                            monitor.set_fs(sr)
                            print(f'[Fatigue] Updated fs={sr:.0f} Hz')
                        print(f'[Plotter] EMG meta: sr_hz={emg_sr_hz:.1f} ch={emg_ch}')
                # Reset on new BLE session (seg=0 after data already seen).
                # seg=0 means btCentral just started a new BLE connection / CSV rotation 0.
                # The device timer resets to 0 on reconnect, so t0_dev_us and all rolling
                # buffers must be cleared; otherwise new dev_us values are negative relative
                # to the old t0_dev_us and prune() discards every incoming sample immediately,
                # causing the plot to appear frozen/stuck.
                if meta_seg == 0 and t0_dev_us is not None:
                    print('[Plotter] New BLE session (seg=0) — resetting timebase and buffers')
                    t0_dev_us = None
                    raw_buf.clear()
                    env_dev_buf.clear()
                    env_lpf_buf.clear()
                    imu_buf.clear()
                    gyro_buf.clear()
                    recent_raw_dev_us.clear()
                    # Also reset the LPF so it doesn't carry stale state into the new session
                    if emg_sr_hz is not None:
                        env_filter = ButterLPF(fs_hz=emg_sr_hz, cutoff_hz=float(args.cutoff_hz))
                    if fatigue_enabled and monitor is not None:
                        monitor.reset()
                        emg_fatigue_buf.clear()
                        last_imu_trigger_t[0] = -999.0
                        in_peak[0] = False
                        peak_gyro_mag[0] = 0.0
                        print('[Fatigue] New BLE session (seg=0) — monitor reset')
                continue

            if k == 'vitals':
                last_vitals.update(msg)
                continue

            # --- Data packets (all have dev_us) ---

            dev_us = msg.get('dev_us')
            if dev_us is None:
                continue
            dev_us = int(dev_us)
            if t0_dev_us is None:
                t0_dev_us = dev_us
            t_sec = (dev_us - t0_dev_us) / 1_000_000.0

            if k == 'raw':
                r = msg.get('raw')
                if r is None:
                    continue
                r = float(r)
                raw_buf.append((t_sec, r))
                recent_raw_dev_us.append(dev_us)

                # Push to fatigue ring buffer at FULL rate (before any decimation)
                if fatigue_enabled:
                    emg_fatigue_buf.append(r)

                # Infer sr_hz from timing if emg_meta was missed
                if env_filter is None and args.infer_sr and \
                        len(recent_raw_dev_us) >= int(args.infer_min_samples):
                    sr_inf = infer_sr_from_dev_us(
                        list(recent_raw_dev_us),
                        float(args.infer_min_hz), float(args.infer_max_hz))
                    if sr_inf is not None:
                        emg_sr_hz = sr_inf
                        env_filter = ButterLPF(fs_hz=emg_sr_hz, cutoff_hz=float(args.cutoff_hz))
                        print(f'[Plotter] Inferred EMG sr_hz={emg_sr_hz:.0f} (no meta yet)')

                # Update DC offset tracker (slow LPF, 0.1 Hz cutoff)
                if raw_dc_state['alpha'] is None and emg_sr_hz is not None:
                    import math
                    raw_dc_state['alpha'] = 1.0 - math.exp(-2.0 * math.pi * 0.1 / emg_sr_hz)
                if raw_dc_state['alpha'] is not None:
                    raw_dc_state['lpf'] += raw_dc_state['alpha'] * (r - raw_dc_state['lpf'])

                if env_filter is not None:
                    # Use tracked DC center — makes envelope symmetric and correct
                    # abs(r) gives DC level (~1843); abs(r - dc) gives true envelope (~0 at rest)
                    env_lpf_buf.append((t_sec, env_filter.update(abs(r - raw_dc_state['lpf']))))

            elif k == 'env':
                e = msg.get('env')
                if e is None:
                    continue
                env_dev_buf.append((t_sec, float(e)))

            elif k == 'imu':
                a = msg.get('amag')
                if a is None:
                    continue
                imu_buf.append((t_sec, float(a)))
                g = msg.get('gmag')
                if g is not None:
                    gyro_buf.append((t_sec, float(g)))

                # Peak detection: only trigger on the HIGHEST point of the swing
                # This prevents double-counting backswing + forward swing
                if fatigue_enabled and monitor is not None and fatigue_q is not None:
                    gmag = msg.get('gmag')
                    if gmag is not None:
                        gmag = float(gmag)

                        if gmag >= imu_thr_dps:
                            if not in_peak[0]:
                                # Start of new peak
                                in_peak[0] = True
                                peak_gyro_mag[0] = gmag
                                peak_time_sec[0] = t_sec
                            else:
                                # Already in peak - update if this is higher
                                if gmag > peak_gyro_mag[0]:
                                    peak_gyro_mag[0] = gmag
                                    peak_time_sec[0] = t_sec
                        elif in_peak[0]:
                            # Dropped below threshold - end of peak
                            # Trigger detection at the peak point (if debounce allows)
                            if (peak_time_sec[0] - last_imu_trigger_t[0]) >= 1.0:
                                last_imu_trigger_t[0] = peak_time_sec[0]
                                swing_count[0] += 1  # Increment swing counter
                                snap = list(emg_fatigue_buf)   # snapshot (copy)
                                if len(snap) >= 32:
                                    t_peak_ms = peak_time_sec[0] * 1000.0
                                    try:
                                        fatigue_q.put_nowait((snap, t_peak_ms, peak_gyro_mag[0]))
                                    except queue.Full:
                                        pass   # drop if fatigue thread is still busy
                            in_peak[0] = False
                            peak_gyro_mag[0] = 0.0

            elif k == 'battery':
                pct = msg.get('pct')
                v   = msg.get('v')
                if pct is not None:
                    print(f'[Plotter] Battery: {int(pct)}%')
                if v is not None:
                    print(f'[Plotter] Voltage: {float(v):.2f}V')

            rx_count += 1

        # --- Compute current time and prune old data ---
        now_t = 0.0
        for b in (raw_buf, env_dev_buf, env_lpf_buf, imu_buf):
            if b:
                now_t = max(now_t, b[-1][0])
        prune(now_t)

        # --- Update EMG lines ---
        if raw_buf:
            xs = np.array([p[0] for p in raw_buf], dtype=float)
            ys = np.array([p[1] for p in raw_buf], dtype=float)
            ln_raw.set_data(xs, ys)

            if args.raw_zoom:
                lo, hi = float(np.min(ys)), float(np.max(ys))
                if hi - lo < 200.0:  # Prevent zooming in too tight on baseline noise
                    mid = (hi + lo) / 2.0
                    lo, hi = mid - 100.0, mid + 100.0
                pad = 0.1 * (hi - lo)
                ax_raw.set_ylim(max(0.0, lo - pad), min(float(args.emg_ymax), hi + pad))

        if env_dev_buf:
            xs = np.array([p[0] for p in env_dev_buf], dtype=float)
            ys = np.array([p[1] for p in env_dev_buf], dtype=float)
            ln_env_dev.set_data(xs, ys)
            # --- Quality / validity check on HW ENV ---
            recent = ys[-min(100, len(ys)):]   # last ~50 ms at 2 kHz
            env_hw_max  = float(np.max(recent))
            env_hw_mean = float(np.mean(recent))
            if env_hw_max > 4000:
                q_txt   = f'Quality: SATURATED  HW_ENV max={env_hw_max:.0f} > 4000  (gain too high / electrode short)'
                q_color = 'red'
                q_bg    = 'mistyrose'
            elif env_hw_mean < 50:
                q_txt   = f'Quality: DEAD SIGNAL  HW_ENV mean={env_hw_mean:.0f} < 50  (electrode off / no contact)'
                q_color = 'dimgray'
                q_bg    = 'lightgray'
            else:
                q_txt   = f'Quality: OK  HW_ENV mean={env_hw_mean:.0f}  max={env_hw_max:.0f}'
                q_color = 'darkgreen'
                q_bg    = 'honeydew'
            env_quality_ann.set_text(q_txt)
            env_quality_ann.set_color(q_color)
            env_quality_ann.get_bbox_patch().set_facecolor(q_bg)
        # Scale ENV_sw to match ENV_hw's dynamic range.
        # _compute_env_sw_scale() is the shared formula (same as offline mode).
        # EMA (tau ≈ 20 frames) smooths rapid changes in the rolling window.
        if env_dev_buf and env_lpf_buf:
            _new_scale = _compute_env_sw_scale(
                float(np.max([p[1] for p in env_dev_buf])),
                float(np.max([p[1] for p in env_lpf_buf])),
            )
            _env_sw_scale[0] = 0.95 * _env_sw_scale[0] + 0.05 * _new_scale

        if env_lpf_buf:
            xs = np.array([p[0] for p in env_lpf_buf], dtype=float)
            ys = np.array([p[1] * _env_sw_scale[0] for p in env_lpf_buf], dtype=float)
            ln_env_lpf.set_data(xs, ys)

        # Auto-scale ENV subplot Y-axis based on ENV_hw (ENV_sw is now scaled to match).
        _env_y_max = 200.0
        if env_dev_buf:
            _env_y_max = max(_env_y_max,
                             float(np.max([p[1] for p in env_dev_buf])) * 1.25)
        ax_env.set_ylim(0, _env_y_max)
        # Update title to show current scale factor so user knows ENV_sw is scaled
        ax_env.set_title(
            f'ENV comparison — HW vs SW (abs(RAW-DC)→LPF ×{_env_sw_scale[0]:.1f})  |  quality check')

        # --- Update IMU lines (acc_mag left-axis + gyro_mag right-axis) ---
        if imu_buf:
            xs = np.array([p[0] for p in imu_buf], dtype=float)
            ys = np.array([p[1] for p in imu_buf], dtype=float)
            ln_imu.set_data(xs, ys)
            # Fixed absolute scale (0 to 4g minimum); expands if swing exceeds 4g.
            hi = max(4.0, float(np.max(ys)))
            ax_imu.set_ylim(0, hi * 1.05)
        if gyro_buf:
            xs = np.array([p[0] for p in gyro_buf], dtype=float)
            ys = np.array([p[1] for p in gyro_buf], dtype=float)
            ln_gyro.set_data(xs, ys)
            # Auto-scale gyro: minimum 200 dps so baseline is visible; expands for fast swings.
            hi_g = max(200.0, float(np.max(ys)) * 1.1)
            ax_imu_gyro.set_ylim(0, hi_g)

        # Shared x-axis for EMG + IMU (rolling window)
        # Guard against now_t == 0.0 (no data yet) which would produce identical
        # low/high xlims and trigger a matplotlib "singular transformation" warning.
        if now_t > 0.0:
            if feeder is not None and feeder.done and getattr(args, 'replay_no_scroll', False):
                # Replay finished + --replay-no-scroll: show full session
                ax_imu.set_xlim(0.0, feeder.total_t_sec * 1.05)
            else:
                xlim_lo = max(0.0, now_t - max(emg_win, imu_win))
                ax_imu.set_xlim(xlim_lo, now_t)   # propagates to ax_emg via sharex

        # --- Title: vitals + swing count ---
        if last_vitals:
            parts = []

            batt_pct = last_vitals.get('pct')
            batt_v = last_vitals.get('v')
            if batt_pct is not None:
                batt_str = f"BATTERY: {int(batt_pct)}%"
                if batt_v is not None:
                    try:
                        batt_str += f" ({float(batt_v):.2f}V)"
                    except Exception:
                        pass
                parts.append(batt_str)
            else:
                # ESP32 firmware may not report battery; keep plotter alive.
                parts.append("BATTERY: N/A")

            if last_vitals.get('spo2') is not None:
                parts.append(f"SpO2: {last_vitals['spo2']}%")
            if last_vitals.get('hr') is not None:
                parts.append(f"HR: {last_vitals['hr']:.1f} bpm")
            # Add swing count
            if fatigue_enabled and swing_count[0] > 0:
                parts.append(f"SWINGS: {swing_count[0]}")

            title_text.set_text('Realtime Monitoring | ' + ' | '.join(parts))

            # Only color-code if batt_pct is known
            if batt_pct is None:
                title_text.set_color('black')
                title_text.set_fontweight('normal')
            else:
                try:
                    batt_pct_i = int(batt_pct)
                except Exception:
                    batt_pct_i = None
                if batt_pct_i is None:
                    title_text.set_color('black')
                    title_text.set_fontweight('normal')
                else:
                    batt_color = 'red' if batt_pct_i < 20 else ('orange' if batt_pct_i < 50 else 'green')
                    title_text.set_color(batt_color)
                    title_text.set_fontweight('bold')
        else:
            # Show swing count even without vitals
            swing_str = f" | SWINGS: {swing_count[0]}" if (fatigue_enabled and swing_count[0] > 0) else ""
            title_text.set_text(f'Realtime Monitoring [Waiting for Vitals...]{swing_str}')
            title_text.set_color('black')
            title_text.set_fontweight('normal')

        seg_str = f'seg={last_seg}' if last_seg is not None else 'seg=?'
        sr_str  = f'sr={emg_sr_hz:.0f}Hz' if emg_sr_hz else 'sr=?'
        status.set_text(
            f'UDP {args.listen_host}:{args.listen_port}  {seg_str}  {sr_str}  rx={rx_count}')

        # -----------------------------------------------------------------------
        # Fatigue display update (annotation + MDF trend subplot)
        # -----------------------------------------------------------------------
        if fatigue_enabled and fatigue_ann is not None:
            with fatigue_lock:
                fr = dict(fatigue_result)
                history = list(fr.get('history', []))

            swing_id       = fr.get('swing_id', -1)
            level          = fr.get('fatigue_level', 'warming_up')
            mdf            = fr.get('mdf')
            drop           = fr.get('mdf_drop_pct')
            baseline_ready = fr.get('baseline_ready', False)
            n_baseline     = fr.get('baseline_swings_collected', 0)
            warning        = fr.get('warning', False)
            baseline_mdf   = fr.get('baseline_mdf')

            # Text annotation
            if swing_id < 0:
                fat_str    = 'Fatigue: waiting for first swing...'
                fat_color  = 'gray'
                bbox_color = 'lightyellow'
            elif not baseline_ready:
                fat_str    = (f'Swing #{swing_id} | Warming up '
                              f'({n_baseline}/{args.fatigue_baseline_swings} baseline swings)')
                fat_color  = 'navy'
                bbox_color = 'lightcyan'
            else:
                mdf_str  = f'{mdf:.1f} Hz' if mdf is not None else 'N/A'
                drop_str = f'{drop:+.1f}%'  if drop is not None else 'N/A'
                warn_pfx = '[!] ' if warning else ''
                fat_str  = (f'{warn_pfx}Swing #{swing_id} | MDF={mdf_str} | '
                            f'Drop={drop_str} | {level.upper()}')
                fat_color  = {'fresh': 'darkgreen', 'moderate': 'darkorange',
                              'high': 'red'}.get(level, 'gray')
                bbox_color = {'fresh': 'honeydew', 'moderate': 'lightyellow',
                              'high': 'mistyrose'}.get(level, 'lightyellow')

            fatigue_ann.set_text(fat_str)
            fatigue_ann.set_color(fat_color)
            fatigue_ann.get_bbox_patch().set_facecolor(bbox_color)

            # MDF trend subplot
            if ax_fat is not None and ln_mdf_scatter is not None and len(history) >= 1:
                valid = [(i, h['mdf']) for i, h in enumerate(history) if h['mdf'] is not None]
                if valid:
                    xs_h = [v[0] for v in valid]
                    ys_h = [v[1] for v in valid]
                    ln_mdf_scatter.set_data(xs_h, ys_h)

                    # Rolling median trend line (window = min(10, n//3), min 3)
                    n_h = len(ys_h)
                    win = max(3, min(10, n_h // 3)) if n_h >= 3 else n_h
                    if n_h >= win:
                        trend = [
                            float(np.median(ys_h[max(0, i - win + 1):i + 1]))
                            for i in range(n_h)
                        ]
                        ln_mdf_trend.set_data(xs_h, trend)

                    # Baseline reference horizontal line (created once, updated after)
                    if baseline_mdf is not None:
                        if fat_baseline_line[0] is None:
                            fat_baseline_line[0] = ax_fat.axhline(
                                float(baseline_mdf), color='k', ls='--',
                                lw=1.5, alpha=0.6, label='baseline MDF')
                            ax_fat.legend(loc='upper right', fontsize=8)
                        else:
                            fat_baseline_line[0].set_ydata(
                                [float(baseline_mdf), float(baseline_mdf)])

                    ax_fat.set_xlim(-0.5, max(len(history) - 0.5, 5))
                    lo = min(ys_h) * 0.85
                    hi = max(ys_h) * 1.15
                    if hi <= lo:
                        hi = lo + 10.0
                    ax_fat.set_ylim(lo, hi)

        # Collect artists for return (blit=False so not strictly needed, but good practice)
        artists = [ln_raw, ln_env_dev, ln_env_lpf, ln_imu, ln_gyro, status, env_quality_ann]
        if fatigue_ann is not None:
            artists.append(fatigue_ann)
        if ln_mdf_scatter is not None:
            artists.extend([ln_mdf_scatter, ln_mdf_trend])
        return artists

    interval_ms = max(10, int(1000.0 / float(args.fps)))
    _ani = FuncAnimation(fig, update, interval=interval_ms, blit=False, cache_frame_data=False)
    plt.show()


# ---------------------------------------------------------------------------
# CSV Replay Feeder  (--mode offline --fatigue)
# ---------------------------------------------------------------------------

class CsvReplayFeeder:
    """Reads EMG + IMU CSV files and feeds JSON-encoded messages into a queue,
    mimicking the UDP stream produced by btCentral.py.

    Supports instant replay (speed=0) and real-time / N× replay (speed > 0).
    Call load() first to pre-load files, then start() to begin feeding.
    """

    def __init__(self, emg_file, imu_file, sr_hz: float, speed: float = 0.0):
        self.emg_file = emg_file
        self.imu_file = imu_file
        self.sr_hz = float(sr_hz)
        self.speed = float(speed)
        self.q = queue.Queue(maxsize=0)   # unlimited — feeder fills as fast as possible
        self._thread = None
        self._done = False
        self.total_t_sec = 0.0
        self._all_rows = []   # populated by load()

    # ------------------------------------------------------------------
    def load(self) -> None:
        """Pre-load both CSV files into memory and merge by dev_us.
        Must be called before start().
        """
        rows = []

        # EMG rows: (dev_us, 'emg', raw, env)
        if self.emg_file:
            with open(self.emg_file, 'r', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    try:
                        du = int(row['dev_us'])
                        rw = float(row['raw'])
                        ev = float(row['env'])
                    except Exception:
                        continue
                    rows.append((du, 'emg', rw, ev))

        # IMU rows: (dev_us, 'imu', amag_g, gmag_dps)
        if self.imu_file:
            acc_fsr_g = 4
            gyro_fsr_dps = 1000
            acc_map = {2: 16384.0, 4: 8192.0, 8: 4096.0, 16: 2048.0}
            gyr_map = {250: 131.0, 500: 65.5, 1000: 32.8, 2000: 16.4}
            with open(self.imu_file, 'r', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    try:
                        du = int(row['dev_us'])
                        if row.get('acc_fsr_g'):
                            acc_fsr_g = int(row['acc_fsr_g'])
                        if row.get('gyro_fsr_dps'):
                            gyro_fsr_dps = int(row['gyro_fsr_dps'])
                        ax = float(row['ax']); ay = float(row['ay']); az = float(row['az'])
                        gx = float(row['gx']); gy = float(row['gy']); gz = float(row['gz'])
                        acc_lsb = acc_map.get(acc_fsr_g, 8192.0)
                        gyr_lsb = gyr_map.get(gyro_fsr_dps, 32.8)
                        amag = (ax * ax + ay * ay + az * az) ** 0.5 / acc_lsb
                        gmag = (gx * gx + gy * gy + gz * gz) ** 0.5 / gyr_lsb
                    except Exception:
                        continue
                    rows.append((du, 'imu', amag, gmag))

        rows.sort(key=lambda r: r[0])
        self._all_rows = rows

        if rows:
            t0 = rows[0][0]
            t_end = rows[-1][0]
            self.total_t_sec = (t_end - t0) / 1_000_000.0

    # ------------------------------------------------------------------
    @property
    def done(self) -> bool:
        """True once the feeder thread has finished AND the queue is drained."""
        return self._done and self.q.empty()

    # ------------------------------------------------------------------
    def recv(self) -> bytes:
        """Returns next JSON-encoded message bytes, or raises queue.Empty."""
        return self.q.get_nowait()

    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start background feeder thread. Call load() first."""
        self._thread = threading.Thread(target=self._feed, daemon=True, name='csv_replay')
        self._thread.start()

    # ------------------------------------------------------------------
    def _feed(self) -> None:
        rows = self._all_rows
        if not rows:
            self._done = True
            return

        t0_dev = rows[0][0]
        sr = int(self.sr_hz)

        # Inject emg_meta first so run_live() initialises LPF + FatigueMonitor
        meta = json.dumps({
            'k': 'emg_meta', 'sr_hz': sr, 'ch': 3,
            'adc_bits': 12, 'ymax': 4095, 'seg': 0,
        }).encode('utf-8')
        self.q.put(meta)

        wall_t0 = time.time()

        for du, kind, a, b in rows:
            if self.speed > 0.0:
                # Throttle to simulate real-time (or N× speed)
                dev_elapsed = (du - t0_dev) / 1_000_000.0
                wall_elapsed = time.time() - wall_t0
                target = dev_elapsed / self.speed
                if target > wall_elapsed:
                    time.sleep(target - wall_elapsed)

            if kind == 'emg':
                self.q.put(json.dumps({
                    'k': 'raw', 'dev_us': du, 'raw': a, 'seg': 0,
                }).encode('utf-8'))
                self.q.put(json.dumps({
                    'k': 'env', 'dev_us': du, 'env': b, 'seg': 0,
                }).encode('utf-8'))
            else:  # imu
                self.q.put(json.dumps({
                    'k': 'imu', 'dev_us': du, 'amag': a, 'gmag': b, 'seg': 0,
                }).encode('utf-8'))

        self._done = True


# ---------------------------------------------------------------------------
# Offline mode
# ---------------------------------------------------------------------------

def run_offline(args: argparse.Namespace) -> None:
    if not args.emg_file and not args.imu_file:
        raise SystemExit('Offline mode requires --emg-file or --imu-file')

    # ── Fatigue offline: drive run_live() via CSV replay feeder ─────────────
    if getattr(args, 'fatigue', False):
        if not args.emg_file or not args.imu_file:
            raise SystemExit(
                '--fatigue offline mode requires both --emg-file and --imu-file')
        util_path = args.emg_util_path
        if util_path is None:
            util_path = os.path.normpath(os.path.join(
                os.path.dirname(os.path.abspath(__file__)), '..', '..', 'emg_util'))
        if not _try_import_fatigue_monitor(util_path):
            raise SystemExit(
                '--fatigue requires fatigue_monitor.py (use --emg-util-path to point to its directory)')
        feeder = CsvReplayFeeder(
            args.emg_file, args.imu_file,
            float(args.sr_hz),
            float(getattr(args, 'replay_speed', 0.0)),
        )
        feeder.load()
        print(f'[Replay] Session: {feeder.total_t_sec:.1f}s | '
              f'{len(feeder._all_rows)} rows | speed='
              f'{"instant" if feeder.speed == 0.0 else f"{feeder.speed}x"}')
        if getattr(args, 'replay_no_scroll', False):
            # Expand window to full session so prune() keeps all data
            args.emg_window_sec = feeder.total_t_sec + 1.0
            if args.imu_window_sec is None:
                args.imu_window_sec = feeder.total_t_sec + 1.0
        feeder.start()
        run_live(args, recv_fn=feeder.recv, feeder=feeder)
        return
    # ────────────────────────────────────────────────────────────────────────

    if args.emg_file:
        t_ms, raw, env = [], [], []
        with open(args.emg_file, 'r', encoding='utf-8') as f:
            r = csv.DictReader(f)
            for row in r:
                try:
                    t  = int(row.get('host_rx_ms', '0'))
                    rw = float(row.get('raw', 'nan'))
                    ev = float(row.get('env', 'nan'))
                except Exception:
                    continue
                t_ms.append(t)
                raw.append(rw)
                env.append(ev)
                if len(t_ms) >= int(args.max_points):
                    break

        if not t_ms:
            raise SystemExit('No data read from EMG file')

        t0 = t_ms[0]
        xs  = np.array([(t - t0) / 1000.0 for t in t_ms], dtype=float)
        raw = np.array(raw, dtype=float)
        env = np.array(env, dtype=float)

        # DC offset: subtract mean of raw to get true envelope (0 at rest, not ~1843).
        # MyoWare DC bias shifts center from theoretical 2048 to ~1830-1843.
        # abs(x) gives DC level; abs(x - mean) gives symmetric envelope amplitude.
        raw_dc_offline = float(np.mean(raw))
        env_filter = ButterLPF(fs_hz=float(args.sr_hz), cutoff_hz=float(args.cutoff_hz))
        env_lpf = np.array([env_filter.update(abs(x - raw_dc_offline)) for x in raw], dtype=float)
        # Scale ENV_sw to match ENV_hw's dynamic range (whole-file ratio).
        # Uses the same _compute_env_sw_scale() helper as live mode.
        _env_sw_scale_off = _compute_env_sw_scale(
            float(np.nanmax(env[np.isfinite(env)])) if np.any(np.isfinite(env)) else 1.0,
            float(np.max(env_lpf)) if np.max(env_lpf) > 0 else 1.0,
        )
        env_lpf = env_lpf * _env_sw_scale_off

        # --- Quality metrics (whole-file) ---
        env_fin = env[np.isfinite(env)]
        env_hw_max  = float(np.nanmax(env_fin))  if len(env_fin) else 0.0
        env_hw_mean = float(np.nanmean(env_fin)) if len(env_fin) else 0.0
        sat_pct  = float(np.mean(env > 4000) * 100.0)
        dead_pct = float(np.mean(env < 50)   * 100.0)
        if sat_pct > 5.0:
            quality_str   = f'SATURATED  ({sat_pct:.1f}% samples > 4000 — gain too high / electrode short)'
            quality_color = 'red'
        elif dead_pct > 50.0:
            quality_str   = f'DEAD SIGNAL  ({dead_pct:.1f}% samples < 50 — electrode off / no contact)'
            quality_color = 'dimgray'
        else:
            quality_str   = f'OK  mean={env_hw_mean:.0f}  max={env_hw_max:.0f}  sat={sat_pct:.1f}%'
            quality_color = 'darkgreen'

        fig, (ax_r, ax_e) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)

        # RAW subplot
        ax_r.plot(xs, raw, lw=0.8, color='steelblue', label='RAW')
        ax_r.set_title(f'Offline EMG — {os.path.basename(args.emg_file)}')
        ax_r.set_ylabel('ADC (counts)')
        if args.raw_zoom:
            ax_r.set_ylim((float(args.emg_ymax) / 2.0) - 500.0, (float(args.emg_ymax) / 2.0) + 500.0)
        else:
            ax_r.set_ylim(0, float(args.emg_ymax))
        ax_r.grid(True, alpha=0.3)
        ax_r.legend(loc='upper right')

        # ENV comparison subplot
        ax_e.plot(xs, env,     lw=1.2, color='tab:orange',
                  label='ENV_hw  (MyoWare hardware analog envelope)')
        ax_e.plot(xs, env_lpf, lw=1.2, color='tab:green', ls='--',
                  label='ENV_sw  (abs(RAW) → Butterworth LPF)')
        ax_e.axhline(4000, color='red',     ls=':', lw=1.2, alpha=0.75,
                     label='Saturation  (>4000)')
        ax_e.axhline(50,   color='dimgray', ls=':', lw=1.2, alpha=0.75,
                     label='Dead signal (<50)')
        ax_e.set_title(
            f'ENV comparison — HW (MyoWare) vs SW (abs(RAW-DC)→LPF ×{_env_sw_scale_off:.1f})\n'
            f'Quality: {quality_str}',
            color=quality_color,
        )
        ax_e.set_xlabel('Time (s) (host_rx_ms)')
        ax_e.set_ylabel('ADC (counts)')
        # Auto-scale to show both ENV_hw and ENV_sw clearly (ENV_sw is now scaled to match ENV_hw).
        _env_off_max = max(200.0,
                           float(np.nanmax(env[np.isfinite(env)])) * 1.25 if len(env_fin) else 200.0)
        ax_e.set_ylim(0, _env_off_max)
        ax_e.grid(True, alpha=0.3)
        ax_e.legend(loc='upper right', fontsize=8, ncol=2)

        plt.tight_layout()
        plt.show()

    if args.imu_file:
        t_ms, ax_vals, ay_vals, az_vals, gx_vals, gy_vals, gz_vals = [], [], [], [], [], [], []
        # Fallback FSR values if missing from CSV
        acc_fsr_g = 4
        gyro_fsr_dps = 1000

        with open(args.imu_file, 'r', encoding='utf-8') as f:
            r = csv.DictReader(f)
            for row in r:
                try:
                    t  = int(row.get('host_rx_ms', '0'))

                    # Read FSR metadata if available in CSV row
                    if 'acc_fsr_g' in row and row['acc_fsr_g']:
                        acc_fsr_g = int(row['acc_fsr_g'])
                    if 'gyro_fsr_dps' in row and row['gyro_fsr_dps']:
                        gyro_fsr_dps = int(row['gyro_fsr_dps'])

                    ax = float(row.get('ax', 'nan'))
                    ay = float(row.get('ay', 'nan'))
                    az = float(row.get('az', 'nan'))
                    gx = float(row.get('gx', 'nan'))
                    gy = float(row.get('gy', 'nan'))
                    gz = float(row.get('gz', 'nan'))
                except Exception:
                    continue
                t_ms.append(t)
                ax_vals.append(ax)
                ay_vals.append(ay)
                az_vals.append(az)
                gx_vals.append(gx)
                gy_vals.append(gy)
                gz_vals.append(gz)
                if len(t_ms) >= int(args.max_points):
                    break

        if not t_ms:
            raise SystemExit('No data read from IMU file')

        # Convert raw LSB to physical units
        acc_map = {2: 16384.0, 4: 8192.0, 8: 4096.0, 16: 2048.0}
        gyr_map = {250: 131.0, 500: 65.5, 1000: 32.8, 2000: 16.4}
        acc_lsb_per_g = acc_map.get(acc_fsr_g, 16384.0)
        gyro_lsb_per_dps = gyr_map.get(gyro_fsr_dps, 131.0)

        t0 = t_ms[0]
        xs = np.array([(t - t0) / 1000.0 for t in t_ms], dtype=float)

        # Calculate magnitudes in physical units
        ax_g = np.array(ax_vals, dtype=float) / acc_lsb_per_g
        ay_g = np.array(ay_vals, dtype=float) / acc_lsb_per_g
        az_g = np.array(az_vals, dtype=float) / acc_lsb_per_g
        amag = np.sqrt(ax_g**2 + ay_g**2 + az_g**2)

        gx_dps = np.array(gx_vals, dtype=float) / gyro_lsb_per_dps
        gy_dps = np.array(gy_vals, dtype=float) / gyro_lsb_per_dps
        gz_dps = np.array(gz_vals, dtype=float) / gyro_lsb_per_dps
        gmag = np.sqrt(gx_dps**2 + gy_dps**2 + gz_dps**2)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)

        # Accel plot
        ax1.plot(xs, amag, lw=1.2, color='black', label='acc_mag')
        ax1.plot(xs, ax_g, lw=0.8, alpha=0.6, label='ax')
        ax1.plot(xs, ay_g, lw=0.8, alpha=0.6, label='ay')
        ax1.plot(xs, az_g, lw=0.8, alpha=0.6, label='az')
        ax1.set_title(f'Offline IMU: {args.imu_file}\nFSR: {acc_fsr_g}g, {gyro_fsr_dps}dps')
        ax1.set_ylabel('Acceleration (g)')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper right', ncol=4)

        # Gyro plot
        ax2.plot(xs, gmag, lw=1.2, color='black', label='gyro_mag')
        ax2.plot(xs, gx_dps, lw=0.8, alpha=0.6, label='gx')
        ax2.plot(xs, gy_dps, lw=0.8, alpha=0.6, label='gy')
        ax2.plot(xs, gz_dps, lw=0.8, alpha=0.6, label='gz')
        ax2.set_xlabel('Time (s) (host_rx_ms)')
        ax2.set_ylabel('Rotation (dps)')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper right', ncol=4)

        plt.tight_layout()
        plt.show()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    if args.mode == 'live':
        run_live(args)
    else:
        run_offline(args)


if __name__ == '__main__':
    main()
