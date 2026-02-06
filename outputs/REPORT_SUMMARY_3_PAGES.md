# Maritime Hackathon 2026 — 3-Page Report Summary

Use this summary to fill in your case paper (≤3 pages excl. cover). Copy and adapt sections as needed.

---

## PAGE 1 — Introduction & Problem Statement

### What the project is about

**Smart Fleet Selection** is an optimisation project for the Maritime Hackathon 2026. The goal is to select a **minimum-cost fleet** of Chemical/Products Tankers to transport **bunker fuel** from **Singapore** to **Australia West Coast (Port Hedland)** in one month, while meeting safety and sustainability constraints.

### Route and demand

- **Route:** Singapore → Port Hedland (~1,762 nautical miles).
- **Monthly cargo demand:** 4,576,667 tonnes (from MPA Annual Report 2024: 54.92 M tonnes/year ÷ 12).
- **Candidate pool:** 108 vessels with AIS movement data for this route; each vessel is used at most once (single one-way voyage per month).

### Constraints

1. **Demand:** Combined fleet deadweight tonnage (DWT) ≥ 4,576,667 tonnes.
2. **Safety:** Fleet average RightShip Safety Score ≥ 3.0 (scale 1 = highest risk, 5 = least risk).
3. **Fuel diversity:** At least one vessel of each of the **8 main engine fuel types** (Distillate, LNG, Methanol, Ethanol, Ammonia, Hydrogen, LPG Propane, LPG Butane).
4. **Single use:** Each ship selected at most once.

### Cost components (per vessel)

Total cost per vessel includes: **fuel cost** (main engine, auxiliary engine, boiler); **carbon cost** (CO₂eq × $80/t); **amortised monthly CAPEX** (30-year life, 8% discount, 10% salvage); and **risk premium** by safety score (+10% for score 1 to −5% for score 5).

### Data

- **Vessels:** 108 ships from `vessel_movements_dataset.csv` (AIS-derived); attributes include DWT, engine power, fuel types, specific fuel consumption, RightShip safety score.
- **Global parameters:** Emission factors, fuel prices, carbon price, CAPEX by DWT bracket and fuel type, from methodology and `calculation_factors.xlsx`.
- **Key modelling choice:** Auxiliary engine and boiler always use **Distillate**; only the main engine uses the ship’s designated fuel type. So even Ammonia/Hydrogen vessels have non-zero CO₂ from auxiliaries.

---

## PAGE 2 — Methodology & Main Results

### Methodology in three phases

1. **Per-row AIS calculations:** Classify operating mode (Transit, Maneuver, Anchorage, Drifting); compute activity hours (capped at 6 h to handle AIS gaps); main engine load factor via cubic speed–power law; adjusted SFC by fuel LCV; fuel consumption and emissions (with LLAF for low-load main engine); CO₂eq using IPCC GWP.
2. **Per-vessel cost:** Sum fuel cost (each machinery at its own fuel price), carbon cost, monthly CAPEX (ship cost by DWT bracket × fuel-type multiplier × CRF), and safety risk premium.
3. **Fleet optimisation:** Mixed-Integer Linear Program (MILP) — binary selection variables; minimise total fleet cost; constraints: DWT ≥ demand, linearised average safety ≥ 3.0, and at least one vessel per fuel type. Solved with PuLP (CBC).

### Baseline fleet (cost-minimising MILP)

- **Carbon price:** $80/tCO₂eq; **safety threshold:** ≥ 3.0.
- **Results:** **21 vessels**; total cost **$19,706,494**; total DWT 4,577,756 t (meets demand); average safety **3.24**; **8** fuel types; total CO₂eq **13,095 t**; total fuel **4,600 t**.
- This is the **provably optimal** lowest-cost feasible fleet for the base case.

### Robust fleet (min–max over stress scenarios)

- **Idea:** One fleet that remains feasible and cost-bounded under four scenarios (base; safety stress 4.0; carbon $160/t; joint: $160/t + safety 4.0). Minimise the **worst-case** cost Z over these scenarios.
- **Results:** **22 vessels**; worst-case cost **Z = $21,705,607**; base-scenario cost $20,765,143; average safety **4.0**; total CO₂eq **11,756 t** (lower than baseline); all 8 fuel types.
- Use this fleet when you want **one submission fleet** resilient to stricter safety and/or higher carbon prices.

