#!/usr/bin/env python3
"""n2_preimpact_mdf.py

N2: Pre-impact MDF window (Approach B) analysis for journal §6.6.

Computes per-swing MDF using two methods on log0305:
  - Full-window MDF: Welch PSD on full padded swing window (250+1300+450ms)
  - Pre-impact MDF: Welch PSD on [t_impact-600ms, t_impact-20ms] (~580ms,
    nperseg=512), only for swings with acc_dyn peak >= 3.0g

Outputs:
  paper_figures/fig_n2_preimpact_mdf.png  — per-swing MDF comparison figure
  paper_figures/table_n2_preimpact_mdf.csv — summary statistics
"""

import os
import sys

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import emg_util_yaml_runner as runner
import capture_loader as cl

OUTDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "papers", "paper_figures")
os.makedirs(OUTDIR, exist_ok=True)

# ── Load and analyze log0305 ─────────────────────────────────────────────────

print("Loading config...")
cfg = yaml.safe_load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")))
cfg['swing_detection']['impact_mask_thr_g'] = 3.0
cfg['swing_detection']['impact_pre_impact_ms'] = 600

print("Loading log0305 session...")
sessions = cl.discover_sessions(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "log0305"))
emg_df, imu_df, rec_times, _ = cl.load_session_stitched(sessions)
print(f"  {len(emg_df):,} EMG rows, {len(imu_df):,} IMU rows")

print("Detecting swings...")
swings = runner.detect_swings_from_imu(imu_df, cfg)
print(f"  {len(swings)} swings detected")

print("Computing per-swing EMG features (with Approach B pre-impact MDF)...")
feat = runner.per_swing_emg_features_stitched(swings, emg_df, cfg, imu_df)

# ── Results ───────────────────────────────────────────────────────────────────

n_total = len(feat)
n_impact = int(feat['impact_detected'].sum())
n_pre = int(feat['mdf_pre_impact'].notna().sum())
assert n_impact == n_pre, "mdf_pre_impact should be computed for all impact swings"

impact_df = feat[feat['mdf_pre_impact'].notna()].copy()
delta = impact_df['mdf_pre_impact'] - impact_df['mdf']
no_impact_df = feat[~feat['impact_detected']]

print()
print("=" * 72)
print("N2 PRE-IMPACT MDF (Approach B) — PAPER-READY SUMMARY (for §6.6)")
print("=" * 72)
print(f"\nlog0305: {n_total} total swings")
print(f"  Swings with impact_acc_dyn >= 3.0g: {n_impact} ({100*n_impact/n_total:.0f}%)")
print(f"  Swings without detected impact:     {len(no_impact_df)}")
print()
print(f"Full-window MDF (all {n_total} swings):")
print(f"  mean={feat['mdf'].mean():.1f} Hz, std={feat['mdf'].std():.1f} Hz, "
      f"median={feat['mdf'].median():.1f} Hz")
print()
print(f"Full-window MDF (impact swings only, n={n_impact}):")
print(f"  mean={impact_df['mdf'].mean():.1f} Hz, std={impact_df['mdf'].std():.1f} Hz, "
      f"median={impact_df['mdf'].median():.1f} Hz")
print()
print(f"Pre-impact MDF (impact swings only, n={n_pre}, [t-600ms, t-20ms]):")
print(f"  mean={impact_df['mdf_pre_impact'].mean():.1f} Hz, "
      f"std={impact_df['mdf_pre_impact'].std():.1f} Hz, "
      f"median={impact_df['mdf_pre_impact'].median():.1f} Hz")
print()
print(f"Delta (mdf_pre_impact - mdf_full) for impact swings:")
print(f"  mean={delta.mean():.2f} Hz, std={delta.std():.2f} Hz, "
      f"median={delta.median():.2f} Hz")
print(f"  p5={delta.quantile(0.05):.2f} Hz, p25={delta.quantile(0.25):.2f} Hz, "
      f"p75={delta.quantile(0.75):.2f} Hz, p95={delta.quantile(0.95):.2f} Hz")

# ── Figure ────────────────────────────────────────────────────────────────────

fig = plt.figure(figsize=(12, 5))
gs = gridspec.GridSpec(1, 3, figure=fig, wspace=0.35)

# Panel A: MDF distribution comparison (violin + box)
ax0 = fig.add_subplot(gs[0])
mdf_full = impact_df['mdf'].dropna().values
mdf_pre  = impact_df['mdf_pre_impact'].dropna().values

vp = ax0.violinplot([mdf_full, mdf_pre], positions=[1, 2],
                    showmedians=True, showextrema=False, widths=0.6)
colors = ['#2980b9', '#e74c3c']
for i, body in enumerate(vp['bodies']):
    body.set_facecolor(colors[i])
    body.set_alpha(0.4)
vp['cmedians'].set_colors(['#2980b9', '#e74c3c'])
vp['cmedians'].set_linewidth(2.5)

ax0.boxplot([mdf_full, mdf_pre], positions=[1, 2], widths=0.25,
            patch_artist=False, medianprops=dict(color='black', linewidth=1.5),
            whiskerprops=dict(linewidth=0.8), capprops=dict(linewidth=0.8),
            flierprops=dict(marker='.', markersize=2, alpha=0.4))

