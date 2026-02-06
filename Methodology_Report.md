# Maritime Hackathon 2026 — Case Paper

## Smart Fleet Selection: Cost-Optimal Vessel Chartering with Safety and Sustainability Constraints

---

## 1. Problem Statement

We are tasked with selecting a minimum-cost fleet of Chemical/Products Tankers to transport Singapore's monthly bunker fuel demand from Singapore to the Australian West Coast (Port Hedland). The fleet must satisfy three binding constraints: total deadweight tonnage (DWT) must meet or exceed the monthly cargo demand, the fleet's average RightShip Safety Score must be at least 3.0, and at least one vessel of each of the eight main engine fuel types must be represented in the selection.

Monthly cargo demand is derived from the MPA Annual Report 2024 (p. 10): Singapore's 2024 Bunker Sales Volume of 54.92 million tonnes, divided by 12, yields a monthly demand D = 4,576,667 tonnes. Each vessel makes a single one-way voyage during the month, and each vessel can only be selected once. DWT is treated as full cargo capacity with no utilisation factor applied.

The candidate pool consists of 108 vessels for which we have AIS movement data capturing a complete Singapore–Port Hedland voyage (approximately 1,762 nautical miles). The total available DWT across all 108 vessels is 15,299,332 tonnes, meaning roughly 30% of the fleet must be selected to meet demand.

---

## 2. Data Overview

### 2.1 Dataset Structure

The vessel movements dataset contains 13,216 AIS records across 108 unique vessels. Each record provides a GPS timestamp, position (latitude/longitude), speed in knots, port boundary indicators, and static vessel attributes (DWT, engine specifications, fuel types, safety score). All vessels are classified as Chemical/Products Tankers.

### 2.2 Fleet Composition

The fleet spans eight main engine fuel types, with highly uneven representation:

| Fuel Type | Ships | Total DWT | DWT Range |
|---|---|---|---|
| Distillate | 54 | 7,399,678 | 14,226 – 262,781 |
| LNG | 22 | 3,024,480 | 25,035 – 261,089 |
| Methanol | 11 | 1,281,230 | 37,520 – 210,102 |
| Ammonia | 8 | 1,483,752 | 106,507 – 210,909 |
| Ethanol | 5 | 922,748 | 174,802 – 207,939 |
| LPG (Butane) | 3 | 442,239 | 49,861 – 210,909 |
| LPG (Propane) | 3 | 451,804 | 39,781 – 206,118 |
| Hydrogen | 2 | 293,401 | 114,563 – 178,838 |

Critically, all 108 vessels use Distillate fuel for their auxiliary engines and auxiliary boilers, regardless of main engine fuel type. This is a physically realistic assumption — even on LNG or Ammonia-powered ships, generators and boilers typically run on marine diesel.

Safety scores are distributed across the full 1–5 range: 17 ships at score 1, 14 at score 2, 31 at score 3, 29 at score 4, and 17 at score 5.

### 2.3 Data Quality Decisions

We identified and addressed the following data quality issues before computation:

**Timestamp gaps.** The median AIS reporting interval is 1.00 hours, with a 95th percentile of 1.97 hours. However, 33 inter-row gaps exceed 24 hours, with the largest being 51.7 days (vessel 10007920). These gaps represent data loss, not continuous sailing. We capped activity hours per row at a maximum of 6 hours. Without this cap, two vessels would receive absurdly inflated fuel costs from phantom transit time. Justification: a 6-hour threshold is approximately 3× the 95th percentile of normal AIS intervals.

**Load factor exceedances.** 186 out of 13,135 transit/maneuver records (1.4%) produce a load factor exceeding 1.0 when applying the cubic speed-to-power relationship. Since an engine cannot physically sustain load above 100% continuously, we cap LF at 1.0.

**Reverse-direction ships.** Eleven vessels travel Port Hedland → Singapore rather than the expected direction. Route distance is approximately symmetric (~1,762 NM), so fuel consumption calculations remain valid regardless of direction. Excluding these vessels would sacrifice 1.05 million DWT of fleet capacity unnecessarily.

