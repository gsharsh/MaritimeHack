# MILP vs Min-Max Robust Fleet — Comparison Summary

This document compares two optimization runs:
- **CBC MILP (no min-max)**: Single-scenario cost minimization at base carbon price and safety threshold.
- **Min-Max MILP**: Robust optimization minimizing worst-case cost across multiple stress scenarios (base, safety stress, carbon stress, joint stress).

---

## 1. Base case fleet metrics

| Metric | CBC MILP | Min-Max MILP |
|--------|----------|--------------|
| Fleet size | 21 | 22 |
| Total cost (USD) | $19,706,494 | $20,765,143 |
| Total DWT | 4,577,756 | 4,580,084 |
| Avg safety score | 3.24 | 4.00 |
| Total CO2eq (tonnes) | 13,095 | 11,756 |
| Total fuel (tonnes) | 4,600 | 4,630 |

**Note:** Min-max selects a fleet that minimizes the worst-case cost across scenarios; base-scenario cost may be higher than the pure MILP base-case fleet, but the fleet is more resilient to stress scenarios.

---

## 2. Carbon price sensitivity (fixed fleet)

Sensitivity evaluates the **same** selected fleet at different carbon prices ($80, $120, $160, $200/tCO2eq).

### CBC MILP

| Carbon price ($/t) | Total cost (USD) | CO2eq (t) | Fleet size |
| --- | --- | --- | --- |
| 80.0 | 19706493.720250208 | 13095.277228879191 | 21.0 |
| 120.0 | 20230304.809405375 | 13095.277228879191 | 21.0 |
| 160.0 | 20754115.898560543 | 13095.277228879191 | 21.0 |
| 200.0 | 21277926.987715703 | 13095.277228879191 | 21.0 |

### Min-Max MILP

| Carbon price ($/t) | Total cost (USD) | CO2eq (t) | Fleet size |
| --- | --- | --- | --- |
| 80.0 | 20765142.645192135 | 11755.80055165016 | 22.0 |
| 120.0 | 21235374.667258132 | 11755.80055165016 | 22.0 |
| 160.0 | 21705606.689324144 | 11755.80055165016 | 22.0 |
| 200.0 | 22175838.711390153 | 11755.80055165016 | 22.0 |

---

## 3. Safety threshold sensitivity (fixed fleet)

Sensitivity evaluates the **same** selected fleet at different minimum safety thresholds.

### CBC MILP

| safety_threshold | total_cost_usd | total_co2e_tonnes | fleet_size | avg_safety_score |
| --- | --- | --- | --- | --- |
| 2.5 | 19706493.720250208 | 13095.277228879191 | 21.0 | 3.238095238095238 |
| 3.0 | 19706493.720250208 | 13095.277228879191 | 21.0 | 3.238095238095238 |
| 3.5 | 19706493.720250208 | 13095.277228879191 | 21.0 | 3.238095238095238 |
| 4.0 | 19706493.720250208 | 13095.277228879191 | 21.0 | 3.238095238095238 |
| 4.5 | 19706493.720250208 | 13095.277228879191 | 21.0 | 3.238095238095238 |

### Min-Max MILP

| safety_threshold | total_cost_usd | total_co2e_tonnes | fleet_size | avg_safety_score |
| --- | --- | --- | --- | --- |
| 2.5 | 20765142.645192135 | 11755.80055165016 | 22.0 | 4.0 |
| 3.0 | 20765142.645192135 | 11755.80055165016 | 22.0 | 4.0 |
| 3.5 | 20765142.645192135 | 11755.80055165016 | 22.0 | 4.0 |
| 4.0 | 20765142.645192135 | 11755.80055165016 | 22.0 | 4.0 |
| 4.5 | 20765142.645192135 | 11755.80055165016 | 22.0 | 4.0 |

---

## 4. Charts generated

### CBC MILP (test 1)

- Main charts: `outputs/test_milp/charts`
  - `carbon_price_sweep_milp.png`
  - `fleet_composition_milp.png`
  - `macc_milp.png`, `macc_full_range_milp.png`
  - `pareto_frontier_milp.png`
  - `safety_comparison_milp.png`
- Sensitivity plots: `outputs/test_milp/sensitivity/plots` (e.g. `carbon_price_sensitivity_milp.png`, `macc_milp.png`, `tornado_analysis_milp.png`, etc.)

### Min-Max MILP (test 2)

- Main charts: `outputs/test_minmax/charts`
  - `carbon_price_sweep_minmax.png`
  - `fleet_composition_minmax.png`
  - `macc_minmax.png`, `macc_full_range_minmax.png`
  - `pareto_frontier_minmax.png`
  - `safety_comparison_minmax.png`
- Sensitivity plots: `outputs/test_minmax/sensitivity/plots` (e.g. `carbon_price_sensitivity_minmax.png`, `macc_minmax.png`, `tornado_analysis_minmax.png`, etc.)

---

## 5. Summary

- **CBC MILP** minimizes cost for the base scenario only; the fleet is optimal for current assumptions but may perform worse under higher carbon prices or stricter safety.
- **Min-Max MILP** chooses a fleet that limits the worst-case cost across several stress scenarios, at the cost of potentially higher base-scenario cost.
- Sensitivity analysis (carbon price sweep, safety sweep) shows how each chosen fleet behaves when assumptions change, without re-optimizing.
