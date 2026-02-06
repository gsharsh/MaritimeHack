# Codebase Structure

**Analysis Date:** 2026-02-06

## Directory Layout

```
MaritimeHack/
├── run.py                    # Main CLI entry point & orchestrator
├── requirements.txt          # pip dependencies
├── README.md                 # Project documentation
├── config/                   # Project-level configuration
│   ├── __init__.py
│   └── params.yaml           # Cargo demand, constraints, sensitivity settings
├── src/                      # Core business logic (5 modules)
│   ├── __init__.py
│   ├── data_loader.py        # Data I/O & validation
│   ├── cost_model.py         # Cost computation (fuel, carbon, ownership, risk)
│   ├── optimization.py       # Fleet selection algorithm & validation
│   ├── sensitivity.py        # Parametric sensitivity analysis
│   └── utils.py              # Path helpers, voyage calculations, constants
├── data/                     # User-provided input data
│   ├── raw/                  # Ship CSV datasets
│   ├── processed/            # Cleaned/aggregated data
│   └── global_params/        # Emission factors, fuel prices, CAPEX
│       └── global_params.yaml.example
├── given_data/               # Hackathon-provided data (read-only reference)
│   ├── vessel_movements_dataset.csv
│   ├── llaf_table.csv
│   ├── calculation_factors.xlsx
│   ├── submission_template.csv
│   ├── submission_template - SAMPLE SUBMISSION.csv
│   └── Maritime Hackathon 2026_Calculation Methodology.docx
├── tests/                    # Unit tests
│   ├── __init__.py
│   ├── test_cost_model.py
│   └── test_optimization.py
├── outputs/                  # Generated results
│   ├── results/              # Fleet selection results, sensitivity summary
│   └── submission/           # Official submission CSV files
├── docs/                     # Documentation
│   ├── problem_summary.md
│   └── given_data_summary.md
└── notebooks/                # Jupyter exploration
    └── exploration.ipynb
```

## Directory Purposes

**config/**
- Purpose: Central project configuration
- Contains: `params.yaml` with cargo demand, constraints, sensitivity settings
- Key files: `params.yaml`

**src/**
- Purpose: Core algorithms and business logic
- Contains: 5 Python modules (data_loader, cost_model, optimization, sensitivity, utils)
- Key files: All `.py` files are core logic

**data/**
- Purpose: User-provided input data and parameters
- Contains: Raw ship CSVs, processed data, global parameter YAML
- Subdirectories: `raw/`, `processed/`, `global_params/`

**given_data/**
- Purpose: Hackathon-provided reference data (should not be modified)
- Contains: AIS vessel data, calculation factors, submission templates, methodology doc
- Key files: `vessel_movements_dataset.csv` (main data source)

**tests/**
- Purpose: Unit test suite
- Contains: pytest test files for cost_model and optimization
- Key files: `test_cost_model.py`, `test_optimization.py`

**outputs/**
- Purpose: Generated results from optimization runs
- Contains: Fleet selection results, sensitivity summaries, submission CSVs
- Subdirectories: `results/`, `submission/`

**docs/**
- Purpose: Problem and data documentation
- Contains: Problem summary, data file descriptions
- Key files: `problem_summary.md`, `given_data_summary.md`

**notebooks/**
- Purpose: Interactive data exploration
- Contains: Jupyter notebook for analysis
- Key files: `exploration.ipynb`

## Key File Locations

**Entry Points:**
- `run.py`: Main CLI entry point (fleet optimization pipeline)

**Configuration:**
- `config/params.yaml`: Project parameters (cargo demand, constraints)
- `data/global_params/global_params.yaml.example`: Global parameter template
- `requirements.txt`: Python dependencies

**Core Logic:**
- `src/data_loader.py`: Data loading and validation
- `src/cost_model.py`: Per-ship cost calculations
- `src/optimization.py`: Fleet selection and constraint validation
- `src/sensitivity.py`: Sensitivity analysis wrapper
- `src/utils.py`: Path helpers and voyage calculations

**Testing:**
- `tests/test_cost_model.py`: Cost model unit tests
- `tests/test_optimization.py`: Optimization unit tests

**Documentation:**
- `README.md`: Project overview and usage
- `docs/problem_summary.md`: Problem statement recap
- `docs/given_data_summary.md`: Data file descriptions

## Naming Conventions

**Files:**
- snake_case.py for all Python modules (`cost_model.py`, `data_loader.py`)
- test_module_name.py for test files (`test_cost_model.py`)
- snake_case.yaml for config files (`params.yaml`)
- UPPERCASE.md for important docs (`README.md`)

**Directories:**
- lowercase with underscores: `given_data/`, `global_params/`
- lowercase single words: `src/`, `tests/`, `docs/`, `config/`, `data/`, `outputs/`

**Special Patterns:**
- `__init__.py` in `src/`, `tests/`, `config/` for Python packaging
- `.example` suffix for template config files

## Where to Add New Code

**New Cost Component:**
- Implementation: `src/cost_model.py` (add function)
- Integration: `run.py` (call in cost loop)
- Tests: `tests/test_cost_model.py`

**New Optimization Algorithm:**
- Implementation: `src/optimization.py` (add function)
- Integration: `run.py` (swap selection call)
- Tests: `tests/test_optimization.py`

**New Data Source:**
- Loader: `src/data_loader.py` (add loading function)
- Data file: `data/raw/` or `given_data/`
- Tests: `tests/test_data_loader.py` (create if needed)

**New Analysis:**
- Implementation: `src/sensitivity.py` or new `src/analysis_name.py`
- Integration: `run.py` (add CLI flag and call)

**Utilities:**
- Shared helpers: `src/utils.py`
- Constants: `src/utils.py` (UPPER_SNAKE_CASE)

## Special Directories

**given_data/**
- Purpose: Hackathon-provided reference data
- Source: Downloaded from hackathon organizers
- Committed: Yes (read-only reference)

**outputs/**
- Purpose: Generated results from optimization runs
- Source: Auto-generated by `run.py`
- Committed: Partially (directory structure committed, results may not be)

---

*Structure analysis: 2026-02-06*
*Update when directory structure changes*
