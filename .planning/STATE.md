# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-06)

**Core value:** Produce a correct, optimal fleet selection via MILP that minimizes total cost while satisfying all constraints — this is the submission answer.
**Current focus:** ALL PHASES COMPLETE — Ready for production data and submission

## Current Position

Phase: 6 of 6 (Submission & Charts) — COMPLETE
Plan: 2 of 2 in current phase
Status: Phase complete
Last activity: 2026-02-06 — Completed 06-02-PLAN.md

Progress: ██████████ 100%

## Performance Metrics

**Velocity:**
- Total plans completed: 11
- Average duration: 3 min
- Total execution time: 35 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 3/3 | 11 min | 4 min |
| 2 | 2/2 | 4 min | 2 min |
| 3 | 1/1 | 3 min | 3 min |
| 4 | 1/1 | 2 min | 2 min |
| 5 | 2/2 | 6 min | 3 min |
| 6 | 2/2 | 9 min | 5 min |

**Recent Trend:**
- Last 5 plans: 05-01 (3 min), 05-02 (3 min), 06-01 (5 min), 06-02 (4 min)
- Trend: consistent ~3-5 min/plan

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
- Infeasible thresholds shown as INFEASIBLE in sweep table (not omitted)
- CO2eq cap added as optional parameter to existing select_fleet_milp() (not a separate function)
- Min-emissions bound found via dedicated MILP (_solve_min_co2) rather than binary search
- Shadow carbon price = marginal cost per tonne CO2eq reduced between consecutive Pareto points
- Carbon price adjustment via final_cost recalculation: final_cost - carbon_cost + CO2eq * new_price
- Graceful fallback when carbon_cost column missing: compute as CO2eq * CARBON_PRICE(80)
- Submission CSV preserves 4-column template format (Header Name, Data Type, Units, Submission)
- Charts use matplotlib Agg backend for headless CLI execution
- --all flag for one-command full output generation

### Deferred Issues

None.

### Blockers/Concerns

- per_vessel.csv dependency on teammates (not yet available)
- Deadline: 7 Feb 2026 09:00 SGT

## Session Continuity

Last session: 2026-02-06T13:11:31Z
Stopped at: Completed 06-02-PLAN.md — All phases complete
Resume file: None
