# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-06)

**Core value:** Produce a correct, optimal fleet selection via MILP that minimizes total cost while satisfying all constraints — this is the submission answer.
**Current focus:** Phase 5 in progress — Pareto frontier plan 1 complete, plan 2 next

## Current Position

Phase: 5 of 6 (Cost-Emissions Pareto Frontier)
Plan: 1 of 2 in current phase
Status: In progress
Last activity: 2026-02-06 — Completed 05-01-PLAN.md

Progress: ████████░░ 80%

## Performance Metrics

**Velocity:**
- Total plans completed: 8
- Average duration: 3 min
- Total execution time: 23 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 3/3 | 11 min | 4 min |
| 2 | 2/2 | 4 min | 2 min |
| 3 | 1/1 | 3 min | 3 min |
| 4 | 1/1 | 2 min | 2 min |
| 5 | 1/2 | 3 min | 3 min |

**Recent Trend:**
- Last 5 plans: 02-02 (1 min), 03-01 (3 min), 04-01 (2 min), 05-01 (3 min)
- Trend: consistent ~2-3 min/plan

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Delete all placeholder code — start fresh
- Trust teammates for per_vessel.csv, don't implement Steps 0-6
- Test fixtures: minimal, just enough for MILP testing
- per_vessel.csv drops into data/processed/, MILP reads it directly
- All SOP constants in one module (src/constants.py) as single source of truth
- Kept validate_fleet, total_cost_and_metrics, format_outputs, submission_outputs for reuse
- load_per_vessel() auto-falls back to test fixtures when per_vessel.csv absent
- PuLP enabled in requirements.txt, OR-Tools removed
- Linearized safety constraint: sum(safety_i - threshold) >= 0
- Return empty list on infeasible (not raise)
- Column defaults match per_vessel.csv: final_cost, FC_total, CO2eq
- Infeasible exits with sys.exit(1) for clean CLI behavior
- Integer comparison for final_cost, pytest.approx for CO2eq
- Infeasible thresholds shown as INFEASIBLE in sweep table (not omitted)
- CO2eq cap added as optional parameter to existing select_fleet_milp() (not a separate function)
- Min-emissions bound found via dedicated MILP (_solve_min_co2) rather than binary search
- Shadow carbon price = marginal cost per tonne CO2eq reduced between consecutive Pareto points

### Deferred Issues

None yet.

### Blockers/Concerns

- per_vessel.csv dependency on teammates (not yet available)
- Deadline: 7 Feb 2026 09:00 SGT — hours away

## Session Continuity

Last session: 2026-02-06T12:43:00Z
Stopped at: Completed 05-01-PLAN.md — Phase 5 plan 1 of 2
Resume file: None
