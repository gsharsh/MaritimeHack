# Maritime Hackathon 2026 — Complete Reference Guide

## 1. THE PROBLEM IN ONE SENTENCE

Select a subset of 108 ships (one-way Singapore → Port Hedland voyages) that meets **≥ 4,576,667 tonnes DWT**, covers **all 8 fuel types**, averages **safety score ≥ 3.0**, and **minimizes total risk-adjusted cost**.

---

## 2. KEY NUMBERS

| Parameter | Value |
|---|---|
| Bunker Sales 2024 (MPA Report p.10) | **54.92 million tonnes** |
| Monthly demand (D = 54.92M / 12) | **≈ 4,576,667 tonnes** |
| Total ships in dataset | **108** |
| Total available DWT | **15,299,332 tonnes** |
| You need roughly | **~30% of the fleet** |
| Route | Singapore → Port Hedland (AUS West Coast) |
| Typical voyage duration | **5–7 days** |
| Carbon price | **$80 USD / tonne CO₂eq** |
| Ship lifespan (N) | **30 years** |
| Depreciation rate (r) | **8% per annum** |
| Salvage value | **10% of ship cost** |

---

## 3. THE 108 SHIPS — BREAKDOWN

### By Main Engine Fuel Type (MUST have ≥1 of each)
| Fuel Type | Ships | Total DWT | DWT Range |
|---|---|---|---|
| DISTILLATE FUEL | 54 | 7,399,678 | 14,226 – 262,781 |
| LNG | 22 | 3,024,480 | 25,035 – 261,089 |
| Methanol | 11 | 1,281,230 | 37,520 – 210,102 |
| Ammonia | 8 | 1,483,752 | 106,507 – 210,909 |
| Ethanol | 5 | 922,748 | 174,802 – 207,939 |
| LPG (Butane) | 3 | 442,239 | 49,861 – 210,909 |
| LPG (Propane) | 3 | 451,804 | 39,781 – 206,118 |
| Hydrogen | 2 | 293,401 | 114,563 – 178,838 |

**Critical:** Hydrogen only has 2 ships, LPG (Butane) and LPG (Propane) only 3 each. You MUST pick at least one from each — these are forced selections.

### By Safety Score
| Score | Meaning | Ships | Adjustment |
|---|---|---|---|
| 1 | Highest Risk | 17 | +10% penalty |
| 2 | High Risk | 14 | +5% penalty |
| 3 | Neutral | 31 | 0% |
| 4 | Low Risk | 29 | −2% reward |
| 5 | Least Risk | 17 | −5% reward |

### All aux engines and boilers use DISTILLATE FUEL (no variation).

### DWT Size Buckets (for CAPEX lookup)
| Bucket | Ship Count | Base Cost (Distillate, $M) |
|---|---|---|
| 10–40k DWT | 9 | $35M |
| 40–55k DWT | 17 | $53M |
| 55–80k DWT | 8 | $80M |
| 80–120k DWT | 12 | $78M |
| >120k DWT | 62 | $90M |

**Note:** The 80–120k bucket is actually cheaper than 55–80k. And >120k DWT dominates the fleet (62 of 108 ships).

---

## 4. COMPLETE CALCULATION PIPELINE (Step by Step)

### Step 1: Operating Modes
For each AIS row, classify:
- **Anchorage:** `in_anchorage == "anchorage"` AND `speed_knots < 1`
- **Maneuver:** `in_port_boundary` is not null AND `speed_knots > 1`
- **Transit:** `in_port_boundary` is null AND `speed_knots >= 1`
- **Drifting:** everything else

**⚠️ Only Transit and Maneuver rows count for fuel & emissions.**

Dataset breakdown: ~12,178 Transit rows, ~562 Maneuver, ~377 Anchorage, ~99 Drifting.

### Step 2: Activity Hours (A)
For each row, `A = time difference to next consecutive timestamp` (same vessel), in **hours**.

### Step 3a: Maximum Speed
```
MS = 1.066 × Vref
```

### Step 3b: Engine Load Factor (LF) — Main Engine Only
```
LF = (AS / MS)³
```
Where AS = actual speed (speed_knots from AIS data).

- Round LF to 2 decimal places
- If LF < 0.02 and mode is Transit or Maneuver → default LF to 0.02

### Step 4a: Adjusted SFC per Machinery
The dataset's SFC values assume Distillate fuel (LCV = 42.7 MJ/kg). Adjust for actual fuel:
```
sfc_adjusted_xy = sfc_xy × (42.7 / LCV_of_fuel_type_for_that_machinery)
```

