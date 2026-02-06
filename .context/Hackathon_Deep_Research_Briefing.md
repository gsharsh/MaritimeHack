# Maritime Hackathon 2026 — Deep Research & Competitive Edge Briefing

---

## PART 1: DOMAIN KNOWLEDGE YOUR TEAM NEEDS

### 1.1 The Route: Singapore → Port Hedland

Two major sources give different distances: **1,683 NM** (SeaRoutes) and **2,206 NM** (Ports.com). However, **the AIS data tells the real story.** From the actual vessel tracks:

- **Mean voyage distance: ~1,762 NM** (computed from AIS lat/lon waypoints)
- **Median: ~1,644 NM**
- **Typical voyage: 5–8 days** for well-performing ships

**You do NOT need to estimate route distance** — the AIS data already captures the full voyage for each ship. Your calculations should use the actual per-ship AIS timestamps and positions. This is a crucial insight: each ship's fuel consumption will differ based on its actual speed profile and voyage duration, not a theoretical distance.

### 1.2 Voyage Duration Problem

**Critical finding:** 2 out of 108 ships take >30 days in the dataset:
- Vessel **10007920**: 73.5 days (DWT 171,810, Safety=1, Distillate) — appears to have drifted/waited extensively
- Vessel **10372190**: 38.5 days (DWT 209,951, Safety=3, Distillate) — significant anchorage time (14 records)

Since the problem says cargo must move "in one month," you should consider whether these ships are viable. However, **fuel and emissions are only calculated for Transit and Maneuver modes**, so the cost model handles this — they'll just have proportionally more transit fuel burn. Both are Distillate ships (54 available), so excluding them won't break the fuel-type constraint.

### 1.3 Operating Modes — What Counts

Only **Transit** and **Maneuver** modes contribute to fuel/emissions. The data breaks down as:
- Transit: ~92% of all AIS records
- Maneuver: ~4.3%
- Anchorage: ~2.9%
- Drifting: ~0.8%

Anchorage and Drifting records are ignored for fuel/emission calculations. This means ships that spent a long time at anchor will still only be charged for their actual sailing time.

### 1.4 RightShip Safety Score System

RightShip (one of the hackathon co-organizers) is the world's largest maritime operational due diligence organization. Their Safety Score (1–5) is the real industry standard used by major charterers like BHP, Vale, Cargill, and Rio Tinto.

Key facts for your presentation:
- **Score 3–5**: Ships "working towards best practice" — the industry standard minimum most charterers accept
- **Score 1–2**: Ships "needing improvement" — many charterers won't even consider them
- **Score is based on**: Incident history (highest weight), DOC holder performance (high weight), PSC deficiencies, detentions, flag performance, and classification society
- **In real life**, a score below 3 effectively makes a ship commercially unviable on major routes

This context matters for your sensitivity analysis: moving from avg≥3 to avg≥4 mimics a real-world trend where charterers demand safer vessels.

### 1.5 GWP Values — Why They Matter

The hackathon uses IPCC AR5 values:
- **CO₂**: GWP = 1
- **N₂O**: GWP = 265
- **CH₄**: GWP = 28

N₂O has a massive multiplier (265×). Even tiny N₂O emissions become significant when converted to CO₂eq. Ships burning LNG have **zero CH₄ emission factor** in the Cf table, and **lower N₂O** (0.00011 vs 0.00018 for most fuels). Hydrogen has **zero for all three** — making it the cleanest fuel by emissions despite being the most expensive.

Ammonia also has **zero CO₂ emission factor** — meaning zero carbon cost. This partially offsets its higher fuel price.

### 1.6 The LLAF Table — When It Matters

The Low Load Adjustment Factor inflates emissions at low engine load percentages. At typical transit speeds, most ships operate at Load Factor > 20%, meaning **LLAF = 1.0** (no adjustment).

LLAF matters during:
- **Maneuvering at low speeds** (entering/leaving port)
- **Ships with high design speed but low actual speed**

