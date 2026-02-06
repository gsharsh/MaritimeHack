"""
Sensitivity analysis: re-run fleet selection at different safety thresholds
and compare costs, fleet composition, and emissions.
"""

from typing import Any

import numpy as np
import pandas as pd
from pulp import LpBinary, LpMinimize, LpProblem, LpVariable, PULP_CBC_CMD, lpSum

from src.constants import CARBON_PRICE, MONTHLY_DEMAND, SAFETY_THRESHOLD
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


def _solve_min_co2(
    df: pd.DataFrame,
    cargo_demand: float,
    min_avg_safety: float,
    require_all_fuel_types: bool,
) -> float | None:
    """
    Solve a one-off MILP that minimizes total CO2eq subject to the same
    feasibility constraints (DWT, safety, fuel diversity).

    Returns the minimum achievable CO2eq, or None if infeasible.
    """
    indices = list(df.index)
    dwts = df["dwt"].tolist()
    safety_deltas = (df["safety_score"] - min_avg_safety).tolist()
    co2eqs = df["CO2eq"].tolist()

    prob = LpProblem("min_co2", LpMinimize)
    x = LpVariable.dicts("x", indices, 0, 1, LpBinary)

    # Objective: minimize total CO2eq
    prob += lpSum([co2eqs[i] * x[i] for i in indices])

    # Constraint 1: DWT >= cargo demand
    prob += lpSum([dwts[i] * x[i] for i in indices]) >= cargo_demand, "DWT"

    # Constraint 2: linearized average safety >= threshold
    prob += lpSum([safety_deltas[i] * x[i] for i in indices]) >= 0, "Safety"

    # Constraint 3: fuel diversity
    if require_all_fuel_types:
        fuel_types = df["main_engine_fuel_type"].unique()
        for ft in fuel_types:
            ft_indices = df.index[df["main_engine_fuel_type"] == ft].tolist()
            prob += lpSum([x[i] for i in ft_indices]) >= 1, f"Fuel_{ft}"

    prob.solve(PULP_CBC_CMD(msg=0))

    if prob.status != 1:
        return None

    selected_co2 = sum(co2eqs[i] for i in indices if x[i].varValue > 0.5)
    return selected_co2


def run_pareto_sweep(
    df: pd.DataFrame,
    n_points: int = 15,
    cargo_demand: float = MONTHLY_DEMAND,
    min_avg_safety: float = SAFETY_THRESHOLD,
    require_all_fuel_types: bool = True,
) -> list[dict[str, Any]]:
    """
    Epsilon-constraint Pareto frontier: sweep CO2eq cap from fleet-max to
    fleet-min in ``n_points`` steps, solve MILP at each point, and compute
    shadow carbon prices.

    Algorithm:
    1. Run base MILP (no cap) to get cost-minimizing fleet -> co2_max.
    2. Solve min-CO2eq MILP (same constraints) -> co2_min.
    3. Create ``n_points`` evenly-spaced epsilon values from co2_max to co2_min.
    4. For each epsilon, solve MILP with co2_cap=epsilon.
    5. Compute shadow carbon price between consecutive feasible points.

    Returns list of dicts with keys: epsilon, feasible, fleet_size,
    total_cost_usd, total_co2e_tonnes, avg_safety_score, total_dwt,
    selected_ids, shadow_carbon_price.
    """
    # Step 1: base MILP (cost-minimizing, no CO2 cap) -> co2_max
    base_ids = select_fleet_milp(
        df,
        cargo_demand=cargo_demand,
        min_avg_safety=min_avg_safety,
        require_all_fuel_types=require_all_fuel_types,
    )
    if not base_ids:
        # Base problem is infeasible — no Pareto frontier possible
        return []

    base_metrics = total_cost_and_metrics(df, base_ids)
    co2_max = base_metrics["total_co2e_tonnes"]

    # Step 2: min-CO2eq MILP -> co2_min
    co2_min = _solve_min_co2(
        df, cargo_demand, min_avg_safety, require_all_fuel_types
    )
    if co2_min is None:
        # Should not happen if base is feasible, but handle gracefully
        return []

    # Step 3: build epsilon grid from co2_max down to co2_min
    epsilons = np.linspace(co2_max, co2_min, n_points).tolist()

    # Step 4: solve at each epsilon
    results: list[dict[str, Any]] = []
    for eps in epsilons:
        selected_ids = select_fleet_milp(
            df,
            cargo_demand=cargo_demand,
            min_avg_safety=min_avg_safety,
            require_all_fuel_types=require_all_fuel_types,
            co2_cap=eps,
        )

        if not selected_ids:
            results.append({
                "epsilon": eps,
                "feasible": False,
                "fleet_size": None,
                "total_cost_usd": None,
                "total_co2e_tonnes": None,
                "avg_safety_score": None,
                "total_dwt": None,
                "selected_ids": [],
                "shadow_carbon_price": None,
            })
        else:
            metrics = total_cost_and_metrics(df, selected_ids)
            results.append({
                "epsilon": eps,
                "feasible": True,
                "fleet_size": metrics["fleet_size"],
                "total_cost_usd": metrics["total_cost_usd"],
                "total_co2e_tonnes": metrics["total_co2e_tonnes"],
                "avg_safety_score": metrics["avg_safety_score"],
                "total_dwt": metrics["total_dwt"],
                "selected_ids": selected_ids,
                "shadow_carbon_price": None,  # computed below
            })

    # Step 5: compute shadow carbon prices between consecutive feasible points
    prev_feasible = None
    for r in results:
        if not r["feasible"]:
            continue
        if prev_feasible is not None:
            co2_reduction = prev_feasible["total_co2e_tonnes"] - r["total_co2e_tonnes"]
            cost_increase = r["total_cost_usd"] - prev_feasible["total_cost_usd"]
            if co2_reduction > 0:
                r["shadow_carbon_price"] = cost_increase / co2_reduction
            else:
                # No actual CO2 reduction (same fleet selected) -> no shadow price
                r["shadow_carbon_price"] = None
        prev_feasible = r

    return results


