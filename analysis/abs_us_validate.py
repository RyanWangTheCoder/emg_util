#!/usr/bin/env python3
"""abs_us_validate.py

N1 validation: Quantitative analysis of the hybrid abs_us timeline reconstruction
for the journal paper §5.4.

Compares three timeline reconstruction strategies for BLE wearable sessions:
  A. dev_us-only   — device microsecond clock; fails when device reboots between
                     BLE connections (clock restarts at 0)
  B. host_rx_ms-only — host wall-clock milliseconds; continuous across reconnects
                     but assigns the SAME timestamp to all ~54 samples in one BLE
                     notification batch, giving batch-resolution (~9–170ms) rather
                     than per-sample timing
  C. abs_us hybrid  — dev_us for intra-connection per-sample precision (±25 µs),
                     host_rx_ms gap for inter-connection bridging (~170ms at p99)

Data used:
  log0305 files 001–003: 60 min, single BLE connection, clean sequential data
    (emg_seq [278374, 7485631], no device reboots)
  log0303 files 183639_001 and 191258_000: clean boundary files for inter-
    connection gap measurement

Outputs:
  paper_figures/fig_absus_error_cdf.png      — BLE batch interval CDF + 5s window
                                               (reconstruction error characterization)
  paper_figures/fig_absus_timeline_methods.png — method comparison at reconnect
  paper_figures/table_absus_validation.csv   — summary statistics
"""

import os
import sys

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import capture_loader as cl

OUTDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "papers", "paper_figures")
os.makedirs(OUTDIR, exist_ok=True)

# ── Paths to CLEAN rotation files ────────────────────────────────────────────
LOG0305_CLEAN = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "data", "log0305", f"emg_log_20260305_192734_20260305_{name}.csv")
    for name in ["194756_624_001", "200757_983_002", "202758_952_003"]
]

LOG0303_C1 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "log0303", "emg_log_20260303_183639_20260303_185708_920_001.csv")
LOG0303_C2 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "log0303", "emg_log_20260303_191258_20260303_191313_303_000.csv")

# ── Section 1: BLE batching and intra-connection analysis (log0305 clean) ────

print("Loading log0305 clean files (001–003)...")
parts = [pd.read_csv(f, usecols=["dev_us", "emg_seq", "host_rx_ms"])
         for f in LOG0305_CLEAN]
df = pd.concat(parts, ignore_index=True).sort_values("dev_us").reset_index(drop=True)
print(f"  {len(df):,} rows, {len(df)/2000/60:.1f} min")

# BLE notification interval distribution
host_diff = np.diff(df["host_rx_ms"].values)
notif_intervals_ms = host_diff[host_diff > 0].astype(float)  # ms
n_notif = len(notif_intervals_ms)
samples_per_notif = len(df) / n_notif
print(f"  {n_notif:,} BLE notification boundaries detected")
print(f"  Mean samples per notification: {samples_per_notif:.1f}")
print(f"  Notification interval: "
      f"p25={np.percentile(notif_intervals_ms,25):.0f}ms, "
      f"p50={np.percentile(notif_intervals_ms,50):.0f}ms, "
      f"p75={np.percentile(notif_intervals_ms,75):.0f}ms, "
      f"p99={np.percentile(notif_intervals_ms,99):.0f}ms")

# Within-batch temporal resolution loss:
# Each sample's distance from its batch's START (via dev_us).
# All samples in a batch get the SAME host_rx_ms, so the per-sample timing error
# of host_rx_ms-only = offset from batch start in dev_us.
# Build batch start times using host_rx_ms transitions.
host = df["host_rx_ms"].values
dev  = df["dev_us"].values
# Find batch start indices
batch_start_idx = np.concatenate([[0], 1 + np.where(host_diff > 0)[0]])
# For each sample, compute its dev_us offset from its batch start
# (use searchsorted to assign batch ID to every sample)
sample_batch_id = np.searchsorted(batch_start_idx, np.arange(len(df)), side="right") - 1
sample_batch_id = np.clip(sample_batch_id, 0, len(batch_start_idx) - 1)
batch_start_dev = dev[batch_start_idx]
# Intra-batch offset in µs (how far each sample is from batch start, in dev_us)
intra_offset_us = dev - batch_start_dev[sample_batch_id]
intra_offset_ms = intra_offset_us / 1000.0