**Last AIS record per vessel.** The final timestamped row for each vessel has no subsequent row to compute activity hours from. We assign A = 0 to these rows.

---

## 3. Methodology

Our methodology proceeds in three phases: (1) per-row AIS calculations producing fuel consumption and emissions at each timestamp, (2) per-vessel cost aggregation combining fuel, carbon, CAPEX, and risk components, and (3) fleet-level optimisation using mixed-integer linear programming.

### Phase 1: Per-Row AIS Calculations

#### 3.1 Operating Mode Classification

Each AIS record is classified into one of four operating modes:

- **Transit:** `in_port_boundary` is null AND `speed_knots` ≥ 1
- **Maneuver:** `in_port_boundary` is not null AND `speed_knots` > 1
- **Anchorage:** `in_anchorage` = "anchorage" AND `speed_knots` < 1
- **Drifting:** all remaining records

Only Transit and Maneuver modes contribute to fuel consumption and emission calculations. In our dataset, approximately 92% of records are Transit, 4.3% Maneuver, 2.9% Anchorage, and 0.8% Drifting.

#### 3.2 Activity Hours

For each row within a vessel's chronologically sorted records:

```
A = min((epoch_next − epoch_current) / 3600, 6.0) hours
```

The 6-hour cap addresses data gaps as described in Section 2.3. The last record per vessel receives A = 0.

#### 3.3 Maximum Speed and Engine Load Factor

Maximum speed is derived from the vessel's reference speed:

```
MS = 1.066 × Vref
```

The main engine load factor follows the cubic admiralty law:

```
LF = min((AS / MS)³, 1.0)
```

where AS is the actual speed (knots) from AIS data. LF is rounded to two decimal places. If LF < 0.02 and the operating mode is Transit or Maneuver, LF is defaulted to 0.02 (the minimum entry in the LLAF table).

#### 3.4 Adjusted Specific Fuel Consumption

The dataset's SFC values are calibrated for Distillate fuel (LCV = 42.7 MJ/kg). To account for the actual fuel burned by each machinery, we apply an energy-density correction:

```
sfc_adjusted_xy = sfc_xy × (42.7 / LCV_fuel_xy)
```

where `xy` denotes the machinery (ME, AE, or AB) and `LCV_fuel_xy` is the Lower Calorific Value of the fuel that machinery burns.

This is where a critical distinction arises. The main engine burns the ship's designated fuel type, which varies across the fleet (Distillate, LNG, Methanol, Ammonia, Hydrogen, Ethanol, LPG Propane, or LPG Butane). The auxiliary engine and auxiliary boiler, however, always burn Distillate in this dataset. Since Distillate has LCV = 42.7, the correction ratio for AE and AB is always 42.7/42.7 = 1.0, meaning their SFC values remain unadjusted.

The impact of the SFC adjustment on the main engine varies dramatically by fuel type:

| Fuel Type | LCV (MJ/kg) | 42.7/LCV | Effect on SFC |
|---|---|---|---|
| Distillate | 42.7 | 1.000 | No change |
| LNG | 48.0 | 0.890 | −11% (less fuel mass needed) |
| LPG (Propane) | 46.3 | 0.922 | −8% |
| LPG (Butane) | 45.7 | 0.934 | −7% |
| Ethanol | 26.8 | 1.593 | +59% (more fuel mass needed) |
| Methanol | 19.9 | 2.146 | +115% |
| Ammonia | 18.6 | 2.296 | +130% |
| Hydrogen | 120.0 | 0.356 | −64% (far less fuel mass needed) |

Hydrogen's adjusted SFC is remarkably low (~60 g/kWh) because its energy density is nearly 3× that of Distillate. Conversely, Methanol and Ammonia ships burn roughly twice the fuel mass per unit of engine output due to their lower energy density.

#### 3.5 Fuel Consumption

For each Transit or Maneuver row, fuel consumption (in tonnes) is computed per machinery:

```
FC_me = LF × MEP × sfc_adjusted_me × A / 1,000,000
FC_ae = AEL × sfc_adjusted_ae × A / 1,000,000
FC_ab = ABL × sfc_adjusted_ab × A / 1,000,000
```

