"""
paper_figures.py  —  Generate key figures for the paper.

Run from C:\wangx\ftc\emg_util:
    python paper_figures.py

Outputs saved to: C:\wangx\ftc\emg_util\paper_figures\
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import pearsonr

OUT_DIR = "paper_figures"
os.makedirs(OUT_DIR, exist_ok=True)

# ── load data ────────────────────────────────────────────────────────────────

df03 = pd.read_csv("out0303/swing_features.csv")
df05 = pd.read_csv("out0305/swing_features.csv")

# time in minutes
df03["t_min"] = df03["t_peak_ms"] / 60000
df05["t_min"] = df05["t_peak_ms"] / 60000

# rolling window helper (by swing count, not time)
def rolling_mean(series, window=15):
    return series.rolling(window=window, center=True, min_periods=5).mean()

def rolling_std(series, window=15):
    return series.rolling(window=window, center=True, min_periods=5).std()


# ── Figure 1: Electrode settling  (log0305 MDF vs time) ──────────────────────
print("Generating Figure 1: Electrode settling (log0305 MDF vs time)...")

fig, ax = plt.subplots(figsize=(10, 5))

t = df05["t_min"]
mdf = df05["mdf"]
mdf_roll = rolling_mean(mdf)
mdf_std  = rolling_std(mdf)

ax.scatter(t, mdf, s=6, alpha=0.25, color="steelblue", label="Per-swing MDF")
ax.plot(t, mdf_roll, color="navy", linewidth=2, label="Rolling mean (±15 swings)")
ax.fill_between(t, mdf_roll - mdf_std, mdf_roll + mdf_std,
                alpha=0.15, color="navy")

# baseline reference line (from baseline.json)
baseline_mdf = 166.0
ax.axhline(baseline_mdf, color="green", linewidth=1.5,
           linestyle="--", label=f"Stable baseline MDF = {baseline_mdf:.0f} Hz")

# shade settling zone
settling_end_min = 17.5
ax.axvspan(0, settling_end_min, alpha=0.08, color="red",
           label=f"Electrode settling (0–{settling_end_min:.0f} min)")
ax.axvline(settling_end_min, color="red", linewidth=1.2, linestyle=":")

# annotation
ax.annotate("Early session:\nlow MDF = electrode\ncontact artifact",
            xy=(8, 108), xytext=(12, 75),
            arrowprops=dict(arrowstyle="->", color="red"),
            fontsize=9, color="red")
ax.annotate("Stable signal\n(post-settling)",
            xy=(40, 163), xytext=(38, 200),
            arrowprops=dict(arrowstyle="->", color="green"),
            fontsize=9, color="green")

ax.set_xlabel("Time in session (min)", fontsize=12)
ax.set_ylabel("Median Frequency – MDF (Hz)", fontsize=12)
ax.set_title("log0305: EMG Median Frequency Over Session\n"
             "Electrode settling period suppresses MDF for ~17 min", fontsize=12)
ax.set_ylim(0, 350)
ax.set_xlim(0, df05["t_min"].max() + 1)
ax.legend(fontsize=9, loc="upper left")
ax.grid(True, alpha=0.3)

plt.tight_layout()
path1 = os.path.join(OUT_DIR, "fig1_electrode_settling_log0305.png")
plt.savefig(path1, dpi=150)
plt.close()
print(f"  Saved: {path1}")


# ── Figure 2: IMU cross-validation  (log0305 imu_peak_mag vs time) ───────────
print("Generating Figure 2: IMU cross-validation (log0305 imu_peak_mag vs time)...")

fig, ax = plt.subplots(figsize=(10, 5))

t = df05["t_min"]
mag = df05["imu_peak_mag"]
mag_roll = rolling_mean(mag, window=20)

ax.scatter(t, mag, s=6, alpha=0.2, color="darkorange", label="Per-swing peak gyro")
ax.plot(t, mag_roll, color="saddlebrown", linewidth=2,
        label="Rolling mean (±20 swings)")

# linear regression
m, b = np.polyfit(t, mag, 1)
ax.plot(t, m * t + b, color="black", linewidth=1.5, linestyle="--",
        label=f"Linear fit: slope = {m:+.1f} dps/min")

r, p = pearsonr(t, mag)
ax.text(0.98, 0.95, f"Pearson r = {r:+.3f}  (p = {p:.2f})",
        transform=ax.transAxes, fontsize=10, ha="right", va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.6))

ax.axhline(300, color="gray", linewidth=1, linestyle=":", alpha=0.6,
           label="300 dps swing detection threshold")

ax.set_xlabel("Time in session (min)", fontsize=12)
ax.set_ylabel("Peak Gyro Magnitude (dps)", fontsize=12)
ax.set_title("log0305: IMU Swing Intensity Over Session\n"
             "Flat trend confirms electrode settling ≠ biomechanical fatigue", fontsize=12)
ax.set_ylim(0, 3000)
ax.set_xlim(0, df05["t_min"].max() + 1)
ax.legend(fontsize=9, loc="lower right")
ax.grid(True, alpha=0.3)

plt.tight_layout()
path2 = os.path.join(OUT_DIR, "fig2_imu_crossval_log0305.png")
plt.savefig(path2, dpi=150)
plt.close()
print(f"  Saved: {path2}")


# ── Figure 3: Contact quality metric  (both sessions) ────────────────────────
print("Generating Figure 3: Contact quality metric (both sessions)...")

def contact_quality(df):
    rms = df["rms"]
    p90 = rms.quantile(0.90)
    return (rms / p90).clip(0, 1.5) if p90 > 0 else rms * 0

fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=False)

for ax, df, label, color, xlim in [
    (axes[0], df05, "log0305 (63 min, continuous)", "steelblue", 64),
    (axes[1], df03, "log0303 (88 min, with 66-min gap)", "darkorange", 90),
]:
    t = df["t_min"]
    q = contact_quality(df)
    q_roll = rolling_mean(q, window=15)

    ax.scatter(t, q, s=6, alpha=0.2, color=color)
    ax.plot(t, q_roll, color=color, linewidth=2, label="Rolling mean")
    ax.axhline(0.25, color="red", linewidth=1.2, linestyle="--",
               label="Threshold = 0.25 (reliable EMG)")
    ax.axhline(0.10, color="darkred", linewidth=1.2, linestyle=":",
               label="Threshold = 0.10 (contact loss)")
    ax.fill_between(t, 0, 0.10, alpha=0.08, color="red")
    ax.fill_between(t, 0.10, 0.25, alpha=0.05, color="orange")

    # shade settling zone for log0305 only
    if "0305" in label:
        ax.axvspan(0, 17.5, alpha=0.08, color="red",
                   label="Electrode settling zone")

    ax.set_ylabel("Contact Quality\n(RMS / session p90-RMS)", fontsize=10)
    ax.set_title(label, fontsize=11)
    ax.set_xlim(0, xlim)
    ax.set_ylim(0, 1.6)
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)

axes[1].set_xlabel("Time in session (min)", fontsize=12)
fig.suptitle("EMG Contact Quality Over Session\n"
             "contact_quality(t) = RMS(t) / session_p90_rms", fontsize=12)
plt.tight_layout()
path3 = os.path.join(OUT_DIR, "fig3_contact_quality_both.png")
plt.savefig(path3, dpi=150)
plt.close()
print(f"  Saved: {path3}")


# ── Figure 4: Session thirds comparison  (bar chart, both sessions) ───────────
print("Generating Figure 4: Session thirds comparison (bar chart)...")

def thirds(df, col):
    t = df["t_peak_ms"]
    q1, q2 = t.quantile(1/3), t.quantile(2/3)
    e = df.loc[t <= q1, col].dropna()
    m = df.loc[(t > q1) & (t <= q2), col].dropna()
    l = df.loc[t > q2, col].dropna()
    return (e.mean(), m.mean(), l.mean()), (e.std(), m.std(), l.std())

labels = ["Early\n(1st third)", "Mid\n(2nd third)", "Late\n(3rd third)"]
x = np.arange(len(labels))
width = 0.35

fig, axes = plt.subplots(1, 3, figsize=(14, 5))

metrics = [
    ("mdf",          "MDF (Hz)",                     "Median Frequency"),
    ("imu_peak_mag", "Peak Gyro Magnitude (dps)",     "IMU Swing Intensity"),
    ("rms",          "EMG RMS (a.u.)",                "EMG RMS"),
]

for ax, (col, ylabel, title) in zip(axes, metrics):
    means03, stds03 = thirds(df03, col)
    means05, stds05 = thirds(df05, col)

    bars03 = ax.bar(x - width/2, means03, width, yerr=stds03,
                    label="log0303", color="darkorange", alpha=0.8,
                    capsize=4, error_kw={"linewidth": 1.2})
    bars05 = ax.bar(x + width/2, means05, width, yerr=stds05,
                    label="log0305", color="steelblue", alpha=0.8,
                    capsize=4, error_kw={"linewidth": 1.2})

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)

    # annotate delta for log0305 MDF to highlight settling
    if col == "mdf":
        delta = means05[2] - means05[0]
        ax.annotate(f"Δ0305 = {delta:+.0f} Hz\n(settling artifact)",
                    xy=(x[2] + width/2, means05[2]),
                    xytext=(x[2] + width/2 + 0.1, means05[2] + 30),
                    arrowprops=dict(arrowstyle="->", color="navy"),
                    fontsize=8, color="navy")

fig.suptitle("Per-Session-Third Comparison: log0303 vs log0305\n"
             "(mean ± std, thirds split by t_peak_ms quantile)", fontsize=12)
plt.tight_layout()
path4 = os.path.join(OUT_DIR, "fig4_thirds_comparison.png")
plt.savefig(path4, dpi=150)
plt.close()
print(f"  Saved: {path4}")


# ── Figure 5: Combined overview  (log0305, two-panel: MDF + imu_peak_mag) ────
print("Generating Figure 5: Combined overview (log0305)...")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)

t = df05["t_min"]

# top: MDF
mdf = df05["mdf"]
ax1.scatter(t, mdf, s=5, alpha=0.2, color="steelblue")
ax1.plot(t, rolling_mean(mdf, 20), color="navy", linewidth=2, label="Rolling mean MDF")
ax1.axhline(166, color="green", linewidth=1.5, linestyle="--",
            label="Stable baseline MDF = 166 Hz")
ax1.axvspan(0, 17.5, alpha=0.08, color="red", label="Settling zone (~0–17 min)")
ax1.axvline(17.5, color="red", linewidth=1.2, linestyle=":")
ax1.set_ylabel("MDF (Hz)", fontsize=11)
ax1.set_ylim(0, 350)
ax1.legend(fontsize=9)
ax1.set_title("log0305 (63 min): EMG MDF and IMU Swing Intensity", fontsize=12)
ax1.grid(True, alpha=0.3)

# bottom: imu_peak_mag
mag = df05["imu_peak_mag"]
ax2.scatter(t, mag, s=5, alpha=0.2, color="darkorange")
ax2.plot(t, rolling_mean(mag, 20), color="saddlebrown", linewidth=2,
         label="Rolling mean gyro peak")
ax2.axhline(mag.mean(), color="gray", linewidth=1.5, linestyle="--",
            label=f"Session mean = {mag.mean():.0f} dps")
ax2.axvspan(0, 17.5, alpha=0.08, color="red")
ax2.axvline(17.5, color="red", linewidth=1.2, linestyle=":")
r, p = pearsonr(t, mag)
ax2.text(0.02, 0.95, f"r = {r:+.3f}  p = {p:.2f}  (flat = no biomechanical fatigue)",
         transform=ax2.transAxes, fontsize=9, va="top",
         bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.7))
ax2.set_ylabel("Peak Gyro Magnitude (dps)", fontsize=11)
ax2.set_xlabel("Time in session (min)", fontsize=11)
ax2.set_ylim(0, 3200)
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
path5 = os.path.join(OUT_DIR, "fig5_combined_log0305.png")
plt.savefig(path5, dpi=150)
plt.close()
print(f"  Saved: {path5}")


# ── Summary statistics printout ───────────────────────────────────────────────
print("\n" + "="*60)
print("SUMMARY STATISTICS FOR PAPER")
print("="*60)

for df, name in [(df05, "log0305"), (df03, "log0303")]:
    print(f"\n--- {name} ---")
    dur = df["t_min"].max()
    print(f"  Duration:   {dur:.1f} min")
    print(f"  Swings:     {len(df)}")
    print(f"  Swing rate: {len(df)/dur:.1f} swings/min")

    for col in ["mdf", "imu_peak_mag", "rms"]:
        r, p = pearsonr(df["t_min"], df[col].fillna(df[col].median()))
        print(f"  {col:20s}: mean={df[col].mean():.1f}  std={df[col].std():.1f}  "
              f"r={r:+.3f}  p={p:.3f}")

    # thirds
    t = df["t_peak_ms"]
    q1, q2 = t.quantile(1/3), t.quantile(2/3)
    for col in ["mdf", "imu_peak_mag"]:
        e = df.loc[t <= q1, col].mean()
        l = df.loc[t > q2, col].mean()
        delta_pct = (l - e) / e * 100 if e > 0 else float("nan")
        print(f"  {col:20s} thirds: early={e:.1f}  late={l:.1f}  "
              f"delta={delta_pct:+.1f}%")

print("\nAll figures saved to:", os.path.abspath(OUT_DIR))
