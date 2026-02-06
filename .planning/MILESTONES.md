# Project Milestones: Maritime Hackathon 2026 — Nickolas's Optimization Module

## v2.0 Submission Polish (Shipped: 2026-02-06)

**Delivered:** Production-ready submission with shadow prices, MACC, carbon sweep charts, case paper, presentation, and independently validated results from 108-vessel dataset.

**Phases completed:** 7-10 (4 plans total)

**Key accomplishments:**

- Shadow prices via constraint perturbation (DWT +1%, safety +0.1) and diversity what-if analysis
- MACC chart from Pareto frontier data and carbon price sweep dual-subplot chart (5 charts total)
- 3-page case paper and 6-slide presentation outline with all production numbers filled
- Full production run: 21 vessels, $19.7M cost, 4.58M DWT, 3.24 safety, 8 fuel types
- Independent constraint validation confirming all 4 constraints satisfied
- Submission CSV complete with team metadata (REPmonkeys, Category A)

**Stats:**

- 17 files changed, 1,761 insertions
- 4 phases, 4 plans, ~10 tasks
- Same day as v1.0 (~20 min execution time across 4 plans)

**Git range:** `feat(07-01)` → `feat(10-01)`

---

## v1.0 Maritime Fleet Optimizer (Shipped: 2026-02-06)

**Delivered:** Complete MILP-based fleet optimizer with sensitivity analyses, charts, and submission CSV — ready for Maritime Hackathon 2026 submission.

**Phases completed:** 1-6 (11 plans total)

**Key accomplishments:**

- PuLP binary MILP fleet optimizer minimizing cost subject to DWT, safety, and fuel diversity constraints
- 15-point epsilon-constraint Pareto frontier with shadow carbon prices
- Safety threshold sweep (3.0/3.5/4.0/4.5) with infeasible detection
- Carbon price sweep ($80/$120/$160/$200) with fleet re-optimization
- Submission CSV auto-filled from MILP results matching template exactly
- 3 matplotlib charts: Pareto frontier, fleet composition stacked bars, safety comparison table
- Single-command output: `python run.py --all` generates everything

**Stats:**

- 10 source files, 1,700 lines of Python
- 6 phases, 11 plans, ~22 tasks
- 1 day from start to ship (35 min execution time across 11 plans)

**Git range:** `feat(01-01)` → `feat(06-02)`

---
