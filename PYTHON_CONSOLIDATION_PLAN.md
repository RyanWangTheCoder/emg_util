# Python Script Consolidation & Android Integration Plan

**Created:** 2026-02-27  
**Status:** Proposed  
**Priority:** High

---

## Current Situation

### Scattered Python Scripts

Currently, Python scripts are scattered across multiple locations:

```
ftc/
├── emg_util/                          # Core analysis library
│   ├── emg_util.py                    # Signal processing
│   ├── fatigue_monitor.py             # Fatigue tracking
│   ├── capture_loader.py              # Data loading
│   └── emg_util_yaml_runner.py        # Pipeline runner
│
├── arduino/py_scripts/                # Desktop tools
│   ├── sensordata_plotter.py          # Real-time plotter
│   ├── btCentral.py                   # BLE central
│   └── ble_find_uuid.py               # BLE utilities
│
└── btLeApp/app/src/main/python/       # Android-embedded scripts
    ├── emg_processor.py               # EMG processing (duplicate?)
    ├── swing_detector.py              # Swing detection (duplicate?)
    └── fatigue_analyzer.py            # Fatigue analysis (duplicate?)
```

### Problems

1. **Code Duplication** - Same algorithms implemented multiple times
2. **Inconsistent Behavior** - Different versions may have bugs/fixes
3. **Maintenance Burden** - Changes must be replicated across locations
4. **Testing Gaps** - Android scripts not covered by regression tests
5. **Version Drift** - Scripts diverge over time

---

## Proposed Solution: Git Submodules

### Architecture

```
ftc/
├── emg_util/                          # Main repository (submodule)
│   ├── emg_util.py                    # Core library
│   ├── fatigue_monitor.py
│   ├── capture_loader.py
│   ├── tests/
│   │   ├── test_regression.py         # Regression tests
│   │   └── test_android_compat.py     # Android compatibility tests
│   └── android_bridge/                # NEW: Android integration layer
│       ├── __init__.py
│       ├── emg_processor.py           # Thin wrapper for Android
│       ├── swing_detector.py          # Thin wrapper for Android
│       └── fatigue_analyzer.py        # Thin wrapper for Android
│
├── arduino/                           # Arduino repository
│   └── py_scripts/                    # Desktop tools (reference emg_util)
│       ├── sensordata_plotter.py      # Uses emg_util as dependency
│       └── btCentral.py
│
└── btLeApp/                           # Android repository
    └── app/src/main/python/           # Git submodule → emg_util
        └── emg_util/                  # Submodule link
            ├── emg_util.py            # Same code as main repo
            ├── fatigue_monitor.py
            └── android_bridge/        # Android-specific wrappers
```

### Benefits

✅ **Single Source of Truth** - One codebase, multiple consumers  
✅ **Automatic Updates** - `git submodule update` pulls latest  
✅ **Version Control** - Pin to specific commits for stability  
✅ **Unified Testing** - All code tested in one place  
✅ **Easier Maintenance** - Fix once, deploy everywhere  

---

## Implementation Plan

### Phase 1: Consolidate Core Library (Week 1)

**Goal:** Move all core algorithms to `emg_util/`

**Tasks:**
1. ✅ Create regression test suite (DONE)
2. Audit Android scripts for unique functionality
3. Move unique code to `emg_util/android_bridge/`
4. Create thin wrappers for Android compatibility
5. Add Android compatibility tests

**Deliverables:**
- `emg_util/android_bridge/` module
- `tests/test_android_compat.py`
- Migration guide document

### Phase 2: Setup Git Submodules (Week 2)

**Goal:** Configure submodules in consuming repositories

**Tasks:**
1. Initialize `emg_util` as standalone git repository
2. Add submodule to `btLeApp`:
   ```bash
   cd btLeApp/app/src/main/python
   git submodule add <emg_util_repo_url> emg_util
   ```
3. Update Android build scripts to include submodule
4. Update `arduino/py_scripts` to use emg_util as dependency
5. Test all integrations