where MEP is main engine power (kW), AEL is auxiliary engine load (kW), ABL is auxiliary boiler load (kW), and A is activity hours. The division by 1,000,000 converts from grams to tonnes. Units check: kW × g/kWh × hours / 10⁶ = tonnes.

The main engine's fuel consumption is speed-dependent via the load factor, while auxiliary engine and boiler consumption depends only on their constant load ratings and operating time.

#### 3.6 Low Load Adjustment Factor (LLAF)

The LLAF corrects for increased incomplete combustion at low engine loads, which produces disproportionately higher emissions per unit of fuel burned. To look up the LLAF table:

1. Convert LF to a percentage: `%LF = LF × 100`
2. Round `%LF` to the nearest integer
3. If `%LF < 2` and mode is Transit or Maneuver, default to 2%
4. If `%LF ≥ 20`, LLAF = 1.0 for all gases (no adjustment)
5. Otherwise, look up CO₂, CH₄, and N₂O multipliers from the LLAF table

We apply LLAF only to main engine emissions. The rationale: LLAF accounts for combustion efficiency degradation in propulsion engines running below their design load, which varies with vessel speed. Auxiliary engines and boilers operate at a constant, factory-rated load regardless of vessel speed, and therefore do not experience the same low-load combustion inefficiencies.

At typical transit speeds, most vessels operate at LF > 20%, meaning LLAF = 1.0. The LLAF multipliers are most impactful during low-speed maneuvering (LF 2–10%), where CO₂ LLAF ranges from 1.59× to 3.28× and CH₄ LLAF ranges from 4.35× to 21.18×. Since maneuvering accounts for only ~5% of total activity hours, the fleet-wide impact of LLAF is modest but non-trivial.

#### 3.7 Emission Calculations

For each Transit/Maneuver row, greenhouse gas emissions are computed per machinery using the appropriate emission factors (Cf) from the Cf table:

```
Emission_gas_xy = LLAF_gas × Cf_gas_fuel_xy × FC_xy
```

where `gas` ∈ {CO₂, CH₄, N₂O}, `xy` ∈ {ME, AE, AB}, and `Cf_gas_fuel_xy` is the emission factor for the fuel type burned by that specific machinery.

**This is a critical modelling choice.** The main engine uses the Cf values for its designated fuel type (e.g., Ammonia has Cf_CO₂ = 0.000), while the auxiliary engine and auxiliary boiler always use Distillate Cf values (Cf_CO₂ = 3.206, Cf_CH₄ = 0.00005, Cf_N₂O = 0.00018), because they burn Distillate.

The practical consequence is that no vessel achieves zero total CO₂ emissions, even those running on zero-carbon main engine fuels. An Ammonia-powered vessel with zero ME CO₂ emissions still produces approximately 121 tonnes of CO₂ per voyage from its Distillate-burning auxiliary systems. A Hydrogen-powered vessel still produces approximately 102 tonnes. Applying the main engine's emission factors to all machineries would incorrectly yield zero total CO₂ for these ships.

The table below summarises this distinction:

|  | Main Engine | Auxiliary Engine / Boiler |
|---|---|---|
| Fuel Type | Ship-specific (8 types) | Always Distillate |
| SFC Adjustment Ratio | 42.7 / LCV_ME | 1.0 (no change) |
| Fuel Price | ME fuel rate | Distillate rate ($555/t) |
| Emission Factors (Cf) | ME fuel Cf | Distillate Cf |
| LLAF | Speed-dependent (via LF) | 1.0 (constant load) |
| Load Model | LF = (AS/MS)³ (variable) | AEL/ABL (fixed kW rating) |

#### 3.8 CO₂ Equivalent

Total equivalent CO₂ emissions per vessel are computed by summing across all Transit/Maneuver rows and all three machineries, then applying IPCC AR5 GWP values:

```
CO₂eq = 1 × Total_CO₂ + 28 × Total_CH₄ + 265 × Total_N₂O
```

