import pandas as pd
import numpy as np
from scipy import stats

files = {
    "0303": r"C:\wangx\ftc\emg_util\out0303\swing_features.csv",
    "0305": r"C:\wangx\ftc\emg_util\out0305\swing_features.csv",
}

for label, fpath in files.items():
    print("=" * 72)
    print(f"FILE: log{label}  ({fpath})")
    print("=" * 72)

    df = pd.read_csv(fpath)

    # ------------------------------------------------------------------ #
    # 1. Basic stats
    # ------------------------------------------------------------------ #
    print("\n--- 1. BASIC STATS ---")
    n = len(df)
    t_min = df['t_peak_ms'].min()
    t_max = df['t_peak_ms'].max()
    dur   = (t_max - t_min) / 60000.0
    print(f"  Total swings : {n}")
    print(f"  t_peak_ms    : {t_min:.0f} .. {t_max:.0f} ms  ({dur:.2f} min)")
    print(f"  Columns      : {list(df.columns)}")

    # ------------------------------------------------------------------ #
    # Compute thirds (by time percentile)
    # ------------------------------------------------------------------ #
    t_33 = df['t_peak_ms'].quantile(1/3)
    t_67 = df['t_peak_ms'].quantile(2/3)
    segs = {
        'early': df[df['t_peak_ms'] <= t_33],
        'mid':   df[(df['t_peak_ms'] > t_33) & (df['t_peak_ms'] <= t_67)],
        'late':  df[df['t_peak_ms'] > t_67],
    }
    t33_min = (t_33 - t_min) / 60000
    t67_min = (t_67 - t_min) / 60000
    print(f"  Thirds split : early=0..{t33_min:.1f} min | mid={t33_min:.1f}..{t67_min:.1f} min | late={t67_min:.1f}..{dur:.1f} min")
    for s, d in segs.items():
        print(f"    {s}: n={len(d)}")

    # ------------------------------------------------------------------ #
    # 2. IMU trend
    # ------------------------------------------------------------------ #
    print("\n--- 2. IMU TREND (by thirds) ---")
    imu_cols = [c for c in ['imu_peak_mag', 'imu_mean_acc_dyn', 'imu_peak_acc_dyn'] if c in df.columns]
    if imu_cols:
        hdr = f"  {'metric':<24}  {'early mean (std)':>22}  {'mid mean (std)':>22}  {'late mean (std)':>22}  delta(early->late)"
        print(hdr)
        for col in imu_cols:
            row = f"  {col:<24}"
            means = []
            for seg in ['early', 'mid', 'late']:
                s = segs[seg][col].dropna()
                row += f"  {s.mean():9.3f} ({s.std():.3f})"
                means.append(s.mean())
            delta = means[2] - means[0]
            pct   = delta / means[0] * 100 if means[0] != 0 else float('nan')
            row  += f"  {delta:+.3f}  ({pct:+.1f}%)"
            print(row)
    else:
        print("  (no IMU columns found)")

    # ------------------------------------------------------------------ #
    # 3. EMG quality trend
    # ------------------------------------------------------------------ #
    print("\n--- 3. EMG QUALITY TREND (by thirds) ---")
    emg_cols = [c for c in ['rms', 'mdf', 'swing_mdf_drop_pct', 'swing_acc_drop_pct'] if c in df.columns]
    if emg_cols:
        hdr = f"  {'metric':<26}  {'early mean (std)':>22}  {'mid mean (std)':>22}  {'late mean (std)':>22}  delta(early->late)"
        print(hdr)
        for col in emg_cols:
            row = f"  {col:<26}"
            means = []
            for seg in ['early', 'mid', 'late']:
                s = segs[seg][col].dropna()
                row += f"  {s.mean():9.3f} ({s.std():.3f})"
                means.append(s.mean())
            delta = means[2] - means[0]
            pct   = delta / abs(means[0]) * 100 if means[0] != 0 else float('nan')
            row  += f"  {delta:+.3f}  ({pct:+.1f}%)"
            print(row)
    else:
        print("  (no EMG columns found)")

    # ------------------------------------------------------------------ #
    # 4. Swing rate per 5-min bucket
    # ------------------------------------------------------------------ #
    print("\n--- 4. SWING RATE (per 5-min bucket) ---")
    df['bucket_5min'] = ((df['t_peak_ms'] - t_min) / (5 * 60000)).astype(int)
    rate = df.groupby('bucket_5min').size()
    for b, cnt in rate.items():
        s0 = int(b * 5); e0 = s0 + 5
        print(f"  {s0:>3}-{e0:<3} min : {cnt:3d} swings")

    # ------------------------------------------------------------------ #
    # 5. Pearson r vs time
    # ------------------------------------------------------------------ #
    print("\n--- 5. PEARSON r vs t_peak_ms ---")
    all_m = imu_cols + emg_cols
    if all_m:
        print(f"  {'metric':<26}  {'r':>8}  {'p-value':>10}  trend  sig")
        for col in all_m:
            sub = df[['t_peak_ms', col]].dropna()
            if len(sub) < 5:
                print(f"  {col:<26}  (too few points)")
                continue
            r, p = stats.pearsonr(sub['t_peak_ms'], sub[col])
            direction = "DOWN" if r < -0.05 else ("UP" if r > 0.05 else "flat")
            sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))
            print(f"  {col:<26}  {r:8.4f}  {p:10.6f}  {direction:4s}  {sig}")

    # ------------------------------------------------------------------ #
    # 6. log0303: MDF thirds vs baseline
    # ------------------------------------------------------------------ #
    if label == "0303" and 'mdf' in df.columns:
        print("\n--- 6. log0303: MDF TREND vs BASELINE 201 Hz ---")
        baseline = 201.0
        print(f"  Baseline MDF = {baseline} Hz (from baseline.json)")
        for seg in ['early', 'mid', 'late']:
            s = segs[seg]['mdf'].dropna()
            drop = (baseline - s.mean()) / baseline * 100
            print(f"  {seg:5s}: n={len(s):3d}  mean={s.mean():.2f} Hz  std={s.std():.2f}  drop_from_baseline={drop:+.2f}%")
        overall_drop = (baseline - df['mdf'].mean()) / baseline * 100
        print(f"  session mean mdf={df['mdf'].mean():.2f} Hz  overall_drop={overall_drop:+.2f}%")

    # ------------------------------------------------------------------ #
    # 7. log0305: IMU-based fatigue detail
    # ------------------------------------------------------------------ #
    if label == "0305":
        print("\n--- 7. log0305: IMU-BASED FATIGUE DETAIL (MDF drop only -2.6%) ---")
        for col in ['swing_acc_drop_pct', 'imu_peak_mag']:
            if col not in df.columns:
                print(f"  '{col}' not found")
                continue
            print(f"\n  {col}:")
            for seg in ['early', 'mid', 'late']:
                s = segs[seg][col].dropna()
                print(f"    {seg:5s}: n={len(s):3d}  mean={s.mean():.3f}  std={s.std():.3f}  median={s.median():.3f}")
            sub = df[['t_peak_ms', col]].dropna()
            r, p = stats.pearsonr(sub['t_peak_ms'], sub[col])
            sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))
            print(f"    Pearson r={r:.4f}  p={p:.6f} {sig}")
            # delta early -> late
            e_mean = segs['early'][col].dropna().mean()
            l_mean = segs['late'][col].dropna().mean()
            delta  = l_mean - e_mean
            pct    = delta / abs(e_mean) * 100 if e_mean != 0 else float('nan')
            print(f"    delta early->late: {delta:+.3f} ({pct:+.1f}%)")

print("\n====== DONE ======")
