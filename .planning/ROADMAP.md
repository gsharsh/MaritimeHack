# Roadmap: Maritime Hackathon 2026 — Nickolas's Optimization Module

## Overview

MILP-based fleet optimization for the Smart Fleet Selection challenge. Starting from per_vessel.csv (produced by teammates), build a PuLP MILP optimizer to select the minimum-cost fleet, then run sensitivity analyses (safety thresholds, Pareto frontier, carbon price sweep) and generate submission outputs.

## Domain Expertise

None

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Clean Slate & Data Foundation** - Delete placeholder code, set up lookup tables/constants, test fixtures, per_vessel.csv adapter
- [x] **Phase 2: MILP Fleet Optimizer** - Replace greedy solver with PuLP MILP (Step 7)
- [x] **Phase 3: Validation** - Verify MILP against 5 checkpoint vessels and expected ranges
- [x] **Phase 4: Safety Threshold Sweep** - Re-run MILP at 3.0/3.5/4.0/4.5, compare results (Step 10)
- [ ] **Phase 5: Cost-Emissions Pareto Frontier** - Epsilon-constraint method, shadow carbon prices, carbon price sweep (Step 8)
- [ ] **Phase 6: Submission & Charts** - Fill submission CSV, Pareto chart, fleet bars, safety table

## Phase Details

### Phase 1: Clean Slate & Data Foundation
**Goal**: Remove existing placeholder code (wrong constants, wrong approach), set up correct lookup tables from calculation_factors.xlsx, build minimal test fixtures from 5 SOP checkpoint vessels, create adapter to load per_vessel.csv from data/processed/
**Depends on**: Nothing (first phase)
**Research**: Unlikely (all values specified in SOP, existing code to delete is known)
**Plans**: TBD

Specifics:
- Delete innards of: src/optimization.py (greedy solver), src/cost_model.py (wrong GWP/CRF), src/data_loader.py (wrong approach), src/sensitivity.py (too basic)
- Hardcode lookup tables: Cf emission factors, LCV, fuel prices, CAPEX brackets/multipliers, safety adjustment rates, LLAF table
- Fix constants: MONTHLY_DEMAND=4,576,667, CRF=0.088827, GWP CH4=28/N2O=265, carbon_price=80
- Build test fixtures: 5 checkpoint vessels (10102950, 10657280, 10791900, 10522650, 10673120) with per_vessel.csv columns using SOP expected values
- Data adapter: load per_vessel.csv from data/processed/, fall back to test fixtures if not found

Plans:
- [x] 01-01: Delete placeholder code & create constants/lookup tables (2 tasks) ✓
- [x] 01-02: Build test fixtures & per_vessel.csv adapter (2 tasks) ✓
- [x] 01-03: Update run.py, config, verify end-to-end (2 tasks) ✓

### Phase 2: MILP Fleet Optimizer
**Goal**: Replace select_fleet_greedy() with PuLP MILP. Binary decision variables x_i ∈ {0,1}, objective min Σ x_i × final_cost_i, constraints: DWT >= 4,576,667, Σ x_i × (safety_i - 3.0) >= 0, ∀ fuel_type Σ x_i >= 1. Solve with CBC, extract selected fleet.
**Depends on**: Phase 1
**Research**: Likely (PuLP is new to codebase — need to verify API patterns for binary MILP)
**Research topics**: PuLP LpProblem setup, LpVariable Binary type, PULP_CBC_CMD solver options, extracting solution values
**Plans**: TBD

Plans:
- [x] 02-01: TDD — Build select_fleet_milp() with PuLP binary MILP (TDD plan) ✓
- [x] 02-02: Wire MILP into run.py, fix column defaults, add CLI args (2 tasks) ✓

### Phase 3: Validation
**Goal**: Run MILP on test fixtures and verify: (1) each checkpoint vessel's cost matches SOP ±2%, (2) fleet solution falls within expected ranges (25-40 ships, $25M-$40M total, avg safety 3.0-3.5, all 8 fuel types), (3) all constraints satisfied.
**Depends on**: Phase 2
**Research**: Unlikely (comparing numbers against known expected values)
**Plans**: TBD

Plans:
- [x] 03-01: Validation test suite & full regression check (2 tasks) ✓

### Phase 4: Safety Threshold Sweep
**Goal**: Re-run MILP at safety thresholds 3.0, 3.5, 4.0, 4.5. For each, record: fleet size, total cost, avg safety, total CO2eq, fleet composition by fuel type. Output comparison table. Detect infeasible thresholds.
**Depends on**: Phase 3
**Research**: Unlikely (re-runs existing MILP with different constraint parameter)
**Plans**: TBD

Plans:
- [x] 04-01: Implement safety sweep function and wire into CLI (2 tasks) ✓

### Phase 5: Cost-Emissions Pareto Frontier
**Goal**: Epsilon-constraint method: sweep CO2eq cap from fleet-max to fleet-min in 15 steps. At each point solve MILP with additional constraint Σ x_i × CO2eq_i <= epsilon. Record cost/emissions/fleet at each point. Compute shadow carbon price (marginal cost per tonne CO2eq reduced). Also run carbon price sweep at $80/$120/$160/$200 (recomputing final_cost with new carbon_cost before re-solving MILP).
**Depends on**: Phase 3
**Research**: Unlikely (epsilon-constraint is standard OR technique, re-uses existing MILP infrastructure)
**Plans**: TBD

Plans:
- [x] 05-01: Epsilon-constraint Pareto sweep + shadow carbon prices (2 tasks) ✓
- [ ] 05-02: Carbon price sweep + CLI wiring (2 tasks)

### Phase 6: Submission & Charts
**Goal**: Fill submission_template.csv with base case results (matching column order exactly). Generate matplotlib charts: Pareto frontier curve (cost vs CO2eq), fleet composition stacked bars (by fuel type across thresholds), safety comparison table. Save all to outputs/.
**Depends on**: Phase 4, Phase 5
**Research**: Unlikely (matplotlib, pandas, standard patterns)
**Plans**: TBD

Plans:
- [ ] 06-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 (and 5 in parallel) → 6

| Phase | Plans Complete | Status | Completed |
|-------|---------------|--------|-----------|
| 1. Clean Slate & Data Foundation | 3/3 | Complete | 2026-02-06 |
| 2. MILP Fleet Optimizer | 2/2 | Complete | 2026-02-06 |
| 3. Validation | 1/1 | Complete | 2026-02-06 |
| 4. Safety Threshold Sweep | 1/1 | Complete | 2026-02-06 |
| 5. Cost-Emissions Pareto Frontier | 1/2 | In progress | - |
| 6. Submission & Charts | 0/? | Not started | - |
