"""
exp10_high_dynamic_psd.py  —  Experiment 10: PSD around high-dynamic IMU events.

Gateway test for the impact-artifact hypothesis (Appendix E, paper.md).
Compares EMG spectral shape near the peak dynamic acceleration within each swing
window against a paired pre-event control window.

Primary metric:
    delta_log_hf_lf = log10(high_band/low_band)_near - log10(high_band/low_band)_ctrl
    high_band: 200-450 Hz,  low_band: 50-200 Hz

Gateway decision (see todo.md Experiment 10):
    PROCEED to Batch C  if  median delta > 0 AND Wilcoxon p < 0.05
                              AND post-20-min subset holds AND dose-response > 0
    DEPRIORITIZE Batch C otherwise

Run from /local/mnt/workspace/wangx/projects/emg_util/:
    /local/mnt/workspace/wangx/miniconda3/envs/fft-env/bin/python exp10_high_dynamic_psd.py

Outputs:
    paper_figures/fig8_high_dynamic_event_psd.png
    paper_figures/table_exp10_high_dynamic_event_psd.csv
"""

import os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import welch
from scipy.stats import wilcoxon, ttest_rel, spearmanr
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/local/mnt/workspace/wangx/projects/emg_util')
import capture_loader as loader
from fatigue_monitor import preprocess_emg

OUT_DIR = "paper_figures"
os.makedirs(OUT_DIR, exist_ok=True)

# ── constants ─────────────────────────────────────────────────────────────────

FS_EMG      = 2000.0      # Hz
FS_IMU      = 200.0       # Hz
WIN_MS      = 100.0       # ms — each EMG analysis window
WIN_SAMP    = int(WIN_MS / 1000 * FS_EMG)  # 200 samples
CTRL_LAG_MS = (200.0, 300.0)   # control window: 200-300 ms before event
PAD_MS      = 300.0            # same as yaml_runner mdf_pad_ms
NPERSEG     = 128              # Welch → freq resolution = 2000/128 ≈ 15.6 Hz
LOW_BAND    = (50, 200)        # Hz
HIGH_BAND   = (200, 450)       # Hz
MIN_RMS_PCT = 0.05             # reject windows with RMS < 5% of session median
WARMUP_MIN  = 20.0             # post-settling boundary
EPS         = 1e-20            # avoid log(0)

print("=" * 60)
print("Experiment 10: High-Dynamic IMU Event PSD Analysis")
print("=" * 60)

# ── load data ─────────────────────────────────────────────────────────────────

print("\nLoading log0305 stitched data...")
sessions = loader.discover_sessions("log0305")
emg_df, imu_df, _, _ = loader.load_session_stitched(sessions)

# EMG: sort by abs_us, extract arrays
emg_s = emg_df.dropna(subset=['raw']).sort_values('abs_us').reset_index(drop=True)
abs_us_arr = emg_s['abs_us'].to_numpy(dtype=np.int64)
raw_arr    = emg_s['raw'].to_numpy(dtype=float)

# IMU: sort by ts_ms, compute acc_dyn
# ax/ay/az are in physical units (g) after load_session_stitched FSR conversion.
imu_s = imu_df.dropna(subset=['ts_ms']).sort_values('ts_ms').reset_index(drop=True)
assert imu_s['ax'].abs().quantile(0.99) < 50, \
    "ax appears to be in m/s², not g — check FSR conversion"
imu_ts_ms = imu_s['ts_ms'].to_numpy(dtype=float)
acc_mag   = np.sqrt(imu_s['ax']**2 + imu_s['ay']**2 + imu_s['az']**2).to_numpy()
acc_dyn   = np.abs(acc_mag - 1.0)   # remove gravity (in g; 1g ≈ 9.81 m/s²)

# Swing features (canonical 20-min skip)
swings = pd.read_csv("out0305_w20/swing_features.csv")
swings["t_min"] = swings["t_peak_ms"] / 60000

# Session median RMS for flatline filter
session_rms_median = np.median(swings["rms"].dropna())
rms_threshold = MIN_RMS_PCT * session_rms_median

