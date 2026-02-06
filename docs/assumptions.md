# Assumptions

## Data & Problem Scope

1. **Single monthly cycle** -- each vessel makes exactly one Singapore-to-Port Hedland voyage per month; no return leg modelled.
2. **Monthly demand derived from annual figure** -- 54.92M tonnes/year (MPA Annual Report 2024) divided by 12 = 4,576,667 tonnes/month.
3. **Fixed vessel universe** -- 108 Chemical/Products Tankers from the provided dataset are the only candidates; no chartering external tonnage.
4. **Fixed route** -- Singapore to Port Hedland, Australia (~2,100 nm); no alternative ports or waypoints considered.
5. **AIS data extrapolation** -- the dataset covers ~2 weeks of actual vessel movements; fuel consumption and emissions are aggregated from these observations to represent a full monthly cost profile.

## Cost Model & Financial

6. **Fleet is owned, not chartered** -- CAPEX is amortised as an ownership cost using a Capital Recovery Factor, not a time-charter rate.
7. **New-build acquisition pricing** -- base CAPEX is derived from DWT-bracket lookup tables (5 brackets, $35M--$90M) with fuel-type multipliers (1.0x--1.4x).
8. **30-year useful life, 8% discount rate** -- standard maritime finance parameters used for CRF calculation (CRF = 0.088827).
9. **Salvage value = 10% of ship cost** -- residual value at end of economic life.
10. **Static fuel prices** -- spot prices per fuel type in USD/GJ are fixed for the analysis period; no volatility, seasonality, or regional price variation.
11. **Carbon price = $80/tCO2eq** -- single base-case value; sensitivity analysis explores $80--$200/t.

## Robust Optimisation (Min-Max)

12a. **Discrete scenario set** -- the robust model considers exactly 4 scenarios (base, safety stress, carbon stress, joint stress) rather than continuous probability distributions; no CVaR or stochastic programming.
12b. **Only carbon cost varies across scenarios** -- fuel cost, CAPEX, and risk premium are held constant; only the carbon price component is recalculated per scenario ($80 or $160/tCO2eq).
12c. **Strictest safety threshold governs all scenarios** -- the robust fleet must satisfy the highest safety threshold across all scenarios (4.0), not each scenario's individual threshold.
12d. **Deterministic worst-case, not probabilistic** -- no scenario probabilities are assigned; the solver purely minimises the maximum cost across all scenarios.

## Safety & Operations

13. **Safety score is exogenous** -- integer 1--5 per vessel, taken directly from the dataset with no time-variation or route-dependence.
14. **Risk premium maps linearly from safety score** -- Score 1 = +10% surcharge, Score 5 = -5% discount, applied to total monthly cost before optimisation.
15. **DWT equals available cargo capacity** -- the full deadweight tonnage of each vessel is assumed available for bunker fuel cargo (no deductions for stores, ballast, or crew).
16. **No partial loading** -- each selected vessel is assumed to carry its full DWT; fractional trips are not modelled.

## Fuel Consumption & Emissions

17. **SFC baseline calibrated to Distillate** -- manufacturer SFC values (g/kWh) are for Distillate fuel (LCV 42.7 MJ/kg); alternative fuels are adjusted via the LCV ratio (e.g., Ammonia SFC *= 42.7/18.6).
18. **Auxiliary engines and boilers always burn Distillate** -- regardless of main engine fuel type, AE and AB fuel consumption uses Distillate emission factors and prices.
19. **Constant auxiliary/boiler load** -- AE and boiler power output is fixed per vessel; only main engine load varies with speed.
20. **Cubic speed-power relationship** -- engine load factor = (speed / max_speed)^3, capped at 1.0 with a floor of 0.02 (2%).
21. **Activity hours capped at 6h** -- AIS time gaps exceeding 6 hours are truncated to prevent data-gap artefacts from inflating fuel consumption.
22. **Only Transit and Manoeuvre modes consume fuel** -- Anchorage and Drifting modes are treated as zero-fuel overhead.
23. **GWP values from IPCC AR6** -- CH4 = 28, N2O = 265 (100-year horizon); not the older AR4 values.
24. **Low-Load Adjustment Factors (LLAF) applied to main engine only** -- at engine loads below 20%, emissions are scaled up by LLAF multipliers to account for incomplete combustion; AE/AB are unaffected.
25. **No weather or current effects** -- fuel consumption is purely a function of speed and engine specs; no sea-state, wind, or current adjustments.
