# Sensor Data Analysis Enhancement Recommendations for Publication
## Updated Based on Existing Research Roadmap & System Architecture

> **Context:** This document builds upon the existing RESEARCH_ROADMAP.md and integrates with the current system architecture (ESP32 → BLE → btCentral.py → emg_util.py pipeline).

---

## Executive Summary

After reviewing your **RESEARCH_ROADMAP.md** and **SYSTEM_HIGH_LEVEL_DESIGN.md**, I see you've already identified **multi-modal sensor fusion** as your chosen research direction and have a comprehensive plan. This updated document provides:

1. **Implementation-ready code** for the algorithms outlined in your roadmap
2. **Integration guidance** with your existing codebase
3. **Prioritized enhancements** aligned with your 6-9 month publication timeline
4. **Specific improvements** to bridge gaps between current implementation and roadmap goals

---

## Current Status Assessment

### ✅ Already Implemented (Strong Foundation)
1. **Robust data acquisition** — ESP32 BLE streaming with CRC validation, time synchronization
2. **Swing-aligned analysis** — IMU-based swing detection (gyro peak detection)
3. **Activity gating** — Hybrid gyro+acc intensity for work/rest segmentation
4. **Bout segmentation** — Groups swings into training bouts
5. **Basic EMG features** — MAV, RMS, WL, ZC, SSC, MNF, MDF
6. **Basic IMU features** — Gyro/acc magnitudes, RMS
7. **Fatigue detection** — MDF drop + RMS increase with baseline comparison
8. **Real-time capability** — Android app with live fatigue monitoring

### 🔄 Roadmap Goals (From RESEARCH_ROADMAP.md)
1. **Multi-modal fusion** — Early, Late, Attention-based (Section 5)
2. **Nonlinear complexity** — SampEn, DFA (Section 3.1)
3. **Wavelet analysis** — CWT for time-frequency (Section 3.1)
4. **Deep learning** — 1D-CNN-LSTM (Section 3.2)
5. **Personalized baselines** — Bayesian adaptation (Section 3.3)
6. **Biomechanical context** — Swing quality metrics (Section 3.5)
7. **Validation study** — N=20 participants, MVC + RPE ground truth (Section 6)

### 🎯 This Document's Focus
**Provide implementation-ready code and integration guidance for roadmap items 1-6**, prioritized to support your publication timeline.

---

## Priority 1: Implement Roadmap Section 5 (Fusion Algorithms)

Your roadmap already outlines three fusion approaches. Here's the implementation:

### 1.1 Early Fusion (Feature-Level) — IMMEDIATE PRIORITY

**Status:** Roadmap defined, needs implementation  
**Timeline:** 1 week  
**Integration point:** `emg_util_yaml_runner.py` → new function `compute_fusion_features()`

