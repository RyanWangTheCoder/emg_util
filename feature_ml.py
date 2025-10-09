# pip install if needed (Colab has sklearn by default)
# !pip install numpy scipy scikit-learn matplotlib seaborn

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.signal import butter, filtfilt, iirnotch, welch
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, confusion_matrix, roc_curve

# Set plot style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ---------- Load your EMG ----------
emg = pd.read_csv('emg_example.csv')['emg'].values.astype(np.float32)  # one column: 'emg'
fs = 1000  # sampling rate (Hz) — set to your acquisition rate

# ---------- Filters ----------
def bandpass(x, fs, low=20, high=450, order=4):
    b, a = butter(order, [low/(fs/2), high/(fs/2)], btype='band')
    return filtfilt(b, a, x)

def notch60(x, fs, f0=60, Q=30):
    b, a = iirnotch(f0/(fs/2), Q)
    return filtfilt(b, a, x)

x = bandpass(emg, fs)
x = notch60(x, fs)

# ---------- Windowing ----------
win_ms = 200
step_ms = 100  # 50% overlap
win = int(fs * win_ms/1000)
step = int(fs * step_ms/1000)

def sliding_windows(sig, win, step):
    starts = np.arange(0, len(sig)-win+1, step)
    return np.array([sig[s:s+win] for s in starts]), starts

Xwin, starts = sliding_windows(x, win, step)

# ---------- Feature extraction ----------
def mav(sig):  return np.mean(np.abs(sig))
def rms(sig):  return np.sqrt(np.mean(sig**2))
def wl(sig):   return np.sum(np.abs(np.diff(sig)))
def zc(sig, thr=0.01):
    s = sig - np.mean(sig)
    return np.sum(((s[:-1] * s[1:]) < 0) & (np.abs(s[:-1]-s[1:]) > thr))
def ssc(sig, thr=0.01):
    s = sig - np.mean(sig)
    return np.sum(((s[1:-1]-s[:-2])*(s[1:-1]-s[2:]) > 0) &
                  (np.abs(s[1:-1]-s[:-2]) > thr) & (np.abs(s[1:-1]-s[2:]) > thr))
def mdf(sig, fs):
    # Welch PSD, then median freq
    f, Pxx = welch(sig, fs=fs, nperseg=len(sig))
    cdf = np.cumsum(Pxx)
    total = cdf[-1]
    return f[np.searchsorted(cdf, total/2)]

def extract_features(win_sig):
    return np.array([
        mav(win_sig),
        rms(win_sig),
        wl(win_sig),
        zc(win_sig),
        ssc(win_sig),
        mdf(win_sig, fs)
    ], dtype=np.float32)

F = np.vstack([extract_features(w) for w in Xwin])

# ---------- Build labels (Option 1: MDF/RMS thresholds) ----------
# Baseline from first N windows (e.g., 1 minute of rest)
baseline_duration_sec = 60
N_base = int((baseline_duration_sec*fs - win)/step) + 1
base_mdf = np.median(F[:N_base, -1])   # MDF column
base_rms = np.median(F[:N_base, 1])    # RMS column

mdf_drop_pct = (base_mdf - F[:, -1]) / base_mdf * 100.0
rms_increase_pct = (F[:, 1] - base_rms) / base_rms * 100.0

fatigue_flag = (mdf_drop_pct >= 12.0) & (rms_increase_pct >= 8.0)  # tweak thresholds
# Smooth labels: need 4 consecutive windows to call it fatigue-on
consec = 4
Y = np.zeros_like(fatigue_flag, dtype=int)
count = 0
for i, f in enumerate(fatigue_flag):
    if f:
        count += 1
        if count >= consec: Y[i] = 1
    else:
        count = 0

# ---------- Train/test split ----------
X_train, X_test, y_train, y_test = train_test_split(F, Y, test_size=0.3, random_state=42, stratify=Y)

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

# Logistic Regression
logit = LogisticRegression(max_iter=1000)
logit.fit(X_train_s, y_train)
proba_lr = logit.predict_proba(X_test_s)[:,1]
pred_lr  = (proba_lr >= 0.5).astype(int)

# kNN
knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(X_train_s, y_train)
proba_knn = knn.predict_proba(X_test_s)[:,1]
pred_knn  = (proba_knn >= 0.5).astype(int)

print("Logistic: acc", accuracy_score(y_test, pred_lr), "F1", f1_score(y_test, pred_lr), "ROC-AUC", roc_auc_score(y_test, proba_lr))
print("kNN:      acc", accuracy_score(y_test, pred_knn), "F1", f1_score(y_test, pred_knn), "ROC-AUC", roc_auc_score(y_test, proba_knn))
print("Confusion (Logistic):\n", confusion_matrix(y_test, pred_lr))

# ========== VISUALIZATIONS ==========

# 1. Raw vs Filtered Signal
fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=True)
t_raw = np.arange(len(emg)) / fs
t_filt = np.arange(len(x)) / fs

axes[0].plot(t_raw, emg, 'gray', alpha=0.6, lw=0.5, label='Raw EMG')
axes[0].set_ylabel('Amplitude (μV)')
axes[0].set_title('Raw EMG Signal')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].plot(t_filt, x, 'b', lw=0.7, label='Filtered EMG (20-450 Hz + Notch 60Hz)')
axes[1].set_xlabel('Time (s)')
axes[1].set_ylabel('Amplitude (μV)')
axes[1].set_title('Filtered EMG Signal')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('emg_raw_vs_filtered.png', dpi=150)
print("Saved: emg_raw_vs_filtered.png")
plt.show()