print()
print("Per-sample timing loss when using host_rx_ms (all samples in batch get same time):")
print(f"  (dev_us offset from batch start)")
for p in [50, 75, 90, 95, 99]:
    print(f"  p{p}: {np.percentile(intra_offset_ms, p):.1f} ms")

# ── Section 2: Inter-connection gap (log0303) ─────────────────────────────────

print()
print("Loading log0303 boundary files...")
c1 = pd.read_csv(LOG0303_C1, usecols=["dev_us", "emg_seq", "host_rx_ms"])
c2 = pd.read_csv(LOG0303_C2, usecols=["dev_us", "emg_seq", "host_rx_ms"])

# Use the LAST ROW of c1 and FIRST ROW of c2 (chronological boundary)
host_c1_last = float(c1["host_rx_ms"].iloc[-1])
host_c2_first = float(c2["host_rx_ms"].iloc[0])
dev_c1_last = int(c1["dev_us"].iloc[-1])
dev_c2_first = int(c2["dev_us"].iloc[0])

gap_ms = host_c2_first - host_c1_last
reset = dev_c2_first < dev_c1_last

print(f"  C1 last:  dev_us={dev_c1_last:,} µs  host_rx_ms={host_c1_last:.0f}")
print(f"  C2 first: dev_us={dev_c2_first:,} µs  host_rx_ms={host_c2_first:.0f}")
print(f"  BLE gap (host_rx_ms): {gap_ms:.0f} ms = {gap_ms/1000:.1f} s = {gap_ms/60000:.2f} min")
print(f"  dev_us clock reset: {dev_c1_last:,} → {dev_c2_first:,} µs  (RESET={reset})")
print()

# abs_us via load_session_stitched
sessions0303 = cl.discover_sessions(
    os.path.join(os.path.dirname(__file__), "log0303"))
emg_abs, _, recon_times, _ = cl.load_session_stitched(sessions0303)
print(f"  load_session_stitched: total abs_us = {emg_abs.abs_us.max()/1e6/60:.1f} min")
print(f"  Reconnection at {recon_times[0]/60:.2f} min (abs_us)")

# ── Figure 1: BLE batching analysis ──────────────────────────────────────────

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

# Left: CDF of BLE notification interval
sorted_int = np.sort(notif_intervals_ms[::10])  # subsample for speed
cdf_int = np.arange(1, len(sorted_int) + 1) / len(sorted_int) * 100
ax = axes[0]
ax.semilogx(sorted_int, cdf_int, linewidth=1.5, color="#2980b9")
for p, c in [(50, "green"), (95, "orange"), (99, "red")]:
    v = np.percentile(notif_intervals_ms, p)
    ax.axvline(v, color=c, linestyle=":", linewidth=1.2,
               label=f"p{p} = {v:.0f} ms")
ax.set_xlabel("BLE notification interval (ms, log scale)")
ax.set_ylabel("Cumulative (%)")
ax.set_title(f"BLE notification interval distribution\n"
             f"(log0305, 60.1 min, mean {samples_per_notif:.0f} samples/notif)")
ax.legend(fontsize=9)
ax.grid(True, which="both", alpha=0.3)
ax.set_ylim(0, 100)

# Right: 5-second window showing dev_us precision vs host_rx_ms batching
WINDOW_START = 1_000_000  # row index
WINDOW_LEN = 10_000       # 5 s at 2000 Hz
t_window = dev[WINDOW_START:WINDOW_START + WINDOW_LEN] / 1e6
t0 = t_window[0]
h_window = host[WINDOW_START:WINDOW_START + WINDOW_LEN]
ax2 = axes[1]
ax2.scatter(t_window - t0, (h_window - h_window[0]) / 1e3,
            s=0.5, color="#e74c3c", alpha=0.6, label="host_rx_ms (ms)", rasterized=True)
