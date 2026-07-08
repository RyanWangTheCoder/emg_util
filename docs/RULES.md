# Development Rules & Guidelines

**Last Updated:** 2026-02-27  
**Purpose:** Establish clear rules for maintaining code consistency, preventing breakage, and ensuring proper workflow

---

## 🔴 CRITICAL RULES - MUST FOLLOW

### Rule 1: Read Documentation First

**BEFORE making ANY changes, you MUST read:**

1. **HIGH_LEVEL_DESIGN.md** (or **ANDROID_HLD.md** for Android)
   - Understand the three-tier architecture
   - Understand file relationships
   - Understand why code is organized this way

2. **PYTHON_CONSOLIDATION_PLAN.md**
   - Understand the consolidation strategy
   - Understand which files are shared vs platform-specific

3. **COMMANDS.md**
   - Understand how tools are used
   - Understand command-line interfaces

**❌ DO NOT skip documentation reading**  
**❌ DO NOT assume you understand the architecture**  
**✅ DO ask questions if documentation is unclear**

---

### Rule 2: Discuss & Align BEFORE Coding

**NEVER start coding without explicit approval!**

**Required workflow:**
1. **Propose changes** - Explain what you want to change and why
2. **Discuss details** - Get feedback on approach
3. **Align on solution** - Ensure everyone agrees
4. **Get explicit approval** - Wait for "go ahead" or "approved"
5. **Then code** - Only after approval

**Examples of what requires discussion:**
- Adding new features
- Modifying existing algorithms
- Refactoring code structure
- Removing "duplicate" code
- Changing function signatures
- Updating dependencies

**❌ DO NOT code first, ask later**  
**❌ DO NOT assume changes are obvious**  
**✅ DO provide detailed proposals**  
**✅ DO wait for explicit approval**

---

### Rule 3: Maintain Dual-File Consistency

**Critical file pairs that MUST stay synchronized:**

#### Pair 1: `emg_util.py` ↔ `emg_util_nopandas.py`

**When updating `emg_util.py`, you MUST also update `emg_util_nopandas.py`**

**Synchronization checklist:**
- [ ] Update algorithm in `emg_util.py` (Windows, pandas-based)
- [ ] Test on Windows
- [ ] Port changes to `emg_util_nopandas.py` (Android, no pandas)
- [ ] Test on Android
- [ ] Verify consistency (compare function signatures, parameters, logic)
- [ ] Update CHANGELOG.md in both locations
- [ ] Update version numbers

**Functions that MUST match:**
- `envelope()` - Same algorithm, same parameters
- `mnf_mdf()` - Same Welch parameters, same calculations
- `feat_mav()`, `feat_rms()`, `feat_wl()`, `feat_zc()`, `feat_ssc()` - Identical
- `robust_zscore()` - Same MAD-based calculation
- `detect_swing_windows_from_imu_arrays()` - Same detection logic
- `select_baseline_swings()` - Same warmup/baseline logic
- `compute_baseline_from_swing_features()` - Same median calculation
- `apply_baseline_deltas()` - Same percentage formulas
- `compute_swing_emg_features()` - Same windowing logic

**Exception: `preprocess_emg()`**
- ✅ Both files import from `fatigue_monitor.py` (single source of truth)
- ✅ NO manual synchronization needed
- ✅ Changes to preprocessing go in `fatigue_monitor.py` only

**❌ DO NOT update only one file**  
**❌ DO NOT assume "it's just a small change"**  
**✅ DO update both files together**  
**✅ DO test on both platforms**

---

### Rule 4: Never Break Existing Functionality

**Backward compatibility is CRITICAL!**

**Before making changes:**
1. **Identify all callers** - Who uses this function?
2. **Check dependencies** - What depends on this behavior?
3. **Review tests** - What tests cover this code?
4. **Consider impact** - What could break?

**When modifying functions:**
- ✅ **Add optional parameters** (with defaults) - Safe
- ✅ **Add new functions** - Safe
- ✅ **Extend functionality** (backward-compatible) - Safe
- ❌ **Remove parameters** - Breaking change!
- ❌ **Change parameter order** - Breaking change!
- ❌ **Change return type** - Breaking change!
- ❌ **Remove functions** - Breaking change!

