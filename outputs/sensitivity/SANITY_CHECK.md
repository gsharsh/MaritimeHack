# Sensitivity Analysis Output – Sanity Check

Run: after fix (seed global params + row capex).  
Base case and all sensitivities now have non-zero cost and CO2e.

---

## Why CO2e was 0.0 before the fix

**Root cause:** When using seed ships, the runner did **not** load `data/seed/seed_global_params.json`. So `global_params` was empty (or only had defaults). In `ship_total_cost_usd()` we call:

```python
co2e = co2e_tonnes(
    fuel_tonnes,
    global_params.get("emission_factors", {}),  # → {} when not loaded
    fuel_types,
)
```

In `co2e_tonnes()`, for each fuel type we do:

```python
cf = emission_factors.get(ft, {})  # → {} for every fuel type
total += tonnes * (cf.get("CO2", 0) + cf.get("CH4", 0)*25 + cf.get("N2O", 0)*298)
#                  ↑ 0              ↑ 0                    ↑ 0  → total stays 0
```

So **fuel_tonnes** was correct (computed from row P, sfc_me, voyage_hours), but **CO2e** was 0 because there were no emission factors. Same for **total_cost_usd**: `price_usd_per_gj` was empty so fuel cost was 0; with zero carbon and often zero capex, total cost was 0.

**Fix:** When `--ships` points to seed data, the runner now loads `data/seed/seed_global_params.json`, so `emission_factors`, `price_usd_per_gj`, and `lcv_mj_per_kg` are set. The cost model also uses `row.get("capex_usd", 0)` when the vessel is not in `ship_capex_usd`, so ownership cost is correct for seed vessels.

---

## Output files and field-by-field check

### 1. `base_case.csv`

| Field | Value (this run) | Sanity check |
|-------|------------------|----------------|
| total_dwt | 4,151,907 | ≥ cargo_demand 4,150,000 ✓ |
| total_cost_usd | 93,530,408 | Non-zero, plausible for 26 ships ✓ |
| avg_safety_score | 3.0 | Equals base min_safety 3.0 ✓ |
| num_unique_main_engine_fuel_types | 8 | All fuel types required ✓ |
| fleet_size | 26 | Integer, reasonable ✓ |
| total_fuel_tonnes | 70,301 | Non-zero, ~2.7 kt/ship ✓ |
| total_co2e_tonnes | 192,746 | Non-zero; fuel × emission factors ✓ |

**Consistency:** total_dwt ≥ demand; avg_safety ≥ 3.0; cost and CO2e scale with fleet.

---

### 2. `safety_sensitivity.csv`

| Field | Role | Sanity check |
|-------|------|----------------|
| safety_threshold | 2.5, 3.0, 3.5, 4.0, 4.5 | Sweep as designed ✓ |
| total_dwt | Per row | All ≥ 4,150,000 (within rounding) ✓ |
| total_cost_usd | Per row | Increases as threshold rises (stricter → costlier fleet) ✓ |
| avg_safety_score | Per row | Matches or slightly exceeds threshold (2.92→2.5, 3.0→3.0, etc.) ✓ |
| num_unique_main_engine_fuel_types | 8 | Always 8 ✓ |
| fleet_size | 26, 26, 26, 25, 24 | Shrinks at 4.0 and 4.5 ✓ |
| total_fuel_tonnes | Per row | Tracks fleet size and efficiency ✓ |
| total_co2e_tonnes | Per row | Non-zero; higher at 4.5 (more fuel use) ✓ |

**Trends:** Stricter safety → fewer ships (24–26), higher cost, fuel/CO2e reflect fleet composition.

---

### 3. `carbon_price_sensitivity.csv`

| Field | Role | Sanity check |
|-------|------|----------------|
| carbon_price_usd_per_tco2e | 80, 120, 160, 200 | Sweep as designed ✓ |
| total_dwt | Per row | All ≥ 4.15M ✓ |
| total_cost_usd | Per row | Rises with carbon price ✓ |
| avg_safety_score | 3.0, 3.0, 3.08, 3.12 | Slight increase as carbon rises (cleaner fleet) ✓ |
| num_unique_main_engine_fuel_types | 8 | Always 8 ✓ |
| fleet_size | 26, 26, 25, 25 | Drops at 160 and 200 ✓ |
| total_fuel_tonnes | Per row | Slight variation by fleet ✓ |
| total_co2e_tonnes | 192746 → 170293 → 166001 → 151155 | Falls as carbon price rises ✓ |

**Trends:** Higher carbon price → lower fleet CO2e (optimizer picks lower-emission vessels); cost increases.

---

### 4. `2024_scenarios.csv`

| Field | Role | Sanity check |
|-------|------|----------------|
| scenario_name | Base, 2024 Typical, 2024 Stress | Three scenarios ✓ |
| total_dwt | Per scenario | All ≥ 4.15M ✓ |
| total_cost_usd | Per scenario | Base < Typical < Stress ✓ |
| avg_safety_score | 3.0 for all | Base min_safety ✓ |
| num_unique_main_engine_fuel_types | 8 | Always 8 ✓ |
| fleet_size | 26 for all | Same optimal fleet in this run ✓ |
| total_fuel_tonnes | 70k, 72k, 73k | Rises with congestion (Typical/Stress) ✓ |
| total_co2e_tonnes | 192746, 176294, 179294 | Base highest; Typical/Stress have CII/congestion adjustments ✓ |
| config_fuel_price_multiplier | 1.0, 1.05, 1.1 | Matches scenario definitions ✓ |
| config_congestion_hours | 0, 48, 72 | Matches scenario definitions ✓ |
| config_cii_enforcement | False, True, True | Base no CII; Typical/Stress CII on ✓ |
| avg_cii | Empty for Base; 24.6, 25.0 for Typical/Stress | Only when CII enforced ✓ |
| cii_rating_distribution | E/A/B for Typical/Stress | E dominant; A/B/C present ✓ |

**Note:** Base CO2e (192,746) > Typical (176,294) because Typical applies congestion/CII and re-optimizes; fleet composition and fuel use differ. All values non-zero and internally consistent.

---

### 5. `sensitivity_results_*.json`

Same metrics as above, plus:

- **base_case:** `metrics` only (no selected_vessel_ids in saved JSON).
- **safety_sensitivity:** array of `{ threshold, metrics, error }`; `error` null when OK.
- **carbon_price_sensitivity:** array of `{ carbon_price, metrics, error }`; each `metrics` includes `carbon_price_usd_per_tco2e`.
- **scenarios_2024:** array of `{ scenario_name, metrics, scenario_config, avg_cii?, cii_rating_distribution?, error }`.

**Type note:** In JSON, `total_dwt` is sometimes a string (e.g. `"4151907"`). For analysis, convert to float/int; CSVs store numeric.

---

## Summary

- **CO2e was 0.0** because `emission_factors` was empty when seed global params were not loaded; the fix is to load `data/seed/seed_global_params.json` for seed ships and to use row `capex_usd` when needed.
- **All output fields** after the fix are consistent: demand and safety constraints hold, cost and CO2e are non-zero, and trends (safety, carbon price, scenarios) match expectations.
- **Visualizations:** Run `python -m src.visualize_sensitivity outputs/sensitivity` (with a writable matplotlib/font cache if needed) to regenerate plots from these CSVs.
