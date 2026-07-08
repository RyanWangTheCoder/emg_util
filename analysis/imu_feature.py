import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, detrend
import matplotlib.pyplot as plt

# -------------------------------
# Utility: filters & entropy
# -------------------------------

def butter_lowpass(cut, fs, order=4):
    ny = 0.5 * fs
    b, a = butter(order, cut / ny, btype='low')
    return b, a

def lp_filter(x, fs, cut=20.0, order=4):
    if len(x) < 3*order:
        return x
    b, a = butter_lowpass(cut, fs, order=order)
    return filtfilt(b, a, x)

def sample_entropy(x, m=2, r_ratio=0.2):
    """
    Simple SampEn (m, r) using Chebyshev distance.
    r = r_ratio * std(x). Returns np.nan for too-short signals.
    """
    x = np.asarray(x, dtype=float)
    N = x.size
    if N < m + 2:
        return np.nan
    r = r_ratio * np.std(x, ddof=0)
    def _phi(m):
        # build embed matrix of m-length vectors
        Xm = np.array([x[i:i+m] for i in range(N - m + 1)])
        # count matches (distance <= r) excluding self
        C = 0
        for i in range(len(Xm)):
            d = np.max(np.abs(Xm - Xm[i]), axis=1)
            # exclude self-match at index i
            C += np.sum(d <= r) - 1
        # average probability
        denom = (len(Xm) * (len(Xm) - 1))
        return C / denom if denom > 0 else np.nan
    A = _phi(m+1)
    B = _phi(m)
    if A <= 0 or B <= 0 or np.isnan(A) or np.isnan(B):
        return np.nan
    return -np.log(A / B)

# -------------------------------
# Orientation (pitch/roll) from accel
# -------------------------------
def accel_to_pitch_roll(ax, ay, az):
    """
    Pitch/roll from accelerometer (gravity-dominant).
    Returns radians.
    """
    # Avoid division warnings
    eps = 1e-9
    pitch = np.arctan2(-ax, np.sqrt(ay**2 + az**2) + eps)   # rotation around Y
    roll  = np.arctan2( ay, (az + eps))                     # rotation around X
    return pitch, roll

# -------------------------------
# Feature extraction (windowed)
# -------------------------------
def window_indices(n, fs, win_s=2.0, overlap=0.5):
    hop = int(win_s * fs * (1 - overlap))
    win = int(win_s * fs)
    i = 0
    idx = []
    while i + win <= n:
        idx.append((i, i + win))
        i += hop if hop > 0 else win
    return idx

def compute_features(df, fs, win_s=2.0, overlap=0.5, baseline_mask=None):
    """
    df columns: time, ax, ay, az, gx, gy, gz (SI units)
    """
    t = df['time'].to_numpy()
    ax = df['ax'].to_numpy()
    ay = df['ay'].to_numpy()
    az = df['az'].to_numpy()
    gx = df['gx'].to_numpy()
    gy = df['gy'].to_numpy()
    gz = df['gz'].to_numpy()

    # Detrend & filter (low-pass ~20 Hz to cut HF noise)
    ax_f = lp_filter(detrend(ax, type='constant'), fs, 20)
    ay_f = lp_filter(detrend(ay, type='constant'), fs, 20)
    az_f = lp_filter(detrend(az, type='constant'), fs, 20)
    gx_f = lp_filter(detrend(gx, type='constant'), fs, 20)
    gy_f = lp_filter(detrend(gy, type='constant'), fs, 20)
    gz_f = lp_filter(detrend(gz, type='constant'), fs, 20)

    # Accelerometer magnitude and jerk (derivative)
    acc_mag = np.sqrt(ax_f**2 + ay_f**2 + az_f**2)
    dt = np.gradient(t)
    # robust dt
    dt[dt <= 0] = np.median(dt[dt > 0]) if np.any(dt > 0) else 1.0 / fs
    jerk = np.gradient(acc_mag, dt)  # m/s^3

    # Orientation for sway metrics
    pitch, roll = accel_to_pitch_roll(ax_f, ay_f, az_f)
    pitch = lp_filter(pitch, fs, 10)
    roll  = lp_filter(roll,  fs, 10)

    # Gyro magnitude
    gyro_mag = np.sqrt(gx_f**2 + gy_f**2 + gz_f**2)

    feats = []
    idxs = window_indices(len(t), fs, win_s, overlap)
    for (i0, i1) in idxs:
        seg = slice(i0, i1)
        seconds = t[i1-1] - t[i0]
        if seconds <= 0:
            continue

        # Basic window arrays
        axw, ayw, azw = ax_f[seg], ay_f[seg], az_f[seg]
        gmw = gyro_mag[seg]
        amw = acc_mag[seg]
        jw  = jerk[seg]
        pw, rw = pitch[seg], roll[seg]

        # Features
        feat = {
            't_start': t[i0],
            't_end': t[i1-1],
            # Acceleration RMS & per-axis
            'acc_rms': np.sqrt(np.mean(amw**2)),
            'ax_rms': np.sqrt(np.mean(axw**2)),
            'ay_rms': np.sqrt(np.mean(ayw**2)),
            'az_rms': np.sqrt(np.mean(azw**2)),
            # Angular velocity RMS
            'gyro_rms': np.sqrt(np.mean(gmw**2)),
            # Jerk index (RMS jerk)
            'jerk_rms': np.sqrt(np.mean(jw**2)),
            # Range of motion (ROM) of pitch/roll (radians)
            'rom_pitch': np.max(pw) - np.min(pw),
            'rom_roll':  np.max(rw) - np.min(rw),
            # Sway RMS: variability of pitch & roll (radians)
            'sway_pitch_rms': np.sqrt(np.mean((pw - np.mean(pw))**2)),
            'sway_roll_rms':  np.sqrt(np.mean((rw - np.mean(rw))**2)),
            # Irregularity: sample entropy of acc magnitude
            'sampen_acc': sample_entropy(amw, m=2, r_ratio=0.2),
        }
        feats.append(feat)

    feats = pd.DataFrame(feats)
    # Label baseline windows if a mask was provided (time-based)
    if baseline_mask is not None:
        feats['is_baseline'] = ((feats['t_start'] >= baseline_mask[0]) &
                                (feats['t_end']   <= baseline_mask[1]))
    else:
        feats['is_baseline'] = False
    return feats

