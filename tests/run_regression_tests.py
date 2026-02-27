#!/usr/bin/env python3
"""
Regression Test Runner

Runs regression tests and generates a detailed report.

Usage:
    python tests/run_regression_tests.py
    python tests/run_regression_tests.py --verbose
    python tests/run_regression_tests.py --generate-baseline
"""

import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print colored header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def run_tests(verbose=False):
    """Run pytest regression tests."""
    print_header("Running Regression Tests")
    
    # Build pytest command
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_regression.py",
        "-v" if verbose else "-q",
        "--tb=short",
        "--color=yes",
        "-ra",  # Show summary of all test outcomes
    ]
    
    print_info(f"Command: {' '.join(cmd)}")
    print()
    
    # Run tests
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    elapsed_time = time.time() - start_time
    
    print()
    print_info(f"Tests completed in {elapsed_time:.2f} seconds")
    
    return result.returncode == 0


def generate_baseline():
    """Generate baseline values for regression tests."""
    print_header("Generating Regression Baseline")
    
    print_info("Running analysis on regression data...")
    
    # Import required modules
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import emg_util as core
    import capture_loader as loader
    import numpy as np
    
    # Load regression data
    data_dir = Path(__file__).parent.parent / "regression_testlogs"
    
    if not data_dir.exists():
        print_error(f"Regression data not found: {data_dir}")
        return False
    
    try:
        # Load session
        print_info("Loading EMG data...")
        emg_df, emg_meta = loader.load_session_emg(str(data_dir))
        
        print_info("Loading IMU data...")
        imu_df, imu_meta = loader.load_session_imu(str(data_dir))
        
        # Detect swings
        print_info("Detecting swings...")
        swings = core.detect_swing_windows_from_imu(imu_df, fs_imu=imu_meta["fs_hz"])
        
        # Compute MDF samples
        print_info("Computing MDF samples...")
        mdf_values = []
        for i in range(0, min(len(emg_df) - 2600, 50000), 5000):
            raw = emg_df["emg_raw"].values[i:i+2600]
            if len(raw) < 2600:
                continue
            from fatigue_monitor import preprocess_emg
            processed = preprocess_emg(raw, fs=2000)
            _, mdf = core.mnf_mdf(processed, fs=2000)
            mdf_values.append(mdf)
        
        # Generate baseline
        baseline = {
            "generated_at": datetime.now().isoformat(),
            "data_dir": str(data_dir),
            "emg_samples": len(emg_df),
            "imu_samples": len(imu_df),
            "num_swings": len(swings),
            "mdf_mean": float(np.mean(mdf_values)),
            "mdf_std": float(np.std(mdf_values)),
            "mdf_min": float(np.min(mdf_values)),
            "mdf_max": float(np.max(mdf_values)),
        }
        
        # Save baseline
        baseline_file = Path(__file__).parent / "regression_baseline.json"
        with open(baseline_file, 'w') as f:
            json.dump(baseline, f, indent=2)
        
        print_success(f"Baseline saved to: {baseline_file}")
        print()
        print("Baseline values:")
        for key, value in baseline.items():
            if key != "generated_at":
                print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to generate baseline: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print_header("Checking Dependencies")
    
    required = ["pytest", "numpy", "pandas", "scipy"]
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print_success(f"{package} installed")
        except ImportError:
            print_error(f"{package} NOT installed")
            missing.append(package)
    
    if missing:
        print()
        print_warning("Missing dependencies. Install with:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run regression tests")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--generate-baseline", "-g", action="store_true",
                       help="Generate baseline values")
    parser.add_argument("--skip-deps-check", action="store_true",
                       help="Skip dependency check")
    
    args = parser.parse_args()
    
    # Check dependencies
    if not args.skip_deps_check:
        if not check_dependencies():
            return 1
    
    # Generate baseline if requested
    if args.generate_baseline:
        success = generate_baseline()
        return 0 if success else 1
    
    # Run tests
    success = run_tests(verbose=args.verbose)
    
    if success:
        print()
        print_success("All regression tests passed! ✓")
        return 0
    else:
        print()
        print_error("Some regression tests failed! ✗")
        print_info("Review the output above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
