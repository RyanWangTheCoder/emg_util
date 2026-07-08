# -*- coding: utf-8 -*-
"""
imu_baseline.py

Shared IMU baseline detector for swing threshold estimation.

Used by all three swing detectors to derive a consistent threshold_dps
from the full session's gyro magnitude, rather than relying on a fixed
magic number or a potentially-corrupted short time window.

Algorithm
---------
Tennis sessions are typically 80-90% rest (between points, walking,
waiting) and only 10-20% active swings. The p10 percentile of the full
session's gyro magnitude therefore reliably lands in the rest distribution,
not in the swing distribution.

From that rest floor we compute:
    rest_median = median of samples below REST_SAMPLE_PERCENTILE
    rest_mad    = MAD of those same samples
    threshold   = rest_median + N_SIGMA * 1.4826 * rest_mad

This is the same MAD-based formula used in robust_zscore() -- just with a
correct, session-wide rest baseline instead of a fixed time window.

Fallback
--------
If the session is too short (<MIN_SESSION_S seconds) or the detected
rest floor is implausibly high (>MAX_REST_MEDIAN_DPS), the class falls
back to FALLBACK_DPS (300 dps) -- the same value used as the hardcoded
default in ThresholdSwingDetector and HysteresisSwingDetector.

Usage
-----
    from imu_baseline import ImuBaseline

    bl = ImuBaseline(gmag_dps)          # full session array in dps
    print(bl.threshold_dps)             # use this as detector threshold
    print(bl.used_fallback)             # True if session too short/noisy

    # HysteresisSwingDetector: th_on = bl.th_on, th_off = bl.th_off
    # ThresholdSwingDetector:  thr_gyro_dps = bl.threshold_dps
    # emg_util z-score:        z_thr derived from same threshold

Android / no-pandas compatibility
----------------------------------
This file has zero dependencies beyond numpy. It can be copied to the
Android emg_util_nopandas directory unchanged.
"""

from __future__ import annotations
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Percentile used to identify the rest floor of the session.
# p10 is safely below swing peaks for sessions where swings are <20% of time.
REST_PERCENTILE = 10.0

# Samples at or below this percentile are used to compute rest median + MAD.
# Slightly wider than REST_PERCENTILE for stable statistics.
REST_SAMPLE_PERCENTILE = 25.0

# Number of MAD-sigmas above rest median to set the threshold.
# N=5 matches the default z_thr=5 in emg_util's robust_zscore.
N_SIGMA = 5.0

# If the detected rest median exceeds this value the session is unusually
# active and we fall back to the default.
MAX_REST_MEDIAN_DPS = 200.0

# Minimum session duration to attempt adaptive baseline detection.
MIN_SESSION_S = 30.0

# Fallback threshold -- consistent with ThresholdSwingDetector and
# HysteresisSwingDetector hardcoded defaults.
FALLBACK_DPS = 300.0


# ---------------------------------------------------------------------------
# ImuBaseline
# ---------------------------------------------------------------------------

