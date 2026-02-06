# Tornado analysis (clarification)

## What it is

**Tornado analysis** shows how key outputs (total cost, emissions) change across your sensitivity cases. Each case is one run of the same MILP with a different assumption:

- **Safety cases**: minimum average safety threshold (e.g. ≥2.5, ≥3.0, …, ≥4.5).
- **Carbon cases**: carbon price in $/tCO₂eq (e.g. $80, $120, $160, $200).

## What the chart shows

- **One horizontal bar per case.** Bar length = value of the metric (Cost in M$ or Emissions in kt CO₂eq).
- **Sorted by that metric** so the case with the **largest** value is at the **top**. That gives the “tornado” shape and makes it obvious which assumptions drive the most change.
- **Two panels**: left = Total Cost (M$), right = Total Emissions (kt CO₂eq). Same cases in both; sort order can differ because cost and emissions don’t rank cases the same way.

## When it’s produced

- Automatically when you run `python run_sensitivity_analysis.py` (same run that writes the sensitivity CSVs).
- Or by running `python -m src.visualize_sensitivity` (or with a results directory argument), which regenerates all plots from existing CSVs in `outputs/sensitivity/`.

## Data source

Same as the other sensitivity plots: `safety_sensitivity.csv` and `carbon_price_sensitivity.csv` in `outputs/sensitivity/`. If `2024_scenarios.csv` has rows, those scenarios are included in the tornado as well.