At 2% load (the minimum), CO₂ LLAF is 3.28× and CH₄ LLAF is 21.18× — a massive multiplier. For ships that spend time maneuvering slowly, this can significantly increase emission calculations.

### 1.7 Fuel Cost Landscape

| Fuel | Cost/tonne (USD) | CO₂ per tonne fuel | Net carbon cost/tonne | Effective cost (fuel+carbon) |
|---|---|---|---|---|
| Distillate | $555 | 3.206t | $256 | **$811** |
| LPG Propane | $695 | 3.000t | $240 | **$935** |
| LPG Butane | $686 | 3.030t | $242 | **$928** |
| LNG | $720 | 2.750t | $220 | **$940** |
| Ammonia | $744 | 0t | $0 | **$744** |
| Methanol | $1,075 | 1.375t | $110 | **$1,185** |
| Ethanol | $1,447 | 1.913t | $153 | **$1,600** |
| Hydrogen | $6,000 | 0t | $0 | **$6,000** |

**Key insight:** Ammonia is actually competitive when you include carbon cost — it's cheaper than LNG, LPG, and Methanol on an effective basis because it has zero CO₂ emissions. Distillate remains cheapest overall. Hydrogen is in a league of its own at $6,000/tonne.

### 1.8 CAPEX Anomaly

The ship cost table has a non-intuitive structure:
- 55–80k DWT: **$80M** base
- 80–120k DWT: **$78M** base (cheaper!)
- >120k DWT: **$90M** base

The 80–120k bucket is a sweet spot for CAPEX per DWT. Combined with the fact that 62 of 108 ships are >120k DWT, the fleet is skewed toward large ships.

---

## PART 2: OPTIMIZATION MODEL FACTORS

### 2.1 Decision Variables
Binary: x_i ∈ {0,1} for each ship i = 1..108

### 2.2 Objective Function
Minimize: Σ(x_i × final_adjusted_cost_i)

### 2.3 Constraints (Linearized)

**Demand:** Σ(x_i × DWT_i) ≥ 4,576,667

**Safety average ≥ 3:** This is nonlinear as written (average = sum/count). Linearize it:
```
Σ(x_i × safety_i) ≥ 3.0 × Σ(x_i)
→ Σ(x_i × (safety_i - 3.0)) ≥ 0
```
This is now a linear constraint! Each ship contributes (safety_score - 3) when selected.

**Fuel type coverage:** For each fuel type f ∈ {8 types}:
Σ(x_i for i with fuel_type=f) ≥ 1

### 2.4 Pre-computation (Before Optimization)

For each ship, pre-compute from AIS data:
1. Total fuel consumption (tonnes) — sum across all Transit+Maneuver rows
2. Total CO₂eq emissions (tonnes) — including LLAF adjustments
3. Fuel cost (USD)
4. Carbon cost (USD)
5. Monthly CAPEX (USD)
6. Risk premium (USD)
7. Final adjusted cost (USD)

These become constants in the optimization — the MILP solver just picks the combination.

### 2.5 Solver Recommendation

**PuLP with CBC** (free, comes with PuLP) — perfectly adequate for 108 binary variables. This is a small problem by MILP standards.

```python
from pulp import *
prob = LpProblem("FleetSelection", LpMinimize)
x = {i: LpVariable(f"x_{i}", cat='Binary') for i in ship_ids}
prob += lpSum(x[i] * cost[i] for i in ship_ids)  # objective
prob += lpSum(x[i] * dwt[i] for i in ship_ids) >= 4576667  # demand
prob += lpSum(x[i] * (safety[i] - 3.0) for i in ship_ids) >= 0  # safety
for ft in fuel_types:
    prob += lpSum(x[i] for i in ships_by_fuel[ft]) >= 1
prob.solve()
```

---

## PART 3: YOUR COMPETITIVE EDGE

### Edge 1: Pareto Front Visualization (Cost vs Safety vs Emissions)

Most teams will submit a single optimal solution. **Stand out by presenting the Pareto frontier** — the set of non-dominated solutions showing the trade-off between cost, safety, and emissions.