N₂O carries a GWP of 265, meaning even trace quantities are significant in CO₂ equivalent terms.

---

### Phase 2: Per-Vessel Cost Aggregation

#### 3.9 Fuel Cost

Fuel cost is computed per machinery at each machinery's own fuel rate. The fuel price per tonne is derived as:

```
Price_per_tonne = Cost_per_GJ × LCV (MJ/kg)
```

Since LCV in MJ/kg is numerically equivalent to GJ/tonne (after unit conversion: MJ/kg × 1000 kg/t ÷ 1000 MJ/GJ), this gives cost directly in USD/tonne.

```
Fuel_cost_ME = FC_me_total × Price_per_tonne(ME fuel type)
Fuel_cost_AE = FC_ae_total × Price_per_tonne(Distillate) = FC_ae_total × $555.10
Fuel_cost_AB = FC_ab_total × Price_per_tonne(Distillate) = FC_ab_total × $555.10
Total_fuel_cost = Fuel_cost_ME + Fuel_cost_AE + Fuel_cost_AB
```

The reference fuel prices span a wide range:

| Fuel Type | Cost/GJ | LCV | Price/tonne |
|---|---|---|---|
| Distillate | $13.00 | 42.7 | $555 |
| LPG (Propane) | $15.00 | 46.3 | $695 |
| LPG (Butane) | $15.00 | 45.7 | $686 |
| LNG | $15.00 | 48.0 | $720 |
| Ammonia | $40.00 | 18.6 | $744 |
| Methanol | $54.00 | 19.9 | $1,075 |
| Ethanol | $54.00 | 26.8 | $1,447 |
| Hydrogen | $50.00 | 120.0 | $6,000 |

Pricing each machinery at its own fuel rate rather than applying a uniform ME fuel rate to all fuel consumption is particularly impactful for Hydrogen ships: ~32 tonnes of AE/AB Distillate fuel priced at $6,000/t instead of $555/t would introduce approximately $173,000 in phantom cost (+38.4% overstatement).

#### 3.10 Carbon Cost

```
Carbon_cost = CO₂eq × $80
```

where $80 USD per tonne CO₂eq is the 2024 carbon price provided in the problem parameters.

#### 3.11 Ship Ownership Cost (Monthly Amortised CAPEX)

Ship purchase cost is determined by DWT bracket and fuel type:

```
Ship_cost = Base_cost(DWT bracket) × Multiplier(ME fuel type) × 1,000,000
```

DWT brackets are: 10–40k ($35M), 40–55k ($53M), 55–80k ($80M), 80–120k ($78M), >120k ($90M). Notably, the 80–120k bracket is $2M cheaper than the 55–80k bracket.

Fuel type multipliers range from 1.0 (Distillate, the base case) to 1.4 (LNG and Ammonia), with Hydrogen at 1.1 — lower than most alternative fuels, reflecting its simpler fuel handling systems.

The monthly amortised cost is derived using standard capital recovery:

```
Salvage (S) = 10% × Ship_cost
CRF = r × (1+r)^N / ((1+r)^N − 1)     where r = 0.08, N = 30
Annual_cost = (Ship_cost − S) × CRF + r × S
Monthly_CAPEX = Annual_cost / 12
```

With r = 0.08 and N = 30, CRF = 0.088827. For a >120k DWT Distillate ship ($90M), monthly CAPEX is $659,585. For the same bracket with LNG (×1.4 = $126M), it rises to $923,419.

CAPEX is the dominant cost component, representing 60–75% of total monthly cost for most vessels. This means the optimiser is largely solving for how to meet DWT demand with the fewest large ships.

#### 3.12 Risk Premium

The RightShip Safety Score drives a risk adjustment applied to the total pre-risk cost:

```
Risk_premium = (Fuel_cost + Carbon_cost + Monthly_CAPEX) × Adjustment_rate
Final_adjusted_cost = (Fuel_cost + Carbon_cost + Monthly_CAPEX) + Risk_premium
```

