# Maritime Hackathon 2026 — Nickolas's Optimization Module

## What This Is

MILP-based fleet optimization for the Maritime Hackathon 2026 Smart Fleet Selection challenge. Selects the minimum-cost fleet of ships to transport bunker fuel from Singapore to Australia West Coast, subject to DWT demand, safety, and fuel diversity constraints. Includes Pareto frontier analysis (cost vs emissions) and safety threshold comparison.

## Core Value

Produce a correct, optimal fleet selection via MILP that minimizes total cost while satisfying all constraints — this is the submission answer.

## Requirements

### Validated

- ✓ Project structure with src/, config/, data/, tests/ — existing
- ✓ Cost model functions (fuel, carbon, ownership, risk) — existing (`src/cost_model.py`)
- ✓ Data loading from vessel_movements_dataset.csv — existing (`src/data_loader.py`)
- ✓ Sensitivity analysis framework — existing (`src/sensitivity.py`)
- ✓ Basic unit tests for cost model and validation — existing (`tests/`)

### Active

- [ ] **MILP base fleet optimizer** (Step 7): Replace greedy solver with PuLP MILP in `src/optimization.py`. Minimize total fleet cost subject to: DWT >= 4,576,667, avg safety >= 3.0, all 8 fuel types represented. Binary decision per ship (108 vessels).
- [ ] **Cost-Emissions Pareto frontier** (Step 8): Epsilon-constraint method sweeping emissions cap from max to min in 15 steps. Compute shadow carbon prices at each point. Output Pareto curve chart (matplotlib) and fleet composition stacked bars.
- [ ] **Safety threshold comparison** (Step 10): Re-run MILP at safety >= 4.0, compare fleet cost/composition/CO2eq vs base case (safety >= 3.0). Output comparison table.
- [ ] **Test fixtures from checkpoint vessels**: Build test data from 5 SOP checkpoint vessels (10102950, 10657280, 10791900, 10522650, 10673120) to validate MILP before real per_vessel.csv arrives.
- [ ] **Submission CSV generation**: Fill `submission_template.csv` with base case results.
- [ ] **Charts**: Pareto frontier chart, fleet composition stacked bars, safety comparison table — all matplotlib, saved to `outputs/`.

### Out of Scope

- Steps 0-6 (data processing pipeline) — teammates A+B's responsibility
- Step 9 (carbon price sensitivity) — Teammate C's responsibility
- Case paper writing — team effort after results are ready
- Presentation slides — team effort after results are ready
- Refactoring existing cost model code — not Nickolas's task

## Context

**Hackathon:** Maritime Hackathon 2026, organized by MPA Singapore. Submission deadline: 7 Feb 2026 09:00 SGT.

**Team structure:** Nickolas handles Steps 7, 8, 10 (optimization). Teammates A+B handle Steps 0-6 (data processing → per_vessel.csv). Teammate C handles Step 9 (carbon price sensitivity).

**Data handoff:** Teammates will produce `data/processed/per_vessel.csv` with 108 rows containing: vessel_id, dwt, safety_score, main_engine_fuel_type, FC_me_total, FC_ae_total, FC_ab_total, FC_total, CO2eq, fuel_cost, carbon_cost, monthly_capex, total_monthly, adj_rate, risk_premium, final_cost.

**Existing code status:** Current `src/optimization.py` has a greedy solver — this will be replaced with PuLP MILP. The `build_and_solve_milp()` function from the SOP is the reference implementation.

**Key constants:**
- MONTHLY_DEMAND = 4,576,667 tonnes (54.92M / 12, from MPA AR 2024 page 10)
- SAFETY_THRESHOLD = 3.0 (base case), 4.0 (comparison)
- CARBON_PRICE = 80 USD/tCO2e (base case)
- CRF = 0.088827
- 8 fuel types: DISTILLATE FUEL, LNG, Methanol, Ethanol, Ammonia, Hydrogen, LPG (Propane), LPG (Butane)

**Verification checkpoints:** 5 checkpoint vessels in Nickolas.md with expected values at every calculation stage. Use these to validate the pipeline.

## Constraints

- **Timeline**: Submission due 7 Feb 2026 09:00 SGT — hours away, must ship fast
- **Dependency**: Requires per_vessel.csv from teammates (not yet available) — build with test fixtures first
- **Tech stack**: Python, PuLP for MILP, matplotlib for charts, pandas for data
- **Submission format**: Must match `given_data/submission_template.csv` column order exactly

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| PuLP MILP over greedy | MILP guarantees optimal solution; greedy was placeholder | — Pending |
| Replace src/optimization.py | Keep codebase clean, one optimizer module | — Pending |
| matplotlib for charts | Standard, lightweight, good for static exports | — Pending |
| per_vessel.csv at data/processed/ | Clean separation: teammates write, Nickolas reads | — Pending |
| Test with 5 checkpoint vessels | Validate MILP before real data arrives | — Pending |
| MONTHLY_DEMAND = 4,576,667 | SOP value from MPA AR 2024 p10 (54.92M / 12) | — Pending |

---
*Last updated: 2026-02-06 after initialization*