How to do it:
- Run the optimizer at multiple safety thresholds: 2.5, 3.0, 3.5, 4.0, 4.5
- For each, record: total cost, avg safety, total CO₂eq
- Plot the Pareto curve: Cost vs Safety Score (with emissions as color/size)
- Show the "knee point" — where the marginal cost of additional safety is smallest

This demonstrates sophisticated multi-criteria thinking and directly addresses the sensitivity analysis stretch objective in a visual, impactful way.

### Edge 2: Marginal Cost of Safety Analysis

Calculate the **marginal cost per unit of safety improvement**:
```
ΔCost / ΔSafety = (Cost at safety≥4 - Cost at safety≥3) / (AvgSafety@4 - AvgSafety@3)
```

This tells decision-makers: "Each 0.1 improvement in average fleet safety costs $X." This is exactly the kind of insight a port authority or regulator would want.

### Edge 3: Fleet Composition Dashboard

Create a visual showing how fleet composition shifts as safety requirements tighten:
- At safety≥3: mostly cheap Distillate ships (avg safety 2.6)
- At safety≥4: more LNG, LPG, Ammonia ships (higher safety scores, greener fuels)

This reveals the **hidden link between safety and sustainability** — safer ships tend to use cleaner fuels. This is a powerful narrative for judges from RightShip (whose business is safety scoring).

### Edge 4: Emissions Intensity Metric

Go beyond the required outputs. Calculate **emissions intensity** = Total CO₂eq / Total DWT moved. This is essentially the fleet-level CII (Carbon Intensity Indicator) — the real IMO regulatory metric.

Show how this metric improves as you select safer/greener fleets, connecting your hackathon analysis to actual IMO 2023 GHG Strategy goals of reducing carbon intensity by 40% by 2030.

### Edge 5: "What If Carbon Price Doubles?" Sensitivity

The hackathon uses $80/tonne CO₂eq (2024 EU ETS price). But carbon prices are volatile and trending upward. Run your model at $80, $120, $160, $200 per tonne and show how fleet composition changes.

At higher carbon prices:
- Zero-carbon fuels (Ammonia, Hydrogen) become more competitive
- High-carbon fuels (Distillate, Ethanol) become less attractive
- Fleet "greens up" naturally through economic incentive

This shows awareness of real-world market dynamics and demonstrates your model's flexibility.

### Edge 6: Speed Optimization Insight (Advanced)

The AIS data contains actual speed at each timestamp. Some ships sail slower than their design speed (slow steaming), which:
- Reduces fuel consumption (cubic relationship: LF = (AS/MS)³)
- Reduces emissions
- But increases voyage time

You could briefly note that real operators use speed optimization to reduce costs — but in this hackathon, the speeds are fixed by the AIS data. This shows maritime domain awareness.

### Edge 7: Connect to IMO Regulatory Context

In your presentation/report, mention:
- **IMO CII** (Carbon Intensity Indicator): Ships rated A–E on operational efficiency. Your fleet selection inherently optimizes CII.
- **IMO 2023 GHG Strategy**: Net-zero by 2050, 40% carbon intensity reduction by 2030.
- **RightShip's GHG Rating**: Beyond safety, RightShip also rates vessels on greenhouse gas performance.
- **EU ETS**: Since 2024, shipping is covered by EU emissions trading.

This regulatory awareness will impress the NUS Centre for Maritime Studies and RightShip judges.

---

## PART 4: GOTCHAS & PITFALLS TO AVOID

### Pitfall 1: Fuel Cost Calculation Ambiguity
The methodology doc says to use `main_engine_fuel_type` for fuel cost, but aux engines/boilers always use Distillate. Calculate ME fuel cost using ME fuel price, and AE/AB fuel cost using Distillate price. Since all aux fuels are Distillate, this should match either interpretation.