print(f"  EMG rows: {len(emg_s):,}  IMU rows: {len(imu_s):,}")
print(f"  Swings: {len(swings)}  Session RMS median: {session_rms_median:.1f}")

# ── per-swing processing ──────────────────────────────────────────────────────

print("\nProcessing swings...")

results = []
n_rejected = {"outside_window": 0, "short_samples": 0, "low_rms": 0, "imu_missing": 0}

for _, r in swings.iterrows():
    t_start_ms = float(r['t_start_ms'])
    t_end_ms   = float(r['t_end_ms'])
    t_peak_ms  = float(r['t_peak_ms'])
    swing_id   = int(r['swing_id'])
    t_min      = float(r['t_min'])

    # Padded window boundaries (same as per_swing_emg_features_stitched)
    t0p_ms = t_start_ms - PAD_MS
    t1p_ms = t_end_ms   + PAD_MS
    t0p_us = int(t0p_ms * 1000)
    t1p_us = int(t1p_ms * 1000)

    # IMU acc_dyn window
    ia0 = int(np.searchsorted(imu_ts_ms, t0p_ms, side='left'))
    ia1 = int(np.searchsorted(imu_ts_ms, t1p_ms, side='right'))
    if ia1 - ia0 < 3:
        n_rejected["imu_missing"] += 1
        continue

    imu_seg    = acc_dyn[ia0:ia1]
    imu_ts_seg = imu_ts_ms[ia0:ia1]

    # Find peak dynamic acceleration in this window
    pk_idx            = int(np.argmax(imu_seg))
    acc_dyn_peak_val  = float(imu_seg[pk_idx])
    acc_dyn_peak_t_ms = float(imu_ts_seg[pk_idx])
    event_offset_ms   = acc_dyn_peak_t_ms - t_peak_ms   # + = after gyro peak

    # EMG padded window
    j0 = int(np.searchsorted(abs_us_arr, t0p_us, side='left'))
    j1 = int(np.searchsorted(abs_us_arr, t1p_us, side='right'))
    raw_pad    = raw_arr[j0:j1]
    abs_us_pad = abs_us_arr[j0:j1]

    if raw_pad.size < WIN_SAMP * 2:
        n_rejected["outside_window"] += 1
        continue

    # FIX: preprocess the FULL padded window once, then slice.
    # Filtering 200-sample windows independently creates edge transients that
    # contaminate high-frequency PSD comparisons — the central measurement here.
    proc_pad = preprocess_emg(raw_pad, FS_EMG)

    # Near-peak window: ±WIN_MS/2 around event (indices into proc_pad)
    event_us     = acc_dyn_peak_t_ms * 1000.0
    half_us      = (WIN_MS / 2) * 1000.0
    near_i0_abs  = int(np.searchsorted(abs_us_pad, event_us - half_us, side='left'))
    near_i1_abs  = int(np.searchsorted(abs_us_pad, event_us + half_us, side='right'))
    near_proc    = proc_pad[near_i0_abs:near_i1_abs]

    # Control window: 200-300ms before event
    ctrl_end_us   = (acc_dyn_peak_t_ms - CTRL_LAG_MS[0]) * 1000.0
    ctrl_start_us = (acc_dyn_peak_t_ms - CTRL_LAG_MS[1]) * 1000.0
    ctrl_i0_abs   = int(np.searchsorted(abs_us_pad, ctrl_start_us, side='left'))
    ctrl_i1_abs   = int(np.searchsorted(abs_us_pad, ctrl_end_us,   side='right'))
    ctrl_proc     = proc_pad[ctrl_i0_abs:ctrl_i1_abs]

    # Validity: minimum sample count
    if near_proc.size < WIN_SAMP or ctrl_proc.size < WIN_SAMP:
        n_rejected["short_samples"] += 1
        continue

    # Trim to exact WIN_SAMP (take center if over-length)
    def trim_center(arr, n):
        if len(arr) > n:
            start = (len(arr) - n) // 2
            return arr[start:start + n]
        return arr

    near_proc = trim_center(near_proc, WIN_SAMP)
    ctrl_proc = trim_center(ctrl_proc, WIN_SAMP)

    # RMS validity check on preprocessed windows (reject near-zero / flatline)
    near_rms = float(np.sqrt(np.mean(near_proc ** 2)))
    ctrl_rms = float(np.sqrt(np.mean(ctrl_proc ** 2)))
    if near_rms < rms_threshold or ctrl_rms < rms_threshold:
        n_rejected["low_rms"] += 1
        continue

    # Welch PSD — normalized by total 50-450 Hz power
    def spectral_ratio(sig, fs, nperseg, low_band, high_band):
        f, psd = welch(sig, fs=fs, nperseg=nperseg,
                       noverlap=nperseg // 2, window='hann')
        mask_all  = (f >= 50) & (f <= 450)
        mask_low  = (f >= low_band[0])  & (f < low_band[1])
        mask_high = (f >= high_band[0]) & (f <= high_band[1])
        total = np.sum(psd[mask_all]) + EPS
        psd_norm = psd / total           # shape-normalised PSD
        low_pow  = np.sum(psd[mask_low])  + EPS
        high_pow = np.sum(psd[mask_high]) + EPS
        log_hf_lf = float(np.log10(high_pow / low_pow))
        return f, psd_norm, log_hf_lf, psd

    f_near, psd_near_norm, lr_near, psd_near_abs = spectral_ratio(
        near_proc, FS_EMG, NPERSEG, LOW_BAND, HIGH_BAND)
    f_ctrl, psd_ctrl_norm, lr_ctrl, psd_ctrl_abs = spectral_ratio(
        ctrl_proc, FS_EMG, NPERSEG, LOW_BAND, HIGH_BAND)

    delta_log_hf_lf = lr_near - lr_ctrl

    results.append({
        "swing_id":           swing_id,
        "t_min":              t_min,
        "t_peak_ms":          t_peak_ms,
        "acc_dyn_peak_val":   acc_dyn_peak_val,
        "acc_dyn_peak_t_ms":  acc_dyn_peak_t_ms,
        "event_offset_ms":    event_offset_ms,
        "lr_near":            lr_near,
        "lr_ctrl":            lr_ctrl,
        "delta_log_hf_lf":    delta_log_hf_lf,
        "near_rms":           near_rms,
        "ctrl_rms":           ctrl_rms,
        "psd_near_norm":      psd_near_norm,   # store full array
        "psd_ctrl_norm":      psd_ctrl_norm,
    })

df_res = pd.DataFrame([{k: v for k, v in r.items()
                         if k not in ('psd_near_norm', 'psd_ctrl_norm')}
                        for r in results])

if len(results) == 0:
    raise RuntimeError("No valid swings after filtering — cannot proceed.")

psd_near_stack = np.vstack([r["psd_near_norm"] for r in results])
psd_ctrl_stack = np.vstack([r["psd_ctrl_norm"] for r in results])
freq_axis = f_near   # same for all

print(f"\nValidity:")
print(f"  Total swings:     {len(swings)}")
print(f"  Valid swings:     {len(df_res)}")
print(f"  Rejected — IMU missing:    {n_rejected['imu_missing']}")
print(f"  Rejected — outside window: {n_rejected['outside_window']}")
print(f"  Rejected — short samples:  {n_rejected['short_samples']}")
print(f"  Rejected — low RMS:        {n_rejected['low_rms']}")

# ── statistics ────────────────────────────────────────────────────────────────

def compute_stats(df, label):
    d = df["delta_log_hf_lf"].dropna().values
    n = len(d)
    if n < 10:
        return {"label": label, "n": n}

    # Wilcoxon (primary)
    stat_w, p_w = wilcoxon(d, alternative='greater')

    # Paired t-test — use explicit shared mask to guarantee pairing
    valid = df[["lr_near", "lr_ctrl"]].dropna()
    _, p_t = ttest_rel(valid["lr_near"], valid["lr_ctrl"])

    # Bootstrap CI for median delta
    rng = np.random.default_rng(42)
    boot_medians = [np.median(rng.choice(d, size=n, replace=True))
                    for _ in range(5000)]
    ci_low, ci_high = np.percentile(boot_medians, [2.5, 97.5])

    # Spearman dose-response
    sp_r, sp_p = spearmanr(df["acc_dyn_peak_val"], df["delta_log_hf_lf"])

    # Cohen's dz
    dz = np.mean(d) / (np.std(d, ddof=1) + 1e-12)

    print(f"\n  [{label}]  n = {n}")
    print(f"    median delta_log_hf_lf = {np.median(d):+.4f}")
    print(f"    mean   delta_log_hf_lf = {np.mean(d):+.4f}  (Cohen dz = {dz:.3f})")
    print(f"    95% CI (bootstrap)     = [{ci_low:+.4f}, {ci_high:+.4f}]")
    print(f"    Wilcoxon one-sided p   = {p_w:.4f}  (stat = {stat_w:.1f})")
    print(f"    Paired t-test p        = {p_t:.4f}")
    print(f"    Spearman rho (dose)    = {sp_r:+.3f}  p = {sp_p:.4f}")
    print(f"    Event offset: median = {df['event_offset_ms'].median():+.1f} ms  "
          f"IQR = [{df['event_offset_ms'].quantile(.25):+.1f}, "
          f"{df['event_offset_ms'].quantile(.75):+.1f}] ms")

    return {
        "label": label, "n": n,
        "median_delta": np.median(d), "mean_delta": np.mean(d),
        "cohen_dz": dz,
        "ci_low": ci_low, "ci_high": ci_high,
        "wilcoxon_p": p_w, "paired_t_p": p_t,
        "spearman_rho": sp_r, "spearman_p": sp_p,
        "median_event_offset_ms": df["event_offset_ms"].median(),
        "iqr_event_offset_ms_lo": df["event_offset_ms"].quantile(.25),
        "iqr_event_offset_ms_hi": df["event_offset_ms"].quantile(.75),
        "median_acc_dyn_peak": df["acc_dyn_peak_val"].median(),
    }

print("\n" + "=" * 50)
print("STATISTICS")
print("=" * 50)

stats_all   = compute_stats(df_res, "All valid swings")
df_post20    = df_res[df_res["t_min"] > WARMUP_MIN]
stats_post20 = compute_stats(df_post20, f"Post-{WARMUP_MIN:.0f}min valid swings")

# ── gateway decision ──────────────────────────────────────────────────────────

print("\n" + "=" * 50)
print("GATEWAY DECISION")
print("=" * 50)

def gateway_decision(s_all, s_post):
    crit = {
        "median_all > 0":    s_all.get("median_delta", 0) > 0,
        "wilcoxon_all < 0.05": s_all.get("wilcoxon_p", 1) < 0.05,
        "median_post > 0":   s_post.get("median_delta", 0) > 0,
        "wilcoxon_post < 0.05": s_post.get("wilcoxon_p", 1) < 0.05,
        "spearman_r > 0":    s_all.get("spearman_rho", 0) > 0,
    }
    for c, v in crit.items():
        print(f"  {'✅' if v else '❌'}  {c}")
    n_pass = sum(crit.values())
    if n_pass == 5:
        verdict = "STRONG POSITIVE — proceed to Experiments 11/12 (pre-impact MDF + impact-risk score)"
    elif n_pass >= 3:
        verdict = "WEAK POSITIVE — exploratory only; no algorithm development yet"
    else:
        verdict = "NULL / NEGATIVE — deprioritize Batch C; focus on Batch B"
    print(f"\n  Verdict: {verdict}  ({n_pass}/5 criteria met)")
    return verdict

verdict = gateway_decision(stats_all, stats_post20)

# Save auditable CSV table (verdict and rejection counts included)
table_rows = [stats_all, stats_post20]
for row in table_rows:
    row["n_total"]                  = len(swings)
    row["n_rejected_imu_missing"]   = n_rejected["imu_missing"]
    row["n_rejected_outside_window"]= n_rejected["outside_window"]
    row["n_rejected_short"]         = n_rejected["short_samples"]
    row["n_rejected_low_rms"]       = n_rejected["low_rms"]
    row["gateway_verdict"]          = verdict

table_df   = pd.DataFrame([{k: v for k, v in row.items()} for row in table_rows])
table_path = os.path.join(OUT_DIR, "table_exp10_high_dynamic_event_psd.csv")
table_df.to_csv(table_path, index=False)
print(f"\n  Saved: {table_path}")


print("\nGenerating Figure 8...")

fig, axes = plt.subplots(2, 2, figsize=(12, 8))
ax_a, ax_b, ax_c, ax_d = axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]

