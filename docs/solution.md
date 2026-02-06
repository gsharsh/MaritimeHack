# Solution Summary (2-Slide Presentation)

---

## Slide 1: How We Solved It

### Problem
Select the minimum-cost fleet of Chemical/Products Tankers to deliver 4.58M tonnes/month of bunker fuel from Singapore to Port Hedland, subject to safety, emissions, and fuel-diversity requirements.

### Approach: Binary Integer Linear Programming (MILP)

We formulate a **binary optimisation** over 108 candidate vessels:

- **Decision:** Select or reject each vessel (binary 0/1)
- **Objective:** Minimise total fleet cost
- **Solver:** PuLP + COIN-OR CBC -- provably optimal, not heuristic

### Cost Model (4 components per vessel)

| Component | What it captures |
|-----------|-----------------|
| **Fuel cost** | Main engine fuel (type-specific pricing) + auxiliary/boiler (Distillate) |
| **Carbon cost** | CO2-equivalent emissions x $80/tCO2eq (CH4 GWP=28, N2O GWP=265) |
| **Ownership cost** | CAPEX amortised over 30 years at 8% discount rate, with fuel-type premiums |
| **Risk premium** | Safety-linked surcharge (+10% for score 1) or discount (-5% for score 5) |

### Key Constraints

| # | Constraint | Why it matters |
|---|-----------|----------------|
| 1 | Fleet DWT >= 4.58M tonnes | Must meet Singapore's monthly bunker demand |
| 2 | Avg safety score >= 3.0 | Ensures fleet-wide operational safety standards |
| 3 | >= 1 vessel per fuel type (8 types) | Supply-chain resilience against fuel disruptions |
| 4 | CO2 cap (sensitivity only) | Explores cost-emissions trade-off via Pareto frontier |

### Data Pipeline

Raw AIS data (13,216 rows) --> operating mode classification --> engine load from speed (cubic law) --> fuel consumption with SFC adjustment for alternative fuels --> emissions with Low-Load Adjustment Factors --> per-vessel cost aggregation (108 vessels) --> MILP optimisation

---

## Slide 2: Results & Insights

### Base Case Results

| Metric | Value |
|--------|-------|
| Fleet size | **21 vessels** |
| Total cost | **$19.7M/month** |
| Total DWT | 4,577,756 t (99.98% utilisation) |
| CO2-equivalent | 13,095 tonnes |
| Avg safety score | 3.24 |
| Fuel types covered | All 8 |

### Sensitivity Analysis -- What-If Scenarios

**Cost vs. Safety:**
Raising the safety threshold from 3.0 to 4.5 increases cost by 18% ($19.7M to $23.3M) and requires 5 additional vessels. Moderate improvements (to 3.5) cost only 2%.

**Cost vs. Emissions (Pareto Frontier):**
Initial CO2 reductions are cheap (~$21/tCO2eq) through fuel-switching. Aggressive decarbonisation to minimum-achievable emissions (7,521 t) costs $3,839/tCO2eq -- a 190x increase in marginal cost.

**Carbon Price Sensitivity:**
At $80/t, Distillate vessels dominate. Above $120/t, fleet composition shifts toward LNG and Ammonia. At $200/t, green fuels become strongly favoured.

**Fuel Diversity Premium:**
The all-8-fuel-types mandate costs $1.1M (5.7%) vs. an unconstrained fleet -- the price of supply-chain resilience.

### Key Takeaways

1. **Fuel diversity and moderate safety improvements are achievable at manageable cost** -- the first 80% of benefit comes at 20% of maximum cost
2. **Aggressive decarbonisation follows exponential cost curves** -- policymakers face sharply diminishing returns beyond moderate targets
3. **Carbon pricing is an effective policy lever** -- doubling the carbon price from $80 to $160/t shifts fleet composition meaningfully without extreme cost impact
4. **The demand constraint is the tightest binding constraint** -- fleet selection is primarily driven by finding enough capacity at minimum cost, with safety and diversity as secondary shapers
