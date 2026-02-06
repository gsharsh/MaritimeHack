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
- ✓ **Shadow prices & what-if analyses** — v2.0: DWT/safety perturbation, diversity what-if, fleet efficiency
- ✓ **Enhanced charts** — v2.0: MACC from Pareto data, carbon price sweep dual-subplot
- ✓ **Case paper & presentation** — v2.0: 3-page paper + 6-slide outline with production numbers
- ✓ **Production validation** — v2.0: 108-vessel run, independent constraint checks, submission packaged

### Active

None — all v2.0 requirements shipped.

### Out of Scope

- Steps 0-6 (data processing pipeline) — teammates A+B's responsibility
- Step 9 (carbon price sensitivity) — Teammate C's responsibility

## Context

**Hackathon:** Maritime Hackathon 2026, organized by MPA Singapore. Submission deadline: 7 Feb 2026 09:00 SGT.

**Current state:** v2.0 shipped. 3,639 LOC Python. Tech stack: PuLP, pandas, matplotlib, numpy. Production run complete with 108-vessel dataset: 21 vessels selected, $19.7M cost, all constraints satisfied.

**Team structure:** Nickolas handles Steps 7, 8, 10 (optimization). Teammates A+B handle Steps 0-6 (data processing → per_vessel.csv). Teammate C handles Step 9 (carbon price sensitivity).

**Data handoff:** per_vessel.csv received with 108 rows. Production run complete.

**Production run:** `python run.py --all --team-name "REPmonkeys" --category "A" --report-file "case_paper.pdf"`

## Constraints

- **Timeline**: Submission due 7 Feb 2026 09:00 SGT
- **Dependency**: per_vessel.csv received and processed
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
| Shadow prices via perturbation | +1% DWT, +0.1 safety — standard OR technique | ✓ Good |
| MACC from Pareto shadow prices | Sorted cheapest-first, color-coded by cost tier | ✓ Good |
| Placeholder syntax for deliverables | {placeholder} filled at production run time | ✓ Good |
| Independent constraint validation | Separate from MILP — cross-checks submission | ✓ Good |

---
*Last updated: 2026-02-06 after v2.0 milestone*
