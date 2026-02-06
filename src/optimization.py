"""
Fleet selection optimization.
Objective: minimize total cost subject to:
- Combined fleet DWT >= cargo demand D
- Average fleet safety score >= 3 (configurable)
- At least one vessel of each main_engine_fuel_type
- Each ship at most once (no repeat trips)
"""

from typing import Any

import pandas as pd


def validate_fleet(
    df: pd.DataFrame,
    selected_ids: list[str | int],
    cargo_demand_tonnes: float,
    min_avg_safety: float,
    require_all_fuel_types: bool,
) -> tuple[bool, list[str]]:
    """Check constraints. Returns (ok, list of error messages)."""
    subset = df[df["vessel_id"].isin(selected_ids)]
    errors = []

    if subset["dwt"].sum() < cargo_demand_tonnes:
        errors.append(
            f"Combined DWT {subset['dwt'].sum()} < demand {cargo_demand_tonnes}"
        )
    if subset["safety_score"].mean() < min_avg_safety:
        errors.append(
            f"Average safety score {subset['safety_score'].mean():.2f} < {min_avg_safety}"
        )
    if require_all_fuel_types:
        all_types = set(df["main_engine_fuel_type"].dropna().unique())
        selected_types = set(subset["main_engine_fuel_type"].dropna().unique())
        missing = all_types - selected_types
        if missing:
            errors.append(f"Missing main_engine_fuel_type: {missing}")

    return (len(errors) == 0, errors)


def total_cost_and_metrics(
    df: pd.DataFrame,
    selected_ids: list[str | int],
    cost_col: str = "total_cost_usd",
    fuel_col: str = "fuel_tonnes",
    co2e_col: str = "co2e_tonnes",
) -> dict[str, Any]:
    """Aggregate total DWT, cost, fuel, CO2e, avg safety, unique fuel types, fleet size."""
    subset = df[df["vessel_id"].isin(selected_ids)]
    return {
        "total_dwt": subset["dwt"].sum(),
        "total_cost_usd": subset[cost_col].sum(),
        "avg_safety_score": subset["safety_score"].mean(),
        "num_unique_main_engine_fuel_types": subset["main_engine_fuel_type"].nunique(),
        "fleet_size": len(selected_ids),
        "total_fuel_tonnes": subset[fuel_col].sum(),
        "total_co2e_tonnes": subset[co2e_col].sum(),
    }


def select_fleet_greedy(*args, **kwargs):
    raise NotImplementedError("Replaced by MILP in Phase 2")


def format_outputs(metrics: dict[str, Any], sensitivity_done: bool = False) -> dict[str, Any]:
    """Format for report / console."""
    return {
        "Total DWT of selected fleet": metrics["total_dwt"],
        "Total cost of selected fleet (USD)": metrics["total_cost_usd"],
        "Average fleet safety score": round(metrics["avg_safety_score"], 2),
        "Number of unique main_engine_fuel_type vessels": metrics["num_unique_main_engine_fuel_types"],
        "Sensitivity analysis performed": "Yes" if sensitivity_done else "No",
        "Size of fleet (Number of ships)": metrics["fleet_size"],
        "Total emission of CO2 equivalent (tonnes)": round(metrics["total_co2e_tonnes"], 2),
        "Total fuel consumption (tonnes)": round(metrics["total_fuel_tonnes"], 2),
    }


def submission_outputs(
    metrics: dict[str, Any],
    sensitivity_done: bool = False,
    team_name: str = "",
    category: str = "",
    report_file_name: str = "",
) -> dict[str, Any]:
    """Official submission column values (given_data submission_template.csv). Do not alter column order."""
    return {
        "team_name": team_name,
        "category": category,
        "report_file_name": report_file_name,
        "sum_of_fleet_deadweight": metrics["total_dwt"],
        "total_cost_of_fleet": metrics["total_cost_usd"],
        "average_fleet_safety_score": round(metrics["avg_safety_score"], 2),
        "no_of_unique_main_engine_fuel_types_in_fleet": int(metrics["num_unique_main_engine_fuel_types"]),
        "sensitivity_analysis_performance": "Yes" if sensitivity_done else "No",
        "size_of_fleet_count": int(metrics["fleet_size"]),
        "total_emission_CO2_eq": round(metrics["total_co2e_tonnes"], 2),
        "total_fuel_consumption": round(metrics["total_fuel_tonnes"], 2),
    }
