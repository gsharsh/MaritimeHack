# Roadmap: Maritime Hackathon 2026 — Nickolas's Optimization Module

## Overview

MILP-based fleet optimization for the Smart Fleet Selection challenge. Starting from per_vessel.csv (produced by teammates), build a PuLP MILP optimizer to select the minimum-cost fleet, then run sensitivity analyses (safety thresholds, Pareto frontier, carbon price sweep) and generate submission outputs.

## Milestones

- ✅ **v1.0 Maritime Fleet Optimizer** - [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md) (Phases 1-6, shipped 2026-02-06)
- ✅ **v2.0 Submission Polish** - Phases 7-10 (shipped 2026-02-06)

## Domain Expertise

None

## Completed Phases

<details>
<summary>✅ v1.0 Maritime Fleet Optimizer (Phases 1-6) — SHIPPED 2026-02-06</summary>

- [x] **Phase 1: Clean Slate & Data Foundation** (3/3 plans) — 2026-02-06
- [x] **Phase 2: MILP Fleet Optimizer** (2/2 plans) — 2026-02-06
- [x] **Phase 3: Validation** (1/1 plan) — 2026-02-06
- [x] **Phase 4: Safety Threshold Sweep** (1/1 plan) — 2026-02-06
- [x] **Phase 5: Cost-Emissions Pareto Frontier** (2/2 plans) — 2026-02-06
- [x] **Phase 6: Submission & Charts** (2/2 plans) — 2026-02-06

</details>

### ✅ v2.0 Submission Polish (SHIPPED 2026-02-06)

**Milestone Goal:** Enhance optimizer outputs with shadow prices, additional charts (MACC, fleet composition), what-if analyses, and produce final deliverables (case paper + slides) for Maritime Hackathon 2026 submission.

#### Phase 7: Shadow Prices & What-If Analyses

**Goal**: Extract shadow prices via perturbation (DWT & safety constraints), run drop-diversity what-if, compute cost-per-DWT efficiency metrics
**Depends on**: v1.0 complete
**Research**: Unlikely (internal patterns — perturbation uses existing solver, what-if is a flag toggle)
**Plans**: 1

Plans:
- [x] 07-01: Shadow prices, diversity what-if, fleet efficiency + CLI wiring — 2026-02-06

#### Phase 8: Enhanced Charts

**Goal**: Fleet composition stacked bar chart across safety thresholds (C2) and Marginal Abatement Cost Curve from Pareto data (C3) — the visual centerpieces for stretch objective
**Depends on**: Phase 7 (needs sensitivity data with fleet lists)
**Research**: Unlikely (matplotlib charts, existing data structures)
**Plans**: TBD

Plans:
- [x] 08-01: MACC chart, carbon sweep chart, wire into run.py — 2026-02-06

#### Phase 9: Case Paper & Slides

**Goal**: Write 3-page case paper (problem/solution, sensitivity analysis, beyond-the-brief) and 6-slide presentation deck using all generated outputs
**Depends on**: Phase 8 (needs all charts and analysis numbers)
**Research**: Unlikely (writing deliverables from existing artifacts)
**Plans**: 1

Plans:
- [x] 09-01: Case paper + presentation outline — 2026-02-06

#### Phase 10: Final Validation & Submission

**Goal**: Re-verify all 4 constraints independently, generate all outputs end-to-end, finalize REPmonkeys_submission.csv, package deliverables
**Depends on**: Phase 9
**Research**: Unlikely (running existing pipeline, final checks)
**Plans**: TBD

Plans:
- [x] 10-01: Run production pipeline, fill placeholders, validate constraints — 2026-02-06

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|---------------|--------|-----------|
| 1. Clean Slate & Data Foundation | v1.0 | 3/3 | Complete | 2026-02-06 |
| 2. MILP Fleet Optimizer | v1.0 | 2/2 | Complete | 2026-02-06 |
| 3. Validation | v1.0 | 1/1 | Complete | 2026-02-06 |
| 4. Safety Threshold Sweep | v1.0 | 1/1 | Complete | 2026-02-06 |
| 5. Cost-Emissions Pareto Frontier | v1.0 | 2/2 | Complete | 2026-02-06 |
| 6. Submission & Charts | v1.0 | 2/2 | Complete | 2026-02-06 |
| 7. Shadow Prices & What-If Analyses | v2.0 | 1/1 | Complete | 2026-02-06 |
| 8. Enhanced Charts | v2.0 | 1/1 | Complete | 2026-02-06 |
| 9. Case Paper & Slides | v2.0 | 1/1 | Complete | 2026-02-06 |
| 10. Final Validation & Submission | v2.0 | 1/1 | Complete | 2026-02-06 |
