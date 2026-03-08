#!/usr/bin/env python3
"""
Motion Artifact Analysis Tool

Tests for motion artifact in EMG data using three methods:
1. EMG-IMU coherence (correlation between low-freq EMG and IMU acceleration)
2. MDF stability with/without impact windows
3. Stationarity check (coefficient of variation in swing windows)

Usage:
    python motion_artifact_analysis.py --log-dir C:\wangx\ftc\emg_util\log0305
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy import signal
from scipy.stats import pearsonr

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import capture_loader
import emg_util


def compute_low_freq_envelope(emg_raw: np.ndarray, fs: float, cutoff_hz: float = 20.0) -> np.ndarray:
    """Compute low-frequency envelope (<20 Hz) to capture motion artifact."""
    # Rectify
    rect = np.abs(emg_raw)
    
    # Low-pass filter at cutoff_hz
    nyq = fs / 2.0
    b, a = signal.butter(2, cutoff_hz / nyq, btype='low')
    env_lf = signal.filtfilt(b, a, rect)
    
    return env_lf


def test_emg_imu_coherence(
    emg_df,
    imu_df,
    emg_fs: float = 2000.0,
    imu_fs: float = 200.0,
) -> Dict:
    """Test 1: EMG-IMU coherence.
    
    High correlation between low-freq EMG envelope and IMU acceleration
    magnitude indicates motion artifact.
    
    Returns:
        dict with correlation coefficient and interpretation
    """
    print("\n" + "="*70)
    print("TEST 1: EMG-IMU Coherence (Motion Artifact Detection)")
    print("="*70)
    
    # Get EMG raw signal
    emg_raw = emg_df['raw'].values
    emg_ts_ms = emg_df['ts_ms'].values
    
    # Compute low-frequency envelope (<20 Hz)
    env_lf = compute_low_freq_envelope(emg_raw, emg_fs, cutoff_hz=20.0)
    
    # Get IMU acceleration magnitude (physical units: g)
    ax = imu_df['ax'].values
    ay = imu_df['ay'].values
    az = imu_df['az'].values
    imu_ts_ms = imu_df['ts_ms'].values
    
    # Convert to g (FSR=4g → 8192 LSB/g)
    acc_mag_g = np.sqrt(ax**2 + ay**2 + az**2) / 8192.0
    
    # Resample EMG envelope to IMU rate for comparison
    # Use simple decimation (take every Nth sample)
    decim_factor = int(emg_fs / imu_fs)
    env_lf_decimated = env_lf[::decim_factor]
    
    # Align lengths
    min_len = min(len(env_lf_decimated), len(acc_mag_g))
    env_lf_decimated = env_lf_decimated[:min_len]
    acc_mag_g = acc_mag_g[:min_len]
    
    # Compute correlation
    corr, p_value = pearsonr(env_lf_decimated, acc_mag_g)
    
    print(f"\nLow-frequency EMG envelope (<20 Hz) vs IMU acceleration magnitude:")
    print(f"  Correlation coefficient: {corr:.3f}")
    print(f"  P-value: {p_value:.2e}")
    
    # Interpretation
    if abs(corr) > 0.7:
        interpretation = "STRONG motion artifact detected"
        severity = "HIGH"
    elif abs(corr) > 0.5:
        interpretation = "MODERATE motion artifact detected"
        severity = "MODERATE"
    elif abs(corr) > 0.3:
        interpretation = "MILD motion artifact detected"
        severity = "MILD"
    else:
        interpretation = "No significant motion artifact"
        severity = "LOW"
    
    print(f"\n  Interpretation: {interpretation}")
    print(f"  Severity: {severity}")
    
    return {
        "correlation": float(corr),
        "p_value": float(p_value),
        "interpretation": interpretation,
        "severity": severity,
    }


def test_mdf_impact_gating(
    emg_df,
    imu_df,
    swing_windows: List[Dict],
    emg_fs: float = 2000.0,
    impact_window_ms: float = 50.0,
) -> Dict:
    """Test 2: MDF stability with/without impact windows.
    
    If MDF stabilizes or drops when excluding ±50ms around impact,
    this confirms motion artifact contamination.
    
    Returns:
        dict with MDF statistics and interpretation
    """
    print("\n" + "="*70)
    print("TEST 2: MDF Stability with Impact Gating")
    print("="*70)
    
    # Preprocess EMG
    emg_raw = emg_df['raw'].values
    emg_ts_ms = emg_df['ts_ms'].values
    emg_proc = emg_util.preprocess_emg(emg_raw, emg_fs)
    
    # Compute MDF for each swing with and without impact window
    mdf_full = []
    mdf_gated = []
    
    for swing in swing_windows:
        t_peak = swing['t_peak_ms']
        t_start = swing['t_start_ms']
        t_end = swing['t_end_ms']
        
        # Full swing window
        i0 = int(np.searchsorted(emg_ts_ms, t_start))
        i1 = int(np.searchsorted(emg_ts_ms, t_end))
        seg_full = emg_proc[i0:i1]
        
        # Gated window (exclude ±impact_window_ms around peak)
        t_gate_start = t_peak - impact_window_ms
        t_gate_end = t_peak + impact_window_ms
        
        # Get segments before and after impact
        i_gate_start = int(np.searchsorted(emg_ts_ms, t_gate_start))
        i_gate_end = int(np.searchsorted(emg_ts_ms, t_gate_end))
        
        seg_before = emg_proc[i0:i_gate_start]
        seg_after = emg_proc[i_gate_end:i1]
        seg_gated = np.concatenate([seg_before, seg_after]) if seg_before.size and seg_after.size else seg_before if seg_before.size else seg_after
        
        # Compute MDF
        if seg_full.size >= 256:
            _, mdf_f = emg_util.mnf_mdf(seg_full, emg_fs)
            mdf_full.append(mdf_f)
        
        if seg_gated.size >= 256:
            _, mdf_g = emg_util.mnf_mdf(seg_gated, emg_fs)
            mdf_gated.append(mdf_g)
    
    mdf_full = np.array([m for m in mdf_full if np.isfinite(m)])
    mdf_gated = np.array([m for m in mdf_gated if np.isfinite(m)])
    
    print(f"\nMDF statistics (N={len(mdf_full)} swings):")
    print(f"  Full swing windows:")
    print(f"    Mean: {np.mean(mdf_full):.1f} Hz")
    print(f"    Std:  {np.std(mdf_full):.1f} Hz")
    print(f"    CV:   {np.std(mdf_full)/np.mean(mdf_full)*100:.1f}%")
    
    print(f"\n  Impact-gated windows (±{impact_window_ms}ms excluded):")
    print(f"    Mean: {np.mean(mdf_gated):.1f} Hz")
    print(f"    Std:  {np.std(mdf_gated):.1f} Hz")
    print(f"    CV:   {np.std(mdf_gated)/np.mean(mdf_gated)*100:.1f}%")
    
    # Compare
    mdf_change_pct = (np.mean(mdf_gated) - np.mean(mdf_full)) / np.mean(mdf_full) * 100
    cv_change_pct = (np.std(mdf_gated)/np.mean(mdf_gated) - np.std(mdf_full)/np.mean(mdf_full)) * 100
    
    print(f"\n  Change with gating:")
    print(f"    MDF mean change: {mdf_change_pct:+.1f}%")
    print(f"    CV change: {cv_change_pct:+.1f} percentage points")
    
    # Interpretation
    if mdf_change_pct < -5 or cv_change_pct < -5:
        interpretation = "MDF DROPS or stabilizes with gating → Motion artifact CONFIRMED"
        artifact_confirmed = True
    elif abs(mdf_change_pct) < 2 and abs(cv_change_pct) < 2:
        interpretation = "No significant change → Artifact minimal or absent"
        artifact_confirmed = False
    else:
        interpretation = "Inconclusive (MDF increases with gating)"
        artifact_confirmed = False
    
    print(f"\n  Interpretation: {interpretation}")
    
    return {
        "mdf_full_mean": float(np.mean(mdf_full)),
        "mdf_full_std": float(np.std(mdf_full)),
        "mdf_full_cv": float(np.std(mdf_full)/np.mean(mdf_full)*100),
        "mdf_gated_mean": float(np.mean(mdf_gated)),
        "mdf_gated_std": float(np.std(mdf_gated)),
        "mdf_gated_cv": float(np.std(mdf_gated)/np.mean(mdf_gated)*100),
        "mdf_change_pct": float(mdf_change_pct),
        "cv_change_pct": float(cv_change_pct),
        "interpretation": interpretation,
        "artifact_confirmed": artifact_confirmed,
    }


def test_stationarity(
    emg_df,
    swing_windows: List[Dict],
    emg_fs: float = 2000.0,
) -> Dict:
    """Test 3: Stationarity check.
    
    EMG fatigue metrics require quasi-stationary windows.
    Tennis swings are highly non-stationary.
    High coefficient of variation indicates non-stationarity.
    
    Returns:
        dict with stationarity metrics
    """
    print("\n" + "="*70)
    print("TEST 3: Stationarity Check")
    print("="*70)
    
    emg_raw = emg_df['raw'].values
    emg_ts_ms = emg_df['ts_ms'].values
    emg_proc = emg_util.preprocess_emg(emg_raw, emg_fs)
    
    # Compute RMS in sliding windows within each swing
    rms_cvs = []
    
    for swing in swing_windows:
        t_start = swing['t_start_ms']
        t_end = swing['t_end_ms']
        
        i0 = int(np.searchsorted(emg_ts_ms, t_start))
        i1 = int(np.searchsorted(emg_ts_ms, t_end))
        seg = emg_proc[i0:i1]
        
        if seg.size < 500:  # Need at least 250ms at 2000 Hz
            continue
        
        # Compute RMS in 50ms sliding windows
        win_size = int(0.05 * emg_fs)  # 50ms
        step_size = int(0.01 * emg_fs)  # 10ms step
        
        rms_values = []
        for j in range(0, len(seg) - win_size, step_size):
            win = seg[j:j+win_size]
            rms_values.append(np.sqrt(np.mean(win**2)))
        
        if len(rms_values) >= 3:
            cv = np.std(rms_values) / np.mean(rms_values) * 100
            rms_cvs.append(cv)
    
    rms_cvs = np.array(rms_cvs)
    
    print(f"\nWithin-swing RMS variability (N={len(rms_cvs)} swings):")
    print(f"  Mean CV: {np.mean(rms_cvs):.1f}%")
    print(f"  Median CV: {np.median(rms_cvs):.1f}%")
    print(f"  Range: {np.min(rms_cvs):.1f}% - {np.max(rms_cvs):.1f}%")
    
    # Interpretation
    mean_cv = np.mean(rms_cvs)
    if mean_cv > 50:
        interpretation = "HIGHLY non-stationary → MDF mathematically unstable"
        stationarity = "POOR"
    elif mean_cv > 30:
        interpretation = "MODERATELY non-stationary → MDF reliability questionable"
        stationarity = "FAIR"
    elif mean_cv > 15:
        interpretation = "MILDLY non-stationary → MDF usable with caution"
        stationarity = "GOOD"
    else:
        interpretation = "Quasi-stationary → MDF assumptions satisfied"
        stationarity = "EXCELLENT"
    
    print(f"\n  Interpretation: {interpretation}")
    print(f"  Stationarity: {stationarity}")
    
    return {
        "mean_cv": float(mean_cv),
        "median_cv": float(np.median(rms_cvs)),
        "min_cv": float(np.min(rms_cvs)),
        "max_cv": float(np.max(rms_cvs)),
        "interpretation": interpretation,
        "stationarity": stationarity,
    }


def main():
    parser = argparse.ArgumentParser(description="Motion artifact analysis tool")
    parser.add_argument("--log-dir", required=True, help="Directory containing EMG/IMU logs")
    parser.add_argument("--emg-fs", type=float, default=2000.0, help="EMG sampling rate (Hz)")
    parser.add_argument("--imu-fs", type=float, default=200.0, help="IMU sampling rate (Hz)")
    parser.add_argument("--impact-window-ms", type=float, default=50.0, help="Impact exclusion window (ms)")
    parser.add_argument("--output", help="Output JSON file for results")
    
    args = parser.parse_args()
    
    log_dir = Path(args.log_dir)
    if not log_dir.exists():
        print(f"Error: Log directory not found: {log_dir}")
        return 1
    
    print("="*70)
    print("MOTION ARTIFACT ANALYSIS")
    print("="*70)
    print(f"\nLog directory: {log_dir}")
    
    # Load session data
    print("\nLoading session data...")
    sessions = capture_loader.discover_sessions(str(log_dir))
    if not sessions:
        print("Error: No sessions found")
        return 1
    
    print(f"Found {len(sessions)} session(s)")
    
    # Load stitched data
    emg_df, imu_df, reconnection_times, capture_ids = capture_loader.load_session_stitched(sessions)
    
    print(f"  EMG samples: {len(emg_df)}")
    print(f"  IMU samples: {len(imu_df)}")
    print(f"  Duration: {(emg_df['ts_ms'].iloc[-1] - emg_df['ts_ms'].iloc[0])/1000:.1f} seconds")
    
    # Detect swings
    print("\nDetecting swings...")
    swing_windows_df = emg_util.detect_swing_windows_from_imu(
        imu_df,
        thr_gyro_dps=300.0,
        thr_acc_g=0.0,
        min_gap_ms=2000.0,
    )
    swing_windows = swing_windows_df.to_dict('records')
    print(f"  Detected {len(swing_windows)} swings")
    
    # Run tests
    results = {}
    
    # Test 1: EMG-IMU coherence
    results['test1_coherence'] = test_emg_imu_coherence(emg_df, imu_df, args.emg_fs, args.imu_fs)
    
    # Test 2: MDF impact gating
    results['test2_mdf_gating'] = test_mdf_impact_gating(
        emg_df, imu_df, swing_windows, args.emg_fs, args.impact_window_ms
    )
    
    # Test 3: Stationarity
    results['test3_stationarity'] = test_stationarity(emg_df, swing_windows, args.emg_fs)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    print("\n1. EMG-IMU Coherence:")
    print(f"   Correlation: {results['test1_coherence']['correlation']:.3f}")
    print(f"   Severity: {results['test1_coherence']['severity']}")
    
    print("\n2. MDF Impact Gating:")
    print(f"   MDF change: {results['test2_mdf_gating']['mdf_change_pct']:+.1f}%")
    print(f"   Artifact confirmed: {results['test2_mdf_gating']['artifact_confirmed']}")
    
    print("\n3. Stationarity:")
    print(f"   Mean CV: {results['test3_stationarity']['mean_cv']:.1f}%")
    print(f"   Stationarity: {results['test3_stationarity']['stationarity']}")
    
    # Overall conclusion
    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    
    artifact_score = 0
    if results['test1_coherence']['severity'] in ['HIGH', 'MODERATE']:
        artifact_score += 2
    elif results['test1_coherence']['severity'] == 'MILD':
        artifact_score += 1
    
    if results['test2_mdf_gating']['artifact_confirmed']:
        artifact_score += 2
    
    if results['test3_stationarity']['stationarity'] in ['POOR', 'FAIR']:
        artifact_score += 1
    
    if artifact_score >= 4:
        conclusion = "STRONG evidence of motion artifact contamination"
    elif artifact_score >= 2:
        conclusion = "MODERATE evidence of motion artifact"
    else:
        conclusion = "MINIMAL motion artifact detected"
    
    print(f"\n{conclusion}")
    print(f"Artifact score: {artifact_score}/5")
    
    # Recommendations
    print("\nRECOMMENDATIONS:")
    if artifact_score >= 2:
        print("  ✓ Use IMU-gated EMG windows (exclude ±50ms around impact)")
        print("  ✓ Focus on post-impact isometric segments")
        print("  ✓ Use fatigue features more robust than MDF (e.g., RMS, ENV mean)")
        print("  ✓ Consider multi-session trend modeling instead of per-swing MDF")
    else:
        print("  ✓ Current MDF analysis is likely valid")
        print("  ✓ Motion artifact is minimal")
    
    # Save results
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