# ── Panel A: Event timing distribution ───────────────────────────────────────
offsets = df_res["event_offset_ms"].dropna()
med_off = offsets.median()
iqr_lo  = offsets.quantile(0.25)
iqr_hi  = offsets.quantile(0.75)

ax_a.hist(offsets, bins=40, color="steelblue", alpha=0.75, edgecolor="white", lw=0.5)
ax_a.axvline(0, color="red", lw=1.3, linestyle="--", label="Gyro peak (t=0)")
ax_a.axvline(med_off, color="navy", lw=1.5, linestyle="-",
             label=f"Median = {med_off:+.0f} ms")
ax_a.axvspan(iqr_lo, iqr_hi, alpha=0.15, color="steelblue",
             label=f"IQR [{iqr_lo:+.0f}, {iqr_hi:+.0f}] ms")
ax_a.set_xlabel("acc_dyn peak offset from gyro peak (ms)", fontsize=10)
ax_a.set_ylabel("Count", fontsize=10)
ax_a.set_title("A — Trigger Timing Quality\n"
               "acc_dyn peak relative to gyro peak", fontsize=10)
ax_a.legend(fontsize=8)
ax_a.grid(True, alpha=0.25)
if 50 <= med_off <= 250:
    interp = "follow-through / deceleration"
