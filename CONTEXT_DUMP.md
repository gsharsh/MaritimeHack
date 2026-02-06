# REPmonkeys — Maritime Hackathon 2026: Complete Context Dump

## 1. Problem Statement

We are solving a **fleet selection optimization problem** for the Maritime Hackathon 2026.

**Scenario:** Select a fleet of vessels to transport bunker fuel from Singapore to Australia West Coast. We must choose a subset of 108 available vessels that:
- Meets a monthly cargo demand of **4,576,667 tonnes** (54.92M annual / 12)
- Maintains an average fleet safety score **>= 3.0**
- Includes at least **one vessel of each of 8 fuel types** (fuel diversity constraint)
- **Minimizes total fleet cost** (fuel + carbon + CAPEX + risk premium)

**Category:** A
**Team:** REPmonkeys
**Deadline:** 7 Feb 2026 09:00 SGT

---

## 2. Given Data

### 2.1 Vessel Movements Dataset
- `vessel_movements_dataset.csv` — raw AIS data (3.2MB, ~55k rows)
- Contains: vessel_id, timestamp, position, speed, main_engine_fuel_type, safety_score, engine specs, load factors

### 2.2 Calculation Factors
- `calculation_factors.xlsx` — emission factors (Cf sheet), fuel prices, CAPEX brackets, safety adjustment rates
- `llaf_table.csv` — Low-Load Adjustment Factors for engine loads 2-19%

### 2.3 Submission Template
4-column CSV: Header Name, Data Type, Units, Submission. We fill the Submission column.

---

## 3. Calculation Methodology (from SOP)

### Step 1-3: Data Preparation
- Filter to active vessels, join with vessel metadata
- Result: `df_active.csv` with per-row AIS observations

### Step 4: Fuel Cost
- Fuel price per tonne = `FUEL_PRICE_USD_PER_GJ[fuel] * LCV_MJ_PER_KG[fuel]`
- Fuel prices (USD/GJ): Distillate=13, LNG=15, LPG=15, Ammonia=40, Hydrogen=50, Methanol=54, Ethanol=54
- Main engine uses its own fuel price; AE and boilers use Distillate price

### Step 5: Emissions
- **CO2, CH4, N2O** per-row using Cf emission factors (g pollutant / g fuel)
- **Low-Load Adjustment Factors (LLAF):** for engine loads < 20%, multiply emissions by factors from LLAF table (e.g., at 2% load: CO2 x3.28, CH4 x21.18)
- **CO2eq** = CO2 + (28 * CH4) + (265 * N2O) — GWP values: CH4=28, N2O=265
- **Carbon cost** = CO2eq * $80/tCO2e

### Step 6: CAPEX & Risk Premium
- **Base CAPEX** by DWT bracket:
  - 10k-40k DWT: $35M
  - 40k-55k: $53M
  - 55k-80k: $80M
  - 80k-120k: $78M
  - >120k: $90M
- **Fuel multiplier**: Distillate=1.0, Ethanol=1.2, Hydrogen=1.1, LPG(P)/Methanol=1.3, LPG(B)=1.35, LNG/Ammonia=1.4
- **Ship cost** = base_capex * fuel_multiplier
- **Monthly CAPEX** = ((ship_cost - salvage) * CRF + r * salvage) / 12 (SOP Step 6c)
  - Asset depreciation rate r = 8% per annum (SOP Step 6c)
  - Life of each ship N = 30 years (SOP Step 6c)
  - CRF = r(1+r)^N / ((1+r)^N - 1) = 0.088827 (SOP Step 6c)
  - Salvage = 10% of cost of ship (SOP Step 6c)
- **Safety adjustment rates**: score 1 → +10%, 2 → +5%, 3 → 0%, 4 → -2%, 5 → -5%
- **Risk premium** = total_monthly * adjustment_rate
- **Final cost** = total_monthly + risk_premium (this is the MILP objective)

### Step 7: Fleet Selection Constraints
1. Combined fleet DWT >= 4,576,667 tonnes
2. Average fleet safety score >= 3.0
3. At least one vessel of each of 8 fuel types
4. Each ship selected at most once

---

## 4. Our Solution Architecture

### 4.1 Data Pipeline
```
vessel_movements_dataset.csv
    → df_active.csv (filtered AIS rows)
    → per_vessel.csv (aggregated: 108 vessels × 16 columns)
    → MILP optimizer
    → submission CSV + charts
```

### 4.2 per_vessel.csv Structure (108 rows)
Each row is one vessel with:
```
vessel_id, dwt, safety_score, main_engine_fuel_type,
FC_me_total, FC_ae_total, FC_ab_total, FC_total,
CO2eq, fuel_cost, carbon_cost, monthly_capex,
total_monthly, adj_rate, risk_premium, final_cost
```

