# Robust Fleet Optimization and Sensitivity Analysis

This document describes the **min-max robust fleet optimization** and **fixed-fleet sensitivity analysis** added to the MaritimeHack codebase. These features extend the baseline cost-minimising MILP without replacing it.

---

## 1. Overview

### What was built

| Feature | Purpose |
|---------|---------|
| **Min-max robust MILP** | Select a single fleet that minimises worst-case total cost across multiple stress scenarios (carbon price and safety threshold) |
| **Fixed-fleet sensitivity** | Evaluate a chosen fleet at different safety thresholds and carbon prices without re-optimising |
| **CLI integration** | `run.py --robust` for robust fleet; `run_sensitivity_analysis.py` uses fixed-fleet sweeps |

### Design principles

- **Additive, not disruptive** — existing `select_fleet_milp`, sensitivity logic, and submission flow remain unchanged
- **Same data contract** — `per_vessel.csv` and `REQUIRED_COLUMNS` are unchanged
- **Deterministic** — no probabilities or CVaR; purely worst-case min-max

---

## 2. Min-max robust fleet optimization

### Motivation

The baseline MILP minimises cost under a single scenario (e.g. carbon $80/t, safety ≥ 3.0). If carbon price or safety requirements rise, that fleet may become expensive or infeasible. The robust formulation selects **one fleet** that performs well across several stress scenarios.

### Mathematical formulation

**Variables:**
- \( x_i \in \{0,1\} \) — vessel \( i \) selected (binary)
- \( Z \geq 0 \) — worst-case fleet cost (continuous)

**Parameters:**
- \( c_{i,s} \) — cost of vessel \( i \) under scenario \( s \)
- \( D \) — cargo demand (tonnes)
- \( \tau \) — strictest safety threshold across scenarios
- \( \text{dwt}_i \), \( \text{safety}_i \), fuel type per vessel

**Objective:**
\[
\min Z
\]

**Constraints:**
- For each scenario \( s \): \( \sum_i c_{i,s} x_i \leq Z \)
- DWT: \( \sum_i \text{dwt}_i x_i \geq D \)
- Safety (linearised): \( \sum_i (\text{safety}_i - \tau) x_i \geq 0 \)
- Fuel diversity: \( \geq 1 \) vessel per `main_engine_fuel_type`

The fleet must be feasible in **all** scenarios; the safety constraint uses the **strictest** threshold so the chosen fleet satisfies every scenario.

### Scenario definition

Default scenarios in `src/optimization.py`:

| Scenario | Carbon price ($/tCO2e) | Min. avg. safety |
|----------|------------------------|-------------------|
| `base` | 80 | 3.0 |
| `safety_stress` | 80 | 4.0 |
| `carbon_stress` | 160 | 3.0 |
| `joint_stress` | 160 | 4.0 |

Per-vessel cost under each scenario is computed by adjusting only the **carbon** component:

\[
c_{i,s} = \text{final\_cost}_i - \text{carbon\_cost}_i + \text{CO2eq}_i \times \text{scenario\_carbon\_price}
\]

Fuel cost, CAPEX, and risk premium are unchanged; vessel attributes (DWT, safety, fuel type) are unchanged.

### API

**`select_fleet_minmax_milp`** (`src/optimization.py`)

```python
def select_fleet_minmax_milp(
    df_per_vessel: pd.DataFrame,
    scenarios: dict[str, dict[str, float]],
    cargo_demand: float,
    require_all_fuel_types: bool = True,
) -> tuple[list[int], float | None]:
    """
    Returns (selected_vessel_ids, Z_value).
    Returns ([], None) if infeasible.
    """
```

**Helpers:**
- `build_scenario_cost_matrix(df, scenarios)` → DataFrame with per-vessel cost per scenario
- `fleet_costs_by_scenario(df, scenarios, selected_ids)` → `dict[scenario_name, total_cost]` for validation/reporting

**Constant:** `DEFAULT_ROBUST_SCENARIOS` — the four scenarios above.

---

## 3. Fixed-fleet sensitivity analysis

### Motivation

Sensitivity analysis can either:
- **Re-optimise** at each parameter value (different fleet at each point), or
- **Fix the fleet** and evaluate it at each parameter value.

The fixed-fleet approach answers: “Given the fleet we chose, how does cost/CO2eq change if carbon price or safety requirements change?” There is no reallocation; fleet size and composition stay constant.

### Safety threshold sensitivity (fixed fleet)

**Input:** Base fleet (e.g. from `select_fleet_milp`), list of thresholds (e.g. [2.5, 3.0, 3.5, 4.0, 4.5]).

**Behaviour:** At each threshold, check whether the fleet’s average safety ≥ threshold. Cost and CO2eq are **constant** (same fleet). Fleet size is **constant**.

**Output:** For each threshold: `feasible` (bool), same `total_cost_usd`, same `total_co2e_tonnes`, same `fleet_size`.

### Carbon price sensitivity (fixed fleet)