ax2.plot(t_window - t0, (dev[WINDOW_START:WINDOW_START + WINDOW_LEN] - dev[WINDOW_START]) / 1e6 * 1000,
         linewidth=0.6, color="#2980b9", alpha=0.9, label="dev_us (ms, ×1000)")
ax2.set_xlabel("Time within window (s)")
ax2.set_ylabel("Elapsed time (ms)")
ax2.set_title("5-second window: host_rx_ms stepwise vs dev_us smooth\n"
              "(host_rx_ms flat within each BLE notification batch)")
ax2.legend(fontsize=9, markerscale=5)
ax2.grid(True, alpha=0.3)

fig.suptitle("host_rx_ms reconstruction error: batch granularity within a single BLE connection (log0305 files 001–003)",
             fontsize=10)
fig.tight_layout()
out1 = os.path.join(OUTDIR, "fig_absus_error_cdf.png")
fig.savefig(out1, dpi=150, bbox_inches="tight")
print(f"\nSaved: {out1}")
plt.close(fig)

# ── Figure 2: Three-method timeline comparison (log0303 reconnection) ─────────
# Build reconstructions for the log0303 reconnection point.
# Use ALL four files of connection 2 for the abs_us view;
# for Methods A and B use just c1 and c2 for clarity.

c1_full = pd.read_csv(LOG0303_C1, usecols=["dev_us", "host_rx_ms"])
c2_full = pd.read_csv(LOG0303_C2, usecols=["dev_us", "host_rx_ms"])
c1_full = c1_full.sort_values("dev_us").reset_index(drop=True)
c2_full = c2_full.sort_values("dev_us").reset_index(drop=True)

# --- Method A: dev_us-only (no gap, clock reset is invisible) ---
# Append C2 immediately after C1 in dev_us time (shows clock reset as discontinuity)
dev_A_c1 = (c1_full["dev_us"].values - int(c1_full["dev_us"].min())) / 1e6
dev_A_c2 = (c2_full["dev_us"].values - int(c2_full["dev_us"].min())) / 1e6
# "Reconnect" at the end of C1 with zero gap
recon_A = dev_A_c1[-1]
t_A = np.concatenate([dev_A_c1, recon_A + dev_A_c2])
conn_A = np.concatenate([np.zeros(len(c1_full)), np.ones(len(c2_full))])

# --- Method B: host_rx_ms-only ---
h0 = float(c1_full["host_rx_ms"].iloc[0])
t_B_c1 = (c1_full["host_rx_ms"].values - h0) / 1e3
t_B_c2 = (c2_full["host_rx_ms"].values - h0) / 1e3
recon_B = float(c1_full["host_rx_ms"].iloc[-1] - h0) / 1e3 + gap_ms / 1e3
t_B = np.concatenate([t_B_c1, t_B_c2])

# --- Method C: abs_us hybrid (from load_session_stitched) ---
t_C = emg_abs["abs_us"].values / 1e6
recon_C = recon_times[0]

# Plot each method, window = 1 min before/after reconnection
WINDOW_S = 60  # seconds before/after

fig2, axes2 = plt.subplots(3, 1, figsize=(10, 7), sharex=False)

configs = [
    (axes2[0], t_A, conn_A, "A: dev_us-only", recon_A, "#c0392b",
     np.concatenate([np.zeros(len(c1_full)), np.ones(len(c2_full))]),
     "Clock reset: C2 appears immediately after C1\nwith dev_us restarting from ≈0"),
    (axes2[1], t_B, None, "B: host_rx_ms-only", recon_B, "#2980b9", None,
     "Correct gap length, but stepwise resolution\n(~54 samples share one timestamp)"),
    (axes2[2], t_C, None, "C: abs_us hybrid", recon_C, "#27ae60", None,
     "Correct gap + per-sample dev_us precision within each connection"),
]