For **main engine**: use LCV of `main_engine_fuel_type`
For **aux engine**: use LCV of `aux_engine_fuel_type` (always DISTILLATE → 42.7, so no change)
For **aux boiler**: use LCV of `boil_engine_fuel_type` (always DISTILLATE → 42.7, so no change)

**Practical result:** sfc_ae and sfc_ab stay the same. Only sfc_me changes for non-Distillate ships.

### Step 4b: Fuel Consumption (tonnes) per AIS row
```
Main Engine:  FC_me = (LF × P × sfc_adjusted_me × A) / 1,000,000
Aux Engine:   FC_ae = (ael × sfc_adjusted_ae × A) / 1,000,000
Aux Boiler:   FC_ab = (abl × sfc_adjusted_blr × A) / 1,000,000
```
Where: P = `mep` (kW), A = activity hours, LF = load factor from Step 3b.

**Units check:** kW × g/kWh × hours / 1,000,000 = tonnes ✓

### Step 5a: Low Load Adjustment Factor (LLAF)
- Convert LF to percentage: `%LF = LF × 100`
- Round `%LF` to nearest integer
- If `%LF < 2%` and mode is Transit or Maneuver → default to 2%
- If `%LF ≥ 20%` → LLAF = 1.0 for all gases
- Otherwise, look up the LLAF table for CO2, N2O, CH4 columns

### Step 5b: Emissions per AIS row per machinery
```
Emission_pqr_xy = LLAF_pqr × Cf_pqr × FC_xy
```
Where:
- pqr = CO2, CH4, or N2O
- xy = me, ae, or blr
- Cf values come from the **Cf table** matched to the **fuel type of that machinery**

**Important:** For aux engine and boiler, always use DISTILLATE FUEL Cf values.

### Step 5c: Total CO₂ Equivalent
```
CO2eq = Σ(GWP × Total_Emission_pqr)
```
GWP values: **CO₂ = 1, N₂O = 265, CH₄ = 28**

### Step 6a: Fuel Cost
```
Cost per tonne of fuel = Cost_per_GJ × LCV  (where LCV in MJ/kg ≈ GJ/tonne)
Total fuel cost = Total fuel consumed (all machineries) × Cost per tonne
```

**⚠️ Ambiguity alert:** The methodology says to use `main_engine_fuel_type` LCV for ALL fuel cost. But the problem statement (p.3) says "for each machinery." Since aux/boiler always use Distillate anyway, you might calculate separately:
- ME fuel cost = FC_me_total × 13.0 × 42.7 (for Distillate) or appropriate rate
- AE fuel cost = FC_ae_total × 13.0 × 42.7 (always Distillate)
- AB fuel cost = FC_ab_total × 13.0 × 42.7 (always Distillate)

### Fuel Price Reference
| Fuel Type | Cost/GJ (USD) | LCV (MJ/kg) | Cost/tonne (USD) |
|---|---|---|---|
| Distillate fuel | 13.0 | 42.7 | **555.10** |
| LPG (Propane) | 15.0 | 46.3 | **694.50** |
| LPG (Butane) | 15.0 | 45.7 | **685.50** |
| LNG | 15.0 | 48.0 | **720.00** |
| Methanol | 54.0 | 19.9 | **1,074.60** |
| Ethanol | 54.0 | 26.8 | **1,447.20** |
| Ammonia | 40.0 | 18.6 | **744.00** |
| Hydrogen | 50.0 | 120.0 | **6,000.00** |

**Hydrogen is absurdly expensive** ($6,000/tonne vs $555 for Distillate). Minimizing hydrogen ship count is key.

### Step 6b: Carbon/Emission Cost
```
Total carbon cost = Total CO2eq (tonnes) × $80
```

### Step 6c: Ship Ownership Cost (Monthly Amortized CAPEX)
```
Ship cost = Base Distillate cost (from DWT bucket) × Multiplier (M, from fuel type)
Salvage (S) = 10% × Ship cost
CRF = r × (1+r)^N / ((1+r)^N - 1)    where r = 0.08, N = 30

Annual cost = ((Ship cost - S) × CRF) + (r × S)
Monthly cost = Annual cost / 12
```

**Pre-calculated CRF:** with r=0.08, N=30 → CRF ≈ 0.08883

### CAPEX Multipliers by Fuel Type
| Fuel Type | Multiplier |
|---|---|
| Distillate | 1.0 (base) |
| LPG (Propane) | 1.3 |
| LPG (Butane) | 1.35 |
| LNG | 1.4 |
| Methanol | 1.3 |
| Ethanol | 1.2 |
| Ammonia | 1.4 |
| Hydrogen | 1.1 |

