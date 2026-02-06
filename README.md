# MaritimeHack — Smart Fleet Selection

**Maritime Hackathon 2026:** Select the optimal fleet of ships to transport bunker fuel from **Singapore (A)** to **Australia West coast (B)** in one month, minimizing cost while meeting safety and sustainability constraints.

## Project structure

```
MaritimeHack/
├── config/
│   └── params.yaml          # Cargo demand, constraints, sensitivity settings
├── data/
│   ├── raw/                 # Ship dataset CSV, AIS data (place here)
│   ├── processed/           # Cleaned/aggregated data
│   └── global_params/       # Emission factors, fuel prices, CAPEX, safety rates
├── src/
│   ├── data_loader.py       # Load ships + global params
│   ├── cost_model.py        # Fuel, carbon, ownership, risk premium
│   ├── optimization.py     # Fleet selection (greedy), validation, outputs
│   ├── sensitivity.py       # Sensitivity analysis (safety constraint)
│   └── utils.py             # Voyage time, paths
├── outputs/
│   ├── results/             # Run results, sensitivity summary
│   └── submission/         # teamname_submission.csv (from template)
├── notebooks/
│   └── exploration.ipynb   # Data exploration
├── tests/
│   ├── test_cost_model.py
│   └── test_optimization.py
├── docs/
│   └── problem_summary.md   # Problem statement summary
├── run.py                   # Main entry: run optimization
└── requirements.txt
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Data

- **Given data** in `given_data/`: use `vessel_movements_dataset.csv` (AIS rows → one row per vessel is built automatically), `llaf_table.csv` (load vs emission factors), `calculation_factors.xlsx`, and the Calculation Methodology docx for formulas. See `docs/given_data_summary.md`.
- **Ships:** By default the pipeline uses `given_data/vessel_movements_dataset.csv`. Alternatively place a ship-level CSV in `data/raw/ships.csv` with columns: `vessel_id`, `vessel_type`, `dwt`, `vref`, `P`, `ael`, `abl`, `main_engine_fuel_type`, `aux_engine_fuel_type`, `aux_boiler_fuel_type`, `sfc_me`, `sfc_ae`, `sfc_ab`, `safety_score`. (Given data uses `mep`→P, `boil_engine_fuel_type`→aux_boiler_fuel_type.)
- **Global parameters:** Copy `data/global_params/global_params.yaml.example` to `global_params.yaml` and fill from `calculation_factors.xlsx` / methodology doc (emission factors, LCV, fuel price USD/GJ, carbon price, CAPEX, CRF, safety adjustment rates).
- **Cargo demand:** Set `cargo_demand_tonnes` in `config/params.yaml` from MPA Annual Report 2024 (Page 10), distributed over 12 months.

## Run

```bash
# From project root (with ships + global params in place)
python run.py

# Custom paths
python run.py --ships data/raw/ships.csv --global-params data/global_params/global_params.yaml

# With sensitivity analysis (re-run for min safety 3 and 4)
python run.py --sensitivity --out-dir outputs/results
```

Outputs: total DWT, total cost (USD), average safety score, unique fuel types, fleet size, total CO2e, total fuel consumption. With `--sensitivity`, a summary is written to `outputs/results/sensitivity_summary.txt` for the case paper.

## Submission

- Use the official template: `given_data/submission_template.csv` (or `outputs/submission/submission_template.csv`). Fill the **Submission** column only; rename to `teamname_submission.csv`. Do not alter column order. The code can output `submission_outputs()` with the same header names.
- Case paper: `MaritimeHackathon2026_CasePaper_teamname` (Word/PDF).
- Presentation: `teamname_presentation.ppt` (4–6 slides, ≤10 min).

See `docs/problem_summary.md` for a concise problem recap and required outputs.
