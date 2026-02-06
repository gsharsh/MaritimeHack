# Constraints

## Mathematical Formulation

The optimisation is a **Binary Integer Linear Program (MILP)**.

**Decision variables:** `x_i in {0, 1}` for each vessel i = 1..108, where `x_i = 1` means vessel i is selected.

**Objective:** `minimize SUM(x_i * final_cost_i)`

---

## Hard Constraints (always enforced)

### 1. Demand Coverage (Capacity)

```
SUM(x_i * dwt_i) >= 4,576,667 tonnes
```

The combined deadweight tonnage of selected vessels must meet or exceed Singapore's monthly bunker fuel demand.

- **Binding in base case** -- selected fleet DWT = 4,577,756 t (only 1,089 t of slack)
- **Shadow price** -- ~$4.19 per additional tonne of required capacity

### 2. Average Safety Score

```
SUM(x_i * (safety_i - threshold)) >= 0
```

The fleet-average safety score must meet or exceed the minimum threshold (default 3.0). The constraint is **linearised** to avoid a nonlinear ratio (average = sum/count), which keeps the problem solvable as a standard MILP.

- **Non-binding in base case** -- achieved average = 3.24 vs threshold = 3.0
- **Becomes binding** at threshold >= 3.5, driving cost increases of 5--18%

### 3. Fuel Diversity (Supply Chain Resilience)

```
For each fuel type f in {Distillate, LNG, Methanol, Ethanol, Ammonia, Hydrogen, LPG(Propane), LPG(Butane)}:
    SUM(x_i where fuel_type_i = f) >= 1
```

At least one vessel of each of the 8 fuel types must be selected, ensuring no single-fuel dependency.

- **Always binding** -- some fuel types (Hydrogen, Ethanol) have very few vessels, forcing selection of otherwise expensive ships
- **Cost of diversity** -- relaxing this constraint saves ~$1.1M (5.7% cost reduction), but concentrates supply-chain risk

### 4. Binary Selection (Implicit)

```
x_i in {0, 1}  for all i
```

Each vessel is either fully selected or not; no fractional selection.

---

## Soft / Optional Constraints (used in sensitivity analysis)

### 5. CO2-Equivalent Emissions Cap (Pareto Analysis)

```
SUM(x_i * CO2eq_i) <= epsilon
```

Used in the epsilon-constraint method to trace the cost--emissions Pareto frontier. Progressively tightening epsilon from 13,095 t (unconstrained) to 7,521 t (minimum achievable) reveals the marginal abatement cost curve.

- **Marginal abatement cost** ranges from ~$21/tCO2eq (cheap initial reductions) to $3,839/tCO2eq (aggressive decarbonisation)

---

## Parameter Ranges Explored in Sensitivity

| Parameter | Base Case | Range Tested | Effect |
|-----------|-----------|--------------|--------|
| Safety threshold | 3.0 | 3.0 -- 4.5 | Fleet cost +5% to +18%; fleet size +2 to +5 vessels |
| Carbon price | $80/tCO2eq | $80 -- $200 | Fleet composition shifts toward green fuels above $120/t |
| CO2 cap | None (unconstrained) | 7,521 -- 13,095 t | Traces full Pareto frontier |
| Fuel diversity | Required (all 8 types) | On / Off | $1.1M cost of resilience |
| Demand | 4,576,667 t | +/-10% | Fleet size changes by 2--4 vessels |

---

## Solver Details

- **Engine:** PuLP with COIN-OR CBC (Branch-and-Cut)
- **Optimality:** Provably optimal integer solutions (not heuristic)
- **Scale:** 108 binary variables, 4 constraint families -- solves in <1 second
- **Feasibility:** Returns empty fleet if no combination of vessels can satisfy all constraints simultaneously