**Deliverables:**
- `.gitmodules` configuration
- Updated build scripts
- Integration test results

### Phase 3: Migrate Android App (Week 3)

**Goal:** Switch Android app to use submodule

**Tasks:**
1. Update Android Python imports:
   ```python
   # Old
   from emg_processor import process_emg
   
   # New
   from emg_util.android_bridge import process_emg
   ```
2. Update Chaquopy configuration
3. Run Android regression tests
4. Performance testing on device
5. Remove old duplicate scripts

**Deliverables:**
- Updated Android app using submodule
- Performance benchmarks
- Migration complete

### Phase 4: Continuous Integration (Week 4)

**Goal:** Automate testing across all platforms

**Tasks:**
1. Setup GitHub Actions for `emg_util`
2. Add Android compatibility tests to CI
3. Add desktop tool tests to CI
4. Setup automatic submodule updates
5. Document CI/CD workflow

**Deliverables:**
- `.github/workflows/` configurations
- CI/CD documentation
- Automated test reports

---

## Android Compatibility Testing

### New Test Suite: `tests/test_android_compat.py`

```python
"""
Android Compatibility Tests

Ensures emg_util works correctly in Android/Chaquopy environment.
Tests memory usage, performance, and API compatibility.
"""

import pytest
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import emg_util as core
import fatigue_monitor as fm


class TestAndroidCompatibility:
    """Test Android-specific requirements."""
    
    def test_memory_efficient_processing(self):
        """Test that processing doesn't use excessive memory."""
        # Android devices have limited memory
        signal = np.random.randn(10000)  # 5 seconds @ 2000 Hz
        
        import tracemalloc
        tracemalloc.start()
        
        # Process signal
        processed = fm.preprocess_emg(signal, fs=2000)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Should use < 10 MB for 5 seconds of data
        assert peak < 10 * 1024 * 1024, f"Memory usage {peak/1024/1024:.1f} MB too high"
    
    def test_real_time_performance(self):
        """Test that processing is fast enough for real-time."""
        import time
        
        # Simulate real-time: 1.3 second window @ 2000 Hz
        signal = np.random.randn(2600)
        
        start = time.time()
        processed = fm.preprocess_emg(signal, fs=2000)
        _, mdf = core.mnf_mdf(processed, fs=2000)
        elapsed = time.time() - start
        
        # Should process faster than real-time (< 1.3 seconds)
        assert elapsed < 1.3, f"Processing took {elapsed:.3f}s, too slow for real-time"
    
    def test_android_bridge_api(self):
        """Test Android bridge wrapper API."""
        from emg_util.android_bridge import process_emg_window
        
        # Simulate Android calling pattern
        raw_data = np.random.randn(2600).tolist()  # Android passes lists
        
        result = process_emg_window(
            raw_data,
            fs=2000,
            return_dict=True  # Android expects dict
        )
        
        # Verify Android-friendly output
        assert isinstance(result, dict)
        assert "mdf" in result
        assert "fatigue_level" in result
        assert isinstance(result["mdf"], float)  # Not numpy type
    
    def test_no_matplotlib_dependency(self):
        """Test that core library doesn't require matplotlib."""
        # Matplotlib not available on Android
        import importlib
        
        # Should be able to import without matplotlib
        try:
            import matplotlib
            pytest.skip("matplotlib is installed, can't test absence")
        except ImportError:
            pass  # Good - matplotlib not available
        
        # Core functions should still work
        signal = np.random.randn(2600)
        processed = fm.preprocess_emg(signal, fs=2000)
        assert processed is not None
```

### Android-Specific Regression Tests

