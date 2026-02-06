# Solution Summary (2-Slide Presentation)

---

## Slide 1: How We Solved It -- Two Complementary Approaches

### Problem
Select the minimum-cost fleet of Chemical/Products Tankers to deliver 4.58M tonnes/month of bunker fuel from Singapore to Port Hedland, subject to safety, emissions, and fuel-diversity requirements.

### Approach 1: Cost-Minimising MILP (Base Case)

Binary optimisation over 108 candidate vessels:

- **Decision:** Select or reject each vessel (binary 0/1)
- **Objective:** Minimise total fleet cost under current assumptions
- **Solver:** PuLP + COIN-OR CBC -- provably optimal, not heuristic

### Approach 2: Min-Max Robust MILP (Stress-Tested)

Same binary selection, but adds a continuous variable Z (worst-case cost):

- **Objective:** Minimise Z, where Z >= fleet cost under every stress scenario
- **Scenarios:** Base ($80/t carbon, safety >= 3.0), safety stress (safety >= 4.0), carbon stress ($160/t), joint stress (both)
- **Result:** One fleet that performs well no matter which scenario materialises

### Cost Model (4 components per vessel, shared by both approaches)

| Component | What it captures |
|-----------|-----------------|
| **Fuel cost** | Main engine fuel (type-specific pricing) + auxiliary/boiler (Distillate) |
| **Carbon cost** | CO2-equivalent emissions x $80/tCO2eq (CH4 GWP=28, N2O GWP=265) |
| **Ownership cost** | CAPEX amortised over 30 years at 8% discount rate, with fuel-type premiums |
| **Risk premium** | Safety-linked surcharge (+10% for score 1) or discount (-5% for score 5) |

### Key Constraints

| # | Constraint | Base MILP | Robust MILP |
|---|-----------|-----------|-------------|
| 1 | Fleet DWT >= 4.58M tonnes | Same | Same |
| 2 | Avg safety score >= threshold | >= 3.0 | >= 4.0 (strictest across scenarios) |
| 3 | >= 1 vessel per fuel type (8 types) | Same | Same |
| 4 | Scenario cost bounds: fleet cost <= Z for all scenarios | -- | 4 scenario constraints |

### Data Pipeline

Raw AIS data (13,216 rows) --> operating mode classification --> engine load from speed (cubic law) --> fuel consumption with SFC adjustment for alternative fuels --> emissions with Low-Load Adjustment Factors --> per-vessel cost aggregation (108 vessels) --> MILP / Robust MILP optimisation

---

## Slide 2: Results & Insights

### Head-to-Head Comparison

| Metric | Base MILP | Robust Min-Max |
|--------|-----------|----------------|
| Fleet size | **21 vessels** | **22 vessels** |
| Total cost (base scenario) | **$19.7M/month** | **$20.8M/month** |
| Worst-case cost | -- | **$21.7M/month** |
| Total DWT | 4,577,756 t | 4,580,084 t |
| CO2-equivalent | 13,095 t | 11,756 t (-10.2%) |
| Avg safety score | 3.24 | 4.00 |
| Fuel types covered | All 8 | All 8 |

The robust fleet costs 5.4% more today but **caps worst-case exposure** at $21.7M, achieves a **higher safety score** (4.0 vs 3.24), and produces **10% fewer emissions** -- all as side-effects of hedging against carbon price and safety-regulation uncertainty.

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

1. **Robust optimisation provides a practical insurance policy** -- 5.4% higher base cost buys resilience against carbon price doubling and stricter safety regulation, with bonus emission reductions
2. **Fuel diversity and moderate safety improvements are achievable at manageable cost** -- the first 80% of benefit comes at 20% of maximum cost
3. **Aggressive decarbonisation follows exponential cost curves** -- policymakers face sharply diminishing returns beyond moderate targets
4. **Carbon pricing is an effective policy lever** -- doubling the carbon price from $80 to $160/t shifts fleet composition meaningfully without extreme cost impact
5. **The demand constraint is the tightest binding constraint** -- fleet selection is primarily driven by finding enough capacity at minimum cost, with safety and diversity as secondary shapers
