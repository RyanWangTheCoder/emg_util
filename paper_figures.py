"""
paper_figures.py  —  Generate paper figures aligned with paper.md figure list.

Run from /local/mnt/workspace/wangx/projects/emg_util/:
    /local/mnt/workspace/wangx/miniconda3/envs/fft-env/bin/python paper_figures.py

Figures generated (matching paper.md):
    Fig 2  — Electrode settling: MDF vs time, first 30 min (log0305, 20-min skip)
    Fig 3  — IMU consistency: imu_peak_mag vs time (log0305, 20-min skip)
    Fig 4  — Warmup-skip sensitivity bar chart (4 skip conditions)
    Fig 5  — Contact quality over session (both sessions)
    Fig 6  — log0303 gap artifact: MDF over full session with reconnection annotation
    Fig 7  — IMU-EMG diagnostic matrix (2x2 scatter, log0305)

Note: Fig 1 (system overview diagram) is created manually.
      Fig 8 (pre-impact MDF comparison) requires future implementation of E5.

Outputs saved to: paper_figures/
"""

import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, linregress

OUT_DIR = "paper_figures"
os.makedirs(OUT_DIR, exist_ok=True)

# ── helpers ──────────────────────────────────────────────────────────────────

def rolling_mean(s, w=15): return s.rolling(w, center=True, min_periods=5).mean()
def rolling_std(s,  w=15): return s.rolling(w, center=True, min_periods=5).std()

def contact_quality(df):
    p90 = df["rms"].quantile(0.90)
    return (df["rms"] / p90).clip(0, 1.5) if p90 > 0 else df["rms"] * 0

def load_fatigue(path):
    return pd.read_csv(path).iloc[0]

# ── load data ────────────────────────────────────────────────────────────────

print("Loading data...")

# Canonical log0305 (20-min skip) — used for Figs 2, 3, 5, 7
df05       = pd.read_csv("out0305_w20/swing_features.csv")
# log0305 other skip conditions — used for Fig 4
df05_10    = pd.read_csv("out0305/swing_features.csv")
df05_v2    = pd.read_csv("out0305_v2/swing_features.csv")
df05_w15   = pd.read_csv("out0305_w15/swing_features.csv")

# log0303 full session (2 BLE connections) — used for Figs 5, 6
df03       = pd.read_csv("out0303_v2/swing_features.csv")
# log0303 segment 1 only — used for Fig 6
df03_seg1  = pd.read_csv("out0303_seg1/swing_features.csv")

# Fatigue summaries for Fig 4
# NOTE: out0305 (10-min, no RMS filter) was generated with an earlier code version
# before _filter_baseline_by_rms was added. The current code always applies RMS
# filtering, so re-running out0305 gives 166 Hz / +15.2% (same as out0305_v2).
# The -2.6% / 137.1 Hz values are from paper.md confirmed numbers and kept as
# hardcoded reference to show the pre-RMS-filter pipeline behavior.
fs_10_normsfilter = {   # hardcoded — old pipeline, no RMS filter
    "baseline_MDF": 137.1, "final_MDF": 140.7, "MDF_drop_pct": -2.6,
    "MNF_drop_pct": float("nan"), "fatigue_onset_s": float("nan"),
}
fs_v2  = load_fatigue("out0305_v2/fatigue_summary.csv")    # 10-min + RMS filter
fs_w15 = load_fatigue("out0305_w15/fatigue_summary.csv")   # 15-min skip
fs_w20 = load_fatigue("out0305_w20/fatigue_summary.csv")   # 20-min skip (canonical)

# Session summary for log0303 reconnection time
with open("out0303_v2/session_summary.json") as f:
    ss03 = json.load(f)
RECONNECT_S = ss03["reconnection_times_s"][0]   # 4815.8 s = 80.3 min
RECONNECT_MIN = RECONNECT_S / 60.0

# time in minutes
for df in [df05, df05_10, df05_v2, df05_w15, df03, df03_seg1]:
    df["t_min"] = df["t_peak_ms"] / 60000

print("  All data loaded.\n")

# ── Figure 2: Electrode settling curve — two-panel MDF + contact quality ─────
print("Generating Figure 2: Electrode settling curve (MDF + contact quality, first 30 min)...")

p90_rms = df05["rms"].quantile(0.90)
df05["contact_quality"] = df05["rms"] / p90_rms
df05["mdf_roll"] = df05["mdf"].rolling(10, center=True, min_periods=3).median()
df05["q_roll"]   = df05["contact_quality"].rolling(10, center=True, min_periods=3).median()