### Step 6d: Total Monthly Ship Cost
```
Total monthly cost = Fuel cost + Carbon cost + Monthly ownership cost
```

### Step 6e–f: Risk Premium & Final Adjusted Cost
```
Risk Premium = Total monthly cost × Safety adjustment rate
Final cost = Total monthly cost + Risk Premium
```

| Safety Score | Rate | Effect |
|---|---|---|
| 1 | +10% | Cost × 1.10 |
| 2 | +5% | Cost × 1.05 |
| 3 | 0% | Cost × 1.00 |
| 4 | −2% | Cost × 0.98 |
| 5 | −5% | Cost × 0.95 |

---

## 5. OPTIMIZATION PROBLEM FORMULATION

**Decision variables:** Binary x_i ∈ {0, 1} for each ship i (i = 1..108)

**Minimize:** Σ(x_i × adjusted_cost_i)

**Subject to:**
1. Σ(x_i × DWT_i) ≥ 4,576,667
2. Average safety score ≥ 3.0 → Σ(x_i × score_i) / Σ(x_i) ≥ 3.0
3. At least one ship from each of the 8 fuel types
4. x_i ∈ {0, 1}

This is a **Mixed Integer Linear Program** (the safety average constraint can be linearized). Use **PuLP** or **OR-Tools** in Python.

---

## 6. LLAF TABLE (Low Load Adjustment Factors)

| Load % | CO2 | N2O | CH4 |
|---|---|---|---|
| 2% | 3.28 | 4.63 | 21.18 |
| 3% | 2.44 | 2.92 | 11.68 |
| 4% | 2.01 | 2.21 | 7.71 |
| 5% | 1.76 | 1.83 | 5.61 |
| ... | ... | ... | ... |
| 19% | 1.01 | 1.01 | 1.05 |
| ≥20% | 1.00 | 1.00 | 1.00 |

Most ships in transit have load factors well above 20%, so LLAF=1 for the bulk of calculations. It matters mainly for maneuvering at low speeds.

---

## 7. SENSITIVITY ANALYSIS (Stretch Objective)

Re-run the entire optimization with **average safety score ≥ 4.0** instead of 3.0. Compare:
- Fleet composition changes
- Cost increase
- Emissions impact
- Which ships get swapped in/out

---

## 8. SUBMISSION CHECKLIST

| Deliverable | Format | Naming |
|---|---|---|
| Case Paper | Word or PDF, ≤3 pages + cover | `MaritimeHackathon2026_CasePaper_teamname` |
| Results CSV | Provided template, fill "Submission" column only | `teamname_submission.csv` |
| Presentation | PowerPoint, 4–6 slides, ≤10 min | `teamname_presentation.ppt` |

**Deadline: 7 Feb 2026, 09:00 SGT**

### CSV Submission Fields
1. team_name (String)
2. category (String — A or B)
3. report_file_name (String — include extension)
4. sum_of_fleet_deadweight (Float, tonnes)
5. total_cost_of_fleet (Float, USD)
6. average_fleet_safety_score (Float)
7. no_of_unique_main_engine_fuel_types_in_fleet (Integer — should be 8)
8. sensitivity_analysis_performance (Yes/No)
9. size_of_fleet_count (Integer)
10. total_emission_CO2_eq (Float, tonnes)
11. total_fuel_consumption (Float, tonnes)

---

## 9. STRATEGIC INSIGHTS

1. **Forced picks:** You must include ≥1 Hydrogen ship (only 2 exist), ≥1 LPG Butane (3 exist), ≥1 LPG Propane (3 exist). Pick the cheapest/safest from each.

2. **Hydrogen is the pain point:** $6,000/tonne fuel cost. Minimize to exactly 1 Hydrogen ship, and pick the smallest one if possible to reduce fuel burn.

3. **Distillate ships are cheapest to operate** — they dominate the fleet (54 ships) and have the lowest fuel price ($555/tonne). Fill remaining DWT mostly with these.

4. **Safety score 4–5 ships get discounts** (−2% and −5%). Prefer these when costs are similar. But score 1–2 ships may have lower base costs, so the optimizer needs to weigh both.

5. **Big ships are efficient** — >120k DWT ships (62 in the fleet) get you to the 4.58M tonne target with fewer ships. Fewer ships = fewer CAPEX costs.

6. **The >120k bucket is only $90M base** while 55–80k is $80M — the marginal cost per DWT is much lower for big ships.

7. **Aux boiler load (abl) is 0 for some ships** — these have zero boiler fuel consumption, saving costs.