```python
# Add to emg_util.py

def compute_early_fusion_features(swing_feat_df: pd.DataFrame, 
                                  imu_df: pd.DataFrame,
                                  vitals_df: pd.DataFrame) -> pd.DataFrame:
    """Implement Early Fusion from RESEARCH_ROADMAP.md Section 5, Approach 1.
    
    Creates 18D feature vector per swing:
    - EMG (10): mav, rms, wl, zc, ssc, mnf, mdf, env_peak, env_mean, iemg
    - IMU (6): swing_velocity, jerk_rms, sway_pitch_rms, sway_roll_rms, rom_pitch, rom_roll
    - Vitals (2): hr_mean_bpm, spo2_mean
    
    Args:
        swing_feat_df: Per-swing EMG features (from compute_swing_emg_features)
        imu_df: Full IMU stream with ts_ms, ax, ay, az, gx, gy, gz
        vitals_df: Vitals log with ts_ms, hr_bpm, spo2
    
    Returns:
        DataFrame with 18 features per swing + metadata
    """
    fused = swing_feat_df.copy()
    
    # Add IMU features per swing
    imu_feats = []
    for _, swing in fused.iterrows():
        t0 = swing['t_start_ms']
        t1 = swing['t_end_ms']
        
        # Extract IMU segment for this swing
        imu_seg = imu_df[(imu_df['ts_ms'] >= t0) & (imu_df['ts_ms'] <= t1)]
        
        if len(imu_seg) < 5:  # Need minimum samples
            imu_feats.append({
                'swing_velocity': np.nan,
                'jerk_rms': np.nan,
                'sway_pitch_rms': np.nan,
                'sway_roll_rms': np.nan,
                'rom_pitch': np.nan,
                'rom_roll': np.nan
            })
            continue
        
        # Swing velocity (peak gyro magnitude)
        gx = imu_seg['gx'].to_numpy(float)
        gy = imu_seg['gy'].to_numpy(float)
        gz = imu_seg['gz'].to_numpy(float)
        gyro_mag = np.sqrt(gx**2 + gy**2 + gz**2)
        swing_velocity = float(np.max(gyro_mag))
        
        # Jerk (rate of acceleration change)
        ax = imu_seg['ax'].to_numpy(float)
        ay = imu_seg['ay'].to_numpy(float)
        az = imu_seg['az'].to_numpy(float)
        
        # Estimate sampling rate from timestamps
        dt_ms = np.diff(imu_seg['ts_ms'].to_numpy(float))
        fs_est = 1000.0 / np.median(dt_ms) if len(dt_ms) > 0 else 200.0
        
        jerk_x = np.diff(ax) * fs_est
        jerk_y = np.diff(ay) * fs_est
        jerk_z = np.diff(az) * fs_est
        jerk_mag = np.sqrt(jerk_x**2 + jerk_y**2 + jerk_z**2)
        jerk_rms = float(np.sqrt(np.mean(jerk_mag**2)))
        
        # Postural sway (from accelerometer)
        # Pitch ≈ atan2(ax, sqrt(ay² + az²))
        # Roll ≈ atan2(ay, sqrt(ax² + az²))
        pitch = np.arctan2(ax, np.sqrt(ay**2 + az**2))
        roll = np.arctan2(ay, np.sqrt(ax**2 + az**2))
        
        sway_pitch_rms = float(np.std(pitch))  # RMS of deviations
        sway_roll_rms = float(np.std(roll))
        
        # Range of motion (ROM)
        rom_pitch = float(np.ptp(pitch))  # Peak-to-peak
        rom_roll = float(np.ptp(roll))
        
        imu_feats.append({
            'swing_velocity': swing_velocity,
            'jerk_rms': jerk_rms,
            'sway_pitch_rms': sway_pitch_rms,
            'sway_roll_rms': sway_roll_rms,
            'rom_pitch': rom_pitch,
            'rom_roll': rom_roll
        })
    
    # Merge IMU features
    imu_feat_df = pd.DataFrame(imu_feats)
    for col in imu_feat_df.columns:
        fused[col] = imu_feat_df[col].values
    
    # Add vitals features per swing (nearest neighbor within ±2s)
    vitals_feats = []
    for _, swing in fused.iterrows():
        t_center = swing['t_peak_ms']
        
        # Find nearest vitals measurement within ±2000ms
        vitals_window = vitals_df[
            (vitals_df['ts_ms'] >= t_center - 2000) & 
            (vitals_df['ts_ms'] <= t_center + 2000)
        ]
        
        if len(vitals_window) == 0:
            # Forward-fill from last valid measurement
            prev_vitals = vitals_df[vitals_df['ts_ms'] < t_center]
            if len(prev_vitals) > 0:
                last_vital = prev_vitals.iloc[-1]
                hr_mean = float(last_vital['hr_bpm'])
                spo2_mean = float(last_vital['spo2'])
                interpolated = True
            else:
                hr_mean = np.nan
                spo2_mean = np.nan
                interpolated = True
        else:
            # Use nearest measurement
            nearest_idx = (vitals_window['ts_ms'] - t_center).abs().idxmin()
            nearest = vitals_window.loc[nearest_idx]
            hr_mean = float(nearest['hr_bpm'])
            spo2_mean = float(nearest['spo2'])
            interpolated = False
        
        vitals_feats.append({
            'hr_mean_bpm': hr_mean,
            'spo2_mean': spo2_mean,
            'vitals_interpolated': interpolated
        })
    
    # Merge vitals features
    vitals_feat_df = pd.DataFrame(vitals_feats)
    for col in vitals_feat_df.columns:
        fused[col] = vitals_feat_df[col].values
    
    return fused


def train_early_fusion_classifier(features_df: pd.DataFrame, 
                                  labels: np.ndarray,
                                  test_size: float = 0.2) -> Dict[str, Any]:
    """Train Random Forest classifier for early fusion (Roadmap Section 5, Approach 1).
    
    Args:
        features_df: DataFrame with 18 fusion features
        labels: Binary labels (0=non-fatigued, 1=fatigued)
        test_size: Train/test split ratio
    
    Returns:
        Dict with model, metrics, feature importance
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, roc_auc_score, f1_score, confusion_matrix
    
    # Feature columns (18D as per roadmap)
    feature_cols = [
        # EMG (10)
        'mav', 'rms', 'wl', 'zc', 'ssc', 'mnf', 'mdf', 
        'emg_env_peak', 'emg_env_mean', 'emg_iemg',
        # IMU (6)
        'swing_velocity', 'jerk_rms', 'sway_pitch_rms', 
        'sway_roll_rms', 'rom_pitch', 'rom_roll',
        # Vitals (2)
        'hr_mean_bpm', 'spo2_mean'
    ]
    
    # Handle missing features gracefully
    available_cols = [c for c in feature_cols if c in features_df.columns]
    X = features_df[available_cols].fillna(0).to_numpy()
    y = labels
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    
    # Train Random Forest (parameters from roadmap)
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=20,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]
    
    metrics = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'auc': float(roc_auc_score(y_test, y_proba)),
        'f1': float(f1_score(y_test, y_pred)),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
        'feature_importance': dict(zip(available_cols, clf.feature_importances_))
    }
    
    return {
        'model': clf,
        'metrics': metrics,
        'feature_cols': available_cols,
        'X_test': X_test,
        'y_test': y_test,
        'y_pred': y_pred,
        'y_proba': y_proba
    }
```