elif abs(med_off) < 50:
    interp = "near gyro peak (swing apex)"
else:
    interp = "timing unclear"
ax_a.text(0.98, 0.97, f"n = {len(offsets)}\n→ {interp}",
          transform=ax_a.transAxes, fontsize=8, ha="right", va="top",
          bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.9))

# ── Panel B: Normalized PSD near vs. control ─────────────────────────────────
mask_plot = (freq_axis >= 40) & (freq_axis <= 480)
f_plot = freq_axis[mask_plot]

near_med = np.median(psd_near_stack[:, mask_plot], axis=0)
ctrl_med = np.median(psd_ctrl_stack[:, mask_plot], axis=0)
near_q25 = np.percentile(psd_near_stack[:, mask_plot], 25, axis=0)
near_q75 = np.percentile(psd_near_stack[:, mask_plot], 75, axis=0)
ctrl_q25 = np.percentile(psd_ctrl_stack[:, mask_plot], 25, axis=0)
ctrl_q75 = np.percentile(psd_ctrl_stack[:, mask_plot], 75, axis=0)

ax_b.plot(f_plot, near_med, color="tomato",     lw=2.0, label="Near acc_dyn peak")
ax_b.plot(f_plot, ctrl_med, color="steelblue",  lw=2.0, label="Control (pre-event)")
ax_b.fill_between(f_plot, near_q25, near_q75, alpha=0.15, color="tomato")
ax_b.fill_between(f_plot, ctrl_q25, ctrl_q75, alpha=0.15, color="steelblue")
ax_b.axvspan(*LOW_BAND,  alpha=0.06, color="steelblue", label="Low band 50–200 Hz")
ax_b.axvspan(*HIGH_BAND, alpha=0.06, color="tomato",    label="High band 200–450 Hz")
ax_b.set_xlabel("Frequency (Hz)", fontsize=10)
ax_b.set_ylabel("Normalized PSD (power fraction)", fontsize=10)
ax_b.set_title("B — Median Normalized PSD Shape\n"
               "Near-event vs. pre-event control (IQR shaded)", fontsize=10)
