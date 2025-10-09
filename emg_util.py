# -*- coding: utf-8 -*-
"""
EMG fatigue feature extraction & plotting

Features per sliding window:
  1) RMS
  2) Mean Frequency (MNF)
  3) Median Frequency (MDF)
  4) Wavelet Entropy (time-frequency feature)
  5) Sample Entropy (nonlinear feature)

Author: Larry's Copilot
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, iirnotch, welch, detrend
import pywt
import math

# ------------------ USER SETTINGS ------------------ #
FILE_PATH = r"C:\wangx\ftc\btLeApp\app\src\main\res\raw\emgdata.txt"
FS_HZ = 1000            # <<<<<<<<<<<<<<<<<<<<<< Set your EMG sampling rate (Hz)
CHANNEL_INDEX = 0       # 0-based index if multiple columns in the file
WINDOW_SEC = 1.0        # analysis window length (s) - common: 0.5–2.0 s
STEP_SEC = 0.25         # step/overlap hop (s) - e.g., 75% overlap with 1.0 s window
DO_EXPORT_CSV = True
CSV_OUT = "emg_features.csv"
# --------------------------------------------------- #

from scipy.signal import filtfilt

from scipy.signal import welch

def mnf_mdf_feature(x, fs):
    x = np.asarray(x, dtype=float)
    n = x.size
    if n < 2 or not np.isfinite(x).any():
        return np.nan, np.nan

    nperseg = min(n, 256)
    noverlap = nperseg // 2 if nperseg >= 16 else 0

    f, Pxx = welch(x, fs=fs, nperseg=nperseg, noverlap=noverlap,
                   window='hann', scaling='density')
    if Pxx.size == 0 or not np.isfinite(Pxx).any():
        return np.nan, np.nan

    Pxx = np.maximum(Pxx, 1e-20)
    psd_sum = float(np.sum(Pxx))
    mnf = float(np.sum(f * Pxx) / psd_sum)

    cdf = np.cumsum(Pxx)
    mdf = float(f[min(np.searchsorted(cdf, 0.5 * psd_sum), len(f) - 1)])
    return mnf, mdf

def filtfilt_safe(b, a, x):
    n = x.size
    default_padlen = 3 * (max(len(a), len(b)) - 1)
    if n <= default_padlen:
        try:
            return filtfilt(b, a, x, method='gust')
        except Exception:
            padlen = max(1, min(default_padlen, n - 2))
            return filtfilt(b, a, x, padlen=padlen)
    return filtfilt(b, a, x)

from pathlib import Path
import re
import numpy as np
import pandas as pd

def read_emg_file(filepath: str, channel_index=0):
    """
    Robust reader: tries multiple delimiters; falls back to extracting all numbers by regex.
    Returns a 1D numpy array (selected channel).
    """
    fp = Path(filepath)
    if not fp.exists():
        raise FileNotFoundError(f"File not found: {fp}")

    # --- Try structured parsing with pandas using several delimiters ---
    candidate_reads = []
    # (label, kwargs)
    attempts = [
        ("sep=None", dict(sep=None, engine="python", comment="#", header=None, dtype=str)),
        (",", dict(sep=",", engine="python", comment="#", header=None, dtype=str)),
        ("\\t", dict(sep="\t", engine="python", comment="#", header=None, dtype=str)),
        (";", dict(sep=";", engine="python", comment="#", header=None, dtype=str)),
        ("whitespace", dict(delim_whitespace=True, engine="python", comment="#", header=None, dtype=str)),
        ("|", dict(sep="|", engine="python", comment="#", header=None, dtype=str)),
    ]

    for label, kw in attempts:
        try:
            df = pd.read_csv(fp, **kw)
            df = df.apply(pd.to_numeric, errors="coerce")
            df = df.dropna(axis=1, how="all")
            if df.shape[1] > 0 and df.shape[0] > 0:
                arr = df.values.astype(float)
                candidate_reads.append((label, arr))
        except Exception:
            pass

    # Choose the parse with the most rows
    if candidate_reads:
        label_best, arr_best = max(candidate_reads, key=lambda t: t[1].shape[0])
        # If multiple columns, honor channel_index
        if arr_best.ndim == 2:
            if channel_index >= arr_best.shape[1]:
                raise ValueError(f"Requested channel_index={channel_index}, but file has only {arr_best.shape[1]} columns (best parse='{label_best}').")
            x = arr_best[:, channel_index]
        else:
            x = arr_best
        x = x[np.isfinite(x)]
        if x.size >= 10:  # reasonable lower bound
            return x

    # --- Fallback: extract every number in the file (robust to weird formats) ---
    text = fp.read_text(errors="ignore")
    # float regex: handles ints, floats, scientific notation, +/- signs
    nums = re.findall(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?", text)
    x = np.array([float(v) for v in nums], dtype=float)
    if x.size == 0:
        raise ValueError("No numeric data found in file (even with regex fallback). "
                         "Please check the file contents and delimiter.")
    return x

def bandpass_filter(x, fs, low=20.0, high=450.0, order=4):
    nyq = 0.5 * fs
    lown, highn = low/nyq, high/nyq
    b, a = butter(order, [lown, highn], btype='bandpass')
    return filtfilt_safe(b, a, x)

def notch_filter(x, fs, f0=60.0, q=30.0, harmonics=(2,)):  # 60Hz and (optionally) 120Hz, etc.
    y = x.copy()
    # Fundamental
    b, a = iirnotch(w0=f0/(fs/2), Q=q)
    y = filtfilt_safe(b, a, y)
    # Harmonics
    for h in harmonics:
        f = f0 * h
        if f < fs/2 - 1:
            b, a = iirnotch(w0=f/(fs/2), Q=q)
            y = filtfilt_safe(b, a, y)
    return y

def windowed_view(x, win_samples, step_samples):
    """Return list of (start, end) indices for sliding windows."""
    idx = []
    n = len(x)
    start = 0
    while start + win_samples <= n:
        idx.append((start, start + win_samples))
        start += step_samples
    return idx

def rms_feature(x):
    return np.sqrt(np.mean(np.square(x)))

def mnf_mdf_feature(x, fs):
    """
    Compute Mean Frequency (MNF) and Median Frequency (MDF) using Welch PSD.
    """
    # Welch parameters: nperseg equals window len, no overlap (windowing done outside)
    nperseg = len(x)
    if nperseg < 64:
        # fall back to small segment if window is too small
        nperseg = max(64, nperseg)
    f, Pxx = welch(x, fs=fs, nperseg=nperseg, noverlap=0, window='hann', scaling='density')
    Pxx = np.maximum(Pxx, 1e-20)  # avoid zeros
    psd_sum = np.sum(Pxx)
    mnf = np.sum(f * Pxx) / psd_sum

    cdf = np.cumsum(Pxx)
    half = 0.5 * psd_sum
    mdf_idx = np.searchsorted(cdf, half)
    mdf = f[min(mdf_idx, len(f)-1)]
    return mnf, mdf

import numpy as np
import pywt

def wavelet_entropy_feature(x, wavelet='db4', level=None):
    """
    Wavelet entropy from normalized energies of wavedec coefficients.
    Robust to short segments: returns NaN if no decomposition is possible.
    """
    x = np.asarray(x, dtype=float)
    n = x.size
    if n == 0 or not np.isfinite(x).any():
        return np.nan

    w = pywt.Wavelet(wavelet)
    # Max allowed level for 1-D data of length n
    max_level = pywt.dwt_max_level(data_len=n, filter_len=w.dec_len)
    # Choose level (auto if None)
    lvl = max_level if level is None else max(0, min(level, max_level))

    if lvl == 0:
        # No valid decomposition for this length & wavelet
        return np.nan

    # Do the decomposition (mode can be 'symmetric' or 'periodization')
    coeffs = pywt.wavedec(x, wavelet=w, level=lvl, mode='symmetric')

    energies = np.array([np.sum(c * c) for c in coeffs], dtype=float)
    total = float(np.sum(energies))
    if not np.isfinite(total) or total <= 0.0:
        return np.nan

    p = energies / total
    return float(-np.sum(p * np.log(p + 1e-20)))

def sample_entropy_feature(x, m=2, r=None):
    """
    Sample Entropy (SampEn) implementation.
    m: pattern length
    r: tolerance (default 0.2 * std)
    Returns SampEn(m, r, N).
    """
    x = np.asarray(x, dtype=float)
    N = len(x)
    if r is None:
        r = 0.2 * np.std(x)
    if N <= m + 1:
        return np.nan

    def _phi(m):
        # build embedding vectors
        X = np.array([x[i:i+m] for i in range(N - m + 1)])
        # Chebyshev distance (max-norm)
        count = 0
        for i in range(len(X)):
            dist = np.max(np.abs(X[i+1:] - X[i]), axis=1)
            count += np.sum(dist <= r)
        # number of template comparisons
        denom = (len(X) * (len(X) - 1)) / 2
        return count / denom if denom > 0 else 0.0

    phi_m   = _phi(m)
    phi_m1  = _phi(m + 1)
    if phi_m <= 1e-20 or phi_m1 <= 1e-20:
        return np.inf
    return -np.log(phi_m1 / phi_m)

def compute_features_over_time(x, fs, win_sec=1.0, step_sec=0.25):
    n = len(x)
    if n == 0:
        return np.asarray([]), {'RMS': np.asarray([]), 'MNF': np.asarray([]), 'MDF': np.asarray([]),
                                'WaveletEntropy': np.asarray([]), 'SampleEntropy': np.asarray([])}

    win_samples = int(round(win_sec * fs))
    step_samples = int(round(step_sec * fs))

    # If the signal is shorter than the requested window, shrink the window
    if n < win_samples:
        win_samples = n
        step_samples = max(1, win_samples // 4)

    windows = windowed_view(x, win_samples, step_samples)
    if not windows:
        windows = [(0, n)]

    t_centers = []
    rms_vals, mnf_vals, mdf_vals, went_vals, sampen_vals = [], [], [], [], []
    for (i0, i1) in windows:
        seg = x[i0:i1]
        t_centers.append((i0 + i1) / 2 / fs)
        rms_vals.append(rms_feature(seg))
        mnf, mdf = mnf_mdf_feature(seg, fs)
        mnf_vals.append(mnf)
        mdf_vals.append(mdf)
        went_vals.append(wavelet_entropy_feature(seg, wavelet='db4'))
        sampen_vals.append(sample_entropy_feature(seg, m=2, r=None))

    feats = {
        'RMS': np.asarray(rms_vals),
        'MNF': np.asarray(mnf_vals),
        'MDF': np.asarray(mdf_vals),
        'WaveletEntropy': np.asarray(went_vals),
        'SampleEntropy': np.asarray(sampen_vals),
    }
    return np.asarray(t_centers), feats
def preprocess_pipeline(x, fs):
    """
    Detrend -> Band-pass (20–450 Hz) -> Notch (60 Hz + 120 Hz)
    Adjust to your environment as needed.
    """
    y = detrend(x, type='constant')
    y = bandpass_filter(y, fs, 20.0, min(0.45*fs, 450.0))  # keep under Nyquist
    y = notch_filter(y, fs, f0=60.0, q=30.0, harmonics=(2,))  # USA mains
    return y

def plot_all(t_signal, signal, t_feat, feats, fs):
    nrows = 1 + len(feats)  # raw + 5 features
    fig, axes = plt.subplots(nrows=nrows, ncols=1, figsize=(13, 12), sharex=False)
    if nrows == 1:
        axes = [axes]

    # Raw signal
    axes[0].plot(t_signal, signal, color='k', lw=0.8)
    axes[0].set_title("Raw EMG (preprocessed)")
    axes[0].set_ylabel("Amplitude (a.u.)")
    axes[0].grid(True, alpha=0.2)

    # Features
    names = ['RMS', 'MNF', 'MDF', 'WaveletEntropy', 'SampleEntropy']
    ylabels = [
        "RMS (a.u.)",
        "Mean Freq (Hz)",
        "Median Freq (Hz)",
        "Wavelet Entropy",
        "Sample Entropy",
    ]
    for i, (name, yl) in enumerate(zip(names, ylabels), start=1):
        axes[i].plot(t_feat, feats[name], lw=1.5)
        axes[i].set_title(name)
        axes[i].set_ylabel(yl)
        axes[i].grid(True, alpha=0.2)

    axes[-1].set_xlabel("Time (s)")
    plt.tight_layout()
    plt.show()

def main():
    # 1) Load
    #emg = read_emg_file(FILE_PATH, channel_index=CHANNEL_INDEX)
    emg = pd.read_csv('emg_example.csv')['emg'].values.astype(np.float32)  # one column: 'emg'

    print(f"[DEBUG] raw: N={emg.size}, finite%={np.isfinite(emg).mean() * 100:.1f}%")

    # 2) Preprocess
    emg_proc = preprocess_pipeline(emg, FS_HZ)

    print(f"[DEBUG] proc: N={emg_proc.size}, finite%={np.isfinite(emg_proc).mean() * 100:.1f}%")

    win_samples = int(round(WINDOW_SEC * FS_HZ))
    step_samples = int(round(STEP_SEC * FS_HZ))
    print(f"[DEBUG] win/sec={WINDOW_SEC}, step/sec={STEP_SEC}, win_samples={win_samples}, step_samples={step_samples}")

    # 3) Time axis for signal
    t = np.arange(len(emg_proc)) / FS_HZ

    # 4) Features over time (sliding windows)
    t_feat, feats = compute_features_over_time(emg_proc, FS_HZ, win_sec=WINDOW_SEC, step_sec=STEP_SEC)

    print(f"[DEBUG] windows={t_feat.size}  | feats lens: " +
         ", ".join(f"{k}:{len(v)}" for k, v in feats.items()))

    # 5) Plot
    plot_all(t, emg_proc, t_feat, feats, FS_HZ)

    # 6) Export CSV (optional)
    if DO_EXPORT_CSV:
        df = pd.DataFrame({
            't_center_s': t_feat,
            'RMS': feats['RMS'],
            'MNF_Hz': feats['MNF'],
            'MDF_Hz': feats['MDF'],
            'WaveletEntropy': feats['WaveletEntropy'],
            'SampleEntropy': feats['SampleEntropy'],
        })
        df.to_csv(CSV_OUT, index=False)
        print(f"Saved features -> {CSV_OUT}")

if __name__ == "__main__":
    main()
