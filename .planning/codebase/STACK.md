# Technology Stack

**Analysis Date:** 2026-02-06

## Languages

**Primary:**
- Python 3.10+ - All application code (uses `|` union types, modern type hints)

**Secondary:**
- YAML - Configuration files (`config/params.yaml`, `data/global_params/global_params.yaml.example`)

## Runtime

**Environment:**
- Python 3.10+ (no version pinned via `.python-version` or `pyproject.toml`)
- No browser runtime (CLI/script execution only)

**Package Manager:**
- pip - `requirements.txt`
- No lockfile (no pip.lock, poetry.lock, etc.)
- No virtual environment committed

## Frameworks

**Core:**
- None (vanilla Python CLI script)

**Testing:**
- pytest >=7.0.0 - Unit tests

**Build/Dev:**
- No build tools (interpreted Python)
- Jupyter >=1.0.0 (optional, commented out in `requirements.txt`)

## Key Dependencies

**Critical:**
- pandas >=2.0.0 - Core data manipulation, DataFrame-centric pipeline - `requirements.txt`
- PyYAML >=6.0 - Configuration parsing (params, global_params) - `requirements.txt`

**Optional (commented out):**
- PuLP >=2.7.0 - Linear optimization solver (alternative to greedy) - `requirements.txt`
- OR-Tools >=9.0 - Google's optimization library (alternative solver) - `requirements.txt`

## Configuration

**Environment:**
- No environment variables required
- `.env` in `.gitignore` but no `.env` files present
- All configuration via YAML files

**Config Hierarchy:**
- Project config: `config/params.yaml` (cargo demand, constraints, sensitivity)
- Global parameters: `data/global_params/global_params.yaml` (emission factors, fuel prices, CAPEX, CRF)
- CLI overrides: `run.py --ships`, `--global-params`, `--config`, `--out-dir`

## Platform Requirements

**Development:**
- Any platform with Python 3.10+
- No external dependencies (no Docker, no database)

**Production:**
- Standalone CLI execution (`python run.py`)
- Hackathon submission context (not deployed as service)

---

*Stack analysis: 2026-02-06*
*Update after major dependency changes*