# 2. Feature Evolution Over Time
feature_names = ['MAV', 'RMS', 'WL', 'ZC', 'SSC', 'MDF']
t_windows = (starts + win/2) / fs  # center time of each window

fig, axes = plt.subplots(3, 2, figsize=(14, 10))
axes = axes.flatten()

for i, name in enumerate(feature_names):
    axes[i].plot(t_windows, F[:, i], lw=1.2, color=f'C{i}')
    axes[i].set_title(f'{name} Over Time')
    axes[i].set_xlabel('Time (s)')
    axes[i].set_ylabel(name)
    axes[i].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('emg_features_evolution.png', dpi=150)
print("Saved: emg_features_evolution.png")
plt.show()

# 3. Fatigue Indicators (MDF drop % and RMS increase %)
fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=True)

axes[0].plot(t_windows, mdf_drop_pct, 'r', lw=1.5, label='MDF Drop %')
axes[0].axhline(12.0, color='k', linestyle='--', lw=1, label='Threshold (12%)')
axes[0].set_ylabel('MDF Drop (%)')
axes[0].set_title('Median Frequency Drop (Fatigue Indicator)')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].plot(t_windows, rms_increase_pct, 'g', lw=1.5, label='RMS Increase %')
axes[1].axhline(8.0, color='k', linestyle='--', lw=1, label='Threshold (8%)')
axes[1].set_xlabel('Time (s)')
axes[1].set_ylabel('RMS Increase (%)')
axes[1].set_title('RMS Increase (Fatigue Indicator)')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('emg_fatigue_indicators.png', dpi=150)
print("Saved: emg_fatigue_indicators.png")
plt.show()

# 4. Ground Truth Labels (Fatigue Detection)
fig, ax = plt.subplots(figsize=(14, 4))
colors = ['green' if y == 0 else 'red' for y in Y]
ax.scatter(t_windows, Y, c=colors, alpha=0.6, s=20, edgecolors='k', linewidths=0.5)
ax.set_xlabel('Time (s)')
ax.set_ylabel('Fatigue State')
ax.set_yticks([0, 1])
ax.set_yticklabels(['No Fatigue', 'Fatigue'])
ax.set_title('Ground Truth: Fatigue Onset Detection')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('emg_ground_truth_labels.png', dpi=150)
print("Saved: emg_ground_truth_labels.png")
plt.show()

# 5. Model Predictions vs Actual (Test Set)
fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=True)

# Logistic Regression
axes[0].plot(y_test, 'o', label='Actual', alpha=0.6, markersize=4)
axes[0].plot(pred_lr, 's', label='Predicted (Logistic)', alpha=0.6, markersize=3)
axes[0].set_ylabel('Class')
axes[0].set_yticks([0, 1])
axes[0].set_yticklabels(['No Fatigue', 'Fatigue'])
axes[0].set_title('Logistic Regression: Predictions vs Actual (Test Set)')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# kNN
axes[1].plot(y_test, 'o', label='Actual', alpha=0.6, markersize=4)
axes[1].plot(pred_knn, '^', label='Predicted (kNN)', alpha=0.6, markersize=3)
axes[1].set_xlabel('Test Sample Index')
axes[1].set_ylabel('Class')
axes[1].set_yticks([0, 1])
axes[1].set_yticklabels(['No Fatigue', 'Fatigue'])
axes[1].set_title('kNN: Predictions vs Actual (Test Set)')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('emg_predictions_vs_actual.png', dpi=150)
print("Saved: emg_predictions_vs_actual.png")
plt.show()

# 6. Confusion Matrices
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

cm_lr = confusion_matrix(y_test, pred_lr)
cm_knn = confusion_matrix(y_test, pred_knn)

sns.heatmap(cm_lr, annot=True, fmt='d', cmap='Blues', ax=axes[0],
            xticklabels=['No Fatigue', 'Fatigue'],
            yticklabels=['No Fatigue', 'Fatigue'])
axes[0].set_title('Logistic Regression\nConfusion Matrix')
axes[0].set_ylabel('True Label')
axes[0].set_xlabel('Predicted Label')

sns.heatmap(cm_knn, annot=True, fmt='d', cmap='Greens', ax=axes[1],
            xticklabels=['No Fatigue', 'Fatigue'],
            yticklabels=['No Fatigue', 'Fatigue'])
axes[1].set_title('kNN\nConfusion Matrix')
axes[1].set_ylabel('True Label')
axes[1].set_xlabel('Predicted Label')

plt.tight_layout()
plt.savefig('emg_confusion_matrices.png', dpi=150)
print("Saved: emg_confusion_matrices.png")
plt.show()

# 7. ROC Curves
fpr_lr, tpr_lr, _ = roc_curve(y_test, proba_lr)
fpr_knn, tpr_knn, _ = roc_curve(y_test, proba_knn)

fig, ax = plt.subplots(figsize=(8, 8))
ax.plot(fpr_lr, tpr_lr, 'b-', lw=2, label=f'Logistic Regression (AUC = {roc_auc_score(y_test, proba_lr):.3f})')
ax.plot(fpr_knn, tpr_knn, 'g-', lw=2, label=f'kNN (AUC = {roc_auc_score(y_test, proba_knn):.3f})')
ax.plot([0, 1], [0, 1], 'k--', lw=1, label='Random Classifier')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.set_title('ROC Curves: Fatigue Detection Models')
ax.legend(loc='lower right')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('emg_roc_curves.png', dpi=150)
print("Saved: emg_roc_curves.png")
plt.show()

print("\n✅ All visualizations saved!")
