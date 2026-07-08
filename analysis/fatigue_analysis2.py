#!/usr/bin/env python3
"""Full fatigue analysis for log0303 and log0305 swing_features.csv files."""
import csv, math, sys

def mean(vals):
    v = [x for x in vals if x is not None and not math.isnan(x)]
    return sum(v)/len(v) if v else float('nan')

def std(vals):
    v = [x for x in vals if x is not None and not math.isnan(x)]
    if len(v) < 2: return float('nan')
    m = sum(v)/len(v)
    return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1))

def median(vals):
    v = sorted(x for x in vals if x is not None and not math.isnan(x))
    if not v: return float('nan')
    n = len(v)
    return v[n//2] if n%2 else (v[n//2-1]+v[n//2])/2

def pearsonr(xs, ys):
    n = len(xs)
    if n < 3: return float('nan'), float('nan')
    mx, my = sum(xs)/n, sum(ys)/n
    sx = math.sqrt(sum((x-mx)**2 for x in xs)/(n-1))
    sy = math.sqrt(sum((y-my)**2 for y in ys)/(n-1))
    if sx == 0 or sy == 0: return float('nan'), float('nan')
    r = sum((xs[i]-mx)*(ys[i]-my) for i in range(n)) / ((n-1)*sx*sy)
    # p-value approximation via t-distribution
    t = r * math.sqrt(n-2) / math.sqrt(max(1e-15, 1-r*r))
    # two-tailed p from t with n-2 df, use approximation
    # simple approximation for large n
    import math as m
    # use complementary incomplete beta function approximation
    df = n - 2
    tt = abs(t)
    # approximation: p ≈ 2 * (1 - normal_cdf(|t|)) for large df
    # use erfc for normal approximation
    p = math.erfc(tt / math.sqrt(2))  # rough approximation
    return r, p

def sig_label(p):
    if math.isnan(p): return "?"
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"

def load_csv(path):
    rows = []
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed = {}
            for k, v in row.items():
                try:
                    parsed[k] = float(v)
                except:
                    parsed[k] = None
            rows.append(parsed)
    return rows

def quantile(vals, q):
    v = sorted(x for x in vals if x is not None and not math.isnan(x))
    if not v: return float('nan')
    idx = q * (len(v) - 1)
    lo, hi = int(idx), min(int(idx)+1, len(v)-1)
    return v[lo] + (idx - lo) * (v[hi] - v[lo])

FILES = {
    "0303": r"C:\wangx\ftc\emg_util\out0303\swing_features.csv",
    "0305": r"C:\wangx\ftc\emg_util\out0305\swing_features.csv",
}

for label, fpath in FILES.items():
    print("=" * 72)
    print(f"FILE: log{label}  ({fpath})")
    print("=" * 72)

    rows = load_csv(fpath)
    n = len(rows)
    ts = [r['t_peak_ms'] for r in rows]
    t_min, t_max = min(ts), max(ts)
    dur = (t_max - t_min) / 60000.0

    print(f"\n--- 1. BASIC STATS ---")
    print(f"  Total swings : {n}")
    print(f"  t_peak_ms    : {t_min:.0f} .. {t_max:.0f} ms  ({dur:.2f} min)")
    print(f"  Columns      : {list(rows[0].keys())}")

    # Thirds
    t_33 = quantile(ts, 1/3)
    t_67 = quantile(ts, 2/3)
    segs = {
        'early': [r for r in rows if r['t_peak_ms'] <= t_33],
        'mid':   [r for r in rows if t_33 < r['t_peak_ms'] <= t_67],
        'late':  [r for r in rows if r['t_peak_ms'] > t_67],
    }
    print(f"  Thirds bounds: early=0..{(t_33-t_min)/60000:.1f} min | mid={((t_33-t_min)/60000):.1f}..{((t_67-t_min)/60000):.1f} min | late={((t_67-t_min)/60000):.1f}..{dur:.1f} min")
    for s, d in segs.items():
        print(f"    {s}: n={len(d)}")

    # 2. IMU trend
    print(f"\n--- 2. IMU TREND (by thirds) ---")
    imu_cols = [c for c in ['imu_peak_mag', 'imu_mean_acc_dyn', 'imu_peak_acc_dyn'] if c in rows[0]]
    if imu_cols:
        hdr = f"  {'metric':<24}  {'early mean(std)':>22}  {'mid mean(std)':>22}  {'late mean(std)':>22}  delta(e->l)%"
        print(hdr)
        for col in imu_cols:
            row_s = f"  {col:<24}"
            ms = []
            for seg in ['early', 'mid', 'late']:
                v = [r[col] for r in segs[seg] if r[col] is not None]
                m_ = mean(v); s_ = std(v)
                row_s += f"  {m_:9.3f}({s_:.3f})"
                ms.append(m_)
            delta = ms[2]-ms[0]
            pct = delta/ms[0]*100 if ms[0] != 0 else float('nan')
            row_s += f"  {delta:+.2f} ({pct:+.1f}%)"
            print(row_s)

    # 3. EMG quality trend
    print(f"\n--- 3. EMG QUALITY TREND (by thirds) ---")
    emg_cols = [c for c in ['rms','mdf','swing_mdf_drop_pct','swing_acc_drop_pct'] if c in rows[0]]
    if emg_cols:
        hdr = f"  {'metric':<26}  {'early mean(std)':>22}  {'mid mean(std)':>22}  {'late mean(std)':>22}  delta(e->l)%"
        print(hdr)
        for col in emg_cols:
            row_s = f"  {col:<26}"
            ms = []
            for seg in ['early', 'mid', 'late']:
                v = [r[col] for r in segs[seg] if r[col] is not None]
                m_ = mean(v); s_ = std(v)
                row_s += f"  {m_:9.3f}({s_:.3f})"
                ms.append(m_)
            delta = ms[2]-ms[0]
            pct = delta/abs(ms[0])*100 if ms[0] != 0 else float('nan')
            row_s += f"  {delta:+.3f} ({pct:+.1f}%)"
            print(row_s)

    # 4. Swing rate
    print(f"\n--- 4. SWING RATE (per 5-min bucket) ---")
    from collections import defaultdict
    buckets = defaultdict(int)
    for r in rows:
        b = int((r['t_peak_ms'] - t_min) / (5*60000))
        buckets[b] += 1
    for b in sorted(buckets):
        s0 = int(b*5); e0 = s0+5
        print(f"  {s0:>4}-{e0:<4} min: {buckets[b]:3d} swings")

    # 5. Pearson r
    print(f"\n--- 5. PEARSON r vs t_peak_ms ---")
    all_m = imu_cols + emg_cols
    print(f"  {'metric':<26}  {'r':>8}  {'p':>10}  trend  sig")
    for col in all_m:
        pairs = [(r['t_peak_ms'], r[col]) for r in rows if r[col] is not None]
        if len(pairs) < 5:
            print(f"  {col:<26}  (too few)")
            continue
        xs, ys = zip(*pairs)
        r_, p_ = pearsonr(list(xs), list(ys))
        direction = "DOWN" if r_ < -0.05 else ("UP" if r_ > 0.05 else "flat")
        print(f"  {col:<26}  {r_:8.4f}  {p_:10.6f}  {direction:4s}  {sig_label(p_)}")

    # 6. log0303 MDF vs baseline
    if label == "0303" and 'mdf' in rows[0]:
        print(f"\n--- 6. log0303: MDF TREND vs BASELINE 201 Hz ---")
        baseline = 201.0
        print(f"  Baseline MDF = {baseline} Hz")
        for seg in ['early', 'mid', 'late']:
            v = [r['mdf'] for r in segs[seg] if r['mdf'] is not None]
            m_ = mean(v); s_ = std(v)
            drop = (baseline - m_) / baseline * 100
            print(f"  {seg:5s}: n={len(v):3d}  mean={m_:.2f} Hz  std={s_:.2f}  drop_from_baseline={drop:+.2f}%")
        all_mdf = [r['mdf'] for r in rows if r['mdf'] is not None]
        m_all = mean(all_mdf)
        drop_all = (baseline - m_all) / baseline * 100
        print(f"  session mean MDF={m_all:.2f} Hz  overall_drop_from_baseline={drop_all:+.2f}%")

    # 7. log0305 IMU fatigue detail
    if label == "0305":
        print(f"\n--- 7. log0305: IMU-BASED FATIGUE DETAIL (fatigue_summary MDF drop -2.6%) ---")
        for col in ['swing_acc_drop_pct', 'imu_peak_mag']:
            if col not in rows[0]: continue
            print(f"\n  {col}:")
            for seg in ['early', 'mid', 'late']:
                v = [r[col] for r in segs[seg] if r[col] is not None]
                print(f"    {seg:5s}: n={len(v):3d}  mean={mean(v):.3f}  std={std(v):.3f}  median={median(v):.3f}")
            pairs = [(r['t_peak_ms'], r[col]) for r in rows if r[col] is not None]
            xs, ys = zip(*pairs)
            r_, p_ = pearsonr(list(xs), list(ys))
            print(f"    Pearson r={r_:.4f}  p={p_:.6f} {sig_label(p_)}")
            v_e = [r[col] for r in segs['early'] if r[col] is not None]
            v_l = [r[col] for r in segs['late']  if r[col] is not None]
            delta = mean(v_l) - mean(v_e)
            pct = delta/abs(mean(v_e))*100 if mean(v_e) != 0 else float('nan')
            print(f"    delta early->late: {delta:+.3f} ({pct:+.1f}%)")

print("\n====== DONE ======")
