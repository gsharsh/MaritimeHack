# Results

## The Story: From Cost-Optimal to Robust

Our solution follows a two-stage approach. First, we solve for the cheapest possible fleet under today's assumptions. Then, we stress-test those assumptions through sensitivity analysis, identify the key risks, and use that insight to build a second, robust fleet that hedges against regulatory and market uncertainty.

---

## Stage 1: Base Case -- Minimise Cost

We solve a binary MILP that selects the cheapest subset of 108 vessels meeting all hard constraints (demand, safety, fuel diversity).

| Metric | Value |
|--------|-------|
| Fleet size | 21 vessels |
| Total cost | $19,706,494 /month |
| Total DWT | 4,577,756 t (100.02% of demand) |
| Avg safety score | 3.24 (threshold: 3.0) |
| CO2-equivalent | 13,095 tonnes |
| Total fuel | 4,600 tonnes |
| Fuel types | All 8 represented |

This fleet is **provably optimal** for the base scenario -- no other combination of vessels can satisfy all constraints at lower cost. It achieves near-perfect capacity utilisation (only 1,089 t of slack) and clears the safety threshold with moderate headroom.

---

## Stage 2: Sensitivity Analysis -- Stress-Testing the Base Fleet

We then ask: *what happens to this fleet if conditions change?*

### Safety Threshold Sensitivity (re-optimising)

| Threshold | Fleet Size | Cost | Avg Safety |
|-----------|-----------|------|------------|
| 3.0 | 21 | $19.7M | 3.24 |
| 3.5 | 22 | $19.8M (+1%) | 3.50 |
| 4.0 | 22 | $20.8M (+5%) | 4.00 |
| 4.5 | 26 | $23.3M (+18%) | 4.50 |

Moderate safety improvements are cheap (+1% for threshold 3.5), but aggressive requirements get expensive fast (+18% for 4.5).

### Carbon Price Sensitivity (re-optimising)

| Carbon Price | Fleet Size | Cost | CO2eq |
|-------------|-----------|------|-------|
| $80/t | 21 | $19.7M | 13,095 t |
| $120/t | 22 | $20.2M | 12,351 t |
| $160/t | 22 | $20.7M | 12,069 t |
| $200/t | 22 | $21.2M | 12,069 t |

Rising carbon prices push the solver toward lower-emission vessels. At $200/t the fleet emits 8% less CO2 than the base case.

### Pareto Frontier (cost vs emissions)

The epsilon-constraint sweep reveals the full cost-emissions trade-off:
- **Cheap reductions:** First 1,500 t of CO2 cut at ~$13--$40/tCO2eq (fuel-switching)
- **Mid-range:** Next 2,700 t at $150--$300/tCO2eq
- **Expensive tail:** Final 1,100 t at $1,200--$6,900/tCO2eq (diminishing returns)

### Fuel Diversity Premium

Relaxing the all-8-fuel-types mandate saves $1.1M (5.7%), but concentrates the fleet on only 3 fuel types -- a significant supply-chain risk.

### Key Insight from Sensitivity

The base fleet fails safety constraints above 3.24 and faces rising costs under higher carbon pricing. These are realistic regulatory risks (IMO decarbonisation targets, tightening safety standards). This motivates a robust approach.

---

## Stage 3: Robust Fleet -- Min-Max Optimisation

Using the sensitivity insights, we define four stress scenarios and solve a min-max MILP that picks **one fleet** minimising the **worst-case cost** across all of them.

### Stress Scenarios

| Scenario | Carbon Price | Safety Threshold |
|----------|-------------|-----------------|
| Base | $80/t | 3.0 |
| Safety stress | $80/t | 4.0 |
| Carbon stress | $160/t | 3.0 |
| Joint stress | $160/t | 4.0 |

### Robust Fleet Results

| Metric | Value |
|--------|-------|
| Fleet size | 22 vessels |
| Base-scenario cost | $20,765,143 /month |
| Worst-case cost (Z) | $21,705,607 /month |
| Avg safety score | 4.00 |
| CO2-equivalent | 11,756 tonnes |
| Total fuel | 4,630 tonnes |
| Fuel types | All 8 represented |

### Cost by Scenario

| Scenario | Fleet Cost |
|----------|-----------|
| Base | $20,765,143 |
| Safety stress | $20,765,143 |
| Carbon stress | $21,705,607 |
| Joint stress | $21,705,607 |

---

## Head-to-Head: Base vs Robust

| Metric | Base MILP | Robust Min-Max | Delta |
|--------|-----------|----------------|-------|
| Fleet size | 21 | 22 | +1 vessel |
| Cost (base scenario) | $19.7M | $20.8M | +5.4% |
| Worst-case cost | -- | $21.7M | capped |
| Avg safety | 3.24 | 4.00 | +0.76 |
| CO2-equivalent | 13,095 t | 11,756 t | -10.2% |
| Passes safety >= 4.0? | No | Yes | -- |
| Resilient to $160/t carbon? | No (re-optimisation needed) | Yes (same fleet) | -- |

### What You Get for 5.4% More

The robust fleet costs $1.06M more per month in the base scenario. In return:

1. **Regulatory resilience** -- the fleet remains feasible and cost-bounded even if safety standards tighten to 4.0 or carbon price doubles to $160/t
2. **Higher safety** -- average score of 4.0 vs 3.24, reducing insurance risk premiums and improving operational standards
3. **Lower emissions** -- 10.2% fewer CO2-equivalent tonnes, positioning the fleet ahead of decarbonisation targets
4. **No re-selection needed** -- one fleet works across all tested scenarios; no costly mid-contract vessel swaps

---

## Recommendation

**Submit the robust fleet.** The 5.4% cost premium is a practical insurance policy against the two most likely regulatory changes in maritime shipping: stricter safety requirements and rising carbon pricing. The robust fleet simultaneously delivers better safety and lower emissions as a bonus -- not because we optimised for those directly, but because hedging against worst-case cost naturally selects cleaner, safer vessels.

For operators prioritising pure cost minimisation under current conditions, the base MILP fleet remains the optimal choice at $19.7M.
