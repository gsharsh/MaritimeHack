# Given Data Summary (Maritime Hackathon 2026)

Summary of files in `given_data/` and how they relate to the problem.

---

## 1. `vessel_movements_dataset.csv`

**Format:** AIS-style data — **one row per timestamp per vessel** (many rows per ship). Ship-level attributes are repeated on every row.

**Columns (used):**

| Column | Description |
|--------|-------------|
| `vessel_id` | Unique ship ID |
| `vessel_type_new` | e.g. "Chemical/Products Tanker" |
| `timestamp`, `timestamp_epoch` | Position time |
| `latitude`, `longitude` | Position |
| `speed_knots` | Speed at that time |
| `in_anchorage` | e.g. "anchorage", "null" |
| `in_port_boundary` | e.g. "Singapore", "Port Hedland", "null" |
| `safety_score` | Integer 1–5 (1 = highest risk, 5 = least risk) |
| `dwt` | Deadweight (tonnes) — cargo capacity |
| `fuel_category` | Numeric category (e.g. 2) |
| `main_engine_fuel_type` | e.g. "Methanol", "LNG" |
| `aux_engine_fuel_type` | e.g. "DISTILLATE FUEL" |
| `boil_engine_fuel_type` | e.g. "DISTILLATE FUEL" |
| `engine_type` | e.g. "SSD" |
| `mep` | Main engine power (kW) — **this is "P" in the problem** |
| `vref` | Design speed (knots) |
| `sfc_me`, `sfc_ae`, `sfc_ab` | Specific fuel consumption (g/kWh) for main, auxiliary engine, auxiliary boiler |
| `ael` | Auxiliary engine load (kW) |
| `abl` | Auxiliary boiler load (kW) |

**For fleet optimization:** Build a **ship-level table** by taking one row per `vessel_id` (e.g. first row or drop_duplicates). Map `mep` → main engine power P, `boil_engine_fuel_type` → aux boiler fuel type. There is no `vessel_name`; use `vessel_id` if needed.

**Observed main_engine_fuel_type values (examples):** Methanol, LNG. Constraint “at least one vessel of each main_engine_fuel_type” applies to the set of fuel types present in the dataset.

---

## 2. `llaf_table.csv`

**Load (percentage) vs emission multipliers** for NOx, HC, CO, PM, SO2, CO2, N2O, CH4. Rows from 2% to 20% load; multipliers relative to a reference (e.g. 20% = 1). Use for **part-load emission factors** when computing fuel consumption at different engine loads (e.g. voyage at less than 100% MCR). Column name is the pollutant; row key is load % (e.g. "10%").

---

## 3. `calculation_factors.xlsx`

**Excel workbook** — likely contains the numerical factors for the cost model, e.g.:

- Emission factors (tonne CO2, CH4, N2O per tonne fuel)
- LCV (MJ/kg) by fuel type
- Fuel price (USD/GJ) by fuel type
- Carbon price (USD/tCO2e)
- CAPEX base by DWT, multiplier by main_engine_fuel_type, depreciation, CRF
- Safety score adjustment rates (penalty/reward %)

**Action:** Open in Excel or read with `pandas.read_excel()` / `openpyxl` and align with `config` and `global_params` in the code.

---

## 4. `Maritime Hackathon 2026_Calculation Methodology.docx`

**Word document** — describes the **exact calculation methodology** (formulas for fuel cost, carbon cost, CAPEX amortization, risk premium, etc.). Use this as the single source of truth for implementing the cost model. The `.docx` format is binary; read it in Word or export to text/markdown to implement the formulas in `src/cost_model.py`.

---

## 5. `submission_template.csv` (official)

**Submission format** — do not change column order. Fill the **Submission** column (4th column) with your team’s values.

| Header Name | Data Type | Units | Submission (your values) |
|-------------|-----------|-------|---------------------------|
| team_name | String | - | |
| category | String | - | |
| report_file_name | String | - | e.g. MaritimeHackathon2026_CasePaper_teamname.pdf |
| sum_of_fleet_deadweight | Float | tonnes | |
| total_cost_of_fleet | Float | dollars | |
| average_fleet_safety_score | Float | - | |
| no_of_unique_main_engine_fuel_types_in_fleet | Integer | - | |
| sensitivity_analysis_performance | String | Yes/No | |
| size_of_fleet_count | Integer | - | |
| total_emission_CO2_eq | Float | tonnes | |
| total_fuel_consumption | Float | tonnes | |

Rename the file to **`teamname_submission.csv`** for submission.

---

## Column name mapping (given data → code)

| Given data column | Code / problem name |
|-------------------|----------------------|
| `mep` | `P` (main engine power, kW) |
| `boil_engine_fuel_type` | `aux_boiler_fuel_type` |
| `vessel_type_new` | `vessel_type` |
| (none) | `vessel_name` — use `vessel_id` or leave blank |

Use this mapping when building the ship-level table from `vessel_movements_dataset.csv` and when wiring the cost model to the dataset.