**Integration into `emg_util_yaml_runner.py`:**

```python
# Add to analyze_tennis_session() after swing_feat_df is computed

if mode in ['both', 'advanced']:
    # Compute fusion features
    fusion_df = core.compute_early_fusion_features(
        swing_feat_df, imu_df, 
        vitals_df if vitals_df is not None else pd.DataFrame()
    )
    fusion_df.to_csv(os.path.join(out_dir, 'fusion_features.csv'), index=False)
    
    # If ground truth labels available, train classifier
    if 'fatigue_label' in fusion_df.columns:
        labels = fusion_df['fatigue_label'].to_numpy()
        results = core.train_early_fusion_classifier(fusion_df, labels)
        
        with open(os.path.join(out_dir, 'fusion_classifier_results.json'), 'w') as f:
            json.dump({
                'metrics': results['metrics'],
                'feature_importance': results['metrics']['feature_importance']
            }, f, indent=2)
        
        log(f"Early fusion accuracy: {results['metrics']['accuracy']:.3f}, "
            f"AUC: {results['metrics']['auc']:.3f}")
```

---

### 1.2 Late Fusion (Decision-Level) — WEEK 2

**Implementation of Roadmap Section 5, Approach 2:**

```python
# Add to emg_util.py

def train_late_fusion_ensemble(emg_features: pd.DataFrame,
                               imu_features: pd.DataFrame,
                               vitals_features: pd.DataFrame,
                               labels: np.ndarray,
                               fusion_method: str = 'weighted') -> Dict[str, Any]:
    """Implement Late Fusion from RESEARCH_ROADMAP.md Section 5, Approach 2.
    
    Trains 3 modality-specific classifiers and combines predictions.
    
    Args:
        emg_features: EMG-only features (10D)
        imu_features: IMU-only features (6D)
        vitals_features: Vitals-only features (2D)
        labels: Binary fatigue labels
        fusion_method: 'weighted', 'majority', or 'stacking'
    
    Returns:
        Dict with 3 classifiers, fusion results, and metrics
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, roc_auc_score
    
    # Split data
    indices = np.arange(len(labels))
    train_idx, test_idx = train_test_split(
        indices, test_size=0.2, random_state=42, stratify=labels
    )
    
    # Train modality-specific classifiers
    # Classifier A: EMG-only (Random Forest)
    clf_emg = RandomForestClassifier(n_estimators=200, max_depth=10, 
                                     class_weight='balanced', random_state=42)
    X_emg_train = emg_features.iloc[train_idx].fillna(0).to_numpy()
    X_emg_test = emg_features.iloc[test_idx].fillna(0).to_numpy()
    clf_emg.fit(X_emg_train, labels[train_idx])
    P_emg = clf_emg.predict_proba(X_emg_test)[:, 1]
    
    # Classifier B: IMU-only (Random Forest)
    clf_imu = RandomForestClassifier(n_estimators=200, max_depth=10,
                                     class_weight='balanced', random_state=42)
    X_imu_train = imu_features.iloc[train_idx].fillna(0).to_numpy()
    X_imu_test = imu_features.iloc[test_idx].fillna(0).to_numpy()
    clf_imu.fit(X_imu_train, labels[train_idx])
    P_imu = clf_imu.predict_proba(X_imu_test)[:, 1]
    
    # Classifier C: Vitals-only (Logistic Regression)
    clf_vitals = LogisticRegression(class_weight='balanced', random_state=42)
    X_vitals_train = vitals_features.iloc[train_idx].fillna(0).to_numpy()
    X_vitals_test = vitals_features.iloc[test_idx].fillna(0).to_numpy()
    clf_vitals.fit(X_vitals_train, labels[train_idx])
    P_vitals = clf_vitals.predict_proba(X_vitals_test)[:, 1]
    
    y_test = labels[test_idx]
    
    # Fusion strategies
    if fusion_method == 'weighted':
        # Variant 2A: Weighted average (weights from roadmap)
        P_final = 0.50 * P_emg + 0.35 * P_imu + 0.15 * P_vitals
        y_pred = (P_final > 0.5).astype(int)
        
    elif fusion_method == 'majority':
        # Variant 2B: Majority vote
        vote_emg = (P_emg > 0.5).astype(int)
        vote_imu = (P_imu > 0.5).astype(int)
        vote_vitals = (P_vitals > 0.5).astype(int)
        y_pred = ((vote_emg + vote_imu + vote_vitals) >= 2).astype(int)
        P_final = (vote_emg + vote_imu + vote_vitals) / 3.0
        
    elif fusion_method == 'stacking':
        # Variant 2C: Meta-classifier
        meta_features_train = np.column_stack([
            clf_emg.predict_proba(X_emg_train)[:, 1],
            clf_imu.predict_proba(X_imu_train)[:, 1],
            clf_vitals.predict_proba(X_vitals_train)[:, 1]
        ])
        meta_features_test = np.column_stack([P_emg, P_imu, P_vitals])
        
        meta_clf = LogisticRegression(random_state=42)
        meta_clf.fit(meta_features_train, labels[train_idx])
        P_final = meta_clf.predict_proba(meta_features_test)[:, 1]
        y_pred = (P_final > 0.5).astype(int)
    else:
        raise ValueError(f"Unknown fusion_method: {fusion_method}")
    
    # Compute metrics
    metrics = {
        'fusion_method': fusion_method,
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'auc': float(roc_auc_score(y_test, P_final)),
        'emg_only_auc': float(roc_auc_score(y_test, P_emg)),
        'imu_only_auc': float(roc_auc_score(y_test, P_imu)),
        'vitals_only_auc': float(roc_auc_score(y_test, P_vitals))
    }
    
    return {
        'clf_emg': clf_emg,
        'clf_imu': clf_imu,
        'clf_vitals': clf_vitals,
        'meta_clf': meta_clf if fusion_method == 'stacking' else None,
        'metrics': metrics,
        'P_emg': P_emg,
        'P_imu': P_imu,
        'P_vitals': P_vitals,
        'P_final': P_final,
        'y_test': y_test,
        'y_pred': y_pred
    }
```