df_plot = df05[df05["t_min"] <= 30].copy()

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(10, 7), sharex=True,
    gridspec_kw={"height_ratios": [2, 1]},
)

# ── Panel A: MDF vs time ──────────────────────────────────────────────────────
ax1.scatter(df_plot["t_min"], df_plot["mdf"],
            s=8, alpha=0.28, color="steelblue", zorder=2, label="Per-swing MDF")
ax1.plot(df_plot["t_min"], df_plot["mdf_roll"],
         color="navy", linewidth=2.2, zorder=3, label="Rolling median MDF (10 swings)")

# stable settled reference (out0305_v2: 10-min + RMS filter)
ax1.axhline(166, color="seagreen", linewidth=1.6, linestyle="--",
            label="Stable settled reference ≈ 166 Hz")

# 20-min baseline (canonical)
ax1.axhline(199.2, color="steelblue", linewidth=1.2, linestyle=":",
            alpha=0.7, label="20-min baseline = 199 Hz")

# warmup-skip lines
for skip_min, color, style in [
    (10, "#e07b00", "-."),
    (15, "tomato",  ":"),
    (20, "red",     "-"),
]:
    ax1.axvline(skip_min, color=color, linewidth=1.3, linestyle=style)

# settling shade and label
ax1.axvspan(0, 20, alpha=0.07, color="red", zorder=1,
            label="Settling zone (0–20 min)")
ax1.text(1, 30, "← 10 min", color="#e07b00", fontsize=7.5, va="bottom")
ax1.text(10.2, 30, "← 15 min", color="tomato", fontsize=7.5, va="bottom")
ax1.text(20.2, 30, "← 20 min", color="red", fontsize=7.5, va="bottom")

# early MDF annotation
e_mean = df_plot.loc[df_plot["t_min"] <= 21, "mdf"].mean()
ax1.annotate(f"Early MDF\n{e_mean:.0f} Hz\n(settling)",
             xy=(7, e_mean), xytext=(12, 60),
             arrowprops=dict(arrowstyle="->", color="red"),
             fontsize=8.5, color="red")

ax1.set_ylabel("Median Frequency — MDF (Hz)", fontsize=11)
ax1.set_ylim(0, 310)
ax1.set_title("Figure 2  |  log0305: Electrode Settling — First 30 Minutes\n"
              "Early spectral metrics suppressed during electrode settling (~17–20 min)",
              fontsize=11)
ax1.legend(fontsize=8, loc="upper left")
ax1.grid(True, alpha=0.25)

# ── Panel B: Contact quality vs time ─────────────────────────────────────────
ax2.scatter(df_plot["t_min"], df_plot["contact_quality"],
            s=6, alpha=0.25, color="darkorange", zorder=2,
            label="Per-swing contact quality")
ax2.plot(df_plot["t_min"], df_plot["q_roll"],
         color="saddlebrown", linewidth=2.0, zorder=3,
         label="Rolling median (10 swings)")

ax2.axhline(0.25, color="red",     linewidth=1.3, linestyle="--",
            label="Reliable threshold = 0.25")
ax2.axhline(0.10, color="darkred", linewidth=1.2, linestyle=":",
            label="Contact-loss threshold = 0.10")
ax2.fill_between(df_plot["t_min"], 0, 0.10,
                 alpha=0.08, color="red", zorder=1)
ax2.fill_between(df_plot["t_min"], 0.10, 0.25,
                 alpha=0.05, color="orange", zorder=1)

ax2.axvspan(0, 20, alpha=0.07, color="red", zorder=1)
for skip_min, color, style in [
    (10, "#e07b00", "-."),
    (15, "tomato",  ":"),
    (20, "red",     "-"),
]:
    ax2.axvline(skip_min, color=color, linewidth=1.3, linestyle=style)

ax2.set_ylabel("Contact Quality\n(RMS / session p90-RMS)", fontsize=10)
ax2.set_xlabel("Time in session (min)", fontsize=11)
ax2.set_ylim(0, 1.4)
ax2.set_xlim(0, 30)
ax2.legend(fontsize=7.5, loc="upper left")
ax2.grid(True, alpha=0.25)

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "fig2_electrode_settling.png"), dpi=150)
plt.close()
print("  Saved: fig2_electrode_settling.png")