# -------------------------------
# Postural Instability Scoring
# -------------------------------
def fit_baseline(feats, baseline_selector):
    base = feats[baseline_selector].copy()
    stats = {}
    for col in ['sway_pitch_rms', 'sway_roll_rms', 'jerk_rms', 'sampen_acc',
                'rom_pitch', 'rom_roll', 'acc_rms', 'gyro_rms']:
        stats[col] = {
            'mean': base[col].mean(),
            'std':  base[col].std(ddof=1) if len(base) > 1 else 1e-6
        }
    return stats

def postural_instability_score(feats, base_stats, weights=None):
    """
    Compute PIS by weighted z-scores:
      + sway_pitch_rms (↑ unstable)
      + sway_roll_rms  (↑ unstable)
      + jerk_rms       (↑ unstable)
      + sampen_acc     (↑ irregularity)
      - rom_pitch      (↓ suggests instability; invert)
      - rom_roll
    """
    if weights is None:
        # default emphasis on sway & jerk; moderate on entropy; small on ROM
        weights = {
            'sway_pitch_rms': 0.28,
            'sway_roll_rms':  0.28,
            'jerk_rms':       0.22,
            'sampen_acc':     0.12,
            'rom_pitch':      0.05,
            'rom_roll':       0.05,
        }

    # z-score helper
    def z(col, val):
        mu = base_stats[col]['mean']
        sd = base_stats[col]['std'] if base_stats[col]['std'] > 1e-9 else 1e-9
        return (val - mu) / sd

    pis = []
    for _, row in feats.iterrows():
        z_sway_p = z('sway_pitch_rms', row['sway_pitch_rms'])
        z_sway_r = z('sway_roll_rms',  row['sway_roll_rms'])
        z_jerk   = z('jerk_rms',       row['jerk_rms'])
        z_sampen = z('sampen_acc',     row['sampen_acc'])
        # invert ROM (lower-than-baseline should increase PIS)
        z_rom_p  = -z('rom_pitch',     row['rom_pitch'])
        z_rom_r  = -z('rom_roll',      row['rom_roll'])

        score = (
            weights['sway_pitch_rms'] * z_sway_p +
            weights['sway_roll_rms']  * z_sway_r +
            weights['jerk_rms']       * z_jerk   +
            weights['sampen_acc']     * z_sampen +
            weights['rom_pitch']      * z_rom_p  +
            weights['rom_roll']       * z_rom_r
        )
        pis.append(score)
    return np.array(pis)