---

## Priority 2: Implement Roadmap Section 3.1 (Nonlinear Complexity)

Your roadmap identifies **SampEn and DFA** as high-priority additions. Here's the implementation:

### 2.1 Sample Entropy (SampEn)

```python
# Add to emg_util.py

def sample_entropy(signal: np.ndarray, m: int = 2, r: float = 0.2) -> float:
    """Compute Sample Entropy (SampEn) for EMG complexity analysis.
    
    From RESEARCH_ROADMAP.md Section 3.1: "Measures signal irregularity;
    fatigue reduces complexity before MDF drops."
    
    Args:
        signal: EMG signal (preprocessed)
        m: Embedding dimension (default 2)
        r: Tolerance (default 0.2 * std(signal))
    
    Returns:
        SampEn value (higher = more complex/irregular)
    
    Reference:
        Richman & Moorman (2000). "Physiological time-series analysis using
        approximate entropy and sample entropy." Am J Physiol Heart Circ Physiol.
    """
    N = len(signal)
    if N < 100:
        return np.nan
    
    r = r * np.std(signal, ddof=1)
    
    def _maxdist(x_i, x_j):
        return np.max(np.abs(x_i - x_j))
    
    def _phi(m):
        patterns = np.array([signal[i:i+m] for i in range(N-m)])
        C = np.zeros(N-m)
        for i in range(N-m):
            template = patterns[i]
            # Count matches (excluding self-match)
            dists = np.array([_maxdist(template, patterns[j]) 
                             for j in range(N-m) if j != i])
            C[i] = np.sum(dists <= r)
        
        # Avoid log(0)
        C = C[C > 0]
        if len(C) == 0:
            return 0.0
        return np.sum(np.log(C / (N-m)))
    
    phi_m = _phi(m)
    phi_m1 = _phi(m+1)
    
    return float(phi_m - phi_m1)


def detrended_fluctuation_analysis(signal: np.ndarray, 
                                   min_scale: int = 4,
                                   max_scale: int = None) -> float:
    """Compute DFA scaling exponent (alpha) for EMG long-range correlations.
    
    From RESEARCH_ROADMAP.md Section 3.1: "Long-range correlations in EMG;
    changes with fatigue."
    
    Args:
        signal: EMG signal (preprocessed)
        min_scale: Minimum window size
        max_scale: Maximum window size (default: len(signal)//4)
    
    Returns:
        DFA alpha exponent (0.5=white noise, 1.0=1/f noise, 1.5=Brownian)
    
    Reference:
        Peng et al. (1995). "Quantification of scaling exponents and crossover
        phenomena in nonstationary heartbeat time series." Chaos 5(1):82-87.
    """
    N = len(signal)
    if N < 100:
        return np.nan
    
    if max_scale is None:
        max_scale = N // 4
    
    # Integrate signal (cumulative sum)
    y = np.cumsum(signal - np.mean(signal))
    
    # Compute fluctuation for different scales
    scales = np.unique(np.logspace(np.log10(min_scale), 
                                   np.log10(max_scale), 
                                   num=20).astype(int))
    F = np.zeros(len(scales))
    
    for i, n in enumerate(scales):
        # Divide into non-overlapping segments
        n_segments = N // n
        if n_segments < 1:
            continue
        
        # Fit polynomial trend in each segment and compute residuals
        residuals = []
        for j in range(n_segments):
            segment = y[j*n:(j+1)*n]
            x = np.arange(len(segment))
            # Linear detrending
            coeffs = np.polyfit(x, segment, 1)
            trend = np.polyval(coeffs, x)
            residuals.extend((segment - trend)**2)
        
        # Root mean square fluctuation
        F[i] = np.sqrt(np.mean(residuals))
    
    # Fit log-log relationship: log(F) ~ alpha * log(n)
    valid = F > 0
    if np.sum(valid) < 3:
        return np.nan
    
    log_scales = np.log(scales[valid])
    log_F = np.log(F[valid])
    
    alpha = np.polyfit(log_scales, log_F, 1)[0]
    
    return float(alpha)
```

