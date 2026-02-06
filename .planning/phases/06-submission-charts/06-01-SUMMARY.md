---
phase: 06-submission-charts
plan: 01
subsystem: outputs
tags: [submission-csv, pareto-chart, matplotlib, cli]

# Dependency graph
requires:
  - phase: 02-milp-optimizer
    provides: select_fleet_milp(), submission_outputs(), total_cost_and_metrics()
  - phase: 05-pareto-frontier
    provides: run_pareto_sweep(), format_pareto_table()
provides:
  - --submit CLI flag filling submission_template.csv from MILP base case
  - plot_pareto_frontier() in src/charts.py
  - --team-name, --category, --report-file CLI args
affects: [06-02-fleet-composition-charts]

# Tech tracking
tech-stack:
  added: [matplotlib]
  patterns: [agg-backend-for-cli-charts, submission-csv-template-fill]

key-files:
  created: [src/charts.py]
  modified: [run.py, outputs/submission/submission_template.csv]

key-decisions:
  - "Submission CSV preserves 4-column template format (Header Name, Data Type, Units, Submission)"
  - "Charts use matplotlib Agg backend for headless CLI execution"
  - "Pareto chart annotates min-cost and min-emissions endpoints"

patterns-established:
  - "Chart pattern: Agg backend, 150 DPI, tight_layout(), plt.close() after save"
  - "Submission pattern: read template, map Header Name to metrics dict, write back"

issues-created: []

# Metrics
duration: 5min
completed: 2026-02-06
---

# Phase 6 Plan 1: Submission CSV + Pareto Chart Summary

**Submission CSV filled from MILP base case with --submit flag, Pareto frontier line+scatter chart with annotated endpoints**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-06T12:54:41Z
- **Completed:** 2026-02-06T13:00:07Z
- **Tasks:** 2
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments
- Added --submit CLI flag that fills submission_template.csv from MILP base case results using existing submission_outputs()
- Added --team-name, --category, --report-file CLI args for team metadata at submission time
- Created src/charts.py with plot_pareto_frontier() — line+scatter chart with labeled axes, grid, and annotated min-cost/min-emissions endpoints
- Wired Pareto chart into --pareto CLI flag, saves to outputs/charts/pareto_frontier.png at 150 DPI

## Task Commits

Each task was committed atomically:

1. **Task 1: Generate submission CSV from MILP base case** - `0e27d3d` (feat)
2. **Task 2: Generate Pareto frontier chart** - `4e796f7` (feat)

## Files Created/Modified
- `src/charts.py` - New file: plot_pareto_frontier() with Agg backend, 150 DPI
- `run.py` - Added --submit, --team-name, --category, --report-file flags; added chart generation in --pareto block
- `outputs/submission/submission_template.csv` - Populated with MILP base case values

## Decisions Made
- Submission CSV preserves original 4-column template format (Header Name, Data Type, Units, Submission) — matches given_data exactly
- Charts use matplotlib Agg backend to avoid Tkinter issues in headless/CLI mode
- Pareto chart annotates both endpoints (min-cost base case and min-emissions point) for clarity

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Ready for 06-02-PLAN.md (fleet composition bars + safety comparison table chart)
- src/charts.py established as chart module — 06-02 will add plot_fleet_composition() and plot_safety_comparison()
- Agg backend and 150 DPI pattern established for all charts

---
*Phase: 06-submission-charts*
*Completed: 2026-02-06*
