"""
Sensitivity analysis: re-run fleet selection at different safety thresholds
and compare costs, fleet composition, and emissions.
"""

from typing import Any

import pandas as pd

from src.constants import MONTHLY_DEMAND
from src.optimization import select_fleet_milp, total_cost_and_metrics


def run_safety_sweep(
    df: pd.DataFrame,
    thresholds: list[float] | None = None,
    cargo_demand: float = MONTHLY_DEMAND,
) -> list[dict[str, Any]]:
    """
    Re-run MILP at each safety threshold and collect fleet metrics.

    Returns a list of dicts, one per threshold, with keys:
    threshold, feasible, fleet_size, total_cost_usd, avg_safety_score,
    total_co2e_tonnes, total_dwt, total_fuel_tonnes, fuel_type_counts, selected_ids
    """
    if thresholds is None:
        thresholds = [3.0, 3.5, 4.0, 4.5]

    results = []
    for t in thresholds:
        selected_ids = select_fleet_milp(df, cargo_demand=cargo_demand, min_avg_safety=t)

        if not selected_ids:
            results.append({
                "threshold": t,
                "feasible": False,
                "fleet_size": None,
                "total_cost_usd": None,
                "avg_safety_score": None,
                "total_co2e_tonnes": None,
                "total_dwt": None,
                "total_fuel_tonnes": None,
                "fuel_type_counts": {},
                "selected_ids": [],
            })
        else:
            metrics = total_cost_and_metrics(df, selected_ids)
            subset = df[df["vessel_id"].isin(selected_ids)]
            fuel_counts = subset["main_engine_fuel_type"].value_counts().to_dict()

            results.append({
                "threshold": t,
                "feasible": True,
                "fleet_size": metrics["fleet_size"],
                "total_cost_usd": metrics["total_cost_usd"],
                "avg_safety_score": metrics["avg_safety_score"],
                "total_co2e_tonnes": metrics["total_co2e_tonnes"],
                "total_dwt": metrics["total_dwt"],
                "total_fuel_tonnes": metrics["total_fuel_tonnes"],
                "fuel_type_counts": fuel_counts,
                "selected_ids": selected_ids,
            })

    return results


def format_sweep_table(results: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Format sweep results as a readable comparison table.

    Returns a DataFrame with columns: Threshold, Feasible, Fleet Size,
    Total Cost ($), Avg Safety, Total CO2eq (t), Total DWT, Total Fuel (t).
    """
    rows = []
    for r in results:
        if r["feasible"]:
            rows.append({
                "Threshold": r["threshold"],
                "Feasible": "Yes",
                "Fleet Size": r["fleet_size"],
                "Total Cost ($)": f"{r['total_cost_usd']:,.2f}",
                "Avg Safety": f"{r['avg_safety_score']:.2f}",
                "Total CO2eq (t)": f"{r['total_co2e_tonnes']:,.2f}",
                "Total DWT": f"{r['total_dwt']:,.0f}",
                "Total Fuel (t)": f"{r['total_fuel_tonnes']:,.2f}",
            })
        else:
            rows.append({
                "Threshold": r["threshold"],
                "Feasible": "INFEASIBLE",
                "Fleet Size": "-",
                "Total Cost ($)": "-",
                "Avg Safety": "-",
                "Total CO2eq (t)": "-",
                "Total DWT": "-",
                "Total Fuel (t)": "-",
            })

    return pd.DataFrame(rows)
