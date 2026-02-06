# Maritime Hackathon 2026 — Nickolas's Optimization Module

## What This Is

MILP-based fleet optimization for the Maritime Hackathon 2026 Smart Fleet Selection challenge. Selects the minimum-cost fleet of ships to transport bunker fuel from Singapore to Australia West Coast, subject to DWT demand, safety, and fuel diversity constraints. Includes Pareto frontier analysis (cost vs emissions), safety threshold sweep, carbon price sweep, and automated submission output generation.

## Core Value

Produce a correct, optimal fleet selection via MILP that minimizes total cost while satisfying all constraints — this is the submission answer.

## Requirements

### Validated

- ✓ Project structure with src/, config/, data/, tests/ — existing
- ✓ Cost model functions (fuel, carbon, ownership, risk) — existing (`src/cost_model.py`)
- ✓ Data loading from vessel_movements_dataset.csv — existing (`src/data_loader.py`)
- ✓ Sensitivity analysis framework — existing (`src/sensitivity.py`)
- ✓ Basic unit tests for cost model and validation — existing (`tests/`)
- ✓ **MILP base fleet optimizer** (Step 7) — v1.0: PuLP binary MILP in `src/optimization.py`
- ✓ **Cost-Emissions Pareto frontier** (Step 8) — v1.0: 15-point epsilon-constraint sweep with shadow carbon prices
- ✓ **Safety threshold comparison** (Step 10) — v1.0: sweep at 3.0/3.5/4.0/4.5 with infeasible detection
- ✓ **Test fixtures from checkpoint vessels** — v1.0: 5 SOP checkpoint vessels in `tests/fixtures/`
- ✓ **Submission CSV generation** — v1.0: `--submit` flag fills `submission_template.csv`
- ✓ **Charts** — v1.0: Pareto frontier, fleet composition stacked bars, safety comparison table

### Active

None — all v1.0 requirements shipped.

### Out of Scope

- Steps 0-6 (data processing pipeline) — teammates A+B's responsibility
- Step 9 (carbon price sensitivity) — Teammate C's responsibility
- Case paper writing — team effort after results are ready
- Presentation slides — team effort after results are ready

## Context

**Hackathon:** Maritime Hackathon 2026, organized by MPA Singapore. Submission deadline: 7 Feb 2026 09:00 SGT.

**Current state:** v1.0 shipped. 1,700 LOC Python. Tech stack: PuLP, pandas, matplotlib, numpy.

**Team structure:** Nickolas handles Steps 7, 8, 10 (optimization). Teammates A+B handle Steps 0-6 (data processing → per_vessel.csv). Teammate C handles Step 9 (carbon price sensitivity).

**Data handoff:** Teammates will produce `data/processed/per_vessel.csv` with 108 rows. System auto-falls back to test fixtures when per_vessel.csv is absent.

**Production run:** `python run.py --all --team-name "X" --category "A" --report-file "report.pdf"`

## Constraints

- **Timeline**: Submission due 7 Feb 2026 09:00 SGT
- **Dependency**: Requires per_vessel.csv from teammates — code ready, awaiting data
- **Tech stack**: Python, PuLP for MILP, matplotlib for charts, pandas for data
- **Submission format**: Must match `given_data/submission_template.csv` column order exactly

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| PuLP MILP over greedy | MILP guarantees optimal solution; greedy was placeholder | ✓ Good |
| Replace src/optimization.py | Keep codebase clean, one optimizer module | ✓ Good |
| matplotlib for charts | Standard, lightweight, good for static exports | ✓ Good |
| per_vessel.csv at data/processed/ | Clean separation: teammates write, Nickolas reads | ✓ Good |
| Test with 5 checkpoint vessels | Validate MILP before real data arrives | ✓ Good |
| MONTHLY_DEMAND = 4,576,667 | SOP value from MPA AR 2024 p10 (54.92M / 12) | ✓ Good |
| Linearized safety constraint | sum(safety_i - threshold) >= 0 avoids nonlinear avg | ✓ Good |
| Epsilon-constraint for Pareto | Standard OR technique, re-uses existing MILP | ✓ Good |
| Shadow carbon price computation | Marginal cost per tonne CO2eq reduced | ✓ Good |
| Agg backend for matplotlib | Avoids Tkinter issues in headless/CLI mode | ✓ Good |

---
*Last updated: 2026-02-06 after v1.0 milestone*