| Safety Score | Rate | Effective Multiplier |
|---|---|---|
| 1 (highest risk) | +10% | 1.10 |
| 2 | +5% | 1.05 |
| 3 (neutral) | 0% | 1.00 |
| 4 | −2% | 0.98 |
| 5 (lowest risk) | −5% | 0.95 |

A safety score of 1 effectively inflates a ship's cost by 10%, while a score of 5 provides a 5% discount. For a vessel with $1M total monthly cost, this represents a $150,000 swing between score 1 and score 5.

---

### Phase 3: Fleet Optimisation

#### 3.13 Problem Formulation

With all 108 vessels' final adjusted costs pre-computed, the fleet selection problem is formulated as a Mixed Integer Linear Program (MILP):

**Decision variables:** x_i ∈ {0, 1} for each vessel i = 1, ..., 108

**Objective — Minimise total fleet cost:**

```
Minimise  Σᵢ (xᵢ × Final_adjusted_cost_i)
```

**Subject to:**

**(C1) Demand constraint:**
```
Σᵢ (xᵢ × DWT_i) ≥ 4,576,667
```

**(C2) Safety constraint (linearised):**

The raw requirement that average safety score ≥ 3.0 is nonlinear (Σ safety / Σ count). We linearise it by rearranging:

```
Σᵢ (xᵢ × safety_i) ≥ 3.0 × Σᵢ (xᵢ)
→  Σᵢ (xᵢ × (safety_i − 3.0)) ≥ 0
```

Each selected vessel contributes (safety_i − 3.0) to the constraint. A safety-5 ship contributes +2.0; a safety-1 ship contributes −2.0. This is now a standard linear inequality.

**(C3) Fuel type coverage:**
```
For each fuel type f ∈ {8 types}:  Σ(xᵢ : fuel_type_i = f) ≥ 1
```

**(C4) Binary:**
```
xᵢ ∈ {0, 1}  for all i
```

#### 3.14 Solver

We use PuLP (Python LP/MILP library) with the CBC solver. With only 108 binary variables, the problem solves to proven global optimality in under 1 second.

#### 3.15 Structural Observations

Several features of the problem simplify the solution space:

- **Forced selections.** Hydrogen (2 ships), LPG Butane (3), and LPG Propane (3) have very few candidates, so at least one from each is structurally forced. These forced picks commit approximately 400k–600k DWT and constrain the achievable safety average.

- **CAPEX dominance.** Since CAPEX accounts for 60–75% of total cost and is fixed per ship (independent of speed or voyage profile), the optimiser strongly favours fewer, larger ships. The >120k DWT bracket contains 62 of 108 ships and offers the best DWT-per-dollar ratio.

- **Safety-cost tension.** Distillate ships are cheapest (lowest fuel price at $555/t, no CAPEX multiplier) but have the lowest average safety score (2.6). The optimiser must balance low-cost Distillate ships with enough safety-4 and safety-5 ships to maintain the ≥3.0 average.

---

## 4. Sensitivity Analysis

We performed parametric sweeps across two dimensions to characterise the solution's robustness.

### 4.1 Safety Threshold Sensitivity

We re-ran the MILP at safety thresholds of 2.5, 3.0, 3.5, 4.0, and 4.5, constructing a cost-safety Pareto frontier. For each threshold, we record total fleet cost, fleet size, average safety score achieved, total CO₂eq, and fuel mix composition.

This analysis quantifies the **marginal cost of safety**: the incremental cost per unit improvement in the fleet's average safety score. It reveals the "knee point" where additional safety becomes disproportionately expensive — directly useful for port authorities and charterers evaluating risk tolerance.

### 4.2 Carbon Price Sensitivity

We re-ran the MILP at carbon prices of $80 (base), $120, $160, and $200 per tonne CO₂eq. At higher carbon prices:

- Zero-carbon fuels (Ammonia, Hydrogen) become more competitive as their carbon cost remains near-zero while Distillate ships' carbon cost rises
- Fleet composition shifts toward cleaner fuels, demonstrating how carbon pricing mechanisms can drive decarbonisation through economic incentive alone
- The fleet "greens up" naturally — previewing the likely effect of tightening IMO GHG regulations and EU ETS expansion

