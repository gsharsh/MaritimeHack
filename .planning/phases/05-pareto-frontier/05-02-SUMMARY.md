---
phase: 05-pareto-frontier
plan: 02
subsystem: optimization
tags: [carbon-price-sweep, cli, sensitivity-analysis]

# Dependency graph
requires:
  - phase: 05-pareto-frontier
    provides: run_pareto_sweep(), format_pareto_table(), select_fleet_milp(co2_cap)
  - phase: 04-safety-threshold-sweep
    provides: --sweep CLI pattern, sweep formatting pattern
provides:
  - run_carbon_price_sweep() for multi-price MILP comparison
  - format_carbon_sweep_table() for formatted output
  - --pareto CLI flag in run.py
  - --carbon-sweep CLI flag in run.py
affects: [06-submission-charts]

# Tech tracking
tech-stack:
  added: []
  patterns: [carbon-price-adjustment-sweep, cli-flag-pattern]

key-files:
  created: []
  modified: [src/sensitivity.py, run.py]

key-decisions:
  - "Carbon price adjustment via final_cost recalculation: final_cost - carbon_cost + CO2eq * new_price"
  - "Graceful fallback when carbon_cost column missing: compute as CO2eq * CARBON_PRICE(80)"

patterns-established:
  - "Carbon price sweep: copy df, adjust final_cost, re-solve MILP"

issues-created: []

# Metrics
duration: 3min
completed: 2026-02-06
---

# Phase 5 Plan 2: Carbon Price Sweep + CLI Wiring Summary

**Carbon price sweep at $80/$120/$160/$200 with --pareto and --carbon-sweep CLI flags**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-06T12:45:42Z
- **Completed:** 2026-02-06T12:49:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Implemented run_carbon_price_sweep() — adjusts final_cost per carbon price and re-solves MILP
- Implemented format_carbon_sweep_table() — formatted DataFrame output
- Added --pareto CLI flag — triggers 15-point epsilon-constraint Pareto frontier
- Added --carbon-sweep CLI flag — triggers carbon price sweep with fuel composition output
- Graceful handling of missing carbon_cost column in test fixtures

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement run_carbon_price_sweep()** - `0b1e384` (feat)
2. **Task 2: Wire --pareto and --carbon-sweep into run.py CLI** - `169a91d` (feat)

## Files Created/Modified
- `src/sensitivity.py` - Added run_carbon_price_sweep(), format_carbon_sweep_table()
- `run.py` - Added --pareto and --carbon-sweep flags with output sections

## Decisions Made
- Carbon price adjustment: final_cost - carbon_cost + CO2eq * new_price (simple column arithmetic)
- Fallback for missing carbon_cost column: compute as CO2eq * 80 (base CARBON_PRICE)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Phase 5 complete, ready for Phase 6 (Submission & Charts)
- All sensitivity analysis functions available: safety sweep, Pareto frontier, carbon price sweep
- CLI flags: --sweep, --pareto, --carbon-sweep all functional

---
*Phase: 05-pareto-frontier*
*Completed: 2026-02-06*