**Input:** Base fleet, list of carbon prices (e.g. [80, 120, 160, 200]).

**Behaviour:** At each price, recompute total cost (carbon component only). CO2eq and fleet size are **constant** (same fleet, same emissions).

**Output:** For each price: `total_cost_usd` (increases with price), same `total_co2e_tonnes`, same `fleet_size`.

### API

**`run_safety_sweep_fixed_fleet`** (`src/sensitivity.py`)

```python
def run_safety_sweep_fixed_fleet(
    df: pd.DataFrame,
    selected_ids: list[int],
    thresholds: list[float] | None = None,
) -> list[dict]:
    """Evaluate fixed fleet at each threshold. No re-optimisation."""
```

**`run_carbon_price_sweep_fixed_fleet`** (`src/sensitivity.py`)

```python
def run_carbon_price_sweep_fixed_fleet(
    df: pd.DataFrame,
    selected_ids: list[int],
    carbon_prices: list[float] | None = None,
) -> list[dict]:
    """Evaluate fixed fleet at each carbon price. Cost recomputed; CO2eq constant."""
```

---

## 4. CLI usage

### Run robust optimization

```bash
# Robust fleet only
python run.py --robust

# Robust fleet + fill submission CSV from robust fleet
python run.py --robust --submit
```

**Outputs:**
- `outputs/results/robust_fleet.csv` — selected vessels (full rows)
- `outputs/results/robust_fleet_ids.csv` — vessel IDs
- Console: worst-case cost Z, cost by scenario, base-scenario metrics

The baseline MILP still runs and writes `chosen_fleet.csv`; the robust path adds `robust_fleet.csv` when `--robust` is set.

### Run sensitivity analysis (fixed fleet)

```bash
python run_sensitivity_analysis.py
```

**Behaviour:**
1. Solve base-case MILP once
2. Safety sweep: evaluate that fleet at thresholds 2.5–4.5 (fixed fleet)
3. Carbon sweep: evaluate that fleet at $80/$120/$160/$200 (fixed fleet)
4. Write CSVs and generate all sensitivity plots

**Outputs:**
- `outputs/sensitivity/base_case.csv`
- `outputs/sensitivity/safety_sensitivity.csv`
- `outputs/sensitivity/carbon_price_sensitivity.csv`
- `outputs/sensitivity/plots/*.png` (tornado, Pareto, cost vs safety, carbon sensitivity, fuel mix, MACC, dashboard)
- `outputs/sensitivity/sensitivity_summary_*.txt`

### Run re-optimising sweeps (run.py)

`run.py` still supports the **re-optimising** sweeps (different fleet at each parameter):

```bash
python run.py --sweep --pareto --carbon-sweep
```

These use `run_safety_sweep` and `run_carbon_price_sweep` (not the fixed-fleet versions) and write to `outputs/charts/` (fleet_composition, safety_comparison, pareto_frontier, macc, carbon_price_sweep).

---

## 5. Output files reference

| Content | Location |
|---------|----------|
| Baseline fleet | `outputs/results/chosen_fleet.csv`, `chosen_fleet_ids.csv` |
| Robust fleet | `outputs/results/robust_fleet.csv`, `robust_fleet_ids.csv` |
| Results summary (narrative) | `outputs/RESULTS_SUMMARY.md` |
| Sensitivity CSVs | `outputs/sensitivity/base_case.csv`, `safety_sensitivity.csv`, `carbon_price_sensitivity.csv` |
| Sensitivity plots | `outputs/sensitivity/plots/*.png` |
| Run.py charts (sweep/pareto/carbon) | `outputs/charts/*.png` |
| Submission | `outputs/submission/submission_template.csv` |

---

## 6. Tests

**`tests/test_robust_milp.py`** covers:

- `select_fleet_minmax_milp` returns non-empty sorted IDs when feasible
- Returned fleet passes `validate_fleet` for strictest scenario
- Worst-case cost equals optimal Z
- Returns `([], None)` when infeasible
- `build_scenario_cost_matrix` shape and base-scenario alignment
- `fleet_costs_by_scenario` matches sum of cost matrix

Run: `pytest tests/test_robust_milp.py -v`

---

## 7. Relationship to existing pipeline

| Component | Unchanged | New/Modified |
|-----------|-----------|--------------|
| `select_fleet_milp` | ✓ | — |
| `per_vessel.csv` contract | ✓ | — |
| `run_sensitivity_analysis.py` | — | Uses fixed-fleet sweeps |
| `run.py` | ✓ (baseline path) | Adds `--robust` branch |
| `sensitivity.py` | `run_safety_sweep`, `run_carbon_price_sweep` kept | Adds `run_*_fixed_fleet` |
| `optimization.py` | — | Adds robust functions and helpers |

---

## 8. Config (optional)

Scenario set can be extended by passing a custom `scenarios` dict to `select_fleet_minmax_milp`. A future enhancement could read scenarios from `config/params.yaml` (e.g. `robust_scenarios`).