### 4.3 Data Quality Sensitivity

We tested the impact of the activity-hour gap cap by running the model at thresholds of 3 hours, 6 hours (base), 12 hours, and uncapped. This confirms that gap capping is necessary to avoid two specific vessels (10007920 and 10372190) receiving unrealistic fuel costs from 50+ day data gaps.

### 4.4 2024 Route-Specific Adjustments (Singapore–West Australia)

To reflect real-world operating conditions observed in 2024, we extend the sensitivity analysis to incorporate regulatory and operational risk factors specific to the Singapore–West Australia maritime corridor. These adjustments are modelled as scenario overlays on the base case, enabling evaluation of fleet performance under realistic 2024 conditions.

#### 4.4.1 Port Congestion (Singapore)

**2024 Context:** Singapore experienced episodic port congestion in 2024 due to global fleet bunching effects, increasing anchorage waiting times.

**Model Implementation:** Add 24–72 hours to anchorage periods for vessels at Singapore port. Since auxiliary engines and boilers remain operational during waiting, this extends activity hours (A) for auxiliary systems, increasing FC_ae and FC_ab. The cost impact flows naturally through the fuel cost calculation:

```
A_hours_anchorage_SG = A_hours_base + Δ_congestion_hours
where Δ_congestion_hours ∈ [24, 72]
```

This increases auxiliary fuel consumption by approximately 5–15 tonnes per vessel, translating to $2,800–$8,300 additional fuel cost.

#### 4.4.2 Fuel Price Volatility

**2024 Context:** Regional bunker demand pressure led to price volatility above baseline market rates.

**Model Implementation:** Apply a uniform 1.05× multiplier to all fuel prices:

```
fuel_price_2024 = fuel_price_base × 1.05
```

This captures realistic market conditions without overstating geopolitical risk. For the fleet, this translates to approximately +5% increase in total fuel costs ($1.5M–$2M additional fleet cost).

#### 4.4.3 Singapore Carbon Tax (Embedded)

**2024 Context:** Singapore implemented a carbon tax of S$25/tCO₂e applied upstream to large emitting facilities. This is not a direct levy on shipping operators but is embedded in bunker fuel pricing.

**Model Implementation:** The carbon tax impact is captured within the 1.05× fuel price multiplier (Section 4.4.2). Conventional fossil fuels experience an effective +3–4% embedded cost increase, while zero-carbon fuels (Ammonia, Hydrogen) see minimal impact. No separate calculation is required to avoid double-counting.

#### 4.4.4 IMO Carbon Intensity Indicator (CII) Enforcement

**2024 Context:** 2024 marked the first year where IMO CII ratings imposed operational consequences on vessels with poor carbon performance.

**Model Implementation:** We calculate per-vessel CII and apply performance-based cost adjustments:

```
CII = (CO₂_total × 10⁶) / (DWT × 1,762)     [g CO₂ / tonne·NM]
```

Vessels are assigned IMO rating bands based on CII thresholds (ship-type and size-specific):

| CII Rating | Threshold (approx.) | Cost Multiplier |
|---|---|---|
| A (Superior) | CII ≤ 3.5 | 0.95 (5% discount) |
| B (Good) | 3.5 < CII ≤ 4.5 | 0.98 |
| C (Acceptable) | 4.5 < CII ≤ 5.5 | 1.00 (no change) |
| D (Needs improvement) | 5.5 < CII ≤ 6.5 | 1.05 (5% penalty) |
| E (Poor) | CII > 6.5 | 1.10 (10% penalty) |

The CII penalty is applied to the total monthly cost:

```
final_cost_2024 = total_monthly_cost × (1 + safety_adj_rate) × CII_penalty_multiplier
```

This creates a direct economic linkage between emissions performance and vessel operating cost, mirroring real 2024 compliance pressures.

#### 4.4.5 Safety Regulatory Tightening

**2024 Context:** Singapore's Port State Control regime enforced stricter safety standards for hazardous cargo vessels.

**Model Implementation:** We extend the existing safety threshold sensitivity analysis to test more stringent constraints:

