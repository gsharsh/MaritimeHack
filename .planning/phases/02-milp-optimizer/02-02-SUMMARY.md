---
phase: 02-milp-optimizer
plan: 02
subsystem: optimization
tags: [cli, run-py, column-mapping, argparse]

# Dependency graph
requires:
  - phase: 02-milp-optimizer/01
    provides: select_fleet_milp() function
provides:
  - CLI entry point with MILP integration
  - Correct column name defaults for per_vessel.csv
  - --cargo-demand and --safety-threshold CLI args
affects: [03-validation, 04-safety-threshold-sweep, 06-submission-charts]

# Tech tracking
tech-stack:
  added: []
  patterns: [cli-argparse-with-constant-defaults, graceful-infeasible-handling]

key-files:
  created: []
  modified: [run.py, src/optimization.py, tests/test_optimization.py]

key-decisions:
  - "Combined Task 1 and Task 2 (tightly coupled, CLI args needed for verification)"
  - "Column defaults now match per_vessel.csv: final_cost, FC_total, CO2eq"
  - "Infeasible exits with code 1 (not exception) for clean CLI behavior"

patterns-established:
  - "CLI pattern: argparse with constant defaults, run MILP, print results"

issues-created: []

# Metrics
duration: 1min
completed: 2026-02-06
---

# Phase 2 Plan 02: Wire MILP into run.py Summary

**CLI integration: run.py loads data, runs MILP, prints fleet metrics with --cargo-demand/--safety-threshold overrides**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-06T12:15:26Z
- **Completed:** 2026-02-06T12:16:43Z
- **Tasks:** 2 (combined into 1 commit)
- **Files modified:** 3

## Accomplishments

- Fixed `total_cost_and_metrics()` defaults to match per_vessel.csv columns
- Wired `select_fleet_milp()` into run.py with full metrics pipeline
- Added `--cargo-demand` and `--safety-threshold` CLI args
- Graceful infeasible handling (prints explanation, exits 1)
- All 18 tests pass

## Task Commits

1. **Task 1+2: Wire MILP + CLI args** — `7b7f756` (feat)

**Note:** Tasks combined because CLI args were needed to verify the MILP wiring.

## Files Created/Modified

- `run.py` — Full MILP pipeline: load → solve → validate → print metrics
- `src/optimization.py` — Fixed column defaults (final_cost, FC_total, CO2eq)
- `tests/test_optimization.py` — Updated fixture column names to match

## Decisions Made

- Combined tasks 1 and 2 into single commit (tightly coupled)
- Infeasible exits with sys.exit(1) rather than exception (cleaner CLI)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test fixture column names needed updating**
- **Found during:** Task 1 (column default change)
- **Issue:** test_optimization.py fixture used old column names (total_cost_usd, fuel_tonnes, co2e_tonnes)
- **Fix:** Updated to match new defaults (final_cost, FC_total, CO2eq)
- **Verification:** All 18 tests pass
- **Committed in:** 7b7f756

---

**Total deviations:** 1 auto-fixed (bug)
**Impact on plan:** Necessary fix. No scope creep.

## Issues Encountered

None.

## Next Step

Phase 2 complete, ready for Phase 3 (Validation)

---
*Phase: 02-milp-optimizer*
*Completed: 2026-02-06*
