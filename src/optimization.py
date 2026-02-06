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
from pulp import LpBinary, LpMinimize, LpProblem, LpVariable, PULP_CBC_CMD, lpSum

from src.constants import MONTHLY_DEMAND, SAFETY_THRESHOLD


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


def select_fleet_milp(
    df: pd.DataFrame,
    cargo_demand: float = MONTHLY_DEMAND,
    min_avg_safety: float = SAFETY_THRESHOLD,
    require_all_fuel_types: bool = True,
) -> list[int]:
    """
    Select minimum-cost fleet via binary MILP.

    Decision variables: x_i in {0,1} for each vessel i.
    Objective: minimize sum(x_i * final_cost_i).
    Constraints:
        1. sum(x_i * dwt_i) >= cargo_demand
        2. sum(x_i * (safety_i - min_avg_safety)) >= 0  (linearized avg safety)
        3. For each fuel type f: sum(x_i where fuel==f) >= 1  (if require_all_fuel_types)

    Returns sorted list of selected vessel_id integers, or empty list if infeasible.
    """
    indices = list(df.index)
    vessel_ids = df["vessel_id"].tolist()
    costs = df["final_cost"].tolist()
    dwts = df["dwt"].tolist()
    safety_deltas = (df["safety_score"] - min_avg_safety).tolist()

    prob = LpProblem("fleet_selection", LpMinimize)
    x = LpVariable.dicts("x", indices, 0, 1, LpBinary)

    # Objective: minimize total cost
    prob += lpSum([costs[i] * x[i] for i in indices])

    # Constraint 1: DWT >= cargo demand
    prob += lpSum([dwts[i] * x[i] for i in indices]) >= cargo_demand, "DWT"

    # Constraint 2: linearized average safety >= threshold
    prob += lpSum([safety_deltas[i] * x[i] for i in indices]) >= 0, "Safety"

    # Constraint 3: fuel diversity — at least one vessel per fuel type
    if require_all_fuel_types:
        fuel_types = df["main_engine_fuel_type"].unique()
        for ft in fuel_types:
            ft_indices = df.index[df["main_engine_fuel_type"] == ft].tolist()
            prob += lpSum([x[i] for i in ft_indices]) >= 1, f"Fuel_{ft}"

    prob.solve(PULP_CBC_CMD(msg=0))

    # Status 1 = Optimal
    if prob.status != 1:
        return []

    selected = sorted(
        [int(vessel_ids[i]) for i in indices if x[i].varValue > 0.5]
    )
    return selected


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