- Base case: Minimum safety score ≥ 3.0
- 2024 stress scenarios: ≥ 3.5, ≥ 4.0, ≥ 4.5, ≥ 5.0

Under tighter safety thresholds, lower-rated vessels are excluded from the feasible fleet, structurally reducing fleet availability and increasing aggregate cost. This is modelled as a binary feasibility constraint, not a continuous penalty — reflecting the reality that vessels failing Port State Control inspections cannot operate on the route.

#### 4.4.6 Integrated 2024 Cost Structure

The complete per-vessel cost under 2024 conditions is:

```
fuel_cost_2024 = (FC_me × price_ME × 1.05) +
                 ((FC_ae + FC_ab + FC_congestion) × 555.10 × 1.05)

carbon_cost = CO₂eq × 80

CII = (CO₂_total × 10⁶) / (DWT × 1,762)

final_cost_2024 = (fuel_cost_2024 + carbon_cost + monthly_CAPEX) ×
                  (1 + safety_adj_rate) ×
                  CII_penalty_multiplier

Subject to:
    safety_score ≥ S_min
    CII_rating ∈ {A, B, C, D, E}
```

#### 4.4.7 Scenario Comparison

| Scenario | Fuel Price | Congestion (days) | Safety Min | CII Enforcement |
|---|---|---|---|---|
| Base (Idealised) | ×1.00 | 0 | ≥3.0 | No |
| 2024 Typical | ×1.05 | 1–2 | ≥3.0 | Yes |
| 2024 Stress | ×1.10 | 3 | ≥4.0 | Yes (strict D/E penalties) |

This framework enables quantitative assessment of how real-world 2024 operational conditions affect fleet selection, cost structure, and emissions performance on the Singapore–West Australia route.

---

## 5. Key Insights

### 5.1 No Vessel Is Truly Zero-Emission

Even vessels powered by zero-carbon main engine fuels (Ammonia, Hydrogen) produce 93–150 tonnes CO₂eq per voyage from their Distillate-burning auxiliary systems. Capturing these residual emissions — by using Distillate emission factors for AE/AB rather than naively applying the main engine's zero-emission factors to all machineries — yields a more realistic carbon profile and avoids understating carbon costs by $7,400–$9,700 per ship.

### 5.2 Safety and Sustainability Are Complementary

Higher-safety fleets naturally skew toward cleaner fuels. Distillate ships average safety 2.6, while LNG ships average 3.8, LPG Propane 4.7, and Ammonia 3.5. Tightening the safety constraint from ≥3.0 to ≥4.0 simultaneously reduces fleet carbon intensity, demonstrating that the safety and decarbonisation agendas reinforce rather than conflict with each other. This finding has direct implications for charterer vetting policies: requiring higher RightShip Safety Scores also promotes environmental performance.

### 5.3 Fleet Carbon Intensity Index

We compute a fleet-level Carbon Intensity Indicator (CII) — the operational carbon intensity metric mandated by the IMO since 2023:

```
Fleet CII = Total CO₂eq / (Total DWT × 1,762 NM)     [g CO₂ / tonne·NM]
```

This connects our hackathon analysis to the real-world regulatory framework (IMO 2023 GHG Strategy, MARPOL Annex VI) and allows comparison of fleet configurations against IMO A–E rating bands.

### 5.4 CAPEX as the Dominant Cost Lever

Fuel and carbon costs combined represent only 25–40% of total vessel cost. CAPEX dominates, meaning fleet size (number of ships) is a more powerful cost driver than individual ship fuel efficiency. The optimiser's strong preference for large vessels (>120k DWT) reflects this — fewer ships mean fewer fixed CAPEX charges.

---

## 6. Limitations

- DWT is treated as full cargo capacity with no utilisation factor, block coefficient, or seasonal draft adjustment
- Each vessel's cost is based on a single observed voyage; speed profiles are not averaged across multiple trips
- Fuel prices and carbon price are fixed parameters; no stochastic modelling of market volatility
- Route distance is assumed symmetric; any current/weather advantages on one direction are not captured
- Auxiliary engine and boiler loads are constant (no cold-ironing or shore power scenarios)
- The MILP treats each ship as available exactly once; no scheduling, queuing, or return-trip optimisation

