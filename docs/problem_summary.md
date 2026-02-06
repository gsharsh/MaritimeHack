# Maritime Hackathon 2026 — Smart Fleet Selection (summary)

## Objective
Select the **optimal fleet** of ships to transport **bunker fuel** from **Singapore (A)** to **Australia West coast (B)** in one month, minimizing owning + operational cost while meeting safety and sustainability constraints.

## Cargo demand
- **D** = monthly bunker tonnes from MPA Annual Report 2024 (Page 10: Bunker Sales Volume, all fuel types), distributed over 12 months.  
  Example: 49.83 M tonnes/year → 4.15 M tonnes/month.

## Constraints
1. **Demand:** Combined fleet DWT ≥ D tonnes for the month.
2. **Single use:** Each ship selected only once (no return/round trips).
3. **Safety:** Average fleet safety score ≥ 3.0 (1 = highest risk, 5 = least risk).
4. **Fuel diversity:** At least one vessel of each **main_engine_fuel_type**.

## Cost model (per ship, one A→B voyage)
1. Fuel cost (main + auxiliary engine + boiler).
2. Carbon cost (emissions × carbon price, 80 USD/tCO2e).
3. Amortized ownership cost per month (CAPEX, 30-year life, CRF).
4. Risk premium (safety score adjustment).

## Data provided
- **Ships:** vessel ID, name, type; AIS; DWT; Vref; P, ael, abl; main/aux engine/boiler fuel types; sfc_me, sfc_ae, sfc_ab; safety score (1–5).
- **Global:** Emission factors (CO2, CH4, N2O); LCV; fuel price USD/GJ; carbon price; CAPEX base + multiplier by fuel type; depreciation; CRF; safety score adjustment rates.

## Required outputs
1. Total DWT of selected fleet  
2. Total cost (USD)  
3. Average fleet safety score  
4. Number of unique main_engine_fuel_type vessels  
5. Sensitivity analysis — Yes/No (details in report)  
6. Size of fleet (number of ships)  
7. Total CO2 equivalent (tonnes)  
8. Total fuel consumption (tonnes)  

## Stretch: Sensitivity analysis
Re-run fleet selection with a higher average safety constraint (e.g. ≥ 4) and compare cost and fleet composition; discuss in the case paper.

## Submission (by 7 Feb 2026 09:00 SGT)
- **Case paper:** `MaritimeHackathon2026_CasePaper_teamname` (Word/PDF, ≤3 pages excl. cover).
- **Results:** CSV template, renamed `teamname_submission.csv` (do not alter column order).
- **Presentation:** `teamname_presentation.ppt` (4–6 slides, ≤10 min).
