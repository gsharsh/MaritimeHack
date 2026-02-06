---
phase: 09-case-paper-slides
plan: 01
subsystem: deliverables
tags: [case-paper, presentation, markdown, placeholder-values]

# Dependency graph
requires:
  - phase: 06-submission-charts
    provides: chart patterns, submission CSV, Pareto chart
  - phase: 07-shadow-prices-what-if
    provides: shadow prices, diversity what-if, fleet efficiency
  - phase: 08-enhanced-charts
    provides: MACC chart, carbon sweep chart
provides:
  - outputs/deliverables/case_paper.md (3-page case paper, PDF-ready)
  - outputs/deliverables/presentation_outline.md (6-slide outline)
affects: [production-run-number-fill]

# Tech tracking
tech-stack:
  added: []
  patterns: [placeholder-values-for-deferred-data]

key-files:
  created: [outputs/deliverables/case_paper.md, outputs/deliverables/presentation_outline.md]
  modified: []

key-decisions:
  - "All numerical results use {placeholder} syntax for production-run fill"
  - "Case paper structured as 3 sections matching hackathon requirements"
  - "Presentation outline includes timing, visuals, and speaker notes per slide"
  - "All 5 charts referenced as Figures 1-5"

patterns-established:
  - "Placeholder pattern: {snake_case_name} for all production-dependent values"

issues-created: []

# Metrics
duration: 5min
completed: 2026-02-06
---

# Phase 9 Plan 1: Case Paper & Presentation Outline Summary

**Case paper (Markdown, PDF-ready) and 6-slide presentation outline with placeholder values for production-run number fill**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-06
- **Completed:** 2026-02-06
- **Tasks:** 2
- **Files created:** 2

## Accomplishments
- Created case_paper.md: cover + 3 sections (Problem & Approach, Results & Sensitivity, Beyond the Brief)
- Created presentation_outline.md: 6 slides with title, bullets, visual references, and timing (total 10 min)
- All 5 charts referenced (pareto_frontier, fleet_composition, safety_comparison, macc, carbon_price_sweep)
- 28 unique {placeholder} values in case paper, 22 in presentation outline
- Body word count: 610 words (well within 1500 limit for ~3 pages)
- No hardcoded test fixture numbers

## Task Commits

Each task was committed atomically:

1. **Task 1: Write case paper** - `8a2ba5c` (feat)
2. **Task 2: Write presentation outline** - `67339f8` (feat)

## Files Created
- `outputs/deliverables/case_paper.md` - 3-page case paper with cover, methodology, results, and beyond-the-brief sections
- `outputs/deliverables/presentation_outline.md` - 6-slide outline with timing, visuals, and speaker notes

## Decisions Made
- All numerical results use {placeholder} syntax since per_vessel.csv is not yet available
- Case paper follows academic style: concise, no filler, every sentence adds information
- Presentation timing: 0.5 + 2.0 + 2.0 + 2.5 + 2.0 + 1.0 = 10.0 min
- Charts referenced as Figures 1-5 with captions

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Steps
- Drop per_vessel.csv into data/processed/ when teammates deliver it
- Run `python run.py --all` to generate production numbers
- Search-and-replace all {placeholder} values with actual results
- Export case_paper.md to PDF for submission

---
*Phase: 09-case-paper-slides*
*Completed: 2026-02-06*
