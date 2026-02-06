---
phase: 07-shadow-prices-what-if
plan: 01
subsystem: optimization
tags: [shadow-prices, perturbation-analysis, what-if, fleet-efficiency, sensitivity-analysis, cli]

# Dependency graph
requires:
  - phase: 04-safety-threshold-sweep
    provides: run_safety_sweep(), sweep pattern
  - phase: 05-pareto-frontier
    provides: run_pareto_sweep(), shadow carbon price pattern, select_fleet_milp(co2_cap)
  - phase: 06-submission-charts
    provides: --all CLI flag, chart patterns
provides:
  - compute_shadow_prices() for DWT/safety constraint perturbation analysis
  - format_shadow_prices() for formatted shadow price output
  - run_diversity_whatif() for fuel diversity constraint cost analysis
  - compute_fleet_efficiency() for cost/DWT, CO2/DWT, utilization metrics
  - --shadow-prices CLI flag in run.py
affects: [08-enhanced-charts, 09-case-paper-slides]

# Tech tracking
tech-stack:
  added: []
  patterns: [constraint-perturbation-shadow-prices, diversity-what-if-toggle, fleet-efficiency-ratios]

key-files:
  created: []
  modified: [src/sensitivity.py, run.py]

key-decisions:
  - "DWT shadow price via +1% perturbation (cargo_demand * 1.01)"
  - "Safety shadow price via +0.1 perturbation (threshold + 0.1)"
  - "Diversity what-if compares require_all_fuel_types True vs False"
  - "Fleet efficiency uses total_cost_and_metrics() for consistency"

patterns-established:
  - "Constraint perturbation: re-solve MILP with tightened param, compute marginal cost"
  - "What-if: toggle constraint flag, compare results"

issues-created: []

# Metrics
duration: 5min
completed: 2026-02-06
---

# Phase 7 Plan 1: Shadow Prices, What-If & Efficiency Summary

**Shadow prices via DWT/safety perturbation, fuel diversity cost analysis, and fleet efficiency ratios with --shadow-prices CLI flag**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-06T14:47:13Z
- **Completed:** 2026-02-06T14:52:13Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- Added compute_shadow_prices() — perturbs DWT demand +1% and safety threshold +0.1, re-solves MILP, computes marginal cost per unit of constraint tightening
- Added run_diversity_whatif() — compares fleet with/without fuel diversity requirement, showing cost savings and fuel types lost
- Added compute_fleet_efficiency() — cost/DWT, cost/vessel, DWT/vessel, CO2/DWT, capacity utilization ratio
- Wired everything into run.py with --shadow-prices flag (included in --all convenience group)

## Task Commits

Each task was committed atomically:

1. **Task 1: Shadow price extraction via constraint perturbation** - `da697e2` (feat)
2. **Task 2: Diversity what-if and fleet efficiency metrics** - `66b3003` (feat)
3. **Task 3: Wire shadow prices and what-if into CLI** - `50b04c3` (feat)

## Files Created/Modified
- `src/sensitivity.py` - Added compute_shadow_prices(), format_shadow_prices(), run_diversity_whatif(), compute_fleet_efficiency()
- `run.py` - Added --shadow-prices flag, shadow prices/what-if/efficiency output sections, new imports

## Decisions Made
- DWT shadow price computed via +1% perturbation (standard finite-difference approach)
- Safety shadow price via +0.1 perturbation (one-tenth of a safety point)
- Diversity what-if toggles require_all_fuel_types flag for clean A/B comparison
- Format as print-friendly string tables (not DataFrames) for consistency with shadow price output

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Phase 7 complete — all shadow prices and what-if analyses ready
- Test fixture results: DWT shadow = $17.18/tDWT, safety shadow = $0.00 (fleet exceeds by 0.88 margin)
- Diversity constraint costs $2.75M extra (8 vs 4 vessels, 7 fuel types lost without)
- Efficiency: $7.25/tDWT, 0.003 tCO2eq/tDWT, 100% utilization
- Ready for Phase 8 (Enhanced Charts — MACC and fleet composition stacked bars)

---
*Phase: 07-shadow-prices-what-if*
*Completed: 2026-02-06*