ax_b.legend(fontsize=7.5)
ax_b.grid(True, alpha=0.25)

# ── Panel C: Paired delta distribution ────────────────────────────────────────
d_all   = df_res["delta_log_hf_lf"].dropna().values
d_post  = df_post20["delta_log_hf_lf"].dropna().values

ax_c.hist(d_all, bins=35, alpha=0.55, color="steelblue",
          label=f"All valid (n={len(d_all)})", edgecolor="white", lw=0.5)
ax_c.hist(d_post, bins=35, alpha=0.55, color="tomato",
          label=f"Post-{WARMUP_MIN:.0f}min (n={len(d_post)})", edgecolor="white", lw=0.5)
ax_c.axvline(0, color="black", lw=1.3, linestyle="--")
ax_c.axvline(np.median(d_all),  color="steelblue", lw=2.0,
             linestyle="-", label=f"Median all = {np.median(d_all):+.4f}")
ax_c.axvline(np.median(d_post), color="tomato",     lw=2.0,
             linestyle="-", label=f"Median post = {np.median(d_post):+.4f}")

p_str = f"Wilcoxon p (all) = {stats_all.get('wilcoxon_p',1):.3f}\n" \
        f"Wilcoxon p (post) = {stats_post20.get('wilcoxon_p',1):.3f}"