def detect_instability(pis, feats, z_threshold=2.5, min_consec=3):
    """
    Flag fatigue/instability when PIS exceeds threshold for 'min_consec' windows.
    Returns boolean mask and list of intervals (t_start, t_end).
    """
    over = pis > z_threshold
    # find consecutive runs
    flags = np.zeros_like(over, dtype=bool)
    count = 0
    for i, v in enumerate(over):
        count = count + 1 if v else 0
        flags[i] = (count >= min_consec)
    # intervals
    intervals = []
    active = False
    start_t = None
    for i, f in enumerate(flags):
        if f and not active:
            active = True
            start_t = feats.iloc[i]['t_start']
        if active and (not f or i == len(flags)-1):
            end_t = feats.iloc[i]['t_end']
            intervals.append((start_t, end_t))
            active = False
    return flags, intervals

# -------------------------------
# Data I/O: load CSV or simulate
# -------------------------------
def load_imu_csv(path, fs=None):
    """
    Expects columns: time(s), ax, ay, az, gx, gy, gz
    If no fs provided, infer from time.
    """
    df = pd.read_csv(path)
    required = ['time','ax','ay','az','gx','gy','gz']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in CSV: {missing}")
    if fs is None:
        t = df['time'].to_numpy()
        dt = np.diff(t)
        dt = dt[dt > 0]
        fs = 1.0 / np.median(dt) if len(dt) else 100.0
    return df, float(fs)

