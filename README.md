# MaritimeHack — Smart Fleet Selection

**Maritime Hackathon 2026 | Team REPmonkeys | Category A**

Select the optimal fleet of Chemical/Products Tankers to transport bunker fuel from Singapore to Port Hedland (Australia West Coast), minimising cost while meeting safety, emissions, and fuel-diversity constraints.

## Approach

We solve the problem in two stages:

1. **Base MILP** -- binary integer linear program minimising total fleet cost under current assumptions (21 vessels, $19.7M/month)
2. **Min-Max Robust MILP** -- stress-tests the base solution across 4 scenarios (carbon price $80-$160/t, safety threshold 3.0-4.0), then selects one fleet that minimises worst-case cost (22 vessels, $20.8M base / $21.7M worst-case)

We submit the **robust fleet** -- 5.4% higher base cost buys resilience against carbon price doubling and stricter safety regulation, with 10% lower emissions and a safety score of 4.0.

See `docs/` for full documentation of assumptions, constraints, results, and a presentation summary.

## Project Structure

```
MaritimeHack/
├── run.py                          # Main pipeline: MILP + robust + sweeps + submission
├── run_sensitivity_analysis.py     # Fixed-fleet sensitivity analysis with charts
├── requirements.txt
│
├── src/
│   ├── constants.py                # SOP parameters (demand, prices, emission factors, CAPEX)
│   ├── data_loader.py              # AIS data processing: modes, load factors, fuel, emissions
│   ├── data_adapter.py             # Load per_vessel.csv with validation
│   ├── cost_model.py               # 4-component cost model (fuel + carbon + CAPEX + risk)
│   ├── optimization.py             # Base MILP + min-max robust MILP solvers
│   ├── sensitivity.py              # Safety/carbon/Pareto sweeps, shadow prices, diversity analysis
│   ├── charts.py                   # Pareto, MACC, fleet composition, carbon sweep charts
│   └── visualize_sensitivity.py    # Tornado, dashboard, sensitivity plots
│
├── data/
│   └── processed/per_vessel.csv    # 108 vessels with pre-computed costs (pipeline input)
│
├── given_data/                     # Hackathon-provided data and templates
│
├── outputs/
│   ├── results/                    # chosen_fleet.csv, robust_fleet.csv
│   ├── charts/                     # 6 main charts (pareto, MACC, fleet composition, etc.)
│   ├── sensitivity/                # CSVs + 8 sensitivity plots (robust fleet)
│   ├── submission/                 # submission_template.csv (filled, robust fleet values)
│   └── deliverables/               # case_paper.md, presentation_outline.md
│
├── docs/
│   ├── assumptions.md              # 25 modelling assumptions
│   ├── constraints.md              # Full MILP + robust constraint formulations
│   ├── results.md                  # Base vs robust results, sensitivity insights
│   └── solution.md                 # 2-slide presentation summary
│
├── tests/                          # pytest suite (MILP, cost model, data, robust)
└── config/params.yaml              # Runtime parameters
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate              # Windows
# source .venv/bin/activate         # macOS/Linux
pip install -r requirements.txt
```

## Usage

### Full production run (robust fleet + all analyses + submission CSV)

```bash
python run.py --all --robust --team-name "REPmonkeys" --category "A" --report-file "case_paper.pdf"
```

### Individual components

```bash
# Base MILP only
python run.py

# Robust fleet only
python run.py --robust

# Safety sweep + Pareto frontier + carbon sweep + shadow prices
python run.py --all

# Fixed-fleet sensitivity analysis (uses robust fleet)
python run_sensitivity_analysis.py --use-minmax
```

### Tests

```bash
pytest tests/ -v
```

## Key Results (Robust Fleet)

| Metric | Value |
|--------|-------|
| Fleet size | 22 vessels |
| Base-scenario cost | $20,765,143/month |
| Worst-case cost | $21,705,607/month |
| Avg safety score | 4.00 |
| CO2-equivalent | 11,756 tonnes |
| Fuel types | All 8 |

## Submission

The submission CSV at `outputs/submission/submission_template.csv` is pre-filled with robust fleet values by `run.py --all --robust --submit`.

## Documentation

| Document | Contents |
|----------|----------|
| `docs/assumptions.md` | 25 modelling assumptions across data, cost, safety, fuel, and emissions |
| `docs/constraints.md` | Full mathematical formulation of base MILP and robust min-max MILP |
| `docs/results.md` | Base vs robust comparison, sensitivity insights, recommendation |
| `docs/solution.md` | 2-slide presentation summary with key figures |