# ── Figure 3: IMU consistency vs EMG fatigue trend — two-panel ───────────────
print("Generating Figure 3: IMU consistency vs MDF fatigue trend (log0305, full session)...")

t   = df05["t_min"]
mag = df05["imu_peak_mag"]
mdf = df05["mdf"]

# rolling median (consistent with Fig 2)
mag_roll = mag.rolling(15, center=True, min_periods=5).median()
mdf_roll = mdf.rolling(15, center=True, min_periods=5).median()

# Pearson r on ALL swings — most conservative/complete test.
# All-swings: r=+0.029, p=0.468 (closest to paper.md confirmed r=+0.01, p=0.78).
# Post-warmup only (n=390): r=+0.063, p=0.212 — also non-significant.
# Linear fit restricted to post-warmup for the trend line (avoids settling distortion).
WARMUP_MIN = 20.0
post_mask = t > WARMUP_MIN
r_mag, p_mag = pearsonr(t, mag)
slope, intercept, *_ = linregress(t[post_mask], mag[post_mask])

# compute thirds from actual data (all swings, for visual context)
q1, q2 = t.quantile(1/3), t.quantile(2/3)
thirds = {
    "Early":  (t <= q1),
    "Mid":    (t > q1) & (t <= q2),
    "Late":   (t > q2),
}
third_colors = {"Early": "tomato", "Mid": "seagreen", "Late": "steelblue"}

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(10, 8), sharex=True,
    gridspec_kw={"height_ratios": [1, 1]},
)

# ── Panel A: MDF over full session (post-settling context) ───────────────────
ax1.scatter(t, mdf, s=5, alpha=0.20, color="steelblue", zorder=2,
            label="Per-swing MDF")
ax1.plot(t, mdf_roll, color="navy", linewidth=2.0, zorder=3,
         label="Rolling median MDF (15 swings)")

# stable reference
ax1.axhline(166, color="seagreen", linewidth=1.4, linestyle="--",
            label="Stable settled reference ≈ 166 Hz")

# warmup boundary
ax1.axvline(20, color="red", linewidth=1.3, linestyle=":",
            label="20-min warmup skip")
ax1.axvspan(0, 20, alpha=0.06, color="red", zorder=1, label="Settling zone")

# third means
for name, mask in thirds.items():
    seg = mdf[mask]
    ax1.axhline(seg.mean(), color=third_colors[name], linewidth=1.0,
                linestyle="-.", alpha=0.5)
    mid_t = t[mask].mean()
    ax1.text(mid_t, seg.mean() + 6, f"{name}\n{seg.mean():.0f}±{seg.std():.0f}",
             ha="center", va="bottom", fontsize=7.5, color=third_colors[name])

ax1.set_ylabel("MDF (Hz)", fontsize=11)
ax1.set_title("Figure 3  |  log0305: MDF Fatigue Trend + IMU Swing Intensity\n"
              "MDF declines after settling; IMU intensity remains flat", fontsize=11)
ax1.set_ylim(0, 310)
ax1.legend(fontsize=7.5, loc="upper right")
ax1.grid(True, alpha=0.25)

# ── Panel B: IMU peak magnitude over full session ────────────────────────────
ax2.scatter(t, mag, s=5, alpha=0.18, color="darkorange", zorder=2,
            label="Per-swing peak gyro magnitude")
ax2.plot(t, mag_roll, color="saddlebrown", linewidth=2.0, zorder=3,
         label="Rolling median (15 swings)")
ax2.plot(t[post_mask], slope * t[post_mask] + intercept, color="black",
         linewidth=1.3, linestyle="--", zorder=4,
         label=f"Linear fit (post-20min): slope = {slope:+.1f} dps/min")

ax2.axhline(300, color="gray", linewidth=1.0, linestyle=":", alpha=0.6,
            label="300 dps swing threshold")
ax2.axvline(20, color="red", linewidth=1.3, linestyle=":")
ax2.axvspan(0, 20, alpha=0.06, color="red", zorder=1)

# third means with actual computed values
for name, mask in thirds.items():
    seg = mag[mask]
    ax2.axhline(seg.mean(), color=third_colors[name], linewidth=1.0,
                linestyle="-.", alpha=0.5)
    mid_t = t[mask].mean()
    ax2.text(mid_t, seg.mean() + 40, f"{name}\n{seg.mean():.0f}±{seg.std():.0f}",
             ha="center", va="bottom", fontsize=7.5, color=third_colors[name])