---

## Appendix A: Reference Tables

### A.1 Emission Factors (Cf Table)

| Fuel Type | LCV (MJ/kg) | Cf_CO₂ | Cf_CH₄ | Cf_N₂O |
|---|---|---|---|---|
| Distillate | 42.7 | 3.206 | 0.00005 | 0.00018 |
| Light Fuel Oil | 41.2 | 3.151 | 0.00005 | 0.00018 |
| Heavy Fuel Oil | 40.2 | 3.114 | 0.00005 | 0.00018 |
| LPG (Propane) | 46.3 | 3.000 | 0.00005 | 0.00018 |
| LPG (Butane) | 45.7 | 3.030 | 0.00005 | 0.00018 |
| LNG | 48.0 | 2.750 | 0.00000 | 0.00011 |
| Methanol | 19.9 | 1.375 | 0.00005 | 0.00018 |
| Ethanol | 26.8 | 1.913 | 0.00005 | 0.00018 |
| Ammonia | 18.6 | 0.000 | 0.00005 | 0.00018 |
| Hydrogen | 120.0 | 0.000 | 0.00000 | 0.00000 |

### A.2 CAPEX Base Costs and Multipliers

**Base costs (Distillate):**

| DWT Bracket | Base Cost ($M) |
|---|---|
| 10,000 – 40,000 | $35 |
| 40,001 – 55,000 | $53 |
| 55,001 – 80,000 | $80 |
| 80,001 – 120,000 | $78 |
| > 120,000 | $90 |

**Fuel type multipliers:** Distillate 1.0, LPG Propane 1.3, LPG Butane 1.35, LNG 1.4, Methanol 1.3, Ethanol 1.2, Ammonia 1.4, Hydrogen 1.1.

### A.3 Safety Score Adjustment Rates

| Score | Meaning | Adjustment |
|---|---|---|
| 1 | Needs improvement | +10% (increased risk cost) |
| 2 | Needs improvement | +5% |
| 3 | Working towards best practice | 0% |
| 4 | Working towards best practice | −2% (reduced risk cost) |
| 5 | Working towards best practice | −5% |

### A.4 Key Constants

| Parameter | Value |
|---|---|
| Monthly demand (D) | 4,576,667 tonnes |
| Carbon price | $80 / tonne CO₂eq |
| Asset depreciation rate (r) | 8% per annum |
| Ship lifespan (N) | 30 years |
| Salvage value | 10% of ship cost |
| Capital Recovery Factor (CRF) | 0.088827 |
| GWP: CO₂ / CH₄ / N₂O | 1 / 28 / 265 |
| Max speed coefficient | 1.066 |
| Activity hour cap | 6 hours |

### A.5 Verification Checkpoint

To validate our pipeline, we provide the complete intermediate values for one vessel:

**Vessel 10657280 — Ammonia, DWT 206,331, Safety 3**

| Stage | Value |
|---|---|
| MEP | 18,630 kW |
| Vref → MS | 14.97 → 15.96 kn |
| Mean LF (transit) | 0.420 |
| SFC ME adjusted | 388.2 g/kWh (= sfc × 42.7/18.6) |
| Transit hours | 132.9 |
| Maneuver hours | 6.0 |
| FC_ME | 409.13 tonnes |
| FC_AE | 30.46 tonnes |
| FC_AB | 7.29 tonnes |
| CO₂ (total, all machineries) | 121.04 tonnes |
| CO₂eq | 143.08 tonnes |
| Fuel cost | $325,351 |
| Carbon cost | $11,446 |
| Monthly CAPEX | $923,419 |
| Risk premium | $0 (safety = 3) |
| **Final adjusted cost** | **$1,260,216** |

Note: CO₂ is 121.04 tonnes, not zero — the AE and AB contribute all CO₂ emissions from Distillate combustion. The main engine's Ammonia combustion produces zero CO₂ but the ship is not emission-free.