class ImuBaseline:
    """Detect the rest baseline from a full IMU session and derive a swing threshold.

    Parameters
    ----------
    gmag_dps : array-like
        Gyro magnitude in degrees-per-second for the full session.
        Must already be converted from raw LSB to physical units.
    imu_fs_hz : float, optional
        IMU sample rate in Hz. Used only to estimate session duration.
        Default 200 Hz (standard firmware setting).
    fallback_dps : float, optional
        Threshold to use when adaptive detection fails. Default 300 dps.

    Attributes
    ----------
    threshold_dps : float
        Recommended swing detection threshold in dps.
        Use as thr_gyro_dps (ThresholdSwingDetector) or th_on
        (HysteresisSwingDetector). th_off = threshold_dps / 2.
    rest_median_dps : float
        Median gyro magnitude of the detected rest samples (dps).
    rest_mad_dps : float
        MAD of the rest samples (dps).
    used_fallback : bool
        True if adaptive detection failed and fallback_dps was used.
    fallback_reason : str
        Human-readable reason why fallback was used (empty if not used).
    p10_dps : float
        Raw p10 percentile of the full session (dps). Diagnostic only.
    """

    def __init__(self,
                 gmag_dps,
                 imu_fs_hz: float = 200.0,
                 fallback_dps: float = FALLBACK_DPS):

        self.fallback_dps    = float(fallback_dps)
        self.used_fallback   = False
        self.fallback_reason = ''

        gmag = np.asarray(gmag_dps, dtype=float)
        gmag = gmag[np.isfinite(gmag)]

        # guard: too few samples / session too short
        session_s = len(gmag) / float(imu_fs_hz)
        if len(gmag) < 10 or session_s < MIN_SESSION_S:
            self._apply_fallback(
                f'session too short ({session_s:.1f}s < {MIN_SESSION_S}s)')
            return

        # find rest floor via low percentile
        p10_val        = float(np.percentile(gmag, REST_PERCENTILE))
        rest_threshold = float(np.percentile(gmag, REST_SAMPLE_PERCENTILE))
        rest_samples   = gmag[gmag <= rest_threshold]

        if len(rest_samples) < 10:
            self._apply_fallback('not enough rest samples found')
            return

        rest_median = float(np.median(rest_samples))
        rest_mad    = float(np.median(np.abs(rest_samples - rest_median)))

        # guard: rest median implausibly high (unusually dense session)
        if rest_median > MAX_REST_MEDIAN_DPS:
            self._apply_fallback(
                f'rest median too high ({rest_median:.1f} dps > {MAX_REST_MEDIAN_DPS} dps)')
            return

        # guard: MAD too small (degenerate / constant signal)
        scale = 1.4826 * rest_mad
        if scale < 1.0:
            scale = float(np.std(rest_samples))
        if scale < 1.0:
            self._apply_fallback('rest MAD near zero -- degenerate signal')
            return

        threshold = rest_median + N_SIGMA * scale

        # guard: computed threshold out of plausible range
        if threshold < 100.0:
            self._apply_fallback(
                f'computed threshold too low ({threshold:.1f} dps < 100 dps)')
            return
        if threshold > 800.0:
            self._apply_fallback(
                f'computed threshold too high ({threshold:.1f} dps > 800 dps)')
            return

        self.rest_median_dps = rest_median
        self.rest_mad_dps    = rest_mad
        self.threshold_dps   = threshold
        self.p10_dps         = p10_val

    # ------------------------------------------------------------------
    def _apply_fallback(self, reason: str) -> None:
        self.used_fallback   = True
        self.fallback_reason = reason
        self.threshold_dps   = self.fallback_dps
        self.rest_median_dps = float('nan')
        self.rest_mad_dps    = float('nan')
        self.p10_dps         = float('nan')

    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        if self.used_fallback:
            return (f'ImuBaseline(threshold={self.threshold_dps:.1f} dps '
                    f'[FALLBACK: {self.fallback_reason}])')
        return (f'ImuBaseline(threshold={self.threshold_dps:.1f} dps | '
                f'rest_median={self.rest_median_dps:.1f} dps, '
                f'rest_MAD={self.rest_mad_dps:.1f} dps, '
                f'p10={self.p10_dps:.1f} dps)')

    # ------------------------------------------------------------------
    @property
    def th_on(self) -> float:
        """Entry threshold for HysteresisSwingDetector (= threshold_dps)."""
        return self.threshold_dps

    @property
    def th_off(self) -> float:
        """Exit threshold for HysteresisSwingDetector (= threshold_dps / 2)."""
        return self.threshold_dps / 2.0

    # ------------------------------------------------------------------
    @staticmethod
    def lsb_to_dps(gmag_lsb, gyro_fsr_dps: int) -> np.ndarray:
        """Convert raw gyro magnitude LSB to dps.

        Convenience method so callers don't need to know the LSB map.

        Parameters
        ----------
        gmag_lsb : array-like
            Gyro magnitude in raw LSB units.
        gyro_fsr_dps : int
            Gyro full-scale range in dps (250, 500, 1000, or 2000).
        """
        lsb_map = {250: 131.0, 500: 65.5, 1000: 32.8, 2000: 16.4}
        lsb_per_dps = lsb_map.get(int(gyro_fsr_dps), 32.8)
        return np.asarray(gmag_lsb, dtype=float) / lsb_per_dps