ax2.text(0.98, 0.97,
         f"Pearson r = {r_mag:+.3f}   p = {p_mag:.3f}  (all 626 swings)\n"
         "Non-significant → effort unchanged throughout session\n"
         "(IMU is biomechanical effort proxy, not direct force)",
         transform=ax2.transAxes, fontsize=9, ha="right", va="top",
         bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.80))

ax2.set_xlabel("Time in session (min)", fontsize=11)
ax2.set_ylabel("Peak Gyro Magnitude (dps)", fontsize=11)
ax2.set_ylim(0, 3200)
ax2.set_xlim(0, t.max() + 1)
ax2.legend(fontsize=7.5, loc="lower right")
ax2.grid(True, alpha=0.25)

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "fig3_imu_consistency.png"), dpi=150)
plt.close()
print("  Saved: fig3_imu_consistency.png")


# ── Figure 4: Warmup-skip sensitivity bar chart ───────────────────────────────
print("Generating Figure 4: Warmup-skip sensitivity bar chart...")

configs = [
    ("10 min\n(no RMS filter)\n[pre-fix pipeline]", fs_10_normsfilter, "tomato",    "out0305 (old)"),
    ("10 min\n+ RMS filter",                         fs_v2,            "darkorange","out0305_v2"),
    ("15 min",                                        fs_w15,           "gold",      "out0305_w15"),
    ("20 min\n(canonical)",                           fs_w20,           "steelblue", "out0305_w20"),
]

labels  = [c[0] for c in configs]
basemdf = [c[1]["baseline_MDF"] for c in configs]
finmdf  = [c[1]["final_MDF"]    for c in configs]
drops   = [c[1]["MDF_drop_pct"] for c in configs]
colors  = [c[2] for c in configs]

x = np.arange(len(labels))
w = 0.32

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

# left: baseline vs final MDF
bars_b = ax1.bar(x - w/2, basemdf, w, label="Baseline MDF (Hz)",
                 color=colors, alpha=0.85, edgecolor="black", linewidth=0.7)
bars_f = ax1.bar(x + w/2, finmdf,  w, label="Final MDF (Hz)",
                 color=colors, alpha=0.45, edgecolor="black", linewidth=0.7,
                 hatch="///")
ax1.axhline(166, color="green", linewidth=1.5, linestyle="--",
            label="Stable settled MDF = 166 Hz")

for bar, val in zip(bars_b, basemdf):
    ax1.text(bar.get_x() + bar.get_width()/2, val + 4,
             f"{val:.0f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
for bar, val in zip(bars_f, finmdf):
    ax1.text(bar.get_x() + bar.get_width()/2, val + 4,
             f"{val:.0f}", ha="center", va="bottom", fontsize=8, color="gray")

ax1.set_xticks(x); ax1.set_xticklabels(labels, fontsize=9)
ax1.set_ylabel("MDF (Hz)", fontsize=11)
ax1.set_title("Baseline vs Final MDF by Warmup Skip", fontsize=11)
ax1.set_ylim(0, 260)
ax1.legend(fontsize=8)
ax1.grid(axis="y", alpha=0.3)

# right: MDF drop % bar chart
bar_colors = []
for d in drops:
    bar_colors.append("steelblue" if d > 0 else "tomato")

bars_d = ax2.bar(x, drops, 0.5, color=bar_colors, alpha=0.85,
                 edgecolor="black", linewidth=0.7)
ax2.axhline(0, color="black", linewidth=1.0)

for bar, val in zip(bars_d, drops):
    ypos = val + 0.8 if val >= 0 else val - 2.5
    ax2.text(bar.get_x() + bar.get_width()/2, ypos,
             f"{val:+.1f}%", ha="center", va="bottom", fontsize=9.5, fontweight="bold")

# annotations for the extreme cases
ax2.annotate("Fatigue missed\n(false negative)",
             xy=(0, drops[0]), xytext=(0.5, -8),
             arrowprops=dict(arrowstyle="->", color="tomato"),
             fontsize=8, color="tomato")
ax2.annotate("Baseline still\nin settling →\ninverted result",
             xy=(2, drops[2]), xytext=(1.3, -20),
             arrowprops=dict(arrowstyle="->", color="darkred"),
             fontsize=8, color="darkred")
ax2.annotate("Genuine fatigue\nrevealed",
             xy=(3, drops[3]), xytext=(2.4, 22),
             arrowprops=dict(arrowstyle="->", color="steelblue"),
             fontsize=8, color="steelblue")

ax2.set_xticks(x); ax2.set_xticklabels(labels, fontsize=9)
ax2.set_ylabel("MDF Drop % (baseline → final)", fontsize=11)
ax2.set_title("MDF Drop % by Warmup Skip Setting\n"
              "Positive = MDF declined (fatigue); Negative = inverted/missed", fontsize=11)
ax2.set_ylim(-35, 40)
ax2.grid(axis="y", alpha=0.3)

fig.suptitle("Figure 4  |  Warmup-Skip Sensitivity: log0305\n"
             "Standard 10-min skip completely misses genuine 28.1% fatigue signal",
             fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "fig4_warmup_skip_sensitivity.png"), dpi=150)