### Pitfall 2: SFC Adjustment Only Affects Main Engine
`sfc_adjusted = sfc × (42.7 / LCV)`. For Distillate (LCV=42.7), this is 1.0 — no change. Aux engines and boilers always use Distillate, so their SFC stays the same. Only ME SFC changes for non-Distillate ships.

### Pitfall 3: Activity Hours Calculation
"A" is the time difference between **consecutive timestamps for the same vessel**. The last row of each vessel has no "next" row — you need to handle this edge case (typically drop it or use zero).

### Pitfall 4: Load Factor Rounding
LF is rounded to 2 decimal places. %LF (for LLAF lookup) is rounded to nearest integer. If %LF < 2% and mode is Transit/Maneuver, default to 2%.

### Pitfall 5: CRF and CAPEX Units
CAPEX is in **million USD**. CRF formula gives an annuity factor. The annual cost formula includes both principal recovery and return on salvage. Convert to monthly by dividing by 12. Don't forget to convert back to USD (multiply by 1,000,000).

### Pitfall 6: Safety Constraint is Average, Not Minimum
You CAN include safety=1 ships — as long as they're balanced by safety=4 and safety=5 ships. Each safety=1 ship needs offsetting: one safety=5 ship to average to 3.0.

### Pitfall 7: The >30 Day Ships
Two ships have voyage durations >30 days in the AIS data. The fuel/emission calculation uses actual transit+maneuver hours (which will be high for these ships), making them expensive. The optimizer should naturally avoid them.

---

## PART 5: DATA-DRIVEN FLEET INSIGHTS

### Safety vs Cost Tension
- **Distillate ships**: avg safety 2.6, cheapest fuel — but drag down fleet safety average
- **LPG Propane**: avg safety 4.7, moderate fuel cost — excellent safety score suppliers
- **LPG Butane**: avg safety 4.0
- **LNG**: avg safety 3.8
- **Ammonia**: avg safety 3.5, zero carbon

The optimizer must balance cheap Distillate ships (low safety) with enough high-safety ships to maintain the ≥3.0 average.

### Forced Selections (Only 2–3 ships available)
- **Hydrogen**: 2 ships only — DWT 114,563 and 178,838. Pick the one with lower total cost.
- **LPG Butane**: 3 ships — DWT 49,861, 181,469, 210,909
- **LPG Propane**: 3 ships — DWT 39,781, 205,905, 206,118

These forced picks contribute ~500k–1.5M DWT and significantly influence the achievable safety average.

### Cost Efficiency Ranking ($/DWT)
- **Most efficient**: Large Distillate ships with safety 2+ ($3.81–$4.20/DWT)
- **Mid range**: Large LNG ships ($4.58/DWT), LPG ($5.40–5.50/DWT)
- **Expensive**: Methanol ($7.29+/DWT), Ethanol ($7.54+/DWT)
- **Very expensive**: Small ships and Hydrogen ($8.32/DWT for best Hydrogen ship)

### Zero-Boiler Ships (Free DWT)
7 ships have auxiliary boiler load = 0, saving fuel on every voyage. These include 3 Methanol, 2 Distillate, 1 LPG Propane, 1 LNG ship.

---

## PART 6: PRESENTATION STRATEGY

For the 4–6 slide, 10-minute presentation:

**Slide 1: Problem Understanding** — Route map, monthly demand derivation (54.92M ÷ 12), constraint summary

**Slide 2: Methodology** — Cost model pipeline diagram (fuel → carbon → CAPEX → risk premium), optimization approach (MILP)

**Slide 3: Fleet Selection Results** — Key outputs table, fleet composition pie chart by fuel type, safety score distribution

**Slide 4: Sensitivity Analysis** — Pareto curve (cost vs safety threshold), side-by-side comparison tables for safety≥3 vs safety≥4

**Slide 5: Strategic Insights** — The hidden link between safety and sustainability, marginal cost of safety, emissions intensity comparison, regulatory context (IMO CII, EU ETS)

**Slide 6: Conclusion** — Key recommendations, what-if scenarios (carbon price sensitivity), future considerations