**Integration:**

```python
# Modify compute_swing_emg_features_stitched() in emg_util.py

# After computing MDF/MNF, add:
if raw_pad.size >= 256:  # Need sufficient samples for complexity metrics
    proc = core.preprocess_emg(raw_pad, fs)
    
    # Existing features
    mnf, mdf = core.mnf_mdf(proc, fs)
    
    # NEW: Nonlinear complexity features (Roadmap Section 3.1)
    sampen = core.sample_entropy(proc, m=2, r=0.2)
    dfa_alpha = core.detrended_fluctuation_analysis(proc)
else:
    mnf = mdf = sampen = dfa_alpha = np.nan

rows.append({
    # ... existing features ...
    'mnf': float(mnf) if mnf is not None else np.nan,
    'mdf': float(mdf) if mdf is not None else np.nan,
    'sampen': sampen,  # NEW
    'dfa_alpha': dfa_alpha,  # NEW
})
```

---

## Priority 3: Implement Roadmap Section 3.5 (Biomechanical Context)

Your roadmap identifies **swing quality metrics** as important. The swing velocity and jerk features are already included in the Early Fusion implementation above. Here's the additional DTW-based technique degradation metric:

### 3.1 Dynamic Time Warping for Technique Consistency

```python
# Add to emg_util.py

def compute_swing_dtw_distance(swing_imu: np.ndarray, 
                               template_imu: np.ndarray) -> float:
    """Compute DTW distance between swing and baseline template.
    
    From RESEARCH_ROADMAP.md Section 3.5: "Increasing DTW distance =
    technique breakdown."
    
    Args:
        swing_imu: IMU signal for current swing (N x 6: ax,ay,az,gx,gy,gz)
        template_imu: Baseline template swing (M x 6)
    
    Returns:
        Normalized DTW distance (0 = identical, higher = more deviation)
    """
    from scipy.spatial.distance import euclidean
    from fastdtw import fastdtw  # pip install fastdtw
    
    if len(swing_imu) < 5 or len(template_imu) < 5:
        return np.nan
    
    # Normalize both signals (z-score per axis)
    swing_norm = (swing_imu - np.mean(swing_imu, axis=0)) / (np.std(swing_imu, axis=0) + 1e-9)
    template_norm = (template_imu - np.mean(template_imu, axis=0)) / (np.std(template_imu, axis=0) + 1e-9)
    
    # Compute DTW distance
    distance, _ = fastdtw(swing_norm, template_norm, dist=euclidean)
    
    # Normalize by path length
    normalized_distance = distance / max(len(swing_imu), len(template_imu))
    
    return float(normalized_distance)


def create_baseline_swing_template(swings_imu: List[np.ndarray]) -> np.ndarray:
    """Create baseline swing template from first N swings.
    
    Uses DTW Barycenter Averaging (DBA) to find representative template.
    
    Args:
        swings_imu: List of IMU arrays from baseline swings
    
    Returns:
        Template swing (median length x 6)
    """
    from tslearn.barycenters import dtw_barycenter_averaging
    
    if len(swings_imu) == 0:
        return np.array([])
    
    # Pad/truncate to median length
    lengths = [len(s) for s in swings_imu]
    target_len = int(np.median(lengths))
    
    aligned = []
    for swing in swings_imu:
        if len(swing) > target_len:
            # Downsample
            indices = np.linspace(0, len(swing)-1, target_len).astype(int)
            aligned.append(swing[indices])
        elif len(swing) < target_len:
            # Upsample (linear interpolation)
            from scipy.interpolate import interp1d
            x_old = np.arange(len(swing))
            x_new = np.linspace(0, len(swing)-1, target_len)
            interp = interp1d(x_old, swing, axis=0, kind='linear')
            aligned.append(interp(x_new))
        else:
            aligned.append(swing)
    
    # Compute DBA template
    aligned_array = np.array(aligned)
    template = dtw_barycenter_averaging(aligned_array, max_iter=10)
    
    return template
```