**If you must make breaking changes:**
1. **Discuss first** (see Rule 2)
2. **Deprecate old version** (don't remove immediately)
3. **Provide migration path** (document how to update)
4. **Update all callers** (in same commit)
5. **Update tests** (ensure nothing breaks)

**❌ DO NOT remove code without asking**  
**❌ DO NOT change signatures without approval**  
**✅ DO preserve backward compatibility**  
**✅ DO add deprecation warnings**

---

### Rule 5: Always Update Documentation

**Documentation is NOT optional - it's REQUIRED!**

**Every code change MUST be accompanied by documentation updates:**

**ALWAYS update CHANGELOG.md:**
- ✅ **What changed** - Describe the change clearly
- ✅ **Why it changed** - Explain the reason/motivation
- ✅ **When it changed** - Date of change
- ✅ **Who changed it** - Your name/identifier
- ✅ **Impact** - What's affected, who needs to know

**ALWAYS update HIGH_LEVEL_DESIGN.md (or ANDROID_HLD.md) when:**
- Architecture changes (new tiers, new components)
- File relationships change (new files, removed files, moved files)
- Design decisions change (new patterns, new approaches)
- Workflows change (new processes, modified processes)
- Integration points change (new APIs, modified interfaces)

**ALWAYS update function docstrings when:**
- Function behavior changes
- Parameters added/removed/changed
- Return values change
- Error handling changes

**ALWAYS update COMMANDS.md when:**
- CLI arguments change
- New commands added
- Command behavior changes
- Usage examples need updating

**Make documentation updates part of your commit:**
```bash
# Good commit (includes documentation)
git add emg_util.py emg_util_nopandas.py CHANGELOG.md
git commit -m "[EMG] Update MDF calculation

- Changed Welch window size from 1024 to 2048
- Improves frequency resolution for fatigue detection
- Updated both emg_util.py and emg_util_nopandas.py

Tested: pytest passes (25/25), Android build succeeds
Affects: All fatigue analysis workflows
"

# Bad commit (missing documentation)
git add emg_util.py
git commit -m "fix mdf"  # ❌ No CHANGELOG, no details, incomplete
```

**❌ DO NOT commit code without updating documentation**  
**❌ DO NOT say "I'll update docs later" (you won't)**  
**❌ DO NOT assume changes are self-documenting**  
**✅ DO update CHANGELOG.md with every commit**  
**✅ DO update HLD when architecture/design changes**  
**✅ DO make documentation a habit, not an afterthought**

---

### Rule 6: Always Add Regression Tests

**Tests prevent bugs from coming back!**

**Every code change should include tests when applicable:**

**ALWAYS add regression tests for:**
- ✅ **Bug fixes** - Test that the bug doesn't reoccur
- ✅ **New features** - Test that the feature works correctly
- ✅ **Algorithm changes** - Test that results are correct
- ✅ **Edge cases** - Test boundary conditions
- ✅ **Error handling** - Test that errors are handled properly

**Where to add tests:**
- **Windows:** `C:\wangx\ftc\emg_util\tests\test_regression.py`
- **Android:** Build tests in Android project (if applicable)

**Test structure:**
```python
def test_new_feature_or_bugfix():
    """Test description: what are we testing and why?
    
    This test was added on 2026-02-27 to verify that [feature/bug]
    works correctly after [change description].
    """
    # Arrange - set up test data
    input_data = np.array([...])
    expected_output = ...
    
    # Act - call the function
    actual_output = function_under_test(input_data)
    
    # Assert - verify results
    assert actual_output == expected_output
    # or
    np.testing.assert_allclose(actual_output, expected_output, rtol=1e-5)
```

**When tests are applicable:**
- ✅ Algorithm changes (verify correctness)
- ✅ Bug fixes (prevent regression)
- ✅ New features (verify functionality)
- ✅ Edge case handling (verify robustness)
- ✅ Data processing (verify accuracy)

**When tests may not be applicable:**
- ⚠️ UI-only changes (Android layouts, etc.)
- ⚠️ Documentation-only changes
- ⚠️ Configuration changes (but consider integration tests)

**Test quality guidelines:**
- **Clear test names** - `test_mdf_calculation_with_short_signal()`
- **Good docstrings** - Explain what and why
- **Arrange-Act-Assert** - Clear test structure
- **Meaningful assertions** - Test the right thing
- **Edge cases** - Test boundaries, empty inputs, etc.
- **Fast execution** - Tests should run quickly

**Running tests:**
```bash
# Run all tests
cd C:\wangx\ftc\emg_util
pytest tests/test_regression.py -v

# Run specific test
pytest tests/test_regression.py::test_specific_function -v

# Run with coverage
pytest tests/test_regression.py --cov=. --cov-report=html
```

**Example: Adding a regression test for a bug fix**
```python
def test_mdf_handles_short_signals():
    """Test that MDF calculation doesn't crash on short signals.
    
    Bug fix 2026-02-27: Previously crashed with signals < 256 samples.
    This test ensures the fix works and prevents regression.
    """
    # Arrange - create short signal (100 samples)
    short_signal = np.random.randn(100)
    fs = 2000.0
    
    # Act - should not crash
    mnf, mdf = mnf_mdf(short_signal, fs)
    
    # Assert - should return valid values or NaN (not crash)
    assert isinstance(mnf, float)
    assert isinstance(mdf, float)
    # Short signals may return NaN, which is acceptable
    assert np.isnan(mnf) or mnf > 0
    assert np.isnan(mdf) or mdf > 0
```

**❌ DO NOT skip adding tests**  
**❌ DO NOT say "I'll add tests later" (you won't)**  
**❌ DO NOT assume code is self-testing**  
**✅ DO add tests for bug fixes (prevent regression)**  
**✅ DO add tests for new features (verify functionality)**  
**✅ DO add tests for algorithm changes (verify correctness)**  
**✅ DO make testing a habit, not an afterthought**

---

### Rule 7: Ask Before Removing "Duplicates"

**Not all duplication is bad!**

**Before removing "duplicate" code:**
1. **Ask why it exists** - There may be a good reason
2. **Check documentation** - Is it explained in HLD?
3. **Verify it's truly duplicate** - Same logic? Same purpose?
4. **Propose consolidation** - Explain benefits and risks
5. **Get approval** - Wait for explicit "yes"

**Examples of intentional "duplication":**

**✅ Intentional (DO NOT consolidate without approval):**
- `emg_util.py` vs `emg_util_nopandas.py` - Different data structures (pandas vs numpy)
- `realtime_bridge.py` (Android) vs `sensordata_plotter.py` (Windows) - Different platforms
- `offline_runner.py` (Android) vs `emg_util_yaml_runner.py` (Windows) - Different workflows
- `btcentral_offline_decode.py` (Android) vs `btCentral.py` (Windows) - Different use cases

**❌ Not duplicate (DO NOT consolidate):**
- Platform-specific code (Android vs Windows)
- Real-time vs offline algorithms (different constraints)
- Different data structures (pandas vs numpy)

**❌ DO NOT consolidate without asking**  
**❌ DO NOT assume duplication is bad**  
**✅ DO ask first**  
**✅ DO explain your reasoning**

---

## 📋 STANDARD WORKFLOW

### For Algorithm Changes

```
1. Read HIGH_LEVEL_DESIGN.md
2. Identify affected files:
   - emg_util.py (Windows)
   - emg_util_nopandas.py (Android)
   - fatigue_monitor.py (if preprocessing)
3. Propose changes (explain what, why, how)
4. Discuss & get approval
5. Update emg_util.py
6. Add/update regression tests (REQUIRED if applicable!)
7. Test on Windows (pytest tests/test_regression.py - all must pass)
8. Port to emg_util_nopandas.py
9. Test on Android (./gradlew assembleDebug)
10. Update CHANGELOG.md (REQUIRED!)
11. Update HIGH_LEVEL_DESIGN.md (if design/architecture changed)
12. Update function docstrings (if behavior changed)
13. Commit with clear message (include what, why, impact, tests added)
```

### For New Features

```
1. Read HIGH_LEVEL_DESIGN.md
2. Propose feature (explain use case, design, impact)
3. Discuss & get approval
4. Determine which files need changes
5. Implement in appropriate tier:
   - Tier 1 (Real-time): fatigue_monitor.py, realtime_bridge.py
   - Tier 2 (Post-capture): offline_runner.py
   - Tier 3 (Offline): emg_util.py, emg_util_yaml_runner.py
6. Add regression tests (REQUIRED! - test new functionality)
7. Test on Windows (pytest tests/test_regression.py - all must pass)
8. Test on Android (if applicable)
9. Update CHANGELOG.md (REQUIRED! - describe new feature)
10. Update HIGH_LEVEL_DESIGN.md (REQUIRED! - document new component/workflow)
11. Update COMMANDS.md (if CLI changed)
12. Update function docstrings (document new APIs)
13. Commit with clear message (include what, why, how to use, tests added)
```

### For Bug Fixes

```
1. Identify root cause
2. Determine affected files
3. If affects shared code (emg_util.py):
   - Fix in emg_util.py
   - Port to emg_util_nopandas.py
   - Test both platforms
4. If affects platform-specific code:
   - Fix in that file only
   - Test that platform
5. Add regression test (REQUIRED! - prevent bug from returning)
6. Test on Windows (pytest tests/test_regression.py - all must pass)
7. Test on Android (if applicable)
8. Update CHANGELOG.md (REQUIRED! - describe bug and fix)
9. Update HIGH_LEVEL_DESIGN.md (if bug revealed design issue)
10. Update function docstrings (if behavior clarification needed)
11. Commit with clear message (include bug description, root cause, fix, test added)
```

---

## 🧪 TESTING REQUIREMENTS

### Before Committing

**Windows:**
```bash
cd C:\wangx\ftc\emg_util
pytest tests/test_regression.py -v
# All tests must pass (25/25)
```

**Android:**
```bash
cd C:\wangx\ftc\btLeApp
./gradlew clean
./gradlew assembleDebug
# Build must succeed
```

**Functional Testing:**
- [ ] Test real-time fatigue monitoring
- [ ] Test swing detection
- [ ] Test offline analysis
- [ ] Compare results (Android vs Windows should match)

---

## 📝 DOCUMENTATION REQUIREMENTS

### When Making Changes

**ALWAYS update (not optional!):**

1. **CHANGELOG.md** - REQUIRED for EVERY commit
   - What changed (clear description)
   - Why it changed (motivation/reason)
   - When it changed (date)
   - Impact (what's affected, who needs to know)
   - Example:
     ```markdown
     ## [2026-02-27] - MDF Calculation Update
     ### Changed
     - Increased Welch window size from 1024 to 2048 samples
     - Improves frequency resolution for fatigue detection
     - Affects: emg_util.py, emg_util_nopandas.py, fatigue_monitor.py
     ### Impact
     - More accurate MDF values (better fatigue detection)
     - Slightly slower computation (~10ms per window)
     - All existing data remains compatible
     ```

2. **HIGH_LEVEL_DESIGN.md** - REQUIRED when:
   - Architecture changes (new tiers, components, workflows)
   - File relationships change (new files, moved files, removed files)
   - Design decisions change (new patterns, approaches)
   - Integration points change (new APIs, modified interfaces)
   - Example: Added new Tier 2 component → Update HLD architecture diagram

3. **Function docstrings** - REQUIRED when:
   - Function behavior changes
   - Parameters added/removed/changed
   - Return values change
   - Error handling changes
   - Example:
     ```python
     def mnf_mdf(x: np.ndarray, fs: float) -> Tuple[float, float]:
         """Compute Mean and Median Frequency using Welch's method.
         
         Args:
             x: EMG signal (preprocessed)
             fs: Sampling rate in Hz
             
         Returns:
             (mnf, mdf): Mean and Median Frequency in Hz
             
         Changed 2026-02-27: Increased nperseg from 1024 to 2048
         for better frequency resolution.
         """
     ```

4. **COMMANDS.md** - REQUIRED when:
   - CLI arguments change
   - New commands added
   - Command behavior changes
   - Usage examples need updating

**Commit message format (REQUIRED):**
```
[Component] Brief description

- Detailed change 1
- Detailed change 2
- Why this change was needed

Documentation:
- Updated CHANGELOG.md (describe what changed)
- Updated HIGH_LEVEL_DESIGN.md (if applicable)
- Updated docstrings (if applicable)

Tested: [describe testing]
Affects: [list affected files]
```

**Example good commit:**
```
[EMG] Improve MDF frequency resolution

- Increased Welch window size from 1024 to 2048 samples
- Improves frequency resolution from ~2Hz to ~1Hz
- Better fatigue detection for subtle MDF changes
- Updated both emg_util.py and emg_util_nopandas.py

Documentation:
- Updated CHANGELOG.md with change details and impact
- Updated mnf_mdf() docstrings in both files
- No HLD changes needed (algorithm improvement only)

Tested: 
- pytest passes (25/25)
- Android build succeeds
- Verified MDF values match between platforms
- Tested on sample data: MDF resolution improved as expected

Affects: emg_util.py, emg_util_nopandas.py
```

**Example bad commit (DO NOT DO THIS):**
```
fix mdf  # ❌ No details, no CHANGELOG, no documentation
```

---

## 🔍 CODE REVIEW CHECKLIST

### Before Submitting Changes

**Documentation (REQUIRED):**
- [ ] Updated CHANGELOG.md (EVERY commit needs this!)
- [ ] Updated HIGH_LEVEL_DESIGN.md (if architecture/design changed)
- [ ] Updated ANDROID_HLD.md (if Android-specific changes)
- [ ] Updated COMMANDS.md (if CLI changed)
- [ ] Updated function docstrings (if behavior changed)
- [ ] Clear commit message with documentation section

**Code Changes:**
- [ ] Read relevant documentation (HLD, consolidation plan)
- [ ] Discussed changes and got approval
- [ ] Updated both emg_util.py and emg_util_nopandas.py (if applicable)
- [ ] Verified backward compatibility
- [ ] Added/updated tests

**Testing:**
- [ ] Added/updated regression tests (if applicable)
- [ ] All tests pass on Windows (pytest - 25/25 or more)
- [ ] Tested on Android (build succeeds)
- [ ] Functional testing completed
- [ ] Results match between platforms (if applicable)
- [ ] Test coverage adequate for changes

**Final Check:**
- [ ] All documentation updated
- [ ] All tests pass
- [ ] No breaking changes (or properly documented)
- [ ] Commit message includes documentation updates

---

## 🚫 COMMON MISTAKES TO AVOID

### ❌ DON'T:
1. **Skip documentation reading** - Always read HLD first
2. **Code without approval** - Always discuss first
3. **Update only one file** - Update both emg_util.py and nopandas version
4. **Break backward compatibility** - Preserve existing APIs
5. **Remove "duplicate" code** - Ask first, it may be intentional
6. **Change function signatures** - Add optional parameters instead
7. **Skip testing** - Always test both platforms
8. **Forget CHANGELOG.md** - REQUIRED for EVERY commit!
9. **Forget to update HLD** - REQUIRED when design/architecture changes
10. **Skip docstring updates** - Keep documentation accurate
11. **Skip adding tests** - REQUIRED for bug fixes and new features!
12. **Write vague commit messages** - Be specific, include documentation updates
13. **Assume understanding** - Ask questions if unclear
14. **Rush changes** - Take time to do it right

### ✅ DO:
1. **Read documentation first** - Understand before changing
2. **Discuss and align** - Get approval before coding
3. **Maintain consistency** - Keep dual files synchronized
4. **Test thoroughly** - Both platforms, all use cases
5. **Update CHANGELOG.md** - EVERY commit, no exceptions!
6. **Update HLD** - When architecture/design changes
7. **Update docstrings** - Keep function documentation accurate
8. **Add regression tests** - For bug fixes, new features, algorithm changes
9. **Write clear commit messages** - Include what, why, documentation updates, tests added
10. **Ask questions** - Better to ask than break things
11. **Be careful** - Existing functionality is critical
12. **Think about impact** - Who uses this code?
13. **Follow workflow** - Use standard procedures
14. **Communicate clearly** - Explain what, why, how
15. **Make documentation a habit** - Not an afterthought
16. **Make testing a habit** - Add tests as you code

---

## 📚 KEY DOCUMENTATION FILES

### Must Read (In Order)

1. **HIGH_LEVEL_DESIGN.md** (`C:\wangx\ftc\emg_util\HIGH_LEVEL_DESIGN.md`)
   - Three-tier architecture
   - File relationships
   - Design decisions

2. **ANDROID_HLD.md** (`C:\wangx\ftc\btLeApp\app\src\main\python\ANDROID_HLD.md`)
   - Android-specific architecture
   - Git submodule setup
   - Platform differences

3. **PYTHON_CONSOLIDATION_PLAN.md** (`C:\wangx\ftc\emg_util\PYTHON_CONSOLIDATION_PLAN.md`)
   - Consolidation strategy
   - File organization
   - Maintenance approach

4. **COMMANDS.md** (`C:\wangx\ftc\emg_util\COMMANDS.md`)
   - Command reference
   - Usage examples
   - Common workflows

5. **RULES.md** (this file)
   - Development rules
   - Workflow guidelines
   - Best practices

---

## 🎯 QUICK REFERENCE

### File Synchronization Matrix

| File | Sync With | How | When |
|------|-----------|-----|------|
| `emg_util.py` | `emg_util_nopandas.py` | Manual port | Every algorithm change |
| `fatigue_monitor.py` | (imported by both) | Auto via import | Preprocessing changes only |
| `btCentral.py` | `btcentral_offline_decode.py` | Manual (if protocol changes) | Protocol changes only |
| `sensordata_plotter.py` | `realtime_bridge.py` | No sync (different platforms) | Never |
| `emg_util_yaml_runner.py` | `offline_runner.py` | No sync (different workflows) | Never |

### Platform-Specific Files (DO NOT consolidate)

**Android-specific:**
- `realtime_bridge.py` - Java ↔ Python bridge
- `offline_runner.py` - Android post-capture
- `btcentral_offline_decode.py` - Binary decoder
- `analysis_bridge.py` - Deprecated (check before removing)

**Windows-specific:**
- `sensordata_plotter.py` - Real-time plotter
- `emg_util_yaml_runner.py` - CLI runner
- `btCentral.py` - BLE capture

**Shared (via git submodule):**
- `fatigue_monitor.py` - Real-time fatigue
- `emg_util_nopandas.py` - Signal processing (no pandas)
- `capture_loader.py` - Session loading

---

## 💡 WHEN IN DOUBT

**Ask these questions:**

1. **Have I read the documentation?**
   - If no → Read HIGH_LEVEL_DESIGN.md first

2. **Have I discussed this change?**
   - If no → Propose and discuss before coding

3. **Does this affect both platforms?**
   - If yes → Update both emg_util.py and nopandas version

4. **Could this break existing code?**
   - If yes → Discuss backward compatibility strategy

5. **Am I removing "duplicate" code?**
   - If yes → Ask first, it may be intentional

6. **Have I tested thoroughly?**
   - If no → Test on both Windows and Android

7. **Have I updated CHANGELOG.md?**
   - If no → STOP! Update CHANGELOG.md first (REQUIRED!)

8. **Have I updated HIGH_LEVEL_DESIGN.md?**
   - If design/architecture changed → Update HLD (REQUIRED!)

9. **Have I updated docstrings?**
   - If function behavior changed → Update docstrings (REQUIRED!)

10. **Have I added regression tests?**
   - If bug fix, new feature, or algorithm change → Add tests (REQUIRED!)

**If you're unsure about ANY of these → ASK!**

**Remember: Documentation is NOT optional. Every commit MUST include:**
- ✅ Updated CHANGELOG.md (what, why, when, impact)
- ✅ Updated HLD (if architecture/design changed)
- ✅ Updated docstrings (if function behavior changed)
- ✅ Clear commit message (including documentation updates)

---

## 📞 GETTING HELP

**When you need clarification:**

1. **Check documentation** - HLD, consolidation plan, commands
2. **Check this file** - RULES.md (you're reading it!)
3. **Ask specific questions** - "Why does X exist?" not "What should I do?"
4. **Provide context** - What are you trying to accomplish?
5. **Wait for response** - Don't proceed until you understand

**Good questions:**
- "Why do we have both emg_util.py and emg_util_nopandas.py?"
- "Is this code duplication intentional?"
- "What's the best way to add feature X?"
- "Will this change break backward compatibility?"

**Bad questions:**
- "Can I just remove this?" (without context)
- "Should I consolidate these files?" (without understanding why they exist)
- "Is this okay?" (after already making changes)

---

## 🎓 LEARNING RESOURCES

**To understand the codebase:**

1. **Start here:** HIGH_LEVEL_DESIGN.md
2. **Then read:** PYTHON_CONSOLIDATION_PLAN.md
3. **Then read:** ANDROID_HLD.md
4. **Then read:** COMMANDS.md
5. **Then read:** This file (RULES.md)

**To understand specific topics:**
- **Three-tier architecture:** HIGH_LEVEL_DESIGN.md → "Overview: Three Processing Tiers"
- **Git submodules:** ANDROID_HLD.md → "Git Submodule Consolidation"
- **File relationships:** HIGH_LEVEL_DESIGN.md → "File Inventory & Relationships"
- **Consistency verification:** ANDROID_HLD.md → "Consistency Verification"

---

## ✅ SUCCESS CRITERIA

**You're following the rules if:**

- ✅ You read documentation before making changes
- ✅ You discuss and get approval before coding
- ✅ You update both emg_util.py and nopandas version together
- ✅ You test on both platforms
- ✅ You don't break existing functionality
- ✅ You ask before removing "duplicate" code
- ✅ **You update CHANGELOG.md with EVERY commit** ← CRITICAL!
- ✅ **You update HLD when design/architecture changes** ← CRITICAL!
- ✅ **You update docstrings when behavior changes** ← CRITICAL!
- ✅ **You add regression tests when applicable** ← CRITICAL!
- ✅ You write clear commit messages (including documentation updates and tests)
- ✅ All tests pass (including new tests)
- ✅ Code review checklist is complete

**You're NOT following the rules if:**

- ❌ You skip documentation reading
- ❌ You code without approval
- ❌ You update only one file
- ❌ You break backward compatibility
- ❌ You remove code without asking
- ❌ You skip testing
- ❌ **You forget to update CHANGELOG.md** ← CRITICAL FAILURE!
- ❌ **You forget to update HLD when design changes** ← CRITICAL FAILURE!
- ❌ **You skip docstring updates** ← CRITICAL FAILURE!
- ❌ **You skip adding regression tests** ← CRITICAL FAILURE!
- ❌ You write vague commit messages
- ❌ Tests fail (old or new)
- ❌ You rush changes

---

## 🏆 BEST PRACTICES

### General Principles

1. **Understand before changing** - Read docs, ask questions
2. **Discuss before coding** - Align on approach
3. **Test thoroughly** - Both platforms, all use cases
4. **Document EVERYTHING** - CHANGELOG.md (EVERY commit!), HLD (design changes), docstrings (behavior changes)
5. **Make documentation a habit** - Update docs as you code, not after
6. **Maintain consistency** - Keep dual files synchronized
6. **Preserve compatibility** - Don't break existing code
7. **Ask when unsure** - Better safe than sorry
8. **Follow workflow** - Use standard procedures
9. **Communicate clearly** - Explain what, why, how
10. **Take your time** - Quality over speed

### Code Quality

- **Clear naming** - Functions and variables should be self-explanatory
- **Consistent style** - Follow existing code style
- **Good comments** - Explain why, not what
- **Comprehensive docstrings** - Document parameters, returns, behavior
- **Error handling** - Handle edge cases gracefully
- **Type hints** - Use type annotations where helpful

### Collaboration

- **Be respectful** - Everyone is learning
- **Be patient** - Take time to explain
- **Be thorough** - Don't skip steps
- **Be honest** - Admit when you don't know
- **Be helpful** - Share knowledge
- **Be careful** - Existing code is production-critical

---

**Remember: These rules exist to prevent bugs, maintain quality, and ensure smooth collaboration. Following them makes everyone's life easier!**

**Last Updated:** 2026-02-27  
**Version:** 1.0  
**Maintainer:** Development Team