for ax, t, c, label, recon_t, color, labels, note in configs:
    lo, hi = recon_t - WINDOW_S, recon_t + WINDOW_S
    mask = (t >= lo) & (t <= hi)
    t_rel = t[mask] - recon_t
    ax.scatter(t_rel, np.zeros(mask.sum()), s=0.4, c=color, alpha=0.35, rasterized=True)
    ax.axvline(0, color="black", linestyle="--", linewidth=1.0, label="Reconnection")
    ax.set_xlim(-WINDOW_S, WINDOW_S)
    ax.set_yticks([])
    ax.set_title(f"Method {label}", fontsize=9, fontweight="bold")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:.0f} s"))
    ax.text(0.02, 0.82, note, transform=ax.transAxes, fontsize=8,
            color=color, va="top")

axes2[-1].set_xlabel("Time relative to reconnection event (s)")
fig2.suptitle(
    f"Timeline reconstruction at BLE reconnection (log0303)\n"
    f"BLE gap: {gap_ms/1000:.0f} s | dev_us clock reset confirmed ({dev_c1_last:,}→{dev_c2_first:,} µs)",
    fontsize=10,
)
fig2.tight_layout()
out2 = os.path.join(OUTDIR, "fig_absus_timeline_methods.png")
fig2.savefig(out2, dpi=150, bbox_inches="tight")
print(f"Saved: {out2}")
plt.close(fig2)

# ── Summary table ─────────────────────────────────────────────────────────────

rows = [
    {"Method": "A. dev_us-only",
     "Within-connection precision": "±25 µs per sample",
     "Handles device reboot": "NO — clock restarts, C2 appears immediately after C1",
     "Cross-connection gap accuracy": "None (gap absent)"},
    {"Method": "B. host_rx_ms-only",
     "Within-connection precision": f"Batch-resolution: p50={np.percentile(notif_intervals_ms,50):.0f} ms, "
                                     f"p99={np.percentile(notif_intervals_ms,99):.0f} ms "
                                     f"(~{samples_per_notif:.0f} samples share one timestamp)",
     "Handles device reboot": "YES",
     "Cross-connection gap accuracy": f"±one notification interval (p99 ≈ {np.percentile(notif_intervals_ms,99):.0f} ms)"},
    {"Method": "C. abs_us hybrid (this work)",
     "Within-connection precision": "±25 µs per sample (dev_us)",
     "Handles device reboot": "YES",
     "Cross-connection gap accuracy": f"±one notification interval (p99 ≈ {np.percentile(notif_intervals_ms,99):.0f} ms)"},
]
tbl = pd.DataFrame(rows)
tbl_path = os.path.join(OUTDIR, "table_absus_validation.csv")
tbl.to_csv(tbl_path, index=False)
print(f"Saved: {tbl_path}")

# ── Paper-ready summary ───────────────────────────────────────────────────────
print()
print("=" * 72)
print("N1 VALIDATION — PAPER-READY SUMMARY (for §5.4)")
print("=" * 72)
print(f"\nlog0305 (clean files 001–003): {len(df)/1e6:.2f}M samples, {len(df)/2000/60:.1f} min")
print(f"  BLE notification interval:  p50={np.percentile(notif_intervals_ms,50):.0f} ms, "
      f"p95={np.percentile(notif_intervals_ms,95):.0f} ms, "
      f"p99={np.percentile(notif_intervals_ms,99):.0f} ms")
print(f"  Mean samples per batch:     {samples_per_notif:.1f}")
print(f"  Intra-batch dev_us offset (per-sample timing loss with host_rx_ms-only):")
print(f"    p50={np.percentile(intra_offset_ms,50):.1f} ms, "
      f"p95={np.percentile(intra_offset_ms,95):.1f} ms, "
      f"p99={np.percentile(intra_offset_ms,99):.1f} ms")

print(f"\nlog0303 (clean boundary files):")
print(f"  BLE gap (host_rx_ms): {gap_ms:.0f} ms = {gap_ms/1000:.1f} s = {gap_ms/60000:.2f} min")
print(f"  dev_us clock reset:   {dev_c1_last:,} → {dev_c2_first:,} µs  (RESET={reset})")
print(f"  abs_us session total: {emg_abs.abs_us.max()/1e6/60:.1f} min (via load_session_stitched)")
print(f"  Reconnect at abs_us:  {recon_times[0]/60:.2f} min")