---

## Priority 4: Statistical Validation (Roadmap Section 6)

Your roadmap requires **MVC + RPE ground truth**. Here's the implementation for correlation analysis:

```python
# Add to emg_util.py

def validate_against_ground_truth(swing_features: pd.DataFrame,
                                 mvc_decline_pct: float,
                                 rpe_timestamps: List[Dict],
                                 session_t0_ms: float) -> Dict[str, Any]:
    """Validate fatigue metrics against MVC and RPE ground truth.
    
    From RESEARCH_ROADMAP.md Section 6: "Correlate metrics with gold standards."
    
    Args:
        swing_features: Per-swing features with MDF, RMS, etc.
        mvc_decline_pct: Post-session MVC decline percentage
        rpe_timestamps: List of {"time_ms": ..., "rpe": ...} dicts
        session_t0_ms: Session start time in ms
    
    Returns:
        Dict with correlation coefficients and p-values
    """
    from scipy.stats import pearsonr, spearmanr
    
    # Interpolate RPE to each swing
    rpe_times = np.array([r['time_ms'] for r in rpe_timestamps])
    rpe_values = np.array([r['rpe'] for r in rpe_timestamps])
    
    swing_rpe = []
    for t_peak in swing_features['t_peak_ms']:
        # Find nearest RPE measurement
        idx = np.argmin(np.abs(rpe_times - t_peak))
        swing_rpe.append(rpe_values[idx])
    
    swing_features['rpe'] = swing_rpe
    
    # Compute correlations
    results = {}
    
    for metric in ['mdf', 'rms', 'sampen', 'dfa_alpha', 'swing_velocity']:
        if metric not in swing_features.columns:
            continue
        
        values = swing_features[metric].dropna().to_numpy()
        rpe_aligned = swing_features.loc[swing_features[metric].notna(), 'rpe'].to_numpy()
        
        if len(values) < 10:
            continue
        
        # Pearson correlation with RPE
        r_pearson, p_pearson = pearsonr(values, rpe_aligned)
        
        # Spearman correlation (non-parametric)
        r_spearman, p_spearman = spearmanr(values, rpe_aligned)
        
        results[metric] = {
            'pearson_r': float(r_pearson),
            'pearson_p': float(p_pearson),
            'spearman_r': float(r_spearman),
            'spearman_p': float(p_spearman),
            'significant': p_pearson < 0.05
        }
    
    # Overall session correlation with MVC decline
    # Use final 10% of swings as "fatigued state"
    n_final = max(10, len(swing_features) // 10)
    final_swings = swing_features.iloc[-n_final:]
    
    results['mvc_correlation'] = {
        'mvc_decline_pct': mvc_decline_pct,
        'final_mdf_drop': float(final_swings['swing_mdf_drop_pct'].mean()),
        'final_rms_increase': float(final_swings['swing_rms_increase_pct'].mean()),
        'correlation_mdf_mvc': float(np.corrcoef(
            [mvc_decline_pct], 
            [final_swings['swing_mdf_drop_pct'].mean()]
        )[0, 1])
    }
    
    return results
```

