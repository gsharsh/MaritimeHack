---
phase: 05-pareto-frontier
plan: 01
subsystem: optimization
tags: [pareto-frontier, epsilon-constraint, shadow-carbon-price, milp, co2-cap]

# Dependency graph
requires:
  - phase: 02-milp-optimizer
    provides: select_fleet_milp(), total_cost_and_metrics()
  - phase: 01-clean-slate-data-foundation
    provides: constants module, data adapter
provides:
  - select_fleet_milp() with optional co2_cap parameter
  - run_pareto_sweep() for 15-point epsilon-constraint Pareto frontier
  - format_pareto_table() for readable output
  - _solve_min_co2() helper for emissions-minimizing MILP
affects: [05-02-carbon-sweep, 06-submission-charts]

# Tech tracking
tech-stack:
  added: []
  patterns: [epsilon-constraint-pareto, shadow-carbon-price-computation, min-emissions-milp]

key-files:
  created: []
  modified: [src/optimization.py, src/sensitivity.py]

key-decisions:
  - "CO2eq cap added as optional parameter to existing select_fleet_milp() (not a separate function)"
  - "Min-emissions bound found via dedicated MILP (_solve_min_co2) rather than binary search"
  - "Shadow carbon price = marginal cost per tonne CO2eq reduced between consecutive Pareto points"

patterns-established:
  - "Epsilon-constraint pattern: find bounds (min-cost, min-emissions), sweep 15 evenly-spaced caps"
  - "Shadow price computation between consecutive feasible Pareto points"

issues-created: []

# Metrics
duration: 3min
completed: 2026-02-06
---

# Phase 5 Plan 1: Epsilon-Constraint Pareto Frontier Summary

**15-point cost-emissions Pareto frontier with CO2eq cap constraint and shadow carbon price computation**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-06T12:39:36Z
- **Completed:** 2026-02-06T12:43:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added optional `co2_cap` parameter to `select_fleet_milp()` — constrains total fleet CO2eq when provided
- Implemented `_solve_min_co2()` — dedicated MILP minimizing CO2eq to find Pareto lower bound
- Implemented `run_pareto_sweep()` — 15-point epsilon-constraint sweep with shadow carbon prices
- Implemented `format_pareto_table()` — readable DataFrame output matching existing sweep table pattern

## Task Commits

Each task was committed atomically:

1. **Task 1: Add optional CO2eq cap to select_fleet_milp()** - `2cdc0f7` (feat)
2. **Task 2: Implement run_pareto_sweep() with shadow carbon prices** - `4d516f7` (feat)

## Files Created/Modified
- `src/optimization.py` - Added co2_cap parameter and CO2eq constraint to select_fleet_milp()
- `src/sensitivity.py` - Added _solve_min_co2(), run_pareto_sweep(), format_pareto_table()

## Decisions Made
- CO2eq cap added as optional parameter to existing select_fleet_milp() rather than a separate function — keeps API surface minimal
- Min-emissions bound computed via dedicated MILP (_solve_min_co2) for efficiency
- Shadow carbon price = (cost_i - cost_{i-1}) / (co2_{i-1} - co2_i) between consecutive feasible points

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Ready for 05-02-PLAN.md (carbon price sweep + CLI wiring)
- run_pareto_sweep() pattern established for reference

---
*Phase: 05-pareto-frontier*
*Completed: 2026-02-06*
