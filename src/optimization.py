"""
Fleet selection optimization using Mixed Integer Linear Programming (MILP).
Objective: minimize total cost subject to:
- Combined fleet DWT >= cargo demand D
- Average fleet safety score >= 3 (configurable)
- At least one vessel of each main_engine_fuel_type
- Each ship at most once (no repeat trips)

Based on Methodology_Report.md Section 3.13 and Methodology_SOP.md Section 7.
"""

from typing import Any

import pandas as pd
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, PULP_CBC_CMD


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
    cargo_demand_tonnes: float,
    min_avg_safety: float = 3.0,
    require_all_fuel_types: bool = True,
    cost_col: str = "total_cost_usd",
    solver_msg: bool = False,
) -> list[str | int]:
    """
    MILP fleet selection as per Methodology_Report.md Section 3.13.

    Formulation:
        Decision variables: x_i ∈ {0, 1} for each vessel i

        Objective: Minimize Σ(x_i × cost_i)

        Subject to:
            (C1) Σ(x_i × DWT_i) ≥ cargo_demand
            (C2) Σ(x_i × (safety_i - min_safety)) ≥ 0  [linearized average]
            (C3) For each fuel type: Σ(x_i : fuel_type_i = f) ≥ 1
            (C4) x_i ∈ {0, 1}

    Args:
        df: DataFrame with vessel data
        cargo_demand_tonnes: Minimum total DWT required
        min_avg_safety: Minimum average fleet safety score
        require_all_fuel_types: Require at least one vessel per fuel type
        cost_col: Column name for vessel cost
        solver_msg: Show solver output

    Returns:
        List of selected vessel IDs

    Raises:
        ValueError: If problem is infeasible
    """
    # Create MILP problem
    prob = LpProblem("FleetSelection", LpMinimize)

    # Convert to list of dicts for easier access
    vessels = df.to_dict('records')
    vessel_ids = [v['vessel_id'] for v in vessels]

    # Decision variables: x[vessel_id] ∈ {0, 1}
    x = {vid: LpVariable(f"x_{vid}", cat='Binary') for vid in vessel_ids}

    # Objective: Minimize total cost
    prob += lpSum(x[v['vessel_id']] * v[cost_col] for v in vessels), "TotalCost"

    # Constraint 1: DWT demand
    prob += (
        lpSum(x[v['vessel_id']] * v['dwt'] for v in vessels) >= cargo_demand_tonnes,
        "DWT_Demand"
    )

    # Constraint 2: Average safety (linearized)
    # Average safety ≥ min_safety  →  Σ(x_i × safety_i) / Σ(x_i) ≥ min_safety
    # Linearized: Σ(x_i × (safety_i - min_safety)) ≥ 0
    prob += (
        lpSum(x[v['vessel_id']] * (v['safety_score'] - min_avg_safety) for v in vessels) >= 0,
        "Safety_Average"
    )

    # Constraint 3: At least one vessel per fuel type
    if require_all_fuel_types:
        fuel_types = df['main_engine_fuel_type'].unique()
        for fuel_type in fuel_types:
            ft_vessels = [v for v in vessels if v['main_engine_fuel_type'] == fuel_type]
            prob += (
                lpSum(x[v['vessel_id']] for v in ft_vessels) >= 1,
                f"FuelType_{fuel_type.replace(' ', '_')}"
            )

    # Solve
    solver = PULP_CBC_CMD(msg=solver_msg)
    status = prob.solve(solver)

    # Check solution status
    if LpStatus[status] != 'Optimal':
        raise ValueError(f"MILP optimization failed: {LpStatus[status]}")

    # Extract selected vessels
    selected = [vid for vid in vessel_ids if x[vid].value() == 1]

    # Validate solution
    ok, errs = validate_fleet(
        df, selected, cargo_demand_tonnes, min_avg_safety, require_all_fuel_types
    )
    if not ok:
        raise ValueError("MILP solution validation failed: " + "; ".join(errs))

    return selected


# Keep old function name for backward compatibility
select_fleet_greedy = select_fleet_milp


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