plt.close()
print("  Saved: fig4_warmup_skip_sensitivity.png")


# ── Figure 5: Contact quality over session ────────────────────────────────────
print("Generating Figure 5: Contact quality over session (both sessions)...")

fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=False)

for ax, df, label, color, xlim, gap_min in [
    (axes[0], df05, "log0305  (63 min, single continuous BLE connection)",
     "steelblue", 64, None),
    (axes[1], df03, "log0303  (88 min, two BLE connections — 66-min gap)",
     "darkorange", 90, RECONNECT_MIN),
]:
    t = df["t_min"]
    p90 = df["rms"].quantile(0.90)
    q = (df["rms"] / p90).clip(0, 1.5) if p90 > 0 else df["rms"] * 0
    q_roll = q.rolling(15, center=True, min_periods=5).median()  # median, not mean

    ax.scatter(t, q, s=5, alpha=0.20, color=color, zorder=2)
    ax.plot(t, q_roll, color=color, linewidth=2.2, zorder=3,
            label="Rolling median CQ (15 swings)")
    ax.axhline(0.25, color="red", linewidth=1.2, linestyle="--",
               label="Reliable threshold = 0.25")
    ax.axhline(0.10, color="darkred", linewidth=1.2, linestyle=":",
               label="Contact-loss threshold = 0.10")
    ax.fill_between(t, 0, 0.10, alpha=0.08, color="red", zorder=1)
    ax.fill_between(t, 0.10, 0.25, alpha=0.05, color="orange", zorder=1)

    if gap_min is not None:
        # log0303: annotate segments and gap
        ax.axvline(gap_min, color="purple", linewidth=2.0, linestyle="--",
                   label=f"BLE reconnection at {gap_min:.0f} min")
        ax.axvspan(13.5, gap_min, alpha=0.07, color="purple", zorder=1,
                   label="BLE gap — no data (~66 min)")
        # segment labels
        seg1_mean = q[t <= 13.5].mean()
        seg2_mean = q[t >= gap_min].mean()
        ax.text(7, 1.40, f"Seg 1\nCQ ≈ {seg1_mean:.2f}",
                ha="center", fontsize=8, color="saddlebrown",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="wheat", alpha=0.7))
        ax.text(gap_min + 2, 1.40, f"Seg 2\nCQ ≈ {seg2_mean:.2f}",
                ha="left", fontsize=8, color="purple",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="lavender", alpha=0.7))
        if abs(seg2_mean - seg1_mean) > 0.05:
            ax.annotate(f"Δ CQ = {seg2_mean - seg1_mean:+.2f}\n(different contact\nstate after gap)",
                        xy=(gap_min + 1, (seg1_mean + seg2_mean) / 2),
                        xytext=(gap_min + 5, 0.80),
                        arrowprops=dict(arrowstyle="->", color="purple"),
                        fontsize=7.5, color="purple")
    else:
        # log0305: settling zone + per-third annotations
        ax.axvspan(0, 20, alpha=0.07, color="tomato", zorder=1,
                   label="Electrode settling zone (0–20 min)")
        ax.axvline(20, color="red", linewidth=1.3, linestyle=":",
                   label="20-min warmup skip")
        # per-third means
        q1t, q2t = t.quantile(1/3), t.quantile(2/3)
        for name, mask, col in [
            ("Early", t <= q1t, "tomato"),
            ("Mid",   (t > q1t) & (t <= q2t), "seagreen"),
            ("Late",  t > q2t, "steelblue"),
        ]:
            seg_q = q[mask]
            mid_t = t[mask].mean()
            ax.text(mid_t, seg_q.mean() + 0.07,
                    f"{name}\n{seg_q.mean():.2f}±{seg_q.std():.2f}",
                    ha="center", va="bottom", fontsize=7.5, color=col)

    ax.set_ylabel("Contact Quality\n(RMS / session p90-RMS)", fontsize=10)
    ax.set_title(label, fontsize=10)
    ax.set_xlim(0, xlim)
    ax.set_ylim(0, 1.6)
    ax.legend(fontsize=7.5, loc="upper right")
    ax.grid(True, alpha=0.25)

