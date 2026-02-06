# Fleet Selection Results — Summary and Interpretation

This document summarises the optimisation results for the Maritime Hackathon 2026 fleet selection problem: choosing a minimum-cost fleet to move bunker fuel **Singapore → Australia West (Port Hedland)** for one month, and how the selected fleets perform.

---

## 1. Problem and constraints (recap)

| Requirement | Value |
|-------------|--------|
| **Monthly cargo demand** | 4,576,667 tonnes |
| **Minimum average safety score** | ≥ 3.0 (RightShip 1–5, 5 = safest) |
| **Fuel diversity** | At least one vessel per main engine fuel type (8 types) |
| **Per-vessel cost** | Fuel + carbon (CO2eq × price) + amortised CAPEX + risk premium by safety |

The optimizer selects vessels so that **total cost is minimised** while **total DWT ≥ demand**, **average safety ≥ threshold**, and **all fuel types are represented**. Each ship is used at most once.

---

## 2. Baseline fleet (cost-minimising MILP)

The **baseline** is the fleet chosen by a single-scenario MILP: minimise total cost at **carbon price $80/tCO2e** and **safety threshold 3.0**.

### Results

| Metric | Value |
|--------|--------|
| **Fleet size** | 21 vessels |
| **Total DWT** | 4,577,756 tonnes (≥ demand ✓) |
| **Total cost** | **$19,706,494** |
| **Average safety score** | 3.24 |
| **Total CO2eq** | 13,095 tonnes |
| **Total fuel consumption** | 4,600 tonnes |
| **Unique fuel types** | 8 (all required types ✓) |

### Why this fleet performs well

- **Meets demand:** Total DWT exceeds the monthly requirement with minimal slack, so capacity is used efficiently.
- **Cost-efficient:** The MILP explicitly minimises cost (fuel + carbon + CAPEX + risk premium), so this is the cheapest feasible fleet under the base assumptions.
- **Safety:** Average safety 3.24 is above the 3.0 requirement, without over-paying for much higher safety.
- **Fuel diversity:** All eight main-engine fuel types are represented, satisfying the constraint and supporting operational flexibility.
- **Emissions:** CO2eq is a consequence of the cost-minimising choice; the same formulation can be extended with a CO2 cap or Pareto analysis (see sensitivity).

**Outputs:** `outputs/results/chosen_fleet.csv`, `chosen_fleet_ids.csv`.

---

## 3. Robust fleet (min–max across stress scenarios)

The **robust** fleet is chosen by a **min–max** model: one fleet that minimises the **worst-case** total cost over four scenarios, so it stays affordable even if carbon price or safety requirements become stricter.

### Scenarios

| Scenario | Carbon price ($/tCO2e) | Min. avg. safety |
|----------|------------------------|------------------|
| Base | 80 | 3.0 |
| Safety stress | 80 | 4.0 |
| Carbon stress | 160 | 3.0 |
| Joint stress | 160 | 4.0 |

The same fleet must be feasible and cost-conscious in **all** of these (demand, safety ≥ 4.0, fuel diversity). The model minimises **Z** where **Z** is the maximum fleet cost over the four scenarios.

### Results

| Metric | Value |
|--------|--------|
| **Fleet size** | 22 vessels |
| **Total DWT** | 4,580,084 tonnes (≥ demand ✓) |
| **Worst-case cost (Z)** | **$21,705,607** |
| **Base-scenario cost** | $20,765,143 |
| **Average safety score** | 4.0 |
| **Total CO2eq** | 11,756 tonnes |
| **Total fuel consumption** | 4,630 tonnes |
| **Unique fuel types** | 8 ✓ |

**Cost by scenario**

| Scenario | Fleet cost |
|----------|------------|
| Base | $20,765,143 |
| Safety stress | $20,765,143 |
| Carbon stress | $21,705,607 |
| Joint stress | $21,705,607 |

So the **worst case** is **$21.7M** (high carbon and/or high safety); the robust formulation chooses a fleet that keeps this maximum as low as possible.

### Why the robust fleet performs well

- **Resilience:** One fleet remains feasible and cost-bounded in all four scenarios (higher carbon price, higher safety bar, or both). No re-optimisation or different fleet per scenario.
- **Controlled worst case:** The worst-case cost **Z = $21.7M** is the minimum possible maximum over these scenarios; any other feasible fleet would have a higher worst-case cost.
- **Higher baseline safety:** Average safety 4.0 meets even the strictest scenario (4.0) and gives a safety margin vs. the 3.0 requirement.
- **Lower emissions:** 11,756 t CO2eq vs. 13,095 t for the baseline fleet, because the robust solution leans toward vessels that do better under higher carbon price.
- **Narrative:** “Sensitivity analysis → identify stress scenarios → choose a single robust fleet” is a clear, defensible decision story for submission.