def simulate_imu(fs=100, t_baseline=20, t_activity=40, seed=7):
    """
    Simulate trunk-mounted IMU during baseline (quiet stance) then
    racket swings with increasing postural instability toward the end.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(0, t_baseline + t_activity, 1/fs)
    n = len(t)

    # Baseline sway: small pitch/roll oscillations
    sway_freq = 0.4
    pitch = 2*np.pi/180 * np.sin(2*np.pi*sway_freq*t) + rng.normal(0, 0.2*np.pi/180, n)
    roll  = 2*np.pi/180 * np.cos(2*np.pi*sway_freq*t) + rng.normal(0, 0.2*np.pi/180, n)

    # Activity: transient bursts to mimic swings
    for k in range(10, len(t), int(fs*3)):
        if k+int(0.5*fs) < n:
            pitch[k:k+int(0.5*fs)] += (rng.normal(0.0, 1.0*np.pi/180, int(0.5*fs)) +
                                       np.hanning(int(0.5*fs))*5*np.pi/180)
            roll[k:k+int(0.5*fs)]  += (rng.normal(0.0, 1.0*np.pi/180, int(0.5*fs)) +
                                       np.hanning(int(0.5*fs))*4*np.pi/180)

    # Progressive fatigue in last 1/3 of activity: larger sway & jerk
    fatigue_start = t_baseline + (2/3)*t_activity
    fat_idx = t >= fatigue_start
    pitch[fat_idx] += rng.normal(0, 1.5*np.pi/180, fat_idx.sum())
    roll[fat_idx]  += rng.normal(0, 1.5*np.pi/180, fat_idx.sum())

    # Construct accel from pitch/roll (approximate gravity projection + linear accel noise)
    g = 9.80665
    ax = -g * np.sin(pitch)
    ay =  g * np.sin(roll)
    az =  g * np.cos(pitch) * np.cos(roll)
    # add small linear acceleration (sports motion) + noise (higher in fatigue)
    lin_noise = rng.normal(0, 0.25, n)
    lin_noise[fat_idx] += rng.normal(0, 0.25, fat_idx.sum())  # more noisy after fatigue
    ax += lin_noise * 0.15
    ay += lin_noise * 0.10
    az += lin_noise * 0.05

    # Gyro from angular rates (finite difference of angles)
    dt = 1/fs
    gx = np.gradient(roll, dt)    # rad/s (rot about x approximated by roll rate)
    gy = np.gradient(pitch, dt)   # rad/s (rot about y approximated by pitch rate)
    gz = rng.normal(0, 0.05, n)   # small yaw noise

    df = pd.DataFrame({
        'time': t,
        'ax': ax, 'ay': ay, 'az': az,
        'gx': gx, 'gy': gy, 'gz': gz
    })

    # Provide baseline time window (0, t_baseline)
    baseline_mask = (0.0, float(t_baseline))
    return df, fs, baseline_mask, fatigue_start

# -------------------------------
# Main demo (set csv_path=None to simulate)
# -------------------------------
if __name__ == "__main__":
    # ---- Config ----
    csv_path = None  # put path like "/mnt/data/imu_tennis.csv" or leave None to simulate
    fs_default = 100.0
    win_s = 2.0
    overlap = 0.5

    if csv_path:
        df, fs = load_imu_csv(csv_path)
        # Assume first N seconds are baseline; adjust as needed
        baseline_mask = (df['time'].min(), df['time'].min() + 20.0)
        fatigue_start = None
    else:
        df, fs, baseline_mask, fatigue_start = simulate_imu(fs=int(fs_default), t_baseline=20, t_activity=40)

    feats = compute_features(df, fs, win_s=win_s, overlap=overlap, baseline_mask=baseline_mask)
    base_stats = fit_baseline(feats, feats['is_baseline'])

    pis = postural_instability_score(feats, base_stats)
    feats['PIS'] = pis

    flags, intervals = detect_instability(pis, feats, z_threshold=2.5, min_consec=3)
    feats['fatigue_flag'] = flags

    # ---- Console summary ----
    print("\nBaseline stats (key features):")
    for k in ['sway_pitch_rms','sway_roll_rms','jerk_rms','sampen_acc','rom_pitch','rom_roll']:
        print(f"  {k:>15s}: mean={base_stats[k]['mean']:.4f}, std={base_stats[k]['std']:.4f}")

    print("\nDetected postural-instability intervals:")
    if intervals:
        for (s,e) in intervals:
            print(f"  {s:7.2f}s → {e:7.2f}s")
    else:
        print("  None at current thresholds.")

    # ---- Diagnostic: Print feature statistics ----
    print("\n=== Feature Statistics ===")
    print(feats[['acc_rms', 'gyro_rms', 'jerk_rms', 'sway_pitch_rms', 'sway_roll_rms', 'sampen_acc']].describe())

    print("\n=== PIS Statistics ===")
    print(f"PIS min: {pis.min():.4f}, max: {pis.max():.4f}, mean: {pis.mean():.4f}, std: {pis.std():.4f}")
    # ---- Plot 1: Raw IMU signals ----
    fig, axes = plt.subplots(2, 1, figsize=(14, 8))

    # Accelerometer
    axes[0].plot(df['time'], df['ax'], label='ax', alpha=0.7)
    axes[0].plot(df['time'], df['ay'], label='ay', alpha=0.7)
    axes[0].plot(df['time'], df['az'], label='az', alpha=0.7)
    axes[0].axvspan(baseline_mask[0], baseline_mask[1], color='green', alpha=0.1, label='Baseline')
    if fatigue_start is not None:
        axes[0].axvline(fatigue_start, color='k', ls=':', label='Fatigue start')
    axes[0].set_ylabel('Acceleration (m/s²)')
    axes[0].set_title('Raw Accelerometer Data')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Gyroscope
    axes[1].plot(df['time'], df['gx'], label='gx', alpha=0.7)
    axes[1].plot(df['time'], df['gy'], label='gy', alpha=0.7)
    axes[1].plot(df['time'], df['gz'], label='gz', alpha=0.7)
    axes[1].axvspan(baseline_mask[0], baseline_mask[1], color='green', alpha=0.1, label='Baseline')
    if fatigue_start is not None:
        axes[1].axvline(fatigue_start, color='k', ls=':', label='Fatigue start')
    axes[1].set_xlabel('Time (s)')
    axes[1].set_ylabel('Angular Velocity (rad/s)')
    axes[1].set_title('Raw Gyroscope Data')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('imu_raw_signals.png', dpi=150)
    print("Saved: imu_raw_signals.png")
    plt.show()

    # ---- Plot 2: Key Features Over Time ----
    fig, axes = plt.subplots(3, 2, figsize=(14, 10))
    ts = 0.5*(feats['t_start'] + feats['t_end'])

    axes[0, 0].plot(ts, feats['acc_rms'], 'b-', lw=1.5)
    axes[0, 0].set_ylabel('Acc RMS (m/s²)')
    axes[0, 0].set_title('Acceleration RMS')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].axvspan(baseline_mask[0], baseline_mask[1], color='green', alpha=0.1)

    axes[0, 1].plot(ts, feats['gyro_rms'], 'r-', lw=1.5)
    axes[0, 1].set_ylabel('Gyro RMS (rad/s)')
    axes[0, 1].set_title('Gyroscope RMS')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].axvspan(baseline_mask[0], baseline_mask[1], color='green', alpha=0.1)

    axes[1, 0].plot(ts, feats['jerk_rms'], 'g-', lw=1.5)
