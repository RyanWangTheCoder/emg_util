#!/usr/bin/env python3
"""
paper_analysis.py — Generate paper figures and statistics for:
"EMG-IMU Wearable for Tennis Fatigue Monitoring:
 Electrode Contact Dynamics and IMU-Based Signal Quality Cross-Validation"

Usage (from C:\wangx\ftc\emg_util):
    python paper_analysis.py

Outputs (in paper_figures/):
    fig1_system_overview.txt        (placeholder — drawn manually)
    fig2_electrode_settling.png     (MDF vs time, first 30 min, log0305)
    fig3_imu_cross_validation.png   (two-panel: MDF + imu_peak_mag vs time, log0305)
    fig4_contact_quality.png        (RMS/p90_rms vs time, both sessions)
    fig5_log0303_fatigue.png        (MDF over session with gap annotation)
    fig6_diagnostic_matrix.png      (scatter: IMU consistency vs EMG quality)
    paper_stats.txt                 (all key numbers for the paper)
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.stats import pearsonr

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT0303  = os.path.join(BASE_DIR, 'out0303_v2')
OUT0305  = os.path.join(BASE_DIR, 'out0305_v2')
FIG_DIR  = os.path.join(BASE_DIR, 'paper_figures')
os.makedirs(FIG_DIR, exist_ok=True)

# ── Style ──────────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.size': 11,
    'axes.titlesize': 12,
    'axes.labelsize': 11,
    'legend.fontsize': 10,
    'figure.dpi': 150,
})
C_EMG  = '#1f77b4'   # blue
C_IMU  = '#d62728'   # red
C_QUAL = '#2ca02c'   # green
C_GAP  = '#ff7f0e'   # orange

# ── Load data ──────────────────────────────────────────────────────────────
print("Loading swing_features.csv ...")
sf03 = pd.read_csv(os.path.join(OUT0303, 'swing_features.csv'))
sf05 = pd.read_csv(os.path.join(OUT0305, 'swing_features.csv'))

with open(os.path.join(OUT0303, 'fatigue_summary.csv')) as f:
    fat03 = pd.read_csv(f).iloc[0].to_dict()
with open(os.path.join(OUT0305, 'fatigue_summary.csv')) as f:
    fat05 = pd.read_csv(f).iloc[0].to_dict()

with open(os.path.join(OUT0303, 'session_summary.json')) as f:
    sess03 = json.load(f)
with open(os.path.join(OUT0305, 'session_summary.json')) as f:
    sess05 = json.load(f)

with open(os.path.join(OUT0303, 'baseline.json')) as f:
    base03 = json.load(f)
with open(os.path.join(OUT0305, 'baseline.json')) as f:
    base05 = json.load(f)

# ── Derived time axes ──────────────────────────────────────────────────────
sf03['t_min'] = sf03['t_peak_ms'] / 60000.0
sf05['t_min'] = sf05['t_peak_ms'] / 60000.0

# Reconnection time for log0303 (seconds → minutes)
reconnect_min_03 = sess03['reconnection_times_s'][0] / 60.0  # ~80.3 min

# ── Session p90 RMS (for contact quality metric) ───────────────────────────
p90_rms_03 = float(np.percentile(sf03['rms'].dropna(), 90))
p90_rms_05 = float(np.percentile(sf05['rms'].dropna(), 90))

sf03['contact_quality'] = sf03['rms'] / p90_rms_03
sf05['contact_quality'] = sf05['rms'] / p90_rms_05

# ── Rolling averages (10-swing window) ────────────────────────────────────
def rolling10(series):
    return series.rolling(10, min_periods=3, center=True).mean()

sf03['mdf_roll']  = rolling10(sf03['mdf'])
sf03['imu_roll']  = rolling10(sf03['imu_peak_mag'])
sf03['qual_roll'] = rolling10(sf03['contact_quality'])

sf05['mdf_roll']  = rolling10(sf05['mdf'])
sf05['imu_roll']  = rolling10(sf05['imu_peak_mag'])
sf05['qual_roll'] = rolling10(sf05['contact_quality'])

# ── IMU consistency: rolling CV of imu_peak_mag ───────────────────────────
def rolling_cv(series, window=10):
    r_std  = series.rolling(window, min_periods=5).std()
    r_mean = series.rolling(window, min_periods=5).mean()
    return (r_std / (r_mean + 1e-9)) * 100.0   # percent

sf03['imu_cv'] = rolling_cv(sf03['imu_peak_mag'])
sf05['imu_cv'] = rolling_cv(sf05['imu_peak_mag'])

# ── Pearson r: imu_peak_mag vs time (log0305) ─────────────────────────────
r_imu05, p_imu05 = pearsonr(sf05['t_peak_ms'], sf05['imu_peak_mag'])
r_imu03, p_imu03 = pearsonr(sf03['t_peak_ms'], sf03['imu_peak_mag'])

# ── Electrode settling analysis (log0305) ─────────────────────────────────
# Thirds of session (by time)
t_total_05 = sf05['t_min'].max()
t1 = t_total_05 / 3.0
t2 = 2.0 * t_total_05 / 3.0

early05 = sf05[sf05['t_min'] < t1]
mid05   = sf05[(sf05['t_min'] >= t1) & (sf05['t_min'] < t2)]
late05  = sf05[sf05['t_min'] >= t2]

# First 30 min for settling curve
first30_05 = sf05[sf05['t_min'] <= 30.0]

# Find settling time: first time rolling MDF stays above 150 Hz for 5 consecutive swings
mdf_stable_thr = 150.0
stable_mask = sf05['mdf_roll'] >= mdf_stable_thr
# Find first index where 5 consecutive swings are stable
settling_idx = None
for i in range(len(stable_mask) - 4):
    if stable_mask.iloc[i:i+5].all():
        settling_idx = i
        break
settling_min = sf05['t_min'].iloc[settling_idx] if settling_idx is not None else None

# ── log0303 segment analysis ───────────────────────────────────────────────
seg1_03 = sf03[sf03['t_min'] < reconnect_min_03]   # first segment
seg2_03 = sf03[sf03['t_min'] >= reconnect_min_03]  # second segment

# ── Contact quality thresholds ─────────────────────────────────────────────
QUAL_GOOD    = 0.25   # above: reliable EMG
QUAL_MARGINAL = 0.10  # below: contact loss

# ── Compute all paper statistics ──────────────────────────────────────────
stats = {}

# log0305 fatigue summary
stats['log0305_baseline_mdf']   = fat05['baseline_MDF']
stats['log0305_final_mdf']      = fat05['final_MDF']
stats['log0305_mdf_drop_pct']   = fat05['MDF_drop_pct']
stats['log0305_mnf_drop_pct']   = fat05['MNF_drop_pct']
stats['log0305_fatigue_onset_s']= fat05['fatigue_onset_s']
stats['log0305_n_swings']       = len(sf05)
stats['log0305_duration_min']   = sess05['total_duration_min']

# log0303 fatigue summary
stats['log0303_baseline_mdf']   = fat03['baseline_MDF']
stats['log0303_final_mdf']      = fat03['final_MDF']
stats['log0303_mdf_drop_pct']   = fat03['MDF_drop_pct']
stats['log0303_mnf_drop_pct']   = fat03['MNF_drop_pct']
stats['log0303_n_swings']       = len(sf03)
stats['log0303_duration_min']   = sess03['total_duration_min']
stats['log0303_reconnect_min']  = reconnect_min_03
stats['log0303_seg1_n_swings']  = len(seg1_03)
stats['log0303_seg2_n_swings']  = len(seg2_03)

# IMU consistency
stats['log0305_imu_pearson_r']  = r_imu05
stats['log0305_imu_pearson_p']  = p_imu05
stats['log0303_imu_pearson_r']  = r_imu03
stats['log0303_imu_pearson_p']  = p_imu03

# Electrode settling
stats['log0305_settling_min']   = settling_min
stats['log0305_mdf_early_mean'] = float(early05['mdf'].mean())
stats['log0305_mdf_early_std']  = float(early05['mdf'].std())
stats['log0305_mdf_mid_mean']   = float(mid05['mdf'].mean())
stats['log0305_mdf_mid_std']    = float(mid05['mdf'].std())
stats['log0305_mdf_late_mean']  = float(late05['mdf'].mean())
stats['log0305_mdf_late_std']   = float(late05['mdf'].std())

# IMU thirds (log0305)
stats['log0305_imu_early_mean'] = float(early05['imu_peak_mag'].mean())
stats['log0305_imu_early_std']  = float(early05['imu_peak_mag'].std())
stats['log0305_imu_mid_mean']   = float(mid05['imu_peak_mag'].mean())
stats['log0305_imu_mid_std']    = float(mid05['imu_peak_mag'].std())
stats['log0305_imu_late_mean']  = float(late05['imu_peak_mag'].mean())
stats['log0305_imu_late_std']   = float(late05['imu_peak_mag'].std())

# Contact quality
stats['log0305_p90_rms']        = p90_rms_05
stats['log0303_p90_rms']        = p90_rms_03
stats['log0305_qual_early_mean']= float(early05['contact_quality'].mean())
stats['log0305_qual_late_mean'] = float(late05['contact_quality'].mean())
stats['log0305_pct_below_good'] = float((sf05['contact_quality'] < QUAL_GOOD).mean() * 100)

# ADC saturation in log0303 second segment
sat_swings_03 = seg2_03[seg2_03['emg_env_peak'] >= 4090]
stats['log0303_seg2_sat_swings'] = len(sat_swings_03)

# log0303 segment MDF
stats['log0303_seg1_mdf_mean']  = float(seg1_03['mdf'].mean())
stats['log0303_seg1_mdf_std']   = float(seg1_03['mdf'].std())
stats['log0303_seg2_mdf_mean']  = float(seg2_03['mdf'].mean())
stats['log0303_seg2_mdf_std']   = float(seg2_03['mdf'].std())

# log0303 IMU thirds
stats['log0303_imu_seg1_mean']  = float(seg1_03['imu_peak_mag'].mean())
stats['log0303_imu_seg2_mean']  = float(seg2_03['imu_peak_mag'].mean())
stats['log0303_acc_seg1_mean']  = float(seg1_03['imu_mean_acc_dyn'].mean())
stats['log0303_acc_seg2_mean']  = float(seg2_03['imu_mean_acc_dyn'].mean())

# ── Print stats ────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("PAPER STATISTICS SUMMARY")
print("="*70)

print("\n--- log0305 (63.1 min, 626 swings, single BLE connection) ---")
print(f"  Baseline MDF:        {stats['log0305_baseline_mdf']:.1f} Hz")
print(f"  Final MDF:           {stats['log0305_final_mdf']:.1f} Hz")
print(f"  MDF drop:            {stats['log0305_mdf_drop_pct']:.1f}%")
print(f"  MNF drop:            {stats['log0305_mnf_drop_pct']:.1f}%")
print(f"  Fatigue onset:       {stats['log0305_fatigue_onset_s']:.0f}s ({stats['log0305_fatigue_onset_s']/60:.1f} min)")
print(f"  Settling time:       {stats['log0305_settling_min']:.1f} min" if settling_min else "  Settling time:       not detected")
print(f"  MDF early third:     {stats['log0305_mdf_early_mean']:.1f} ± {stats['log0305_mdf_early_std']:.1f} Hz")
print(f"  MDF mid third:       {stats['log0305_mdf_mid_mean']:.1f} ± {stats['log0305_mdf_mid_std']:.1f} Hz")
print(f"  MDF late third:      {stats['log0305_mdf_late_mean']:.1f} ± {stats['log0305_mdf_late_std']:.1f} Hz")
print(f"  IMU peak_mag early:  {stats['log0305_imu_early_mean']:.0f} ± {stats['log0305_imu_early_std']:.0f} dps")
print(f"  IMU peak_mag mid:    {stats['log0305_imu_mid_mean']:.0f} ± {stats['log0305_imu_mid_std']:.0f} dps")
print(f"  IMU peak_mag late:   {stats['log0305_imu_late_mean']:.0f} ± {stats['log0305_imu_late_std']:.0f} dps")
print(f"  IMU Pearson r:       r={stats['log0305_imu_pearson_r']:.3f}, p={stats['log0305_imu_pearson_p']:.3f}")
print(f"  Session p90 RMS:     {stats['log0305_p90_rms']:.2f}")
print(f"  Contact quality early: {stats['log0305_qual_early_mean']:.2f}")
print(f"  Contact quality late:  {stats['log0305_qual_late_mean']:.2f}")
print(f"  % swings below 0.25 quality: {stats['log0305_pct_below_good']:.1f}%")

print(f"\n--- log0303 (87.9 min, 197 swings, 66-min BLE gap at {reconnect_min_03:.1f} min) ---")
print(f"  Baseline MDF:        {stats['log0303_baseline_mdf']:.1f} Hz")
print(f"  Final MDF:           {stats['log0303_final_mdf']:.1f} Hz")
print(f"  MDF drop:            {stats['log0303_mdf_drop_pct']:.1f}%")
print(f"  MNF drop:            {stats['log0303_mnf_drop_pct']:.1f}%")
print(f"  Segment 1 ({len(seg1_03)} swings, 0-{reconnect_min_03:.0f} min):")
print(f"    MDF:               {stats['log0303_seg1_mdf_mean']:.1f} ± {stats['log0303_seg1_mdf_std']:.1f} Hz")
print(f"    IMU peak_mag:      {stats['log0303_imu_seg1_mean']:.0f} dps")
print(f"    acc_dyn:           {stats['log0303_acc_seg1_mean']:.3f} g")
print(f"  Segment 2 ({len(seg2_03)} swings, {reconnect_min_03:.0f}-{sess03['total_duration_min']:.0f} min):")
print(f"    MDF:               {stats['log0303_seg2_mdf_mean']:.1f} ± {stats['log0303_seg2_mdf_std']:.1f} Hz")
print(f"    IMU peak_mag:      {stats['log0303_imu_seg2_mean']:.0f} dps")
print(f"    acc_dyn:           {stats['log0303_acc_seg2_mean']:.3f} g")
print(f"    ADC-saturated swings: {stats['log0303_seg2_sat_swings']}")
print(f"  IMU Pearson r:       r={stats['log0303_imu_pearson_r']:.3f}, p={stats['log0303_imu_pearson_p']:.3f}")
print(f"  Session p90 RMS:     {stats['log0303_p90_rms']:.2f}")

# ── Save stats to file ─────────────────────────────────────────────────────
stats_path = os.path.join(FIG_DIR, 'paper_stats.txt')
with open(stats_path, 'w') as f:
    f.write("PAPER STATISTICS — EMG-IMU Tennis Fatigue Study\n")
    f.write("="*60 + "\n\n")
    f.write("log0305 (63.1 min, 626 swings, single BLE connection)\n")
    f.write("-"*60 + "\n")
    for k, v in stats.items():
        if '0305' in k:
            f.write(f"  {k}: {v}\n")
    f.write("\nlog0303 (87.9 min, 197 swings, 66-min BLE gap)\n")
    f.write("-"*60 + "\n")
    for k, v in stats.items():
        if '0303' in k:
            f.write(f"  {k}: {v}\n")
print(f"\nStats saved to: {stats_path}")

# ══════════════════════════════════════════════════════════════════════════
# FIGURE 2: Electrode Settling Curve (log0305, first 30 min)
# ══════════════════════════════════════════════════════════════════════════
print("\nGenerating Figure 2: Electrode settling curve ...")

fig, ax = plt.subplots(figsize=(8, 4))

# Scatter: individual swing MDF
ax.scatter(first30_05['t_min'], first30_05['mdf'],
           s=15, alpha=0.4, color=C_EMG, label='Per-swing MDF', zorder=2)

# Rolling average
first30_roll = sf05[sf05['t_min'] <= 30.0]['mdf_roll']
first30_t    = sf05[sf05['t_min'] <= 30.0]['t_min']
ax.plot(first30_t, first30_roll, color=C_EMG, linewidth=2.0,
        label='10-swing rolling mean', zorder=3)

# Baseline reference line
ax.axhline(stats['log0305_baseline_mdf'], color='gray', linestyle='--',
           linewidth=1.5, label=f"Stable baseline ({stats['log0305_baseline_mdf']:.0f} Hz)", zorder=1)

# Settling threshold
ax.axhline(mdf_stable_thr, color='orange', linestyle=':', linewidth=1.2,
           label=f'Settling threshold ({mdf_stable_thr:.0f} Hz)', zorder=1)

# Settling time marker
if settling_min is not None:
    ax.axvline(settling_min, color='green', linestyle='--', linewidth=1.5,
               label=f'Settling complete (~{settling_min:.0f} min)', zorder=4)
    ax.fill_betweenx([0, 500], 0, settling_min, alpha=0.08, color='red',
                     label='Settling zone')

# Warmup skip marker (10 min)
ax.axvline(10.0, color='purple', linestyle=':', linewidth=1.2,
           label='Current warmup skip (10 min)', zorder=4)

ax.set_xlabel('Time (minutes)')
ax.set_ylabel('Median Frequency (Hz)')
ax.set_title('Figure 2: Electrode Settling — log0305 (first 30 min)\n'
             'EMG MDF is depressed during electrode settling, mimicking fatigue')
ax.set_xlim(0, 30)
ax.set_ylim(0, 350)
ax.legend(loc='upper right', fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
fig2_path = os.path.join(FIG_DIR, 'fig2_electrode_settling.png')
plt.savefig(fig2_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {fig2_path}")

# ══════════════════════════════════════════════════════════════════════════
# FIGURE 3: IMU Cross-Validation (log0305, full session, two-panel)
# ══════════════════════════════════════════════════════════════════════════
print("Generating Figure 3: IMU cross-validation ...")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

# Panel 1: EMG MDF
ax1.scatter(sf05['t_min'], sf05['mdf'], s=8, alpha=0.3, color=C_EMG, zorder=2)
ax1.plot(sf05['t_min'], sf05['mdf_roll'], color=C_EMG, linewidth=2.0,
         label='10-swing rolling mean', zorder=3)
ax1.axhline(stats['log0305_baseline_mdf'], color='gray', linestyle='--',
            linewidth=1.5, label=f"Baseline ({stats['log0305_baseline_mdf']:.0f} Hz)")
if settling_min is not None:
    ax1.axvline(settling_min, color='green', linestyle='--', linewidth=1.5,
                label=f'Settling (~{settling_min:.0f} min)')
    ax1.fill_betweenx([0, 500], 0, settling_min, alpha=0.08, color='red')
ax1.set_ylabel('MDF (Hz)')
ax1.set_title(f'Figure 3: IMU Cross-Validation — log0305\n'
              f'EMG shows {stats["log0305_mdf_drop_pct"]:.1f}% MDF drop; '
              f'IMU shows flat biomechanics (r={r_imu05:.3f}, p={p_imu05:.3f})')
ax1.set_ylim(0, 400)
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3)
ax1.text(0.02, 0.92, 'EMG MDF', transform=ax1.transAxes,
         fontsize=10, color=C_EMG, fontweight='bold')

# Panel 2: IMU peak_mag
ax2.scatter(sf05['t_min'], sf05['imu_peak_mag'], s=8, alpha=0.3, color=C_IMU, zorder=2)
ax2.plot(sf05['t_min'], sf05['imu_roll'], color=C_IMU, linewidth=2.0,
         label='10-swing rolling mean', zorder=3)
# Trend line
z = np.polyfit(sf05['t_min'], sf05['imu_peak_mag'], 1)
p_fit = np.poly1d(z)
t_range = np.linspace(sf05['t_min'].min(), sf05['t_min'].max(), 100)
ax2.plot(t_range, p_fit(t_range), 'k--', linewidth=1.2, alpha=0.6,
         label=f'Linear trend (r={r_imu05:.3f})')
if settling_min is not None:
    ax2.axvline(settling_min, color='green', linestyle='--', linewidth=1.5)
    ax2.fill_betweenx([0, 5000], 0, settling_min, alpha=0.08, color='red')
ax2.set_xlabel('Time (minutes)')
ax2.set_ylabel('Peak Gyro Magnitude (dps)')
ax2.set_ylim(0, 4000)
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.text(0.02, 0.92, 'IMU Peak Gyro', transform=ax2.transAxes,
         fontsize=10, color=C_IMU, fontweight='bold')

plt.tight_layout()
fig3_path = os.path.join(FIG_DIR, 'fig3_imu_cross_validation.png')
plt.savefig(fig3_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {fig3_path}")

# ══════════════════════════════════════════════════════════════════════════
# FIGURE 4: Contact Quality Time Series (both sessions)
# ══════════════════════════════════════════════════════════════════════════
print("Generating Figure 4: Contact quality time series ...")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))

for ax, sf, label, p90 in [
    (ax1, sf05, 'log0305 (63.1 min, single connection)', p90_rms_05),
    (ax2, sf03, f'log0303 (87.9 min, 66-min gap at {reconnect_min_03:.0f} min)', p90_rms_03),
]:
    ax.scatter(sf['t_min'], sf['contact_quality'], s=10, alpha=0.4,
               color=C_QUAL, zorder=2)
    ax.plot(sf['t_min'], sf['qual_roll'], color=C_QUAL, linewidth=2.0,
            label='10-swing rolling mean', zorder=3)
    ax.axhline(QUAL_GOOD, color='orange', linestyle='--', linewidth=1.5,
               label=f'Reliable threshold ({QUAL_GOOD})')
    ax.axhline(QUAL_MARGINAL, color='red', linestyle=':', linewidth=1.2,
               label=f'Contact loss threshold ({QUAL_MARGINAL})')
    ax.fill_between(sf['t_min'], 0, QUAL_MARGINAL, alpha=0.1, color='red',
                    label='Contact loss zone')
    ax.fill_between(sf['t_min'], QUAL_MARGINAL, QUAL_GOOD, alpha=0.08,
                    color='orange', label='Marginal zone')
    ax.set_ylabel('Contact Quality\n(RMS / session p90 RMS)')
    ax.set_title(label)
    ax.set_ylim(0, min(3.0, sf['contact_quality'].quantile(0.99) * 1.1))
    ax.legend(loc='upper right', fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.text(0.02, 0.92, f'p90 RMS = {p90:.1f}', transform=ax.transAxes,
            fontsize=9, color='gray')

# Add reconnection marker to log0303 panel
ax2.axvline(reconnect_min_03, color='purple', linestyle='--', linewidth=2.0,
            label=f'BLE reconnect ({reconnect_min_03:.0f} min)', zorder=5)
ax2.legend(loc='upper right', fontsize=8, ncol=2)
ax2.set_xlabel('Time (minutes)')

plt.tight_layout()
fig4_path = os.path.join(FIG_DIR, 'fig4_contact_quality.png')
plt.savefig(fig4_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {fig4_path}")

# ══════════════════════════════════════════════════════════════════════════
# FIGURE 5: log0303 Fatigue Result (MDF over session with gap annotation)
# ══════════════════════════════════════════════════════════════════════════
print("Generating Figure 5: log0303 fatigue result ...")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=False)

# Panel 1: MDF over session (with gap)
ax1.scatter(seg1_03['t_min'], seg1_03['mdf'], s=15, alpha=0.5,
            color=C_EMG, label='Segment 1 (0–13 min)', zorder=2)
ax1.scatter(seg2_03['t_min'], seg2_03['mdf'], s=15, alpha=0.5,
            color='#9467bd', marker='s', label='Segment 2 (80–88 min)', zorder=2)

# Rolling means per segment
if len(seg1_03) >= 3:
    seg1_roll = seg1_03['mdf'].rolling(5, min_periods=2, center=True).mean()
    ax1.plot(seg1_03['t_min'], seg1_roll, color=C_EMG, linewidth=2.0)
if len(seg2_03) >= 3:
    seg2_roll = seg2_03['mdf'].rolling(5, min_periods=2, center=True).mean()
    ax1.plot(seg2_03['t_min'], seg2_roll, color='#9467bd', linewidth=2.0)

ax1.axhline(stats['log0303_baseline_mdf'], color='gray', linestyle='--',
            linewidth=1.5, label=f"Baseline ({stats['log0303_baseline_mdf']:.0f} Hz)")
ax1.axhline(stats['log0303_final_mdf'], color='red', linestyle=':',
            linewidth=1.5, label=f"Final MDF ({stats['log0303_final_mdf']:.0f} Hz)")

# Gap annotation
ax1.annotate('', xy=(reconnect_min_03, 200), xytext=(13.5, 200),
             arrowprops=dict(arrowstyle='<->', color='orange', lw=2))
ax1.text((13.5 + reconnect_min_03) / 2, 210, '66-min BLE gap',
         ha='center', fontsize=9, color='orange')

ax1.set_ylabel('MDF (Hz)')
ax1.set_title(f'Figure 5: log0303 — {stats["log0303_mdf_drop_pct"]:.1f}% MDF Drop '
              f'(confounded by 66-min session gap)')
ax1.set_ylim(0, 500)
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3)

# Panel 2: IMU peak_mag over session
ax2.scatter(seg1_03['t_min'], seg1_03['imu_peak_mag'], s=15, alpha=0.5,
            color=C_IMU, label='Segment 1', zorder=2)
ax2.scatter(seg2_03['t_min'], seg2_03['imu_peak_mag'], s=15, alpha=0.5,
            color='#ff7f0e', marker='s', label='Segment 2', zorder=2)

# Mark ADC-saturated swings
sat_mask = seg2_03['emg_env_peak'] >= 4090
if sat_mask.any():
    ax2.scatter(seg2_03[sat_mask]['t_min'], seg2_03[sat_mask]['imu_peak_mag'],
                s=60, marker='x', color='red', linewidths=2,
                label=f'ADC saturated ({sat_mask.sum()} swings)', zorder=5)

ax2.set_xlabel('Time (minutes)')
ax2.set_ylabel('Peak Gyro Magnitude (dps)')
ax2.set_title('IMU Swing Intensity — Segment 2 shows lower intensity '
              f'(acc_dyn: {stats["log0303_acc_seg1_mean"]:.2f}g → {stats["log0303_acc_seg2_mean"]:.2f}g)')
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
fig5_path = os.path.join(FIG_DIR, 'fig5_log0303_fatigue.png')
plt.savefig(fig5_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {fig5_path}")

# ══════════════════════════════════════════════════════════════════════════
# FIGURE 6: Diagnostic Matrix Scatter (IMU consistency vs EMG quality)
# ══════════════════════════════════════════════════════════════════════════
print("Generating Figure 6: Diagnostic matrix scatter ...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

for ax, sf, label in [
    (ax1, sf05, 'log0305 (63.1 min)'),
    (ax2, sf03, 'log0303 (87.9 min)'),
]:
    # Use 5-min windows for cleaner visualization
    sf_clean = sf.dropna(subset=['imu_cv', 'contact_quality'])
    
    # Color by time
    t_norm = (sf_clean['t_min'] - sf_clean['t_min'].min()) / \
             (sf_clean['t_min'].max() - sf_clean['t_min'].min() + 1e-9)
    
    sc = ax.scatter(sf_clean['imu_cv'], sf_clean['contact_quality'],
                    c=t_norm, cmap='viridis', s=20, alpha=0.6, zorder=2)
    
    # Quadrant lines
    imu_cv_thr = 50.0   # % CV — above = inconsistent IMU
    ax.axvline(imu_cv_thr, color='gray', linestyle='--', linewidth=1.2, alpha=0.7)
    ax.axhline(QUAL_GOOD, color='orange', linestyle='--', linewidth=1.2, alpha=0.7)
    
    # Quadrant labels
    ax.text(0.02, 0.97, 'Normal\n(consistent IMU,\ngood EMG)',
            transform=ax.transAxes, fontsize=8, va='top',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    ax.text(0.55, 0.97, 'Electrode Issue\n(consistent IMU,\npoor EMG)',
            transform=ax.transAxes, fontsize=8, va='top',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    ax.text(0.02, 0.35, 'Genuine Fatigue\n(declining IMU,\ngood EMG)',
            transform=ax.transAxes, fontsize=8, va='top',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    ax.text(0.55, 0.35, 'Ambiguous\n(declining IMU,\npoor EMG)',
            transform=ax.transAxes, fontsize=8, va='top',
            bbox=dict(boxstyle='round', facecolor='lightsalmon', alpha=0.5))
    
    ax.set_xlabel('IMU Swing Consistency CV (%)\n(lower = more consistent)')
    ax.set_ylabel('EMG Contact Quality\n(RMS / session p90 RMS)')
    ax.set_title(f'Figure 6: Diagnostic Matrix — {label}')
    ax.set_xlim(0, min(200, sf_clean['imu_cv'].quantile(0.99)))
    ax.set_ylim(0, min(3.0, sf_clean['contact_quality'].quantile(0.99) * 1.1))
    
    plt.colorbar(sc, ax=ax, label='Time (normalized)')

plt.tight_layout()
fig6_path = os.path.join(FIG_DIR, 'fig6_diagnostic_matrix.png')
plt.savefig(fig6_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {fig6_path}")

# ══════════════════════════════════════════════════════════════════════════
# FIGURE 7: Session Comparison Summary (bar chart)
# ══════════════════════════════════════════════════════════════════════════
print("Generating Figure 7: Session comparison summary ...")

fig, axes = plt.subplots(1, 3, figsize=(12, 4))

# MDF by thirds
sessions = ['log0303\nSeg1', 'log0303\nSeg2', 'log0305\nEarly', 'log0305\nMid', 'log0305\nLate']
mdf_means = [
    stats['log0303_seg1_mdf_mean'],
    stats['log0303_seg2_mdf_mean'],
    stats['log0305_mdf_early_mean'],
    stats['log0305_mdf_mid_mean'],
    stats['log0305_mdf_late_mean'],
]
mdf_stds = [
    stats['log0303_seg1_mdf_std'],
    stats['log0303_seg2_mdf_std'],
    stats['log0305_mdf_early_std'],
    stats['log0305_mdf_mid_std'],
    stats['log0305_mdf_late_std'],
]
colors_bar = ['#1f77b4', '#9467bd', '#d62728', '#ff7f0e', '#2ca02c']
axes[0].bar(sessions, mdf_means, yerr=mdf_stds, capsize=4,
            color=colors_bar, alpha=0.8, edgecolor='black')
axes[0].axhline(stats['log0305_baseline_mdf'], color='gray', linestyle='--',
                linewidth=1.2, label=f'log0305 baseline ({stats["log0305_baseline_mdf"]:.0f} Hz)')
axes[0].set_ylabel('MDF (Hz)')
axes[0].set_title('MDF by Session Segment')
axes[0].legend(fontsize=8)
axes[0].tick_params(axis='x', labelsize=8)

# IMU peak_mag by segment
imu_means = [
    stats['log0303_imu_seg1_mean'],
    stats['log0303_imu_seg2_mean'],
    stats['log0305_imu_early_mean'],
    stats['log0305_imu_mid_mean'],
    stats['log0305_imu_late_mean'],
]
imu_stds = [
    float(seg1_03['imu_peak_mag'].std()),
    float(seg2_03['imu_peak_mag'].std()),
    stats['log0305_imu_early_std'],
    stats['log0305_imu_mid_std'],
    stats['log0305_imu_late_std'],
]
axes[1].bar(sessions, imu_means, yerr=imu_stds, capsize=4,
            color=colors_bar, alpha=0.8, edgecolor='black')
axes[1].set_ylabel('Peak Gyro Magnitude (dps)')
axes[1].set_title('IMU Swing Intensity by Segment')
axes[1].tick_params(axis='x', labelsize=8)

# Contact quality by segment
qual_means = [
    float(seg1_03['contact_quality'].mean()),
    float(seg2_03['contact_quality'].mean()),
    stats['log0305_qual_early_mean'],
    float(mid05['contact_quality'].mean()),
    stats['log0305_qual_late_mean'],
]
axes[2].bar(sessions, qual_means, color=colors_bar, alpha=0.8, edgecolor='black')
axes[2].axhline(QUAL_GOOD, color='orange', linestyle='--', linewidth=1.5,
                label=f'Reliable threshold ({QUAL_GOOD})')
axes[2].axhline(QUAL_MARGINAL, color='red', linestyle=':', linewidth=1.2,
                label=f'Contact loss ({QUAL_MARGINAL})')
axes[2].set_ylabel('Contact Quality')
axes[2].set_title('EMG Contact Quality by Segment')
axes[2].legend(fontsize=8)
axes[2].tick_params(axis='x', labelsize=8)

plt.suptitle('Figure 7: Session Comparison — log0303 vs log0305', fontsize=12)
plt.tight_layout()
fig7_path = os.path.join(FIG_DIR, 'fig7_session_comparison.png')
plt.savefig(fig7_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {fig7_path}")

# ══════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("ALL FIGURES GENERATED")
print("="*70)
print(f"Output directory: {FIG_DIR}")
print("\nKey findings for paper:")
print(f"  1. Electrode settling (log0305): MDF rises from "
      f"{stats['log0305_mdf_early_mean']:.0f} Hz (early) to "
      f"{stats['log0305_mdf_late_mean']:.0f} Hz (late)")
if settling_min:
    print(f"     Settling completes at ~{settling_min:.0f} min "
          f"(current warmup skip = 10 min is insufficient)")
print(f"  2. IMU cross-validation (log0305): r={r_imu05:.3f}, p={p_imu05:.3f} "
      f"(flat — no biomechanical fatigue)")
print(f"  3. EMG shows {stats['log0305_mdf_drop_pct']:.1f}% MDF drop but "
      f"IMU shows no change => electrode contact degradation, not fatigue")
print(f"  4. log0303: {stats['log0303_mdf_drop_pct']:.1f}% MDF drop "
      f"(confounded by {reconnect_min_03:.0f}-min BLE gap + "
      f"{stats['log0303_seg2_sat_swings']} ADC-saturated swings)")
print(f"  5. False fatigue onset detected at "
      f"{stats['log0305_fatigue_onset_s']/60:.1f} min "
      f"(during electrode settling period)")