def format_pareto_table(results: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Format Pareto sweep results as a readable comparison table.

    Returns a DataFrame with columns: CO2eq Cap, Feasible, Fleet Size,
    Total Cost ($), Actual CO2eq (t), Shadow Price ($/tCO2eq), Avg Safety.
    Numbers formatted with commas and 2 decimal places.
    """
    rows = []
    for r in results:
        if r["feasible"]:
            shadow = (
                f"{r['shadow_carbon_price']:,.2f}"
                if r["shadow_carbon_price"] is not None
                else "-"
            )
            rows.append({
                "CO2eq Cap": f"{r['epsilon']:,.2f}",
                "Feasible": "Yes",
                "Fleet Size": r["fleet_size"],
                "Total Cost ($)": f"{r['total_cost_usd']:,.2f}",
                "Actual CO2eq (t)": f"{r['total_co2e_tonnes']:,.2f}",
                "Shadow Price ($/tCO2eq)": shadow,
                "Avg Safety": f"{r['avg_safety_score']:.2f}",
            })
        else:
            rows.append({
                "CO2eq Cap": f"{r['epsilon']:,.2f}",
                "Feasible": "INFEASIBLE",
                "Fleet Size": "-",
                "Total Cost ($)": "-",
                "Actual CO2eq (t)": "-",
                "Shadow Price ($/tCO2eq)": "-",
                "Avg Safety": "-",
            })

    return pd.DataFrame(rows)


def compute_shadow_prices(
    df: pd.DataFrame,
    cargo_demand: float = MONTHLY_DEMAND,
    safety_threshold: float = SAFETY_THRESHOLD,
) -> dict[str, Any]:
    """
    Compute shadow prices via constraint perturbation.

    Shadow price = (perturbed_cost - base_cost) / perturbation_size.
    Two constraints perturbed:
    1. DWT demand: +1% (cargo_demand * 1.01)
    2. Safety threshold: +0.1 (e.g. 3.0 -> 3.1)

    Returns dict with base_cost, perturbed costs, fleet sizes, and shadow prices.
    """
    # --- Base case ---
    base_ids = select_fleet_milp(df, cargo_demand=cargo_demand, min_avg_safety=safety_threshold)
    if not base_ids:
        return {
            "base_cost": None,
            "base_fleet_size": None,
            "dwt_shadow_price": None,
            "safety_shadow_price": None,
            "perturbed_cost_dwt": None,
            "perturbed_cost_safety": None,
            "perturbed_fleet_size_dwt": None,
            "perturbed_fleet_size_safety": None,
            "dwt_perturbation": None,
            "safety_perturbation": None,
            "note": "base case infeasible",
        }

    base_metrics = total_cost_and_metrics(df, base_ids)
    base_cost = base_metrics["total_cost_usd"]
    base_fleet_size = base_metrics["fleet_size"]

    result: dict[str, Any] = {
        "base_cost": base_cost,
        "base_fleet_size": base_fleet_size,
        "cargo_demand": cargo_demand,
        "safety_threshold": safety_threshold,
    }

    # --- DWT demand perturbation (+1%) ---
    dwt_delta = cargo_demand * 0.01
    perturbed_demand = cargo_demand + dwt_delta
    dwt_ids = select_fleet_milp(df, cargo_demand=perturbed_demand, min_avg_safety=safety_threshold)

    if dwt_ids:
        dwt_metrics = total_cost_and_metrics(df, dwt_ids)
        result["perturbed_cost_dwt"] = dwt_metrics["total_cost_usd"]
        result["perturbed_fleet_size_dwt"] = dwt_metrics["fleet_size"]
        result["dwt_perturbation"] = dwt_delta
        result["dwt_shadow_price"] = (dwt_metrics["total_cost_usd"] - base_cost) / dwt_delta
    else:
        result["perturbed_cost_dwt"] = None
        result["perturbed_fleet_size_dwt"] = None
        result["dwt_perturbation"] = dwt_delta
        result["dwt_shadow_price"] = None
        result["dwt_note"] = "infeasible at +1% DWT perturbation"

    # --- Safety threshold perturbation (+0.1) ---
    safety_delta = 0.1
    perturbed_safety = safety_threshold + safety_delta
    safety_ids = select_fleet_milp(df, cargo_demand=cargo_demand, min_avg_safety=perturbed_safety)

    if safety_ids:
        safety_metrics = total_cost_and_metrics(df, safety_ids)
        result["perturbed_cost_safety"] = safety_metrics["total_cost_usd"]
        result["perturbed_fleet_size_safety"] = safety_metrics["fleet_size"]
        result["safety_perturbation"] = safety_delta
        result["safety_shadow_price"] = (safety_metrics["total_cost_usd"] - base_cost) / safety_delta
    else:
        result["perturbed_cost_safety"] = None
        result["perturbed_fleet_size_safety"] = None
        result["safety_perturbation"] = safety_delta
        result["safety_shadow_price"] = None
        result["safety_note"] = "infeasible at +0.1 safety perturbation"

    return result


def format_shadow_prices(shadow_results: dict[str, Any]) -> str:
    """
    Format shadow price results as a readable text table.

    Returns a multi-line string showing constraint, base/perturbed values,
    costs, shadow price, and interpretation.
    """
    if shadow_results.get("base_cost") is None:
        return "  Base case is infeasible — no shadow prices available."

    lines = []
    lines.append(f"  {'Constraint':<20} {'Base Value':>14} {'Perturbed':>14} "
                 f"{'Base Cost ($)':>16} {'New Cost ($)':>16} {'Shadow Price':>16} {'Interpretation'}")
    lines.append(f"  {'-' * 20} {'-' * 14} {'-' * 14} {'-' * 16} {'-' * 16} {'-' * 16} {'-' * 30}")

    # DWT demand row
    cargo = shadow_results.get("cargo_demand", 0)
    dwt_perturbed = cargo * 1.01
    dwt_sp = shadow_results.get("dwt_shadow_price")
    if dwt_sp is not None:
        lines.append(
            f"  {'DWT Demand':<20} {cargo:>14,.0f} {dwt_perturbed:>14,.0f} "
            f"{shadow_results['base_cost']:>16,.2f} {shadow_results['perturbed_cost_dwt']:>16,.2f} "
            f"{'$' + f'{dwt_sp:,.2f}' + '/t':>16} {'$/tonne additional capacity'}"
        )
    else:
        note = shadow_results.get("dwt_note", "infeasible")
        lines.append(
            f"  {'DWT Demand':<20} {cargo:>14,.0f} {dwt_perturbed:>14,.0f} "
            f"{shadow_results['base_cost']:>16,.2f} {'N/A':>16} {'N/A':>16} {note}"
        )

    # Safety threshold row
    safety = shadow_results.get("safety_threshold", 0)
    safety_perturbed = safety + 0.1
    safety_sp = shadow_results.get("safety_shadow_price")
    if safety_sp is not None:
        lines.append(
            f"  {'Safety Threshold':<20} {safety:>14.1f} {safety_perturbed:>14.1f} "
            f"{shadow_results['base_cost']:>16,.2f} {shadow_results['perturbed_cost_safety']:>16,.2f} "
            f"{'$' + f'{safety_sp:,.2f}' + '/pt':>16} {'$/unit safety increase'}"
        )
    else:
        note = shadow_results.get("safety_note", "infeasible")
        lines.append(
            f"  {'Safety Threshold':<20} {safety:>14.1f} {safety_perturbed:>14.1f} "
            f"{shadow_results['base_cost']:>16,.2f} {'N/A':>16} {'N/A':>16} {note}"
        )

    return "\n".join(lines)


def run_carbon_price_sweep(
    df: pd.DataFrame,
    carbon_prices: list[float] | None = None,
    cargo_demand: float = MONTHLY_DEMAND,
    safety_threshold: float = SAFETY_THRESHOLD,
) -> list[dict[str, Any]]:
    """
    Re-run MILP at each carbon price and collect fleet metrics.

    Adjusts ``final_cost`` by removing the original carbon cost component
    and replacing it with ``CO2eq * new_carbon_price``, then solves the
    cost-minimising MILP on the adjusted DataFrame.

    Returns a list of dicts, one per carbon price, with keys:
    carbon_price, feasible, fleet_size, total_cost_usd, total_co2e_tonnes,
    avg_safety_score, total_dwt, selected_ids, fuel_type_counts.
    """
    if carbon_prices is None:
        carbon_prices = [80, 120, 160, 200]

    results: list[dict[str, Any]] = []
    for cp in carbon_prices:
        df_copy = df.copy()

        # Compute the original carbon cost; fall back to base CARBON_PRICE if column missing
        if "carbon_cost" in df_copy.columns:
            original_carbon_cost = df_copy["carbon_cost"]
        else:
            original_carbon_cost = df_copy["CO2eq"] * CARBON_PRICE

        # Recalculate final_cost with the new carbon price
        df_copy["final_cost"] = (
            df_copy["final_cost"] - original_carbon_cost + df_copy["CO2eq"] * cp
        )

        selected_ids = select_fleet_milp(
            df_copy,
            cargo_demand=cargo_demand,
            min_avg_safety=safety_threshold,
        )

        if not selected_ids:
            results.append({
                "carbon_price": cp,
                "feasible": False,
                "fleet_size": None,
                "total_cost_usd": None,
                "total_co2e_tonnes": None,
                "avg_safety_score": None,
                "total_dwt": None,
                "selected_ids": [],
                "fuel_type_counts": {},
            })
        else:
            metrics = total_cost_and_metrics(df_copy, selected_ids)
            subset = df_copy[df_copy["vessel_id"].isin(selected_ids)]
            fuel_counts = subset["main_engine_fuel_type"].value_counts().to_dict()

            results.append({
                "carbon_price": cp,
                "feasible": True,
                "fleet_size": metrics["fleet_size"],
                "total_cost_usd": metrics["total_cost_usd"],
                "total_co2e_tonnes": metrics["total_co2e_tonnes"],
                "avg_safety_score": metrics["avg_safety_score"],
                "total_dwt": metrics["total_dwt"],
                "selected_ids": selected_ids,
                "fuel_type_counts": fuel_counts,
            })

    return results


def format_carbon_sweep_table(results: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Format carbon price sweep results as a readable comparison table.

    Returns a DataFrame with columns: Carbon Price ($/t), Feasible,
    Fleet Size, Total Cost ($), Total CO2eq (t), Avg Safety.
    """
    rows = []
    for r in results:
        if r["feasible"]:
            rows.append({
                "Carbon Price ($/t)": r["carbon_price"],
                "Feasible": "Yes",
                "Fleet Size": r["fleet_size"],
                "Total Cost ($)": f"{r['total_cost_usd']:,.2f}",
                "Total CO2eq (t)": f"{r['total_co2e_tonnes']:,.2f}",
                "Avg Safety": f"{r['avg_safety_score']:.2f}",
            })
        else:
            rows.append({
                "Carbon Price ($/t)": r["carbon_price"],
                "Feasible": "INFEASIBLE",
                "Fleet Size": "-",
                "Total Cost ($)": "-",
                "Total CO2eq (t)": "-",
                "Avg Safety": "-",
            })

    return pd.DataFrame(rows)


def run_diversity_whatif(
    df: pd.DataFrame,
    cargo_demand: float = MONTHLY_DEMAND,
    safety_threshold: float = SAFETY_THRESHOLD,
) -> dict[str, Any]:
    """
    Compare fleet selection with and without fuel diversity constraint.

    Returns dict with:
    - with_diversity: metrics when require_all_fuel_types=True
    - without_diversity: metrics when require_all_fuel_types=False
    - cost_savings: cost difference (negative = cheaper without diversity)
    - fleet_size_diff: fleet size difference
    - fuel_types_lost: fuel types present with diversity but missing without
    """
    # --- With diversity constraint ---
    with_ids = select_fleet_milp(
        df, cargo_demand=cargo_demand, min_avg_safety=safety_threshold,
        require_all_fuel_types=True,
    )
    if with_ids:
        with_metrics = total_cost_and_metrics(df, with_ids)
        with_subset = df[df["vessel_id"].isin(with_ids)]
        with_fuel_types = set(with_subset["main_engine_fuel_type"].unique())
        with_fuel_counts = with_subset["main_engine_fuel_type"].value_counts().to_dict()
    else:
        with_metrics = None
        with_fuel_types = set()
        with_fuel_counts = {}

    # --- Without diversity constraint ---
    without_ids = select_fleet_milp(
        df, cargo_demand=cargo_demand, min_avg_safety=safety_threshold,
        require_all_fuel_types=False,
    )
    if without_ids:
        without_metrics = total_cost_and_metrics(df, without_ids)
        without_subset = df[df["vessel_id"].isin(without_ids)]
        without_fuel_types = set(without_subset["main_engine_fuel_type"].unique())
        without_fuel_counts = without_subset["main_engine_fuel_type"].value_counts().to_dict()
    else:
        without_metrics = None
        without_fuel_types = set()
        without_fuel_counts = {}

    result: dict[str, Any] = {
        "with_diversity": {
            "feasible": with_ids is not None and len(with_ids) > 0,
            "selected_ids": with_ids or [],
            "metrics": with_metrics,
            "fuel_type_counts": with_fuel_counts,
            "fuel_types": with_fuel_types,
        },
        "without_diversity": {
            "feasible": without_ids is not None and len(without_ids) > 0,
            "selected_ids": without_ids or [],
            "metrics": without_metrics,
            "fuel_type_counts": without_fuel_counts,
            "fuel_types": without_fuel_types,
        },
    }

    # Compute savings and differences
    if with_metrics and without_metrics:
        result["cost_savings"] = without_metrics["total_cost_usd"] - with_metrics["total_cost_usd"]
        result["fleet_size_diff"] = without_metrics["fleet_size"] - with_metrics["fleet_size"]
        result["fuel_types_lost"] = with_fuel_types - without_fuel_types
    else:
        result["cost_savings"] = None
        result["fleet_size_diff"] = None
        result["fuel_types_lost"] = set()

    return result


def compute_fleet_efficiency(
    df: pd.DataFrame,
    selected_ids: list[int],
    cargo_demand: float = MONTHLY_DEMAND,
) -> dict[str, Any]:
    """
    Compute fleet efficiency metrics for a selected fleet.

    Returns dict with:
    - cost_per_dwt: total_cost / total_dwt ($/tonne capacity)
    - cost_per_vessel: total_cost / fleet_size
    - dwt_per_vessel: total_dwt / fleet_size (average vessel size)
    - co2_per_dwt: total_co2e / total_dwt (emissions intensity)
    - utilization: total_dwt / cargo_demand (capacity utilization ratio)
    """
    if not selected_ids:
        return {
            "cost_per_dwt": None,
            "cost_per_vessel": None,
            "dwt_per_vessel": None,
            "co2_per_dwt": None,
            "utilization": None,
            "note": "no fleet selected",
        }

    metrics = total_cost_and_metrics(df, selected_ids)
    total_cost = metrics["total_cost_usd"]
    total_dwt = metrics["total_dwt"]
    fleet_size = metrics["fleet_size"]
    total_co2e = metrics["total_co2e_tonnes"]

    return {
        "cost_per_dwt": total_cost / total_dwt if total_dwt > 0 else None,
        "cost_per_vessel": total_cost / fleet_size if fleet_size > 0 else None,
        "dwt_per_vessel": total_dwt / fleet_size if fleet_size > 0 else None,
        "co2_per_dwt": total_co2e / total_dwt if total_dwt > 0 else None,
        "utilization": total_dwt / cargo_demand if cargo_demand > 0 else None,
        "total_cost": total_cost,
        "total_dwt": total_dwt,
        "fleet_size": fleet_size,
        "total_co2e": total_co2e,
    }
