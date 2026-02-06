---
phase: 05-pareto-frontier
plan: 01
status: complete
---

# 05-01 Summary: Epsilon-Constraint Pareto Frontier

## Tasks Completed: 2/2

### Task 1: Add optional CO2eq cap to select_fleet_milp()
- **File:** `src/optimization.py`
- **Commit:** `2cdc0f7`
- **Change:** Added `co2_cap: float | None = None` parameter. When not None, adds MILP constraint `sum(co2eq_i * x_i) <= co2_cap`. Existing behavior unchanged when `co2_cap=None`.

### Task 2: Implement run_pareto_sweep() with shadow carbon prices
- **File:** `src/sensitivity.py`
- **Commit:** `4d516f7`
- **Change:** Added `_solve_min_co2()` helper (min-CO2eq MILP), `run_pareto_sweep()` (15-point epsilon-constraint sweep with shadow prices), and `format_pareto_table()` (readable DataFrame output).

## Verification Results
- [x] `python -m pytest tests/ -v` -- 42/42 passed
- [x] All imports succeed (`select_fleet_milp`, `run_pareto_sweep`, `format_pareto_table`)
- [x] `select_fleet_milp()` has `co2_cap` parameter (default: `None`)
- [x] `run_pareto_sweep()` returns list of dicts with `shadow_carbon_price` field

## Deviations
None. Plan executed as specified.

## Files Modified
- `src/optimization.py` -- added `co2_cap` parameter and CO2eq constraint
- `src/sensitivity.py` -- added `_solve_min_co2()`, `run_pareto_sweep()`, `format_pareto_table()`
