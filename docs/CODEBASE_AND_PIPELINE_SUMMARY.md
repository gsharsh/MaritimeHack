# MaritimeHack Codebase & Pipeline — Technical Summary for Agents

This document gives another agent (or human) a precise picture of the repo layout, data flow, and how to run or extend the pipeline.

---

## 1. Project context

- **Maritime Hackathon 2026**: select a **minimum-cost fleet** of ships to move bunker fuel **Singapore → Australia West (Port Hedland)** in one month.
- **Constraints**: total DWT ≥ monthly demand (~4.15–4.58M tonnes), average RightShip safety score ≥ 3.0, at least one vessel per main_engine_fuel_type, each ship used at most once.
- **Cost per ship**: fuel + carbon (emissions × carbon price) + amortized CAPEX + risk premium by safety score. All embodied in a single **per-vessel** metric `final_cost` that the optimizer minimizes.

---

## 2. Repo layout (what lives where)

```
MaritimeHack/
├── config/
│   └── params.yaml              # cargo_demand_tonnes, constraints, sensitivity toggles
├── data/
│   ├── processed/               # Main pipeline outputs
│   │   ├── df_active.csv        # (Optional) Per-row AIS: FC_me, FC_ae, FC_ab, E_CO2/CH4/N2O, vessel_id, dwt, safety, fuel type
│   │   └── per_vessel.csv       # PRIMARY INPUT: one row per vessel, required columns below
│   ├── seed/
│   │   ├── seed_vessels.csv     # Synthetic fleet (from src.seed_data); different column names
│   │   └── seed_global_params.json
│   └── global_params/           # global_params.yaml (from example) — not used by current code path; constants in code
├── given_data/                  # Hackathon-provided: vessel_movements_dataset.csv, llaf_table.csv, calculation_factors.xlsx, submission_template.csv
├── src/
│   ├── constants.py             # Single source of truth: MONTHLY_DEMAND, SAFETY_THRESHOLD, CARBON_PRICE, FUEL_TYPES, CF_EMISSION_FACTORS, LCV, FUEL_PRICE_*, CAPEX brackets, SAFETY_ADJUSTMENT_RATES, GWP, LLAF_TABLE, get_monthly_capex()
│   ├── data_adapter.py          # Load/validate per_vessel.csv; aggregate df_active → per_vessel (Steps 5c–6f)
│   ├── data_loader.py           # Stub; actual loading is data_adapter
│   ├── cost_model.py            # Stub; cost logic is in constants.py + data_adapter.aggregate_df_active
│   ├── optimization.py          # MILP (PuLP/CBC): select_fleet_milp, validate_fleet, total_cost_and_metrics, format_outputs, submission_outputs
│   ├── sensitivity.py           # run_safety_sweep, run_carbon_price_sweep, run_pareto_sweep (epsilon-constraint), formatters
│   ├── sensitivity_2024.py      # 2024 scenarios (CII, congestion, fuel multiplier), _df_for_milp; NOT wired into run_sensitivity_analysis yet
│   ├── visualize_sensitivity.py # All charts: load from CSVs, plot_tornado_analysis, plot_safety_pareto_frontier, plot_cost_vs_safety_threshold, plot_carbon_price_sensitivity, plot_fuel_mix_vs_carbon_price, plot_macc, plot_2024_scenario_comparison, plot_combined_summary; generate_all_visualizations()
│   ├── charts.py                # plot_pareto_frontier, plot_fleet_composition, plot_safety_comparison (used by run.py --sweep/--pareto)
│   ├── seed_data.py             # generate_seed_fleet(), compute_estimated_costs(), save_seed_data() → data/seed/
│   └── utils.py                 # project_root(), data_path(), outputs_path(), voyage_hours_from_nm_and_speed
├── run.py                       # Main CLI: load per_vessel → MILP → results; optional --sweep, --pareto, --carbon-sweep, --submit
├── run_sensitivity_analysis.py  # Load config + per_vessel → run_sensitivity_using_milp (base + safety + carbon); write CSVs + JSON; call generate_all_visualizations
├── outputs/
│   ├── results/                 # chosen_fleet.csv, chosen_fleet_ids.csv (from run.py)
│   ├── sensitivity/             # base_case.csv, safety_sensitivity.csv, carbon_price_sensitivity.csv, 2024_scenarios.csv (empty if not run), *.json, *.txt
│   │   └── plots/               # All sensitivity charts (tornado, Pareto, cost/emissions vs safety, carbon, fuel mix, MACC, dashboard)
│   ├── charts/                  # From run.py --sweep/--pareto: fleet_composition, safety_comparison, pareto_frontier
│   └── submission/              # submission_template.csv filled by run.py --submit
├── tests/                       # test_data_adapter, test_optimization, test_milp, test_validation, test_cost_model
├── docs/                        # problem_summary.md, given_data_summary.md, assumptions.md, constraints.md
├── Methodology_Report.md        # Full case-paper methodology (AIS → cost → MILP)
├── Methodology_SOP.md           # Implementation guide
├── SENSITIVITY_ANALYSIS_README.md
└── requirements.txt
```