ax_c.text(0.98, 0.97, p_str, transform=ax_c.transAxes,
          fontsize=8.5, ha="right", va="top",
          bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.9))
ax_c.set_xlabel("Δ log₁₀(high/low spectral ratio)  [near − control]", fontsize=10)
ax_c.set_ylabel("Count", fontsize=10)
ax_c.set_title("C — Paired Delta Distribution\n"
               "Primary gateway test (positive = elevated high-freq near event)",
               fontsize=10)
ax_c.legend(fontsize=8)
ax_c.grid(True, alpha=0.25)

# ── Panel D: Dose-response scatter ────────────────────────────────────────────
x = df_res["acc_dyn_peak_val"].values
y = df_res["delta_log_hf_lf"].values
sr, sp = spearmanr(x, y)

ax_d.scatter(x, y, s=5, alpha=0.25, color="darkorange", zorder=2)
# visual trend line only; inference uses Spearman correlation (not this line)
m, b = np.polyfit(x, y, 1)
x_line = np.linspace(x.min(), x.max(), 200)
ax_d.plot(x_line, m * x_line + b, color="black", lw=1.5, linestyle="--", zorder=3)
ax_d.axhline(0, color="gray", lw=1.0, linestyle=":", alpha=0.7)
ax_d.text(0.98, 0.97,
          f"Spearman rho = {sr:+.3f}\np = {sp:.3f}",
          transform=ax_d.transAxes, fontsize=9, ha="right", va="top",
          bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.9))
ax_d.set_xlabel("acc_dyn peak magnitude (g)", fontsize=10)
ax_d.set_ylabel("Δ log₁₀(high/low spectral ratio)", fontsize=10)
ax_d.set_title("D — Dose-Response\n"
               "Larger dynamic event → larger spectral shift?", fontsize=10)
ax_d.grid(True, alpha=0.25)

fig.suptitle(
    "Figure 8  |  Experiment 10: High-Dynamic IMU Event PSD Analysis (log0305)\n"
    f"Gateway verdict: {verdict[:50]}",
    fontsize=10, fontweight="bold"
)
plt.tight_layout()
fig_path = os.path.join(OUT_DIR, "fig8_high_dynamic_event_psd.png")
plt.savefig(fig_path, dpi=150)
plt.close()
print(f"  Saved: {fig_path}")

print("\n" + "=" * 60)
print("Experiment 10 complete.")
print(f"Gateway verdict: {verdict}")
print("=" * 60)