### 4.3 Fleet Pool Statistics
| Fuel Type | Count | Total DWT | Avg Safety | Avg Cost |
|-----------|-------|-----------|------------|----------|
| DISTILLATE FUEL | 54 | 7,399,678 | 2.56 | $731,714 |
| LNG | 22 | 3,024,480 | 3.77 | $905,296 |
| Methanol | 11 | 1,281,230 | 3.64 | $1,038,951 |
| Ammonia | 8 | 1,483,752 | 3.50 | $1,189,940 |
| Ethanol | 5 | 922,748 | 3.40 | $1,254,741 |
| LPG (Propane) | 3 | 451,804 | 4.67 | $813,562 |
| LPG (Butane) | 3 | 442,239 | 4.00 | $934,332 |
| Hydrogen | 2 | 293,401 | 3.50 | $1,088,723 |
| **Total** | **108** | **15,299,332** | **3.14** | **$871,036** |

Safety distribution: score 1 (17), 2 (14), 3 (31), 4 (29), 5 (17)
DWT range: 14,226 – 262,781, median 179,078

---

## 5. MILP Formulation

**Solver:** PuLP with CBC backend (binary integer programming)

**Decision variables:** x_i ∈ {0, 1} for each vessel i (i = 1..108)

**Objective:** Minimize Σ(x_i × final_cost_i)

**Constraints:**
1. **DWT:** Σ(x_i × dwt_i) ≥ 4,576,667
2. **Safety (linearized):** Σ(x_i × (safety_i - 3.0)) ≥ 0
   - This is equivalent to: average safety of selected fleet ≥ 3.0
   - Linearization avoids dividing by fleet size (which would be nonlinear)
3. **Fuel diversity:** For each fuel type f: Σ(x_i where fuel_type_i = f) ≥ 1
4. **CO2 cap (optional, for Pareto):** Σ(x_i × CO2eq_i) ≤ ε

---

## 6. Production Results

### 6.1 Base Case Optimal Fleet
| Metric | Value |
|--------|-------|
| Fleet size | 21 vessels |
| Total DWT | 4,577,756 tonnes |
| Total cost | $19,706,493.72 |
| Avg safety score | 3.24 |
| Unique fuel types | 8 / 8 |
| CO2eq emissions | 13,095.28 tonnes |
| Fuel consumption | 4,599.57 tonnes |

Fleet composition: DISTILLATE FUEL (14), LPG (Propane) (1), LPG (Butane) (1), Methanol (1), Ethanol (1), Ammonia (1), Hydrogen (1), LNG (1)

Selected vessel IDs: [10087110, 10110870, 10126700, 10134620, 10150460, 10174220, 10190060, 10237570, 10245490, 10269250, 10332600, 10340520, 10403870, 10427630, 10443460, 10459300, 10562250, 10578090, 10641440, 10673120, 10776060]

### 6.2 Safety Threshold Sensitivity
| Threshold | Feasible | Fleet Size | Total Cost | Avg Safety | CO2eq | DWT |
|-----------|----------|------------|------------|------------|-------|-----|
| 3.0 | Yes | 21 | $19,706,494 | 3.24 | 13,095 | 4,577,756 |
| 3.5 | Yes | 22 | $19,831,197 | 3.50 | 13,011 | 4,577,367 |
| 4.0 | Yes | 22 | $20,763,960 | 4.00 | 12,153 | 4,578,979 |
| 4.5 | Yes | 26 | $23,251,571 | 4.50 | 12,585 | 4,577,948 |

Observation: Raising safety from 3.0 to 4.5 costs +$3.5M (+18%) but fleet shifts from distillate-heavy (14 ships) to more LNG (7) and LPG.

### 6.3 Carbon Price Sensitivity
| Carbon Price | Fleet Size | Total Cost | CO2eq | Avg Safety |
|-------------|------------|------------|-------|------------|
| $80/t | 21 | $19,706,494 | 13,095 | 3.24 |
| $120/t | 22 | $20,216,486 | 12,351 | 3.05 |
| $160/t | 22 | $20,707,913 | 12,069 | 3.14 |
| $200/t | 22 | $21,190,674 | 12,069 | 3.14 |

Observation: Higher carbon price shifts fleet to lower-emission vessels. At $120+, fleet picks up one more vessel and drops CO2 by ~6%.