```python
class TestAndroidRegression:
    """Regression tests using Android session data."""
    
    def test_android_session_loading(self):
        """Test loading data from Android app format."""
        # Android saves in slightly different format
        android_data_dir = Path("regression_testlogs/android_format")
        
        if not android_data_dir.exists():
            pytest.skip("Android format data not available")
        
        # Load Android-format data
        from emg_util.android_bridge import load_android_session
        
        emg_df, imu_df = load_android_session(str(android_data_dir))
        
        assert len(emg_df) > 0
        assert len(imu_df) > 0
    
    def test_android_fatigue_workflow(self):
        """Test complete fatigue workflow as used by Android."""
        from emg_util.android_bridge import AndroidFatigueMonitor
        
        # Initialize (Android pattern)
        monitor = AndroidFatigueMonitor(
            fs=2000,
            warmup_skip_min=2.0,
            baseline_swings=10
        )
        
        # Simulate Android sending swing data
        for i in range(15):
            swing_data = np.random.randn(2600).tolist()
            result = monitor.process_swing(
                swing_data,
                timestamp_ms=i * 2000,
                gyro_peak=200.0
            )
            
            # Verify Android-friendly output
            assert isinstance(result, dict)
            assert "fatigue_level" in result
            assert result["fatigue_level"] in ["warming_up", "fresh", "moderate", "high"]
```

---

## Migration Checklist

### For Each Python Script

- [ ] Identify unique functionality
- [ ] Move to appropriate location (core vs android_bridge)
- [ ] Add regression tests
- [ ] Add Android compatibility tests
- [ ] Update imports in consuming code
- [ ] Verify performance on Android device
- [ ] Remove old duplicate
- [ ] Update documentation

### For Android App

- [ ] Add emg_util as git submodule
- [ ] Update Chaquopy configuration
- [ ] Update all Python imports
- [ ] Test on physical device
- [ ] Measure memory usage
- [ ] Measure processing latency
- [ ] Update app documentation

### For Desktop Tools

- [ ] Update to use emg_util as dependency
- [ ] Remove duplicate code
- [ ] Add integration tests
- [ ] Update documentation

---

## Risk Mitigation

### Risk 1: Breaking Changes

**Mitigation:**
- Pin submodule to specific commit initially
- Thorough testing before updating
- Maintain backward compatibility layer
- Version numbering (semantic versioning)

### Risk 2: Performance Regression

**Mitigation:**
- Benchmark before/after migration
- Add performance tests to CI
- Profile on actual Android devices
- Optimize hot paths if needed

### Risk 3: Build Complexity

**Mitigation:**
- Document build process clearly
- Automate submodule updates
- Provide troubleshooting guide
- Test on clean environments

### Risk 4: Team Coordination

**Mitigation:**
- Clear communication plan
- Phased rollout
- Training sessions
- Dedicated support channel

---

## Success Metrics

### Code Quality
- ✅ 100% test coverage for core algorithms
- ✅ All regression tests passing
- ✅ Android compatibility tests passing
- ✅ Zero code duplication

### Performance
- ✅ Processing time < 1 second per swing
- ✅ Memory usage < 50 MB on Android
- ✅ No performance regression vs current

### Maintenance
- ✅ Single codebase to maintain
- ✅ Automated testing on all platforms
- ✅ Clear documentation
- ✅ Easy to onboard new developers

---

## Timeline

| Phase | Duration | Completion |
|-------|----------|------------|
| Phase 1: Consolidate Core | 1 week | TBD |
| Phase 2: Setup Submodules | 1 week | TBD |
| Phase 3: Migrate Android | 1 week | TBD |
| Phase 4: CI/CD | 1 week | TBD |
| **Total** | **4 weeks** | **TBD** |

---

## Next Steps

1. **Review this plan** with team
2. **Audit Android scripts** for unique functionality
3. **Create android_bridge module** structure
4. **Write Android compatibility tests**
5. **Begin Phase 1** implementation

---

## References

- [Git Submodules Documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [Chaquopy Documentation](https://chaquo.com/chaquopy/doc/current/)
- [Python Packaging Guide](https://packaging.python.org/)
- Regression Test Suite: `emg_util/tests/test_regression.py`
- High-Level Design: `emg_util/HIGH_LEVEL_DESIGN.md`