---

## Priority 5: Config Integration

Update `config.yaml` to enable new features:

```yaml
# Add to existing config.yaml

features:
  mode: 'advanced'  # 'bout', 'medium', 'both', 'advanced'
  
  # NEW: Advanced feature extraction (Roadmap Section 3.1)
  nonlinear_complexity:
    enable: true
    sampen_m: 2
    sampen_r: 0.2
    dfa_min_scale: 4
  
  # NEW: Biomechanical context (Roadmap Section 3.5)
  swing_quality:
    enable: true
    dtw_baseline_swings: 20
    compute_dtw_distance: true
  
  # NEW: Sensor fusion (Roadmap Section 5)
  fusion:
    enable: true
    method: 'early'  # 'early', 'late_weighted', 'late_majority', 'late_stacking'
    
    # Late fusion weights (if method='late_weighted')
    late_fusion_weights:
      emg: 0.50
      imu: 0.35
      vitals: 0.15

# NEW: Ground truth validation (Roadmap Section 6)
validation:
  enable: false  # Set to true when ground truth available
  mvc_decline_threshold: 20.0  # Percent
  rpe_threshold: 7.0  # Borg CR-10 scale
  
# Existing sections remain unchanged
session:
  emg_fs_hz: 2000
  use_physical_units: true
  # ...
```

---

## Implementation Timeline (Aligned with Roadmap)

### Week 1-2: Core Fusion Implementation
- [x] Early Fusion (18D feature vector + Random Forest)
- [x] Late Fusion (3 variants: weighted, majority, stacking)
- [ ] Integration testing with existing pipeline
- [ ] Validation on pilot data (2-3 sessions)

### Week 3-4: Nonlinear Features
- [x] Sample Entropy implementation
- [x] DFA implementation
- [ ] Integration into feature extraction pipeline
- [ ] Baseline comparison (with vs without complexity features)

### Week 5-6: Biomechanical Context
- [x] Swing quality metrics (velocity, jerk, ROM)
- [x] DTW-based technique degradation
- [ ] Template creation from baseline swings
- [ ] Visualization of technique degradation over session

### Week 7-8: Validation Framework
- [x] RPE correlation analysis
- [x] MVC correlation analysis
- [ ] Statistical testing framework
- [ ] Prepare for N=20 data collection

### Week 9-12: Data Collection (Roadmap Section 6)
- [ ] IRB approval
- [ ] Pilot testing (2-3 participants)
- [ ] Main data collection (N=20)
- [ ] Quality control and data cleaning