### 6.4 Cost-Emissions Pareto Frontier (15 points)
| CO2eq Cap | Fleet Size | Total Cost | Actual CO2eq | Shadow Price ($/tCO2eq) | Avg Safety |
|-----------|------------|------------|--------------|------------------------|------------|
| 13,095 | 21 | $19,706,494 | 13,095 | - | 3.24 |
| 12,697 | 22 | $19,722,457 | 12,351 | $21.44 | 3.05 |
| 12,299 | 22 | $19,742,389 | 12,069 | $70.76 | 3.14 |
| 11,901 | 22 | $19,820,824 | 11,707 | $216.71 | 3.23 |
| 11,503 | 22 | $19,842,029 | 11,500 | $102.39 | 3.36 |
| 11,105 | 22 | $20,029,956 | 11,074 | $441.60 | 3.36 |
| 10,707 | 22 | $20,209,186 | 10,665 | $437.39 | 3.27 |
| 10,308 | 22 | $20,483,879 | 10,304 | $760.92 | 3.41 |
| 9,910 | 22 | $20,827,340 | 9,904 | $860.05 | 3.59 |
| 9,512 | 22 | $21,146,818 | 9,474 | $742.91 | 3.36 |
| 9,114 | 22 | $21,581,274 | 9,102 | $1,167.22 | 3.32 |
| 8,716 | 22 | $21,994,623 | 8,680 | $979.92 | 3.41 |
| 8,318 | 22 | $22,567,073 | 8,311 | $1,549.75 | 3.23 |
| 7,920 | 23 | $23,507,290 | 7,918 | $2,393.08 | 3.57 |
| 7,521 | 24 | $25,029,360 | 7,521 | $3,839.04 | 3.46 |

Observation: Emissions can be cut from 13,095 → 7,521 tonnes (-42%) at a cost increase from $19.7M → $25.0M (+27%). The marginal abatement cost rises steeply from $21/tCO2e to $3,839/tCO2e.

---

## 7. Code Structure

```
MaritimeHack/
├── run.py                          # Main entry point (--all runs everything)
├── src/
│   ├── constants.py                # All SOP constants, CAPEX brackets, emission factors
│   ├── optimization.py             # MILP solver (PuLP CBC), validation, metrics
│   ├── data_adapter.py             # Load/validate per_vessel.csv, aggregate df_active.csv
│   ├── sensitivity.py              # Safety sweep, Pareto frontier, carbon price sweep
│   ├── charts.py                   # matplotlib charts (Agg backend, headless)
│   ├── seed_data.py                # Synthetic test data generator
│   └── utils.py                    # Path helpers
├── data/processed/
│   ├── per_vessel.csv              # 108 vessels, 16 columns (production data)
│   └── df_active.csv               # Aggregated AIS rows
├── given_data/
│   ├── vessel_movements_dataset.csv
│   ├── calculation_factors.xlsx
│   ├── llaf_table.csv
│   └── submission_template.csv
├── outputs/
│   ├── submission/submission_template.csv  # Filled submission
│   └── charts/                     # PNG visualizations
├── tests/                          # pytest suite with 5-vessel fixtures
└── config/params.yaml              # YAML config (mirrors constants.py)
```

---

## 8. Key Design Decisions

1. **Binary MILP over greedy/heuristic** — guarantees global optimum, not approximate
2. **Linearized safety constraint** — `Σ(x_i × (safety_i - threshold)) ≥ 0` avoids nonlinear division
3. **Epsilon-constraint Pareto** — standard OR technique, reuses same MILP with added CO2 cap
4. **Carbon price sensitivity via cost recalculation** — removes original carbon cost, applies new price, re-optimizes
5. **Safety sweep** — re-runs full MILP at each threshold, shows cost of higher safety standards
6. **Shadow carbon pricing** — computed between consecutive Pareto points as Δcost/ΔCO2eq

---

## 9. What We're Submitting

| Field | Value |
|-------|-------|
| team_name | REPmonkeys |
| category | A |
| sum_of_fleet_deadweight | 4,577,756 |
| total_cost_of_fleet | 19,706,493.72 |
| average_fleet_safety_score | 3.24 |
| no_of_unique_main_engine_fuel_types_in_fleet | 8 |
| sensitivity_analysis_performance | Yes |
| size_of_fleet_count | 21 |
| total_emission_CO2_eq | 13,095.28 |
| total_fuel_consumption | 4,599.57 |

---

## 10. What We Want Help With

We are looking for ways to **gain an edge** — improvements to our optimization, analysis, presentation, or methodology that could differentiate our submission. Areas to consider:
- Is our MILP formulation missing anything?
- Are there better sensitivity analyses we could run?
- Could we improve the objective function (multi-objective, weighted)?
- Are there insights in the data we're not exploiting?
- Is our cost model correctly implementing the SOP?
- What would make our report/presentation stand out?
- Are there additional charts or analysis that judges would value?