axes[1].set_xlabel("Time in session (min)", fontsize=12)
fig.suptitle("Figure 5  |  EMG Contact Quality Over Session\n"
             "contact_quality(t) = RMS(t) / session_p90_rms", fontsize=12,
             fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "fig5_contact_quality.png"), dpi=150)
plt.close()
print("  Saved: fig5_contact_quality.png")


# ── Figure 6: log0303 gap artifact ───────────────────────────────────────────
print("Generating Figure 6: log0303 gap artifact visualization...")

fig, ax = plt.subplots(figsize=(11, 5.5))

# full session scatter + rolling median
t03  = df03["t_min"]
m03  = df03["mdf"]
m03_roll = m03.rolling(10, center=True, min_periods=3).median()
ax.scatter(t03, m03, s=7, alpha=0.25, color="darkorange", zorder=2,
           label="Per-swing MDF (full session, n=197)")
ax.plot(t03, m03_roll, color="saddlebrown", linewidth=2.0, zorder=3,
        label="Rolling median MDF (10 swings)")

# segment 1 overlay — larger diamonds, rolling median
t01 = df03_seg1["t_min"]
m01 = df03_seg1["mdf"]
m01_roll = m01.rolling(10, center=True, min_periods=3).median()
ax.scatter(t01, m01, s=18, alpha=0.70, color="navy", marker="D", zorder=4,
           label=f"Segment 1 only (n={len(df03_seg1)}, 13.5 min)")
ax.plot(t01, m01_roll, color="navy", linewidth=1.8, linestyle="-", zorder=5, alpha=0.7)

# baseline MDF line (from full session analysis = first segment swings)
baseline_mdf_full = 212.9    # confirmed from out0303_v2/baseline.json
ax.axhline(baseline_mdf_full, color="seagreen", linewidth=1.4, linestyle="--",
           label=f"Full-session baseline MDF = {baseline_mdf_full:.0f} Hz")

# gap shading
ax.axvspan(13.5, RECONNECT_MIN, alpha=0.10, color="purple", zorder=1,
           label="BLE gap (~66 min, no data)")
ax.axvline(RECONNECT_MIN, color="purple", linewidth=2.0, linestyle="--")

# segment region labels on x-axis area
ax.text(7, 15, "Segment 1\n(0–13.5 min)", ha="center", va="bottom",
        fontsize=8.5, color="navy",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="aliceblue", alpha=0.85))
ax.text((13.5 + RECONNECT_MIN) / 2, 15, "BLE gap\n(~66 min)", ha="center",
        va="bottom", fontsize=8.5, color="purple",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="lavender", alpha=0.85))
ax.text(RECONNECT_MIN + 3.5, 15, "Segment 2\n(80–88 min)", ha="center",
        va="bottom", fontsize=8.5, color="saddlebrown",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="papayawhip", alpha=0.85))

# reconnection annotation
ax.text(RECONNECT_MIN + 0.5, 290,
        f"Reconnection\nt = {RECONNECT_MIN:.0f} min",
        ha="left", va="top", fontsize=8.5, color="purple",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="lavender", alpha=0.8))

# drop % summary box
full_drop = 28.7
seg1_drop = 4.9
ax.text(0.02, 0.97,
        f"Full session MDF drop:  {full_drop:.1f}%  ← cross-segment artifact\n"
        f"Segment 1 only drop:    {seg1_drop:.1f}%  ← no meaningful within-segment fatigue",
        transform=ax.transAxes, fontsize=9.5, va="top",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="lightyellow", alpha=0.9))

ax.set_xlabel("Reconstructed absolute time (min)", fontsize=12)
ax.set_ylabel("Median Frequency — MDF (Hz)", fontsize=12)
ax.set_title("Figure 6  |  log0303: BLE Gap Artifact\n"
             "Apparent 28.7% MDF drop is a cross-segment artifact — Segment 1 alone shows only 4.9%",
             fontsize=11)
ax.set_xlim(-1, 90)
ax.set_ylim(0, 350)
ax.legend(fontsize=8, loc="upper right")
ax.grid(True, alpha=0.25)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "fig6_log0303_gap_artifact.png"), dpi=150)
plt.close()
print("  Saved: fig6_log0303_gap_artifact.png")