ax0.set_xticks([1, 2])
ax0.set_xticklabels(['Full-window\nMDF', 'Pre-impact\nMDF\n[t−600ms, t−20ms]'])
ax0.set_ylabel("MDF (Hz)")
ax0.set_title(f"MDF distribution comparison\n(impact swings, n={n_impact})", fontsize=9)
ax0.grid(True, alpha=0.3, axis='y')

# Panel B: Scatter plot (full vs pre-impact per swing)
ax1 = fig.add_subplot(gs[1])
ax1.scatter(mdf_full, mdf_pre, s=4, alpha=0.35, color='#8e44ad')
lo = min(mdf_full.min(), mdf_pre.min())
hi = max(mdf_full.max(), mdf_pre.max())
ax1.plot([lo, hi], [lo, hi], 'k--', linewidth=1.0, label='y=x (no change)')
ax1.set_xlabel("Full-window MDF (Hz)")
ax1.set_ylabel("Pre-impact MDF (Hz)")
ax1.set_title(f"Per-swing: full vs pre-impact MDF\n(n={n_impact} impact swings)", fontsize=9)
ax1.legend(fontsize=8)
ax1.grid(True, alpha=0.3)

# Panel C: CDF of delta
ax2 = fig.add_subplot(gs[2])
delta_sorted = np.sort(delta.values)
cdf_delta = np.arange(1, len(delta_sorted) + 1) / len(delta_sorted) * 100
ax2.plot(delta_sorted, cdf_delta, linewidth=1.5, color='#27ae60')
ax2.axvline(0, color='black', linestyle='--', linewidth=1.0, label='Δ=0 (no change)')
ax2.axvline(delta.median(), color='#e74c3c', linestyle=':', linewidth=1.2,
            label=f'Median Δ={delta.median():.1f} Hz')
ax2.axvline(delta.mean(), color='#2980b9', linestyle=':', linewidth=1.2,
            label=f'Mean Δ={delta.mean():.1f} Hz')
ax2.set_xlabel("Δ MDF = pre-impact − full-window (Hz)")
ax2.set_ylabel("Cumulative (%)")
ax2.set_title("CDF of per-swing MDF shift\n(Approach B − full window)", fontsize=9)
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.3)
ax2.set_ylim(0, 100)

fig.suptitle(
    f"N2: Pre-impact MDF window (Approach B) — log0305, {n_total} swings, "
    f"{n_impact} with acc_dyn ≥ 3.0g\n"
    f"Full MDF: {impact_df['mdf'].mean():.0f}±{impact_df['mdf'].std():.0f} Hz  →  "
    f"Pre-impact: {impact_df['mdf_pre_impact'].mean():.0f}±{impact_df['mdf_pre_impact'].std():.0f} Hz  "
    f"(Δ median={delta.median():.1f} Hz, mean={delta.mean():.1f} Hz)",
    fontsize=9
)
fig.tight_layout()

out_fig = os.path.join(OUTDIR, "fig_n2_preimpact_mdf.png")
fig.savefig(out_fig, dpi=150, bbox_inches="tight")
print(f"\nSaved: {out_fig}")
plt.close(fig)

# ── Summary table ─────────────────────────────────────────────────────────────

rows = [
    {"Metric": "N total swings", "Value": str(n_total)},
    {"Metric": "N swings with impact_acc_dyn >= 3.0g", "Value": str(n_impact)},
    {"Metric": "Full-window MDF (impact swings): mean ± std",
     "Value": f"{impact_df['mdf'].mean():.1f} ± {impact_df['mdf'].std():.1f} Hz"},
    {"Metric": "Full-window MDF (impact swings): median",
     "Value": f"{impact_df['mdf'].median():.1f} Hz"},
    {"Metric": "Pre-impact MDF (impact swings): mean ± std",
     "Value": f"{impact_df['mdf_pre_impact'].mean():.1f} ± {impact_df['mdf_pre_impact'].std():.1f} Hz"},
    {"Metric": "Pre-impact MDF (impact swings): median",
     "Value": f"{impact_df['mdf_pre_impact'].median():.1f} Hz"},
    {"Metric": "Delta (pre-impact - full): mean ± std",
     "Value": f"{delta.mean():.2f} ± {delta.std():.2f} Hz"},
    {"Metric": "Delta (pre-impact - full): median",
     "Value": f"{delta.median():.2f} Hz"},
    {"Metric": "Delta: p5, p25, p75, p95",
     "Value": f"{delta.quantile(0.05):.1f}, {delta.quantile(0.25):.1f}, "
              f"{delta.quantile(0.75):.1f}, {delta.quantile(0.95):.1f} Hz"},
    {"Metric": "Pre-impact window",
     "Value": "[t_impact - 600 ms, t_impact - 20 ms] ≈ 580 ms (nperseg=512)"},
]
tbl = pd.DataFrame(rows)
tbl_path = os.path.join(OUTDIR, "table_n2_preimpact_mdf.csv")
tbl.to_csv(tbl_path, index=False)
print(f"Saved: {tbl_path}")
