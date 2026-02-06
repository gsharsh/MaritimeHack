# Architecture

**Analysis Date:** 2026-02-06

## Pattern Overview

**Overall:** Layered/Modular Data Processing Pipeline (Monolithic)

**Key Characteristics:**
- Sequential data transformation pipeline
- Functional style (no classes, pure functions)
- Configuration-driven parameters
- Single-process, deterministic optimization

## Layers

**Data Access Layer:**
- Purpose: Load and validate external data sources
- Contains: CSV/YAML/JSON readers, column mapping, schema validation
- Location: `src/data_loader.py`
- Depends on: pandas, pyyaml, filesystem
- Used by: Entry point (`run.py`)

**Cost Model Layer:**
- Purpose: Compute per-ship economic costs
- Contains: Fuel consumption, CO2 emissions, fuel cost, ownership cost, risk premium
- Location: `src/cost_model.py`
- Depends on: pandas (row data), global parameters dict
- Used by: Entry point (`run.py`), optimization layer

**Optimization Layer:**
- Purpose: Fleet selection algorithm and constraint validation
- Contains: Greedy selection, constraint validation, output formatting
- Location: `src/optimization.py`
- Depends on: pandas DataFrames with cost columns
- Used by: Entry point (`run.py`), sensitivity layer

**Sensitivity Layer:**
- Purpose: Parametric analysis over safety constraints
- Contains: Re-run optimization for multiple thresholds
- Location: `src/sensitivity.py`
- Depends on: Optimization layer functions
- Used by: Entry point (`run.py`)

**Utility Layer:**
- Purpose: Shared helpers for paths and voyage calculations
- Contains: Path resolution, voyage duration calculation, constants
- Location: `src/utils.py`
- Depends on: Python pathlib only
- Used by: All layers

## Data Flow

**Fleet Optimization Pipeline (`run.py` → main()):**

1. Parse CLI arguments (custom paths, sensitivity flag)
2. Load config from `config/params.yaml` → cargo demand, constraints
3. Load ships from CSV → `src/data_loader.py::load_ships()`
4. Load global parameters from YAML → emission factors, fuel prices, CAPEX
5. Compute voyage hours per ship → `src/utils.py::voyage_hours_from_nm_and_speed()`
6. Compute per-ship costs → `src/cost_model.py::ship_total_cost_usd()` (fuel, carbon, ownership, risk)
7. Run greedy fleet selection → `src/optimization.py::select_fleet_greedy()`
8. Validate fleet constraints → `src/optimization.py::validate_fleet()`
9. Aggregate fleet metrics → `src/optimization.py::total_cost_and_metrics()`
10. Optionally run sensitivity analysis → `src/sensitivity.py::run_sensitivity()`
11. Write results to `outputs/`

**State Management:**
- Stateless - all data passes through function parameters
- No persistent in-memory state between runs
- File-based I/O only (CSV in, CSV/text out)

## Key Abstractions

**Cost Functions:**
- Purpose: Decompose ship cost into independent components
- Examples: `fuel_consumption_tonnes()`, `co2e_tonnes()`, `fuel_cost_usd()`, `amortized_ownership_per_month_usd()`, `risk_premium_usd()`
- Location: `src/cost_model.py`
- Pattern: Functional decomposition (each cost type = separate function)

**Fleet Validation:**
- Purpose: Check fleet satisfies all constraints
- Examples: `validate_fleet()` returns `(bool, list[str])` tuple
- Location: `src/optimization.py`
- Pattern: Constraint validation with error messages

**DataFrame as Data Model:**
- Purpose: Ship records with computed columns
- Pattern: Progressively enriched DataFrame (raw → voyage_hours → cost columns → selection)

## Entry Points

**CLI Entry:**
- Location: `run.py`
- Triggers: `python run.py [--ships PATH] [--global-params PATH] [--config PATH] [--sensitivity] [--out-dir PATH]`
- Responsibilities: Parse args, orchestrate pipeline, write output

**Test Entry:**
- Location: `tests/test_cost_model.py`, `tests/test_optimization.py`
- Triggers: `pytest`

**Notebook Entry:**
- Location: `notebooks/exploration.ipynb`
- Triggers: Jupyter notebook server

## Error Handling

**Strategy:** Minimal - print warnings and continue with defaults

**Patterns:**
- Silent fallbacks: missing config returns empty dict, functions use `.get()` with defaults
- `load_ships()` validates required columns exist via `REQUIRED_SHIP_COLUMNS`
- No try/catch in cost calculation pipeline
- Validation errors returned as list of strings from `validate_fleet()`

## Cross-Cutting Concerns

**Logging:**
- `print()` statements for status output
- No logging framework

**Validation:**
- Required columns check in `src/data_loader.py`
- Fleet constraint validation in `src/optimization.py::validate_fleet()`
- No input validation on individual ship rows

**Configuration:**
- Multi-level YAML hierarchy (project config + global params + CLI overrides)

---

*Architecture analysis: 2026-02-06*
*Update when major patterns change*