---

## 3. Data contract: per_vessel.csv (required columns)

The optimizer and sensitivity code expect a **single DataFrame** with one row per vessel. Required columns (see `src/data_adapter.py` `REQUIRED_COLUMNS`):

- **Identifiers & attributes:** `vessel_id`, `dwt`, `safety_score`, `main_engine_fuel_type`
- **Fuel/emissions (aggregated per vessel):** `FC_me_total`, `FC_ae_total`, `FC_ab_total`, `FC_total`, `CO2eq`
- **Cost components:** `fuel_cost`, `carbon_cost`, `monthly_capex`, `total_monthly`, `adj_rate`, `risk_premium`, `final_cost`

Validation in `load_per_vessel()`: no missing required columns, no NaN in them, all `final_cost` > 0, all `CO2eq` > 0. Production checks in `validate_per_vessel()`: 108 rows, 8 fuel types, total DWT ≥ demand.

---

## 4. End-to-end pipeline (three stages)

### Stage A: Raw AIS → per-row “active” data (outside or partial in repo)

- **Input:** `given_data/vessel_movements_dataset.csv` (AIS: one row per timestamp per vessel; static ship attributes on each row).
- **Described in:** `Methodology_Report.md` (operating mode, activity hours, load factor, LLAF, SFC adjustment, emissions).
- **Output (expected):** `data/processed/df_active.csv` — one row per AIS row, with at least: `vessel_id`, `dwt`, `safety_score`, `main_engine_fuel_type`, `FC_me`, `FC_ae`, `FC_ab`, `E_CO2_total`, `E_CH4_total`, `E_N2O_total`.
- **Current repo:** No script in the repo produces `df_active` from `vessel_movements_dataset.csv`. That step is assumed to be done by a teammate or notebook (SOP Steps 1–5). The repo **does** provide the next step: aggregate `df_active` → `per_vessel`.

### Stage B: df_active → per_vessel (in-repo)

- **Function:** `src/data_adapter.py` → `aggregate_df_active(input_path, output_path)`.
- **Default paths:** `data/processed/df_active.csv` → `data/processed/per_vessel.csv`.
- **Logic:** Group by `vessel_id`; sum FC_me/FC_ae/FC_ab and E_CO2/CH4/N2O; compute `CO2eq` (GWP); merge static vessel cols; apply fuel cost (ME at ME fuel price, AE/AB at Distillate), carbon cost (CO2eq × CARBON_PRICE), monthly CAPEX (from `constants.get_monthly_capex`), risk premium (from `SAFETY_ADJUSTMENT_RATES`), then `final_cost = total_monthly + risk_premium`. Writes CSV with `REQUIRED_COLUMNS`.
- **When to use:** When you have `df_active.csv` from an upstream AIS pipeline. Call `aggregate_df_active()` (or a small script that calls it) to refresh `per_vessel.csv`.