### Key outputs for submission

- Total DWT, total cost (USD), average safety score, number of unique fuel types, fleet size, total CO₂eq, total fuel consumption.
- CSV: baseline → `chosen_fleet.csv` / `chosen_fleet_ids.csv`; robust → `robust_fleet.csv` / `robust_fleet_ids.csv`.
- Run: `python run.py` (baseline); `python run.py --robust --submit` for robust submission.

---

## PAGE 3 — Sensitivity, Insights & Conclusion

### Sensitivity analysis

- **Safety threshold:** Re-run MILP at 2.5, 3.0, 3.5, 4.0, 4.5. Cost rises as threshold increases (e.g. ~5.4% from 3.0 to 4.0); fleet composition shifts toward higher-safety (and often cleaner) vessels.
- **Carbon price:** Sweep $80, $120, $160, $200/tCO₂eq. Higher carbon price increases total cost and shifts the optimal fleet toward lower-emission fuels (Ammonia, Hydrogen).
- **Fixed-fleet sensitivity:** For a *given* chosen fleet, varying safety threshold shows when the fleet still meets the constraint; varying carbon price shows how cost changes with price (CO₂eq unchanged).
- **Pareto frontier (cost vs CO₂eq):** Epsilon-constraint method: tighten CO₂eq cap and re-solve MILP. Shows trade-off between cost and emissions; shadow carbon prices between points give a Marginal Abatement Cost Curve (MACC).
- **2024 scenarios (optional):** Port congestion, fuel price volatility, CII enforcement, stricter safety — see `Methodology_Report.md` Section 4.4.

### Main insights

1. **No vessel is zero-emission:** Even Ammonia/Hydrogen main-engine vessels emit ~93–150 t CO₂eq per voyage from Distillate-burning auxiliaries; modelling AE/AB with Distillate emission factors is essential.
2. **Safety and sustainability align:** Higher safety thresholds tend to favour cleaner fuels; tightening safety (e.g. to 4.0) often improves fleet carbon intensity.
3. **CAPEX dominates cost:** Ownership (60–75% of cost) drives the optimiser toward fewer, larger ships; fleet size and DWT mix matter more than small fuel-efficiency gains.
4. **Fuel diversity has a cost:** Requiring all 8 fuel types adds roughly $1.1M vs. dropping the constraint; it buys operational resilience.

### Policy implications

- **Safety:** Moderate increase (e.g. 3.0 → 4.0) is achievable at a quantified cost increase (~5.4% in the base-case run).
- **Carbon pricing:** Above ~$120/tCO₂eq, alternative fuels become more competitive; carbon price is an effective lever for decarbonisation.
- **MACC:** Identifies which abatement steps are cost-effective at $80/tCO₂eq and which need higher carbon prices.

### Limitations (short)

- DWT = full capacity (no utilisation factor); single voyage per vessel; fixed fuel/carbon prices; no scheduling or return trips; auxiliary loads constant (no cold-ironing).

### Conclusion for the report

The project delivers a **MILP-based fleet selection** for Singapore–Port Hedland bunker transport: a **baseline** minimum-cost fleet (21 vessels, $19.7M) and a **robust** min–max fleet (22 vessels, worst-case $21.7M) that performs well under higher carbon price and safety requirements. Sensitivity analysis (safety, carbon price, Pareto/MACC) supports the choice and shows that **safety and decarbonisation can be pursued together** at quantifiable cost. Use the **robust** fleet for a single submission fleet that is resilient to regulatory and carbon-price uncertainty.

---

## Quick reference — key numbers

| Metric              | Baseline fleet | Robust fleet   |
|---------------------|----------------|----------------|
| Vessels             | 21             | 22             |
| Total cost          | $19,706,494    | Worst-case $21,705,607 |
| Average safety      | 3.24           | 4.0            |
| Total CO₂eq (t)     | 13,095         | 11,756         |
| Fuel types          | 8              | 8              |
| Total DWT           | 4,577,756      | 4,580,084      |

**Demand:** 4,576,667 t/month. **Carbon price (base):** $80/tCO₂eq. **Safety threshold (base):** ≥ 3.0.