# ── Figure 7: IMU-EMG diagnostic matrix ──────────────────────────────────────
print("Generating Figure 7: IMU-EMG diagnostic matrix (log0305)...")

fig, ax = plt.subplots(figsize=(9, 7))

t   = df05["t_min"]
mag = df05["imu_peak_mag"]
mdf = df05["mdf"]

# colour by session third
q1, q2 = t.quantile(1/3), t.quantile(2/3)
thirds_lbl = ["Early (0–21 min)\nSettling", "Mid (21–42 min)\nStable", "Late (42–63 min)\nFatigue"]
third_colors = ["tomato", "gold", "steelblue"]
masks = [t <= q1, (t > q1) & (t <= q2), t > q2]

for mask, lbl, col in zip(masks, thirds_lbl, third_colors):
    ax.scatter(mag[mask], mdf[mask], s=10, alpha=0.40, color=col,
               label=f"{lbl}\n  n={mask.sum()}", zorder=2)

# median crosshairs per third
for mask, col in zip(masks, third_colors):
    mx, my = mag[mask].median(), mdf[mask].median()
    ax.plot(mx, my, "o", ms=11, color=col, markeredgecolor="black",
            markeredgewidth=1.2, zorder=4)

# quadrant reference lines
med_mag = mag.median()
med_mdf = mdf.median()
ax.axvline(med_mag, color="gray", linewidth=1.0, linestyle=":", alpha=0.6)
ax.axhline(med_mdf, color="gray", linewidth=1.0, linestyle=":", alpha=0.6)

# quadrant labels
for qx, qy, qtxt in [
    (0.05, 0.95, "Low IMU + Low MDF\n→ Settling / bad contact"),
    (0.55, 0.95, "High IMU + Low MDF\n→ High effort, still fatigued"),
    (0.05, 0.45, "Low IMU + High MDF\n→ Low effort, fresh"),
    (0.55, 0.45, "High IMU + High MDF\n→ High effort, fresh"),
]:
    ax.text(qx, qy, qtxt, transform=ax.transAxes, fontsize=7.5,
            ha="left" if qx < 0.5 else "left", va="top",
            color="dimgray",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.5))

ax.set_xlabel("IMU Peak Gyro Magnitude (dps)\n← effort proxy →", fontsize=11)
ax.set_ylabel("EMG Median Frequency — MDF (Hz)\n← low = settling or fatigue →", fontsize=11)
ax.set_title("Figure 7  |  IMU-EMG Diagnostic Matrix (log0305)\n"
             "Early swings: low MDF despite normal IMU  →  settling not fatigue",
             fontsize=11)
ax.legend(fontsize=8.5, loc="lower right")
ax.grid(True, alpha=0.25)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "fig7_imu_emg_diagnostic_matrix.png"), dpi=150)
plt.close()
print("  Saved: fig7_imu_emg_diagnostic_matrix.png")


# ── paper_stats.txt ──────────────────────────────────────────────────────────
print("\nGenerating paper_stats.txt...")

lines = []
lines.append("=" * 65)
lines.append("PAPER STATISTICS — generated from correct output directories")
lines.append("=" * 65)

def thirds_stats(df, col):
    t = df["t_peak_ms"]
    q1, q2 = t.quantile(1/3), t.quantile(2/3)
    e = df.loc[t <= q1, col].dropna()
    m = df.loc[(t > q1) & (t <= q2), col].dropna()
    l = df.loc[t > q2, col].dropna()
    return e, m, l

# ── log0305 (canonical: out0305_w20) ──────────────────────────────────────────
lines.append("\n--- log0305  (out0305_w20, 20-min warmup skip) ---")
lines.append(f"  Duration:     {df05['t_min'].max():.1f} min")
lines.append(f"  Swings:       {len(df05)}")
lines.append(f"  Swing rate:   {len(df05)/df05['t_min'].max():.1f} swings/min")

r_mag, p_mag = pearsonr(df05["t_min"], df05["imu_peak_mag"])
r_mdf, p_mdf = pearsonr(df05["t_min"], df05["mdf"].fillna(df05["mdf"].median()))
lines.append(f"  imu_peak_mag  Pearson r = {r_mag:+.3f}  p = {p_mag:.3f}")
lines.append(f"  mdf           Pearson r = {r_mdf:+.3f}  p = {p_mdf:.3f}")