### Stage C: per_vessel → optimization & sensitivity (in-repo)

- **Load:** `load_per_vessel(path)` — default `data/processed/per_vessel.csv`, fallback `tests/fixtures/checkpoint_vessels.csv` if file missing.
- **Optimization:** `src/optimization.py` → `select_fleet_milp(df, cargo_demand, min_avg_safety, require_all_fuel_types, co2_cap=None)`. Binary MILP: minimize sum(x_i * final_cost_i); constraints: sum(dwt_i * x_i) ≥ demand, linearized average safety ≥ threshold, ≥1 vessel per fuel type, optional CO2 cap. Returns list of selected `vessel_id`.
- **Metrics:** `total_cost_and_metrics(df, selected_ids)` → total_dwt, total_cost_usd, avg_safety_score, num_unique_main_engine_fuel_types, fleet_size, total_fuel_tonnes, total_co2e_tonnes.
- **Sensitivity (same MILP, different params):**
  - **Safety:** `run_safety_sweep(df, thresholds=[2.5,3,3.5,4,4.5], cargo_demand)` → one MILP per threshold.
  - **Carbon:** `run_carbon_price_sweep(df, cargo_demand, safety_threshold, carbon_prices=[80,120,160,200])` → reprice carbon per vessel, set `final_cost` from new cost components, then MILP at each price.
  - **Pareto (run.py only):** `run_pareto_sweep(df, n_points=15)` — epsilon-constraint on CO2eq cap, shadow carbon prices.
- **2024 scenarios:** Implemented in `sensitivity_2024.py` (CII, congestion hours, fuel price multiplier). **Not** currently called from `run_sensitivity_analysis.py`; `scenarios_2024` is left empty so the 2024 scenario comparison plot is skipped unless you wire it in.

---

## 5. Entry points and what they do

| Entry point | Purpose |
|------------|--------|
| `python run.py` | Load `per_vessel` (default path or `--data`), run MILP once, print metrics, save chosen fleet to `outputs/results/`, optionally `--sweep` / `--pareto` / `--carbon-sweep` / `--submit` |
| `python run.py --data <path>` | Use custom per_vessel CSV (must have `REQUIRED_COLUMNS`). |
| `python run.py --sweep` | Plus safety threshold sweep 3.0–4.5 and fleet composition / safety charts. |
| `python run.py --pareto` | Plus cost–emissions Pareto (epsilon-constraint) and Pareto chart. |
| `python run.py --carbon-sweep` | Plus carbon price sweep $80/$120/$160/$200. |
| `python run.py --submit` | Plus fill submission CSV from base MILP. |
| `python run_sensitivity_analysis.py` | Load config (`config/params.yaml`: cargo_demand, min_safety) and per_vessel (default or `--data`); run base case + safety sweep (2.5–4.5) + carbon sweep (80,120,160,200); write CSVs + JSON + summary txt; call `generate_all_visualizations(results_dir, plots_dir)`. |
| `python run_sensitivity_analysis.py --data <path>` | Same with custom per_vessel. |
| `python -m src.visualize_sensitivity [results_dir]` | Regenerate all sensitivity plots from existing CSVs in `results_dir` (default `outputs/sensitivity`). |
| `python -m src.seed_data` | Generate synthetic fleet + global params into `data/seed/`. **Note:** `seed_vessels.csv` uses names like `total_cost_usd`, `co2e_tonnes`, `fuel_tonnes`; it does **not** match `REQUIRED_COLUMNS`. To use with `run.py` / `run_sensitivity_analysis.py` you must either produce a per_vessel-shaped CSV (e.g. by mapping and adding missing columns) or add a conversion in the loader. |