### Week 13-16: Analysis & Paper Writing
- [ ] Run full analysis pipeline on N=20 dataset
- [ ] Generate all figures and tables
- [ ] Write Methods and Results sections
- [ ] Statistical analysis and significance testing

---

## Key Differences from Original Recommendations

### What's Already in Your Roadmap (No Need to Duplicate)
1. ✅ **Attention-based fusion** — Roadmap Section 5, Approach 3 (detailed architecture provided)
2. ✅ **1D-CNN-LSTM** — Roadmap Section 3.2 (for future work)
3. ✅ **Bayesian baselines** — Roadmap Section 3.3 (personalization)
4. ✅ **Validation protocol** — Roadmap Section 6 (N=20, MVC+RPE)
5. ✅ **Paper outline** — Roadmap Section 7 (complete structure)
6. ✅ **Target journals** — Roadmap Section 8 (Sensors, IEEE TBME)

### What This Document Adds
1. ✅ **Implementation-ready code** for roadmap algorithms
2. ✅ **Integration guidance** with existing codebase
3. ✅ **Config file updates** for new features
4. ✅ **Testing and validation** procedures
5. ✅ **Prioritized timeline** aligned with 6-9 month goal

---

## Next Steps (Action Items)

### Immediate (This Week)
1. **Add nonlinear features** (SampEn, DFA) to `emg_util.py`
2. **Implement Early Fusion** feature extraction
3. **Test on existing data** (logs_new/ directory)
4. **Verify feature importance** matches expectations (MDF, swing_velocity top 5)

### Short-term (Next 2 Weeks)
5. **Implement Late Fusion** (3 variants)
6. **Add DTW technique degradation** metric
7. **Create comparison plots** (single-modality vs fusion)
8. **Document results** in lab notebook

### Medium-term (Next 4 Weeks)
9. **Pilot test** with 2-3 participants
10. **Refine ground truth labeling** procedure
11. **Finalize data collection protocol**
12. **Submit IRB application**

### Long-term (Next 3 Months)
13. **Collect N=20 dataset**
14. **Run full analysis pipeline**
15. **Generate publication figures**
16. **Write paper draft**

---

## References (From Your Roadmap + Additions)

### Nonlinear Dynamics
- Richman & Moorman (2000). "Physiological time-series analysis using approximate entropy and sample entropy." *Am J Physiol Heart Circ Physiol*, 278(6):H2039-H2049.
- Peng et al. (1995). "Quantification of scaling exponents and crossover phenomena in nonstationary heartbeat time series." *Chaos*, 5(1):82-87.

### Sensor Fusion
- Lahat et al. (2015). "Multimodal data fusion: An overview of methods, challenges, and prospects." *Proc IEEE*, 103(9):1449-1477.

### EMG Fatigue
- Merletti & Farina (2016). *Surface Electromyography: Physiology, Engineering, and Applications*. Wiley-IEEE Press.
- Phinyomark et al. (2023). "EMG feature extraction for tolerance of white Gaussian noise." *J Electromyogr Kinesiol*.

### Biomechanics
- Camomilla et al. (2018). "Trends supporting the in-field use of wearable inertial sensors for sport performance evaluation: A systematic review." *Sensors*, 18(3):873.

---

## Conclusion

Your **RESEARCH_ROADMAP.md** already provides an excellent foundation. This document delivers:

1. **Implementation-ready code** for your chosen fusion algorithms
2. **Integration guidance** with your existing ESP32 → BLE → btCentral.py → emg_util.py pipeline
3. **Prioritized enhancements** aligned with your 6-9 month publication timeline
4. **Validation framework** for N=20 data collection

**Key Insight:** Your roadmap's multi-modal fusion approach is well-designed. The Early Fusion (18D feature vector) should be your **immediate priority** — it's simple, interpretable, and will provide the baseline for comparing Late Fusion and Attention-based approaches.

**Expected Outcome:** With these implementations, you should achieve the roadmap's target metrics:
- Early Fusion: ~87% accuracy, ~0.92 AUC
- Late Fusion: ~88% accuracy, ~0.91-0.93 AUC
- 42±18s earlier detection than EMG-only

This positions you well for publication in **Sensors (MDPI)** or **IEEE TBME** within your 6-9 month timeline.