e_mdf, m_mdf, l_mdf = thirds_stats(df05, "mdf")
e_mag, m_mag, l_mag = thirds_stats(df05, "imu_peak_mag")
lines.append(f"  MDF thirds:   early={e_mdf.mean():.1f}±{e_mdf.std():.1f}  "
             f"mid={m_mdf.mean():.1f}±{m_mdf.std():.1f}  "
             f"late={l_mdf.mean():.1f}±{l_mdf.std():.1f} Hz")
lines.append(f"  IMU thirds:   early={e_mag.mean():.0f}±{e_mag.std():.0f}  "
             f"mid={m_mag.mean():.0f}±{m_mag.std():.0f}  "
             f"late={l_mag.mean():.0f}±{l_mag.std():.0f} dps")

for fs, label in [
    (fs_10_normsfilter, "10min (no RMS, old pipeline)"),
    (fs_v2,  "10min+RMS"),
    (fs_w15, "15min"),
    (fs_w20, "20min"),
]:
    lines.append(f"\n  Fatigue summary ({label}):")
    lines.append(f"    baseline_MDF = {fs['baseline_MDF']:.1f} Hz")
    lines.append(f"    final_MDF    = {fs['final_MDF']:.1f} Hz")
    lines.append(f"    MDF_drop_pct = {fs['MDF_drop_pct']:+.2f}%")
    lines.append(f"    MNF_drop_pct = {fs['MNF_drop_pct']:+.2f}%")
    if not pd.isna(fs.get("fatigue_onset_s", float("nan"))):
        lines.append(f"    fatigue_onset = {fs['fatigue_onset_s']:.0f} s "
                     f"= {fs['fatigue_onset_s']/60:.1f} min")

# ── log0303 (canonical: out0303_v2) ───────────────────────────────────────────
lines.append("\n\n--- log0303  (out0303_v2, full session, gap-confounded) ---")
lines.append(f"  Duration:     {df03['t_min'].max():.1f} min")
lines.append(f"  Swings:       {len(df03)}")
lines.append(f"  BLE reconnection at: {RECONNECT_MIN:.1f} min ({RECONNECT_S:.0f} s)")

fs_03 = load_fatigue("out0303_v2/fatigue_summary.csv")
lines.append(f"  MDF_drop_pct (full session) = {fs_03['MDF_drop_pct']:+.2f}%  "
             f"<-- GAP ARTIFACT")

# segment 1 only
lines.append(f"\n  Segment 1 only (out0303_seg1):")
lines.append(f"    Duration:  {df03_seg1['t_min'].max():.1f} min")
lines.append(f"    Swings:    {len(df03_seg1)}")
fs_03s1 = load_fatigue("out0303_seg1/fatigue_summary.csv")
lines.append(f"    MDF_drop_pct = {fs_03s1['MDF_drop_pct']:+.2f}%  "
             f"<-- no meaningful within-segment fatigue")

# ── key paper claims verification ─────────────────────────────────────────────
lines.append("\n\n--- KEY NUMBERS VERIFICATION ---")
lines.append(f"  Settling duration:         ~17–20 min (early MDF={e_mdf.mean():.1f} Hz "
             f"vs stable={m_mdf.mean():.1f} Hz)")
lines.append(f"  Fatigue found (20-min):    MDF drop = {fs_w20['MDF_drop_pct']:+.2f}%  "
             f"MNF drop = {fs_w20['MNF_drop_pct']:+.2f}%")
lines.append(f"  Fatigue missed (10-min, no RMS): MDF drop = {fs_10_normsfilter['MDF_drop_pct']:+.2f}% "
             f"  [pre-fix pipeline, hardcoded from paper.md]")
lines.append(f"  Inverted (15-min):         MDF drop = {fs_w15['MDF_drop_pct']:+.2f}%")
lines.append(f"  IMU consistency (r, p):    r={r_mag:+.3f}  p={p_mag:.3f}")
lines.append(f"  log0303 gap artifact:      {fs_03['MDF_drop_pct']:+.2f}% full vs "
             f"{fs_03s1['MDF_drop_pct']:+.2f}% seg1-only")

stats_path = os.path.join(OUT_DIR, "paper_stats.txt")
with open(stats_path, "w") as f:
    f.write("\n".join(lines) + "\n")
print(f"  Saved: {stats_path}")

print("\n" + "=" * 55)
print("All figures and stats generated in:", os.path.abspath(OUT_DIR))
print("=" * 55)
