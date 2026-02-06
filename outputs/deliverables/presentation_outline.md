# Smart Fleet Selection: MILP-Based Optimization
## Presentation Outline (6 Slides, 10 Minutes)

---

## Slide 1: Title (0.5 min)

**Title:** Smart Fleet Selection: MILP-Based Optimization for Singapore-Australia Bunker Transport

**Bullets (Speaker Notes):**
- Team REPmonkeys, Category A, Maritime Hackathon 2026
- Objective: Select minimum-cost fleet from 108 vessels for monthly bunker transport
- Approach: Mixed-Integer Linear Programming with provably optimal solution
- Key deliverables: Optimal fleet, sensitivity analysis, policy insights

**Visual:** Title slide with team name, hackathon logo, and route map (Singapore to Port Hedland).

---

## Slide 2: Problem & Approach (2 min)

**Title:** The Fleet Selection Problem

**Bullets (Speaker Notes):**
- 108 Chemical/Products Tankers, 8 fuel types, safety scores 1-5, DWT range 14k-263k tonnes
- Four constraints: DWT >= 4,576,667t demand, avg safety >= 3.0, all 8 fuel types, single-use per vessel
- MILP formulation: binary decision variable per vessel, minimize total risk-adjusted cost (fuel + carbon + CAPEX +/- risk premium)
- Key insight: linearized safety constraint (SUM(safety_i - 3.0) >= 0) keeps problem fully linear; MILP guarantees optimality vs heuristic

**Visual:** Constraint diagram showing the four constraints as boxes feeding into the MILP solver, with the objective function displayed. Alternatively, a schematic of the cost model components (fuel cost + carbon cost + ownership + risk premium).

---

## Slide 3: Base Case Results (2 min)

**Title:** Optimal Fleet at Base Parameters

**Bullets (Speaker Notes):**
- Fleet of 21 vessels selected, total cost $19,706,493.72, DWT 4,577,756 tonnes
- Average safety score 3.24, all 8 fuel types represented
- Total CO2eq emissions: 13,095.28 tonnes, total fuel: 4,599.57 tonnes
- Solver confirms optimality: no feasible fleet exists at lower cost

**Visual:** Key metrics summary table:

| Metric | Value |
|---|---|
| Fleet size | 21 vessels |
| Total cost | $19,706,493.72 |
| Total DWT | 4,577,756 t |
| Avg safety | 3.24 |
| CO2eq | 13,095.28 t |
| Fuel types | 8 |

---

## Slide 4: Sensitivity Analysis (2.5 min)

**Title:** How Sensitive Is the Optimal Fleet?

**Bullets (Speaker Notes):**
- Safety threshold sweep (3.0 / 3.5 / 4.0 / 4.5): raising safety to 4.0 increases cost by 5.4%; threshold 4.5 is feasible at cost $23,251,571.47
- Shadow prices quantify constraint costs: DWT demand $4.19/tonne, safety $0.00/0.1-point
- Fuel diversity what-if: removing the 8-fuel-type requirement saves $1,116,062.40 (5.7%) but drops 5 fuel types
- Tradeoff is clear: moderate safety tightening is affordable, aggressive tightening may be infeasible

**Visual:** `safety_comparison.png` (Figure 3) showing fleet metrics across safety thresholds, or `fleet_composition.png` (Figure 2) showing fuel type mix shifts.

---

## Slide 5: Beyond the Brief (2 min)

**Title:** Cost-Emissions Tradeoffs & Policy Scenarios

**Bullets (Speaker Notes):**
- Pareto frontier (15-point epsilon-constraint): cost rises from $19,706,493.72 to $25,029,360.02 as CO2eq drops from 13,095.28 to 7,521.49 tonnes
- MACC identifies 2 abatement tranches below $80/tCO2eq reference price (cost-effective now)
- Carbon price sweep ($80-$200/t): at $200, fleet shifts toward Ammonia/Hydrogen; cost rises to $21,190,674.31
- Fleet efficiency: $4.3048/tDWT cost intensity, 0.002861 tCO2eq/tDWT emissions intensity

**Visual:** Split layout with `pareto_frontier.png` (Figure 1) on left and `macc.png` (Figure 5) on right. Or use `carbon_price_sweep.png` (Figure 4) as the primary visual.

---

## Slide 6: Recommendations & Conclusion (1 min)

**Title:** Recommendations

**Bullets (Speaker Notes):**
- The MILP-optimal fleet is provably the lowest-cost solution under base parameters
- Moderate safety tightening (to 3.5-4.0) improves fleet safety at manageable cost (5.4% increase)
- Carbon pricing above $120/tCO2eq drives meaningful fleet decarbonization; the MACC shows which reductions are cost-effective today
- Fuel diversity adds $1,116,062.40 but ensures supply-chain resilience against single-fuel disruptions
- Next steps: apply this framework to real operational planning with updated vessel data and route-specific constraints

**Visual:** Summary recommendation table or key takeaway callout boxes. Include a "decision matrix" showing the recommended operating point on the Pareto frontier.

---

## Timing Summary

| Slide | Topic | Duration |
|---|---|---|
| 1 | Title | 0.5 min |
| 2 | Problem & Approach | 2.0 min |
| 3 | Base Case Results | 2.0 min |
| 4 | Sensitivity Analysis | 2.5 min |
| 5 | Beyond the Brief | 2.0 min |
| 6 | Recommendations | 1.0 min |
| **Total** | | **10.0 min** |

## Chart Reference

| Figure | File | Used in Slide(s) |
|---|---|---|
| Figure 1 | `pareto_frontier.png` | 5 |
| Figure 2 | `fleet_composition.png` | 4 |
| Figure 3 | `safety_comparison.png` | 4 |
| Figure 4 | `carbon_price_sweep.png` | 5 |
| Figure 5 | `macc.png` | 5 |