Config for sensitivity: `config/params.yaml` — `cargo_demand_tonnes`, `constraints.min_avg_safety_score`. Run scripts read these; `run.py` can also override via `--cargo-demand` and `--safety-threshold`.

---

## 6. Where constants and cost logic live

- **Constants:** `src/constants.py` — demand, safety threshold, carbon price, fuel types, emission factors (Cf), LCV, fuel prices (USD/GJ then per tonne), CAPEX brackets and fuel multipliers, safety adjustment rates, GWP, LLAF. Used by `data_adapter.aggregate_df_active` and by validation/display.
- **Cost calculation (from row-level to per-vessel):** In `data_adapter.aggregate_df_active()`: fuel cost (ME vs AE/AB pricing), carbon cost, `get_monthly_capex(dwt, main_engine_fuel_type)`, risk premium, `final_cost`. No separate `cost_model.py` step; that file is a stub.
- **Carbon price sweep:** `sensitivity.run_carbon_price_sweep` temporarily overrides effective carbon cost per vessel and recomputes `final_cost` (and possibly other components) so the MILP sees updated costs; it does not change `constants.CARBON_PRICE` globally.

---

## 7. Visualizations (where and from what)

- **From run.py:** `src/charts.py` — `plot_fleet_composition`, `plot_safety_comparison`, `plot_pareto_frontier`; outputs under `outputs/charts/`.
- **From run_sensitivity_analysis / visualize_sensitivity:** `src/visualize_sensitivity.py` reads CSVs from `outputs/sensitivity/` (`base_case.csv`, `safety_sensitivity.csv`, `carbon_price_sensitivity.csv`, `2024_scenarios.csv`). Produces in `outputs/sensitivity/plots/`: tornado, safety Pareto (cost/fleet size vs threshold), cost vs safety threshold, cost breakdown vs safety, emissions vs safety threshold, carbon price sensitivity, fuel mix vs carbon price, MACC, 2024 scenario comparison (if `2024_scenarios.csv` has rows), and summary dashboard. Tornado uses safety + carbon cases; each case = one horizontal bar (cost or emissions), sorted by impact.

---

## 8. Tests and fixtures

- **Fixtures:** `tests/fixtures/checkpoint_vessels.csv` — small per_vessel CSV with `REQUIRED_COLUMNS`; used by tests and as fallback when `data/processed/per_vessel.csv` is missing.
- **Tests:** `test_data_adapter.py` (load_per_vessel, validate_per_vessel, aggregate_df_active contract), `test_optimization.py`, `test_milp.py`, `test_validation.py`, `test_cost_model.py`. Run with pytest from project root.

---

## 9. Submission

- **Template:** `given_data/submission_template.csv` — column “Header Name” mapped to “Submission” values.
- **Filler:** `optimization.submission_outputs(metrics, ...)` returns the dict; `run.py --submit` maps it onto the template and writes `outputs/submission/submission_template.csv`. Rename to `teamname_submission.csv` and do not reorder columns.

---

## 10. Summary for another agent

- **Primary input:** A single per-vessel table with `REQUIRED_COLUMNS` (see Section 3), usually at `data/processed/per_vessel.csv`. It can be produced by `aggregate_df_active()` from `df_active.csv`, or by some other process that obeys the same contract.
- **Upstream gap:** The repo does **not** implement AIS → `df_active`; that is assumed to exist or be built (e.g. from `vessel_movements_dataset.csv` following Methodology_Report).
- **Core flow:** Load per_vessel → MILP (`select_fleet_milp`) → metrics and optional sweeps → CSVs and plots. Constants and cost aggregation live in `constants.py` and `data_adapter.py`; `sensitivity_2024` (2024 scenarios) is implemented but not wired into the sensitivity runner.
- **To add 2024 scenarios to the runner:** In `run_sensitivity_analysis.py`, call the logic in `sensitivity_2024.py` to fill `results["scenarios_2024"]` and ensure the corresponding CSV is written so `generate_all_visualizations` can plot the 2024 scenario comparison.
