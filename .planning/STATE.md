# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-06)

**Core value:** Produce a correct, optimal fleet selection via MILP that minimizes total cost while satisfying all constraints — this is the submission answer.
**Current focus:** v2.0 Submission Polish — Shadow prices, enhanced charts, case paper & slides

## Current Position

Phase: 9 of 10 (Case Paper & Slides)
Plan: 1 of 1 in current phase
Status: Phase complete
Last activity: 2026-02-06 — Completed 09-01-PLAN.md

Progress: ██████████░░░░ 70%

## Performance Metrics

**Velocity:**
- Total plans completed: 14
- Average duration: 4 min
- Total execution time: 50 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 3/3 | 11 min | 4 min |
| 2 | 2/2 | 4 min | 2 min |
| 3 | 1/1 | 3 min | 3 min |
| 4 | 1/1 | 2 min | 2 min |
| 5 | 2/2 | 6 min | 3 min |
| 6 | 2/2 | 9 min | 5 min |
| 7 | 1/1 | 5 min | 5 min |
| 8 | 1/1 | 5 min | 5 min |
| 9 | 1/1 | 5 min | 5 min |

**Recent Trend:**
- Last 5 plans: 06-02 (4 min), 07-01 (5 min), 08-01 (5 min), 09-01 (5 min)
- Trend: consistent ~5 min/plan

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
- DWT shadow price via +1% perturbation, safety shadow price via +0.1 perturbation
- Diversity what-if toggles require_all_fuel_types True vs False
- --shadow-prices flag added to --all convenience group
- MACC bars sorted cheapest-first, color thresholds: <$100 green, $100-$500 yellow, >$500 red
- Carbon sweep chart: dual subplot (cost + emissions), infeasible shown as text
- All deliverable numbers use {placeholder} syntax for production-run fill
- Case paper structured as 3 sections matching hackathon requirements

### Deferred Issues

None.

### Blockers/Concerns

- per_vessel.csv dependency on teammates (not yet available)
- Deadline: 7 Feb 2026 09:00 SGT

### Roadmap Evolution

- Milestone v1.0 created: MILP fleet optimizer, 6 phases (Phase 1-6)
- Milestone v1.0 shipped: 2026-02-06, 11 plans, 35 min total
- Milestone v2.0 created: Submission polish, 4 phases (Phase 7-10)

## Session Continuity

Last session: 2026-02-06
Stopped at: Completed 09-01-PLAN.md (Phase 9 complete)
Resume file: None