**Outputs:** `outputs/results/robust_fleet.csv`, `robust_fleet_ids.csv`.

---

## 4. Sensitivity analysis — what it shows (fixed fleet)

Sensitivity uses the **same** base-case fleet everywhere; there is **no re-optimisation** or reallocation. We only vary the **parameter** (safety threshold or carbon price) and report how **cost** and **CO2eq** behave for that fixed fleet.

### Safety threshold sensitivity (fixed fleet)

The **base fleet (21 vessels)** is evaluated at each safety threshold. Fleet size, cost, and CO2eq are unchanged—we only check whether the fleet still meets the constraint (avg safety ≥ threshold).

| Min. safety | Fleet size | Total cost | CO2eq (t) | Meets constraint? |
|------------|------------|------------|-----------|------------------|
| 2.5 | 21 | $19,706,494 | 13,095 | Yes |
| 3.0 | 21 | $19,706,494 | 13,095 | Yes |
| 3.5 | 21 | $19,706,494 | 13,095 | No (fleet avg 3.24) |
| 4.0 | 21 | $19,706,494 | 13,095 | No |
| 4.5 | 21 | $19,706,494 | 13,095 | No |

**Interpretation:** For thresholds ≤ the fleet’s average safety (3.24), the fleet meets the constraint and cost/CO2eq are constant. For stricter thresholds (3.5 and above), the **same** fleet no longer meets the constraint—we do not reallocate; we only report that it fails at those thresholds.

### Carbon price sensitivity (fixed fleet)

The **same base fleet** is evaluated at each carbon price. Fleet size and **CO2eq are unchanged** (same vessels, same emissions). Only **cost** changes because the carbon component is recomputed at each price.

| Carbon price ($/t) | Fleet size | Total cost | CO2eq (t) |
|-------------------|------------|------------|-----------|
| 80 | 21 | $19,706,494 | 13,095 |
| 120 | 21 | $20,230,305 | 13,095 |
| 160 | 21 | $20,754,116 | 13,095 |
| 200 | 21 | $21,277,927 | 13,095 |

**Interpretation:** Cost increases with carbon price (same emissions × higher price). CO2eq is flat because we are not reallocating to different vessels. This shows “how much would this **chosen** fleet cost if carbon price went up?”

**Plots:** See `outputs/sensitivity/plots/` for tornado, cost vs safety, carbon sensitivity, fuel mix vs carbon price, MACC, and summary dashboard.

---

## 5. How the selected fleets perform — short summary

- **Baseline fleet (21 vessels):**  
  Lowest cost ($19.7M) for the base case (demand 4.58M t, safety ≥ 3.0, $80/t CO2e). Meets all constraints and is optimal for that single scenario.

- **Robust fleet (22 vessels):**  
  Same demand and fuel diversity, but chosen to **minimise worst-case cost** over base, safety stress, carbon stress, and joint stress. Slightly more vessels and higher base-scenario cost ($20.8M vs $19.7M), but **guaranteed** to stay at or below **$21.7M** in any of the four scenarios, with average safety 4.0 and lower CO2eq (11,756 t). Prefer this fleet when you want one submission fleet that is resilient to stricter safety and/or higher carbon prices.

- **Sensitivity:**  
  Fixed base fleet: no reallocation. Safety sweep checks at which thresholds the fleet still meets the constraint (cost/CO2eq constant). Carbon sweep shows how total cost changes with carbon price (CO2eq constant). Supports the narrative that the robust fleet is a prudent choice when future carbon and safety rules are uncertain.

---

## 6. Output files reference

| Content | Location |
|--------|----------|
| Baseline fleet (CSV + IDs) | `outputs/results/chosen_fleet.csv`, `chosen_fleet_ids.csv` |
| Robust fleet (CSV + IDs) | `outputs/results/robust_fleet.csv`, `robust_fleet_ids.csv` |
| Sensitivity CSVs | `outputs/sensitivity/base_case.csv`, `safety_sensitivity.csv`, `carbon_price_sensitivity.csv` |
| Sensitivity summary | `outputs/sensitivity/sensitivity_summary_*.txt` |
| Sensitivity plots | `outputs/sensitivity/plots/*.png` |
| Run.py charts (sweep/pareto/carbon) | `outputs/charts/*.png` |

Submission: use `run.py --robust --submit` to fill the submission template from the **robust** fleet; use `run.py --submit` (no `--robust`) to use the **baseline** fleet.
