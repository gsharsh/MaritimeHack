---
phase: 08-enhanced-charts
plan: 01
subsystem: charts
tags: [macc, carbon-sweep, visualization, matplotlib, pareto, sensitivity]

# Dependency graph
requires:
  - phase: 05-pareto-frontier
    provides: run_pareto_sweep(), shadow_carbon_price between consecutive Pareto points
  - phase: 06-submission-charts
    provides: chart patterns (Agg, 150 DPI, tight_layout), plot_pareto_frontier, plot_fleet_composition, plot_safety_comparison
  - phase: 07-shadow-prices-what-if
    provides: --shadow-prices flag, --all convenience group
provides:
  - plot_macc() for Marginal Abatement Cost Curve visualization
  - plot_carbon_sweep() for carbon price sensitivity dual-subplot chart
  - Both charts auto-generated with --all flag
affects: [09-case-paper-slides]

# Tech tracking
tech-stack:
  added: []
  patterns: [macc-waterfall-bars, dual-subplot-sensitivity, color-gradient-by-value]

key-files:
  created: []
  modified: [src/charts.py, run.py]

key-decisions:
  - "MACC bars sorted by shadow_carbon_price ascending (cheapest abatement first)"
  - "Color thresholds: <$100/t green, $100-$500/t yellow, >$500/t red"
  - "Reference line at $80/t matching CARBON_PRICE constant"
  - "Carbon sweep uses blue-to-red for cost, green-to-orange for emissions"
  - "Infeasible carbon prices show INFEASIBLE text instead of bars"

patterns-established:
  - "Waterfall-style MACC: cumulative x-axis with variable-width bars"
  - "Dual-subplot chart: shared x-axis labels, independent y-axes"

issues-created: []

# Metrics
duration: 5min
completed: 2026-02-06
---

# Phase 8 Plan 1: Enhanced Charts (MACC + Carbon Sweep) Summary

**MACC chart and carbon price sweep chart added to src/charts.py and wired into run.py --all**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-06
- **Completed:** 2026-02-06
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- Added plot_macc() — waterfall-style MACC from Pareto frontier shadow_carbon_price data, color-coded by cost tier, $80/t reference line
- Added plot_carbon_sweep() — dual-subplot chart (cost + emissions) across carbon prices with color gradients, infeasible handling
- Wired both charts into run.py: --pareto generates MACC alongside Pareto frontier, --carbon-sweep generates carbon sweep chart
- All 5 chart files now auto-generated with --all flag

## Task Commits

Each task was committed atomically:

1. **Task 1: MACC chart from Pareto data** - `d021aa4` (feat)
2. **Task 2: Carbon price sweep dual-subplot chart** - `aaaf2bb` (feat)
3. **Task 3: Wire charts into run.py** - `79b3f13` (feat)

## Files Created/Modified
- `src/charts.py` - Added plot_macc(), plot_carbon_sweep()
- `run.py` - Added imports and chart calls in pareto and carbon-sweep sections

## Decisions Made
- MACC sorted cheapest-first (ascending shadow_carbon_price) for standard MACC convention
- Color thresholds match typical abatement cost tiers ($100/t and $500/t boundaries)
- Reference line at $80/t matches project's CARBON_PRICE constant
- Carbon sweep uses intuitive color gradients (blue→red for cost, green→orange for emissions)

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Phase 8 complete — all 5 charts auto-generated with --all
- Charts in outputs/charts/: pareto_frontier.png, fleet_composition.png, safety_comparison.png, macc.png, carbon_price_sweep.png
- Ready for Phase 9 (Case Paper & Slides)

---
*Phase: 08-enhanced-charts*
*Completed: 2026-02-06*
